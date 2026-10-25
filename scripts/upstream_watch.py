#!/usr/bin/env python3
"""Compare UPSTREAM.json to latest pstack commit; open or update upstream-sync issue."""

from __future__ import annotations

import json
import os
import sys
import urllib.error
import urllib.request
from pathlib import Path

import tiktoken

REPO_ROOT = Path(__file__).resolve().parent.parent
UPSTREAM_PATH = REPO_ROOT / "UPSTREAM.json"
ENCODING_NAME = "cl100k_base"
ISSUE_LABEL = "upstream-sync"
# Land sync PRs on beta; watch must read UPSTREAM.json from this line, not main.
INTEGRATION_BRANCH = "beta"
GITHUB_API = "https://api.github.com"
COMMITS_PER_PAGE = 100
MAX_COMMIT_PAGES = 10
TRUNCATED_NOTE = (
    f"_Commit list truncated after {MAX_COMMIT_PAGES * COMMITS_PER_PAGE} commits; "
    "synced commit not reached. Use the compare link._"
)


def load_upstream() -> dict[str, object]:
    return json.loads(UPSTREAM_PATH.read_text(encoding="utf-8"))


def api_request(
    method: str,
    url: str,
    token: str,
    body: dict | None = None,
) -> dict | list:
    data = json.dumps(body).encode("utf-8") if body is not None else None
    headers = {
        "Authorization": f"Bearer {token}",
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
    }
    if data is not None:
        headers["Content-Type"] = "application/json"
    req = urllib.request.Request(url, data=data, headers=headers, method=method)
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def fetch_json(url: str) -> dict | list:
    req = urllib.request.Request(url, headers={"Accept": "application/vnd.github+json"})
    with urllib.request.urlopen(req, timeout=120) as resp:
        return json.loads(resp.read().decode("utf-8"))


def latest_pstack_commit(upstream: dict[str, object]) -> str:
    repo = upstream["repo"]
    branch = upstream.get("branch", "main")
    path = upstream["path"]
    url = (
        f"{GITHUB_API}/repos/{repo}/commits?"
        f"sha={branch}&path={path}&per_page=1"
    )
    commits = fetch_json(url)
    if not commits:
        raise RuntimeError(f"No commits found for {repo}/{path}")
    return commits[0]["sha"]


def compare_commits(upstream: dict[str, object], base: str, head: str) -> dict:
    repo = upstream["repo"]
    url = f"{GITHUB_API}/repos/{repo}/compare/{base}...{head}"
    return fetch_json(url)  # type: ignore[return-value]


def is_sync_needed(last_synced: str, latest: str, compare: dict | None) -> bool:
    """True only when upstream tip has commits not already in last_synced_sha.

    last_synced_sha may sit on a non-pstack merge after the latest path commit.
    Equality alone then false-alarms; GitHub compare status \"behind\"/\"identical\"
    means the tracked tip already contains latest.
    """
    if last_synced == latest:
        return False
    if compare is None:
        return True
    status = compare.get("status")
    if status in ("identical", "behind"):
        return False
    ahead = compare.get("ahead_by")
    return isinstance(ahead, int) and ahead > 0


def commits_touching_path(
    upstream: dict[str, object], base: str, head: str
) -> tuple[list[dict], bool]:
    """Walk path-specific history from head until base (same scope as latest_pstack_commit).

    Returns (commits, truncated). truncated is True when MAX_COMMIT_PAGES pages were
    read without finding base or reaching the end of history, so the list is partial.
    """
    repo = upstream["repo"]
    path = upstream["path"]
    result: list[dict] = []
    for page in range(1, MAX_COMMIT_PAGES + 1):
        url = (
            f"{GITHUB_API}/repos/{repo}/commits?sha={head}&path={path}"
            f"&per_page={COMMITS_PER_PAGE}&page={page}"
        )
        commits = fetch_json(url)
        if not isinstance(commits, list):
            return result, False
        for commit in commits:
            sha = commit.get("sha")
            if not isinstance(sha, str):
                continue
            if sha == base:
                return result, False
            result.append(commit)
        if len(commits) < COMMITS_PER_PAGE:
            return result, False
    return result, True


def count_tokens_text(text: str) -> int:
    return len(tiktoken.get_encoding(ENCODING_NAME).encode(text))


def fetch_upstream_skill_at(sha: str, upstream: dict, skill: str) -> str | None:
    repo = upstream["repo"]
    path = upstream["path"]
    url = (
        f"https://raw.githubusercontent.com/{repo}/{sha}/"
        f"{path}/skills/{skill}/SKILL.md"
    )
    try:
        with urllib.request.urlopen(url, timeout=60) as resp:
            return resp.read().decode("utf-8")
    except urllib.error.HTTPError:
        return None


def classify_file(
    filename: str,
    mapping: dict[str, str],
    unported: set[str],
) -> str:
    # filename like pstack/skills/foo/SKILL.md
    parts = filename.split("/")
    if len(parts) >= 3 and parts[-1] == "SKILL.md":
        skill = parts[-2]
        if skill in mapping.values():
            return "mapped"
        if skill in unported:
            return "unported"
        return "new"
    return "other"


def build_issue_body(
    upstream: dict[str, object],
    last_synced: str,
    latest: str,
    compare: dict,
) -> str:
    mapping = upstream.get("mapping", {})
    if not isinstance(mapping, dict):
        mapping = {}
    unported_list = upstream.get("unported", [])
    unported = set(unported_list) if isinstance(unported_list, list) else set()

    grouped: dict[str, list[str]] = {
        "mapped": [],
        "unported": [],
        "new": [],
        "other": [],
    }
    for file_info in compare.get("files", []):
        fn = file_info.get("filename", "")
        bucket = classify_file(fn, mapping, unported)
        status = file_info.get("status", "")
        grouped[bucket].append(f"- `{fn}` ({status})")

    lines = [
        "# Upstream pstack drift",
        "",
        f"Integration line: `{INTEGRATION_BRANCH}` "
        "(compare `UPSTREAM.json` `last_synced_sha` on this branch; land sync PRs here).",
        "",
        f"Tracked sync point (`last_synced_sha` on `{INTEGRATION_BRANCH}`): `{last_synced}`",
        f"Latest commit touching `{upstream['path']}/`: `{latest}`",
        "",
        f"Compare: https://github.com/{upstream['repo']}/compare/{last_synced}...{latest}",
        "",
        "## Commits",
        "",
    ]
    commits, truncated = commits_touching_path(upstream, last_synced, latest)
    if truncated:
        lines.append(TRUNCATED_NOTE)
    for commit in commits:
        sha = commit.get("sha", "")[:7]
        msg = (commit.get("commit") or {}).get("message", "").split("\n")[0]
        lines.append(f"- `{sha}` {msg}")

    for section, title in (
        ("mapped", "Changed files (mapped skills)"),
        ("unported", "Changed files (unported upstream skills)"),
        ("new", "Changed files (new upstream skills)"),
    ):
        lines.extend(["", f"## {title}", ""])
        items = grouped[section]
        lines.extend(items if items else ["- (none)"])

    lines.extend(["", "## Upstream token deltas (cl100k_base)", ""])
    lines.append("| Upstream skill | Tokens @ synced | Tokens @ latest | Δ |")
    lines.append("| --- | ---: | ---: | ---: |")

    touched_skills: set[str] = set()
    for file_info in compare.get("files", []):
        fn = file_info.get("filename", "")
        parts = fn.split("/")
        if len(parts) >= 3 and parts[-1] == "SKILL.md":
            touched_skills.add(parts[-2])

    for skill in sorted(touched_skills):
        old_text = fetch_upstream_skill_at(last_synced, upstream, skill)
        new_text = fetch_upstream_skill_at(latest, upstream, skill)
        old_t = count_tokens_text(old_text) if old_text else 0
        new_t = count_tokens_text(new_text) if new_text else 0
        lines.append(f"| `{skill}` | {old_t} | {new_t} | {new_t - old_t:+d} |")

    lines.extend(
        [
            "",
            "---",
            "_This issue is managed by `.github/workflows/upstream-watch.yml` "
            f"(checks out `{INTEGRATION_BRANCH}`). "
            f"Port on `{INTEGRATION_BRANCH}`, bump `last_synced_sha`, open a sync PR there._",
        ]
    )
    return "\n".join(lines)


def find_open_issue(repo: str, token: str) -> int | None:
    url = f"{GITHUB_API}/repos/{repo}/issues?state=open&labels={ISSUE_LABEL}&per_page=10"
    issues = api_request("GET", url, token)
    if not isinstance(issues, list):
        return None
    for issue in issues:
        if isinstance(issue, dict) and "pull_request" not in issue:
            num = issue.get("number")
            if isinstance(num, int):
                return num
    return None


def close_open_sync_issue(repo: str, token: str, last_synced: str) -> int | None:
    """Close a stale upstream-sync issue when beta tip already covers latest."""
    existing = find_open_issue(repo, token)
    if existing is None:
        return None
    api_request(
        "POST",
        f"{GITHUB_API}/repos/{repo}/issues/{existing}/comments",
        token,
        {
            "body": (
                f"Closing: `{INTEGRATION_BRANCH}` `last_synced_sha` `{last_synced}` "
                "already includes the current upstream tip (no sync needed)."
            ),
        },
    )
    api_request(
        "PATCH",
        f"{GITHUB_API}/repos/{repo}/issues/{existing}",
        token,
        {"state": "closed", "state_reason": "completed"},
    )
    return existing


def dry_run_report(upstream: dict[str, object], last_synced: str, latest: str) -> int:
    print(f"Drift: {last_synced[:7]} → {latest[:7]} (integration: {INTEGRATION_BRANCH})")
    print(
        f"Compare: https://github.com/{upstream['repo']}/compare/"
        f"{last_synced}...{latest}"
    )
    commits, truncated = commits_touching_path(upstream, last_synced, latest)
    suffix = "+ (truncated)" if truncated else ""
    print(f"Commits touching {upstream['path']}/: {len(commits)}{suffix}")
    for commit in commits[:10]:
        sha = commit.get("sha", "")[:7]
        msg = (commit.get("commit") or {}).get("message", "").split("\n")[0]
        print(f"  {sha} {msg}")
    if len(commits) > 10:
        print(f"  ... and {len(commits) - 10} more")
    return 0


def main() -> int:
    argv = sys.argv[1:]
    dry_run = "--dry-run" in argv

    upstream = load_upstream()
    last_synced = str(upstream["last_synced_sha"])
    latest = latest_pstack_commit(upstream)

    compare: dict | None = None
    if last_synced != latest:
        compare = compare_commits(upstream, last_synced, latest)

    if not is_sync_needed(last_synced, latest, compare):
        print(
            f"Up to date on {INTEGRATION_BRANCH} "
            f"(last_synced_sha {last_synced[:7]}; upstream tip {latest[:7]})"
        )
        if dry_run:
            return 0
        token = os.environ.get("GITHUB_TOKEN")
        github_repo = os.environ.get("GITHUB_REPOSITORY")
        if token and github_repo:
            closed = close_open_sync_issue(github_repo, token, last_synced)
            if closed is not None:
                print(f"Closed stale issue #{closed}")
        return 0

    if dry_run:
        return dry_run_report(upstream, last_synced, latest)

    token = os.environ.get("GITHUB_TOKEN")
    github_repo = os.environ.get("GITHUB_REPOSITORY")
    if not token or not github_repo:
        print(
            "GITHUB_TOKEN and GITHUB_REPOSITORY required (or pass --dry-run)",
            file=sys.stderr,
        )
        return 1

    assert compare is not None
    body = build_issue_body(upstream, last_synced, latest, compare)
    title = (
        f"Upstream pstack sync available on {INTEGRATION_BRANCH} "
        f"({last_synced[:7]} → {latest[:7]})"
    )

    existing = find_open_issue(github_repo, token)
    if existing:
        api_request(
            "PATCH",
            f"{GITHUB_API}/repos/{github_repo}/issues/{existing}",
            token,
            {"title": title, "body": body},
        )
        print(f"Updated issue #{existing}")
    else:
        issue = api_request(
            "POST",
            f"{GITHUB_API}/repos/{github_repo}/issues",
            token,
            {"title": title, "body": body, "labels": [ISSUE_LABEL]},
        )
        num = issue.get("number") if isinstance(issue, dict) else None
        print(f"Created issue #{num}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
