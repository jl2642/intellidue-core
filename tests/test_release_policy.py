from __future__ import annotations

import json
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts/release_gate.py"


class ReleasePolicyTests(unittest.TestCase):
    def test_valid_release_gate(self):
        with tempfile.TemporaryDirectory() as tmp:
            output = Path(tmp) / "release.json"
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--tag", "core-v1.4.0", "--output", str(output), "--commit", "abc123"],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertEqual(result.returncode, 0, result.stdout + result.stderr)
            metadata = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(metadata["core_version"], "1.4.0")
            self.assertEqual(metadata["license_posture"], "NO_LICENSE_ALL_RIGHTS_RESERVED")
            self.assertFalse(metadata["private_project_data_included"])

    def test_rejects_invalid_tag(self):
        with tempfile.TemporaryDirectory() as tmp:
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--tag", "v1.4.0", "--output", str(Path(tmp) / "release.json")],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RELEASE_TAG_INVALID", result.stdout)

    def test_rejects_version_mismatch(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            (project / "src/intellidue_core").mkdir(parents=True)
            shutil.copy2(ROOT / "NO_LICENSE.md", project / "NO_LICENSE.md")
            (project / "pyproject.toml").write_text('[project]\nname="x"\nversion="1.4.1"\n', encoding="utf-8")
            (project / "src/intellidue_core/__init__.py").write_text('__version__ = "1.4.0"\n', encoding="utf-8")
            result = subprocess.run(
                [sys.executable, str(SCRIPT), "--tag", "core-v1.4.1", "--output", str(project / "release.json"), "--project-root", str(project)],
                cwd=ROOT,
                text=True,
                capture_output=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("RELEASE_VERSION_MISMATCH", result.stdout)


if __name__ == "__main__":
    unittest.main()
