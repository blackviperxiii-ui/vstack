# CI policy

Which workflow jobs run on which event, and the rules every workflow change keeps. Update this file in the same PR as any workflow change.

All jobs run on Linux (`ubuntu-latest`). There are no Windows or macOS jobs and no uploaded artifacts.

## Run-on and skip-on

| Event | Runs | Skips | Cancelled by a newer run? |
| --- | --- | --- | --- |
| Pull request to `beta` or `main` | `ci.yml`: `lint` (skill lint, secret scan, unit tests) and `token-check` (growth vs the PR base). `pii-guard.yml`: `pii-guard`. | `lint` when only `docs/`, `assets/` or `README.md` change; `token-check` also when only `tests/` change. A skipped check still reports as passed. | Yes |
| Push to `beta` | `lint`, `token-check` (growth vs the commit before the push, label read from the merged PR), `pii-guard` | Nothing | Yes, a newer push to `beta` |
| Push to `main` | `lint`, `token-check`, `pii-guard` | Nothing | No |
| Merge queue | `lint`, `token-check` (growth vs the queue base), `pii-guard` | Nothing | No |
| Tag `v*`, or a manual Release run on `main` | `release.yml`: lint, tests, package, publish the GitHub Release | Nothing | No (`release` group never cancels) |
| Nightly, 08:25 UTC on the default branch | `lint`, `token-check` (checks only that `tokens.json` is fresh, since a nightly has no base) | Both jobs when the commit already passed a push, nightly or manual CI run | No |
| Manual CI run | `lint`, `token-check` (freshness only) | Nothing | No |
| Daily, 14:00 UTC | `upstream-watch.yml`: opens or closes the upstream drift issue | Nothing | No |
| Issue label or `@claude` comment by the owner | `claude.yml` | Everyone else's events | No |

Required checks on `beta`: `lint`, `token-check`, `pii-guard`.

## Rules

- Every job sets `timeout-minutes`, sized at a few times its usual run time.
- Uploaded artifacts that aren't release assets keep `retention-days: 7` or less. Release assets go to the GitHub Release, not to artifact storage.
- Heavy work never runs on pull requests. Pull requests run only the short gate above.
- Path gating uses a job-level `if:` on the `changes` job's outputs, never a workflow-level path filter, so skipped required checks still report.
- No pip cache: the install is small, and a refused cache restore can stall a job for 10 minutes.
