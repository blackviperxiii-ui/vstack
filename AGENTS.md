# AGENTS

## vstack skills

Always load and follow the vstack skills in `skills/` (start with `viper-mode`). Never use pstack.

### When and how coding agents must use vstack

Applies to Claude Code, Cursor, Codex, and any other agent working in this repository.

1. **Must use vstack** for nontrivial work here: code, scripts, CI, docs that change agent behavior, reviews, and shipping. Load `skills/` before planning or editing; read `skills/viper-mode/SKILL.md` first.
2. **How:** Follow `viper-mode` (playbook + principles + evidence). Use supporting skills as needed (`setup-vstack`, `in-your-own-words`, `how`, `why`, `architect`, `blast-radius`, `principle-*`, `qa-walkthrough`, `av-qa-walkthrough`). Prefer Auto / Composer 2.5 Standard; keep parent context short; verify before claiming done.
3. **Never use pstack** (or `poteto-mode`) in this repo. Upstream pstack is tracked only via `UPSTREAM.json` and sync tooling — not as the active skill pack.
4. **Do not grow skill files** for prose. Put usage guidance in `docs/USAGE.md` (and consumer snippets in `docs/CONSUMING.md`) so token-check stays green.

Human-oriented how/when/examples: [docs/USAGE.md](docs/USAGE.md). Snippet for other repos: [docs/CONSUMING.md](docs/CONSUMING.md).


## Branches

- **`beta`** is the working integration branch. Land agent and day-to-day changes here.
- **`main`** is the stable line. Do **not** open PRs from `beta` → `main` or promote `beta` to `main` unless the user explicitly asks.

## Pull requests and merge

- Open PRs targeting **`beta`** (or `main` only when the user directs a stable release).
- **Squash merge** when CI is green. No review holds are required (0 approving reviews).
- **Auto-merge** is allowed when checks pass.
- Delete the head branch after merge when GitHub offers it.
- Never force-push or delete `main` or `beta`.

## CI

- **CI** runs on push and PR to `main` and `beta` (`lint`, `token-check`). PRs must be green before merge.
- Preserve token-check and skill lint behavior; do not bypass without user approval (`token-growth-approved` label rules still apply on sync PRs per README).

## Verification

Run locally before pushing when you touch scripts, skills, or tests:

```bash
python3 scripts/lint_skills.py
python3 scripts/check_secrets.py
python3 -m unittest discover -s tests -p 'test_*.py' -q
pip install -r requirements-ci.txt && python3 scripts/token_check.py
```

## No personal info (hard rule)

This is open-source work meant for anyone to use. Keep every file, commit, PR and issue generic.

- Never include a real name, nickname used as a person, personal email, phone, address, employer, city, machine name, or real home-folder path. Where a name is needed, write "user". Paths use `/home/user`.
- Never mention the maintainer's other projects, personal bots or assistants, task boards, or personal workflow (Notion cards, Slack pings, approval habits). Examples use neutral names like `my-app`.
- Commits use the GitHub no-reply email. Squash merges use a clean subject and body with no `Co-authored-by` lines.
- `scripts/pii-guard/pii_guard.py` runs in CI as the required `pii-guard` check; run it locally before pushing.

## Command Centre board guide (GitHub access only)

Work is planned on the Notion board "Grok Bot Command Centre". Cards with
Status = Ready sync to GitHub issues on blackviperxiii-ui/vstack (Project = VStack; the issue sync is being rolled out here after GrokHub).
You don't need Notion access: the issue is your copy of the card.

### Finding your work
1. Open issues with your label: claude, copilot or jules.
2. Do High priority first, then lowest Order (both are shown on the card, linked from the issue).
3. Each issue links its Notion card and copies its Evidence / Fix / Acceptance.
4. Don't start a new issue while you already have 2 open PRs.

### Board terms used in issues
- Status: Idea, Ready, Doing, Waiting, Needs you, Done, Notes.
- Assigned: Claude, Copilot or Jules (matches your label).
- Priority: High, Medium, Low, Eh... Whenever.
- Order: pickup sequence. Lower goes first.
- Result: the card's outcome line. Picked up / Done at: start and finish dates.

### Working an issue
- Start: comment on the issue saying you've started (the card moves to Doing).
- PR body must include:
  - `Closes #N` (the issue number)
  - the Notion card URL from the issue
  - a one-line summary of the change
- On merge to beta, the Repo bot sets the card to Done, fills in Done at,
  and puts the PR link and summary in Result. Don't do this yourself.
- Blocked: comment on the issue with what blocked you and what's needed,
  then stop. The card goes back to Ready with your note.

### Never
- Work issues labelled for another coder, or change their labels.
- Close or delete issues, or relabel your own issue to someone else.

### Repo rules
- PRs target beta only. Never main or genesis.
- Squash-merge style: one clean subject line, no Co-authored-by lines.
- No force-pushes.
- Run fmt, lint and tests locally before pushing, then push once.
- At most 2 open PRs per coder.
- The Repo bot does all merges. Never merge your own PR.
- No personal info in the repo: write 'user' for names and /home/user for paths.

Coders with Notion access: see `docs/agents/board-guide-notion.md`.
