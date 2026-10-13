#!/usr/bin/env python3
"""Lint SKILL.md frontmatter and UPSTREAM.json."""

from __future__ import annotations

import json
import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
UPSTREAM_PATH = REPO_ROOT / "UPSTREAM.json"

FRONTMATTER_RE = re.compile(r"^---\s*\n(.*?)\n---\s*\n", re.DOTALL)


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
    return errors


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
            skill_md = skill_dir / "SKILL.md"
            if skill_dir.is_dir() and skill_md.is_file():
                errors.extend(lint_skill(skill_md))
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("lint OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
