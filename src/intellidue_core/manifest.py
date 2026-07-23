from __future__ import annotations

import hashlib
import json
from pathlib import Path
from typing import Iterable

from .contracts import SCHEMA_VERSION, ValidationIssue, validate_object


def file_hash(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def canonical_json_bytes(value: dict) -> bytes:
    return (json.dumps(value, ensure_ascii=False, sort_keys=True, separators=(",", ":")) + "\n").encode("utf-8")


def manifest_hash(manifest: dict) -> str:
    return hashlib.sha256(canonical_json_bytes(manifest)).hexdigest()


def inspect_release_tree(root: str | Path) -> list[ValidationIssue]:
    root = Path(root)
    if not root.exists():
        return [ValidationIssue("MANIFEST_ROOT_MISSING", "$", f"root not found: {root}")]
    if not root.is_dir():
        return [ValidationIssue("MANIFEST_ROOT_NOT_DIRECTORY", "$", f"root is not a directory: {root}")]
    issues: list[ValidationIssue] = []
    for path in sorted(root.rglob("*")):
        relative = path.relative_to(root).as_posix()
        if path.is_symlink():
            issues.append(ValidationIssue("MANIFEST_SYMLINK", f"$.files[{relative!r}]", "symbolic links are not allowed"))
        elif not path.is_dir() and not path.is_file():
            issues.append(ValidationIssue("MANIFEST_SPECIAL_FILE", f"$.files[{relative!r}]", "special files are not allowed"))
    return sorted(set(issues))


def build_manifest(root: str | Path, *, root_name: str | None = None) -> dict:
    root = Path(root)
    issues = inspect_release_tree(root)
    if issues:
        raise ValueError("; ".join(f"{issue.code}:{issue.message}" for issue in issues))
    entries = []
    for path in sorted(item for item in root.rglob("*") if item.is_file() and not item.is_symlink()):
        entries.append({
            "path": path.relative_to(root).as_posix(),
            "size_bytes": path.stat().st_size,
            "sha256": file_hash(path),
        })
    return {"schema_version": SCHEMA_VERSION, "root": root_name or root.name, "files": entries}


def save_manifest(root: str | Path, output: str | Path, *, root_name: str | None = None) -> dict:
    manifest = build_manifest(root, root_name=root_name)
    Path(output).write_bytes(canonical_json_bytes(manifest))
    return manifest


def verify_manifest(root: str | Path, manifest: dict) -> list[ValidationIssue]:
    issues = list(validate_object("manifest", manifest))
    issues.extend(inspect_release_tree(root))
    if issues:
        return sorted(set(issues))

    actual = build_manifest(root, root_name=manifest["root"])
    expected_by_path = {item["path"]: item for item in manifest["files"]}
    actual_by_path = {item["path"]: item for item in actual["files"]}

    for path in sorted(expected_by_path.keys() - actual_by_path.keys()):
        issues.append(ValidationIssue("MANIFEST_FILE_MISSING", f"$.files[{path!r}]", "manifest file is missing from the filesystem"))
    for path in sorted(actual_by_path.keys() - expected_by_path.keys()):
        issues.append(ValidationIssue("MANIFEST_FILE_EXTRA", f"$.files[{path!r}]", "filesystem contains a file not recorded in the manifest"))
    for path in sorted(expected_by_path.keys() & actual_by_path.keys()):
        expected = expected_by_path[path]
        current = actual_by_path[path]
        if expected["size_bytes"] != current["size_bytes"]:
            issues.append(ValidationIssue("MANIFEST_SIZE_MISMATCH", f"$.files[{path!r}].size_bytes", "filesystem size does not match manifest"))
        if expected["sha256"] != current["sha256"]:
            issues.append(ValidationIssue("MANIFEST_HASH_MISMATCH", f"$.files[{path!r}].sha256", "filesystem hash does not match manifest"))
    return sorted(set(issues))


def load_manifest(path: str | Path) -> tuple[dict | None, list[ValidationIssue]]:
    path = Path(path)
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [ValidationIssue("FILE_NOT_FOUND", "$", f"file not found: {path}")]
    except json.JSONDecodeError as exc:
        return None, [ValidationIssue("JSON_INVALID", f"$@{exc.lineno}:{exc.colno}", exc.msg)]
    if not isinstance(value, dict):
        return None, [ValidationIssue("DOCUMENT_NOT_OBJECT", "$", "manifest must be a JSON object")]
    return value, []


def verify_manifest_file(root: str | Path, manifest_path: str | Path) -> list[ValidationIssue]:
    manifest, issues = load_manifest(manifest_path)
    if issues or manifest is None:
        return issues
    return verify_manifest(root, manifest)
