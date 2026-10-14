#!/usr/bin/env python3
"""Regression tests for skill lint rules."""

from __future__ import annotations

import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from lint_skills import lint_skill  # noqa: E402


class LintSkillsTest(unittest.TestCase):
    def test_rejects_ignored_mode_frontmatter(self) -> None:
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=".md", delete=False, encoding="utf-8"
        ) as handle:
            handle.write(
                "---\nname: fake-skill\ndescription: test\nmode: true\n---\n\n# x\n"
            )
            path = Path(handle.name)
        try:
            errors = lint_skill(path)
            self.assertTrue(any("mode" in err for err in errors))
        finally:
            path.unlink(missing_ok=True)


if __name__ == "__main__":
    unittest.main()
