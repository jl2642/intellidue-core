from __future__ import annotations

import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ALLOWED_BINARY = {"tests/fixtures/synthetic_project/package.zip"}
PROHIBITED_SUFFIXES = {".pdf", ".docx", ".xlsx", ".xls", ".pptx", ".ppt", ".7z", ".rar"}
PROHIBITED_DIRS = {"private", "projects", "secrets", "__pycache__"}
TEXT_SUFFIXES = {".md", ".txt", ".py", ".toml", ".yml", ".yaml", ".json"}
MAX_FILE_BYTES = 2 * 1024 * 1024

def rel(path: Path) -> str:
    return path.relative_to(ROOT).as_posix()

def main() -> int:
    findings: list[str] = []
    private_patterns = [
        x.strip() for x in os.getenv("INTELLIDUE_PRIVATE_PATTERNS", "").split("|") if x.strip()
    ]

    for path in sorted(ROOT.rglob("*")):
        if ".git" in path.parts:
            continue
        rp = rel(path)
        if path.is_dir():
            if path.name in PROHIBITED_DIRS:
                findings.append(f"prohibited_directory:{rp}")
            continue

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
