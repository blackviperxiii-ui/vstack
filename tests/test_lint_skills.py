#!/usr/bin/env python3
"""Regression tests for skill lint rules."""

from __future__ import annotations

import io
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
    lint_mcp_json,
    lint_procedural,
    lint_retry_filler,
    lint_skill,
    lint_skill_length,
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


class LintSkillsMainTest(TempDirTestCase):
    def test_main_ok_when_skills_and_upstream_valid(self) -> None:
        skills = self.tmp / "skills" / "demo"
        skills.mkdir(parents=True)
        skills.joinpath("SKILL.md").write_text(
            "---\nname: demo\ndescription: ok\n---\n\n# x\n", encoding="utf-8"
        )
        upstream = self.write(
            "UPSTREAM.json", json.dumps(LintUpstreamTest.VALID)
        )
        with (
            mock.patch.object(lint_skills, "SKILLS_DIR", self.tmp / "skills"),
            mock.patch.object(lint_skills, "UPSTREAM_PATH", upstream),
            mock.patch("sys.stdout", new_callable=io.StringIO) as out,
        ):
            self.assertEqual(lint_skills.main(), 0)
        self.assertIn("lint OK", out.getvalue())

    def test_main_fails_when_name_differs_from_folder(self) -> None:
        skill = self.tmp / "skills" / "demo"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            "---\nname: other\ndescription: ok\n---\n\n# x\n", encoding="utf-8"
        )
        upstream = self.write("UPSTREAM.json", json.dumps(LintUpstreamTest.VALID))
        with (
            mock.patch.object(lint_skills, "SKILLS_DIR", self.tmp / "skills"),
            mock.patch.object(lint_skills, "UPSTREAM_PATH", upstream),
            mock.patch("sys.stderr", new_callable=io.StringIO) as err,
        ):
            self.assertEqual(lint_skills.main(), 1)
        self.assertIn("must match folder 'demo'", err.getvalue())

    def test_main_returns_one_on_errors(self) -> None:
        with (
            mock.patch.object(lint_skills, "SKILLS_DIR", self.tmp / "nope"),
            mock.patch.object(lint_skills, "UPSTREAM_PATH", self.tmp / "nope.json"),
            mock.patch("sys.stderr", new_callable=io.StringIO),
        ):
            self.assertEqual(lint_skills.main(), 1)


class SkillQualityTest(TempDirTestCase):
    FRONT = "---\nname: demo\ndescription: ok\n---\n"

    def write_lines(self, count: int) -> Path:
        header_lines = self.FRONT.splitlines()
        extra = count - len(header_lines)
        body = "\n".join("body" for _ in range(extra))
        text = self.FRONT + (body + "\n" if extra else "")
        path = self.write("SKILL.md", text)
        self.assertEqual(len(path.read_text(encoding="utf-8").splitlines()), count)
        return path

    def skill(self, name: str, body: str) -> Path:
        path = self.tmp / name / "SKILL.md"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(body, encoding="utf-8")
        return path

    def test_fails_when_skill_has_500_lines(self) -> None:
        path = self.write_lines(500)
        errors = lint_skill_length(path)
        self.assertEqual(errors, [f"{path}: SKILL.md has 500 lines, limit is 499"])

    def test_passes_when_skill_has_499_lines(self) -> None:
        path = self.write_lines(499)
        self.assertEqual(lint_skill_length(path), [])

    def test_fails_when_mcp_json_present(self) -> None:
        skill = self.tmp / "skills" / "demo"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            self.FRONT + "\n# Demo\n", encoding="utf-8"
        )
        mcp = skill / ".mcp.json"
        mcp.write_text("{}\n", encoding="utf-8")
        upstream = self.write("UPSTREAM.json", json.dumps(LintUpstreamTest.VALID))
        with (
            mock.patch.object(lint_skills, "SKILLS_DIR", self.tmp / "skills"),
            mock.patch.object(lint_skills, "UPSTREAM_PATH", upstream),
            mock.patch("sys.stderr", new_callable=io.StringIO) as err,
        ):
            self.assertEqual(lint_skills.main(), 1)
        self.assertIn(f"{mcp}: skill directory must not contain .mcp.json", err.getvalue())

    def test_passes_when_mcp_json_absent(self) -> None:
        skill = self.tmp / "skills" / "demo"
        skill.mkdir(parents=True)
        skill.joinpath("SKILL.md").write_text(
            self.FRONT + "\n# Demo\n", encoding="utf-8"
        )
        self.assertEqual(lint_mcp_json(skill), [])

    def test_fails_when_try_again_is_in_recovery(self) -> None:
        for phrase in ("try again", "retry again", "just retry"):
            with self.subTest(phrase=phrase):
                path = self.skill(
                    "demo",
                    self.FRONT
                    + "\n# Demo\n\n## Error recovery\n\n"
                    + f"If the command fails, {phrase}.\n",
                )
                errors = lint_retry_filler(path)
                self.assertEqual(
                    errors,
                    [
                        f"{path}: low-signal retry filler {phrase!r} in an error-recovery section"
                    ],
                )

    def test_passes_when_try_again_is_outside_recovery(self) -> None:
        path = self.skill(
            "demo",
            self.FRONT
            + "\n# Demo\n\ntry again is narration here, not a fix.\n\n"
            + "## Error recovery\n\nRead the error text and fix the command.\n",
        )
        self.assertEqual(lint_retry_filler(path), [])

    def test_fails_when_procedural_skill_misses_steps(self) -> None:
        path = self.skill(
            "demo",
            self.FRONT
            + """
# Demo

## Workflow

- Read the skill file.
- Update the lint script.

```bash
python3 scripts/lint_skills.py
```

## Error recovery

Fix the skill named in the error, then rerun the command.
""",
        )
        self.assertEqual(
            lint_procedural(path),
            [f"{path}: procedural skill needs numbered single-goal steps"],
        )

    def test_fails_when_procedural_skill_misses_verification(self) -> None:
        path = self.skill(
            "demo",
            self.FRONT
            + """
# Demo

## Workflow

1. Read the skill file.
2. Update the lint script.

## Error recovery

Fix the skill named in the error, then rerun the command.
""",
        )
        self.assertEqual(
            lint_procedural(path),
            [f"{path}: procedural skill needs a concrete command or verifiable check"],
        )

    def test_fails_when_procedural_skill_misses_recovery(self) -> None:
        path = self.skill(
            "demo",
            self.FRONT
            + """
# Demo

## Workflow

1. Read the skill file.
2. Update the lint script.

```bash
python3 scripts/lint_skills.py
```
""",
        )
        self.assertEqual(
            lint_procedural(path),
            [f"{path}: procedural skill needs an error-recovery section"],
        )

    def test_passes_compliant_procedural_skill(self) -> None:
        path = self.skill(
            "demo",
            self.FRONT
            + """
# Demo

## Workflow

1. Read the skill file.
2. Update the lint script.

```bash
python3 scripts/lint_skills.py
```

Verify: the command prints `lint OK`.

## Error recovery

Fix the skill named in the error, then rerun the command.
""",
        )
        self.assertEqual(lint_skill_length(path), [])
        self.assertEqual(lint_retry_filler(path), [])
        self.assertEqual(lint_procedural(path), [])
        self.assertEqual(lint_mcp_json(path.parent), [])

    def test_short_principle_skips_procedural_checks(self) -> None:
        path = self.skill(
            "principle-demo",
            "---\nname: principle-demo\ndescription: ok\n---\n\n"
            "# Principle\n\n## Workflow\n\n- Do one thing.\n",
        )
        self.assertEqual(lint_procedural(path), [])

    def test_vendored_skill_skips_procedural_checks(self) -> None:
        path = self.skill(
            "wrapped",
            self.FRONT + "\n# Wrapped\n\n## Workflow\n\n- Do one thing.\n",
        )
        (path.parent / "VENDORED.json").write_text("{}\n", encoding="utf-8")
        self.assertEqual(lint_procedural(path), [])

    def test_legacy_exempt_must_shrink_when_skill_passes(self) -> None:
        path = self.skill(
            "demo",
            self.FRONT
            + """
# Demo

## Workflow

1. Read the skill file.
2. Update the lint script.

```bash
python3 scripts/lint_skills.py
```

## Error recovery

Fix the skill named in the error, then rerun the command.
""",
        )
        with mock.patch.object(lint_skills, "LEGACY_EXEMPT", frozenset({"demo"})):
            errors = lint_procedural(path)
        self.assertEqual(
            errors,
            [f"{path}: remove 'demo' from LEGACY_EXEMPT (procedural checks pass)"],
        )

    def test_log_papercut_passes_quality_gates(self) -> None:
        path = REPO_ROOT / "skills" / "log-papercut" / "SKILL.md"
        self.assertEqual(lint_skill_length(path), [])
        self.assertEqual(lint_retry_filler(path), [])
        self.assertEqual(lint_procedural(path), [])
        self.assertEqual(lint_mcp_json(path.parent), [])

    def test_real_tree_lints(self) -> None:
        with (
            mock.patch("sys.stdout", new_callable=io.StringIO) as out,
            mock.patch("sys.stderr", new_callable=io.StringIO) as err,
        ):
            code = lint_skills.main()
        self.assertEqual(code, 0, err.getvalue())
        self.assertIn("lint OK", out.getvalue())


if __name__ == "__main__":
    unittest.main()
