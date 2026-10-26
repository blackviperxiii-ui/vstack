#!/usr/bin/env python3
"""CI token checks: stale tokens.json, growth limits, sync PR rules."""

from __future__ import annotations

import json
import os
import subprocess
import sys
import urllib.error
import urllib.request
from pathlib import Path

import tiktoken

REPO_ROOT = Path(__file__).resolve().parent.parent
TOKENS_PATH = REPO_ROOT / "tokens.json"
UPSTREAM_PATH = REPO_ROOT / "UPSTREAM.json"
ENCODING_NAME = "cl100k_base"
NEW_SKILL_MAX_UPSTREAM_RATIO = 0.35
# Hard cap for vstack-native skills (no UPSTREAM.json mapping).
ORIGINAL_SKILL_MAX_TOKENS = 400
UPSTREAM_GROWTH_TOLERANCE = 0.05
APPROVAL_LABEL = "token-growth-approved"


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


def pr_has_label(label_name: str) -> bool:
    event = pr_event()
    pull_request = event.get("pull_request")
    if not isinstance(pull_request, dict):
        return False
    labels = pull_request.get("labels") or []
    return any(
        isinstance(label, dict) and label.get("name") == label_name for label in labels
    )


def pr_base_sha() -> str | None:
    event = pr_event()
    pull_request = event.get("pull_request")
    if isinstance(pull_request, dict):
        base = pull_request.get("base") or {}
        if isinstance(base, dict):
            sha = base.get("sha")
            if isinstance(sha, str):
                return sha
    return os.environ.get("GITHUB_BASE_SHA")


def sync_pr_state(base_sha: str | None) -> tuple[bool, str | None, str | None]:
    """True when this PR is an upstream sync (new or bumped last_synced_sha)."""
    if not UPSTREAM_PATH.is_file():
        return False, None, None
    head_raw = UPSTREAM_PATH.read_text(encoding="utf-8")
    head_upstream = json.loads(head_raw)
    new = head_upstream.get("last_synced_sha")
    if not isinstance(new, str):
        return False, None, None

    base_raw = git_show(base_sha, "UPSTREAM.json") if base_sha else None
    if base_raw is None:
        return True, None, new

    base_upstream = json.loads(base_raw)
    old = base_upstream.get("last_synced_sha")
    if isinstance(old, str) and old != new:
        return True, old, new
    return False, None, None


def count_upstream_tokens(sha: str, upstream_skill: str, upstream_meta: dict) -> int:
    repo = upstream_meta["repo"]
    path = upstream_meta["path"]
    branch = upstream_meta.get("branch", "main")
    url = (
        f"https://raw.githubusercontent.com/{repo}/{sha}/"
        f"{path}/skills/{upstream_skill}/SKILL.md"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            text = resp.read().decode("utf-8")
    except urllib.error.HTTPError:
        url_branch = (
            f"https://raw.githubusercontent.com/{repo}/{branch}/"
            f"{path}/skills/{upstream_skill}/SKILL.md"
        )
        with urllib.request.urlopen(url_branch, timeout=60) as resp:
            text = resp.read().decode("utf-8")
    enc = tiktoken.get_encoding(ENCODING_NAME)
    return len(enc.encode(text))


def growth_ratio(old: int, new: int) -> float:
    if old <= 0:
        return float("inf") if new > 0 else 0.0
    return (new - old) / old


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
    if not UPSTREAM_PATH.is_file():
        print(f"Missing {UPSTREAM_PATH}; cannot run token check", file=sys.stderr)
        return 1
    fresh = run_count_tokens()
    committed = load_json(TOKENS_PATH)
    if json.dumps(fresh, sort_keys=True) != json.dumps(committed, sort_keys=True):
        errors.append(
            "tokens.json is stale; run: python scripts/count_tokens.py and commit tokens.json"
        )

    base_sha = pr_base_sha()
    base_tokens_raw = git_show(base_sha, "tokens.json") if base_sha else None
    base_tokens: dict[str, object] = (
        json.loads(base_tokens_raw) if base_tokens_raw else {"skills": {}}
    )

    sync_pr, old_upstream_sha, new_upstream_sha = sync_pr_state(base_sha)
    approved = pr_has_label(APPROVAL_LABEL)
    upstream_meta = load_json(UPSTREAM_PATH)
    mapping = upstream_meta.get("mapping", {})
    if not isinstance(mapping, dict):
        mapping = {}

    current_skills = fresh.get("skills", {})
    base_skills = base_tokens.get("skills", {})
    if not isinstance(current_skills, dict):
        current_skills = {}
    if not isinstance(base_skills, dict):
        base_skills = {}

    all_skill_names = sorted(set(current_skills) | set(base_skills))
    table_rows: list[str] = [
        "## Token delta (PR vs base)",
        "",
        "| Skill | Base tokens | Head tokens | Δ | Status |",
        "| --- | ---: | ---: | ---: | --- |",
    ]

    for skill in all_skill_names:
        base_t = skill_tokens(base_tokens, skill)
        head_t = skill_tokens(fresh, skill)
        if base_t is None and head_t is None:
            continue
        base_t = base_t or 0
        head_t = head_t or 0
        delta = head_t - base_t
        status = "ok"
        if skill not in base_skills and skill in current_skills:
            status = "new"
            upstream_name = mapping.get(skill)
            if isinstance(upstream_name, str):
                if not sync_pr:
                    errors.append(
                        f"New skill '{skill}' is only allowed when last_synced_sha changes (sync PR)"
                    )
                    status = "rejected (not sync PR)"
                elif new_upstream_sha:
                    up_tokens = count_upstream_tokens(
                        new_upstream_sha, upstream_name, upstream_meta
                    )
                    max_allowed = int(up_tokens * NEW_SKILL_MAX_UPSTREAM_RATIO)
                    if head_t > max_allowed:
                        errors.append(
                            f"New skill '{skill}' has {head_t} tokens; "
                            f"max {max_allowed} (35% of upstream {upstream_name} at {up_tokens})"
                        )
                        status = "rejected (too large)"
                    else:
                        status = f"new (≤35% upstream: {head_t}/{up_tokens})"
                else:
                    errors.append(
                        f"Sync PR missing new upstream SHA for mapped skill '{skill}'"
                    )
                    status = "rejected (no upstream sha)"
            elif head_t > ORIGINAL_SKILL_MAX_TOKENS:
                errors.append(
                    f"New original skill '{skill}' has {head_t} tokens; "
                    f"max {ORIGINAL_SKILL_MAX_TOKENS}"
                )
                status = "rejected (original too large)"
            else:
                status = f"new (original ≤{ORIGINAL_SKILL_MAX_TOKENS})"
        elif delta > 0:
            status = "growth"
            if approved:
                status = "growth (label approved)"
            elif sync_pr and isinstance(upstream_name := mapping.get(skill), str):
                if old_upstream_sha and new_upstream_sha:
                    old_up = count_upstream_tokens(old_upstream_sha, upstream_name, upstream_meta)
                    new_up = count_upstream_tokens(new_upstream_sha, upstream_name, upstream_meta)
                    up_ratio = growth_ratio(old_up, new_up)
                    local_ratio = growth_ratio(base_t, head_t)
                    limit = up_ratio + UPSTREAM_GROWTH_TOLERANCE
                    if local_ratio <= limit:
                        status = (
                            f"growth (sync OK: local {local_ratio:.1%} ≤ "
                            f"upstream {up_ratio:.1%}+{UPSTREAM_GROWTH_TOLERANCE:.0%})"
                        )
                    else:
                        errors.append(
                            f"Skill '{skill}' grew {local_ratio:.1%} but upstream "
                            f"'{upstream_name}' grew {up_ratio:.1%}; "
                            f"limit is upstream+5% ({limit:.1%})"
                        )
                        status = "rejected (growth > upstream)"
                else:
                    errors.append(f"Sync PR missing old/new upstream SHAs for '{skill}'")
            else:
                errors.append(
                    f"Skill '{skill}' grew by {delta} tokens ({base_t} → {head_t}); "
                    f"sync last_synced_sha or add label {APPROVAL_LABEL}"
                )
                status = "rejected (growth)"
        elif delta < 0:
            status = "shrink"

        table_rows.append(
            f"| `{skill}` | {base_t} | {head_t} | {delta:+d} | {status} |"
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
