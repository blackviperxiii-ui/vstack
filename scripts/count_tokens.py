#!/usr/bin/env python3
"""Count cl100k_base tokens and bytes for each skills/*/SKILL.md; write tokens.json."""

from __future__ import annotations

import json
import sys
from pathlib import Path

import tiktoken

REPO_ROOT = Path(__file__).resolve().parent.parent
SKILLS_DIR = REPO_ROOT / "skills"
OUTPUT_PATH = REPO_ROOT / "tokens.json"
ENCODING_NAME = "cl100k_base"


def skill_dirs() -> list[Path]:
    if not SKILLS_DIR.is_dir():
        return []
    return sorted(
        p for p in SKILLS_DIR.iterdir() if p.is_dir() and (p / "SKILL.md").is_file()
    )


def count_file(path: Path, enc: tiktoken.Encoding) -> tuple[int, int]:
    data = path.read_bytes()
    text = data.decode("utf-8")
    tokens = len(enc.encode(text))
    return tokens, len(data)


def build_report() -> dict[str, object]:
    enc = tiktoken.get_encoding(ENCODING_NAME)
    skills: dict[str, dict[str, int]] = {}
    for skill_dir in skill_dirs():
        name = skill_dir.name
        tokens, nbytes = count_file(skill_dir / "SKILL.md", enc)
        skills[name] = {"tokens": tokens, "bytes": nbytes}
    return {
        "encoding": ENCODING_NAME,
        "skills": skills,
    }


def write_report(report: dict[str, object], path: Path = OUTPUT_PATH) -> None:
    path.write_text(
        json.dumps(report, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def main() -> int:
    report = build_report()
    write_report(report)
    print(f"Wrote {OUTPUT_PATH} ({len(report['skills'])} skills)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
