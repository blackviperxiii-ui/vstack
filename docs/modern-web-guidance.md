# Modern Web Guidance: vendoring and resync

`skills/modern-web-guidance` and `skills/chrome-extensions` are vendored from
[GoogleChrome/modern-web-guidance](https://github.com/GoogleChrome/modern-web-guidance)
(Apache-2.0). That public repository is a built copy of
`GoogleChrome/modern-web-guidance-src`. The pinned release and a SHA-256 of
every vendored file are in each folder's `VENDORED.json`.

## What vstack keeps and changes

| File | Owner | Notes |
| --- | --- | --- |
| `guides/**`, `references/**`, `LICENSE` | Google | Copied byte for byte. CI fails if one changes (`--check`). |
| `UPSTREAM_SKILL.md` / `GUIDE.md` | Google | Upstream `SKILL.md`, renamed so hosts load the vstack wrapper instead. |
| `SKILL.md`, `NOTICE.md` | vstack | Wrapper trigger and credits. The sync never touches them. |
| `INDEX.md`, `VENDORED.json` | generated | Written by the sync script. |

The wrapper reads local files only. vstack never runs the upstream CLI
(`npx modern-web-guidance@latest ...`): that would run whatever npm serves that
day and start a telemetry process that reports to Google. Its `install` command
(which runs a second package, `npx skills`) and `legacy-scan.mjs` are not used.
If someone does run the CLI, pin `modern-web-guidance@1.0.0` and set
`DISABLE_TELEMETRY=1`.

## Resync to a new upstream release

1. Pick an exact tag (`vX.Y.Z`) from the upstream releases. Never `latest` or a
   branch; the script refuses them.
2. Review the upstream diff before syncing:
   `git diff <old-commit> vX.Y.Z -- skills/` in a clone. Read changes to both
   `SKILL.md` files in full and look for new instructions to run commands, fetch
   URLs, send data, or read credentials. Note any new non-Markdown files.
3. Sync:

   ```bash
   git clone https://github.com/GoogleChrome/modern-web-guidance.git /tmp/mwg
   python3 scripts/sync_modern_web_guidance.py --ref vX.Y.Z --source /tmp/mwg
   python3 scripts/sync_modern_web_guidance.py --check
   ```

   The sync stops if any file has hidden Unicode (zero-width, bidi-control or
   tag characters). Scripts are skipped and listed under `skipped` in
   `VENDORED.json`.
4. If upstream changed its workflow (new CLI flags, new guide id format), update
   the vstack `SKILL.md` wrapper to match, keeping it offline and under the
   400-token cap. Update `NOTICE.md` if the list of local changes changed.
5. Run the full local checks (`AGENTS.md`), add a `CHANGELOG.md` line naming the
   new tag and commit, and open a PR into `beta`.
