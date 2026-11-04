#!/usr/bin/env bash
# Isolated integration test: no changes to the developer's Flatpak installation.
set -euo pipefail
project=$(cd "$(dirname "$0")/.." && pwd)
test_dir=$(mktemp -d)
trap 'rm -rf "$test_dir"' EXIT
export XDG_DATA_HOME="$test_dir/data"
export XDG_CACHE_HOME="$test_dir/cache"
export XDG_CONFIG_HOME="$test_dir/config"
export GNUPGHOME="$test_dir/gnupg"
mkdir -m700 "$GNUPGHOME"
gpg --batch --passphrase '' --quick-generate-key 'Flatpak update test' ed25519 sign 0
key=$(gpg --with-colons --list-secret-keys | awk -F: '$1 == "fpr" {print $10; exit}')
app=io.github.geoffbelknap.keylight-control
ref="app/$app/x86_64/master"
# A tiny app is sufficient to test origin selection, signatures and timestamps.
mkdir -p "$test_dir/build/files/bin"
printf '#!/bin/sh\nexit 0\n' > "$test_dir/build/files/bin/keylight-controller"
chmod +x "$test_dir/build/files/bin/keylight-controller"
cat > "$test_dir/build/metadata" <<EOF
[Application]
name=$app
runtime=org.kde.Platform/x86_64/6.11
sdk=org.kde.Sdk/x86_64/6.11
command=keylight-controller
EOF
flatpak build-finish "$test_dir/build"
flatpak build-export --timestamp='2020-01-01 00:00:00 +0000' \
    "$test_dir/old" "$test_dir/build" master
ostree init --mode=archive-z2 --repo="$test_dir/new"
flatpak build-commit-from --src-repo="$test_dir/old" --src-ref="$ref" \
    --timestamp='2020-01-02 00:00:00 +0000' "$test_dir/new" "$ref"
flatpak build-bundle "$test_dir/new" "$test_dir/new.flatpak" "$app" master
flatpak remote-add --user --no-gpg-verify stale "file://$test_dir/old"
flatpak install --user --noninteractive --no-deps --no-related stale "$app"
flatpak install --user --noninteractive --no-deps --no-related "$test_dir/new.flatpak"
[[ $(flatpak info --user --show-origin "$app") == stale ]]
# Reproduce the original failure before testing the repair.
if flatpak update --user --noninteractive --no-deps --no-related "$app" > "$test_dir/failure" 2>&1; then
    echo 'Expected the stale-origin update to fail' >&2
    exit 1
fi
cat "$test_dir/failure"
grep -q 'Update is older than current version' "$test_dir/failure"
bash "$project/packaging/make-update-repo.sh" "$test_dir/new.flatpak" \
    "$test_dir/site" "file://$test_dir/site" "$key"
flatpak remote-add --user keylight-control "$test_dir/site/keylight-control.flatpakrepo"
# Match the documented migration. Reinstall retains preferences by default.
flatpak install --user --noninteractive --reinstall --no-deps --no-related keylight-control "$app"
[[ $(flatpak info --user --show-origin "$app") == keylight-control ]]
flatpak update --user --noninteractive --no-deps --no-related "$app"
before=$(flatpak info --user --show-commit "$app")
# A subsequent signed release must arrive through ordinary updates.
ostree init --mode=archive-z2 --repo="$test_dir/next"
flatpak build-commit-from --src-repo="$test_dir/new" --src-ref="$ref" \
    --timestamp='2020-01-03 00:00:00 +0000' "$test_dir/next" "$ref"
flatpak build-bundle "$test_dir/next" "$test_dir/next.flatpak" "$app" master
bash "$project/packaging/make-update-repo.sh" "$test_dir/next.flatpak" \
    "$test_dir/next-site" "file://$test_dir/site" "$key"
mv "$test_dir/site" "$test_dir/previous-site"
mv "$test_dir/next-site" "$test_dir/site"
flatpak update --user --noninteractive --no-deps --no-related "$app"
after=$(flatpak info --user --show-commit "$app")
[[ "$before" != "$after" ]]
[[ "$after" == $(ostree --repo="$test_dir/site/repo" rev-parse "$ref") ]]
flatpak update --user --noninteractive --no-deps --no-related
# A fresh installation of the generated download must acquire the hosted origin.
export XDG_DATA_HOME="$test_dir/fresh-data"
flatpak install --user --noninteractive --no-deps --no-related "$test_dir/site/keylight-control.flatpak"
origin=$(flatpak info --user --show-origin "$app")
origin_url=$(flatpak remotes --user --columns=name,url | awk -v origin="$origin" '$1 == origin {print $2}')
[[ "$origin_url" == "file://$test_dir/site/repo/" ]]
flatpak update --user --noninteractive --no-deps --no-related
echo 'PASS: stale origin reproduced, migration verified, signed update applied'
