from __future__ import annotations

from datetime import datetime, timezone
import os
from pathlib import Path
import re
import shutil
import tempfile
import zipfile
from typing import Any

from .contracts import SCHEMA_VERSION, validate_object
from .manifest import build_manifest, canonical_json_bytes, file_hash, inspect_release_tree
from .package_models import PACKAGE_FORMAT_VERSION, PackageLimits
from .package_validation import inspect_package, safe_extract_zip


def _now() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def _safe_identifier(value: str, label: str) -> None:
    if not re.fullmatch(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}", value):
        raise ValueError(f"invalid {label}: {value!r}")


def build_release_package(source: str | Path, output: str | Path, *, package_id: str, release_id: str, timestamp: str | None = None, overwrite: bool = False) -> dict[str, Any]:
    _safe_identifier(package_id, "package_id")
    _safe_identifier(release_id, "release_id")
    source = Path(source)
    output = Path(output)
    if not source.is_dir():
        raise ValueError(f"source is not a directory: {source}")
    if output.suffix.lower() != ".zip":
        raise ValueError("output must have a .zip suffix")
    if output.exists() and not overwrite:
        raise FileExistsError(f"output already exists: {output}")
    source_issues = inspect_release_tree(source)
    if source_issues:
        raise ValueError("; ".join(f"{issue.code}:{issue.message}" for issue in source_issues))
    created_at = timestamp or _now()
    with tempfile.TemporaryDirectory() as tmp:
        package_root = Path(tmp) / package_id
        payload = package_root / "payload"
        shutil.copytree(source, payload)
        manifest = build_manifest(payload, root_name="payload")
        descriptor = {"schema_version": SCHEMA_VERSION, "package_format_version": PACKAGE_FORMAT_VERSION, "package_id": package_id, "release_id": release_id, "package_class": "PRODUCT_RELEASE", "created_at": created_at, "payload_path": "payload", "manifest_path": "manifest.json"}
        issues = validate_object("package", descriptor)
        if issues:
            raise ValueError("; ".join(f"{issue.code}:{issue.message}" for issue in issues))
        (package_root / "package.json").write_bytes(canonical_json_bytes(descriptor))
        (package_root / "manifest.json").write_bytes(canonical_json_bytes(manifest))
        output.parent.mkdir(parents=True, exist_ok=True)
        temporary = output.with_name(f".{output.name}.{os.getpid()}.tmp")
        temporary.unlink(missing_ok=True)
        fixed = (1980, 1, 1, 0, 0, 0)
        with zipfile.ZipFile(temporary, "w", zipfile.ZIP_DEFLATED, compresslevel=9) as archive:
            for path in sorted(item for item in package_root.rglob("*") if item.is_file()):
                relative = path.relative_to(package_root.parent).as_posix()
                info = zipfile.ZipInfo(relative, date_time=fixed)
                info.compress_type = zipfile.ZIP_DEFLATED
                info.external_attr = 0o100644 << 16
                archive.writestr(info, path.read_bytes())
        os.replace(temporary, output)
    inspection, validation_issues = inspect_package(output, profile="release")
    if validation_issues:
        output.unlink(missing_ok=True)
        raise ValueError("; ".join(f"{issue.code}:{issue.message}" for issue in validation_issues))
    return {"package": str(output), "sha256": file_hash(output), "package_id": package_id, "release_id": release_id, "created_at": created_at, "entries": inspection.entries, "total_uncompressed": inspection.total_uncompressed}


def extract_release_package(package: str | Path, destination: str | Path, *, overwrite: bool = False, limits: PackageLimits | None = None) -> dict[str, Any]:
    limits = limits or PackageLimits()
    package = Path(package)
    destination = Path(destination)
    inspection, issues = inspect_package(package, profile="release", limits=limits)
    if issues:
        raise ValueError("; ".join(f"{issue.code}:{issue.message}" for issue in issues))
    root_name = inspection.root
    assert root_name is not None
    target = destination / root_name
    if target.exists():
        if not overwrite:
            raise FileExistsError(f"destination already exists: {target}")
        shutil.rmtree(target)
    destination.mkdir(parents=True, exist_ok=True)
    with tempfile.TemporaryDirectory(dir=destination) as tmp:
        extracted_root, extract_issues, _ = safe_extract_zip(package, Path(tmp), limits)
        if extract_issues or extracted_root is None:
            raise ValueError("; ".join(f"{issue.code}:{issue.message}" for issue in extract_issues))
        os.replace(extracted_root, target)
    return {"destination": str(target), "package_id": inspection.descriptor["package_id"] if inspection.descriptor else None}
