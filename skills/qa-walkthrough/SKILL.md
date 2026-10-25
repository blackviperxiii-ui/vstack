---
name: qa-walkthrough
description: App UI walk + code QA; ranked report; safe fixes as small beta PRs. /qa-walkthrough
disable-model-invocation: true
---

# QA Walkthrough

Run before beta→main, after big features, or on “run a QA walkthrough”. Any Jeremy repo (GrokHub, tech-bench, genesis, tersa, vstack, …). Cite **viper-mode**; do not grow sibling skills.

## 1. UI pass

Boot the real app (Playwright/browser, desktop dev, or repo-supported runner). Walk every screen, flow, and setting; empty/error/loading; light/dark and narrow/wide where applicable.

Hunt bugs, UI defects (layout, overflow, contrast, alignment, broken states, style drift, a11y basics), and improvement ideas. Capture screenshots as evidence.

Each finding: where · repro · expected vs actual · severity · screenshot when possible.

## 2. Code pass

Then read code. Deslop (dead code, redundant comments, needless abstractions, naming drift, leftover debug). Debug UI findings + reading via **principle-fix-root-causes** (reference; do not copy). Improvements/opts (perf, bundle/startup, duplicated logic, error handling) via **sharpen** / **viper-mode**.

## 3. Output

One report ranked by severity; tag UI vs code; attach evidence.

- Clear/safe fixes → small PRs into **beta**; squash-merge on green CI.
- Needs Jeremy’s judgment → Command Centre card **Assigned=Jeremy** + Slack @mention with card link (AGENTS.md user-action rule).
- Suggestions/redesigns → report only; never silent apply.
