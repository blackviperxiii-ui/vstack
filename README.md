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

Then in chat:
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

## Efficiency defaults (baked in)

- Models: auto / inherit parent (set parent to Auto or Composer 2.5 Standard with Fast off)
- Budget: medium preferred
- Panels: single-model sequential unless high-stakes
- Context: bulk work to subagents, summaries only in main thread
- Bias: smallest change that meets the criteria; stop early when good enough

## Expand later

Full playbook set and individual principle/procedure skills can be added under `skills/` as needed. The orchestrator already encodes the method.

---

Viper Stack. Rigorous. Efficient. Yours.
