from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import re
import sys
import tomllib

TAG_PATTERN = re.compile(r"^core-v(?P<version>[0-9]+\.[0-9]+\.[0-9]+)$")
PROHIBITED_LICENSE_FILES = ("LICENSE", "LICENSE.md", "LICENSE.txt", "COPYING")


def _read_versions(root: Path) -> tuple[str, str]:
    project = tomllib.loads((root / "pyproject.toml").read_text(encoding="utf-8"))
    project_version = str(project["project"]["version"])
    init_text = (root / "src/intellidue_core/__init__.py").read_text(encoding="utf-8")
    match = re.search(r'__version__\s*=\s*["\']([^"\']+)["\']', init_text)
    if not match:
        raise ValueError("PACKAGE_VERSION_MISSING: __version__ was not found")
    return project_version, match.group(1)


def build_release_metadata(root: Path, tag: str, commit: str) -> dict[str, object]:
    match = TAG_PATTERN.fullmatch(tag)
    if not match:
        raise ValueError("RELEASE_TAG_INVALID: expected core-vX.Y.Z")
    project_version, package_version = _read_versions(root)
    tag_version = match.group("version")
    if project_version != package_version:
        raise ValueError("RELEASE_VERSION_MISMATCH: pyproject and package versions differ")
    if tag_version != project_version:
        raise ValueError("RELEASE_TAG_VERSION_MISMATCH: tag and package versions differ")
    if not (root / "NO_LICENSE.md").is_file():
        raise ValueError("NO_LICENSE_POLICY_MISSING: NO_LICENSE.md is required")
    present = [name for name in PROHIBITED_LICENSE_FILES if (root / name).exists()]
    if present:
        raise ValueError(f"LICENSE_POLICY_CONFLICT: unexpected license files: {', '.join(present)}")
    return {
        "schema_version": "1.0.0",
        "release_tag": tag,
        "core_version": project_version,
        "schema_contract_version": "1.0.0",
        "cli_contract_version": "1.0.0",
        "release_package_format": "1.0.0",
        "source_commit": commit,
        "license_posture": "NO_LICENSE_ALL_RIGHTS_RESERVED",
        "private_project_data_included": False,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Validate an IntelliDue Core release tag and emit release metadata.")
    parser.add_argument("--tag", required=True)
    parser.add_argument("--output", required=True)
    parser.add_argument("--commit", default=os.environ.get("GITHUB_SHA", "LOCAL"))
    parser.add_argument("--project-root", default=str(Path(__file__).resolve().parents[1]))
    args = parser.parse_args(argv)
    root = Path(args.project_root).resolve()
    try:
        metadata = build_release_metadata(root, args.tag, args.commit)
    except (OSError, KeyError, ValueError, tomllib.TOMLDecodeError) as exc:
        print(json.dumps({"ok": False, "error": str(exc)}, sort_keys=True))
        return 1
    output = Path(args.output)
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(metadata, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(json.dumps({"ok": True, "output": str(output), "metadata": metadata}, sort_keys=True))
    return 0


if __name__ == "__main__":
    sys.exit(main())
