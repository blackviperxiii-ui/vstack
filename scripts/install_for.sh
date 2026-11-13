#!/usr/bin/env bash
# Install vstack skills from this checkout into a consumer project's
# documented skill directory (or, with --global, into a user skill dir).
#
#   scripts/install_for.sh --host agents --project /path/to/app
#   scripts/install_for.sh --host claude --project /path/to/app --mode copy
#   scripts/install_for.sh --host agents --global
#   scripts/install_for.sh --host cursor --global
#
# Never writes outside --project unless --global is set.
# Does not invent plugin manifests; only places SKILL.md trees where
# public host docs say skills are discovered.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
host=""
project=""
global=0
mode="link"
skill=""

usage() {
	sed -n '2,14p' "$0" | sed 's/^# \{0,1\}//'
	echo "Hosts: agents codex muse windsurf antigravity opencode claude grok cursor"
	echo "Deferred (docs only): aider continue"
	exit "${1:-0}"
}

while [ $# -gt 0 ]; do
	case "$1" in
		--host) host="$2"; shift 2 ;;
		--project) project="$2"; shift 2 ;;
		--global) global=1; shift ;;
		--mode) mode="$2"; shift 2 ;;
		--skill) skill="$2"; shift 2 ;;
		-h|--help) usage 0 ;;
		*) echo "unknown option: $1" >&2; usage 1 ;;
	esac
done

[ -n "$host" ] || { echo "--host is required" >&2; usage 1; }
case "$mode" in
	link|copy) ;;
	*) echo "--mode must be link or copy" >&2; exit 1 ;;
esac

case "$host" in
	aider|continue)
		echo "Host '$host' has no confirmed SKILL.md install path; see docs/CONSUMING.md (documented-generic only)." >&2
		exit 2
		;;
esac

# Resolve destination skill directory (and optional full-plugin dest for cursor --global).
dest=""
plugin_dest=""
case "$host" in
	agents|codex|muse|windsurf)
		if [ "$global" -eq 1 ]; then
			dest="$HOME/.agents/skills"
		else
			[ -n "$project" ] || { echo "--project DIR is required (or pass --global)" >&2; exit 1; }
			dest="$project/.agents/skills"
		fi
		;;
	antigravity)
		if [ "$global" -eq 1 ]; then
			dest="$HOME/.gemini/config/skills"
		else
			[ -n "$project" ] || { echo "--project DIR is required (or pass --global)" >&2; exit 1; }
			dest="$project/.agents/skills"
		fi
		;;
	opencode)
		if [ "$global" -eq 1 ]; then
			dest="$HOME/.agents/skills"
		else
			[ -n "$project" ] || { echo "--project DIR is required (or pass --global)" >&2; exit 1; }
			dest="$project/.agents/skills"
		fi
		;;
	claude)
		if [ "$global" -eq 1 ]; then
			dest="$HOME/.claude/skills"
		else
			[ -n "$project" ] || { echo "--project DIR is required (or pass --global)" >&2; exit 1; }
			dest="$project/.claude/skills"
		fi
		;;
	grok)
		if [ "$global" -eq 1 ]; then
			dest="$HOME/.grok/skills"
		else
			[ -n "$project" ] || { echo "--project DIR is required (or pass --global)" >&2; exit 1; }
			dest="$project/.grok/skills"
		fi
		;;
	cursor)
		if [ "$global" -eq 1 ]; then
			plugin_dest="$HOME/.cursor/plugins/local/vstack"
		else
			[ -n "$project" ] || { echo "--project DIR is required (or pass --global)" >&2; exit 1; }
			# Plugin is preferred; project fallback uses the portable agents path.
			dest="$project/.agents/skills"
		fi
		;;
	*)
		echo "unknown host: $host (use agents, codex, muse, windsurf, antigravity, opencode, claude, grok, cursor)" >&2
		exit 1
		;;
esac

if [ "$global" -eq 0 ]; then
	# Refuse paths that escape the consumer project.
	project_abs="$(cd "$project" && pwd)"
	case "$(cd "$(dirname "$dest")" 2>/dev/null && pwd)/$(basename "$dest")" in
		"$project_abs"/*) ;;
		*)
			# dest may not exist yet; check planned path prefix
			case "$dest" in
				"$project"/*|"$project_abs"/*) ;;
				*) echo "refusing to write outside --project ($project)" >&2; exit 1 ;;
			esac
			;;
	esac
fi

place_skill() {
	local name="$1"
	local src="$root/skills/$name"
	local target="$dest/$name"
	[ -f "$src/SKILL.md" ] || { echo "missing skill: $name" >&2; return 1; }
	mkdir -p "$dest"
	rm -rf "$target"
	if [ "$mode" = "link" ]; then
		ln -sfn "$src" "$target"
	else
		cp -R "$src" "$target"
	fi
}

if [ -n "$plugin_dest" ]; then
	mkdir -p "$(dirname "$plugin_dest")"
	rm -rf "$plugin_dest"
	if [ "$mode" = "link" ]; then
		ln -sfn "$root" "$plugin_dest"
	else
		mkdir -p "$plugin_dest"
		# Mirror the release layout used by install.sh / package_release.sh.
		for path in skills rules assets docs .claude-plugin .cursor-plugin \
			plugin.json README.md LICENSE CHANGELOG.md VERSION install.sh AGENTS.md CLAUDE.md; do
			[ -e "$root/$path" ] || continue
			cp -R "$root/$path" "$plugin_dest/$path"
		done
	fi
	echo "Installed vstack as a Cursor plugin at $plugin_dest (mode=$mode). Reload Cursor."
	echo "Start with /viper-mode."
	exit 0
fi

count=0
if [ -n "$skill" ]; then
	place_skill "$skill"
	count=1
else
	for skill_dir in "$root"/skills/*/; do
		[ -d "$skill_dir" ] || continue
		place_skill "$(basename "$skill_dir")"
		count=$((count + 1))
	done
fi

echo "Installed $count skill(s) into $dest (mode=$mode, host=$host)."
echo "Ensure the consumer AGENTS.md points at vstack (see docs/CONSUMING.md)."
echo "Start with /viper-mode (or load skills/viper-mode/SKILL.md)."
