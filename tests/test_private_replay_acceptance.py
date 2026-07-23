from __future__ import annotations

import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import unittest


ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/synthetic_private_project"
RUNNER = ROOT / "scripts/run_private_replay_acceptance.py"


class PrivateReplayAcceptanceRunnerTests(unittest.TestCase):
    def copy_project(self, root: Path, name: str) -> Path:
        target = root / name
        shutil.copytree(FIXTURE, target)
        return target

    def mutate_project(
        self,
        project: Path,
        *,
        release_id: str,
        project_id: str = "SYNTHETIC_PRIVATE_001",
        reader_text: str | None = None,
    ) -> None:
        adapter_path = project / "adapter.json"
        adapter = json.loads(adapter_path.read_text(encoding="utf-8"))
        adapter["project_id"] = project_id
        adapter["release_id"] = release_id
        adapter_path.write_text(
            json.dumps(adapter, indent=2) + "\n", encoding="utf-8"
        )

        for path in (project / "control").glob("*.json"):
            value = json.loads(path.read_text(encoding="utf-8"))
            value["project_id"] = project_id
            if path.name == "release_lock.json":
                value["release"] = release_id
            path.write_text(
                json.dumps(value, indent=2) + "\n", encoding="utf-8"
            )

        if reader_text is not None:
            (project / "products/reader/summary.txt").write_text(
                reader_text, encoding="utf-8"
            )

    def test_runner_completes_and_exports_only_anonymized_metrics(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            v1 = self.copy_project(root, "v1")
            v2 = self.copy_project(root, "v2")
            crash = self.copy_project(root, "crash")
            other = self.copy_project(root, "other")

            self.mutate_project(v1, release_id="private-v1")
            self.mutate_project(
                v2,
                release_id="private-v2",
                reader_text="Synthetic reader v2.\n",
            )
            self.mutate_project(
                crash,
                release_id="private-v3-crash",
                reader_text="Synthetic reader crash candidate.\n",
            )
            self.mutate_project(
                other,
                release_id="private-other",
                project_id="SYNTHETIC_PRIVATE_002",
            )

            runtime = root / "runtime"
            work = root / "work"
            output = root / "public-result.json"
            result = subprocess.run(
                [
                    sys.executable,
                    str(RUNNER),
                    "--v1-project",
                    str(v1),
                    "--v2-project",
                    str(v2),
                    "--crash-project",
                    str(crash),
                    "--contamination-project",
                    str(other),
                    "--runtime",
                    str(runtime),
                    "--work-dir",
                    str(work),
                    "--output",
                    str(output),
                    "--timestamp",
                    "2026-07-23T06:30:00Z",
                ],
                cwd=ROOT,
                text=True,
                capture_output=True,
                check=False,
            )
            self.assertEqual(result.returncode, 0, result.stderr or result.stdout)
            metrics = json.loads(output.read_text(encoding="utf-8"))
            self.assertEqual(metrics["result"], "PASS")
            self.assertEqual(metrics["deterministic_build"], "PASS")
            self.assertEqual(metrics["crash_fail_closed"], "PASS")
            self.assertEqual(metrics["recovery"], "PASS")
            self.assertEqual(metrics["cross_project_contamination"], "PASS")

            serialized = output.read_text(encoding="utf-8")
            self.assertNotIn("SYNTHETIC_PRIVATE_001", serialized)
            self.assertNotIn("SYNTHETIC_PRIVATE_002", serialized)
            self.assertNotIn(str(v1), serialized)
            self.assertNotIn(str(v2), serialized)
            self.assertNotIn(str(crash), serialized)
            self.assertNotIn(str(other), serialized)


if __name__ == "__main__":
    unittest.main()
