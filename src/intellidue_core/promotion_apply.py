from __future__ import annotations

import os
from pathlib import Path
import shutil
import uuid
from typing import Any

from .contracts import SCHEMA_VERSION
from .manifest import build_manifest, canonical_json_bytes, manifest_hash, verify_manifest
from .promotion_support import archive_previous, enforce_expected_current, maybe_fail, now_utc, remove_created, validate_failure_point, validate_identifier
from .workspace import PromotionError, SimulatedCrash, WorkspaceLock, atomic_write_bytes, atomic_write_json, ensure_layout, finish_journal, load_archive, pointer, previous_snapshots, read_json, restore_previous, write_journal


def promote_release(workspace: str | Path, candidate: str | Path, release_id: str, *, expected_current: str | None = None, transaction_id: str | None = None, timestamp: str | None = None, fail_at: str | None = None) -> dict[str, Any]:
    validate_identifier(release_id, "RELEASE_ID_INVALID", "release_id")
    transaction_id = transaction_id or uuid.uuid4().hex
    validate_identifier(transaction_id, "TRANSACTION_ID_INVALID", "transaction_id")
    validate_failure_point(fail_at)
    timestamp = timestamp or now_utc()
    candidate = Path(candidate)

    with WorkspaceLock(workspace):
        paths = ensure_layout(workspace)
        if paths["active"].exists():
            raise PromotionError("RECOVERY_REQUIRED", "an unfinished transaction journal exists")
        previous_current = enforce_expected_current(paths, expected_current)
        release_path = paths["releases"] / release_id
        manifest_path = paths["manifests"] / f"{release_id}.manifest.json"
        if release_path.exists() or manifest_path.exists():
            raise PromotionError("RELEASE_IMMUTABLE", f"release already exists: {release_id}")
        try:
            candidate_manifest = build_manifest(candidate, root_name=release_id)
        except ValueError as exc:
            raise PromotionError("CANDIDATE_INVALID", str(exc)) from exc

        staging_release = paths["releases"] / f".staging-{transaction_id}"
        staging_manifest = paths["manifests"] / f".staging-{transaction_id}.json"
        journal = {
            "schema_version": SCHEMA_VERSION, "transaction_id": transaction_id,
            "operation": "PROMOTE", "status": "PREPARED", "target_release_id": release_id,
            "started_at": timestamp, "previous": previous_snapshots(paths),
            "staging_release": str(staging_release), "staging_manifest": str(staging_manifest),
            "installed_release": str(release_path), "installed_manifest": str(manifest_path),
        }
        write_journal(paths, journal)
        try:
            shutil.copytree(candidate, staging_release)
            staged_manifest = build_manifest(staging_release, root_name=release_id)
            if staged_manifest != candidate_manifest:
                raise PromotionError("PROMOTION_COPY_MISMATCH", "staged release does not match candidate manifest")
            issues = verify_manifest(staging_release, staged_manifest)
            if issues:
                raise PromotionError(issues[0].code, issues[0].message, issues[0].path)
            atomic_write_bytes(staging_manifest, canonical_json_bytes(staged_manifest))
            journal["status"] = "STAGED"
            write_journal(paths, journal)
            maybe_fail("after-stage", fail_at)

            os.replace(staging_release, release_path)
            os.replace(staging_manifest, manifest_path)
            journal["status"] = "INSTALLED"
            write_journal(paths, journal)
            maybe_fail("after-install", fail_at)

            digest = manifest_hash(staged_manifest)
            archive = load_archive(paths["archive"])
            if previous_current is not None:
                old_pointer = read_json(paths["current"])
                assert old_pointer is not None
                archive = archive_previous(archive, old_pointer, timestamp, f"superseded_by:{release_id}", transaction_id)
            atomic_write_json(paths["archive"], archive)
            maybe_fail("after-archive", fail_at)

            current_pointer = pointer("CURRENT", release_id, digest, timestamp, transaction_id)
            atomic_write_json(paths["current"], current_pointer)
            maybe_fail("after-current", fail_at)
            atomic_write_json(paths["last_success"], pointer("LAST_SUCCESS", release_id, digest, timestamp, transaction_id))
            maybe_fail("after-last-success", fail_at)

            journal["manifest_sha256"] = digest
            finish_journal(paths, journal, "COMMITTED")
            return {"transaction_id": transaction_id, "release_id": release_id, "manifest_sha256": digest, "current": current_pointer, "archived_release": previous_current}
        except SimulatedCrash:
            raise
        except Exception as exc:
            restore_previous(paths, journal)
            remove_created(journal)
            finish_journal(paths, journal, "ROLLED_BACK", f"{type(exc).__name__}: {exc}")
            if isinstance(exc, PromotionError):
                raise
            raise PromotionError("PROMOTION_FAILED", f"{type(exc).__name__}: {exc}") from exc
