from __future__ import annotations

import json
import os
from pathlib import Path
import shutil
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[1]
FIXTURE = ROOT / "tests/fixtures/synthetic_private_project"

from intellidue_core.package_format import inspect_package
from intellidue_core.private_runtime import (
    PrivateRuntimeError,
    build_private_release_package,
    inspect_private_project,
    inspect_private_runtime,
    promote_private_release,
    recover_private_runtime,
    rollback_private_release,
    validate_private_project,
    validate_private_runtime,
)
from intellidue_core.promotion import SimulatedCrash
from intellidue_core.promotion_apply import promote_release


class PrivateRuntimeTests(unittest.TestCase):
    def copy_fixture(self, root: Path, name: str = "project") -> Path:
        target = root / name
        shutil.copytree(FIXTURE, target)
        return target

    def config(self, project: Path) -> dict:
        return json.loads((project / "adapter.json").read_text(encoding="utf-8"))

    def save_config(self, project: Path, value: dict) -> None:
        (project / "adapter.json").write_text(json.dumps(value, indent=2) + "\n", encoding="utf-8")

    def test_valid_private_project_inspects_without_data_export(self):
        summary, issues = inspect_private_project(FIXTURE)
        self.assertEqual(issues, [])
        self.assertEqual(summary["project_id"], "SYNTHETIC_PRIVATE_001")
        self.assertEqual(summary["release_id"], "private-v1")
        self.assertFalse(summary["privacy"]["public_export_allowed"])
        self.assertEqual({item["class"] for item in summary["product_summary"]}, {"READER", "CONTROL", "SUPPLEMENTAL"})
        self.assertEqual(validate_private_project(FIXTURE), [])

    def test_private_release_package_is_deterministic_and_strict(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            one = root / "one.zip"
            two = root / "two.zip"
            kwargs = {"timestamp": "2026-07-23T05:00:00Z"}
            first = build_private_release_package(FIXTURE, one, **kwargs)
            second = build_private_release_package(FIXTURE, two, **kwargs)
            self.assertEqual(first["sha256"], second["sha256"])
            self.assertEqual(first["project_id"], "SYNTHETIC_PRIVATE_001")
            inspection, issues = inspect_package(one, profile="release")
            self.assertEqual(issues, [])
            self.assertEqual(inspection.descriptor["release_id"], "private-v1")

    def test_path_escape_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_fixture(Path(tmp))
            config = self.config(project)
            config["control"]["state"] = "../outside.json"
            self.save_config(project, config)
            self.assertIn("SCHEMA_VIOLATION", {issue.code for issue in validate_private_project(project)})

    def test_project_identity_mismatch_is_rejected(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_fixture(Path(tmp))
            state_path = project / "control/current_project_state.json"
            state = json.loads(state_path.read_text())
            state["project_id"] = "OTHER_PRIVATE_001"
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            codes = {issue.code for issue in validate_private_project(project)}
            self.assertIn("CONTRACT_PROJECT_ID_MISMATCH", codes)
            self.assertIn("PRIVATE_PROJECT_ID_MISMATCH", codes)

    def test_required_reader_or_control_cannot_be_empty(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_fixture(Path(tmp))
            (project / "products/reader/summary.txt").unlink()
            self.assertIn("PRIVATE_PRODUCT_ROOT_EMPTY", {issue.code for issue in validate_private_project(project)})

    def test_product_roots_cannot_overlap(self):
        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_fixture(Path(tmp))
            config = self.config(project)
            config["product_roots"][1]["path"] = "products/reader/sub"
            (project / "products/reader/sub").mkdir()
            (project / "products/reader/sub/workpaper.txt").write_text("x")
            self.save_config(project, config)
            self.assertIn("PRIVATE_PRODUCT_ROOT_OVERLAP", {issue.code for issue in validate_private_project(project)})

    def test_symlink_product_is_rejected(self):
        if not hasattr(os, "symlink"):
            self.skipTest("symlinks unavailable")
        with tempfile.TemporaryDirectory() as tmp:
            project = self.copy_fixture(Path(tmp))
            target = project / "products/reader/summary.txt"
            link = project / "products/control/reader-link.txt"
            try:
                os.symlink(target, link)
            except OSError:
                self.skipTest("symlink creation not permitted")
            self.assertIn("PRIVATE_PRODUCT_SYMLINK", {issue.code for issue in validate_private_project(project)})

    def test_promote_second_release_validate_inspect_and_rollback(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.copy_fixture(root)
            runtime = root / "runtime"
            first = promote_private_release(project, runtime, transaction_id="tx1", timestamp="2026-07-23T05:00:01Z")
            self.assertEqual(first["release_id"], "private-v1")
            self.assertEqual(validate_private_runtime(runtime), [])

            config = self.config(project)
            config["release_id"] = "private-v2"
            self.save_config(project, config)
            (project / "products/reader/summary.txt").write_text("Synthetic reader v2.\n")
            second = promote_private_release(project, runtime, expected_current="private-v1", transaction_id="tx2", timestamp="2026-07-23T05:00:02Z")
            self.assertEqual(second["release_id"], "private-v2")
            summary, issues = inspect_private_runtime(runtime)
            self.assertEqual(issues, [])
            self.assertEqual(summary["current_release"], "private-v2")
            self.assertEqual(summary["archived_releases"], ["private-v1"])

            result = rollback_private_release(runtime, "private-v1", "synthetic regression", expected_current="private-v2", transaction_id="tx3", timestamp="2026-07-23T05:00:03Z")
            self.assertEqual(result["release_id"], "private-v1")
            self.assertEqual(validate_private_runtime(runtime), [])

    def test_runtime_rejects_cross_project_contamination(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.copy_fixture(root, "project-one")
            runtime = root / "runtime"
            promote_private_release(project, runtime, transaction_id="tx1", timestamp="2026-07-23T05:01:01Z")
            other = self.copy_fixture(root, "project-two")
            config = self.config(other)
            config["project_id"] = "SYNTHETIC_PRIVATE_002"
            config["release_id"] = "private-other"
            self.save_config(other, config)
            for path in (other / "control").glob("*.json"):
                obj = json.loads(path.read_text())
                obj["project_id"] = "SYNTHETIC_PRIVATE_002"
                path.write_text(json.dumps(obj, indent=2) + "\n")
            with self.assertRaises(PrivateRuntimeError) as ctx:
                promote_private_release(other, runtime, expected_current="private-v1", transaction_id="tx2")
            self.assertEqual(ctx.exception.issue.code, "PRIVATE_RUNTIME_PROJECT_CONFLICT")

    def test_runtime_detects_control_tampering(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.copy_fixture(root)
            runtime = root / "runtime"
            promote_private_release(project, runtime, transaction_id="tx1", timestamp="2026-07-23T05:02:01Z")
            state_path = runtime / "core/releases/private-v1/control/current_project_state.json"
            state = json.loads(state_path.read_text())
            state["project_name"] = "Tampered"
            state_path.write_text(json.dumps(state, indent=2) + "\n")
            codes = {issue.code for issue in validate_private_runtime(runtime)}
            self.assertIn("MANIFEST_HASH_MISMATCH", codes)
            self.assertIn("PRIVATE_CONTROL_HASH_MISMATCH", codes)

    def test_recover_private_runtime_after_core_crash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            project = self.copy_fixture(root)
            runtime = root / "runtime"
            promote_private_release(project, runtime, transaction_id="tx1", timestamp="2026-07-23T05:03:01Z")
            config = self.config(project)
            config["release_id"] = "private-v2"
            self.save_config(project, config)
            package = root / "private-v2.zip"
            build_private_release_package(project, package, timestamp="2026-07-23T05:03:02Z")
            import zipfile
            extracted = root / "extracted"
            with zipfile.ZipFile(package) as archive:
                archive.extractall(extracted)
            candidate = extracted / "private-v2/payload"
            with self.assertRaises(SimulatedCrash):
                promote_release(runtime / "core", candidate, "private-v2", expected_current="private-v1", transaction_id="tx2", timestamp="2026-07-23T05:03:02Z", fail_at="crash-after-current")
            self.assertIn("RECOVERY_REQUIRED", {issue.code for issue in validate_private_runtime(runtime)})
            result = recover_private_runtime(runtime)
            self.assertTrue(result["recovered"])
            self.assertEqual(validate_private_runtime(runtime), [])


if __name__ == "__main__":
    unittest.main()
