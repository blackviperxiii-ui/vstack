# Changelog

All notable changes to vstack. Versions follow [semantic versioning](https://semver.org/).

## Unreleased

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
