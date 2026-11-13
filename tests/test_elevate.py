#!/usr/bin/env python3
"""Guards for elevate skill (SKILL + GUIDE)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "elevate" / "SKILL.md"
GUIDE = REPO_ROOT / "skills" / "elevate" / "GUIDE.md"


class ElevateSkillTest(unittest.TestCase):
    def test_guide_exists(self) -> None:
        self.assertTrue(GUIDE.is_file(), "GUIDE.md required (bag-and-tag / optimize pattern)")

    def test_skill_points_at_guide_and_distinctions(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("GUIDE.md", text)
        self.assertIn("/elevate", text)
        self.assertIn("land-it", text)
        self.assertIn("qa-walkthrough", text)
        self.assertIn("prefers-reduced-motion", text)

    def test_guide_covers_craft_checklists(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        for needle in (
            "elevate",
            "land-it",
            "Motion budget",
            "AI-default",
            "prefers-reduced-motion",
            "State matrix",
        ):
            self.assertIn(needle, text, f"GUIDE missing {needle!r}")


if __name__ == "__main__":
    unittest.main()
