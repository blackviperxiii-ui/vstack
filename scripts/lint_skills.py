#!/usr/bin/env python3
"""Lint SKILL.md frontmatter, quality gates, and UPSTREAM.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
UPSTREAM_PATH = REPO_ROOT / "UPSTREAM.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)
BANNED_FRONTMATTER_KEYS = frozenset({"mode", "reminder"})
MAX_SKILL_LINES = 500
SHORT_PRINCIPLE_LINES = 80
HEADING_RE = re.compile(r"^(#{1,6})[ \t]+(.+?)[ \t]*$", re.M)
PROCEDURE_TITLES = frozenset({"steps", "workflow", "procedure", "playbook"})
NUMBERED_TITLE_RE = re.compile(r"^(\d+)[.)]\s+(\S.*?)\s*$")
STEP_TITLE_RE = re.compile(r"(?i)^step\s+\d+\b\s*[:.)-]?\s*(.*?)\s*$")
RECOVERY_TITLE_RE = re.compile(
    r"(?i)^(error[- ]recovery|failure[- ]handling|troubleshooting|when (this|it) fails)\b"
)
FILLER_RE = re.compile(r"(?i)\b(?:try again|retry again|just retry)\b")
FENCE_RE = re.compile(r"(?im)^```(?:bash|sh|shell|console|zsh|powershell)\b")
TICK_RE = re.compile(
    r"`(?:python3?|pytest|npm|npx|node|git|grep|rg|sqlite3|curl|make|cargo|go|pip3?|gh|test)\b[^`]*`"
)
VERIFY_LINE_RE = re.compile(r"(?im)^(?:verify|check|expected)\s*:.+\S")
LIST_ITEM_RE = re.compile(r"(?m)^\d+[.)]\s+(.+?)\s*$")

# Shrink only. Do not add names. New skills are checked. A name that passes is an error.
LEGACY_EXEMPT = frozenset(
    {
        "automate-me",
        "av-qa-walkthrough",
        "bag-and-tag",
        "blast-radius",
        "create-verification-skill",
        "elevate",
        "follow-through",
        "how",
        "land-it",
        "lean-ci",
        "lean-tests",
        "no-comments",
        "optimize",
        "qa-walkthrough",
        "tdd",
        "updater",
        "why",
    }
)


def parse_simple_yaml_frontmatter(block: str) -> dict[str, str]:
    """Parse minimal YAML key: value lines (no nested structures)."""
    result: dict[str, str] = {}
    for line in block.splitlines():
        stripped = line.strip()
        if not stripped or stripped.startswith("#"):
            continue
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip().strip('"').strip("'")
        if key:
            result[key] = value
    return result


def lint_skill(path: Path) -> list[str]:
    errors: list[str] = []
    text = path.read_text(encoding="utf-8")
    match = FRONTMATTER_RE.match(text)
    if not match:
        errors.append(f"{path}: missing YAML frontmatter delimited by ---")
        return errors
    meta = parse_simple_yaml_frontmatter(match.group(1))
    if not meta.get("name"):
        errors.append(f"{path}: frontmatter missing 'name'")
    if not meta.get("description"):
        errors.append(f"{path}: frontmatter missing 'description'")
    for key in meta:
        if key in BANNED_FRONTMATTER_KEYS:
            errors.append(
                f"{path}: remove ignored frontmatter key '{key}' (Cursor does not apply it)"
            )
    return errors


def lint_name_matches_dir(path: Path) -> list[str]:
    """Hosts key a skill by its folder; a different frontmatter name hides it."""
    match = FRONTMATTER_RE.match(path.read_text(encoding="utf-8"))
    if not match:
        return []
    name = parse_simple_yaml_frontmatter(match.group(1)).get("name")
    if name and name != path.parent.name:
        return [f"{path}: frontmatter name '{name}' must match folder '{path.parent.name}'"]
    return []


def lint_skill_length(path: Path) -> list[str]:
    count = len(path.read_text(encoding="utf-8").splitlines())
    if count >= MAX_SKILL_LINES:
        return [f"{path}: SKILL.md has {count} lines, limit is {MAX_SKILL_LINES - 1}"]
    return []


def lint_mcp_json(skill_dir: Path) -> list[str]:
    if not skill_dir.is_dir():
        return []
    return [
        f"{hit}: skill directory must not contain .mcp.json"
        for hit in sorted(skill_dir.rglob(".mcp.json"))
    ]


def _headings(text: str) -> list[tuple[int, str, int, int]]:
    found: list[tuple[int, str, int, int]] = []
    for match in HEADING_RE.finditer(text):
        found.append(
            (len(match.group(1)), match.group(2).strip(), match.end(), match.start())
        )
    return found


def _section_end(
    heads: list[tuple[int, str, int, int]], index: int, level: int, text_len: int
) -> int:
    for level2, _, _, start2 in heads[index + 1 :]:
        if level2 <= level:
            return start2
    return text_len


def _normalize_title(title: str) -> str:
    return re.sub(r"\s+", " ", title.strip().lower())


def _is_procedure_heading(title: str) -> bool:
    if _normalize_title(title) in PROCEDURE_TITLES:
        return True
    if STEP_TITLE_RE.match(title) or NUMBERED_TITLE_RE.match(title):
        return True
    return False


def _recovery_bodies(text: str) -> list[str]:
    heads = _headings(text)
    bodies: list[str] = []
    for index, (level, title, body_start, _) in enumerate(heads):
        if not RECOVERY_TITLE_RE.match(_normalize_title(title)):
            continue
        end = _section_end(heads, index, level, len(text))
        bodies.append(text[body_start:end])
    return bodies


def lint_retry_filler(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    errors: list[str] = []
    for body in _recovery_bodies(text):
        match = FILLER_RE.search(body)
        if match:
            errors.append(
                f"{path}: low-signal retry filler {match.group(0)!r} in an error-recovery section"
            )
    return errors


def _collect_steps(text: str) -> list[str]:
    heads = _headings(text)
    steps: list[str] = []
    for index, (level, title, body_start, _) in enumerate(heads):
        numbered = NUMBERED_TITLE_RE.match(title)
        if numbered:
            steps.append(numbered.group(2).strip())
            continue
        step_heading = STEP_TITLE_RE.match(title)
        if step_heading:
            steps.append(step_heading.group(1).strip())
            continue
        if _normalize_title(title) not in PROCEDURE_TITLES:
            continue
        end = _section_end(heads, index, level, len(text))
        for item in LIST_ITEM_RE.finditer(text[body_start:end]):
            steps.append(item.group(1).strip())
    return steps


def _single_goal(goal: str) -> bool:
    if not goal.strip():
        return False
    plain = re.sub(r"`[^`]*`", "", goal).replace("**", "")
    parts = [part for part in re.split(r"[.!?;]", plain) if part.strip()]
    return len(parts) <= 1


def _has_verifiable_check(text: str) -> bool:
    return bool(FENCE_RE.search(text) or TICK_RE.search(text) or VERIFY_LINE_RE.search(text))


def _has_recovery_section(text: str) -> bool:
    return any(
        RECOVERY_TITLE_RE.match(_normalize_title(title)) for _, title, _, _ in _headings(text)
    )


def _is_procedural(text: str) -> bool:
    return any(_is_procedure_heading(title) for _, title, _, _ in _headings(text))


def _procedural_failures(path: Path, text: str) -> list[str]:
    if not _is_procedural(text):
        return []
    errors: list[str] = []
    steps = _collect_steps(text)
    if len(steps) < 2 or any(not _single_goal(step) for step in steps):
        errors.append(f"{path}: procedural skill needs numbered single-goal steps")
    if not _has_verifiable_check(text):
        errors.append(
            f"{path}: procedural skill needs a concrete command or verifiable check"
        )
    if not _has_recovery_section(text):
        errors.append(f"{path}: procedural skill needs an error-recovery section")
    return errors


def lint_procedural(path: Path) -> list[str]:
    text = path.read_text(encoding="utf-8")
    name = path.parent.name
    failures = _procedural_failures(path, text)
    if name in LEGACY_EXEMPT:
        if not failures:
            return [
                f"{path}: remove '{name}' from LEGACY_EXEMPT (procedural checks pass)"
            ]
        return []
    if (path.parent / "VENDORED.json").is_file():
        return []
    if name.startswith("principle-") and len(text.splitlines()) < SHORT_PRINCIPLE_LINES:
        return []
    return failures


def lint_upstream() -> list[str]:
    errors: list[str] = []
    if not UPSTREAM_PATH.is_file():
        errors.append(f"{UPSTREAM_PATH}: file not found")
        return errors
    try:
        data = json.loads(UPSTREAM_PATH.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        errors.append(f"{UPSTREAM_PATH}: invalid JSON: {exc}")
        return errors
    for field in ("repo", "path", "branch", "last_synced_sha", "mapping", "unported"):
        if field not in data:
            errors.append(f"{UPSTREAM_PATH}: missing field '{field}'")
    if "mapping" in data and not isinstance(data["mapping"], dict):
        errors.append(f"{UPSTREAM_PATH}: 'mapping' must be an object")
    if "unported" in data and not isinstance(data["unported"], list):
        errors.append(f"{UPSTREAM_PATH}: 'unported' must be a list")
    return errors


def main() -> int:
    errors: list[str] = []
    errors.extend(lint_upstream())
    if SKILLS_DIR.is_dir():
        for skill_dir in sorted(SKILLS_DIR.iterdir()):
            if not skill_dir.is_dir():
                continue
            errors.extend(lint_mcp_json(skill_dir))
            skill_md = skill_dir / "SKILL.md"
            if skill_md.is_file():
                errors.extend(lint_skill(skill_md))
                errors.extend(lint_name_matches_dir(skill_md))
                errors.extend(lint_skill_length(skill_md))
                errors.extend(lint_retry_filler(skill_md))
                errors.extend(lint_procedural(skill_md))
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("lint OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
