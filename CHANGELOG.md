# Changelog

All notable changes to vstack. Versions follow [semantic versioning](https://semver.org/).

## Unreleased

## 1.7.0

### Added

- `lean-ci`: makes GitHub Actions CI fast and cheap without weakening required checks. Measure first, run each check at the right stage (PR gate, post-merge push, release and nightly), gate jobs with job-level `if:` so skipped required checks still report, test only the packages a diff reaches with a tested picker, share caches, cap artifact retention, and report before and after times. Includes a per-repo checklist and a worked Cargo affected-packages picker.

## 1.6.0

### Changed (skill strength over skill size)

- Skill size is no longer capped. The 35%-of-upstream cap on ported skills, the 400-token cap on original skills, the no-growth rule and the `token-growth-approved` label are removed. `token-check` now fails only on a stale `tokens.json` and reports per-skill size deltas in the job summary.
- Every skill ported from pstack is restored to full strength: the complete upstream procedure, examples, edge cases and stop conditions, adapted for all supported hosts, with every vstack-only rule kept. The old ports ran at about 25% to 35% of the upstream text.
- `viper-mode` regains its full principle index (when each principle applies), the Autonomy rules and routing to every skill, and ships 22 task playbooks under `playbooks/`, the review-bot triage reference and the PR-watch and worktree-audit scripts.
- `statechart` ships its rendering and model-checking scripts. `create-verification-skill`, `show-me-your-work` and `typescript-best-practices` ship their references and scripts.
- vstack keeps its own model defaults: subagents inherit the parent model, and panels use one model unless the user asks for a multi-model pass.
- The vstack-original skills written under the old 400-token cap are expanded into full procedure: `qa-walkthrough`, `av-qa-walkthrough`, `land-it` and `follow-through` gain setup steps, what to check in each pass, severity definitions, evidence rules and stop conditions, and the `optimize` and `elevate` playbooks spell out each step. Every existing rule is kept.

### Added

- The 10 upstream skills left out under the old budget: `automate-me`, `bro`, `make-bot-ui`, `no-comments`, `vstack-help` (from `poteto-help`), and the principles `encode-lessons-in-structure`, `exhaust-the-design-space`, `guard-the-context-window`, `laziness-protocol` and `migrate-callers-then-delete-legacy-apis`.
- `arena`, a token-efficient port of pstack's design race: frame with a hidden rubric, fan out candidates, judge, pick a base, graft, verify. Candidates run on the parent model (`auto`) by default; other models and a cross-vendor judge only on a high-stakes ask. 371 tokens, 35% of upstream.

### Changed

- `architect` routes large or contested designs to `arena` (no token growth; the parallel-sketch clause moved there).

- `in-your-own-words` has a description that says when to use it (it was the single word "Goals.").
- `lint_skills.py` fails when a skill's frontmatter `name` differs from its folder name.
- `check_secrets.py` skips `node_modules` and `dist`, which are untracked build output.
- Every workflow pins its actions to a commit, as `claude.yml` already did.
- The root and Cursor plugin descriptions no longer say the skills are for Cursor agents only.
- Port pstack 0.15.48 small updates: add a compressed `/reframe` (35% of upstream) and `viper-mode/worker.md`; fold sharpen prototype/preference line; no-subagent `reflect`; fold why author/inference/gap wording (keep multi-source hunt); pin `UPSTREAM.json` to `9e278fe`.

### Fixed

- `install.sh` and `scripts/install_for.sh` name the option when its value is missing, where they used to stop with "unbound variable".
- `scripts/package_release.sh` packages only the files tracked at `HEAD` (`git archive`). It used to copy the working tree, so release archives from 1.2.0 to 1.5.0 carried `__pycache__` folders, and compiled Python files embed the build machine's absolute path.

## 1.5.0

### Added

- `database-architect`, the Database Architect agent vendored unmodified from [claude-code-templates](https://github.com/davila7/claude-code-templates) at `1530598` (MIT, `LICENSE` and `NOTICE.md` in the folder). A short vstack `SKILL.md` replaces its "MUST BE USED" trigger with a plain one, puts its safety rules first (scratch databases only, stop servers by data directory and never with `pkill`/`killall`, never print credentials, Squawk pinned), maps its hand-offs to `optimize`, `architect` and `qa-walkthrough`, and adds SQLite notes for local app storage. The upstream file is kept as `AGENT.md`.
- `scripts/sync_database_architect.py` resyncs an exact 40-character upstream commit (it refuses branches, tags, and `latest`), reads files with `git cat-file` so nothing upstream runs, blocks on hidden Unicode and red flags (download-and-run including `irm|iex`, unpinned `npx` including `--package=`/`-p`, credential paths, instruction overrides, HTML comments; `--reviewed` allows reviewed red-flag prose while still blocking hidden Unicode), and writes `VENDORED.json`; `--check` fails on drift or a stripped manifest. Steps: `docs/database-architect.md`.

### Changed

- `architect` points schema work to `database-architect` (no token growth).
- The hidden-Unicode check both sync scripts use now also catches bidi isolates (U+2066-2069), soft hyphens, Hangul fillers, variation selectors supplement (U+E0100-E01EF), U+061C and U+180E.

## 1.4.0

### Added

- `modern-web-guidance` and `chrome-extensions`, vendored unmodified from Google Chrome's [Modern Web Guidance](https://github.com/GoogleChrome/modern-web-guidance) v1.0.0 (`4dd9683`, Apache-2.0, `LICENSE` and `NOTICE.md` in each folder). A short vstack `SKILL.md` scopes the trigger to web frontend work and looks guides up in local files (`INDEX.md`, `guides/`); it never runs the upstream `npx ...@latest` CLI, its `install` command, or `legacy-scan`, so nothing unpinned runs and no telemetry is sent. Google's own `SKILL.md` is kept as `UPSTREAM_SKILL.md` (and `GUIDE.md` for extensions).
- `scripts/sync_modern_web_guidance.py` resyncs an exact upstream tag or commit (it refuses `latest` and branches), blocks on hidden Unicode, skips scripts, and writes `VENDORED.json` with a SHA-256 for every file; `--check` fails if any vendored file drifts. Steps: `docs/modern-web-guidance.md`.

### Changed

- `elevate`, `land-it` and `qa-walkthrough` point web frontend work to `modern-web-guidance` (no token growth).

## 1.3.0

### Added

- `elevate`, a skill that raises UI craft toward premium, modern, fluid feel (hierarchy, type, color, space, motion, states, anti-slop); not a feel diagnosis (`/elevate`).

### Changed

- Encode reflect 2026-11-13 Accepted lessons: echo unique names (iyow / never-block); prove contrasted install channels; dual-ship + Projects verify (setup-vstack GUIDE); one-card / serialize shared ship files (follow-through / separate); Cursor skills-missing checklist + bag-and-tag three-manifest bump and ship-time skill-dir proof.
- `updater`: a saved `fetched/` body that does not parse, or has no usable row (a Blizzard table with no `us` row, an OpenRouter list or crates.io index cut off mid-file, an npm, PyPI, Minecraft, Rust channel or Node index body with no version, an empty tag list), stays under Unchecked sources as "saved body unparseable, truncated?" instead of dropping out of the report or crashing the run, and the report lists each `fetched/` file it used with its size. The skill says to save raw bytes only, run the repo's fast checks before opening a bump PR, leave draft with the last code push, and keep the run open until every PR it opened is merged.
- `updater`: an advisory listed in a `deny.toml` `[advisories].ignore` drops to the watch list and the report names it under "Ignored advisories" with its recorded reason; a source the HTTPS proxy refuses reads "proxy blocked (403)" instead of `URLError`; `bump --area cargo` prints the new crates and new duplicate majors a lock refresh pulled in. The skill says to try each blocked source once, try each major as its own small PR before carding it, and name every medium-or-higher finding in the report.
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
