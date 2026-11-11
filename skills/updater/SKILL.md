---
name: updater
description: Find everything in an app that needs updating (deps, advisories, toolchains, CI, game addons, mod sources, model ids, APIs); safe bumps as PRs, the rest as cards. /updater
---

# Updater

Keeps an app's support surfaces current. Scripts read; you read only `report.md`. Cite **viper-mode**.

## 1. Run

```bash
python3 <this skill>/scripts/updater.py run --repo .
```

It inventories surfaces from the repo itself (manifests, lockfiles, workflows, `.toc` files, model ids, API hosts, launchers, mod sources, anti-cheat guards, locales), checks each against its official upstream, and writes a ranked report outside the repo. "Unchecked sources" lists URLs the shell can't reach: fetch each with your web tool, save the raw body as `<out>/fetched/<name>`, rerun.

## 2. Act by `action`

- **auto**: one branch and PR per area: `updater.py bump --area cargo|npm|pypi|wow`, run the repo's fast checks, open the PR into the integration branch (often `beta`), merge on green.
- **card**: majors, unsound or unmaintained crates, fixes needing a major, toolchain and action majors. One card or issue each, with current → latest and the note, on the repo's board or tracker.
- **manual**: verify (unlisted model ids, mod rules) before changing code; then card it.
- **watch**: no action now.
- **guarded**: anti-cheat and other safety lists. Never edit for an update; a change may only add protection.

## 3. Report

Counts per severity, PRs opened, cards made, unchecked sources. Nothing changed without a check that ran.
