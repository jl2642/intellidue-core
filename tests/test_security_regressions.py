from __future__ import annotations

import io
import stat
import tempfile
import unittest
from pathlib import Path
import zipfile

from intellidue_core.package_models import PackageLimits
from intellidue_core.package_validation import inspect_package


class SecurityRegressionTests(unittest.TestCase):
    def _codes(self, archive_path: Path, *, limits: PackageLimits | None = None) -> set[str]:
        _, issues = inspect_package(archive_path, profile="archive", limits=limits)
        return {issue.code for issue in issues}

    def test_rejects_path_traversal(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "traversal.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("pkg/good.txt", "ok")
                archive.writestr("../escape.txt", "bad")
            self.assertIn("PACKAGE_UNSAFE_PATH", self._codes(archive_path))

    def test_rejects_duplicate_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "duplicate.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("pkg/data.txt", "one")
                archive.writestr("pkg/data.txt", "two")
            self.assertIn("PACKAGE_DUPLICATE_MEMBER", self._codes(archive_path))

    def test_rejects_case_collisions(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "case.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("pkg/Report.txt", "one")
                archive.writestr("pkg/report.txt", "two")
            self.assertIn("PACKAGE_CASE_COLLISION", self._codes(archive_path))

    def test_rejects_symbolic_link_members(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "symlink.zip"
            info = zipfile.ZipInfo("pkg/link")
            info.create_system = 3
            info.external_attr = (stat.S_IFLNK | 0o777) << 16
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr(info, "target.txt")
            self.assertIn("PACKAGE_SYMLINK_MEMBER", self._codes(archive_path))

    def test_recursively_rejects_unsafe_nested_zip(self):
        inner_bytes = io.BytesIO()
        with zipfile.ZipFile(inner_bytes, "w") as inner:
            inner.writestr("../nested-escape.txt", "bad")
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "outer.zip"
            with zipfile.ZipFile(archive_path, "w") as outer:
                outer.writestr("pkg/nested.zip", inner_bytes.getvalue())
            self.assertIn("PACKAGE_UNSAFE_PATH", self._codes(archive_path))

    def test_enforces_entry_limit(self):
        with tempfile.TemporaryDirectory() as tmp:
            archive_path = Path(tmp) / "entries.zip"
            with zipfile.ZipFile(archive_path, "w") as archive:
                archive.writestr("pkg/one.txt", "one")
                archive.writestr("pkg/two.txt", "two")
            limits = PackageLimits(max_entries=1)
            self.assertIn("PACKAGE_ENTRY_LIMIT", self._codes(archive_path, limits=limits))


if __name__ == "__main__":
    unittest.main()
