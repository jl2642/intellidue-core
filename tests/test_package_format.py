import io
import json
import os
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
import zipfile

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "src"))

from intellidue_core.package_format import PackageLimits, build_release_package, extract_release_package, inspect_package, validate_package


class TestPackageFormat(unittest.TestCase):
    def source(self, root: Path, content: str = "alpha") -> Path:
        source = root / "source"
        source.mkdir()
        (source / "a.txt").write_text(content, encoding="utf-8")
        (source / "nested").mkdir()
        (source / "nested/b.txt").write_text("beta", encoding="utf-8")
        return source

    def test_release_package_build_is_deterministic_and_valid(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.source(root)
            first = root / "first.zip"
            second = root / "second.zip"
            kwargs = dict(package_id="pkg-1", release_id="r1", timestamp="2026-07-23T00:00:00Z")
            one = build_release_package(source, first, **kwargs)
            two = build_release_package(source, second, **kwargs)
            self.assertEqual(one["sha256"], two["sha256"])
            inspection, issues = inspect_package(first, profile="release")
            self.assertEqual(issues, [])
            self.assertEqual(inspection.profile, "release")
            self.assertEqual(inspection.descriptor["release_id"], "r1")

    def test_release_package_extracts_safely(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "release.zip"
            build_release_package(self.source(root), package, package_id="pkg-1", release_id="r1", timestamp="2026-07-23T00:00:00Z")
            result = extract_release_package(package, root / "out")
            target = Path(result["destination"])
            self.assertEqual((target / "payload/a.txt").read_text(), "alpha")
            with self.assertRaises(FileExistsError):
                extract_release_package(package, root / "out")
            extract_release_package(package, root / "out", overwrite=True)

    def test_release_directory_detects_manifest_tampering_and_extra_root(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "release.zip"
            build_release_package(self.source(root), package, package_id="pkg-1", release_id="r1", timestamp="2026-07-23T00:00:00Z")
            extracted = Path(extract_release_package(package, root / "out")["destination"])
            (extracted / "payload/a.txt").write_text("changed", encoding="utf-8")
            (extracted / "unexpected.txt").write_text("x", encoding="utf-8")
            codes = {issue.code for issue in validate_package(extracted, profile="release")}
            self.assertIn("MANIFEST_HASH_MISMATCH", codes)
            self.assertIn("PACKAGE_ENVELOPE_EXTRA", codes)

    def test_archive_rejects_unsafe_duplicate_case_collision_and_limits(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "bad.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("root/a.txt", "a")
                archive.writestr("root/a.txt", "b")
                archive.writestr("root/A.txt", "c")
                archive.writestr("../escape.txt", "x")
            codes = {issue.code for issue in validate_package(path, profile="archive", limits=PackageLimits(max_entries=2))}
            self.assertIn("PACKAGE_ENTRY_LIMIT", codes)
            self.assertIn("PACKAGE_DUPLICATE_MEMBER", codes)
            self.assertIn("PACKAGE_CASE_COLLISION", codes)
            self.assertIn("PACKAGE_UNSAFE_PATH", codes)

    def test_nested_zip_is_recursively_validated(self):
        with tempfile.TemporaryDirectory() as tmp:
            inner_bytes = io.BytesIO()
            with zipfile.ZipFile(inner_bytes, "w") as inner:
                inner.writestr("../escape.txt", "x")
            outer = Path(tmp) / "outer.zip"
            with zipfile.ZipFile(outer, "w") as archive:
                archive.writestr("root/nested.zip", inner_bytes.getvalue())
            codes = {issue.code for issue in validate_package(outer, profile="archive")}
            self.assertIn("PACKAGE_UNSAFE_PATH", codes)

    def test_auto_profile_preserves_legacy_structural_zip_validation(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "legacy.zip"
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("root/a.txt", "a")
            inspection, issues = inspect_package(path, profile="auto")
            self.assertEqual(issues, [])
            self.assertEqual(inspection.profile, "archive")

    def test_build_rejects_overwrite_and_symlink_source(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = self.source(root)
            package = root / "release.zip"
            build_release_package(source, package, package_id="pkg-1", release_id="r1", timestamp="2026-07-23T00:00:00Z")
            with self.assertRaises(FileExistsError):
                build_release_package(source, package, package_id="pkg-1", release_id="r1", timestamp="2026-07-23T00:00:00Z")
            if hasattr(os, "symlink"):
                link_source = root / "link-source"
                link_source.mkdir()
                (link_source / "target.txt").write_text("x")
                try:
                    os.symlink(link_source / "target.txt", link_source / "link.txt")
                except OSError:
                    return
                with self.assertRaises(ValueError):
                    build_release_package(link_source, root / "link.zip", package_id="pkg-2", release_id="r2")

    def test_release_root_must_match_package_id(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            package = root / "release.zip"
            build_release_package(self.source(root), package, package_id="pkg-1", release_id="r1", timestamp="2026-07-23T00:00:00Z")
            extracted = Path(extract_release_package(package, root / "out")["destination"])
            renamed = extracted.with_name("renamed")
            extracted.rename(renamed)
            codes = {issue.code for issue in validate_package(renamed, profile="release")}
            self.assertIn("PACKAGE_ID_ROOT_MISMATCH", codes)


class TestCLIContract(unittest.TestCase):
    def run_cli(self, *args):
        env = {**os.environ, "PYTHONPATH": str(ROOT / "src")}
        return subprocess.run([sys.executable, "-m", "intellidue_core.cli", *args], cwd=ROOT, env=env, capture_output=True, text=True)

    def test_version_and_validation_exit_codes(self):
        version = self.run_cli("version")
        self.assertEqual(version.returncode, 0)
        payload = json.loads(version.stdout)
        self.assertEqual(payload["cli_contract_version"], "1.0.0")
        self.assertEqual(payload["core_version"], "1.3.0")
        self.assertEqual(payload["exit_code"], 0)
        invalid = self.run_cli("validate-package", "missing.zip")
        self.assertEqual(invalid.returncode, 1)
        self.assertEqual(json.loads(invalid.stdout)["exit_code"], 1)
        usage = self.run_cli("validate-package")
        self.assertEqual(usage.returncode, 2)
        usage_payload = json.loads(usage.stdout)
        self.assertEqual(usage_payload["exit_code"], 2)
        self.assertEqual(usage_payload["issues"][0]["code"], "CLI_USAGE_ERROR")

    def test_build_inspect_extract_cli(self):
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            source = root / "source"
            source.mkdir()
            (source / "payload.txt").write_text("one")
            package = root / "release.zip"
            build = self.run_cli("build-package", "--source", str(source), "--output", str(package), "--package-id", "pkg-1", "--release-id", "r1", "--timestamp", "2026-07-23T00:00:00Z")
            self.assertEqual(build.returncode, 0, build.stdout + build.stderr)
            inspect = self.run_cli("inspect-package", str(package), "--profile", "release")
            self.assertEqual(inspect.returncode, 0, inspect.stdout)
            self.assertEqual(json.loads(inspect.stdout)["inspection"]["profile"], "release")
            extract = self.run_cli("extract-package", "--package", str(package), "--destination", str(root / "out"))
            self.assertEqual(extract.returncode, 0, extract.stdout)


if __name__ == "__main__":
    unittest.main()
