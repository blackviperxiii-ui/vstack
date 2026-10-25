# Viper Stack (vstack)

Token-efficient rigorous engineering skills for Cursor and other agents.

**Credit:** Method and playbooks adapted from Lauren Tan (@poteto)'s pstack. All branding and naming is Viper Stack from here on. Original: https://github.com/cursor/plugins/tree/main/pstack

## What this is

A reworked, self-contained set of agent skills that keep the rigor (playbooks, principles, verification-first, how/why, sequence into verifiable units, smallest change) while defaulting to **Auto** or **Composer 2.5 Standard** so limited token allowances last longer.

- Prefer Auto / inherit-parent for subagents
- Reduced multi-model panels (sequential or single by default)
- Stronger context-window and laziness guards
- Medium/small reasoning budget preferred
- Fresh subagents, summaries only in parent

## Install

### Cursor
Drop the `skills/` folder into `.cursor/skills/` (project) or `~/.cursor/skills/` (global).

Pick **`/viper-mode`** from the `/` menu so Cursor attaches the skill, then type your goal. Plain text `/viper-mode` may not bind the skill.

```
/viper-mode <your goal>
```

Or set it as a custom mode.

### Other agents (Claude Code, Codex, etc.)
```
npx skills add blackviperxiii-ui/vstack --skill viper-mode
```

## Core skill

- **viper-mode**: The main router. Matches the task to a playbook, builds a todo list, applies principles, delegates efficiently, and demands evidence before claiming done.

## Slash skills

- **in-your-own-words**: Before substantial work, restate the user's goals and the problem in your own words (`/in-your-own-words`).

## Efficiency defaults (baked in)

- Models: auto / inherit parent (set parent to Auto or Composer 2.5 Standard with Fast off)
- Budget: medium preferred
- Panels: single-model sequential unless high-stakes
- Context: bulk work to subagents, summaries only in main thread
- Bias: smallest change that meets the criteria; stop early when good enough

## Expand later

Full playbook set and individual principle/procedure skills can be added under `skills/` as needed. The orchestrator already encodes the method.

## Upstream sync and token budget

This repo tracks [cursor/plugins `pstack`](https://github.com/cursor/plugins/tree/main/pstack) in `UPSTREAM.json` (`last_synced_sha`, `mapping`, `unported`). A daily **Upstream watch** workflow opens or updates a single `upstream-sync` issue when `pstack/` moves upstream; it never edits skills for you. **Dependabot** watches `requirements-ci.txt` and GitHub Actions weekly.

**Sync PRs** bump `last_synced_sha` after you port changes. **Token check** on every PR to `main` and `beta` (see `.github/workflows/ci.yml`):

- Regenerate `tokens.json` with `python scripts/count_tokens.py` (tiktoken `cl100k_base`) and commit it; CI fails if the file is stale.
- Existing skills must not grow versus `main`, unless:
  - this is a sync PR and each grown skill’s growth ratio is ≤ its mapped upstream file’s growth between the old and new SHAs, plus 5%; or
  - the PR has the `token-growth-approved` label.
- New skills are allowed only on sync PRs and must stay ≤ 35% of the mapped upstream skill’s token count at the new SHA.

Mapped ports today: `viper-mode` ↔ `poteto-mode`, `setup-vstack` ↔ `setup-pstack`, `principle-fix-root-causes` ↔ same. Other upstream skills stay listed under `unported` until you add them.

---

Viper Stack. Rigorous. Efficient. Yours.
