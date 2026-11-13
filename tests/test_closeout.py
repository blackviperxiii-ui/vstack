#!/usr/bin/env python3
"""Offline tests for skills/follow-through/scripts/closeout.py."""

from __future__ import annotations

import contextlib
import http.client
import io
import os
import subprocess
import sys
import tempfile
import unittest
import urllib.error
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "skills" / "follow-through" / "scripts"))

import closeout  # noqa: E402

STATES = {("my-org/my-app", 12): "MERGED", ("my-org/my-app", 13): "OPEN", ("my-org/lib", 4): "CLOSED"}


def lookup(repo: str, number: int) -> str:
    return STATES[(repo.lower(), number)]


def run(*argv: str) -> tuple[int, str]:
    out = io.StringIO()
    with contextlib.redirect_stdout(out):
        code = closeout.main(list(argv), lookup=lookup)
    return code, out.getvalue()


class CloseoutTest(unittest.TestCase):
    def test_parses_refs_and_urls(self) -> None:
        self.assertEqual(closeout.parse_ref("my-org/my-app#12"), ("my-org/my-app", 12))
        self.assertEqual(closeout.parse_ref("https://github.com/my-org/my.app/pull/7/"), ("my-org/my.app", 7))
        with self.assertRaises(ValueError):
            closeout.parse_ref("#12")

    def test_all_merged_may_close(self) -> None:
        code, out = run("my-org/my-app#12")
        self.assertEqual(code, 0)
        self.assertEqual(out, "my-org/my-app#12 MERGED\ncloseout: OK, the run may close\n")

    def test_an_open_pr_with_no_blocker_refuses_done(self) -> None:
        code, out = run("my-org/my-app#12", "https://github.com/my-org/my-app/pull/13")
        self.assertEqual(code, 1)
        self.assertIn(
            'my-org/my-app#13 OPEN: not merged and no blocker named (--pending "my-org/my-app#13=why")', out
        )
        self.assertTrue(out.endswith("closeout: NOT DONE\n"))

    def test_a_named_blocker_lets_an_open_or_closed_pr_stand(self) -> None:
        code, out = run(
            "my-org/my-app#12", "my-org/my-app#13", "my-org/lib#4",
            "--pending", "https://github.com/my-org/my-app/pull/13=waiting on the release review",
            "--pending", "my-org/lib#4=superseded by my-org/lib#5",
        )
        self.assertEqual(code, 0)
        self.assertEqual(out.splitlines()[:3], [
            "my-org/my-app#12 MERGED",
            "my-org/my-app#13 OPEN pending: waiting on the release review",
            "my-org/lib#4 CLOSED pending: superseded by my-org/lib#5",
        ])

    def test_repo_names_match_without_case(self) -> None:
        code, out = run("My-Org/My-App#13", "my-org/my-app#13", "--pending", "my-org/my-app#13=release review")
        self.assertEqual(code, 0)
        self.assertEqual(out, "My-Org/My-App#13 OPEN pending: release review\ncloseout: OK, the run may close\n")

    def test_an_empty_blocker_does_not_count(self) -> None:
        code, _ = run("my-org/my-app#13", "--pending", "my-org/my-app#13=  ")
        self.assertEqual(code, 1)

    def test_rest_reply_maps_to_a_state(self) -> None:
        self.assertEqual(closeout.pr_state({"state": "closed", "merged": True}), "MERGED")
        self.assertEqual(closeout.pr_state({"state": "open", "merged": False}), "OPEN")
        self.assertEqual(closeout.pr_state({"state": "closed", "merged": False}), "CLOSED")
        with self.assertRaises(ValueError):
            closeout.pr_state({"message": "Not Found"})

    def test_a_pr_that_cannot_be_read_blocks_closing(self) -> None:
        def broken(repo: str, number: int) -> str:
            raise subprocess.CalledProcessError(1, ["gh"])

        code, lines = closeout.verdict([("my-org/my-app", 9)], {}, broken)
        self.assertEqual(code, 2)
        self.assertEqual(lines, ["my-org/my-app#9 UNREADABLE (Command '['gh']' returned non-zero exit status 1.): "
                                 "can't close until it is checked"])

    def test_a_bad_reply_is_unreadable_and_the_other_prs_still_print(self) -> None:
        def flaky(repo: str, number: int) -> str:
            if number == 9:
                return closeout.pr_state([])
            if number == 10:
                raise http.client.IncompleteRead(b"{", 40)
            return lookup(repo, number)

        code, lines = closeout.verdict([("my-org/my-app", 12), ("my-org/my-app", 9), ("my-org/my-app", 10)], {}, flaky)
        self.assertEqual(code, 2)
        self.assertEqual(lines, [
            "my-org/my-app#12 MERGED",
            "my-org/my-app#9 UNREADABLE (reply is not a PR object: list): can't close until it is checked",
            "my-org/my-app#10 UNREADABLE (IncompleteRead(1 bytes read, 40 more expected)): can't close until it is checked",
        ])

    def test_prs_may_follow_a_pending_option(self) -> None:
        code, out = run("my-org/my-app#12", "--pending", "my-org/my-app#13=release review", "my-org/my-app#13")
        self.assertEqual(code, 0)
        self.assertIn("my-org/my-app#13 OPEN pending: release review", out)

    def test_a_pending_that_matches_no_listed_pr_or_has_no_blocker_is_refused(self) -> None:
        for bad in ("my-org/my-app#99=typo", "my-org/my-app#13"):
            with self.subTest(bad=bad), contextlib.redirect_stderr(io.StringIO()) as err:
                with self.assertRaises(SystemExit) as ctx:
                    run("my-org/my-app#13", "--pending", bad)
                self.assertEqual(ctx.exception.code, 2)
                self.assertIn("--pending", err.getvalue())


class RealLookupTest(unittest.TestCase):
    """The real gh and REST paths, with a fake gh on PATH and a patched urlopen."""

    def fake_gh(self, body: str, code: int = 0) -> Path:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        d = Path(tmp.name)
        (d / "reply").write_text(body, encoding="utf-8")
        gh = d / "gh"
        gh.write_text(
            "#!/bin/sh\n"
            f'printf "%s\\n" "$*" > "{d}/args"\n'
            f'if [ {code} -ne 0 ]; then cat "{d}/reply" >&2; exit {code}; fi\n'
            f'cat "{d}/reply"\n',
            encoding="utf-8",
        )
        gh.chmod(0o755)
        patcher = mock.patch.dict(os.environ, {"PATH": f"{d}{os.pathsep}{os.environ.get('PATH', '')}"})
        patcher.start()
        self.addCleanup(patcher.stop)
        return d

    def test_gh_path_reads_rest_state_from_github_com(self) -> None:
        d = self.fake_gh('{"state": "closed", "merged": true}')
        self.assertIs(closeout.default_lookup(), closeout.state_via_gh)
        out = io.StringIO()
        with contextlib.redirect_stdout(out):
            code = closeout.main(["my-org/my-app#12"])
        self.assertEqual(code, 0)
        self.assertEqual(out.getvalue(), "my-org/my-app#12 MERGED\ncloseout: OK, the run may close\n")
        self.assertEqual((d / "args").read_text().strip(), "api --hostname github.com repos/my-org/my-app/pulls/12")

    def test_gh_path_open_pr_refuses_done(self) -> None:
        self.fake_gh('{"state": "open", "merged": false}')
        with contextlib.redirect_stdout(io.StringIO()):
            self.assertEqual(closeout.main(["my-org/my-app#13"]), 1)

    def test_gh_failure_names_the_reason(self) -> None:
        self.fake_gh("gh: Not Found (HTTP 404)", code=1)
        code, lines = closeout.verdict([("my-org/my-app", 99)], {}, closeout.state_via_gh)
        self.assertEqual(code, 2)
        self.assertEqual(lines, ["my-org/my-app#99 UNREADABLE (gh api: gh: Not Found (HTTP 404)): can't close until it is checked"])

    def test_rest_path_maps_merged_and_http_errors(self) -> None:
        with mock.patch.object(closeout.urllib.request, "urlopen", return_value=io.BytesIO(b'{"state": "closed", "merged": true}')):
            self.assertEqual(closeout.state_via_api("my-org/my-app", 12), "MERGED")
        err = urllib.error.HTTPError("https://api.github.com/repos/my-org/my-app/pulls/99", 404, "Not Found", None, None)
        with mock.patch.object(closeout.urllib.request, "urlopen", side_effect=err):
            code, lines = closeout.verdict([("my-org/my-app", 99)], {}, closeout.state_via_api)
        self.assertEqual(code, 2)
        self.assertEqual(lines, ["my-org/my-app#99 UNREADABLE (HTTP 404): can't close until it is checked"])


if __name__ == "__main__":
    unittest.main()
