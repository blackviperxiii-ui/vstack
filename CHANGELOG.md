# Changelog

All notable changes to vstack. Versions follow [semantic versioning](https://semver.org/).

## Unreleased

### Changed

- Encode reflect 2026-11-13 Accepted lessons: echo unique names (iyow / never-block); prove contrasted install channels; dual-ship + Projects verify (setup-vstack GUIDE); one-card / serialize shared ship files (follow-through / separate); Cursor skills-missing checklist + bag-and-tag three-manifest bump and ship-time skill-dir proof.
- `updater`: a saved `fetched/` body that does not parse, or has no usable row (a Blizzard table with no `us` row, an OpenRouter list or crates.io index cut off mid-file, an npm, PyPI, Minecraft, Rust channel or Node index body with no version, an empty tag list), stays under Unchecked sources as "saved body unparseable, truncated?" instead of dropping out of the report or crashing the run, and the report lists each `fetched/` file it used with its size. The skill says to save raw bytes only, run the repo's fast checks before opening a bump PR, leave draft with the last code push, and keep the run open until every PR it opened is merged.
- `follow-through`: `scripts/closeout.py` is the closeout gate. Given every PR a run opened, it refuses "done" unless each one is merged or named `--pending` with its blocker.
- AV ship check lessons: `av-qa-walkthrough` covers apps with no player (reply playback, barge-in echo test, codec boundaries, devices), prefers platform resampling over hand-written DSP, makes each scan line name the command run, keeps the real-media walk as a committed script, and puts decisions only on the decision card; `follow-through` reads the merge commit and checks when someone else merged your PR.

## 1.2.2

### Fixed

- Cursor Projects / Cloud Agents packaging: add root Agent Plugins `plugin.json` alongside `.cursor-plugin/` so Cursor-hosted marketplace installs can resolve skills the same way GitHub Import from Repo already does; expand `docs/CONSUMING.md` Projects checklist (Import from Repo, Required, Auto Refresh, new agent; Sync Skills is personal-only).

## 1.2.1

### Added

- `optimize`, a skill for app performance work: measure the real artifact, rank hot spots, fix root causes, remeasure (`/optimize`).
- `bag-and-tag`, a skill for the promote ritual: beta→main, VERSION/CHANGELOG bump, annotated tag, GitHub Release artifacts, installer verify (`/bag-and-tag`).

### Changed

- `setup-vstack` installs and configures vstack for the current coding agent (Cursor, Claude Code, Codex, Antigravity, Muse, Windsurf, OpenCode, Grok Build); Cursor-only model rule; see `docs/CONSUMING.md`.
- `README.md` restructured to standard GitHub conventions (badges, table of contents, clearer install and skill catalog sections).

## 1.2.0

### Added

- `land-it`, a skill that deep-dives a whole app for product-feel misses (UX that never quite lands, weak interactivity, QoL gaps, code shortfalls) and ranks low-effort fixes (`/land-it`).
- Multi-agent install surface: `scripts/install_for.sh` places skills into documented host paths (`.agents/skills`, `.claude/skills`, `.grok/skills`, Cursor plugin); `install.sh` gains `--target agents` and `--target grok`. Consumer docs (`CONSUMING.md`, `USAGE.md`, README) include a Works-with matrix for Cursor, Claude Code, Codex, Antigravity, Muse, Windsurf, OpenCode, Grok Build, and generic `AGENTS.md` readers; Aider/Continue and GrokHub stay documented-optional / deferred where formats are unconfirmed.
- `updater`, a skill that finds every part of an app that needs updating: Cargo, npm and PyPI dependencies, RustSec and npm advisories, Rust and Node toolchains, GitHub Actions, World of Warcraft `.toc` interface numbers (from Blizzard's version service), Minecraft releases, AI model ids, API hosts, launchers, mod sources and locale gaps. A stdlib script (`skills/updater/scripts/updater.py`) does the checks and writes a ranked report; `bump --area` applies the safe ones. Anti-cheat guards are listed but never edited.
- `stageshow`, a design skill for faux product UI stills, cursor demos and bento grids, vendored from Stageshow by Benji Taylor (MIT) at upstream `8020574`. Its short `SKILL.md` stays under the 400-token cap and points to the full `GUIDE.md`.

### Changed

- `viper-mode`, the always-apply rules, and agent docs now require RPE (Research, then Plan, then Execute) before edits, and waiting only on real (not CI-only) conflicts with other open work.
- `docs/USAGE.md` consumer install matches `docs/CONSUMING.md` (plugin / `install_for.sh` / `install.sh`; no stale `cp -R` or missing-snippet guidance).
- `docs/ci-policy.md` lists which CI jobs run on which event. The nightly CI run skips a commit that already passed CI, and every job has a timeout.

### Fixed

- `token-check` no longer fails every push and nightly run: pushes measure growth against the previous branch tip and read the approval label from the merged PR, and runs with no base check only that `tokens.json` is fresh. The job drops its pip cache, which could stall for 10 minutes, and times out after 5 minutes.

## 1.1.0

### Added

- 16 workflow skills ported from pstack: `how`, `why`, `teach`, `recall`, `architect`, `figure-it-out`, `show-me-your-work`, `blast-radius`, `interrogate`, `tdd`, `correct`, `reflect`, `swarm`, `benchmark-checklist`, `technical-writing`, `typescript-best-practices`.
- 18 `principle-*` skills, one for each principle `viper-mode` cites.
- `follow-through` (task ledger, stall detection, proven done) and `av-qa-walkthrough` (audio and video QA).
- Compressed `statechart` and `ketchup-video` ports.
- Release packaging: `install.sh`, `scripts/package_release.sh`, and a release workflow that publishes tarball and zip downloads with SHA-256 checksums.

### Changed

- `viper-mode` restates the goal and smallest change on the first message, then routes to the new skills.
- `ketchup-video` adds a subtitle strip and measured slide holds.
- Synced to upstream pstack `c742dd6`.
- Agents can load `viper-mode`, the principle skills, and the core workflow skills on their own; you no longer need a slash command for each.

### Fixed

- `how` and `why` frontmatter now parses as YAML.

## 1.0.0

- First release: `viper-mode`, `setup-vstack`, `in-your-own-words`, `sharpen`, `unslop`, `ketchup`, `qa-walkthrough`, verification and formal-verification skills, `principle-fix-root-causes`, and Cursor and Claude Code plugin packaging.
