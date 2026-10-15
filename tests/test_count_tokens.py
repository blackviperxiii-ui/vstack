#!/usr/bin/env python3
"""Regression tests for the helpers in count_tokens (no network, no real tokens.json)."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _stubs import install_tiktoken_stub  # noqa: E402

install_tiktoken_stub()

import count_tokens  # noqa: E402


class WordEncoding:
    """Fake encoder: one token per whitespace-separated word."""

    def encode(self, text: str) -> list[int]:
        return list(range(len(text.split())))


def make_skill(root: Path, name: str, body: str | None) -> None:
    d = root / name
    d.mkdir()
    if body is not None:
        (d / "SKILL.md").write_text(body, encoding="utf-8")


def patched_report(root: Path):
    return (
        mock.patch.object(count_tokens, "SKILLS_DIR", root),
        mock.patch.object(
            count_tokens.tiktoken, "get_encoding", return_value=WordEncoding(), create=True
        ),
    )


class SkillDirsTest(unittest.TestCase):
    def test_missing_dir(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(count_tokens, "SKILLS_DIR", Path(tmp) / "nope"):
                self.assertEqual(count_tokens.skill_dirs(), [])

    def test_sorted_and_filtered(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skill(root, "zeta", "z")
            make_skill(root, "alpha", "a")
            make_skill(root, "empty", None)  # no SKILL.md
            (root / "stray.md").write_text("x", encoding="utf-8")  # not a dir
            with mock.patch.object(count_tokens, "SKILLS_DIR", root):
                names = [p.name for p in count_tokens.skill_dirs()]
        self.assertEqual(names, ["alpha", "zeta"])


class CountFileTest(unittest.TestCase):
    def test_tokens_and_bytes(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_text("one two three é", encoding="utf-8")
            # 4 words; "one two three " is 14 bytes, "é" is 2
            self.assertEqual(count_tokens.count_file(path, WordEncoding()), (4, 16))

    def test_invalid_utf8_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "SKILL.md"
            path.write_bytes(b"\xff\xfe")
            with self.assertRaises(UnicodeDecodeError):
                count_tokens.count_file(path, WordEncoding())


class BuildReportTest(unittest.TestCase):
    def test_report(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            root = Path(tmp)
            make_skill(root, "b", "x y")
            make_skill(root, "a", "hello")
            dirs_patch, enc_patch = patched_report(root)
            with dirs_patch, enc_patch as get_enc:
                report = count_tokens.build_report()
        get_enc.assert_called_once_with("cl100k_base")
        self.assertEqual(
            report,
            {
                "encoding": "cl100k_base",
                "skills": {
                    "a": {"tokens": 1, "bytes": 5},
                    "b": {"tokens": 2, "bytes": 3},
                },
            },
        )

    def test_no_skills(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dirs_patch, enc_patch = patched_report(Path(tmp))
            with dirs_patch, enc_patch:
                report = count_tokens.build_report()
        self.assertEqual(report, {"encoding": "cl100k_base", "skills": {}})


class WriteReportTest(unittest.TestCase):
    def test_exact_output_sorted_with_trailing_newline(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokens.json"
            count_tokens.write_report({"skills": {"a": 1}, "encoding": "e"}, path)
            text = path.read_text(encoding="utf-8")
        self.assertEqual(
            text,
            '{\n  "encoding": "e",\n  "skills": {\n    "a": 1\n  }\n}\n',
        )

    def test_overwrites_existing(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "tokens.json"
            path.write_text("stale", encoding="utf-8")
            count_tokens.write_report({}, path)
            self.assertEqual(path.read_text(encoding="utf-8"), "{}\n")


if __name__ == "__main__":
    unittest.main()
