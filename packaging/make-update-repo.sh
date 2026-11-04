#!/usr/bin/env bash
# Export the exact reviewed release, without rebuilding or changing its commit.
set -euo pipefail

if [[ $# != 4 ]]; then
    echo "Usage: $0 BUNDLE OUTPUT-DIRECTORY PUBLIC-BASE-URL SIGNING-KEY" >&2
    exit 2
fi
bundle=$(realpath "$1")
output=$2
base_url=${3%/}
signing_key=$4
app=io.github.geoffbelknap.keylight-control
[[ ! -e "$output" ]] || { echo "Output already exists: $output" >&2; exit 1; }
mkdir -p "$output"
ostree init --mode=archive-z2 --repo="$output/repo"
flatpak build-import-bundle --gpg-sign="$signing_key" "$output/repo" "$bundle"
flatpak build-update-repo --generate-static-deltas --gpg-sign="$signing_key" "$output/repo"
public_key=$(gpg --batch --export "$signing_key" | base64 -w0)
[[ -n "$public_key" ]]
cat > "$output/keylight-control.flatpakrepo" <<EOF
[Flatpak Repo]
Title=Key Light Control
Url=$base_url/repo/
Homepage=https://github.com/geoffbelknap/keylight-control
Description=Official Key Light Control releases
GPGKey=$public_key
EOF
cat > "$output/keylight-control.flatpakref" <<EOF
[Flatpak Ref]
Title=Key Light Control
Name=$app
Branch=master
IsRuntime=false
Url=$base_url/repo/
SuggestRemoteName=keylight-control
RuntimeRepo=https://dl.flathub.org/repo/flathub.flatpakrepo
GPGKey=$public_key
EOF
# Bundle users also acquire the maintained origin on a fresh installation.
flatpak build-bundle --repo-url="$base_url/repo/" \
    --runtime-repo=https://dl.flathub.org/repo/flathub.flatpakrepo \
    --gpg-keys=<(gpg --batch --export "$signing_key") \
    "$output/repo" "$output/keylight-control.flatpak" "$app" master
touch "$output/.nojekyll"
