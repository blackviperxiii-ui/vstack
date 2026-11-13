#!/usr/bin/env python3
"""Guards for optimize skill (SKILL + GUIDE)."""

from __future__ import annotations

import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILL = REPO_ROOT / "skills" / "optimize" / "SKILL.md"
GUIDE = REPO_ROOT / "skills" / "optimize" / "GUIDE.md"


class OptimizeSkillTest(unittest.TestCase):
    def test_guide_exists(self) -> None:
        self.assertTrue(GUIDE.is_file(), "GUIDE.md required (stageshow pattern)")

    def test_skill_points_at_guide_and_distinctions(self) -> None:
        text = SKILL.read_text(encoding="utf-8")
        self.assertIn("GUIDE.md", text)
        self.assertIn("/optimize", text)
        self.assertIn("benchmark-checklist", text)
        self.assertIn("land-it", text)
        self.assertIn("Remeasure", text)

    def test_guide_covers_measure_and_root_causes(self) -> None:
        text = GUIDE.read_text(encoding="utf-8")
        for needle in (
            "optimize",
            "benchmark-checklist",
            "land-it",
            "flamegraph",
            "N+1",
            "Remeasure",
        ):
            self.assertIn(needle, text, f"GUIDE missing {needle!r}")


if __name__ == "__main__":
    unittest.main()
