#!/usr/bin/env python3
"""Guards for log-papercut skill frontmatter and schema docs."""

from __future__ import annotations

import re
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "log-papercut" / "SKILL.md"
VIPER = REPO_ROOT / "skills" / "viper-mode" / "SKILL.md"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)

SCHEMA_FIELDS = (
    "timestamp",
    "source",
    "tried",
    "expected",
    "observed",
    "suggested_fix",
    "turns_spent",
)


def parse_frontmatter(text: str) -> dict[str, str]:
    match = FRONTMATTER_RE.match(text)
    if not match:
        return {}
    meta: dict[str, str] = {}
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#") or ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            meta[key] = value
    return meta


class LogPapercutSkillTest(unittest.TestCase):
    def setUp(self) -> None:
        self.assertTrue(SKILL.is_file(), f"missing {SKILL}")
        self.text = SKILL.read_text(encoding="utf-8")

    def test_frontmatter_name_and_description(self) -> None:
        meta = parse_frontmatter(self.text)
        self.assertEqual(meta.get("name"), "log-papercut")
        description = meta.get("description", "")
        self.assertTrue(description, "frontmatter missing description")
        self.assertIn("papercut", description.lower())
        self.assertLess(len(self.text.splitlines()), 500)

    def test_schema_fields_documented(self) -> None:
        for field in SCHEMA_FIELDS:
            self.assertIn(field, self.text, f"schema field {field!r} missing")

    def test_queue_path_rules_documented(self) -> None:
        self.assertIn("VSTACK_PAPERCUTS_PATH", self.text)
        self.assertIn("~/.vstack/papercuts.jsonl", self.text)
        self.assertIn(".vstack/papercuts.jsonl", self.text)
        self.assertIn("no secrets", self.text.lower())

    def test_error_recovery_is_concrete(self) -> None:
        lowered = self.text.lower()
        self.assertIn("error recovery", lowered)
        self.assertNotIn("try again", lowered)
        self.assertIn("/tmp/vstack-papercuts.jsonl", self.text)

    def test_viper_mode_references_log_papercut(self) -> None:
        viper = VIPER.read_text(encoding="utf-8")
        self.assertIn("log-papercut", viper)
        self.assertIn("always-on", viper.lower())


if __name__ == "__main__":
    unittest.main()
