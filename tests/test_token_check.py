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

CI_ENV_KEYS = {
    "GITHUB_EVENT_PATH",
    "GITHUB_EVENT_NAME",
    "GITHUB_BASE_SHA",
    "GITHUB_STEP_SUMMARY",
    "GITHUB_REPOSITORY",
    "GITHUB_TOKEN",
}


def clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CI_ENV_KEYS}


class OriginalSkillCapTest(unittest.TestCase):
    def test_cap_is_lean(self) -> None:
        self.assertEqual(token_check.ORIGINAL_SKILL_MAX_TOKENS, 400)
        self.assertLess(token_check.ORIGINAL_SKILL_MAX_TOKENS, 1000)


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
        self.assertIsNone(token_check.diff_base_sha())

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
        self.assertEqual(token_check.diff_base_sha(), "abc123")

    def test_base_sha_falls_back_to_env(self) -> None:
        self.use_event({"pull_request": {"base": {}}}, {"GITHUB_BASE_SHA": "env456"})
        self.assertEqual(token_check.diff_base_sha(), "env456")

    def test_push_uses_previous_tip(self) -> None:
        self.use_event({"before": "old1", "after": "new1"}, {"GITHUB_EVENT_NAME": "push"})
        self.assertEqual(token_check.diff_base_sha(), "old1")

    def test_new_branch_push_has_no_base(self) -> None:
        self.use_event({"before": "0" * 40, "after": "new1"}, {"GITHUB_EVENT_NAME": "push"})
        self.assertIsNone(token_check.diff_base_sha())

    def test_merge_group_base(self) -> None:
        self.use_event({"merge_group": {"base_sha": "mg1"}}, {"GITHUB_EVENT_NAME": "merge_group"})
        self.assertEqual(token_check.diff_base_sha(), "mg1")

    def test_schedule_has_no_base(self) -> None:
        self.use_event({"schedule": "25 8 * * *"}, {"GITHUB_EVENT_NAME": "schedule"})
        self.assertIsNone(token_check.diff_base_sha())


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


class MainByEventTest(unittest.TestCase):
    """main() on push and schedule runs, where the PR payload is absent.

    Push runs used to compare against an empty base, so every skill counted as
    new and any original skill over the cap failed every beta push and nightly.
    """

    BASE = {"encoding": "cl100k_base", "skills": {"big-original": {"tokens": 600, "bytes": 1}}}
    UPSTREAM = {"last_synced_sha": "up1", "mapping": {}}

    def run_main(self, event: dict, name: str, head: dict, pr_labels: list[str] | None = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        event_path = Path(tmp.name) / "event.json"
        event_path.write_text(json.dumps(event), encoding="utf-8")
        tokens_path = Path(tmp.name) / "tokens.json"
        tokens_path.write_text(json.dumps(head), encoding="utf-8")
        upstream_path = Path(tmp.name) / "UPSTREAM.json"
        upstream_path.write_text(json.dumps(self.UPSTREAM), encoding="utf-8")
        env = clean_env()
        env.update(
            {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_EVENT_NAME": name,
                "GITHUB_REPOSITORY": "o/r",
            }
        )
        base_files = {"tokens.json": json.dumps(self.BASE), "UPSTREAM.json": json.dumps(self.UPSTREAM)}
        pulls = [{"labels": [{"name": n} for n in pr_labels or []]}]
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(token_check, "TOKENS_PATH", tokens_path),
            mock.patch.object(token_check, "UPSTREAM_PATH", upstream_path),
            mock.patch.object(token_check, "run_count_tokens", return_value=head),
            mock.patch.object(token_check, "commit_exists", return_value=True),
            mock.patch.object(token_check, "git_show", side_effect=lambda ref, path: base_files.get(path)),
            mock.patch.object(token_check, "github_api", return_value=pulls) as api,
            mock.patch.object(token_check, "count_upstream_tokens") as upstream,
            mock.patch("sys.stderr"),
            mock.patch("sys.stdout"),
        ):
            code = token_check.main()
        upstream.assert_not_called()
        return code, api

    def test_push_without_changes_passes(self) -> None:
        code, api = self.run_main({"before": "b1", "after": "a1"}, "push", self.BASE)
        self.assertEqual(code, 0)
        api.assert_not_called()

    def test_schedule_checks_staleness_only(self) -> None:
        code, _ = self.run_main({}, "schedule", self.BASE)
        self.assertEqual(code, 0)

    def test_push_growth_still_fails_without_label(self) -> None:
        head = {"encoding": "cl100k_base", "skills": {"big-original": {"tokens": 650, "bytes": 1}}}
        code, api = self.run_main({"before": "b1", "after": "a1"}, "push", head)
        self.assertEqual(code, 1)
        api.assert_called_once_with("/repos/o/r/commits/a1/pulls")

    def test_push_growth_passes_with_merged_pr_label(self) -> None:
        head = {"encoding": "cl100k_base", "skills": {"big-original": {"tokens": 650, "bytes": 1}}}
        code, _ = self.run_main(
            {"before": "b1", "after": "a1"}, "push", head, pr_labels=["token-growth-approved"]
        )
        self.assertEqual(code, 0)

    def test_new_original_over_cap_still_fails_on_push(self) -> None:
        head = {
            "encoding": "cl100k_base",
            "skills": {**self.BASE["skills"], "fresh": {"tokens": 401, "bytes": 1}},
        }
        code, _ = self.run_main({"before": "b1", "after": "a1"}, "push", head)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
