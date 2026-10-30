#!/usr/bin/env bash
# Build dist/vstack-<version>.tar.gz and .zip plus SHA256SUMS from the working tree.
set -euo pipefail

root="$(cd "$(dirname "$0")/.." && pwd)"
version="$(tr -d '[:space:]' < "$root/VERSION")"
name="vstack-$version"
out="$root/dist"
stage="$(mktemp -d)"
trap 'rm -rf "$stage"' EXIT

for manifest in .claude-plugin/plugin.json .cursor-plugin/plugin.json; do
	if ! grep -q "\"version\": \"$version\"" "$root/$manifest"; then
		echo "error: $manifest version does not match VERSION ($version)" >&2
		exit 1
	fi
done

mkdir -p "$stage/$name"
for path in skills rules assets docs .claude-plugin .cursor-plugin \
	README.md LICENSE CHANGELOG.md VERSION install.sh; do
	cp -R "$root/$path" "$stage/$name/"
done

rm -rf "$out"
mkdir -p "$out"
tar -C "$stage" -czf "$out/$name.tar.gz" "$name"
(cd "$stage" && zip -qr "$out/$name.zip" "$name")
(cd "$out" && sha256sum "$name.tar.gz" "$name.zip" > SHA256SUMS)
echo "Built $out/$name.tar.gz and $out/$name.zip"
