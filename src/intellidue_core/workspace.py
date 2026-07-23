from __future__ import annotations

import base64
from contextlib import AbstractContextManager
import json
import os
from pathlib import Path
import uuid

from .contracts import SCHEMA_VERSION, ValidationIssue, validate_object
from .manifest import canonical_json_bytes


class PromotionError(Exception):
    def __init__(self, code: str, message: str, path: str = "$"):
        super().__init__(message)
        self.issue = ValidationIssue(code, path, message)


class SimulatedCrash(BaseException):
    """Test-only crash that bypasses automatic rollback."""


class WorkspaceLock(AbstractContextManager):
    def __init__(self, workspace: str | Path):
        self.workspace = Path(workspace)
        self.path = self.workspace / ".promotion.lock"
        self.acquired = False

    def __enter__(self):
        self.workspace.mkdir(parents=True, exist_ok=True)
        try:
            fd = os.open(self.path, os.O_CREAT | os.O_EXCL | os.O_WRONLY, 0o600)
        except FileExistsError as exc:
            raise PromotionError("PROMOTION_LOCKED", f"workspace is locked: {self.path}") from exc
        try:
            os.write(fd, f"pid={os.getpid()}\n".encode())
            os.fsync(fd)
        finally:
            os.close(fd)
        self.acquired = True
        return self

    def __exit__(self, exc_type, exc, tb):
        if self.acquired:
            self.path.unlink(missing_ok=True)
        return False


def workspace_paths(workspace: str | Path) -> dict[str, Path]:
    root = Path(workspace)
    return {
        "root": root,
        "releases": root / "releases",
        "manifests": root / "manifests",
        "pointers": root / "pointers",
        "current": root / "pointers/current.json",
        "last_success": root / "pointers/last_success.json",
        "archive": root / "pointers/archive.json",
        "active": root / "transactions/active.json",
        "history": root / "transactions/history",
    }


def ensure_layout(workspace: str | Path) -> dict[str, Path]:
    paths = workspace_paths(workspace)
    for key in ("releases", "manifests", "pointers", "history"):
        paths[key].mkdir(parents=True, exist_ok=True)
    paths["active"].parent.mkdir(parents=True, exist_ok=True)
    return paths


def atomic_write_bytes(path: Path, payload: bytes) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f".{path.name}.{uuid.uuid4().hex}.tmp")
    with temporary.open("wb") as file:
        file.write(payload)
        file.flush()
        os.fsync(file.fileno())
    os.replace(temporary, path)


def atomic_write_json(path: Path, value: dict) -> None:
    atomic_write_bytes(path, canonical_json_bytes(value))


def read_json(path: Path) -> dict | None:
    if not path.exists():
        return None
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise PromotionError("POINTER_JSON_INVALID", f"invalid JSON at {path}: {exc.msg}") from exc
    if not isinstance(value, dict):
        raise PromotionError("POINTER_NOT_OBJECT", f"JSON document must be an object: {path}")
    return value


def snapshot(path: Path) -> str | None:
    return base64.b64encode(path.read_bytes()).decode("ascii") if path.exists() else None


def restore(path: Path, encoded: str | None) -> None:
    if encoded is None:
        path.unlink(missing_ok=True)
    else:
        atomic_write_bytes(path, base64.b64decode(encoded.encode("ascii")))


def previous_snapshots(paths: dict[str, Path]) -> dict[str, str | None]:
    return {name: snapshot(paths[name]) for name in ("current", "last_success", "archive")}


def restore_previous(paths: dict[str, Path], journal: dict) -> None:
    for name, encoded in journal["previous"].items():
        restore(paths[name], encoded)


def empty_archive() -> dict:
    return {"schema_version": SCHEMA_VERSION, "entries": []}


def load_archive(path: Path) -> dict:
    archive = read_json(path) or empty_archive()
    issues = validate_object("archive", archive)
    if issues:
        issue = issues[0]
        raise PromotionError(issue.code, issue.message, issue.path)
    return archive


def pointer(pointer_type: str, release_id: str, digest: str, timestamp: str, transaction_id: str) -> dict:
    value = {
        "schema_version": SCHEMA_VERSION,
        "pointer_type": pointer_type,
        "release_id": release_id,
        "release_path": f"releases/{release_id}",
        "manifest_path": f"manifests/{release_id}.manifest.json",
        "manifest_sha256": digest,
        "promoted_at": timestamp,
        "transaction_id": transaction_id,
    }
    issues = validate_object("pointer", value)
    if issues:
        issue = issues[0]
        raise PromotionError(issue.code, issue.message, issue.path)
    return value


def write_journal(paths: dict[str, Path], journal: dict) -> None:
    atomic_write_json(paths["active"], journal)


def finish_journal(paths: dict[str, Path], journal: dict, status: str, detail: str | None = None) -> None:
    journal["status"] = status
    if detail:
        journal["detail"] = detail
    atomic_write_json(paths["active"], journal)
    atomic_write_json(paths["history"] / f"{journal['transaction_id']}.json", journal)
    paths["active"].unlink(missing_ok=True)
