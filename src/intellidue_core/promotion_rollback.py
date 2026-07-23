from __future__ import annotations

import json
from pathlib import Path
import uuid
from typing import Any

from .contracts import SCHEMA_VERSION
from .manifest import manifest_hash, verify_manifest
from .promotion_support import archive_previous, enforce_expected_current, maybe_fail, now_utc, validate_failure_point, validate_identifier
from .workspace import PromotionError, SimulatedCrash, WorkspaceLock, atomic_write_json, ensure_layout, finish_journal, load_archive, pointer, previous_snapshots, read_json, restore_previous, write_journal


def rollback_release(workspace: str | Path, release_id: str, reason: str, *, expected_current: str | None = None, transaction_id: str | None = None, timestamp: str | None = None, fail_at: str | None = None) -> dict[str, Any]:
    validate_identifier(release_id, "RELEASE_ID_INVALID", "release_id")
    if not reason.strip():
        raise PromotionError("ROLLBACK_REASON_REQUIRED", "rollback reason is required")
    transaction_id = transaction_id or uuid.uuid4().hex
    validate_identifier(transaction_id, "TRANSACTION_ID_INVALID", "transaction_id")
    validate_failure_point(fail_at)
    timestamp = timestamp or now_utc()

    with WorkspaceLock(workspace):
        paths = ensure_layout(workspace)
        if paths["active"].exists():
            raise PromotionError("RECOVERY_REQUIRED", "an unfinished transaction journal exists")
        previous_current = enforce_expected_current(paths, expected_current)
        if previous_current is None:
            raise PromotionError("CURRENT_POINTER_MISSING", "cannot rollback without a current release")
        if previous_current == release_id:
            raise PromotionError("ROLLBACK_TARGET_IS_CURRENT", "rollback target is already current")
        release_path = paths["releases"] / release_id
        manifest_path = paths["manifests"] / f"{release_id}.manifest.json"
        if not release_path.is_dir() or not manifest_path.is_file():
            raise PromotionError("ROLLBACK_TARGET_MISSING", f"rollback target is incomplete: {release_id}")
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        issues = verify_manifest(release_path, manifest)
        if issues:
            raise PromotionError(issues[0].code, issues[0].message, issues[0].path)

        journal = {"schema_version": SCHEMA_VERSION, "transaction_id": transaction_id, "operation": "ROLLBACK", "status": "PREPARED", "target_release_id": release_id, "started_at": timestamp, "previous": previous_snapshots(paths)}
        write_journal(paths, journal)
        try:
            digest = manifest_hash(manifest)
            old_pointer = read_json(paths["current"])
            assert old_pointer is not None
            archive = load_archive(paths["archive"])
            archive["entries"] = [item for item in archive["entries"] if item["release_id"] not in {release_id, previous_current}]
            archive = archive_previous(archive, old_pointer, timestamp, f"rollback:{reason.strip()}", transaction_id)
            atomic_write_json(paths["archive"], archive)
            maybe_fail("after-archive", fail_at)

            current_pointer = pointer("CURRENT", release_id, digest, timestamp, transaction_id)
            atomic_write_json(paths["current"], current_pointer)
            maybe_fail("after-current", fail_at)
            atomic_write_json(paths["last_success"], pointer("LAST_SUCCESS", release_id, digest, timestamp, transaction_id))
            maybe_fail("after-last-success", fail_at)

            finish_journal(paths, journal, "COMMITTED")
            return {"transaction_id": transaction_id, "release_id": release_id, "manifest_sha256": digest, "current": current_pointer, "archived_release": previous_current, "reason": reason.strip()}
        except SimulatedCrash:
            raise
        except Exception as exc:
            restore_previous(paths, journal)
            finish_journal(paths, journal, "ROLLED_BACK", f"{type(exc).__name__}: {exc}")
            if isinstance(exc, PromotionError):
                raise
            raise PromotionError("ROLLBACK_FAILED", f"{type(exc).__name__}: {exc}") from exc
