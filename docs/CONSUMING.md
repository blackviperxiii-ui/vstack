# Installing vstack for coding agents

vstack is a skill pack (`skills/`, always-apply rules, `AGENTS.md` / `CLAUDE.md`). Prefer a **plugin or marketplace** when the host has one. Otherwise install skills into the host’s **documented** skill directory (portable default: `.agents/skills/`). **Do not hand-copy playbooks into other repos** and do not invent plugin manifests. Agents can also run **`/setup-vstack`**, which detects the host and follows this matrix (Cursor-only model rule; never another host’s paths).

From a clone of this repo, project-local install (idempotent links by default):

```bash
./scripts/install_for.sh --host agents --project /path/to/your-app
# or: --mode copy
```

From a release (user-home targets only):

```bash
curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash
curl -fsSL .../install.sh | bash -s -- --target claude
curl -fsSL .../install.sh | bash -s -- --target agents
curl -fsSL .../install.sh | bash -s -- --target grok
```

## Works with

| Platform | Status | Install |
|----------|--------|---------|
| **Cursor** | First-class plugin | Local plugin or team/public marketplace (below). Fallback: `install_for.sh --host cursor --project …` → `.agents/skills/`. |
| **Claude Code** | First-class plugin | Marketplace (below) or `install.sh --target claude` / `install_for.sh --host claude`. |
| **Codex** | First-class (`.agents/skills`) | `install_for.sh --host codex --project …` or `npx skills add blackviperxiii-ui/vstack` |
| **Antigravity** | First-class (`.agents/skills`) | `install_for.sh --host antigravity --project …` |
| **Muse Code** | First-class (`.agents/skills`) | `install_for.sh --host muse --project …` (trust the workspace so project skills load) |
| **Windsurf / Cascade** | First-class via `.agents/skills` | `install_for.sh --host windsurf --project …` |
| **OpenCode** | First-class via `.agents/skills` | `install_for.sh --host opencode --project …` |
| **Grok Build** | First-class (`.grok/skills`) | `install_for.sh --host grok --project …` or `install.sh --target grok` |
| **Grok Bot / GrokHub** | Documented-generic (optional) | Keep `AGENTS.md` pointing at vstack; do **not** force-package vstack into GrokHub. Optional: Grok Build path above when using the CLI. |
| **Aider** | Documented-generic | `aider --read AGENTS.md` (or conventions that point at it). No SKILL.md loader — deferred. |
| **Continue** | Documented-generic | Rely on consumer `AGENTS.md`. No confirmed SKILL.md host path — deferred. |
| **Any AGENTS.md reader** | First-class path | Install skills (`.agents/skills` or clone `skills/`) + consumer pointer below. |

Evidence and deferred notes: research doc in the project store (`docs/multi-agent-compat-2026-11-12.md`).

## Cursor

### Local (one computer)

```bash
git clone https://github.com/blackviperxiii-ui/vstack ~/vstack
mkdir -p ~/.cursor/plugins/local
ln -sfn ~/vstack ~/.cursor/plugins/local/vstack
# or: ~/vstack/scripts/install_for.sh --host cursor --global
```

Reload Cursor. Update with `git -C ~/vstack pull`.

Or from a tagged release: `curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash`.

### Cloud Agents and Projects

Cloud Agents / Projects install team plugins at **agent start**. A personal local plugin (`~/.cursor/plugins/local`) or Sync Skills does **not** reach them. Do not confuse this with MCP server setup.

**Preferred (works for Projects): Import from Repo**

1. Cursor Dashboard → **Plugins & MCPs** → Team Marketplaces → **Add Marketplace** → **Import from Repo** → `https://github.com/blackviperxiii-ui/vstack` (not “Add plugin by URL” alone, and not MCP).
2. Set **vstack** to **Required**.
3. Turn on **Auto Refresh** (needs the Cursor GitHub App on this repo). After a release, click **Refresh** once if Auto Refresh lags.
4. Start a **new** Project / Cloud Agent (running agents keep the plugin versions they started with).

This repo ships both a Cursor Plugin (`.cursor-plugin/plugin.json`) and a root Agent Plugins `plugin.json` so Cursor-hosted packaging and GitHub import can resolve skills.

**Cursor-hosted / marketplace-listed path**

If you add vstack via the Default marketplace “Add to Marketplace → Plugin” URL flow, or later from the public Cursor Marketplace (`https://cursor.com/marketplace/publish` / Customize / `/add-plugin vstack`), still set it **Required**, Refresh, then start a **new** agent. Prefer **Import from Repo** when Projects must see skills reliably.

**Personal-only fallback:** Sync Skills / local plugin / `install_for.sh --host cursor` — fine for one machine; not a Projects fix.

## Claude Code

```
/plugin marketplace add blackviperxiii-ui/vstack
/plugin install vstack@vstack
```

## Consumer AGENTS.md pointer

In the **consumer** repo (not a full playbook paste), keep a short always-on pointer so agents load vstack instead of pstack:

```markdown
## vstack

Always load and follow the vstack skills (start with `viper-mode`). Never use pstack.
If skills live under `.agents/skills/` (or `.claude/skills/` / `.grok/skills/`), read `viper-mode/SKILL.md` first.
RPE: Research, Plan, then Execute; no edits before a written plan.
```

Optional one-liner for `CLAUDE.md`: `Strictly follow ./AGENTS.md (vstack; never pstack).`

## Other agents (Codex CLI helper)

```bash
npx skills add blackviperxiii-ui/vstack
```

## Grok Bot / GrokHub (optional)

- **Grok Build (CLI):** install into `.grok/skills/` or `~/.grok/skills/`; root `AGENTS.md` is already read for rules.
- **Grok Bot:** product skills are saved inside the Bot UI; folder `SKILL.md` trees are a Build concern.
- **GrokHub:** optional consume only — add the consumer pointer above and/or install skills into a path that checkout’s agent reads. Do not require vstack inside the GrokHub product tree.
