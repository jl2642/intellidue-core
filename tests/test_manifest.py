import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intellidue_core.manifest import build_manifest


class TestManifest(unittest.TestCase):
    def test_manifest_is_deterministic_and_schema_aligned(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp) / "fixture"
            root.mkdir()
            (root / "b.txt").write_text("b", encoding="utf-8")
            (root / "a.txt").write_text("a", encoding="utf-8")
            first = build_manifest(root)
            second = build_manifest(root)
            self.assertEqual(first, second)
            self.assertEqual(first["schema_version"], "1.0.0")
            self.assertEqual(first["root"], "fixture")
            self.assertEqual([item["path"] for item in first["files"]], ["a.txt", "b.txt"])
            for item in first["files"]:
                self.assertEqual(set(item), {"path", "size_bytes", "sha256"})
                self.assertEqual(len(item["sha256"]), 64)


if __name__ == "__main__":
    unittest.main()
