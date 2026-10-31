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

**How and when to use vstack:** [docs/USAGE.md](docs/USAGE.md). Installing it as a Cursor plugin: [docs/CONSUMING.md](docs/CONSUMING.md).

## Install

### One-line installer (from the latest release)

```bash
# Cursor (local plugin)
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash
# Claude Code (personal skills)
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash -s -- --target claude
# Any agent that reads a skills folder
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash -s -- --target dir --dir path/to/skills
```

The installer checks the download's SHA-256 against the release. Pin a version with `--version 1.1.0`. Tarball and zip downloads are on the [Releases](https://github.com/blackviperxiii-ui/vstack/releases) page, and [CHANGELOG.md](CHANGELOG.md) lists what changed.

### Cursor
vstack is a Cursor plugin (`.cursor-plugin/plugin.json`). Install it once in Cursor and every agent gets it; never copy skills into project repos. See [docs/CONSUMING.md](docs/CONSUMING.md).

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
- **sharpen**: Deepen a task (not enlarge it), then rewrite the prompt (`/sharpen`).
- **unslop**: Cut AI tells from writing (`/unslop`).
- **ketchup**: Catch the user up since their last message; list waiting decisions (`/ketchup`).
- **qa-walkthrough**: App UI walk + code QA; ranked report; safe fixes as small beta PRs (`/qa-walkthrough`).
- **av-qa-walkthrough**: Audio/video playback, sync, quality, devices, streaming; ffprobe/ffmpeg evidence; ranked report (`/av-qa-walkthrough`).
- **follow-through**: Task ledger, check-ins, stall detection, proactive status; proven done and handoff (`/follow-through`).
- **create-verification-skill**: Generate a project-local skill that drives the real app and proves behavior (`/create-verification-skill`).
- **maintain-verification-skill**: Audit a verify skill and feature map; one PR of proven fixes max (`/maintain-verification-skill`).
- **create-formal-verification-skill**: Generate a project-local formal verification skill (`/create-formal-verification-skill`).
- **maintain-formal-verification-skill**: Resync formal verification after code drift (`/maintain-formal-verification-skill`).
- **how** / **why**: How a subsystem works; why it is shaped that way, with cited evidence (`/how`, `/why`).
- **teach**: Plain explanation built from how + why, at the reader's pace (`/teach`).
- **recall**: Rebuild recent working context into a current-state brief (`/recall`).
- **architect**: Sketch types and module boundaries before code, then implement against the sketch (`/architect`).
- **figure-it-out**: Design an auditable playbook when none fits (`/figure-it-out`).
- **show-me-your-work**: Append-only TSV decision trail for long or unattended runs (`/show-me-your-work`).
- **blast-radius**: What a change breaks beyond the diff; prove the one safety fact by running code (`/blast-radius`).
- **interrogate**: Adversarial review where only run-proven findings survive (`/interrogate`).
- **tdd**: Failing test first, only when the test path is cheap (`/tdd`).
- **correct**: Make repeated agent mistakes impossible via architecture, types, lint, tests (`/correct`).
- **reflect**: Turn this chat's learnings into skill edits, after approval (`/reflect`).
- **swarm**: Fan out parallel workers for coverage or races; one report (`/swarm`).
- **benchmark-checklist**: Vet a perf number before reporting it (`/benchmark-checklist`).
- **technical-writing**: Layered standard for docs, PR bodies, commits (`/technical-writing`).
- **typescript-best-practices**: Type-safe TS rules, auto-scoped to `.ts`/`.tsx`.
- **principle-\***: One skill per principle `viper-mode` cites (prove it works, model the domain, boundary discipline, and more).

## Efficiency defaults (baked in)

- Models: auto / inherit parent (set parent to Auto or Composer 2.5 Standard with Fast off)
- Budget: medium preferred
- Panels: single-model sequential unless high-stakes
- Context: bulk work to subagents, summaries only in main thread
- Bias: smallest change that meets the criteria; stop early when good enough

## Expand later

Still unported from pstack (see `UPSTREAM.json` `unported`): `arena` (multi-model panels, off by default here), `automate-me`, `make-bot-ui`, `no-comments` (needs a pstack agent), `poteto-help`, `bro`, and principles too small to port under the 35% token cap (their one-liners live in `viper-mode`).

## Releasing

1. Bump `VERSION`, the `version` in both `plugin.json` files and both `marketplace.json` files, and add a `CHANGELOG.md` section.
2. Land it on `beta`, then promote to `main`.
3. Run **Actions → Release → Run workflow** on `main`. It checks that the versions agree, runs lint and tests, builds `vstack-<version>.tar.gz`, `.zip`, and `SHA256SUMS` with `scripts/package_release.sh`, and publishes the `v<version>` tag and GitHub Release.

## Upstream sync and token budget

This repo tracks [cursor/plugins `pstack`](https://github.com/cursor/plugins/tree/main/pstack) in `UPSTREAM.json` (`last_synced_sha`, `mapping`, `unported`). A daily **Upstream watch** workflow checks out **`beta`**, compares against that branch’s `last_synced_sha`, and opens or updates a single `upstream-sync` issue when real upstream tip drift exists (it closes the issue when `beta` is already current); it never edits skills for you. **Dependabot** watches `requirements-ci.txt` and GitHub Actions weekly.

**Sync PRs** bump `last_synced_sha` after you port changes. **Token check** on every PR to `main` and `beta` (see `.github/workflows/ci.yml`):

- Regenerate `tokens.json` with `python scripts/count_tokens.py` (tiktoken `cl100k_base`) and commit it; CI fails if the file is stale.
- Existing skills must not grow versus `main`, unless:
  - this is a sync PR and each grown skill’s growth ratio is ≤ its mapped upstream file’s growth between the old and new SHAs, plus 5%; or
  - the PR has the `token-growth-approved` label.
- New **mapped** (upstream-ported) skills are allowed only on sync PRs and must stay ≤ 35% of the mapped upstream skill’s token count at the new SHA.
- New **original** (vstack-native, no `UPSTREAM.json` mapping) skills are allowed on any PR if they stay ≤ **400** tokens (`ORIGINAL_SKILL_MAX_TOKENS`).

Pushes to `main` and `beta` run the same limits against the commit before the push, reading the `token-growth-approved` label from the merged PR. Nightly and manual runs have no base, so they check only that `tokens.json` is fresh.

Mapped ports today: `viper-mode` ↔ `poteto-mode`, `setup-vstack` ↔ `setup-pstack`, `principle-fix-root-causes` ↔ same, `in-your-own-words`, `sharpen`, `create-formal-verification-skill`, `maintain-formal-verification-skill`, `unslop`, `ketchup`, `create-verification-skill`, `maintain-verification-skill`, `ketchup-video`, `statechart`, plus same-name ports of `how`, `why`, `teach`, `recall`, `architect`, `figure-it-out`, `show-me-your-work`, `blast-radius`, `interrogate`, `tdd`, `correct`, `reflect`, `swarm`, `benchmark-checklist`, `technical-writing`, `typescript-best-practices`, and 18 `principle-*` skills. Original: `qa-walkthrough`, `av-qa-walkthrough`, `follow-through`. Other upstream skills stay listed under `unported` until you add them.

---

Viper Stack. Rigorous. Efficient. Yours.

## Credits

vstack is adapted from [pstack](https://github.com/cursor/plugins/tree/main/pstack) by Lauren Tan (MIT). See [LICENSE](LICENSE).
