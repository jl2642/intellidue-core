from __future__ import annotations

import hashlib
from pathlib import Path

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
    from .package_format import validate_package
    return validate_package(path, profile="archive")


__all__ = [
    "ValidationIssue", "sha256", "validate_state", "validate_release_lock",
    "validate_package_validation", "validate_manifest", "validate_pointer",
    "validate_archive", "validate_contract_files", "validate_zip",
    "verify_manifest_file", "validate_workspace",
]
