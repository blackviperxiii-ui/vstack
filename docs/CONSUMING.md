# Installing vstack in Cursor

vstack is packaged as a Cursor plugin (`.cursor-plugin/plugin.json`, skills in `skills/`, an always-applied rule in `rules/`). Install it in Cursor itself so every agent, local or cloud, can use it. **Do not copy vstack skills, rules, or AGENTS.md/CLAUDE.md sections into project repos.**

## Local Cursor (one computer)

```bash
git clone https://github.com/blackviperxiii-ui/vstack ~/vstack
mkdir -p ~/.cursor/plugins/local
ln -sfn ~/vstack ~/.cursor/plugins/local/vstack
```

Reload Cursor. Update with `git -C ~/vstack pull`.

Or install a tagged release without git: `curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash`. Rerun it to update.

## All agents, including Cloud Agents and Projects

Import this repo as a team marketplace: Cursor Dashboard, Plugins & MCPs, Team Marketplaces, Add Marketplace, Import from Repo, paste `https://github.com/blackviperxiii-ui/vstack`. Set vstack to Required and turn on Auto Refresh. Running agents keep the version they started with; new agents pick up updates.

Alternatively, submit the repo to the public Cursor Marketplace at https://cursor.com/marketplace/publish; once listed, install it from Customize or `/add-plugin vstack`.

## Claude Code

```
/plugin marketplace add blackviperxiii-ui/vstack
/plugin install vstack@vstack
```

## Other agents (Codex, etc.)

```bash
npx skills add blackviperxiii-ui/vstack
```
