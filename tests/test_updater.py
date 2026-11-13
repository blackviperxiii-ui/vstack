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


class SavedBodyTest(RepoTestCase):
    WOW = {"wow": "12.1.5.1", "wow_classic": "5.5.4.1", "wow_classic_era": "1.15.9.1", "wow_anniversary": "2.5.6.1"}
    ROUTER = "https://openrouter.ai/api/v1/models"

    def version_url(self, product: str) -> str:
        return f"https://us.version.battle.net/v2/products/{product}/versions"

    def test_unusable_saved_bodies_stay_unchecked(self) -> None:
        for product, build in self.WOW.items():
            self.fetched(self.version_url(product), version_service(build))
        # A Blizzard body with no us row, and an OpenRouter list cut off mid-file.
        self.fetched(self.version_url("wow"), version_service("12.1.5.1").replace("\nus|", "\nkr|"))
        self.fetched(self.ROUTER, '{"data": [{"id": "openai/gpt-5.1", "created": 1')
        report = updater.run(self.repo, self.out, offline=True, limit=40, probe_mods=False, wow_ptr=False)
        unchecked = report.split("Unchecked sources", 1)[1]
        self.assertIn(f"- {self.version_url('wow')} (saved body unparseable, truncated?)", unchecked)
        self.assertIn(f"- {self.ROUTER} (saved body unparseable, truncated?)", unchecked)
        # The good bodies are used, not flagged.
        self.assertNotIn(self.version_url("wow_classic"), unchecked)
        # Each saved file used is listed with its size.
        router = self.out / "fetched" / updater.fetched_name(self.ROUTER)
        self.assertIn(f"- {router.name} ({router.stat().st_size} bytes)", report.split("Saved bodies used", 1)[1])

    def test_a_parsed_body_with_no_rows_is_unchecked_and_a_good_one_is_not(self) -> None:
        self.fetched(self.ROUTER, '{"error": "rate limited"}')
        f = updater.Fetcher(self.out, offline=True)
        updater.check_models(f, updater.inventory(self.repo))
        self.assertEqual(f.misses.get(self.ROUTER), "saved body unparseable, truncated?")
        self.fetched(self.ROUTER, '{"data": [{"id": "openai/gpt-5.1", "created": 1}]}')
        f = updater.Fetcher(self.out, offline=True)
        updater.check_models(f, updater.inventory(self.repo))
        self.assertNotIn(self.ROUTER, f.misses)

    def test_an_empty_saved_tag_list_is_unchecked(self) -> None:
        url = "https://github.com/actions/checkout"
        self.fetched(url + ".tags", "")
        f = updater.Fetcher(self.out, offline=True)
        updater.check_actions(f, self.repo, updater.inventory(self.repo))
        self.assertEqual(f.misses.get(url), "saved body unparseable, truncated?")

    def test_a_cut_off_crate_index_is_unchecked_not_an_older_latest(self) -> None:
        url = "https://index.crates.io/se/rd/serde"
        good = '{"name": "serde", "vers": "1.0.1"}\n{"name": "serde", "vers": "1.0.2"}\n'
        self.fetched(url, good + '{"name": "serde", "vers": "1.0.3')
        f = updater.Fetcher(self.out, offline=True)
        self.assertIsNone(updater.latest_crate(f, "serde"))
        self.assertEqual(f.misses.get(url), "saved body unparseable, truncated?")
        self.fetched(url, good)
        f = updater.Fetcher(self.out, offline=True)
        self.assertEqual(updater.latest_crate(f, "serde"), "1.0.2")
        self.assertNotIn(url, f.misses)

    def test_registry_bodies_with_no_version_are_unchecked(self) -> None:
        npm = "https://registry.npmjs.org/react/latest"
        pypi = "https://pypi.org/pypi/requests/json"
        for url in (npm, pypi):
            self.fetched(url, '{"error": "rate limited"}')
        f = updater.Fetcher(self.out, offline=True)
        self.assertIsNone(updater.latest_npm(f, "react"))
        self.assertIsNone(updater.latest_pypi(f, "requests"))
        self.assertEqual(f.misses.get(npm), "saved body unparseable, truncated?")
        self.assertEqual(f.misses.get(pypi), "saved body unparseable, truncated?")
        self.fetched(npm, '{"version": "19.2.0"}')
        self.fetched(pypi, '{"info": {"version": "2.32.5"}}')
        f = updater.Fetcher(self.out, offline=True)
        self.assertEqual(updater.latest_npm(f, "react"), "19.2.0")
        self.assertEqual(updater.latest_pypi(f, "requests"), "2.32.5")
        self.assertEqual(f.misses, {})

    def test_toolchain_bodies_with_no_version_are_unchecked_without_crashing(self) -> None:
        rust = "https://static.rust-lang.org/dist/channel-rust-stable.toml"
        node = "https://nodejs.org/dist/index.json"
        self.fetched(rust, 'manifest-version = "2"\n[pkg.cargo]\nversion = "0.9')
        self.fetched(node, '{"error": "rate limited"}')
        f = updater.Fetcher(self.out, offline=True)
        self.assertEqual(updater.check_toolchains(f, updater.inventory(self.repo)), [])
        self.assertEqual(f.misses.get(rust), "saved body unparseable, truncated?")
        self.assertEqual(f.misses.get(node), "saved body unparseable, truncated?")
        self.fetched(rust, '[pkg.rust]\nversion = "1.99.0 (abc 2026-11-01)"\n')
        self.fetched(node, '[{"version": "v26.1.0", "lts": false}, {"version": "v24.11.0", "lts": "Krypton"}]')
        f = updater.Fetcher(self.out, offline=True)
        found = updater.check_toolchains(f, updater.inventory(self.repo))
        self.assertEqual(f.misses, {})
        self.assertEqual([(x.surface, x.latest) for x in found],
                         [("rust-version (MSRV)", "1.99.0"), ("node engines", "v24.11.0")])

    def test_a_minecraft_body_with_no_release_is_unchecked(self) -> None:
        url = "https://piston-meta.mojang.com/mc/game/version_manifest_v2.json"
        self.fetched(url, '{"error": "rate limited"}')
        surface = updater.Surface("integrations", "launcher", "Minecraft", "", ["src/mc.rs"])
        f = updater.Fetcher(self.out, offline=True)
        self.assertEqual(updater.check_minecraft(f, [surface]), [])
        self.assertEqual(f.misses.get(url), "saved body unparseable, truncated?")
        self.fetched(url, '{"latest": {"release": "1.22.1"}}')
        f = updater.Fetcher(self.out, offline=True)
        self.assertEqual([x.latest for x in updater.check_minecraft(f, [surface])], ["1.22.1"])
        self.assertEqual(f.misses, {})


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

    def test_an_advisory_ignored_in_deny_toml_is_a_watch_item_with_its_reason(self) -> None:
        lock = self.write("Cargo.lock", 'version = 4\n\n[[package]]\nname = "demo"\nversion = "0.3.1"\n'
                          'source = "registry+https://github.com/rust-lang/crates.io-index"\n')
        self.write("deny.toml", '[advisories]\nignore = [\n  { id = "RUSTSEC-0000-0001", reason = "only the old '
                   'cabin uses demo" },\n  "RUSTSEC-0000-0009",\n]\n')
        db = self.root / "db"
        (db / "crates" / "demo").mkdir(parents=True)
        (db / "crates" / "demo" / "RUSTSEC-0000-0001.md").write_text(
            '```toml\n[advisory]\nid = "RUSTSEC-0000-0001"\npackage = "demo"\n\n'
            '[versions]\npatched = [">= 0.3.4"]\n```\n\n# Demo overflow\n')
        ignores = updater.deny_ignores(self.repo)
        self.assertEqual(ignores, {"RUSTSEC-0000-0001": "only the old cabin uses demo",
                                   "RUSTSEC-0000-0009": "no reason given"})
        found = updater.mark_deny_ignores(updater.match_rustsec(db, lock, "Cargo.lock"), ignores)
        self.assertEqual((found[0].severity, found[0].action), ("info", "watch"))
        report = updater.render(found, [], {}, self.repo, 10)
        self.assertIn("Findings: none", report)
        self.assertIn("- RUSTSEC-0000-0001 cargo:demo 0.3.1: only the old cabin uses demo", report)


class FetchMissTest(unittest.TestCase):
    def test_a_proxy_refusal_reads_as_proxy_blocked(self) -> None:
        import urllib.error
        blocked = urllib.error.URLError(OSError("Tunnel connection failed: 403 Forbidden"))
        self.assertEqual(updater.miss_reason(blocked), "proxy blocked (403)")
        self.assertEqual(updater.miss_reason(urllib.error.URLError("timed out")), "URLError")
        self.assertEqual(updater.miss_reason(TimeoutError()), "TimeoutError")


class LockReviewTest(unittest.TestCase):
    def test_a_refresh_names_new_crates_and_new_duplicate_majors(self) -> None:
        before = {("zbus", "5.12.0"), ("serde", "1.0.200"), ("ashpd", "0.12.0")}
        after = {("zbus", "5.12.0"), ("zbus", "6.0.1"), ("serde", "1.0.228"), ("ashpd", "0.14.0"),
                 ("zbus-lockstep", "0.5.2")}
        review = updater.lock_review(before, after)
        self.assertEqual(review[0], "new crate zbus-lockstep 0.5.2")
        self.assertEqual(len(review), 2)
        self.assertTrue(review[1].startswith("duplicate majors zbus (5.12.0, 6.0.1);"))

    def test_a_plain_refresh_reports_nothing(self) -> None:
        before = {("serde", "1.0.200"), ("syn", "1.0.109"), ("syn", "2.0.80")}
        after = {("serde", "1.0.228"), ("syn", "1.0.109"), ("syn", "2.0.110")}
        self.assertEqual(updater.lock_review(before, after), [])


if __name__ == "__main__":
    unittest.main()
