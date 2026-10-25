# Requiring vstack in other repos

Paste one of the blocks below into the consumer repo so agents load **vstack** (never pstack). Full how/when guide: [USAGE.md](USAGE.md).

Install skills first (`npx skills add blackviperxiii-ui/vstack --skill viper-mode`, or copy this repo’s `skills/` into `.cursor/skills/` / `~/.cursor/skills/`).

## AGENTS.md / CLAUDE.md

```markdown
## vstack (required)

Always load and follow the vstack skills (start with `viper-mode` / `skills/viper-mode/SKILL.md`). Never use pstack or poteto-mode.

Source: https://github.com/blackviperxiii-ui/vstack — see docs/USAGE.md
```

## `.cursor/rules` (always-applied)

```markdown
---
description: "Always use vstack skills; never pstack."
alwaysApply: true
---

Always load and follow the vstack skills (start with viper-mode); never use pstack.
Source: https://github.com/blackviperxiii-ui/vstack
```

Keep the rule short. Do not paste full playbooks into rules or skills in the consumer repo — that burns tokens. Point agents at the installed `viper-mode` skill instead.
