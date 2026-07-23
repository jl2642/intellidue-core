import json
import unittest
from importlib.resources import files
from pathlib import Path

from jsonschema import Draft202012Validator

ROOT = Path(__file__).resolve().parents[1]


class TestSchemaSync(unittest.TestCase):
    def test_published_and_packaged_schemas_match_and_are_valid(self):
        package_root = files("intellidue_core.schemas")
        for public_schema in sorted((ROOT / "schemas").glob("*.json")):
            public_text = public_schema.read_text(encoding="utf-8")
            packaged = package_root.joinpath(public_schema.name).read_text(encoding="utf-8")
            self.assertEqual(public_text, packaged)
            Draft202012Validator.check_schema(json.loads(public_text))


if __name__ == "__main__":
    unittest.main()
