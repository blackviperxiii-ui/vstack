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

import token_check  # noqa: E402

CI_ENV_KEYS = {
    "GITHUB_EVENT_PATH",
    "GITHUB_EVENT_NAME",
    "GITHUB_BASE_SHA",
    "GITHUB_STEP_SUMMARY",
}


def clean_env() -> dict[str, str]:
    return {k: v for k, v in os.environ.items() if k not in CI_ENV_KEYS}


class DeltaStatusTest(unittest.TestCase):
    def test_values(self) -> None:
        self.assertEqual(token_check.delta_status(False, True, 900), "new")
        self.assertEqual(token_check.delta_status(True, False, -900), "removed")
        self.assertEqual(token_check.delta_status(True, True, 50), "growth")
        self.assertEqual(token_check.delta_status(True, True, -50), "shrink")
        self.assertEqual(token_check.delta_status(True, True, 0), "same")


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
        self.assertIsNone(token_check.diff_base_sha())

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


class MainByEventTest(unittest.TestCase):
    """main() fails only on a stale tokens.json. Size never fails a run."""

    BASE = {"encoding": "cl100k_base", "skills": {"big-original": {"tokens": 600, "bytes": 1}}}

    def run_main(self, event: dict, name: str, head: dict, committed: dict | None = None):
        tmp = tempfile.TemporaryDirectory()
        self.addCleanup(tmp.cleanup)
        event_path = Path(tmp.name) / "event.json"
        event_path.write_text(json.dumps(event), encoding="utf-8")
        tokens_path = Path(tmp.name) / "tokens.json"
        tokens_path.write_text(json.dumps(committed or head), encoding="utf-8")
        summary_path = Path(tmp.name) / "summary.md"
        env = clean_env()
        env.update(
            {
                "GITHUB_EVENT_PATH": str(event_path),
                "GITHUB_EVENT_NAME": name,
                "GITHUB_STEP_SUMMARY": str(summary_path),
            }
        )
        base_files = {"tokens.json": json.dumps(self.BASE)}
        with (
            mock.patch.dict(os.environ, env, clear=True),
            mock.patch.object(token_check, "TOKENS_PATH", tokens_path),
            mock.patch.object(token_check, "run_count_tokens", return_value=head),
            mock.patch.object(token_check, "commit_exists", return_value=True),
            mock.patch.object(token_check, "git_show", side_effect=lambda ref, path: base_files.get(path)),
            mock.patch("sys.stderr"),
            mock.patch("sys.stdout"),
        ):
            code = token_check.main()
        summary = summary_path.read_text(encoding="utf-8") if summary_path.is_file() else ""
        return code, summary

    def test_push_without_changes_passes(self) -> None:
        code, summary = self.run_main({"before": "b1", "after": "a1"}, "push", self.BASE)
        self.assertEqual(code, 0)
        self.assertIn("| `big-original` | 600 | 600 | +0 | same |", summary)

    def test_schedule_checks_staleness_only(self) -> None:
        code, summary = self.run_main({}, "schedule", self.BASE)
        self.assertEqual(code, 0)
        self.assertEqual(summary, "")

    def test_growth_is_reported_not_failed(self) -> None:
        head = {"encoding": "cl100k_base", "skills": {"big-original": {"tokens": 6500, "bytes": 1}}}
        code, summary = self.run_main({"before": "b1", "after": "a1"}, "push", head)
        self.assertEqual(code, 0)
        self.assertIn("| `big-original` | 600 | 6500 | +5900 | growth |", summary)

    def test_new_skill_of_any_size_passes(self) -> None:
        head = {
            "encoding": "cl100k_base",
            "skills": {**self.BASE["skills"], "fresh": {"tokens": 4001, "bytes": 1}},
        }
        code, summary = self.run_main(
            {"pull_request": {"base": {"sha": "b1"}}}, "pull_request", head
        )
        self.assertEqual(code, 0)
        self.assertIn("| `fresh` | 0 | 4001 | +4001 | new |", summary)

    def test_stale_tokens_json_fails(self) -> None:
        head = {"encoding": "cl100k_base", "skills": {"big-original": {"tokens": 650, "bytes": 1}}}
        code, _ = self.run_main({"before": "b1", "after": "a1"}, "push", head, committed=self.BASE)
        self.assertEqual(code, 1)


if __name__ == "__main__":
    unittest.main()
