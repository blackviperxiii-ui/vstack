# AGENTS

## vstack skills

Always load and follow the vstack skills in `skills/` (start with `viper-mode`). Never use pstack.

### When and how coding agents must use vstack

Applies to Claude Code, Cursor, Codex, and any other agent working in this repository.

1. **Must use vstack** for nontrivial work here: code, scripts, CI, docs that change agent behavior, reviews, and shipping. Load `skills/` before planning or editing; read `skills/viper-mode/SKILL.md` first.
2. **How:** Follow `viper-mode` (playbook + principles + evidence). Use supporting skills as needed (`setup-vstack`, `in-your-own-words`, `principle-fix-root-causes`). Prefer Auto / Composer 2.5 Standard; keep parent context short; verify before claiming done.
3. **Never use pstack** (or `poteto-mode`) in this repo. Upstream pstack is tracked only via `UPSTREAM.json` and sync tooling — not as the active skill pack.
4. **Do not grow skill files** for prose. Put usage guidance in `docs/USAGE.md` (and consumer snippets in `docs/CONSUMING.md`) so token-check stays green.

Human-oriented how/when/examples: [docs/USAGE.md](docs/USAGE.md). Snippet for other repos: [docs/CONSUMING.md](docs/CONSUMING.md).

## User-action cards (Command Centre / Notion)

Any Command Centre / Notion card that needs the **user** to act (admin settings, secrets, approvals, etc.) must:

1. Be **Assigned** to the user in Notion (e.g. Jeremy), not Cursor
2. When the card is created or becomes Ready: **Slack @mention** the user with the card link(s)

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
