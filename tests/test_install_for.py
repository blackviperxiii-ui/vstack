#!/usr/bin/env python3
"""Tests for scripts/install_for.sh (no network; temp project dirs only)."""

from __future__ import annotations

import os
import subprocess
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
INSTALL_FOR = REPO_ROOT / "scripts" / "install_for.sh"


def run_install(*args: str, env: dict[str, str] | None = None) -> subprocess.CompletedProcess[str]:
    merged = os.environ.copy()
    if env:
        merged.update(env)
    return subprocess.run(
        ["bash", str(INSTALL_FOR), *args],
        cwd=REPO_ROOT,
        env=merged,
        capture_output=True,
        text=True,
        check=False,
    )


class InstallForTest(unittest.TestCase):
    def test_requires_host(self) -> None:
        result = run_install("--project", "/tmp")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--host is required", result.stderr)

    def test_unknown_host(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result = run_install("--host", "not-a-host", "--project", tmp)
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("unknown host", result.stderr)

    def test_deferred_hosts_exit_2(self) -> None:
        for host in ("aider", "continue"):
            with self.subTest(host=host):
                result = run_install("--host", host, "--project", "/tmp")
                self.assertEqual(result.returncode, 2)
                self.assertIn("no confirmed SKILL.md", result.stderr)

    def test_project_agents_link_installs_viper_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = run_install("--host", "agents", "--project", str(project))
            self.assertEqual(result.returncode, 0, result.stderr)
            skill = project / ".agents" / "skills" / "viper-mode"
            self.assertTrue(skill.exists(), f"missing {skill}")
            self.assertTrue(skill.is_symlink())
            self.assertTrue((skill / "SKILL.md").is_file())
            self.assertEqual(
                skill.resolve(),
                (REPO_ROOT / "skills" / "viper-mode").resolve(),
            )

    def test_project_agents_copy_mode(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = run_install(
                "--host", "agents", "--project", str(project), "--mode", "copy"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            skill = project / ".agents" / "skills" / "viper-mode"
            self.assertTrue(skill.is_dir())
            self.assertFalse(skill.is_symlink())
            self.assertTrue((skill / "SKILL.md").is_file())

    def test_idempotent_relink(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            for _ in range(2):
                result = run_install("--host", "codex", "--project", str(project))
                self.assertEqual(result.returncode, 0, result.stderr)
            skill = project / ".agents" / "skills" / "viper-mode"
            self.assertTrue(skill.is_symlink())

    def test_host_path_map(self) -> None:
        cases = {
            "claude": ".claude/skills",
            "grok": ".grok/skills",
            "antigravity": ".agents/skills",
            "muse": ".agents/skills",
            "windsurf": ".agents/skills",
            "opencode": ".agents/skills",
            "cursor": ".agents/skills",
        }
        for host, rel in cases.items():
            with self.subTest(host=host):
                with tempfile.TemporaryDirectory() as tmp:
                    project = Path(tmp)
                    result = run_install(
                        "--host", host, "--project", str(project), "--skill", "viper-mode"
                    )
                    self.assertEqual(result.returncode, 0, result.stderr)
                    skill = project / rel / "viper-mode"
                    self.assertTrue(skill.exists(), f"{host}: missing {skill}")

    def test_single_skill_flag(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            project = Path(tmp)
            result = run_install(
                "--host", "agents", "--project", str(project), "--skill", "viper-mode"
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            skills_root = project / ".agents" / "skills"
            names = sorted(p.name for p in skills_root.iterdir())
            self.assertEqual(names, ["viper-mode"])

    def test_global_writes_under_home_only(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_install(
                "--host",
                "agents",
                "--global",
                "--skill",
                "viper-mode",
                env={"HOME": home},
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            skill = Path(home) / ".agents" / "skills" / "viper-mode"
            self.assertTrue(skill.is_symlink())

    def test_global_cursor_plugin_link(self) -> None:
        with tempfile.TemporaryDirectory() as home:
            result = run_install(
                "--host", "cursor", "--global", env={"HOME": home}
            )
            self.assertEqual(result.returncode, 0, result.stderr)
            dest = Path(home) / ".cursor" / "plugins" / "local" / "vstack"
            self.assertTrue(dest.is_symlink())
            self.assertEqual(dest.resolve(), REPO_ROOT.resolve())

    def test_project_required_without_global(self) -> None:
        result = run_install("--host", "agents")
        self.assertNotEqual(result.returncode, 0)
        self.assertIn("--project DIR is required", result.stderr)


if __name__ == "__main__":
    unittest.main()
