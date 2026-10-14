#!/usr/bin/env python3
"""Regression tests for the secret scanner."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import check_secrets  # noqa: E402

# Fixtures are assembled at runtime so this file never matches the scanner itself.
GITHUB_TOKEN = "gh" + "p_" + "a" * 24
GITHUB_PAT = "github" + "_pat_" + "B" * 22
AWS_KEY = "AK" + "IA" + "0123456789ABCDEF"
PRIVATE_KEY = "-----BEGIN " + "RSA PRIVATE KEY-----"


class ScanFileTest(unittest.TestCase):
    def scan(self, content: str) -> list[str]:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "note.md"
            path.write_text(content, encoding="utf-8")
            with mock.patch.object(check_secrets, "REPO_ROOT", root):
                return check_secrets.scan_file(path)

    def test_detects_each_pattern(self) -> None:
        cases = {
            f"token = {GITHUB_TOKEN}\n": "note.md: possible GitHub token",
            f"pat: {GITHUB_PAT}\n": "note.md: possible GitHub fine-grained PAT",
            f"id={AWS_KEY}\n": "note.md: possible AWS access key id",
            f"{PRIVATE_KEY}\nabc\n": "note.md: possible Private key block",
        }
        for content, expected in cases.items():
            with self.subTest(expected=expected):
                self.assertEqual(self.scan(content), [expected])

    def test_clean_text_has_no_errors(self) -> None:
        self.assertEqual(self.scan("just prose, ghp_short and AKIA123\n"), [])

    def test_short_token_is_not_flagged(self) -> None:
        self.assertEqual(self.scan("gh" + "p_" + "a" * 19), [])

    def test_undecodable_file_is_skipped(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            path = root / "blob.bin"
            path.write_bytes(b"\xff\xfe\x00\x80" + AWS_KEY.encode())
            with mock.patch.object(check_secrets, "REPO_ROOT", root):
                self.assertEqual(check_secrets.scan_file(path), [])


class IterTextFilesTest(unittest.TestCase):
    def test_skips_excluded_dirs_files_and_images(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            for rel in (
                "a.md",
                "sub/b.txt",
                ".git/config",
                ".github/ci.yml",
                "sub/__pycache__/c.py",
                "check_secrets.py",
                "pic.png",
                "mod.pyc",
            ):
                f = root / rel
                f.parent.mkdir(parents=True, exist_ok=True)
                f.write_text("x", encoding="utf-8")
            with mock.patch.object(check_secrets, "SCAN_ROOTS", (root, root / "nope")):
                found = check_secrets.iter_text_files()
            self.assertEqual(
                [p.relative_to(root).as_posix() for p in found], ["a.md", "sub/b.txt"]
            )


class MainTest(unittest.TestCase):
    def run_main(self, content: str) -> int:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            (root / "f.md").write_text(content, encoding="utf-8")
            with (
                mock.patch.object(check_secrets, "REPO_ROOT", root),
                mock.patch.object(check_secrets, "SCAN_ROOTS", (root,)),
                mock.patch("sys.stdout"),
                mock.patch("sys.stderr"),
            ):
                return check_secrets.main()

    def test_returns_zero_when_clean(self) -> None:
        self.assertEqual(self.run_main("hello\n"), 0)

    def test_returns_one_on_finding(self) -> None:
        self.assertEqual(self.run_main(AWS_KEY), 1)


if __name__ == "__main__":
    unittest.main()
