#!/usr/bin/env python3
"""Run the GitHub-5 private replay sequence without exporting private content.

The runner consumes four caller-prepared private project roots:
- v1: first accepted real-private release;
- v2: controlled incremental release for the same project;
- crash: third release for the same project, used only for recovery testing;
- contamination: a synthetic project with a different project_id.

Only anonymized gate results are written to the requested output file. Project
identities, product names, paths, content hashes and business facts are never
included in the public result.
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
from pathlib import Path
import zipfile

from intellidue_core import __version__
from intellidue_core.private_runtime import (
    ADAPTER_CONTRACT_VERSION,
    PrivateRuntimeError,
    build_private_release_package,
    inspect_private_project,
    inspect_private_runtime,
    promote_private_release,
    recover_private_runtime,
    rollback_private_release,
    validate_private_project,
    validate_private_runtime,
)
from intellidue_core.promotion import SimulatedCrash
from intellidue_core.promotion_apply import promote_release


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Run an anonymized GitHub-5 private replay acceptance sequence."
    )
    parser.add_argument("--v1-project", required=True, type=Path)
    parser.add_argument("--v2-project", required=True, type=Path)
    parser.add_argument("--crash-project", required=True, type=Path)
    parser.add_argument("--contamination-project", required=True, type=Path)
    parser.add_argument("--runtime", required=True, type=Path)
    parser.add_argument("--work-dir", required=True, type=Path)
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument(
        "--timestamp",
        help="ISO-8601 timestamp reused for the deterministic build proof.",
    )
    return parser.parse_args()


def now_utc() -> str:
    return (
        datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )


def require_clean_target(path: Path, label: str) -> None:
    if path.exists():
        raise RuntimeError(f"{label} must not exist before replay: {path}")


def assert_valid_project(path: Path) -> dict:
    issues = validate_private_project(path)
    if issues:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    summary, issues = inspect_private_project(path)
    if issues or summary is None:
        issue = issues[0]
        raise PrivateRuntimeError(issue.code, issue.message, issue.path)
    return summary


def read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def run(args: argparse.Namespace) -> dict:
    require_clean_target(args.runtime, "runtime")
    require_clean_target(args.work_dir, "work directory")
    args.work_dir.mkdir(parents=True)
    args.output.parent.mkdir(parents=True, exist_ok=True)

    v1 = assert_valid_project(args.v1_project)
    v2 = assert_valid_project(args.v2_project)
    crash = assert_valid_project(args.crash_project)
    other = assert_valid_project(args.contamination_project)

    if not (v1["project_id"] == v2["project_id"] == crash["project_id"]):
        raise RuntimeError(
            "v1, v2 and crash project roots must use the same project_id"
        )
    if len({v1["release_id"], v2["release_id"], crash["release_id"]}) != 3:
        raise RuntimeError(
            "v1, v2 and crash project roots must use distinct release_id values"
        )
    if other["project_id"] == v1["project_id"]:
        raise RuntimeError("contamination project must use a different project_id")
    if not other["project_id"].startswith("SYNTHETIC_"):
        raise RuntimeError("contamination project must use a synthetic project_id")

    timestamp = args.timestamp or now_utc()
    metrics: dict[str, object] = {
        "schema_version": "1.0.0",
        "work_package": "GitHub-5",
        "core_version": __version__,
        "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
        "private_project_validation": "PASS",
        "project_identity_exported": False,
        "private_paths_exported": False,
        "private_hashes_exported": False,
        "network_write_performed": False,
    }

    package_a = args.work_dir / "v1-a.zip"
    package_b = args.work_dir / "v1-b.zip"
    first = build_private_release_package(
        args.v1_project, package_a, timestamp=timestamp
    )
    second = build_private_release_package(
        args.v1_project, package_b, timestamp=timestamp
    )
    if first["sha256"] != second["sha256"]:
        raise RuntimeError("deterministic build mismatch")
    metrics["deterministic_build"] = "PASS"

    promote_private_release(
        args.v1_project,
        args.runtime,
        transaction_id="github5-v1",
        timestamp=timestamp,
    )
    if validate_private_runtime(args.runtime):
        raise RuntimeError("runtime validation failed after v1 promotion")
    promote_private_release(
        args.v2_project,
        args.runtime,
        expected_current=v1["release_id"],
        transaction_id="github5-v2",
        timestamp=timestamp,
    )
    if validate_private_runtime(args.runtime):
        raise RuntimeError("runtime validation failed after v2 promotion")
    metrics["v1_promotion"] = "PASS"
    metrics["v2_incremental_promotion"] = "PASS"
    metrics["expected_current_enforced"] = True

    core = args.runtime / "core"
    current = read_json(core / "pointers/current.json")
    last_success = read_json(core / "pointers/last_success.json")
    archive = read_json(core / "pointers/archive.json")
    if (
        current["release_id"] != v2["release_id"]
        or last_success["release_id"] != v2["release_id"]
    ):
        raise RuntimeError("Current and Last-success do not agree with v2")
    if not any(
        item["release_id"] == v1["release_id"] for item in archive["entries"]
    ):
        raise RuntimeError("v1 is missing from Archive after v2 promotion")
    metrics["pointer_reconciliation"] = "PASS"

    rollback_private_release(
        args.runtime,
        v1["release_id"],
        "GitHub-5 controlled rollback drill",
        expected_current=v2["release_id"],
        transaction_id="github5-rollback",
        timestamp=timestamp,
    )
    if validate_private_runtime(args.runtime):
        raise RuntimeError("runtime validation failed after rollback")
    rollback_summary, issues = inspect_private_runtime(args.runtime)
    if (
        issues
        or rollback_summary is None
        or rollback_summary["current_release"] != v1["release_id"]
    ):
        raise RuntimeError("rollback target was not restored")
    metrics["rollback"] = "PASS"

    crash_package = args.work_dir / "crash.zip"
    build_private_release_package(
        args.crash_project, crash_package, timestamp=timestamp
    )
    extracted = args.work_dir / "crash-extracted"
    with zipfile.ZipFile(crash_package) as archive_file:
        archive_file.extractall(extracted)
    candidate = extracted / crash["release_id"] / "payload"
    crashed = False
    try:
        promote_release(
            core,
            candidate,
            crash["release_id"],
            expected_current=v1["release_id"],
            transaction_id="github5-crash",
            timestamp=timestamp,
            fail_at="crash-after-current",
        )
    except SimulatedCrash:
        crashed = True
    if not crashed:
        raise RuntimeError("controlled crash was not raised")
    if "RECOVERY_REQUIRED" not in {
        issue.code for issue in validate_private_runtime(args.runtime)
    }:
        raise RuntimeError("runtime did not fail closed after controlled crash")
    recovery = recover_private_runtime(args.runtime)
    if not recovery.get("recovered") or validate_private_runtime(args.runtime):
        raise RuntimeError("private runtime recovery failed")
    metrics["crash_fail_closed"] = "PASS"
    metrics["recovery"] = "PASS"

    conflict_code = None
    try:
        promote_private_release(
            args.contamination_project,
            args.runtime,
            expected_current=v1["release_id"],
            transaction_id="github5-contamination",
            timestamp=timestamp,
        )
    except PrivateRuntimeError as exc:
        conflict_code = exc.issue.code
    if conflict_code != "PRIVATE_RUNTIME_PROJECT_CONFLICT":
        raise RuntimeError(
            "cross-project contamination was not rejected with the typed conflict code"
        )
    if validate_private_runtime(args.runtime):
        raise RuntimeError("runtime was damaged by contamination attempt")
    metrics["cross_project_contamination"] = "PASS"

    final_summary, issues = inspect_private_runtime(args.runtime)
    if (
        issues
        or final_summary is None
        or final_summary["current_release"] != v1["release_id"]
    ):
        raise RuntimeError(
            "final runtime does not reconcile to the rollback target"
        )
    metrics["final_runtime_validation"] = "PASS"
    metrics["final_current_is_rollback_target"] = True
    metrics["result"] = "PASS"
    return metrics


def main() -> int:
    args = parse_args()
    try:
        metrics = run(args)
    except Exception as exc:
        metrics = {
            "schema_version": "1.0.0",
            "work_package": "GitHub-5",
            "core_version": __version__,
            "adapter_contract_version": ADAPTER_CONTRACT_VERSION,
            "result": "FAIL",
            "error_type": type(exc).__name__,
            "project_identity_exported": False,
            "private_paths_exported": False,
            "private_hashes_exported": False,
            "network_write_performed": False,
        }
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(
            json.dumps(metrics, indent=2, sort_keys=True) + "\n",
            encoding="utf-8",
        )
        return 1
    args.output.write_text(
        json.dumps(metrics, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
