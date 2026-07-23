import json
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intellidue_core.contracts import validate_object
from intellidue_core.manifest import build_manifest, verify_manifest


class TestManifestReconciliation(unittest.TestCase):
    def test_manifest_reconciliation_detects_missing_extra_size_and_hash(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "candidate"
            root.mkdir()
            (root / "a.txt").write_text("alpha", encoding="utf-8")
            manifest = build_manifest(root, root_name="release-1")
            self.assertEqual(verify_manifest(root, manifest), [])

            (root / "a.txt").write_text("beta", encoding="utf-8")
            codes = {issue.code for issue in verify_manifest(root, manifest)}
            self.assertEqual({"MANIFEST_SIZE_MISMATCH", "MANIFEST_HASH_MISMATCH"}, codes)

            (root / "a.txt").unlink()
            (root / "extra.txt").write_text("x", encoding="utf-8")
            codes = {issue.code for issue in verify_manifest(root, manifest)}
            self.assertEqual({"MANIFEST_FILE_MISSING", "MANIFEST_FILE_EXTRA"}, codes)

    def test_pointer_and_archive_schemas_are_strict(self):
        pointer = {
            "schema_version": "1.0.0",
            "pointer_type": "CURRENT",
            "release_id": "r1",
            "release_path": "releases/r1",
            "manifest_path": "manifests/r1.manifest.json",
            "manifest_sha256": "a" * 64,
            "promoted_at": "2026-07-23T00:00:00Z",
            "transaction_id": "tx1",
        }
        self.assertEqual(validate_object("pointer", pointer), [])
        pointer["unexpected"] = True
        self.assertIn("SCHEMA_VIOLATION", {issue.code for issue in validate_object("pointer", pointer)})

        archive = {"schema_version": "1.0.0", "entries": []}
        self.assertEqual(validate_object("archive", archive), [])


if __name__ == "__main__":
    unittest.main()
