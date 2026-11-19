#!/usr/bin/env python3
"""Vendor the Database Architect agent from claude-code-templates at a pinned commit.

    python3 scripts/sync_database_architect.py --ref <40-char commit> [--reviewed]  # sync
    python3 scripts/sync_database_architect.py --ref <commit> --source DIR          # existing clone
    python3 scripts/sync_database_architect.py --check                              # verify

Sync reads the agent file and the repository LICENSE straight from the pinned
commit (`git cat-file`, no checkout), so nothing upstream runs. It refuses
moving refs and tags, and it stops when the agent text has hidden Unicode or a
red flag (download-and-run commands, unpinned npx, credential paths,
instruction overrides). After reading the upstream diff, pass --reviewed to
override red-flag hits; hidden Unicode always blocks. The agent is copied byte
for byte to `skills/database-architect/AGENT.md`; vstack's own SKILL.md and
NOTICE.md are never touched. VENDORED.json records the commit and a SHA-256 of
every vendored file; --check fails on any drift.
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
from sync_modern_web_guidance import HIDDEN_RE, SyncError, sha256  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
DEST = REPO_ROOT / "skills" / "database-architect"
UPSTREAM_URL = "https://github.com/davila7/claude-code-templates.git"
UPSTREAM_REPO = "davila7/claude-code-templates"
UPSTREAM_PATH = "cli-tool/components/agents/database/database-architect.md"
# vendored file -> path in the upstream repository
FILES = {"AGENT.md": UPSTREAM_PATH, "LICENSE": "LICENSE"}
VSTACK_OWNED = frozenset({"SKILL.md", "NOTICE.md"})
GENERATED = frozenset({"VENDORED.json"})
COMMIT_RE = re.compile(r"^[0-9a-f]{40}$")

# Text an agent prompt has no reason to carry. Any hit blocks the sync until a
# human has read the upstream change. Lines ending in a backslash are joined
# with the next one first, so a command split across lines is seen whole.
DOWNLOADERS = r"curl|wget|iwr|irm|invoke-webrequest|invoke-restmethod"
SHELLS = r"(sudo\s+)?(ba|z|da|k|fi)?sh|python3?|node|perl|ruby|iex|invoke-expression"
RED_FLAGS = {
    "download piped to a shell": re.compile(rf"\b({DOWNLOADERS})\b.*\|\s*({SHELLS})\b", re.I),
    "runs downloaded code": re.compile(
        r"(<\(|\$\()\s*(curl|wget)\b"
        r"|\b(curl|wget)\b.*&&\s*(sudo\s+)?(ba|z)?sh\b"
        r"|\bpip3?\s+install\s+\S*https?://"
        r"|\b(iex|invoke-expression)\s*\(\s*(irm|iwr|invoke-restmethod|invoke-webrequest)\b",
        re.I,
    ),
    "fetches a URL with curl or wget": re.compile(r"\b(curl|wget)\b[^\n]*\bhttps?://", re.I),
    "credential path": re.compile(
        r"(~|\$\{?HOME\}?|/home/[^/\s]+|/root)/\.(ssh|aws|grok|docker|kube|gnupg|config/gh|pgpass|netrc|my\.cnf|git-credentials)\b"
        r"|\bauth\.json\b|\bid_(rsa|ed25519|ecdsa)\b|\.pgpass\b|\.netrc\b",
        re.I,
    ),
    "instruction override": re.compile(
        r"\b(ignore|disregard|forget|override)\b[^\n]{0,35}\b"
        r"(?:(?:previous|prior|above|earlier|system|your)\b[^\n]{0,25}\b(?:instructions?|prompts?|rules?|guidelines?|safety(?:\s+rules?)?)"
        r"|(?:the\s+)?(?:instructions?|prompts?|rules?|guidelines?)\s+(?:above|below|given|earlier))\b"
        r"|\b(new|real|actual|updated)\s+system\s+(instructions?|prompts?)\b"
        r"|\byou\s+are\s+now\s+(?:in\s+\w+\s+mode|(?:a|an)\s+(?!connected\b|ready\b|running\b|in\b)[a-z-]+\s+(?:assistant|agent|ai|model|bot|hacker|developer))\b",
        re.I,
    ),
    "hides output from the user": re.compile(
        r"\b(do not|don't|never)\s+(?:tell|inform|mention(?:\s+(?:this|it|that|anything))?\s+to)\s+the\s+user\b"
        r"|\b(do not|don't|never)\s+(?:show|reveal|report|disclose)\s+"
        r"(?:the\s+user\s+(?:this|that|what\s+you|any\s+(?:command|output|file|action|tool))"
        r"|(?:this|that|these|it|what\s+you|your\s+(?:commands?|actions?|output|tools?|prompt)|the\s+(?:commands?|output|files?\s+read))\s+to\s+the\s+user)\b"
        r"|\b(?:hide|conceal|omit)\b[^\n]{0,30}\bfrom\s+the\s+user\b"
        r"|\bwithout\s+(?:telling|informing|notifying)\s+the\s+user\b",
        re.I,
    ),
    "HTML comment (hidden in a rendered diff)": re.compile(r"<!--"),
}

PINNED_NPM_PKG_RE = re.compile(r"^(?:@[\w.-]+/)?[\w.-]+@\d[\w.+-]*$")
NPX_PROSE_WORDS = frozenset(
    {
        "a", "an", "and", "are", "as", "at", "binary", "binaries", "by", "can",
        "cli", "command", "commands", "for", "from", "if", "in", "is", "may",
        "must", "of", "on", "or", "package", "packages", "runner", "script",
        "scripts", "should", "than", "that", "the", "this", "to", "tool",
        "tools", "was", "when", "will", "with", "without", "would",
    }
)
NPX_VALUE_FLAGS = frozenset(
    {"-c", "--call", "--cache", "--shell", "--userconfig", "--registry", "-n", "--node-arg"}
)
NPX_STOP_RE = re.compile(r"(?:`|\|\||&&|[|;)\n])")


def _clean_pkg(spec: str) -> str:
    return spec.strip("'\"").rstrip(".,;:)]}")


def has_unpinned_npx(logical: str) -> bool:
    """Return True if an npx command invocation lacks a pinned numeric version."""
    for match in re.finditer(r"\bnpx\b", logical, re.I):
        after = logical[match.end():]
        if not after or not after[0].isspace():
            continue
        in_backticks = logical[:match.start()].count("`") % 2 == 1
        preceded_by_article = bool(re.search(r"\b(?:an|the)\s+$", logical[:match.start()], re.I))
        stop = NPX_STOP_RE.search(after)
        rest = after[:stop.start()] if stop else after
        tokens = rest.split()
        had_flags = False
        packages: list[str] = []
        positional: str | None = None
        i = 0
        while i < len(tokens):
            tok = tokens[i]
            if tok == "--":
                had_flags = True
                if i + 1 < len(tokens):
                    positional = tokens[i + 1]
                break
            if tok.startswith("--package="):
                had_flags = True
                packages.append(tok.split("=", 1)[1])
                i += 1
                continue
            if tok.startswith("-p") and len(tok) > 2 and not tok.startswith("--"):
                had_flags = True
                packages.append(tok[3:] if tok.startswith("-p=") else tok[2:])
                i += 1
                continue
            if tok in ("--package", "-p"):
                had_flags = True
                packages.append(tokens[i + 1] if i + 1 < len(tokens) else "")
                i += 2
                continue
            if tok in NPX_VALUE_FLAGS:
                had_flags = True
                i += 2
                continue
            if tok.startswith("-"):
                had_flags = True
                i += 1
                continue
            positional = tok
            break

        if packages:
            if any(not PINNED_NPM_PKG_RE.fullmatch(_clean_pkg(p)) for p in packages):
                return True
            continue
        if positional is None:
            continue
        pkg = _clean_pkg(positional)
        if not pkg or PINNED_NPM_PKG_RE.fullmatch(pkg):
            continue
        if not had_flags and not in_backticks and (preceded_by_article or pkg.lower() in NPX_PROSE_WORDS):
            continue
        return True
    return False


def validate_commit(ref: str) -> None:
    if not COMMIT_RE.fullmatch(ref):
        raise SyncError(
            f"--ref {ref!r} is not a full 40-character commit; "
            "moving refs such as latest, main, or tags are refused"
        )


def git(*args: str, cwd: Path) -> str:
    return subprocess.run(
        ["git", *args], cwd=cwd, check=True, capture_output=True, text=True
    ).stdout.strip()


def read_blob(src: Path, commit: str, path: str) -> bytes:
    result = subprocess.run(["git", "cat-file", "blob", f"{commit}:{path}"], cwd=src, capture_output=True)
    if result.returncode != 0:
        detail = result.stderr.decode("utf-8", "replace").strip()
        raise SyncError(f"upstream has no {path} at {commit[:12]} (moved or renamed?): {detail}")
    return result.stdout


def scan_parts(name: str, data: bytes) -> tuple[list[str], list[str]]:
    """Return (hard_problems, red_flags): hard blocks always fail; red flags allow --reviewed."""
    try:
        text = data.decode("utf-8")
    except UnicodeDecodeError as exc:
        return ([f"{name}: not valid UTF-8 ({exc.reason} at byte {exc.start})"], [])
    hard: list[str] = []
    flags: list[str] = []
    lines = text.splitlines()
    for n, line in enumerate(lines, 1):
        if HIDDEN_RE.search(line):
            hard.append(f"{name}:{n}: hidden Unicode character")
    joined: list[str] = []
    start = 1
    for n, line in enumerate(lines, 1):
        joined.append(line[:-1] if line.endswith("\\") else line)
        if line.endswith("\\") and n < len(lines):
            continue
        logical = " ".join(joined)
        for label, pattern in RED_FLAGS.items():
            if pattern.search(logical):
                flags.append(f"{name}:{start}: {label}")
        if has_unpinned_npx(logical):
            flags.append(f"{name}:{start}: unpinned npx package")
        joined, start = [], n + 1
    return hard, flags


def scan(name: str, data: bytes) -> list[str]:
    """Problems that block a sync: hidden Unicode or a red flag in the agent text."""
    hard, flags = scan_parts(name, data)
    return hard + flags


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


def sync(src: Path, commit: str, dest: Path | None = None, *, reviewed: bool = False) -> None:
    dest = dest or DEST
    blobs = {out: read_blob(src, commit, path) for out, path in FILES.items()}
    hard, flags = scan_parts(FILES["AGENT.md"], blobs["AGENT.md"])
    lic_hard, _ = scan_parts(FILES["LICENSE"], blobs["LICENSE"])
    hard.extend(lic_hard)
    if hard:
        raise SyncError("upstream scan failed:\n" + "\n".join(hard + ([] if reviewed else flags)))
    if flags:
        if not reviewed:
            raise SyncError(
                "upstream scan failed:\n"
                + "\n".join(flags)
                + "\n(after reading the upstream diff, pass --reviewed to allow red-flag hits)"
            )
        print("warning: --reviewed passed; allowing red-flag hits:\n" + "\n".join(flags), file=sys.stderr)
    dest.mkdir(parents=True, exist_ok=True)
    for out, data in blobs.items():
        (dest / out).write_bytes(data)
    write_manifest(dest, commit)
    missing = VSTACK_OWNED - {p.name for p in dest.iterdir()}
    if missing:
        print(f"warning: {dest.name} has no vstack-owned {sorted(missing)}; write them by hand", file=sys.stderr)
    print(f"{dest.name}: {len(blobs)} files at {commit[:7]}")


def check(dest: Path | None = None) -> list[str]:
    dest = dest or DEST
    manifest_path = dest / "VENDORED.json"
    if not manifest_path.is_file():
        return [f"{dest.name}: VENDORED.json missing"]
    try:
        manifest = json.loads(manifest_path.read_text(encoding="utf-8"))
        files = dict(manifest["files"])
    except (ValueError, KeyError, TypeError) as exc:
        return [f"{dest.name}/VENDORED.json: unreadable ({exc!r}); rerun the sync"]
    errors = []
    expected = {"upstream": UPSTREAM_REPO, "path": UPSTREAM_PATH, "skill": dest.name, "license": "MIT"}
    for key, value in expected.items():
        if manifest.get(key) != value:
            errors.append(f"{dest.name}/VENDORED.json: {key} is {manifest.get(key)!r}, expected {value!r}")
    if not COMMIT_RE.fullmatch(str(manifest.get("commit", ""))):
        errors.append(f"{dest.name}/VENDORED.json: commit is not a full 40-character commit")
    if sorted(files) != sorted(FILES):
        errors.append(f"{dest.name}/VENDORED.json: lists {sorted(files)}, expected {sorted(FILES)}")
    digest = hashlib.sha256("".join(f"{h}  {f}\n" for f, h in sorted(files.items())).encode()).hexdigest()
    if manifest.get("digest") != digest:
        errors.append(f"{dest.name}/VENDORED.json: digest does not match its file hashes")
    for rel, digest in files.items():
        path = dest / rel
        if not path.is_file():
            errors.append(f"{dest.name}/{rel}: missing")
        elif sha256(path) != digest:
            errors.append(f"{dest.name}/{rel}: changed since sync (the upstream text must stay unmodified)")
    allowed = set(files) | VSTACK_OWNED | GENERATED
    for path in dest.rglob("*"):
        rel = path.relative_to(dest).as_posix()
        if path.is_file() and rel not in allowed:
            errors.append(f"{dest.name}/{rel}: not from the pinned upstream and not vstack-owned")
    return errors


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--ref", help="exact 40-character upstream commit")
    parser.add_argument("--source", type=Path, help="existing upstream clone (default: a partial clone in a temp dir)")
    parser.add_argument("--check", action="store_true", help="verify vendored files against VENDORED.json")
    parser.add_argument(
        "--reviewed",
        action="store_true",
        help="allow red-flag scan hits after reading the upstream diff (hidden Unicode still blocks)",
    )
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
        validate_commit(args.ref)
        with tempfile.TemporaryDirectory() as tmp:
            src = args.source
            if src is None:
                src = Path(tmp) / "upstream"
                subprocess.run(
                    ["git", "clone", "--quiet", "--filter=blob:none", "--no-checkout", UPSTREAM_URL, str(src)],
                    check=True,
                )
            commit = git("rev-parse", "--verify", f"{args.ref}^{{commit}}", cwd=src)
            sync(src, commit, reviewed=args.reviewed)
        return 0
    except subprocess.CalledProcessError as exc:
        detail = exc.stderr.strip() if isinstance(exc.stderr, str) else ""
        print(f"error: {' '.join(map(str, exc.cmd))} failed ({exc.returncode}){': ' + detail if detail else ''}", file=sys.stderr)
        return 1
    except (SyncError, OSError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(main())
