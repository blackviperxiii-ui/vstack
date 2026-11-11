#!/usr/bin/env python3
"""Offline tests for skills/updater/scripts/updater.py."""

from __future__ import annotations

import json
import sys
import tempfile
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "updater" / "scripts"))

import updater  # noqa: E402

TOC = """## Interface: 120105, 50501, 11508
## Title: Demo
## Version: 1.0.0
Demo.lua
"""


def version_service(build: str) -> str:
    return (
        "Region!STRING:0|BuildConfig!HEX:16|CDNConfig!HEX:16|KeyRing!HEX:16|"
        "BuildId!DEC:4|VersionsName!String:0|ProductConfig!HEX:16\n"
        f"us|a|b||1|{build}|c\neu|a|b||1|{build}|c\n"
    )


class VersionTest(unittest.TestCase):
    def test_parse_version(self) -> None:
        self.assertEqual(updater.parse_version("v1.2"), (1, 2, 0))
        self.assertEqual(updater.parse_version("26.3"), (26, 3, 0))
        self.assertIsNone(updater.parse_version("1.0.0-alpha.1"))

    def test_bump_kind_treats_zero_minor_as_breaking(self) -> None:
        self.assertEqual(updater.bump_kind((0, 36, 2), (0, 37, 0)), "major")
        self.assertEqual(updater.bump_kind((1, 2, 0), (1, 5, 0)), "minor")
        self.assertEqual(updater.bump_kind((1, 2, 0), (1, 2, 9)), "patch")
        self.assertEqual(updater.bump_kind((2, 0, 0), (1, 9, 0)), "none")

    def test_matches_req(self) -> None:
        self.assertTrue(updater.matches_req((0, 103, 16), ">= 0.103.12, < 0.104.0-alpha.1"))
        self.assertFalse(updater.matches_req((0, 102, 0), ">= 0.103.12, < 0.104.0-alpha.1"))
        self.assertTrue(updater.matches_req((1, 9, 0), "^1.2"))
        self.assertFalse(updater.matches_req((2, 0, 0), "^1.2"))
        self.assertTrue(updater.matches_req((0, 2, 9), "0.2"))
        self.assertFalse(updater.matches_req((0, 3, 0), "0.2"))
        self.assertTrue(updater.matches_req((7, 0, 0), ">=6, <8"))

    def test_wow_interface(self) -> None:
        self.assertEqual(updater.wow_interface("11.2.7.64978"), 110207)
        self.assertEqual(updater.wow_interface("1.15.9.70576"), 11509)

    def test_hosted_ids_skip_local_weights(self) -> None:
        self.assertTrue(updater.is_hosted_id("gpt-5.1"))
        self.assertFalse(updater.is_hosted_id("gemma-4-12b-it-q4_k_m"))
        self.assertFalse(updater.is_hosted_id("claude-proxy"))


class RepoTestCase(unittest.TestCase):
    def setUp(self) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        self.root = Path(tmp.name)
        self.repo = self.root / "my-app"
        self.out = self.root / "out"
        self.write("Cargo.toml", '[package]\nname = "my-app"\nrust-version = "1.80"\n\n'
                   '[dependencies]\nserde = "1"\nlocal = { path = "../local" }\n')
        self.write("ui/package.json", json.dumps(
            {"dependencies": {"react": "19.0.0"}, "devDependencies": {"vite": "^8.0.0"},
             "engines": {"node": ">=22"}}))
        self.write(".github/workflows/ci.yml", "jobs:\n  a:\n    steps:\n      - uses: actions/checkout@v5\n")
        self.write("addons/demo/Demo.toc", TOC)
        self.write("src/models.rs", 'const M: &str = "gpt-5.1";\nconst L: &str = "gemma-4-12b-it-q4_k_m";\n'
                   '// never trips EasyAntiCheat\nconst U: &str = "https://api.openai.com/v1/chat";\n')
        self.write("locales/en.json", json.dumps({"a": "A", "b": {"c": "C"}}))
        self.write("locales/de.json", json.dumps({"a": "A"}))
        self.write("node_modules/x/package.json", json.dumps({"dependencies": {"left-pad": "1.0.0"}}))

    def write(self, rel: str, text: str) -> Path:
        path = self.repo / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding="utf-8")
        return path

    def fetched(self, url: str, body: str) -> None:
        d = self.out / "fetched"
        d.mkdir(parents=True, exist_ok=True)
        (d / updater.fetched_name(url)).write_text(body, encoding="utf-8")


class InventoryTest(RepoTestCase):
    def test_finds_surfaces_from_the_repo(self) -> None:
        got = {(s.area, s.kind, s.name): s for s in updater.inventory(self.repo)}
        self.assertEqual(got[("deps", "cargo", "serde")].current, "1")
        self.assertNotIn(("deps", "cargo", "local"), got)
        self.assertEqual(got[("deps", "npm", "react")].current, "19.0.0")
        self.assertNotIn(("deps", "npm", "left-pad"), got)
        self.assertEqual(got[("ci", "action", "actions/checkout")].current, "v5")
        self.assertEqual(got[("addons", "wow-toc", "addons/demo/Demo.toc")].current, "120105,50501,11508")
        self.assertIn(("models", "openai", "gpt-5.1"), got)
        self.assertIn(("anticheat", "guard", "EasyAntiCheat"), got)
        self.assertEqual(got[("endpoints", "api", "api.openai.com")].current, "/v1")
        self.assertIn(("toolchain", "rust-msrv", "rust-version"), got)


class OfflineRunTest(RepoTestCase):
    def test_wow_gap_is_found_and_bumped(self) -> None:
        for product, build in {"wow": "12.1.5.1", "wow_classic": "5.5.4.1",
                               "wow_classic_era": "1.15.9.1", "wow_anniversary": "2.5.6.1"}.items():
            self.fetched(f"https://us.version.battle.net/v2/products/{product}/versions", version_service(build))
        report = updater.run(self.repo, self.out, offline=True, limit=40, probe_mods=False, wow_ptr=False)
        self.assertIn("wow 3 (bump --area wow)", report)
        self.assertIn("Unchecked sources", report)
        findings = json.loads((self.out / "findings.json").read_text())
        i18n = [f for f in findings if f["area"] == "i18n"]
        self.assertEqual(i18n[0]["note"], "1 strings missing versus locales/en.json")
        guarded = [f for f in findings if f["action"] == "guarded"]
        self.assertEqual([g["surface"] for g in guarded], ["EasyAntiCheat"])

        changed = updater.bump(self.repo, self.out, "wow")
        self.assertEqual(changed, ["addons/demo/Demo.toc"])
        first = (self.repo / "addons/demo/Demo.toc").read_text().splitlines()[0]
        self.assertEqual(first, "## Interface: 120105, 50504, 50501, 20506, 11509, 11508")

    def test_bump_refuses_unsafe_area(self) -> None:
        updater.run(self.repo, self.out, offline=True, limit=5, probe_mods=False, wow_ptr=False)
        with self.assertRaises(SystemExit):
            updater.bump(self.repo, self.out, "anticheat")


class RustsecTest(RepoTestCase):
    def test_matches_lockfile_against_advisory_db(self) -> None:
        lock = self.write("Cargo.lock", 'version = 4\n\n[[package]]\nname = "demo"\nversion = "0.3.1"\n'
                          'source = "registry+https://github.com/rust-lang/crates.io-index"\n')
        db = self.root / "db"
        (db / "crates" / "demo").mkdir(parents=True)
        (db / "crates" / "demo" / "RUSTSEC-0000-0001.md").write_text(
            '```toml\n[advisory]\nid = "RUSTSEC-0000-0001"\npackage = "demo"\n\n'
            '[versions]\npatched = [">= 0.3.4, < 0.4.0-alpha.1", ">= 0.4.2"]\n```\n\n# Demo overflow\n')
        found = updater.match_rustsec(db, lock, "Cargo.lock")
        self.assertEqual(len(found), 1)
        self.assertEqual(found[0].severity, "critical")
        self.assertEqual(found[0].action, "auto")
        self.assertIn("Demo overflow", found[0].note)
        lock.write_text(lock.read_text().replace("0.3.1", "0.3.5"))
        self.assertEqual(updater.match_rustsec(db, lock, "Cargo.lock"), [])


if __name__ == "__main__":
    unittest.main()
