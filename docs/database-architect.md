# Database Architect: vendoring and resync

`skills/database-architect` vendors one file from
[davila7/claude-code-templates](https://github.com/davila7/claude-code-templates)
(MIT): `cli-tool/components/agents/database/database-architect.md`. The pinned
commit and a SHA-256 of every vendored file are in the folder's `VENDORED.json`.

## What vstack keeps and changes

| File | Owner | Notes |
| --- | --- | --- |
| `AGENT.md`, `LICENSE` | upstream | Copied byte for byte from the pinned commit. CI fails if one changes (`--check`). |
| `SKILL.md`, `NOTICE.md` | vstack | Wrapper trigger, safety rules, hand-offs and credits. The sync never touches them. |
| `VENDORED.json` | generated | Written by the sync script. |

The upstream description says "MUST BE USED for any database schema work"; the
vstack `SKILL.md` replaces it with a plain "use for" trigger. The agent hands
work to `postgres-pro`, `neon-database-architect`, `backend-developer` and
`security-auditor`, which vstack does not ship; the wrapper maps them to
`optimize`, `architect` and `qa-walkthrough`. vstack never runs the upstream
installer (`npx claude-code-templates@latest`).

## Resync to a new upstream commit

1. Pick a full 40-character commit. Never `main` or `latest`; the script
   refuses moving refs.
2. Read the upstream diff in full before syncing:
   `git diff <old-commit> <new-commit> -- cli-tool/components/agents/database/database-architect.md LICENSE`.
   Look for new instructions to run commands, fetch URLs, send data, read
   credentials, or override other instructions. Check that the safety rules
   the wrapper relies on are still there: scratch databases only, stop a server
   by its data directory and never with `pkill`/`killall`, never print
   credentials.
3. Sync:

   ```bash
   git clone --filter=blob:none --no-checkout https://github.com/davila7/claude-code-templates.git /tmp/cct
   python3 scripts/sync_database_architect.py --ref <commit> --source /tmp/cct
   python3 scripts/sync_database_architect.py --check
   ```

   The sync reads the files with `git cat-file` (nothing is checked out or
   run). It stops on hidden Unicode (zero-width, bidi-control or tag
   characters) and on red flags: a download piped to a shell, `curl`/`wget` of
   a URL, an `npx ...@latest`, a credential path, an instruction override, or
   text that hides output from the user.
4. If the hand-offs or safety rules changed, update the wrapper `SKILL.md`
   (keep it under the 400-token cap) and `NOTICE.md`.
5. Run the full local checks (`AGENTS.md`), add a `CHANGELOG.md` line naming
   the new commit, and open a PR into `beta`.
