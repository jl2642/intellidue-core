from __future__ import annotations

import hashlib
from pathlib import Path
import zipfile

from .contracts import ValidationIssue, validate_contract_files, validate_document
from .manifest import verify_manifest_file
from .promotion import validate_workspace


def sha256(path: str | Path) -> str:
    h = hashlib.sha256()
    with Path(path).open("rb") as file:
        for chunk in iter(lambda: file.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def validate_state(path: str | Path) -> list[ValidationIssue]:
    return validate_document("state", path)


def validate_release_lock(path: str | Path) -> list[ValidationIssue]:
    return validate_document("lock", path)


def validate_package_validation(path: str | Path) -> list[ValidationIssue]:
    return validate_document("validation", path)


def validate_manifest(path: str | Path) -> list[ValidationIssue]:
    return validate_document("manifest", path)


def validate_pointer(path: str | Path) -> list[ValidationIssue]:
    return validate_document("pointer", path)


def validate_archive(path: str | Path) -> list[ValidationIssue]:
    return validate_document("archive", path)


def validate_zip(path: str | Path) -> list[ValidationIssue]:
    path = Path(path)
    if not path.exists():
        return [ValidationIssue("FILE_NOT_FOUND", "$", f"file not found: {path}")]
    issues: list[ValidationIssue] = []
    try:
        with zipfile.ZipFile(path) as archive:
            bad = archive.testzip()
            if bad:
                issues.append(ValidationIssue("PACKAGE_CORRUPT", "$", f"corrupt member: {bad}"))
            names = archive.namelist()
            roots = {name.split("/", 1)[0] for name in names if name}
            if len(roots) != 1:
                issues.append(ValidationIssue("PACKAGE_NOT_SINGLE_ROOT", "$", "ZIP must contain exactly one root"))
            for name in names:
                if name.startswith("/") or ".." in Path(name).parts:
                    issues.append(ValidationIssue("PACKAGE_UNSAFE_PATH", "$", f"unsafe ZIP path: {name}"))
    except zipfile.BadZipFile as exc:
        issues.append(ValidationIssue("PACKAGE_INVALID_ZIP", "$", str(exc)))
    return sorted(set(issues))


__all__ = [
    "ValidationIssue", "sha256", "validate_state", "validate_release_lock",
    "validate_package_validation", "validate_manifest", "validate_pointer",
    "validate_archive", "validate_contract_files", "validate_zip",
    "verify_manifest_file", "validate_workspace",
]
