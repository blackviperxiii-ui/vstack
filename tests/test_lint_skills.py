#!/usr/bin/env python3
"""Regression tests for skill lint rules."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

import lint_skills  # noqa: E402
from lint_skills import (  # noqa: E402
    lint_skill,
    lint_upstream,
    parse_simple_yaml_frontmatter,
)


class TempDirTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.tmp = Path(tmp.name)

    def write(self, name: str, content: str) -> Path:
        path = self.tmp / name
        path.write_text(content, encoding="utf-8")
        return path


class LintSkillsTest(TempDirTestCase):
    def test_rejects_ignored_mode_frontmatter(self) -> None:
        path = self.write(
            "SKILL.md",
            "---\nname: fake-skill\ndescription: test\nmode: true\n---\n\n# x\n",
        )
        errors = lint_skill(path)
        self.assertTrue(any("mode" in err for err in errors))

    def test_rejects_banned_reminder_key(self) -> None:
        path = self.write(
            "SKILL.md",
            "---\nname: fake\ndescription: test\nreminder: hi\n---\n\n# x\n",
        )
        errors = lint_skill(path)
        self.assertEqual(len(errors), 1)
        self.assertIn("remove ignored frontmatter key 'reminder'", errors[0])

    def test_missing_name(self) -> None:
        path = self.write("SKILL.md", "---\ndescription: test\n---\n\n# x\n")
        errors = lint_skill(path)
        self.assertEqual(errors, [f"{path}: frontmatter missing 'name'"])

    def test_missing_description(self) -> None:
        path = self.write("SKILL.md", "---\nname: fake\n---\n\n# x\n")
        errors = lint_skill(path)
        self.assertEqual(errors, [f"{path}: frontmatter missing 'description'"])

    def test_missing_frontmatter(self) -> None:
        path = self.write("SKILL.md", "# no frontmatter\n")
        errors = lint_skill(path)
        self.assertEqual(
            errors, [f"{path}: missing YAML frontmatter delimited by ---"]
        )

    def test_happy_path(self) -> None:
        path = self.write(
            "SKILL.md", "---\nname: fake\ndescription: test\n---\n\n# x\n"
        )
        self.assertEqual(lint_skill(path), [])


class ParseFrontmatterTest(unittest.TestCase):
    def test_basic_pairs(self) -> None:
        self.assertEqual(
            parse_simple_yaml_frontmatter("name: a\ndescription: b c"),
            {"name": "a", "description": "b c"},
        )

    def test_blank_lines_and_comments_skipped(self) -> None:
        block = "\n# a comment\nname: a\n   \n  # indented comment\ndescription: b\n"
        self.assertEqual(
            parse_simple_yaml_frontmatter(block),
            {"name": "a", "description": "b"},
        )

    def test_quoted_values_stripped(self) -> None:
        block = 'name: "double"\ndescription: \'single\''
        self.assertEqual(
            parse_simple_yaml_frontmatter(block),
            {"name": "double", "description": "single"},
        )

    def test_lines_without_colon_ignored(self) -> None:
        self.assertEqual(
            parse_simple_yaml_frontmatter("junk line\nname: a\nmore junk"),
            {"name": "a"},
        )

    def test_last_duplicate_key_wins(self) -> None:
        self.assertEqual(
            parse_simple_yaml_frontmatter("name: first\nname: second"),
            {"name": "second"},
        )

    def test_value_may_contain_colon(self) -> None:
        self.assertEqual(
            parse_simple_yaml_frontmatter("description: use when: x"),
            {"description": "use when: x"},
        )

    def test_empty_key_ignored(self) -> None:
        self.assertEqual(parse_simple_yaml_frontmatter(": value"), {})


class LintUpstreamTest(TempDirTestCase):
    VALID = {
        "repo": "owner/repo",
        "path": "skills",
        "branch": "main",
        "last_synced_sha": "abc123",
        "mapping": {},
        "unported": [],
    }

    def lint(self, path: Path) -> list[str]:
        with mock.patch.object(lint_skills, "UPSTREAM_PATH", path):
            return lint_upstream()

    def write_json(self, data: object) -> Path:
        return self.write("UPSTREAM.json", json.dumps(data))

    def test_missing_file(self) -> None:
        path = self.tmp / "UPSTREAM.json"
        self.assertEqual(self.lint(path), [f"{path}: file not found"])

    def test_invalid_json(self) -> None:
        path = self.write("UPSTREAM.json", "{not json")
        errors = self.lint(path)
        self.assertEqual(len(errors), 1)
        self.assertIn(f"{path}: invalid JSON:", errors[0])

    def test_missing_required_fields(self) -> None:
        path = self.write_json({})
        errors = self.lint(path)
        for field in (
            "repo",
            "path",
            "branch",
            "last_synced_sha",
            "mapping",
            "unported",
        ):
            self.assertIn(f"{path}: missing field '{field}'", errors)
        self.assertEqual(len(errors), 6)

    def test_mapping_not_object(self) -> None:
        path = self.write_json({**self.VALID, "mapping": []})
        self.assertEqual(self.lint(path), [f"{path}: 'mapping' must be an object"])

    def test_unported_not_list(self) -> None:
        path = self.write_json({**self.VALID, "unported": {}})
        self.assertEqual(self.lint(path), [f"{path}: 'unported' must be a list"])

    def test_happy_path(self) -> None:
        path = self.write_json(self.VALID)
        self.assertEqual(self.lint(path), [])


if __name__ == "__main__":
    unittest.main()
