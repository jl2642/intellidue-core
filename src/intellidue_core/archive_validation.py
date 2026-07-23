from __future__ import annotations

import io
from pathlib import Path, PurePosixPath
import stat
import zipfile
from typing import Any

from .contracts import ValidationIssue
from .package_models import PackageInspection, PackageLimits


def _safe_member_name(name: str) -> bool:
    if not name or "\\" in name or name.startswith("/"):
        return False
    path = PurePosixPath(name)
    return all(part not in {"", ".", ".."} for part in path.parts)


def _zipinfo_is_symlink(info: zipfile.ZipInfo) -> bool:
    mode = (info.external_attr >> 16) & 0xFFFF
    return stat.S_ISLNK(mode)


def _ratio(info: zipfile.ZipInfo) -> float:
    if info.file_size == 0:
        return 1.0
    if info.compress_size == 0:
        return float("inf")
    return info.file_size / info.compress_size


def _inspect_zip_archive(archive: zipfile.ZipFile, *, label: str, limits: PackageLimits, depth: int, require_single_root: bool) -> tuple[list[ValidationIssue], dict[str, Any]]:
    issues: list[ValidationIssue] = []
    nested_archives = 0
    infos = archive.infolist()
    if len(infos) > limits.max_entries:
        issues.append(ValidationIssue("PACKAGE_ENTRY_LIMIT", "$", f"archive has {len(infos)} entries; limit is {limits.max_entries}"))
    names = [info.filename for info in infos]
    if len(names) != len(set(names)):
        issues.append(ValidationIssue("PACKAGE_DUPLICATE_MEMBER", "$", "archive contains duplicate member names"))
    folded: dict[str, str] = {}
    for name in names:
        key = name.casefold()
        if key in folded and folded[key] != name:
            issues.append(ValidationIssue("PACKAGE_CASE_COLLISION", "$", f"case-insensitive collision: {folded[key]!r} and {name!r}"))
        folded[key] = name
    total = 0
    roots: set[str] = set()
    for index, info in enumerate(infos):
        path = f"$.entries[{index}]"
        name = info.filename
        if not _safe_member_name(name.rstrip("/")):
            issues.append(ValidationIssue("PACKAGE_UNSAFE_PATH", path, f"unsafe ZIP path: {name}"))
            continue
        roots.add(PurePosixPath(name).parts[0])
        if info.flag_bits & 0x1:
            issues.append(ValidationIssue("PACKAGE_ENCRYPTED_MEMBER", path, f"encrypted member is not allowed: {name}"))
        if _zipinfo_is_symlink(info):
            issues.append(ValidationIssue("PACKAGE_SYMLINK_MEMBER", path, f"symbolic link is not allowed: {name}"))
        if info.is_dir():
            continue
        total += info.file_size
        oversized = info.file_size > limits.max_member_uncompressed
        if oversized:
            issues.append(ValidationIssue("PACKAGE_MEMBER_SIZE_LIMIT", path, f"member exceeds uncompressed size limit: {name}"))
        if _ratio(info) > limits.max_compression_ratio:
            issues.append(ValidationIssue("PACKAGE_COMPRESSION_RATIO_LIMIT", path, f"member exceeds compression-ratio limit: {name}"))
        if name.lower().endswith(".zip"):
            nested_archives += 1
            if depth >= limits.max_nested_depth:
                issues.append(ValidationIssue("PACKAGE_NESTED_DEPTH_LIMIT", path, f"nested archive depth exceeds limit: {name}"))
            elif not oversized and not (info.flag_bits & 0x1):
                try:
                    nested_data = archive.read(info)
                except (RuntimeError, zipfile.BadZipFile, OSError) as exc:
                    issues.append(ValidationIssue("PACKAGE_NESTED_READ_FAILED", path, f"cannot read nested archive {name}: {exc}"))
                else:
                    nested_issues, nested_meta = _inspect_zip_bytes(nested_data, label=f"{label}!/{name}", limits=limits, depth=depth + 1, require_single_root=True)
                    nested_archives += nested_meta["nested_archives"]
                    for issue in nested_issues:
                        issues.append(ValidationIssue(issue.code, f"{path}{issue.path[1:]}", issue.message))
    if total > limits.max_total_uncompressed:
        issues.append(ValidationIssue("PACKAGE_TOTAL_SIZE_LIMIT", "$", f"archive expands to {total} bytes; limit is {limits.max_total_uncompressed}"))
    if require_single_root and len(roots) != 1:
        issues.append(ValidationIssue("PACKAGE_NOT_SINGLE_ROOT", "$", "ZIP must contain exactly one root"))
    try:
        bad = archive.testzip()
    except RuntimeError as exc:
        issues.append(ValidationIssue("PACKAGE_ENCRYPTED_MEMBER", "$", f"archive integrity check requires a password: {exc}"))
        bad = None
    if bad:
        issues.append(ValidationIssue("PACKAGE_CORRUPT", "$", f"corrupt member: {bad}"))
    root = next(iter(roots)) if len(roots) == 1 else None
    return sorted(set(issues)), {"entries": len(infos), "total_uncompressed": total, "root": root, "nested_archives": nested_archives}


def _inspect_zip_bytes(data: bytes, *, label: str, limits: PackageLimits, depth: int, require_single_root: bool) -> tuple[list[ValidationIssue], dict[str, Any]]:
    try:
        archive = zipfile.ZipFile(io.BytesIO(data))
    except zipfile.BadZipFile as exc:
        return [ValidationIssue("PACKAGE_INVALID_ZIP", "$", f"{label}: {exc}")], {"entries": 0, "total_uncompressed": 0, "root": None, "nested_archives": 0}
    with archive:
        return _inspect_zip_archive(archive, label=label, limits=limits, depth=depth, require_single_root=require_single_root)


def inspect_archive(path: str | Path, limits: PackageLimits | None = None) -> tuple[PackageInspection, list[ValidationIssue]]:
    limits = limits or PackageLimits()
    path = Path(path)
    if not path.exists():
        inspection = PackageInspection(str(path), "missing", "archive", None, 0, 0, 0)
        return inspection, [ValidationIssue("FILE_NOT_FOUND", "$", f"file not found: {path}")]
    if not path.is_file():
        inspection = PackageInspection(str(path), "directory", "archive", path.name, 0, 0, 0)
        return inspection, [ValidationIssue("PACKAGE_NOT_FILE", "$", f"archive path is not a file: {path}")]
    if path.stat().st_size > limits.max_total_uncompressed:
        inspection = PackageInspection(str(path), "zip", "archive", None, 0, 0, 0)
        return inspection, [ValidationIssue("PACKAGE_ARCHIVE_SIZE_LIMIT", "$", f"archive file exceeds size limit: {path.stat().st_size}")]
    try:
        with zipfile.ZipFile(path) as archive:
            issues, meta = _inspect_zip_archive(archive, label=str(path), limits=limits, depth=0, require_single_root=True)
    except zipfile.BadZipFile as exc:
        inspection = PackageInspection(str(path), "zip", "archive", None, 0, 0, 0)
        return inspection, [ValidationIssue("PACKAGE_INVALID_ZIP", "$", str(exc))]
    except OSError as exc:
        inspection = PackageInspection(str(path), "file", "archive", None, 0, 0, 0)
        return inspection, [ValidationIssue("PACKAGE_READ_FAILED", "$", str(exc))]
    inspection = PackageInspection(str(path), "zip", "archive", meta["root"], meta["entries"], meta["total_uncompressed"], meta["nested_archives"], None)
    return inspection, issues
