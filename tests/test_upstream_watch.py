#!/usr/bin/env python3
"""Regression tests for the pure helpers in upstream_watch (no network, no real UPSTREAM.json)."""

from __future__ import annotations

import contextlib
import io
import json
import sys
import tempfile
import types
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

try:
    import tiktoken  # noqa: F401
except ImportError:
    # upstream_watch imports tiktoken at module level; tests mock get_encoding anyway.
    stub = types.ModuleType("tiktoken")
    stub.Encoding = object  # type: ignore[attr-defined]
    stub.get_encoding = lambda name: None  # type: ignore[attr-defined]
    sys.modules["tiktoken"] = stub

import upstream_watch  # noqa: E402


class WordEncoding:
    """Fake encoder: one token per whitespace-separated word."""

    def encode(self, text: str) -> list[int]:
        return list(range(len(text.split())))


UPSTREAM = {
    "repo": "owner/pstack-repo",
    "path": "pstack",
    "last_synced_sha": "a" * 40,
    "mapping": {"local-a": "up-a"},
    "unported": ["up-u"],
}


class LoadUpstreamTest(unittest.TestCase):
    def test_reads_patched_path(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "UPSTREAM.json"
            path.write_text(json.dumps(UPSTREAM), encoding="utf-8")
            with mock.patch.object(upstream_watch, "UPSTREAM_PATH", path):
                self.assertEqual(upstream_watch.load_upstream(), UPSTREAM)

    def test_missing_file_raises(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            with mock.patch.object(upstream_watch, "UPSTREAM_PATH", Path(tmp) / "nope.json"):
                with self.assertRaises(FileNotFoundError):
                    upstream_watch.load_upstream()

    def test_real_file_has_required_keys(self) -> None:
        data = json.loads((REPO_ROOT / "UPSTREAM.json").read_text(encoding="utf-8"))
        for key in ("repo", "path", "last_synced_sha"):
            self.assertIn(key, data)


class ClassifyFileTest(unittest.TestCase):
    mapping = {"local-a": "up-a"}
    unported = {"up-u"}

    def classify(self, filename: str) -> str:
        return upstream_watch.classify_file(filename, self.mapping, self.unported)

    def test_mapped(self) -> None:
        self.assertEqual(self.classify("pstack/skills/up-a/SKILL.md"), "mapped")

    def test_mapping_matches_values_not_keys(self) -> None:
        self.assertEqual(self.classify("pstack/skills/local-a/SKILL.md"), "new")

    def test_unported(self) -> None:
        self.assertEqual(self.classify("pstack/skills/up-u/SKILL.md"), "unported")

    def test_new(self) -> None:
        self.assertEqual(self.classify("pstack/skills/brand-new/SKILL.md"), "new")

    def test_other_non_skill_file(self) -> None:
        self.assertEqual(self.classify("pstack/README.md"), "other")
        self.assertEqual(self.classify("pstack/skills/up-a/notes.md"), "other")

    def test_other_too_shallow(self) -> None:
        self.assertEqual(self.classify("SKILL.md"), "other")
        self.assertEqual(self.classify("up-a/SKILL.md"), "other")
        self.assertEqual(self.classify(""), "other")


class CountTokensTextTest(unittest.TestCase):
    def test_uses_cl100k_encoding(self) -> None:
        with mock.patch.object(
            upstream_watch.tiktoken, "get_encoding", return_value=WordEncoding(), create=True
        ) as get_enc:
            self.assertEqual(upstream_watch.count_tokens_text("one two three"), 3)
            self.assertEqual(upstream_watch.count_tokens_text(""), 0)
        get_enc.assert_called_with("cl100k_base")


class CompareCommitsTest(unittest.TestCase):
    def test_builds_compare_url(self) -> None:
        with mock.patch.object(
            upstream_watch, "fetch_json", return_value={"files": []}
        ) as fetch:
            upstream_watch.compare_commits(UPSTREAM, "base", "head")
        fetch.assert_called_once_with(
            "https://api.github.com/repos/owner/pstack-repo/compare/base...head"
        )


class LatestPstackCommitTest(unittest.TestCase):
    def test_returns_first_sha_and_builds_url(self) -> None:
        with mock.patch.object(
            upstream_watch, "fetch_json", return_value=[{"sha": "abc"}, {"sha": "def"}]
        ) as fetch:
            self.assertEqual(upstream_watch.latest_pstack_commit(UPSTREAM), "abc")
        fetch.assert_called_once_with(
            "https://api.github.com/repos/owner/pstack-repo/commits?"
            "sha=main&path=pstack&per_page=1"
        )

    def test_branch_override(self) -> None:
        with mock.patch.object(upstream_watch, "fetch_json", return_value=[{"sha": "x"}]) as fetch:
            upstream_watch.latest_pstack_commit({**UPSTREAM, "branch": "dev"})
        self.assertIn("sha=dev&", fetch.call_args.args[0])

    def test_empty_raises(self) -> None:
        with mock.patch.object(upstream_watch, "fetch_json", return_value=[]):
            with self.assertRaises(RuntimeError):
                upstream_watch.latest_pstack_commit(UPSTREAM)


class CommitsTouchingPathTest(unittest.TestCase):
    def run_with(self, payload: object) -> list[dict]:
        with mock.patch.object(upstream_watch, "fetch_json", return_value=payload):
            return upstream_watch.commits_touching_path(UPSTREAM, "base", "head")

    def test_stops_at_base(self) -> None:
        commits = [{"sha": "h1"}, {"sha": "h2"}, {"sha": "base"}, {"sha": "old"}]
        self.assertEqual(self.run_with(commits), [{"sha": "h1"}, {"sha": "h2"}])

    def test_base_not_found_returns_all_valid(self) -> None:
        commits = [{"sha": "h1"}, {"nosha": 1}, {"sha": 5}, {"sha": "h2"}]
        self.assertEqual(self.run_with(commits), [{"sha": "h1"}, {"sha": "h2"}])

    def test_non_list_payload(self) -> None:
        self.assertEqual(self.run_with({"message": "rate limited"}), [])


class FetchUpstreamSkillAtTest(unittest.TestCase):
    def test_returns_decoded_body_and_url(self) -> None:
        resp = mock.MagicMock()
        resp.__enter__.return_value.read.return_value = "héllo".encode("utf-8")
        with mock.patch.object(upstream_watch.urllib.request, "urlopen", return_value=resp) as op:
            text = upstream_watch.fetch_upstream_skill_at("sha1", UPSTREAM, "up-a")
        self.assertEqual(text, "héllo")
        self.assertEqual(
            op.call_args.args[0],
            "https://raw.githubusercontent.com/owner/pstack-repo/sha1/"
            "pstack/skills/up-a/SKILL.md",
        )

    def test_http_error_returns_none(self) -> None:
        err = upstream_watch.urllib.error.HTTPError("u", 404, "nf", {}, None)  # type: ignore[arg-type]
        with mock.patch.object(upstream_watch.urllib.request, "urlopen", side_effect=err):
            self.assertIsNone(upstream_watch.fetch_upstream_skill_at("s", UPSTREAM, "x"))


class FindOpenIssueTest(unittest.TestCase):
    def find(self, payload: object) -> int | None:
        with mock.patch.object(upstream_watch, "api_request", return_value=payload):
            return upstream_watch.find_open_issue("o/r", "tok")

    def test_skips_pull_requests(self) -> None:
        issues = [{"number": 1, "pull_request": {}}, {"number": 2}, {"number": 3}]
        self.assertEqual(self.find(issues), 2)

    def test_none_when_empty_or_bad(self) -> None:
        self.assertIsNone(self.find([]))
        self.assertIsNone(self.find({"message": "x"}))
        self.assertIsNone(self.find([{"number": "7"}, "junk"]))

    def test_request_args(self) -> None:
        with mock.patch.object(upstream_watch, "api_request", return_value=[]) as req:
            upstream_watch.find_open_issue("o/r", "tok")
        req.assert_called_once_with(
            "GET",
            "https://api.github.com/repos/o/r/issues?state=open&labels=upstream-sync&per_page=10",
            "tok",
        )


class BuildIssueBodyTest(unittest.TestCase):
    def build(self, files: list[dict], commits: list[dict]) -> str:
        texts = {("old", "up-a"): "one two", ("new", "up-a"): "one two three four"}
        with (
            mock.patch.object(upstream_watch, "commits_touching_path", return_value=commits),
            mock.patch.object(
                upstream_watch,
                "fetch_upstream_skill_at",
                side_effect=lambda sha, up, skill: texts.get((sha, skill)),
            ),
            mock.patch.object(
                upstream_watch.tiktoken, "get_encoding", return_value=WordEncoding(), create=True
            ),
        ):
            return upstream_watch.build_issue_body(UPSTREAM, "old", "new", {"files": files})

    def test_full_body(self) -> None:
        files = [
            {"filename": "pstack/skills/up-a/SKILL.md", "status": "modified"},
            {"filename": "pstack/skills/up-u/SKILL.md", "status": "added"},
            {"filename": "pstack/skills/fresh/SKILL.md", "status": "added"},
            {"filename": "pstack/README.md", "status": "modified"},
        ]
        commits = [{"sha": "1234567890", "commit": {"message": "Subject\n\nbody"}}]
        body = self.build(files, commits)
        self.assertIn("Tracked sync point: `old`", body)
        self.assertIn("Latest commit touching `pstack/`: `new`", body)
        self.assertIn("Compare: https://github.com/owner/pstack-repo/compare/old...new", body)
        self.assertIn("- `1234567` Subject", body)
        self.assertIn(
            "## Changed files (mapped skills)\n\n- `pstack/skills/up-a/SKILL.md` (modified)", body
        )
        self.assertIn(
            "## Changed files (unported upstream skills)\n\n"
            "- `pstack/skills/up-u/SKILL.md` (added)",
            body,
        )
        self.assertIn(
            "## Changed files (new upstream skills)\n\n- `pstack/skills/fresh/SKILL.md` (added)",
            body,
        )
        # "other" files are not listed in any section
        self.assertNotIn("README.md", body)
        # up-a: 2 -> 4 tokens; skills missing at a sha count as 0
        self.assertIn("| `up-a` | 2 | 4 | +2 |", body)
        self.assertIn("| `up-u` | 0 | 0 | +0 |", body)
        self.assertIn("| `fresh` | 0 | 0 | +0 |", body)
        self.assertTrue(body.endswith("when ready._"))

    def test_empty_compare(self) -> None:
        body = self.build([], [])
        self.assertEqual(body.count("- (none)"), 3)
        self.assertIn("| --- | ---: | ---: | ---: |\n\n---", body)

    def test_malformed_mapping_and_unported_tolerated(self) -> None:
        bad = {**UPSTREAM, "mapping": "oops", "unported": "oops"}
        with (
            mock.patch.object(upstream_watch, "commits_touching_path", return_value=[]),
            mock.patch.object(upstream_watch, "fetch_upstream_skill_at", return_value=None),
        ):
            body = upstream_watch.build_issue_body(
                bad, "old", "new", {"files": [{"filename": "p/skills/s/SKILL.md", "status": "added"}]}
            )
        self.assertIn("## Changed files (new upstream skills)\n\n- `p/skills/s/SKILL.md` (added)", body)


class DryRunReportTest(unittest.TestCase):
    def test_truncates_to_ten(self) -> None:
        commits = [{"sha": f"{i:07d}xx", "commit": {"message": f"msg {i}\nmore"}} for i in range(12)]
        out = io.StringIO()
        with (
            mock.patch.object(upstream_watch, "commits_touching_path", return_value=commits),
            contextlib.redirect_stdout(out),
        ):
            rc = upstream_watch.dry_run_report(UPSTREAM, "a" * 40, "b" * 40)
        lines = out.getvalue().splitlines()
        self.assertEqual(rc, 0)
        self.assertEqual(lines[0], "Drift: aaaaaaa → bbbbbbb")
        self.assertEqual(lines[1], f"Compare: https://github.com/owner/pstack-repo/compare/{'a'*40}...{'b'*40}")
        self.assertEqual(lines[2], "Commits touching pstack/: 12")
        self.assertEqual(lines[3], "  0000000 msg 0")
        self.assertEqual(lines[-1], "  ... and 2 more")
        self.assertEqual(len(lines), 3 + 10 + 1)


class MainTest(unittest.TestCase):
    def test_up_to_date(self) -> None:
        out = io.StringIO()
        with (
            mock.patch.object(upstream_watch, "load_upstream", return_value=UPSTREAM),
            mock.patch.object(upstream_watch, "latest_pstack_commit", return_value="a" * 40),
            mock.patch.object(sys, "argv", ["upstream_watch.py"]),
            contextlib.redirect_stdout(out),
        ):
            self.assertEqual(upstream_watch.main(), 0)
        self.assertEqual(out.getvalue(), "Up to date at aaaaaaa\n")

    def test_missing_env_returns_1(self) -> None:
        err = io.StringIO()
        with (
            mock.patch.object(upstream_watch, "load_upstream", return_value=UPSTREAM),
            mock.patch.object(upstream_watch, "latest_pstack_commit", return_value="b" * 40),
            mock.patch.object(sys, "argv", ["upstream_watch.py"]),
            mock.patch.dict(upstream_watch.os.environ, {}, clear=True),
            contextlib.redirect_stderr(err),
        ):
            self.assertEqual(upstream_watch.main(), 1)
        self.assertIn("GITHUB_TOKEN and GITHUB_REPOSITORY required", err.getvalue())


if __name__ == "__main__":
    unittest.main()
