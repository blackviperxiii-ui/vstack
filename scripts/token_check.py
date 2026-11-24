#!/usr/bin/env python3
"""CI token report: fail on a stale tokens.json, report per-skill deltas.

Skill size is reported, never capped. A skill earns its length by making the
agent do the job right the first time; a size limit only trims the procedure
that prevents rework.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS_PATH = REPO_ROOT / "tokens.json"


def run_count_tokens() -> dict[str, object]:
    subprocess.run(
        [sys.executable, str(REPO_ROOT / "scripts" / "count_tokens.py")],
        check=True,
        cwd=REPO_ROOT,
    )
    return json.loads(TOKENS_PATH.read_text(encoding="utf-8"))


def load_json(path: Path) -> dict[str, object]:
    return json.loads(path.read_text(encoding="utf-8"))


def git_show(ref: str, path: str) -> str | None:
    try:
        return subprocess.check_output(
            ["git", "show", f"{ref}:{path}"],
            cwd=REPO_ROOT,
            stderr=subprocess.DEVNULL,
            text=True,
        )
    except subprocess.CalledProcessError:
        return None


def pr_event() -> dict[str, object]:
    event_path = os.environ.get("GITHUB_EVENT_PATH")
    if not event_path:
        return {}
    return json.loads(Path(event_path).read_text(encoding="utf-8"))


def event_name() -> str:
    return os.environ.get("GITHUB_EVENT_NAME", "")


def commit_exists(sha: str) -> bool:
    return (
        subprocess.run(
            ["git", "cat-file", "-e", f"{sha}^{{commit}}"],
            cwd=REPO_ROOT,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
        ).returncode
        == 0
    )


def diff_base_sha() -> str | None:
    """The commit this run's changes are measured against.

    pull_request: the PR base. merge_group: the queue base. push: the branch tip
    before the push (absent for a new branch). Other events (schedule,
    workflow_dispatch) have no base unless GITHUB_BASE_SHA is set.
    """
    event = pr_event()
    candidates: list[object] = []
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        base = pull_request.get("base") or {}
        if isinstance(base, dict):
            candidates.append(base.get("sha"))
    merge_group = event.get("merge_group")
    if isinstance(merge_group, dict):
        candidates.append(merge_group.get("base_sha"))
    if event_name() == "push":
        candidates.append(event.get("before"))
    candidates.append(os.environ.get("GITHUB_BASE_SHA"))
    for sha in candidates:
        if isinstance(sha, str) and sha.strip("0"):
            return sha
    return None


def delta_status(in_base: bool, in_head: bool, delta: int) -> str:
    if not in_base:
        return "new"
    if not in_head:
        return "removed"
    if delta > 0:
        return "growth"
    if delta < 0:
        return "shrink"
    return "same"


def skill_tokens(report: dict[str, object], skill: str) -> int | None:
    skills = report.get("skills")
    if not isinstance(skills, dict):
        return None
    entry = skills.get(skill)
    if not isinstance(entry, dict):
        return None
    tokens = entry.get("tokens")
    return int(tokens) if isinstance(tokens, int) else None


def write_summary(lines: list[str]) -> None:
    summary_path = os.environ.get("GITHUB_STEP_SUMMARY")
    if not summary_path:
        return
    Path(summary_path).write_text("\n".join(lines) + "\n", encoding="utf-8")


def main() -> int:
    errors: list[str] = []
    fresh = run_count_tokens()
    committed = load_json(TOKENS_PATH)
    if json.dumps(fresh, sort_keys=True) != json.dumps(committed, sort_keys=True):
        errors.append(
            "tokens.json is stale; run: python scripts/count_tokens.py and commit tokens.json"
        )

    base_sha = diff_base_sha()
    if base_sha and not commit_exists(base_sha):
        errors.append(
            f"Base commit {base_sha} is not in this checkout; the token delta cannot be reported"
        )
        base_sha = None
    if base_sha is None:
        # Deltas are relative to a base. Without one (schedule,
        # workflow_dispatch, first push of a branch) only staleness is checked.
        if errors:
            for err in errors:
                print(err, file=sys.stderr)
            return 1
        print(f"token check OK (tokens.json fresh; no diff base for '{event_name() or 'local'}' run)")
        return 0

    base_tokens_raw = git_show(base_sha, "tokens.json")
    base_tokens: dict[str, object] = (
        json.loads(base_tokens_raw) if base_tokens_raw else {"skills": {}}
    )

    current_skills = fresh.get("skills", {})
    base_skills = base_tokens.get("skills", {})
    if not isinstance(current_skills, dict):
        current_skills = {}
    if not isinstance(base_skills, dict):
        base_skills = {}

    table_rows: list[str] = [
        "## Token delta (head vs base)",
        "",
        "Informational only. Skill size is never a reason to fail a change.",
        "",
        "| Skill | Base tokens | Head tokens | Δ | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]
    for skill in sorted(set(current_skills) | set(base_skills)):
        base_t = skill_tokens(base_tokens, skill) or 0
        head_t = skill_tokens(fresh, skill) or 0
        table_rows.append(
            f"| `{skill}` | {base_t} | {head_t} | {head_t - base_t:+d} | "
            f"{delta_status(skill in base_skills, skill in current_skills, head_t - base_t)} |"
        )

    write_summary(table_rows)

    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1

    print("token check OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
