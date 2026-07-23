from __future__ import annotations

from pathlib import Path
import hashlib
import json

from .contracts import SCHEMA_VERSION


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def build_manifest(root: str | Path) -> dict:
    root = Path(root)
    files = []
    for path in sorted(item for item in root.rglob("*") if item.is_file()):
        files.append(
            {
                "path": path.relative_to(root).as_posix(),
                "size_bytes": path.stat().st_size,
                "sha256": file_hash(path),
            }
        )
    return {"schema_version": SCHEMA_VERSION, "root": root.name, "files": files}


def save_manifest(root: str | Path, output: str | Path) -> None:
    Path(output).write_text(json.dumps(build_manifest(root), indent=2), encoding="utf-8")
