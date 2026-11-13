#!/usr/bin/env python3
"""Guards for bag-and-tag skill (SKILL + GUIDE)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "bag-and-tag" / "SKILL.md"
GUIDE = REPO_ROOT / "skills" / "bag-and-tag" / "GUIDE.md"


class BagAndTagSkillTest(unittest.TestCase):
    def test_guide_exists(self) -> None:
        self.assertTrue(GUIDE.is_file(), "GUIDE.md required (stageshow pattern)")

    def test_skill_points_at_guide_and_ritual(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("GUIDE.md", text)
        self.assertIn("/bag-and-tag", text)
        self.assertIn("beta", text)
        self.assertIn("main", text)
        self.assertIn("VERSION", text)
        self.assertIn("CONSUMING.md", text)
        # Must not use banned generic names as the skill identity
        self.assertNotRegex(text, r"(?i)\b/ship\b|\b/deploy\b|\bfull-ship\b")

    def test_guide_covers_promote_tag_verify(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        for needle in (
            "explicit",
            "force-push",
            "plugin.json",
            "Agent Plugins",
            "vX.Y.Z",
            "release.yml",
            "install.sh",
            "CONSUMING.md",
        ):
            self.assertIn(needle, text, f"GUIDE missing {needle!r}")
        self.assertNotRegex(text, r"(?i)\bfull-ship\b")


if __name__ == "__main__":
    unittest.main()
