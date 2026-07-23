import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intellidue_core.contracts import validate_contract_files, validate_contract_objects, validate_object
from intellidue_core.validators import validate_package_validation, validate_release_lock, validate_state, validate_zip


class TestValidators(unittest.TestCase):
    def setUp(self):
        self.fx = ROOT / "tests/fixtures/synthetic_project"
        self.state = json.loads((self.fx / "current_project_state.json").read_text())
        self.lock = json.loads((self.fx / "release_lock.json").read_text())
        self.validation = json.loads((self.fx / "package_validation.json").read_text())

    def test_positive_documents_and_contract(self):
        self.assertEqual(validate_state(self.fx / "current_project_state.json"), [])
        self.assertEqual(validate_release_lock(self.fx / "release_lock.json"), [])
        self.assertEqual(validate_package_validation(self.fx / "package_validation.json"), [])
        self.assertEqual(validate_zip(self.fx / "package.zip"), [])
        self.assertEqual(validate_contract_files(self.fx / "current_project_state.json", self.fx / "release_lock.json", self.fx / "package_validation.json"), [])

    def test_strict_schema_rejects_extra_property(self):
        self.state["unexpected"] = True
        self.assertIn("SCHEMA_VIOLATION", {issue.code for issue in validate_object("state", self.state)})

    def test_missing_and_unsupported_schema_versions_are_typed(self):
        self.state.pop("schema_version")
        self.assertIn("SCHEMA_VERSION_MISSING", {issue.code for issue in validate_object("state", self.state)})
        self.state["schema_version"] = "2.0.0"
        self.assertEqual([issue.code for issue in validate_object("state", self.state)], ["SCHEMA_VERSION_UNSUPPORTED"])

    def test_pass_validation_rejects_failed_tests(self):
        self.validation["tests"]["failed"] = 1
        self.assertIn("SCHEMA_VIOLATION", {issue.code for issue in validate_object("validation", self.validation)})

    def test_contract_mismatches_are_typed(self):
        mutations = [
            (self.lock, "project_id", "OTHER_PROJECT_001", "CONTRACT_PROJECT_ID_MISMATCH"),
            (self.lock, "status", "ARCHIVED", "CONTRACT_STATUS_MISMATCH"),
            (self.lock, "accepted_product_class", "FINAL_FULL_DD", "CONTRACT_PRODUCT_CLASS_MISMATCH"),
            (self.lock, "next", "Different next", "CONTRACT_NEXT_MISMATCH"),
        ]
        for document, key, value, expected in mutations:
            with self.subTest(expected=expected):
                original = document[key]
                document[key] = value
                self.assertIn(expected, {issue.code for issue in validate_contract_objects(self.state, self.lock, self.validation)})
                document[key] = original

        boundary_mutations = [
            ("critical_gates_open", 3, "CONTRACT_GATE_COUNT_MISMATCH"),
            ("restricted_outputs", ["Another output"], "CONTRACT_RESTRICTED_OUTPUTS_MISMATCH"),
            ("decision_ready", True, "CONTRACT_DECISION_READY_MISMATCH"),
        ]
        for key, value, expected in boundary_mutations:
            with self.subTest(expected=expected):
                original = self.lock["hard_controls"][key]
                self.lock["hard_controls"][key] = value
                self.assertIn(expected, {issue.code for issue in validate_contract_objects(self.state, self.lock, self.validation)})
                self.lock["hard_controls"][key] = original

    def test_decision_ready_requires_closed_boundaries(self):
        self.state["project_boundaries"]["decision_ready"] = True
        codes = {issue.code for issue in validate_object("state", self.state)}
        self.assertEqual({"DECISION_READY_OPEN_GATES", "DECISION_READY_RESTRICTED_OUTPUTS"}, codes)

    def test_final_full_dd_requires_closed_boundaries(self):
        self.state["accepted_product_class"] = "FINAL_FULL_DD"
        self.lock["accepted_product_class"] = "FINAL_FULL_DD"
        codes = {issue.code for issue in validate_contract_objects(self.state, self.lock, self.validation)}
        self.assertEqual({"FINAL_DD_OPEN_GATES", "FINAL_DD_RESTRICTED_OUTPUTS", "FINAL_DD_NOT_DECISION_READY"}, codes)

    def test_manifest_semantics(self):
        manifest = {
            "schema_version": "1.0.0",
            "root": "fixture",
            "files": [
                {"path": "b.txt", "size_bytes": 1, "sha256": "b" * 64},
                {"path": "a.txt", "size_bytes": 1, "sha256": "a" * 64},
            ],
        }
        self.assertEqual([issue.code for issue in validate_object("manifest", manifest)], ["MANIFEST_PATH_ORDER"])
        manifest["files"] = [manifest["files"][1], manifest["files"][1]]
        self.assertEqual([issue.code for issue in validate_object("manifest", manifest)], ["MANIFEST_DUPLICATE_PATH"])

    def test_cli_error_contract_and_exit_code(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "invalid.json"
            path.write_text("{}", encoding="utf-8")
            result = subprocess.run(
                [sys.executable, "-m", "intellidue_core.cli", "validate-state", str(path)],
                cwd=ROOT,
                env={**dict(__import__("os").environ), "PYTHONPATH": str(ROOT / "src")},
                capture_output=True,
                text=True,
            )
            payload = json.loads(result.stdout)
            self.assertEqual(result.returncode, 1)
            self.assertFalse(payload["ok"])
            self.assertEqual(payload["contract_version"], "1.0.0")
            self.assertTrue(payload["issues"])
            self.assertEqual(set(payload["issues"][0]), {"code", "path", "message", "severity"})


if __name__ == "__main__":
    unittest.main()
