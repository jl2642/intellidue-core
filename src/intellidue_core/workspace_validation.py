from __future__ import annotations

import json
from pathlib import Path

from .contracts import ValidationIssue, validate_object
from .manifest import manifest_hash, verify_manifest
from .workspace import PromotionError, empty_archive, read_json, workspace_paths


def validate_workspace(workspace: str | Path) -> list[ValidationIssue]:
    root = Path(workspace)
    paths = workspace_paths(root)
    issues: list[ValidationIssue] = []
    if paths["active"].exists():
        issues.append(ValidationIssue("RECOVERY_REQUIRED", "$.transactions.active", "unfinished transaction journal exists"))

    def safe_read(label: str, path: Path) -> dict | None:
        try:
            return read_json(path)
        except PromotionError as exc:
            issues.append(ValidationIssue(exc.issue.code, f"$.pointers.{label}", exc.issue.message))
            return None

    current = safe_read("current", paths["current"])
    last_success = safe_read("last_success", paths["last_success"])
    archive = safe_read("archive", paths["archive"]) or empty_archive()
    if current is None:
        issues.append(ValidationIssue("CURRENT_POINTER_MISSING", "$.pointers.current", "current pointer is missing"))
    if last_success is None:
        issues.append(ValidationIssue("LAST_SUCCESS_POINTER_MISSING", "$.pointers.last_success", "last-success pointer is missing"))

    for label, value, expected_type in (("current", current, "CURRENT"), ("last_success", last_success, "LAST_SUCCESS")):
        if value is None:
            continue
        for issue in validate_object("pointer", value):
            issues.append(ValidationIssue(issue.code, f"$.pointers.{label}{issue.path[1:]}", issue.message))
        if value.get("pointer_type") != expected_type:
            issues.append(ValidationIssue("POINTER_TYPE_MISMATCH", f"$.pointers.{label}.pointer_type", f"expected {expected_type}"))
        _validate_target(root, label, value, issues)

    if current and last_success:
        current_key = (current.get("release_id"), current.get("manifest_sha256"))
        last_key = (last_success.get("release_id"), last_success.get("manifest_sha256"))
        if current_key != last_key:
            issues.append(ValidationIssue("CURRENT_LAST_SUCCESS_MISMATCH", "$.pointers", "current and last-success pointers must identify the same accepted release"))

    for issue in validate_object("archive", archive):
        issues.append(ValidationIssue(issue.code, f"$.pointers.archive{issue.path[1:]}", issue.message))
    current_id = current.get("release_id") if current else None
    for index, entry in enumerate(archive.get("entries", [])):
        prefix = f"$.pointers.archive.entries[{index}]"
        if entry["release_id"] == current_id:
            issues.append(ValidationIssue("ARCHIVE_CURRENT_CONFLICT", prefix, "current release must not be listed as archived"))
        _validate_target(root, f"archive.entries[{index}]", entry, issues, prefix)
    return sorted(set(issues))


def _validate_target(root: Path, label: str, value: dict, issues: list[ValidationIssue], prefix: str | None = None) -> None:
    prefix = prefix or f"$.pointers.{label}"
    release_id = value.get("release_id")
    if not release_id:
        return
    release_path = root / value["release_path"]
    manifest_path = root / value["manifest_path"]
    if not release_path.is_dir() or not manifest_path.is_file():
        issues.append(ValidationIssue("POINTER_TARGET_MISSING", prefix, f"target is incomplete: {release_id}"))
        return
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    except json.JSONDecodeError:
        issues.append(ValidationIssue("POINTER_MANIFEST_INVALID", f"{prefix}.manifest_path", "manifest JSON is invalid"))
        return
    if manifest.get("root") != release_id:
        issues.append(ValidationIssue("POINTER_MANIFEST_ROOT_MISMATCH", f"{prefix}.manifest_path", "manifest root must equal release_id"))
    if manifest_hash(manifest) != value.get("manifest_sha256"):
        issues.append(ValidationIssue("POINTER_MANIFEST_HASH_MISMATCH", f"{prefix}.manifest_sha256", "pointer manifest hash does not match manifest"))
    for issue in verify_manifest(release_path, manifest):
        issues.append(ValidationIssue(issue.code, f"{prefix}{issue.path[1:]}", issue.message))
