#!/usr/bin/env python3
"""Fail CI on likely committed secrets (patterns only; no network)."""

from __future__ import annotations

import re
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
SCAN_ROOTS = (REPO_ROOT / "skills", REPO_ROOT / "scripts", REPO_ROOT)
SKIP_DIRS = {".git", ".github", "__pycache__"}
SKIP_FILES = {"check_secrets.py"}

PATTERNS: list[tuple[str, re.Pattern[str]]] = [
    (
        "GitHub token",
        re.compile(r"\bghp_[A-Za-z0-9]{20,}\b"),
    ),
    (
        "GitHub fine-grained PAT",
        re.compile(r"\bgithub_pat_[A-Za-z0-9_]{20,}\b"),
    ),
    (
        "AWS access key id",
        re.compile(r"\bAKIA[0-9A-Z]{16}\b"),
    ),
    (
        "Private key block",
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
    ),
    (
        "OpenAI API key",
        re.compile(r"\bsk-[A-Za-z0-9]{20,}\b"),
    ),
    (
        "Slack token",
        re.compile(r"\bxox[baprs]-[A-Za-z0-9-]{10,}\b"),
    ),
]


def iter_text_files() -> list[Path]:
    paths: list[Path] = []
    for root in SCAN_ROOTS:
        if not root.is_dir():
            continue
        for path in root.rglob("*"):
            if not path.is_file():
                continue
            if any(part in SKIP_DIRS for part in path.parts):
                continue
            if path.name in SKIP_FILES:
                continue
            if path.suffix in {".png", ".jpg", ".jpeg", ".gif", ".webp", ".pyc"}:
                continue
            paths.append(path)
    return sorted(set(paths))


def scan_file(path: Path) -> list[str]:
    errors: list[str] = []
    try:
        text = path.read_text(encoding="utf-8")
    except (UnicodeDecodeError, OSError):
        return errors
    rel = path.relative_to(REPO_ROOT)
    for label, pattern in PATTERNS:
        if pattern.search(text):
            errors.append(f"{rel}: possible {label}")
    return errors


def main() -> int:
    errors: list[str] = []
    for path in iter_text_files():
        errors.extend(scan_file(path))
    if errors:
        for err in errors:
            print(err, file=sys.stderr)
        return 1
    print("secret scan OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
