from __future__ import annotations

import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_BINARY = {"tests/fixtures/synthetic_project/package.zip"}
PROHIBITED_SUFFIXES = {".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".ppt", ".7z", ".rar"}
PROHIBITED_DIRS = {"private", "projects", "secrets", "__pycache__"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".toml", ".yml", ".yaml", ".json"}
MAX_FILE_BYTES = 2 * 1024 * 1024


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "-C", str(ROOT), "ls-files", "-z"],
        check=True,
        capture_output=True,
        text=True,
    )
    return [ROOT / item for item in result.stdout.split("\0") if item]


def main() -> int:
    findings: list[str] = []
    private_patterns = [
        item.strip()
        for item in os.getenv("INTELLIDUE_PRIVATE_PATTERNS", "").split("|")
        if item.strip()
    ]

    for path in tracked_files():
        rp = path.relative_to(ROOT).as_posix()

        if any(part in PROHIBITED_DIRS for part in Path(rp).parts):
            findings.append(f"prohibited_path:{rp}")
        if path.suffix == ".pyc":
            findings.append(f"generated_bytecode:{rp}")
        if path.suffix.lower() in PROHIBITED_SUFFIXES:
            findings.append(f"prohibited_binary:{rp}")
        if path.suffix.lower() == ".zip" and rp not in ALLOWED_BINARY:
            findings.append(f"unapproved_zip:{rp}")
        if path.stat().st_size > MAX_FILE_BYTES and rp not in ALLOWED_BINARY:
            findings.append(f"large_file:{rp}:{path.stat().st_size}")

        if path.name != "check_repo_hygiene.py" and path.suffix.lower() in TEXT_SUFFIXES:
            text = path.read_text(encoding="utf-8", errors="ignore")
            for pattern in private_patterns:
                if pattern.lower() in text.lower():
                    findings.append(f"configured_private_pattern:{pattern}:{rp}")

    if findings:
        print("\n".join(findings))
        return 1
    print("public-repository hygiene: PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
