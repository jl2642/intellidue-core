import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intellidue_core.promotion import (
    PromotionError,
    SimulatedCrash,
    WorkspaceLock,
    promote_release,
    recover_workspace,
    rollback_release,
    validate_workspace,
)


class TestPromotionEngine(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.workspace = self.root / "workspace"
        self.candidates = self.root / "candidates"
        self.candidates.mkdir()

    def tearDown(self):
        self.temp.cleanup()

    def candidate(self, name: str, content: str) -> Path:
        path = self.candidates / name
        path.mkdir()
        (path / "payload.txt").write_text(content, encoding="utf-8")
        return path

    def read(self, relative: str):
        return json.loads((self.workspace / relative).read_text(encoding="utf-8"))

    def promote(self, release_id: str, content: str, tx: str, timestamp: str, **kwargs):
        return promote_release(
            self.workspace,
            self.candidate(f"candidate-{release_id}", content),
            release_id,
            transaction_id=tx,
            timestamp=timestamp,
            **kwargs,
        )

    def test_initial_and_second_promotion_update_all_pointers(self):
        first = self.promote("r1", "one", "tx1", "2026-07-23T00:00:01Z")
        self.assertEqual(first["archived_release"], None)
        self.assertEqual(self.read("pointers/current.json")["release_id"], "r1")
        self.assertEqual(self.read("pointers/last_success.json")["release_id"], "r1")
        self.assertEqual(self.read("pointers/archive.json")["entries"], [])
        self.assertEqual(validate_workspace(self.workspace), [])

        second = self.promote("r2", "two", "tx2", "2026-07-23T00:00:02Z", expected_current="r1")
        self.assertEqual(second["archived_release"], "r1")
        self.assertEqual(self.read("pointers/current.json")["release_id"], "r2")
        self.assertEqual(self.read("pointers/last_success.json")["release_id"], "r2")
        archive = self.read("pointers/archive.json")
        self.assertEqual([item["release_id"] for item in archive["entries"]], ["r1"])
        self.assertEqual(validate_workspace(self.workspace), [])

    def test_release_is_immutable_and_expected_current_is_enforced(self):
        self.promote("r1", "one", "tx1", "2026-07-23T00:00:01Z")
        with self.assertRaises(PromotionError) as ctx:
            promote_release(self.workspace, self.candidate("dup", "dup"), "r1", transaction_id="tx2")
        self.assertEqual(ctx.exception.issue.code, "RELEASE_IMMUTABLE")

        with self.assertRaises(PromotionError) as ctx:
            promote_release(self.workspace, self.candidate("r2", "two"), "r2", expected_current="wrong", transaction_id="tx3")
        self.assertEqual(ctx.exception.issue.code, "CURRENT_POINTER_CONFLICT")

    def test_workspace_lock_blocks_concurrent_writer(self):
        with WorkspaceLock(self.workspace):
            with self.assertRaises(PromotionError) as ctx:
                self.promote("r1", "one", "tx1", "2026-07-23T00:00:01Z")
        self.assertEqual(ctx.exception.issue.code, "PROMOTION_LOCKED")

    def test_injected_failure_rolls_back_release_and_pointers(self):
        self.promote("r1", "one", "tx1", "2026-07-23T00:00:01Z")
        candidate = self.candidate("candidate-r2", "two")
        with self.assertRaises(PromotionError) as ctx:
            promote_release(
                self.workspace,
                candidate,
                "r2",
                expected_current="r1",
                transaction_id="tx2",
                timestamp="2026-07-23T00:00:02Z",
                fail_at="after-current",
            )
        self.assertEqual(ctx.exception.issue.code, "INJECTED_FAILURE")
        self.assertEqual(self.read("pointers/current.json")["release_id"], "r1")
        self.assertFalse((self.workspace / "releases/r2").exists())
        self.assertFalse((self.workspace / "manifests/r2.manifest.json").exists())
        self.assertFalse((self.workspace / "transactions/active.json").exists())
        history = self.read("transactions/history/tx2.json")
        self.assertEqual(history["status"], "ROLLED_BACK")
        self.assertEqual(validate_workspace(self.workspace), [])

    def test_crash_recovery_restores_previous_state(self):
        self.promote("r1", "one", "tx1", "2026-07-23T00:00:01Z")
        candidate = self.candidate("candidate-r2", "two")
        with self.assertRaises(SimulatedCrash):
            promote_release(
                self.workspace,
                candidate,
                "r2",
                expected_current="r1",
                transaction_id="tx2",
                timestamp="2026-07-23T00:00:02Z",
                fail_at="crash-after-current",
            )
        self.assertTrue((self.workspace / "transactions/active.json").exists())
        self.assertEqual(self.read("pointers/current.json")["release_id"], "r2")
        self.assertIn("RECOVERY_REQUIRED", {issue.code for issue in validate_workspace(self.workspace)})

        result = recover_workspace(self.workspace)
        self.assertTrue(result["recovered"])
        self.assertEqual(self.read("pointers/current.json")["release_id"], "r1")
        self.assertFalse((self.workspace / "releases/r2").exists())
        self.assertFalse((self.workspace / "transactions/active.json").exists())
        self.assertEqual(validate_workspace(self.workspace), [])

    def test_manual_rollback_changes_current_without_deleting_releases(self):
        self.promote("r1", "one", "tx1", "2026-07-23T00:00:01Z")
        self.promote("r2", "two", "tx2", "2026-07-23T00:00:02Z", expected_current="r1")
        result = rollback_release(
            self.workspace,
            "r1",
            "regression detected",
            expected_current="r2",
            transaction_id="tx3",
            timestamp="2026-07-23T00:00:03Z",
        )
        self.assertEqual(result["archived_release"], "r2")
        self.assertEqual(self.read("pointers/current.json")["release_id"], "r1")
        self.assertEqual([item["release_id"] for item in self.read("pointers/archive.json")["entries"]], ["r2"])
        self.assertTrue((self.workspace / "releases/r1").is_dir())
        self.assertTrue((self.workspace / "releases/r2").is_dir())
        self.assertEqual(validate_workspace(self.workspace), [])


if __name__ == "__main__":
    unittest.main()
