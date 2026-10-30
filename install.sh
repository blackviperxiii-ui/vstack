#!/usr/bin/env bash
# Install vstack from a GitHub release.
#
#   curl -fsSL https://raw.githubusercontent.com/blackviperxiii-ui/vstack/main/install.sh | bash
#   curl -fsSL .../install.sh | bash -s -- --target claude --version 1.1.0
#
# Targets:
#   cursor  Cursor local plugin at ~/.cursor/plugins/local/vstack (default)
#   claude  Claude Code personal skills at ~/.claude/skills/<skill>
#   dir     Skills only, into --dir PATH (any agent that reads a skills folder)
set -euo pipefail

repo="blackviperxiii-ui/vstack"
target="cursor"
version="latest"
dir=""

usage() {
	sed -n '2,12p' "$0" 2>/dev/null | sed 's/^# \{0,1\}//'
	exit "${1:-0}"
}

while [ $# -gt 0 ]; do
	case "$1" in
		--target) target="$2"; shift 2 ;;
		--version) version="${2#v}"; shift 2 ;;
		--dir) dir="$2"; shift 2 ;;
		-h|--help) usage 0 ;;
		*) echo "unknown option: $1" >&2; usage 1 ;;
	esac
done

case "$target" in
	cursor|claude) ;;
	dir) [ -n "$dir" ] || { echo "--target dir needs --dir PATH" >&2; exit 1; } ;;
	*) echo "unknown target: $target (use cursor, claude, or dir)" >&2; exit 1 ;;
esac

for tool in curl tar; do
	command -v "$tool" >/dev/null || { echo "$tool is required" >&2; exit 1; }
done

if [ "$version" = "latest" ]; then
	version="$(curl -fsSL "https://api.github.com/repos/$repo/releases/latest" \
		| sed -n 's/.*"tag_name": *"v\{0,1\}\([^"]*\)".*/\1/p' | head -n1)"
	[ -n "$version" ] || { echo "could not find the latest release" >&2; exit 1; }
fi

name="vstack-$version"
base="${VSTACK_RELEASE_BASE:-https://github.com/$repo/releases/download/v$version}"
work="$(mktemp -d)"
trap 'rm -rf "$work"' EXIT

echo "Downloading $name"
curl -fsSL -o "$work/$name.tar.gz" "$base/$name.tar.gz"
curl -fsSL -o "$work/SHA256SUMS" "$base/SHA256SUMS"
expected="$(grep " $name.tar.gz\$" "$work/SHA256SUMS" | cut -d' ' -f1)"
if command -v sha256sum >/dev/null; then
	actual="$(sha256sum "$work/$name.tar.gz" | cut -d' ' -f1)"
else
	actual="$(shasum -a 256 "$work/$name.tar.gz" | cut -d' ' -f1)"
fi
[ -n "$expected" ] && [ "$expected" = "$actual" ] || { echo "checksum mismatch for $name.tar.gz" >&2; exit 1; }
tar -C "$work" -xzf "$work/$name.tar.gz"
src="$work/$name"

install_skills() {
	mkdir -p "$1"
	for skill in "$src"/skills/*/; do
		skill="$(basename "$skill")"
		rm -rf "${1:?}/$skill"
		cp -R "$src/skills/$skill" "$1/$skill"
	done
	echo "Installed $(ls "$src/skills" | wc -l | tr -d ' ') skills into $1"
}

case "$target" in
	cursor)
		dest="$HOME/.cursor/plugins/local/vstack"
		rm -rf "$dest"
		mkdir -p "$(dirname "$dest")"
		cp -R "$src" "$dest"
		echo "Installed vstack $version as a Cursor plugin at $dest. Reload Cursor."
		;;
	claude) install_skills "$HOME/.claude/skills" ;;
	dir) install_skills "$dir" ;;
esac
echo "Start with /viper-mode."
