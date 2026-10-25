# AGENTS

## vstack skills

Always load and follow the vstack skills in `skills/` (start with `viper-mode`). Never use pstack.

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
