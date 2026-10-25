# How and when to use vstack

**Viper Stack (vstack)** is a small set of agent skills that make coding agents work with more rigor and fewer tokens. You keep the engineering habits (playbooks, principles, verify before claiming done) while defaulting to Auto or Composer 2.5 Standard so allowance lasts longer.

This repo is **blackviperxiii-ui/vstack**. It is actively maintained. Use **vstack**, not pstack.

For agents working *in this repo*, also read [AGENTS.md](../AGENTS.md). For dropping a one-liner into another project, see [CONSUMING.md](CONSUMING.md).

## First 5 minutes

1. **Install** — Cursor: install this repo as a plugin (see [CONSUMING.md](CONSUMING.md)). Other agents: `npx skills add blackviperxiii-ui/vstack --skill viper-mode`.
2. **Bind the skill** — In Cursor, pick **`/viper-mode`** from the `/` menu (plain text may not attach it), then state a goal.
3. **Try one example** — e.g. `/viper-mode Fix token_check false positive when tokens.json is fresh`. Expect playbook + root-cause fix + verify before a PR to **`beta`**.

More detail: [Quick start](#quick-start) and [Concrete examples](#concrete-examples) below.

## What vstack is (plain words)

Think of vstack as a playbook pack for your agent:

1. **`viper-mode`** is the main router. It picks a playbook, builds a short todo list, applies principles (smallest fix, verify the real artifact, fix root causes), and uses subagents carefully so the parent chat stays short.
2. Supporting skills cover setup (`setup-vstack`), restating goals (`in-your-own-words`), one named principle (`principle-fix-root-causes`), and app QA (`qa-walkthrough`).
3. Repo tooling (`scripts/`, CI) keeps skills lean (token budgets) and safe (lint, secret scan). That tooling is for *maintaining* vstack; day-to-day *use* is loading the skills.

Credit for the method goes to Lauren Tan’s pstack. Naming and branding here are Viper Stack only.

## When to use

Use vstack when the work needs deliberate engineering, not a one-line chat answer:

| Situation | Use vstack? |
|-----------|-------------|
| Nontrivial code, architecture, data modeling, API boundaries | Yes — start with `viper-mode` |
| Bugs, refactors, perf work, shipping PRs, reviews | Yes |
| Multi-step or ambiguous work where you want a playbook + evidence | Yes |
| Before promoting beta→main, after big features, or “run a QA walkthrough” | Yes — `/qa-walkthrough` (UI pass + code pass + ranked report) |
| Agent work in a repo that requires vstack (this one, or a consumer with the AGENTS snippet) | **Must** — load `skills/`, start with `viper-mode` |
| Quick factual Q&A, one-liner edits, pure brainstorming | Optional; skip if a full playbook adds noise |

## When not to use

- Do **not** load or follow **pstack** / `poteto-mode` in repos that standardize on vstack.
- Do not treat vstack as a product framework or runtime library. It is agent guidance, not app code.
- Do not grow skill files for prose docs. Put how-to text in `docs/` (this file) so token checks stay green.
- Skip the full orchestrator for trivial tasks where a short answer already meets the bar.

## Quick start

### In this repo (maintainers and agents)

1. Open the project with Cursor (or another agent that can load skills).
2. Load skills from `skills/`. **Always start with `skills/viper-mode/SKILL.md`.**
3. In Cursor, pick **`/viper-mode`** from the `/` menu so the skill binds, then state your goal. Plain text `/viper-mode` may not attach the skill.
4. Follow the principles and playbook; verify with the commands in [AGENTS.md](../AGENTS.md) before claiming done.
5. Open PRs to **`beta`**, squash-merge when CI is green. Do not promote `beta` → `main` unless explicitly asked.

Optional once: run **`/setup-vstack`** (or follow `skills/setup-vstack`) so model defaults prefer Auto / Composer 2.5 Standard.

### Install into another Cursor project

```bash
# Project-local
cp -R skills/ path/to/your-repo/.cursor/skills/

# Or user-global
cp -R skills/ ~/.cursor/skills/
```

Then pick `/viper-mode` from the `/` menu and paste the [CONSUMING.md](CONSUMING.md) snippet into that repo’s `AGENTS.md` / `CLAUDE.md` / `.cursor/rules`.

### Other agents (Claude Code, Codex, etc.)

```bash
npx skills add blackviperxiii-ui/vstack --skill viper-mode
```

Add the same consumer snippet so future agents keep using vstack instead of pstack.

## Concrete examples

### Example 1 — Bug fix in this repo

```
/viper-mode Fix token_check false positive when tokens.json is fresh
```

Expected agent behavior: load `viper-mode`, reproduce the failure, find the root cause (not a hiding guard), add or adjust a test, run lint / secret scan / unittest / `token_check.py`, open a PR to `beta`.

### Example 2 — Feature with verification units

```
/viper-mode Add a docs page that explains when to use vstack; link it from README
```

Expected: docs-only change (no skill token growth), README link, local checks green, PR → `beta`.

### Example 3 — Consumer repo requiring vstack

Another project’s `AGENTS.md` includes the snippet from [CONSUMING.md](CONSUMING.md). An agent starting there must load that project’s copy of vstack skills (or the global install), start with `viper-mode`, and never switch to pstack.

### Example 4 — QA walkthrough before promote

```
/qa-walkthrough Walk GrokHub beta end-to-end before we promote to main
```

Expected: run the real app (UI pass across screens/flows/states), then code pass (deslop + root-cause debug + opts), one severity-ranked report with evidence. Clear/safe fixes as small PRs to **beta**; judgment items as Command Centre cards Assigned=Jeremy + Slack; redesign ideas stay in the report.

### Example 5 — Skip the full stack

User asks: “What does `UPSTREAM.json` map?” A direct read of the file is enough. No need to force a multi-step playbook unless the user asks for a deeper audit.

## Skills at a glance

| Skill | Role |
|-------|------|
| `viper-mode` | Main router — playbooks, principles, subagents, evidence |
| `setup-vstack` | Write always-applied model-preference rule |
| `in-your-own-words` | Restate goals before substantial work |
| `principle-fix-root-causes` | Reproduce → root cause → fix at source |
| `qa-walkthrough` | UI + code QA; ranked report; safe fixes → beta PRs |

## Related

- [CONSUMING.md](CONSUMING.md) — copy-paste snippet for other repos
- [AGENTS.md](../AGENTS.md) — branch / PR / CI / verification rules for this repo
- [README.md](../README.md) — install overview and upstream token policy
