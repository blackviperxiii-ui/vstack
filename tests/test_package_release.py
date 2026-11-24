"""Release packaging ships tracked files only."""

from __future__ import annotations

import shutil
import subprocess
import tarfile
import tempfile
import unittest
import zipfile
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent


@unittest.skipUnless(
    all(shutil.which(tool) for tool in ("git", "zip", "sha256sum")),
    "git, zip and sha256sum are required",
)
class PackageReleaseTests(unittest.TestCase):
    def setUp(self) -> None:
        self._tmp = tempfile.TemporaryDirectory()
        self.addCleanup(self._tmp.cleanup)
        self.clone = Path(self._tmp.name) / "vstack"
        subprocess.run(
            ["git", "clone", "--quiet", "--no-hardlinks", str(REPO_ROOT), str(self.clone)],
            check=True,
        )
        # Package the script under test, not the last committed copy.
        shutil.copy2(
            REPO_ROOT / "scripts" / "package_release.sh",
            self.clone / "scripts" / "package_release.sh",
        )

    def _package(self) -> tuple[set[str], set[str]]:
        subprocess.run(
            [str(self.clone / "scripts" / "package_release.sh")],
            check=True,
            capture_output=True,
        )
        version = (self.clone / "VERSION").read_text(encoding="utf-8").strip()
        dist = self.clone / "dist"
        with tarfile.open(dist / f"vstack-{version}.tar.gz") as tar:
            tar_names = set(tar.getnames())
        with zipfile.ZipFile(dist / f"vstack-{version}.zip") as archive:
            zip_names = {name.rstrip("/") for name in archive.namelist()}
        self.prefix = f"vstack-{version}"
        return tar_names, zip_names

    def test_untracked_files_are_not_packaged(self) -> None:
        cache = self.clone / "scripts" / "__pycache__"
        cache.mkdir()
        (cache / "lint_skills.cpython-312.pyc").write_bytes(b"/home/someone/vstack")
        (self.clone / "skills" / "viper-mode" / "scratch.txt").write_text("x")
        modules = self.clone / "skills" / "stageshow" / "node_modules" / "left-pad"
        modules.mkdir(parents=True)
        (modules / "index.js").write_text("x")

        for names in self._package():
            leaked = sorted(
                name
                for name in names
                if "__pycache__" in name
                or name.endswith((".pyc", "scratch.txt"))
                or "node_modules" in name
            )
            self.assertEqual(leaked, [])

    def test_tracked_files_are_packaged(self) -> None:
        for names in self._package():
            for path in (
                "skills/viper-mode/SKILL.md",
                "scripts/lint_skills.py",
                ".claude-plugin/plugin.json",
                "install.sh",
                "VERSION",
            ):
                self.assertIn(f"{self.prefix}/{path}", names)


if __name__ == "__main__":
    unittest.main()
