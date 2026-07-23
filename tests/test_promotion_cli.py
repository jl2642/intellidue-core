import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


class TestPromotionCLI(unittest.TestCase):
    def test_cli_promote_validate_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            workspace = root / "workspace"
            candidate1 = root / "candidate-r1"
            candidate2 = root / "candidate-r2"
            candidate1.mkdir()
            candidate2.mkdir()
            (candidate1 / "payload.txt").write_text("one", encoding="utf-8")
            (candidate2 / "payload.txt").write_text("two", encoding="utf-8")
            env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}

            promote = subprocess.run(
                [sys.executable, "-m", "intellidue_core.cli", "promote", "--workspace", str(workspace), "--candidate", str(candidate1), "--release-id", "r1", "--transaction-id", "tx1", "--timestamp", "2026-07-23T00:00:01Z"],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(promote.returncode, 0, promote.stderr)
            self.assertTrue(json.loads(promote.stdout)["ok"])

            validate = subprocess.run(
                [sys.executable, "-m", "intellidue_core.cli", "validate-workspace", str(workspace)],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(validate.returncode, 0, validate.stdout)

            subprocess.run(
                [sys.executable, "-m", "intellidue_core.cli", "promote", "--workspace", str(workspace), "--candidate", str(candidate2), "--release-id", "r2", "--expected-current", "r1", "--transaction-id", "tx2", "--timestamp", "2026-07-23T00:00:02Z"],
                cwd=ROOT, env=env, check=True, capture_output=True, text=True,
            )
            rollback = subprocess.run(
                [sys.executable, "-m", "intellidue_core.cli", "rollback", "--workspace", str(workspace), "--release-id", "r1", "--reason", "test", "--expected-current", "r2", "--transaction-id", "tx3", "--timestamp", "2026-07-23T00:00:03Z"],
                cwd=ROOT, env=env, capture_output=True, text=True,
            )
            self.assertEqual(rollback.returncode, 0, rollback.stdout)
            self.assertEqual(json.loads(rollback.stdout)["result"]["release_id"], "r1")


if __name__ == "__main__":
    unittest.main()
