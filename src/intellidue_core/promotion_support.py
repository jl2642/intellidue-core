from __future__ import annotations

from datetime import datetime, timezone
import re
import shutil
from pathlib import Path

from .workspace import PromotionError, SimulatedCrash, read_json

ID_PATTERN = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._-]{0,127}$")
FAILURE_POINTS = {"after-stage", "after-install", "after-archive", "after-current", "after-last-success", "crash-after-current"}


def now_utc() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def validate_identifier(value: str, code: str, label: str) -> None:
    if not ID_PATTERN.fullmatch(value):
        raise PromotionError(code, f"invalid {label}: {value!r}")


def validate_failure_point(fail_at: str | None) -> None:
    if fail_at is not None and fail_at not in FAILURE_POINTS:
        raise PromotionError("FAILURE_POINT_INVALID", f"unsupported failure point: {fail_at}")


def maybe_fail(point: str, fail_at: str | None) -> None:
    if fail_at == point:
        raise PromotionError("INJECTED_FAILURE", f"injected failure at {point}")
    if fail_at == f"crash-{point}":
        raise SimulatedCrash(f"simulated crash at {point}")


def current_release(paths: dict[str, Path]) -> str | None:
    value = read_json(paths["current"])
    if value is None:
        return None
    if value.get("pointer_type") != "CURRENT":
        raise PromotionError("POINTER_TYPE_MISMATCH", "current.json must contain pointer_type CURRENT")
    return value.get("release_id")


def enforce_expected_current(paths: dict[str, Path], expected_current: str | None) -> str | None:
    actual = current_release(paths)
    if expected_current is not None and actual != expected_current:
        raise PromotionError("CURRENT_POINTER_CONFLICT", f"expected current {expected_current!r}, found {actual!r}")
    return actual


def archive_previous(archive: dict, old_pointer: dict, timestamp: str, reason: str, transaction_id: str) -> dict:
    old_id = old_pointer["release_id"]
    archive["entries"] = [item for item in archive["entries"] if item["release_id"] != old_id]
    archive["entries"].append({
        "release_id": old_id,
        "release_path": old_pointer["release_path"],
        "manifest_path": old_pointer["manifest_path"],
        "manifest_sha256": old_pointer["manifest_sha256"],
        "archived_at": timestamp,
        "reason": reason,
        "transaction_id": transaction_id,
    })
    archive["entries"] = sorted(archive["entries"], key=lambda item: (item["archived_at"], item["release_id"]))
    return archive


def remove_created(journal: dict) -> None:
    for key in ("staging_release", "installed_release"):
        raw = journal.get(key)
        if raw and Path(raw).exists():
            shutil.rmtree(raw)
    for key in ("staging_manifest", "installed_manifest"):
        raw = journal.get(key)
        if raw:
            Path(raw).unlink(missing_ok=True)
