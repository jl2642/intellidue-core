from __future__ import annotations

import json
from pathlib import Path, PurePosixPath
import shutil
import tempfile
import zipfile
from typing import Any

from .archive_validation import inspect_archive
from .contracts import ValidationIssue, validate_object
from .manifest import inspect_release_tree, verify_manifest
from .package_models import PackageInspection, PackageLimits


def _read_json(path: Path, label: str) -> tuple[dict[str, Any] | None, list[ValidationIssue]]:
    try:
        value = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError:
        return None, [ValidationIssue("PACKAGE_ENVELOPE_MISSING", "$", f"missing {label}: {path.name}")]
    except UnicodeDecodeError as exc:
        return None, [ValidationIssue("TEXT_DECODE_ERROR", "$", f"{path.name}: {exc}")]
    except json.JSONDecodeError as exc:
        return None, [ValidationIssue("JSON_INVALID", f"$@{exc.lineno}:{exc.colno}", f"{path.name}: {exc.msg}")]
    if not isinstance(value, dict):
        return None, [ValidationIssue("DOCUMENT_NOT_OBJECT", "$", f"{path.name} must contain a JSON object")]
    return value, []


def validate_release_directory(root: str | Path, limits: PackageLimits | None = None) -> tuple[PackageInspection, list[ValidationIssue]]:
    limits = limits or PackageLimits()
    root = Path(root)
    issues: list[ValidationIssue] = []
    if not root.exists():
        return PackageInspection(str(root), "missing", "release", None, 0, 0, 0), [ValidationIssue("FILE_NOT_FOUND", "$", f"file not found: {root}")]
    if not root.is_dir():
        return PackageInspection(str(root), "file", "release", None, 0, 0, 0), [ValidationIssue("PACKAGE_NOT_DIRECTORY", "$", f"release package root is not a directory: {root}")]
    allowed_root = {"package.json", "manifest.json", "payload"}
    for child in sorted(root.iterdir(), key=lambda item: item.name):
        if child.name not in allowed_root:
            issues.append(ValidationIssue("PACKAGE_ENVELOPE_EXTRA", "$.root", f"unexpected package-root entry: {child.name}"))
    descriptor, current = _read_json(root / "package.json", "package.json")
    issues.extend(current)
    manifest, current = _read_json(root / "manifest.json", "manifest.json")
    issues.extend(current)
    payload = root / "payload"
    if not payload.is_dir():
        issues.append(ValidationIssue("PACKAGE_PAYLOAD_MISSING", "$.payload", "payload directory is missing"))
    if descriptor is not None:
        issues.extend(validate_object("package", descriptor))
        if descriptor.get("package_id") != root.name:
            issues.append(ValidationIssue("PACKAGE_ID_ROOT_MISMATCH", "$.package_id", "package_id must equal the package root directory name"))
        if descriptor.get("manifest_path") != "manifest.json" or descriptor.get("payload_path") != "payload":
            issues.append(ValidationIssue("PACKAGE_ENVELOPE_PATH_MISMATCH", "$", "package envelope paths must be manifest.json and payload"))
    if manifest is not None:
        issues.extend(validate_object("manifest", manifest))
        if manifest.get("root") != "payload":
            issues.append(ValidationIssue("PACKAGE_MANIFEST_ROOT_MISMATCH", "$.manifest.root", "release package manifest root must be payload"))
    if manifest is not None and payload.is_dir():
        issues.extend(verify_manifest(payload, manifest))
    if payload.is_dir():
        for nested in sorted(payload.rglob("*.zip")):
            _, nested_issues = inspect_archive(nested, limits)
            for issue in nested_issues:
                issues.append(ValidationIssue(issue.code, f"$.payload[{nested.relative_to(payload).as_posix()!r}]{issue.path[1:]}", issue.message))
    file_count = sum(1 for item in payload.rglob("*") if item.is_file()) if payload.is_dir() else 0
    total = sum(item.stat().st_size for item in payload.rglob("*") if item.is_file()) if payload.is_dir() else 0
    inspection = PackageInspection(str(root), "directory", "release", root.name, file_count + 2, total, sum(1 for item in payload.rglob("*.zip")) if payload.is_dir() else 0, descriptor)
    return inspection, sorted(set(issues))


def safe_extract_zip(path: Path, destination: Path, limits: PackageLimits) -> tuple[Path | None, list[ValidationIssue], PackageInspection]:
    inspection, issues = inspect_archive(path, limits)
    if issues:
        return None, issues, inspection
    destination.mkdir(parents=True, exist_ok=True)
    root_name = inspection.root
    assert root_name is not None
    with zipfile.ZipFile(path) as archive:
        for info in archive.infolist():
            member = PurePosixPath(info.filename)
            target = destination.joinpath(*member.parts)
            if info.is_dir():
                target.mkdir(parents=True, exist_ok=True)
                continue
            target.parent.mkdir(parents=True, exist_ok=True)
            with archive.open(info) as source, target.open("wb") as output:
                shutil.copyfileobj(source, output)
    return destination / root_name, [], inspection


def _inspect_generic_directory(path: Path, limits: PackageLimits) -> tuple[PackageInspection, list[ValidationIssue]]:
    issues = list(inspect_release_tree(path))
    files = [item for item in path.rglob("*") if item.is_file() and not item.is_symlink()]
    total = sum(item.stat().st_size for item in files)
    if len(files) > limits.max_entries:
        issues.append(ValidationIssue("PACKAGE_ENTRY_LIMIT", "$", f"directory has {len(files)} files; limit is {limits.max_entries}"))
    if total > limits.max_total_uncompressed:
        issues.append(ValidationIssue("PACKAGE_TOTAL_SIZE_LIMIT", "$", f"directory contains {total} bytes; limit is {limits.max_total_uncompressed}"))
    folded: dict[str, str] = {}
    nested_count = 0
    for item in files:
        relative = item.relative_to(path).as_posix()
        key = relative.casefold()
        if key in folded and folded[key] != relative:
            issues.append(ValidationIssue("PACKAGE_CASE_COLLISION", "$", f"case-insensitive collision: {folded[key]!r} and {relative!r}"))
        folded[key] = relative
        if item.stat().st_size > limits.max_member_uncompressed:
            issues.append(ValidationIssue("PACKAGE_MEMBER_SIZE_LIMIT", f"$.files[{relative!r}]", "file exceeds uncompressed size limit"))
        if item.suffix.lower() == ".zip":
            nested_count += 1
            nested_inspection, nested_issues = inspect_archive(item, limits)
            nested_count += nested_inspection.nested_archives
            for issue in nested_issues:
                issues.append(ValidationIssue(issue.code, f"$.files[{relative!r}]{issue.path[1:]}", issue.message))
    return PackageInspection(str(path), "directory", "directory", path.name, len(files), total, nested_count), sorted(set(issues))


def inspect_package(path: str | Path, *, profile: str = "auto", limits: PackageLimits | None = None) -> tuple[PackageInspection, list[ValidationIssue]]:
    limits = limits or PackageLimits()
    path = Path(path)
    if profile not in {"auto", "archive", "release"}:
        return PackageInspection(str(path), "unknown", profile, None, 0, 0, 0), [ValidationIssue("PACKAGE_PROFILE_INVALID", "$.profile", f"unsupported profile: {profile}")]
    if path.is_dir():
        has_envelope = (path / "package.json").exists() or (path / "manifest.json").exists() or (path / "payload").exists()
        if profile == "archive":
            return PackageInspection(str(path), "directory", "archive", path.name, 0, 0, 0), [ValidationIssue("PACKAGE_PROFILE_MISMATCH", "$", "archive profile requires a ZIP file")]
        if profile == "release" or has_envelope:
            return validate_release_directory(path, limits)
        return _inspect_generic_directory(path, limits)
    if not path.exists():
        return PackageInspection(str(path), "missing", profile, None, 0, 0, 0), [ValidationIssue("FILE_NOT_FOUND", "$", f"file not found: {path}")]
    if path.suffix.lower() != ".zip":
        return PackageInspection(str(path), "file", profile, None, 0, 0, 0), [ValidationIssue("PACKAGE_TYPE_UNSUPPORTED", "$", "package path must be a directory or .zip file")]
    archive_inspection, archive_issues = inspect_archive(path, limits)
    if archive_issues:
        return archive_inspection, archive_issues
    if profile == "archive":
        return archive_inspection, []
    with tempfile.TemporaryDirectory() as tmp:
        extracted_root, extract_issues, _ = safe_extract_zip(path, Path(tmp), limits)
        if extract_issues or extracted_root is None:
            return archive_inspection, extract_issues
        has_envelope = (extracted_root / "package.json").exists() or (extracted_root / "manifest.json").exists() or (extracted_root / "payload").exists()
        if profile == "release" or has_envelope:
            release_inspection, release_issues = validate_release_directory(extracted_root, limits)
            combined = PackageInspection(str(path), "zip", "release", archive_inspection.root, archive_inspection.entries, archive_inspection.total_uncompressed, archive_inspection.nested_archives, release_inspection.descriptor)
            return combined, release_issues
        return archive_inspection, []


def validate_package(path: str | Path, *, profile: str = "auto", limits: PackageLimits | None = None) -> list[ValidationIssue]:
    return inspect_package(path, profile=profile, limits=limits)[1]
