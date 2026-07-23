from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/synthetic_private_project"


class PrivateRuntimeCLITests(unittest.TestCase):
    def run_cli(self, *args):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "intellidue_core.cli", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_private_runtime_cli_lifecycle(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = root / "project"
            shutil.copytree(FIXTURE, project)
            runtime = root / "runtime"
            package = root / "private.zip"

            validate = self.run_cli("validate-private-project", "--project-root", str(project))
            self.assertEqual(validate.returncode, 0, validate.stdout)
            inspect = self.run_cli("inspect-private-project", "--project-root", str(project))
            self.assertEqual(json.loads(inspect.stdout)["inspection"]["project_id"], "SYNTHETIC_PRIVATE_001")
            build = self.run_cli("build-private-release", "--project-root", str(project), "--output", str(package), "--timestamp", "2026-07-23T06:00:00Z")
            self.assertEqual(build.returncode, 0, build.stdout)
            promote = self.run_cli("promote-private-release", "--project-root", str(project), "--runtime", str(runtime), "--transaction-id", "tx1", "--timestamp", "2026-07-23T06:00:01Z")
            self.assertEqual(promote.returncode, 0, promote.stdout)
            runtime_validate = self.run_cli("validate-private-runtime", "--runtime", str(runtime))
            self.assertEqual(runtime_validate.returncode, 0, runtime_validate.stdout)
            runtime_inspect = self.run_cli("inspect-private-runtime", "--runtime", str(runtime))
            payload = json.loads(runtime_inspect.stdout)
            self.assertEqual(payload["inspection"]["current_release"], "private-v1")
            version = self.run_cli("version")
            self.assertEqual(json.loads(version.stdout)["version"]["private_runtime_adapter"], "1.0.0")

    def test_private_project_validation_failure_is_typed(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp) / "project"
            shutil.copytree(FIXTURE, project)
            (project / "products/reader/summary.txt").unlink()
            result = self.run_cli("validate-private-project", "--project-root", str(project))
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertEqual(payload["issues"][0]["code"], "PRIVATE_PRODUCT_ROOT_EMPTY")


if __name__ == "__main__":
    unittest.main()
