#!/usr/bin/env python3
"""Guards for Cursor / Agent Plugins / Claude marketplace manifests."""

from __future__ import annotations

import json
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
AGENT_PLUGINS_SCHEMA = "https://agent-plugins.org/schemas/1.0.0/plugin.schema.json"
# Closed Agent Plugins top-level fields (spec §5.2).
AGENT_PLUGIN_FIELDS = {
    "$schema",
    "name",
    "version",
    "description",
    "author",
    "homepage",
    "repository",
    "license",
    "keywords",
    "extensions",
}


def load(rel: str) -> dict:
    return json.loads((REPO_ROOT / rel).read_text(encoding="utf-8"))


class PluginManifestsTest(unittest.TestCase):
    def test_versions_match_version_file(self) -> None:
        version = (REPO_ROOT / "VERSION").read_text(encoding="utf-8").strip()
        for rel in (
            "plugin.json",
            ".cursor-plugin/plugin.json",
            ".claude-plugin/plugin.json",
            ".cursor-plugin/marketplace.json",
            ".claude-plugin/marketplace.json",
        ):
            data = load(rel)
            if rel.endswith("marketplace.json"):
                self.assertEqual(data["plugins"][0]["version"], version, rel)
                if "version" in data.get("metadata", {}):
                    self.assertEqual(data["metadata"]["version"], version, rel)
            else:
                self.assertEqual(data["version"], version, rel)

    def test_root_agent_plugins_manifest(self) -> None:
        data = load("plugin.json")
        self.assertEqual(data["$schema"], AGENT_PLUGINS_SCHEMA)
        self.assertEqual(data["name"], "vstack")
        unknown = set(data) - AGENT_PLUGIN_FIELDS
        self.assertFalse(unknown, f"non-portable Agent Plugins fields: {unknown}")
        # Skills are discovered from skills/; do not declare Cursor-only paths here.
        self.assertNotIn("skills", data)
        self.assertNotIn("rules", data)
        self.assertTrue((REPO_ROOT / "skills" / "viper-mode" / "SKILL.md").is_file())

    def test_cursor_plugin_and_marketplace(self) -> None:
        plugin = load(".cursor-plugin/plugin.json")
        market = load(".cursor-plugin/marketplace.json")
        self.assertEqual(plugin["name"], "vstack")
        self.assertEqual(market["name"], "vstack")
        self.assertEqual(market["plugins"][0]["name"], "vstack")
        self.assertEqual(market["plugins"][0]["source"], "./")
        self.assertTrue((REPO_ROOT / "assets" / "logo.png").is_file())
        logo = plugin.get("logo", "")
        self.assertTrue(logo.startswith("assets/"), logo)

    def test_consuming_projects_checklist(self) -> None:
        text = (REPO_ROOT / "docs" / "CONSUMING.md").read_text(encoding="utf-8")
        for needle in (
            "Import from Repo",
            "Required",
            "Auto Refresh",
            "new",
            "Sync Skills",
            "plugin.json",
            "MCP",
        ):
            self.assertIn(needle, text, f"CONSUMING missing {needle!r}")


if __name__ == "__main__":
    unittest.main()
