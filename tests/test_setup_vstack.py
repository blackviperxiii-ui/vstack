#!/usr/bin/env python3
"""Guards for multi-host setup-vstack skill (SKILL + GUIDE)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "setup-vstack" / "SKILL.md"
GUIDE = REPO_ROOT / "skills" / "setup-vstack" / "GUIDE.md"


class SetupVstackSkillTest(unittest.TestCase):
    def test_guide_exists(self) -> None:
        self.assertTrue(GUIDE.is_file(), "GUIDE.md required (stageshow pattern)")

    def test_skill_points_at_guide_and_consuming(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("GUIDE.md", text)
        self.assertIn("docs/CONSUMING.md", text)
        self.assertIn("Never write another host", text)

    def test_skill_gates_cursor_paths(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("Cursor-only", text)
        self.assertIn("Never write `~/.cursor/**` on other hosts", text)

    def test_guide_covers_primary_hosts(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        for needle in (
            "cursor",
            "claude",
            "agents",
            "grok",
            "install_for.sh",
            "install.sh",
            "vstack-models.mdc",
            "Do not write `~/.cursor/**` unless host is `cursor`",
        ):
            self.assertIn(needle, text, f"GUIDE missing {needle!r}")

    def test_guide_skips_model_rule_on_non_cursor(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        self.assertIn("On Claude and other hosts: skip this file", text)


if __name__ == "__main__":
    unittest.main()
