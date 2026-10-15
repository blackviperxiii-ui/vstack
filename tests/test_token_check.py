#!/usr/bin/env python3
"""Regression tests for the pure helpers in token_check (no network, no git)."""

from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

REPO_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(REPO_ROOT / "scripts"))

from _stubs import install_tiktoken_stub  # noqa: E402

install_tiktoken_stub()

import token_check  # noqa: E402

CI_ENV_KEYS = {"GITHUB_EVENT_PATH", "GITHUB_BASE_SHA", "GITHUB_STEP_SUMMARY"}


def clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CI_ENV_KEYS}


class GrowthRatioTest(unittest.TestCase):
    def test_values(self) -> None:
        self.assertEqual(token_check.growth_ratio(100, 150), 0.5)
        self.assertEqual(token_check.growth_ratio(200, 100), -0.5)
        self.assertEqual(token_check.growth_ratio(100, 100), 0.0)

    def test_nonpositive_base(self) -> None:
        self.assertEqual(token_check.growth_ratio(0, 5), float("inf"))
        self.assertEqual(token_check.growth_ratio(0, 0), 0.0)
        self.assertEqual(token_check.growth_ratio(-1, 0), 0.0)


class SkillTokensTest(unittest.TestCase):
    def test_returns_int_tokens(self) -> None:
        self.assertEqual(token_check.skill_tokens({"skills": {"a": {"tokens": 42}}}, "a"), 42)

    def test_missing_or_malformed(self) -> None:
        for report in (
            {},
            {"skills": []},
            {"skills": {}},
            {"skills": {"a": 3}},
            {"skills": {"a": {"tokens": "7"}}},
            {"skills": {"a": {}}},
        ):
            with self.subTest(report=report):
                self.assertIsNone(token_check.skill_tokens(report, "a"))


class LoadJsonTest(unittest.TestCase):
    def test_reads_json_file(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "x.json"
            path.write_text('{"k": [1, 2]}', encoding="utf-8")
            self.assertEqual(token_check.load_json(path), {"k": [1, 2]})


class PrEventTest(unittest.TestCase):
    def use_event(self, event: dict | None, extra_env: dict | None = None) -> None:
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        env = clean_env()
        if event is not None:
            path = Path(tmp.name) / "event.json"
            path.write_text(json.dumps(event), encoding="utf-8")
            env["GITHUB_EVENT_PATH"] = str(path)
        env.update(extra_env or {})
        patcher = mock.patch.dict(os.environ, env, clear=True)
        patcher.start()
        self.addCleanup(patcher.stop)

    def test_no_event_path(self) -> None:
        self.use_event(None)
        self.assertEqual(token_check.pr_event(), {})
        self.assertFalse(token_check.pr_has_label("token-growth-approved"))
        self.assertIsNone(token_check.pr_base_sha())

    def test_label_present_and_absent(self) -> None:
        self.use_event(
            {"pull_request": {"labels": [{"name": "bug"}, {"name": "token-growth-approved"}]}}
        )
        self.assertTrue(token_check.pr_has_label("token-growth-approved"))
        self.assertFalse(token_check.pr_has_label("other"))

    def test_label_without_pull_request(self) -> None:
        self.use_event({"push": {}})
        self.assertFalse(token_check.pr_has_label("token-growth-approved"))

    def test_label_with_null_labels(self) -> None:
        self.use_event({"pull_request": {"labels": None}})
        self.assertFalse(token_check.pr_has_label("x"))

    def test_base_sha_from_event(self) -> None:
        self.use_event({"pull_request": {"base": {"sha": "abc123"}}}, {"GITHUB_BASE_SHA": "env456"})
        self.assertEqual(token_check.pr_base_sha(), "abc123")

    def test_base_sha_falls_back_to_env(self) -> None:
        self.use_event({"pull_request": {"base": {}}}, {"GITHUB_BASE_SHA": "env456"})
        self.assertEqual(token_check.pr_base_sha(), "env456")


class WriteSummaryTest(unittest.TestCase):
    def test_writes_lines_when_env_set(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "summary.md"
            with mock.patch.dict(os.environ, {"GITHUB_STEP_SUMMARY": str(out)}):
                token_check.write_summary(["# T", "row"])
            self.assertEqual(out.read_text(encoding="utf-8"), "# T\nrow\n")

    def test_noop_when_env_unset(self) -> None:
        with (
            mock.patch.dict(os.environ, clean_env(), clear=True),
            mock.patch.object(Path, "write_text") as write_text,
            mock.patch.object(Path, "open") as path_open,
        ):
            token_check.write_summary(["x"])
        write_text.assert_not_called()
        path_open.assert_not_called()


class SyncPrStateTest(unittest.TestCase):
    def run_state(self, head: dict | None, base: str | None, base_sha: str | None):
        with tempfile.TemporaryDirectory() as tmp:
            path = Path(tmp) / "UPSTREAM.json"
            if head is not None:
                path.write_text(json.dumps(head), encoding="utf-8")
            with (
                mock.patch.object(token_check, "UPSTREAM_PATH", path),
                mock.patch.object(token_check, "git_show", return_value=base),
            ):
                return token_check.sync_pr_state(base_sha)

    def test_missing_file(self) -> None:
        self.assertEqual(self.run_state(None, None, "b"), (False, None, None))

    def test_non_string_sha(self) -> None:
        self.assertEqual(self.run_state({"last_synced_sha": 5}, None, "b"), (False, None, None))

    def test_no_base_counts_as_sync(self) -> None:
        self.assertEqual(self.run_state({"last_synced_sha": "new"}, None, None), (True, None, "new"))
        self.assertEqual(self.run_state({"last_synced_sha": "new"}, None, "b"), (True, None, "new"))

    def test_bumped_sha(self) -> None:
        base = json.dumps({"last_synced_sha": "old"})
        self.assertEqual(self.run_state({"last_synced_sha": "new"}, base, "b"), (True, "old", "new"))

    def test_unchanged_sha(self) -> None:
        base = json.dumps({"last_synced_sha": "same"})
        self.assertEqual(self.run_state({"last_synced_sha": "same"}, base, "b"), (False, None, None))


if __name__ == "__main__":
    unittest.main()
