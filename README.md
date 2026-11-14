# vstack

[![CI](https://github.com/blackviperxiii-ui/vstack/actions/workflows/ci.yml/badge.svg)](https://github.com/blackviperxiii-ui/vstack/actions/workflows/ci.yml)
[![Release](https://img.shields.io/github/v/release/blackviperxiii-ui/vstack)](https://github.com/blackviperxiii-ui/vstack/releases)
[![License: MIT](https://img.shields.io/badge/License-MIT-blue.svg)](LICENSE)

Token-efficient engineering playbooks, principles, and verification skills for Cursor and coding agents.

## Table of contents

- [Overview](#overview)
- [Features](#features)
- [Getting started](#getting-started)
- [Usage](#usage)
- [Skill catalog](#skill-catalog)
- [Configuration and architecture](#configuration-and-architecture)
- [Upstream sync and token budget](#upstream-sync-and-token-budget)
- [Contributing](#contributing)
- [License](#license)

## Overview

**Viper Stack (`vstack`)** is a self-contained pack of 53 `SKILL.md` playbooks and rules for AI coding agents. It adapts the engineering method from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan so agents keep strict engineering habits (Research-Plan-Execute, root-cause fixes, verifiable units, and runtime proof) without burning token allowances on heavy multi-model panels or bloated prompts.

Instead of defaulting to expensive frontier-model committees, `vstack` defaults parent sessions to **Auto** or **Composer 2.5 Standard**, delegates bulk reads to fresh subagents that inherit the parent model, and enforces strict token budgets on every skill file in CI.

## Features

- **Playbook routing (`viper-mode`)**: Routes nontrivial tasks through Research-Plan-Execute (RPE), builds a task list, cites engineering principles per decision, and requires observable verification before claiming work is done.
- **Token-conscious defaults**: Uses `auto` (inherit parent) for subagents, medium or small reasoning budgets, single-model sequential reviews unless high-stakes work is requested, and concise summaries in the parent context window.
- **58 focused skills**: Covers code comprehension (`how`, `why`, `teach`, `recall`), design (`architect`, `statechart`, `stageshow`, `elevate`), web platform guidance (`modern-web-guidance`, `chrome-extensions`), adversarial review (`blast-radius`, `interrogate`), full-app QA (`qa-walkthrough`, `av-qa-walkthrough`, `land-it`), performance (`optimize`), promote/release (`bag-and-tag`), dependency and surface maintenance (`updater`), and 19 `principle-*` skills.
- **Multi-agent packaging**: Ships Cursor ([`.cursor-plugin/plugin.json`](.cursor-plugin/plugin.json)), root Agent Plugins ([`plugin.json`](plugin.json)), and Claude Code ([`.claude-plugin/plugin.json`](.claude-plugin/plugin.json)) manifests, plus installers for portable `.agents/skills/` and `.grok/skills/` layouts. Cursor Projects: see [`docs/CONSUMING.md`](docs/CONSUMING.md).
- **CI-enforced token caps**: Tracks `cl100k_base` token counts in [`tokens.json`](tokens.json) and blocks unapproved prompt growth on pull requests and branch pushes.

## Getting started

### Supported agents

| Platform | Support | Install path |
| --- | --- | --- |
| Cursor | First-class plugin | Local plugin (`~/.cursor/plugins/local/vstack`) or team/public marketplace |
| Claude Code | First-class plugin | Plugin marketplace or `~/.claude/skills/` |
| Codex, Antigravity, Muse Code, Windsurf, OpenCode | First-class skills | `.agents/skills/` (project or user home) + `AGENTS.md` |
| Grok Build | First-class skills | `.grok/skills/` (project or user home) |
| Grok Bot, GrokHub, Aider, Continue | Documented generic | Consumer `AGENTS.md` pointer (see [`docs/CONSUMING.md`](docs/CONSUMING.md)) |

See [`docs/CONSUMING.md`](docs/CONSUMING.md) for the full compatibility matrix and host-specific instructions.

### Install from the latest release

[`install.sh`](install.sh) downloads the release archive, verifies its SHA-256 checksum against `SHA256SUMS`, and installs into your user directory. Requires `curl`, `tar`, and `sha256sum` (or `shasum`).

```bash
# Cursor local plugin (default)
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash

# Claude Code personal skills (~/.claude/skills)
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash -s -- --target claude

# Portable Agent Skills directory (~/.agents/skills for Codex, Muse, Windsurf, OpenCode, Antigravity)
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash -s -- --target agents

# Grok Build personal skills (~/.grok/skills)
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash -s -- --target grok

# Custom skills directory
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash -s -- --target dir --dir /home/user/my-app/skills
```

Pass `--version 1.2.2` to pin a specific release. Release archives (`.tar.gz`, `.zip`, and `SHA256SUMS`) are published on the [Releases](https://github.com/blackviperxiii-ui/vstack/releases) page, and [`CHANGELOG.md`](CHANGELOG.md) lists version history.

### Install from a git clone

Use [`scripts/install_for.sh`](scripts/install_for.sh) for project-local symlinks (or pass `--mode copy` to copy files):

```bash
git clone https://github.com/blackviperxiii-ui/vstack.git /home/user/vstack
cd /home/user/vstack

./scripts/install_for.sh --host agents --project /home/user/my-app
./scripts/install_for.sh --host cursor --global
./scripts/install_for.sh --host claude --global
./scripts/install_for.sh --host grok --project /home/user/my-app
```

### Marketplace and CLI helpers

In Claude Code:

```text
/plugin marketplace add blackviperxiii-ui/vstack
/plugin install vstack@vstack
```

With the `skills` CLI helper (for example in Codex):

```bash
npx skills add blackviperxiii-ui/vstack --skill viper-mode
```

## Usage

### Quick start in Cursor

1. Install `vstack` once as a Cursor plugin and reload Cursor. Do not copy `skills/` manually into `.cursor/skills/`.
2. Select **`/viper-mode`** from the `/` command menu so Cursor attaches [`skills/viper-mode/SKILL.md`](skills/viper-mode/SKILL.md), then write your task:

```text
/viper-mode Fix token_check false positive when tokens.json is fresh
```

3. Optionally run **`/setup-vstack`** once to install/configure for your agent (Cursor also writes `~/.cursor/rules/vstack-models.mdc` with `auto` defaults).

### Consumer repository pointer

In repositories where agents read `AGENTS.md`, add a short pointer so agents load `vstack` and follow RPE:

```markdown
## vstack

Always load and follow the vstack skills (start with `viper-mode`). Never use pstack.
If skills live under `.agents/skills/` (or `.claude/skills/` or `.grok/skills/`), read `viper-mode/SKILL.md` first.
RPE: Research, Plan, then Execute; no edits before a written plan.
```

See [`docs/USAGE.md`](docs/USAGE.md) for concrete workflows (`/viper-mode`, `/land-it`, `/elevate`, `/optimize`, `/bag-and-tag`, `/qa-walkthrough`, `/av-qa-walkthrough`, and `/updater`).

## Skill catalog

### Core orchestrator

- **`viper-mode`**: Main router. Restates the goal, enforces Research-Plan-Execute, matches the task to a playbook, applies principles, delegates to subagents, and verifies real behavior before completion.

### Workflow and verification skills

- **`setup-vstack`**: Detects the coding agent, installs via marketplace/plugin or `install_for.sh`, ensures the consumer pointer, and (Cursor only) writes the Auto / Composer model rule (`/setup-vstack`).
- **`in-your-own-words`**: Restates the user's goal, problem, and smallest change before substantial edits (`/in-your-own-words`).
- **`sharpen`**: Deepens a task without enlarging scope, then rewrites the prompt (`/sharpen`).
- **`how`** and **`why`**: Explains how a subsystem works or why it is shaped that way with cited code and git evidence (`/how`, `/why`).
- **`teach`**: Builds a plain-language explanation from `how` and `why` at the reader's pace (`/teach`).
- **`recall`**: Reconstructs recent working context into a current-state brief (`/recall`).
- **`architect`**: Sketches data types and module boundaries before writing implementation code (`/architect`).
- **`statechart`**: Models system transitions and bug paths as reader-facing Mermaid statecharts (`/statechart`).
- **`figure-it-out`**: Designs a short, auditable playbook when no standard playbook fits (`/figure-it-out`).
- **`follow-through`**: Maintains a task ledger with check-ins, stall detection, and proven completion (`/follow-through`).
- **`show-me-your-work`**: Records an append-only TSV decision trail during long or unattended runs (`/show-me-your-work`).
- **`tdd`**: Starts with a failing test when the test harness is fast and cheap (`/tdd`).
- **`blast-radius`**: Traces what a change can break beyond the diff and proves safety by running code (`/blast-radius`).
- **`interrogate`**: Runs an adversarial review where only run-proven findings survive (`/interrogate`).
- **`land-it`**: Audits whole-app product feel, interactivity, UX gaps, and code shortfalls, then ranks low-effort fixes (`/land-it`).
- **`elevate`**: Raises UI craft toward premium, modern, fluid feel — hierarchy, type, color, space, motion, states, anti-slop (`/elevate`).
- **`optimize`**: Measures real artifacts, finds hot spots, fixes root causes, and remeasures app performance (`/optimize`).
- **`bag-and-tag`**: Promotes `beta` → `main`, bumps VERSION/CHANGELOG, tags `vX.Y.Z`, publishes release artifacts, and verifies install paths (`/bag-and-tag`).
- **`qa-walkthrough`**: Runs an end-to-end UI and code QA pass and produces a severity-ranked report (`/qa-walkthrough`).
- **`av-qa-walkthrough`**: Audits audio/video playback, sync, devices, and streams using `ffprobe` and `ffmpeg` evidence (`/av-qa-walkthrough`).
- **`updater`**: Audits Cargo, npm, PyPI, RustSec, toolchains, GitHub Actions, WoW `.toc` versions, Minecraft releases, and model IDs via `skills/updater/scripts/updater.py` (`/updater`).
- **`create-verification-skill`** and **`maintain-verification-skill`**: Generates and audits project-local runtime verification skills (`/create-verification-skill`, `/maintain-verification-skill`).
- **`create-formal-verification-skill`** and **`maintain-formal-verification-skill`**: Generates and resyncs project-local formal verification skills (`/create-formal-verification-skill`, `/maintain-formal-verification-skill`).
- **`benchmark-checklist`**: Vets performance numbers before reporting them (`/benchmark-checklist`).
- **`correct`**: Prevents repeated agent mistakes through architecture, types, lint rules, or tests (`/correct`).
- **`reflect`**: Turns session learnings into reviewed skill edits (`/reflect`).
- **`swarm`**: Fans out parallel subagents for broad coverage or competing implementations and merges into one report (`/swarm`).
- **`ketchup`** and **`ketchup-video`**: Summarizes progress since the user's last message as text or a short subtitled slide video, listing pending decisions (`/ketchup`, `/ketchup-video`).
- **`technical-writing`** and **`unslop`**: Enforces clear developer prose and strips AI writing tells (`/technical-writing`, `/unslop`).
- **`typescript-best-practices`**: Applies type-safe TypeScript rules on `.ts` and `.tsx` files.

### Design skills

- **`elevate`**: Raises real product UI craft toward premium, modern, fluid feel (`/elevate`). Read `GUIDE.md` for checklists.
- **`stageshow`**: Builds faux product UI stills, cursor demos, and bento grids in React with automated filming checks (`/stageshow`). Vendored from [Stageshow](https://github.com/benjitaylor/skills/tree/main/stageshow) by Benji Taylor (MIT; see [`skills/stageshow/VENDORED.md`](skills/stageshow/VENDORED.md)). Previewing or filming requires Node.js 20.19+ (`npm install` inside `skills/stageshow`) and local Chrome.
- **`modern-web-guidance`**: Google Chrome's guides for modern HTML, CSS, client-side JavaScript, accessibility, forms, performance and security, read from local files for web frontend work (`/modern-web-guidance`). `elevate`, `land-it` and `qa-walkthrough` point to it. Vendored from [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) by Google (Apache-2.0; see [`skills/modern-web-guidance/NOTICE.md`](skills/modern-web-guidance/NOTICE.md)). It never runs the upstream `npx` CLI. Resync: [`docs/modern-web-guidance.md`](docs/modern-web-guidance.md).
- **`chrome-extensions`**: Google Chrome's Manifest V3 guide for building and publishing Chrome extensions (`/chrome-extensions`). Vendored from the same release (Apache-2.0).

### Principle skills

19 standalone `principle-*` skills back the rules cited by `viper-mode`, including `principle-prove-it-works`, `principle-fix-root-causes`, `principle-model-the-domain`, `principle-boundary-discipline`, `principle-type-system-discipline`, `principle-sequence-verifiable-units`, `principle-subtract-before-you-add`, and `principle-test-behavior-not-implementation`.

## Configuration and architecture

### Efficiency defaults

- **Models**: `auto` / inherit parent (configure parent to Auto or Composer 2.5 Standard with Fast off).
- **Reasoning budget**: Medium or small preferred, matched to task difficulty.
- **Panels**: Single-model sequential passes by default; multi-model only on explicit high-stakes requests.
- **Context discipline**: Bulk exploration runs in fresh subagents; only concise summaries return to the main thread.
- **Change bias**: Smallest root-cause change that meets the acceptance criteria.

### Repository layout

```text
.
├── plugin.json           # Agent Plugins root manifest (Cursor-hosted / portable)
├── .claude-plugin/       # Claude Code plugin and marketplace manifests
├── .cursor-plugin/       # Cursor plugin and marketplace manifests
├── docs/                 # Usage guide, consumer install matrix, and CI policy
├── rules/                # Always-applied Cursor rule distributed with the plugin
├── scripts/              # Skill linter, token counter/checker, secret & PII guards, installers
├── skills/               # 53 skill directories (each containing SKILL.md)
├── tests/                # Python stdlib unittest suite for repo scripts
├── install.sh            # Checksum-verified release installer
├── requirements-ci.txt   # CI dependency for token counting (tiktoken==0.14.0)
├── tokens.json           # Tracked cl100k_base token and byte counts per skill
├── UPSTREAM.json         # Upstream pstack sync state, skill mapping, and unported list
└── VERSION               # Current release version
```

### Documentation

- [`docs/USAGE.md`](docs/USAGE.md): When and how to use `vstack`, concrete examples, and skill overview.
- [`docs/CONSUMING.md`](docs/CONSUMING.md): Multi-agent installation guide and consumer `AGENTS.md` configuration.
- [`docs/ci-policy.md`](docs/ci-policy.md): Workflow triggers, path gating, and CI rules.
- [`AGENTS.md`](AGENTS.md): Repository rules, branch workflow, and verification requirements.
- [`CHANGELOG.md`](CHANGELOG.md): Release notes across versions.

## Upstream sync and token budget

This repository tracks [`cursor/plugins` (`pstack`)](https://github.com/cursor/plugins/tree/main/pstack) in [`UPSTREAM.json`](UPSTREAM.json) (`last_synced_sha`, `mapping`, `unported`). A daily **Upstream watch** workflow compares `beta` against `last_synced_sha` and opens or updates a single `upstream-sync` issue when upstream drifts (closing it once `beta` catches up). Dependabot checks `requirements-ci.txt` and GitHub Actions weekly.

[`scripts/token_check.py`](scripts/token_check.py) enforces token limits on pull requests and pushes to `main` and `beta` (see [`.github/workflows/ci.yml`](.github/workflows/ci.yml)):

- Regenerate [`tokens.json`](tokens.json) with `python3 scripts/count_tokens.py` (`tiktoken` `cl100k_base`) and commit it whenever a `SKILL.md` changes. CI fails if `tokens.json` is stale.
- Existing skills cannot grow relative to the base commit unless:
  - the PR updates `last_synced_sha` (a sync PR) and each skill's growth ratio stays within its mapped upstream skill's growth ratio plus `5%`, or
  - the PR carries the `token-growth-approved` label.
- New **mapped** skills (listed in `UPSTREAM.json` `mapping`) are allowed only on sync PRs and must be `<= 35%` of the upstream skill's token count at the new SHA.
- New **original** skills (not in `UPSTREAM.json` `mapping`) are allowed on any PR if they stay `<= 400` tokens (`ORIGINAL_SKILL_MAX_TOKENS`).

Currently [`UPSTREAM.json`](UPSTREAM.json) maps 47 ported skills, while 11 skills are `vstack`-original or vendored from other sources (`qa-walkthrough`, `av-qa-walkthrough`, `follow-through`, `updater`, `stageshow`, `land-it`, `elevate`, `optimize`, `bag-and-tag`, `modern-web-guidance`, `chrome-extensions`). Upstream skills intentionally omitted under the token budget (`arena`, `automate-me`, `bro`, `make-bot-ui`, `no-comments`, `poteto-help`, and 5 `principle-*` entries) remain listed in `UPSTREAM.json` under `unported`.

## Contributing

### Branch workflow

- **`beta`** is the active integration branch. Open all day-to-day pull requests against `beta`.
- **`main`** is the stable release branch. Do not target `main` directly unless promoting `beta` for a release.
- Follow Research-Plan-Execute (RPE), keep prose docs in `docs/` rather than growing `SKILL.md` files, and keep all content free of personal information (see [`AGENTS.md`](AGENTS.md)).

### Local verification

Python 3.12+ is used in CI. Run the test and lint suite locally before pushing:

```bash
python3 scripts/lint_skills.py
python3 scripts/check_secrets.py
python3 scripts/pii-guard/pii_guard.py
python3 -m unittest discover -s tests -p 'test_*.py' -q
pip install -r requirements-ci.txt
python3 scripts/token_check.py
```

### Releasing

1. Update [`VERSION`](VERSION), the `version` field in root + Cursor/Claude `plugin.json` files and both `marketplace.json` files, and add a release section in [`CHANGELOG.md`](CHANGELOG.md).
2. Merge to `beta`, then promote `beta` to `main`.
3. Run **Actions > Release > Run workflow** on `main` (or push a matching `v<version>` tag). The workflow validates versions, runs lint and unit tests, builds `vstack-<version>.tar.gz`, `vstack-<version>.zip`, and `SHA256SUMS` via [`scripts/package_release.sh`](scripts/package_release.sh), and publishes the GitHub Release.

## License

Licensed under the `MIT` License. See [`LICENSE`](LICENSE) for full text.

`vstack` is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (`MIT`), `skills/stageshow` is vendored from [Stageshow](https://github.com/benjitaylor/skills/tree/main/stageshow) by Benji Taylor (`MIT`), and `skills/modern-web-guidance` and `skills/chrome-extensions` are vendored from [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) by Google (`Apache-2.0`; each folder keeps its `LICENSE` and `NOTICE.md`).
