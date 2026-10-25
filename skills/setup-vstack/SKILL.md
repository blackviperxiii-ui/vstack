---
name: setup-vstack
description: Configure Viper Stack for token efficiency. Writes an always-applied Auto / Composer Standard rule.
---

# Setup Vstack

Write `~/.cursor/rules/vstack-models.mdc` (or project `.cursor/rules/`) so every role uses `auto` (inherit parent).

## Steps

1. Detect models (Task slugs). `auto` / `inherit-parent` always valid.
2. Budget: medium (high effort) or small (medium).
3. Write:

```
---
description: Viper Stack models — Auto / Composer Standard
alwaysApply: true
---
# budget: medium (high)
feature, refactoring, bug-fix, perf-issue, hillclimb: auto
judgment and prose: auto
hardest tasks: auto
how, why, arena, swarm, architect, interrogate: auto
```

4. Tell user: parent Auto or Composer 2.5 Fast OFF, then fresh session.
5. Optional once: offer `/create-verification-skill` if no project verify harness.
6. Optional once: offer `/create-formal-verification-skill` if no formal verify skill.

Keeps rigor while protecting token allowance.
