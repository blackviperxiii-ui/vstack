#!/usr/bin/env python3
"""Vendor the Database Architect agent from claude-code-templates at a pinned commit.

    python3 scripts/sync_database_architect.py --ref <40-char commit>             # sync
    python3 scripts/sync_database_architect.py --ref <commit> --source DIR        # existing clone
    python3 scripts/sync_database_architect.py --check                            # verify

Sync reads the agent file and the repository LICENSE straight from the pinned
commit (`git cat-file`, no checkout), so nothing upstream runs. It refuses
moving refs, and it stops when the agent text has hidden Unicode or a red flag
(download-and-run commands, credential paths, instruction overrides). The agent
is copied byte for byte to `skills/database-architect/AGENT.md`; vstack's own
SKILL.md and NOTICE.md are never touched. VENDORED.json records the commit and
a SHA-256 of every vendored file; --check fails on any drift.
"""

from __future__ import annotations

import argparse
import hashlib
import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
from sync_modern_web_guidance import HIDDEN_RE, SyncError, sha256, validate_ref  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / "skills" / "database-architect"
UPSTREAM_URL = "https://github.com/davila7/claude-code-templates.git"
UPSTREAM_REPO = "davila7/claude-code-templates"
UPSTREAM_PATH = "cli-tool/components/agents/database/database-architect.md"
# vendored file -> path in the upstream repository
FILES = {"AGENT.md": UPSTREAM_PATH, "LICENSE": "LICENSE"}
VSTACK_OWNED = frozenset({"SKILL.md", "NOTICE.md"})
GENERATED = frozenset({"VENDORED.json"})

# Text an agent prompt has no reason to carry. Any hit blocks the sync until a
# human has read the upstream change.
RED_FLAGS = {
    "download piped to a shell": re.compile(r"\b(curl|wget)\b[^\n]*\|\s*(ba|z)?sh\b", re.I),
    "fetches a URL with curl or wget": re.compile(r"\b(curl|wget)\s+\S*https?://", re.I),
    "unpinned npx package": re.compile(r"\bnpx\s+(-y\s+)?[\w@/.-]+@latest\b", re.I),
    "credential path": re.compile(r"~/\.(ssh|aws|grok|config/gh)\b|\bauth\.json\b|\bid_rsa\b", re.I),
    "instruction override": re.compile(
        r"\b(ignore|disregard|forget)\b[^\n]{0,30}\b(previous|prior|above|earlier|system)\b[^\n]{0,20}\b(instructions?|prompts?|rules?)\b",
        re.I,
    ),
    "hides output from the user": re.compile(r"\b(do not|don't|never)\s+(tell|show|mention to)\s+the\s+user\b", re.I),
}


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def read_blob(src: Path, commit: str, path: str) -> bytes:
    return subprocess.run(
        ["git", "cat-file", "blob", f"{commit}:{path}"], cwd=src, check=True, capture_output=True
    ).stdout


def scan(name: str, data: bytes) -> list[str]:
    """Problems that block a sync: hidden Unicode or a red flag in the agent text."""
    problems = []
    for n, line in enumerate(data.decode("utf-8").splitlines(), 1):
        if HIDDEN_RE.search(line):
            problems.append(f"{name}:{n}: hidden Unicode character")
        for label, pattern in RED_FLAGS.items():
            if pattern.search(line):
                problems.append(f"{name}:{n}: {label}")
    return problems


def write_manifest(dest: Path, commit: str) -> None:
    hashes = {f: sha256(dest / f) for f in sorted(FILES)}
    digest = hashlib.sha256("".join(f"{h}  {f}\n" for f, h in hashes.items()).encode()).hexdigest()
    manifest = {
        "upstream": UPSTREAM_REPO,
        "path": UPSTREAM_PATH,
        "skill": dest.name,
        "commit": commit,
        "license": "MIT",
        "digest": digest,
        "files": hashes,
    }
    (dest / "VENDORED.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")


def sync(src: Path, commit: str, dest: Path = DEST) -> None:
    blobs = {out: read_blob(src, commit, path) for out, path in FILES.items()}
    problems = scan(FILES["AGENT.md"], blobs["AGENT.md"])
    if problems:
        raise SyncError("upstream scan failed:\n" + "\n".join(problems))
    dest.mkdir(parents=True, exist_ok=True)
    for out, data in blobs.items():
        (dest / out).write_bytes(data)
    write_manifest(dest, commit)
    missing = VSTACK_OWNED - {p.name for p in dest.iterdir()}
    if missing:
        print(f"warning: {dest.name} has no vstack-owned {sorted(missing)}; write them by hand", file=sys.stderr)
    print(f"{dest.name}: {len(blobs)} files at {commit[:7]}")


def check(dest: Path = DEST) -> list[str]:
    manifest_path = dest / "VENDORED.json"
    if not manifest_path.is_file():
        return [f"{dest.name}: VENDORED.json missing"]
    manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
    errors = []
    for rel, digest in manifest["files"].items():
        path = dest / rel
        if not path.is_file():
            errors.append(f"{dest.name}/{rel}: missing")
        elif sha256(path) != digest:
            errors.append(f"{dest.name}/{rel}: changed since sync (the upstream text must stay unmodified)")
    allowed = set(manifest["files"]) | VSTACK_OWNED | GENERATED
    for path in dest.rglob("*"):
        rel = path.relative_to(dest).as_posix()
        if path.is_file() and rel not in allowed:
            errors.append(f"{dest.name}/{rel}: not from the pinned upstream and not vstack-owned")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", help="exact upstream tag (vX.Y.Z) or 40-character commit")
    parser.add_argument("--source", type=Path, help="existing upstream clone (default: a partial clone in a temp dir)")
    parser.add_argument("--check", action="store_true", help="verify vendored files against VENDORED.json")
    args = parser.parse_args(argv)
    try:
        if args.check:
            errors = check()
            for e in errors:
                print(e, file=sys.stderr)
            if not errors:
                print("database-architect vendor check OK")
            return 1 if errors else 0
        if not args.ref:
            parser.error("--ref is required unless --check")
        validate_ref(args.ref)
        with tempfile.TemporaryDirectory() as tmp:
            src = args.source
            if src is None:
                src = Path(tmp) / "upstream"
                subprocess.run(
                    ["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", UPSTREAM_URL, str(src)],
                    check=True,
                )
            commit = git("rev-parse", "--verify", f"{args.ref}^{{commit}}", cwd=src)
            sync(src, commit)
        return 0
    except (SyncError, subprocess.CalledProcessError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
