# Maintained Flatpak update repository

## Rollout status

The repository publication workflow is in `.github/workflows/publish-flatpak.yml`.
Hosting and the signing secret are configured. The first release deployment must
be verified before using the URLs below. Existing GitHub release bundles remain
available through the README until that verification is complete.

The stable repository URL will be:
`https://geoffbelknap.github.io/keylight-control/repo/`.
Keep this URL and its signing key stable across releases.

The public signing key is tracked in `packaging/release-signing-key.asc`.
Its fingerprint is `FA8C9899C42DD65A2A8D5F87B920239E36BDC93E`.
The workflow checks the secret against this reviewed public key before signing.

## One-time maintainer setup

1. In this GitHub repository's **Settings → Pages**, select **GitHub Actions**
   as the build and deployment source. Reserve this Pages site for the Flatpak
   repository: each deployment replaces the site's contents.
2. Create a dedicated signing key on a trusted machine and back it up securely:

   ```sh
   gpg --quick-generate-key 'Key Light Control releases' ed25519 sign 0
   gpg --list-secret-keys --keyid-format long
   ```

   Use a dedicated, unencrypted CI signing key; the workflow signs unattended.
   Export it directly to the GitHub Actions secret, substituting its fingerprint:

   ```sh
   gpg --armor --export-secret-keys FINGERPRINT |
     gh secret set FLATPAK_GPG_PRIVATE_KEY --repo geoffbelknap/keylight-control
   ```

   Never commit the private key. Keep an offline backup: silently replacing it
   would break existing installations' signature verification.
3. Merge the workflows and scripts before publishing the next tested release.
   Include them in the release tag. Publication runs on **release published**,
   and ignores prereleases. Previously published releases are not retroactively
   deployed. Use the normal next patch release to bootstrap the repository.
4. Verify the deployment, test the install and migration below, and then replace
   the README's default bundle instructions with the repository instructions.

## Release behavior

The workflow verifies the published bundle's checksum, imports that exact commit,
signs it and the repository summary, and deploys through GitHub Pages. It creates
a `.flatpakref`, `.flatpakrepo`, and an alternative bundle carrying the maintained
origin and public verification key. It does not rebuild reviewed application code
or replace GitHub release assets.

Publications are serialized. An older/equal version, older/equal commit timestamp,
or unexpected signing key change is rejected before deployment. Tags use
`vMAJOR.MINOR.PATCH`. A failed publication leaves the previous deployment in place.
For a rollback, publish a new patch release containing the reverted code with a
new build timestamp. Do not move release tags or overwrite reviewed assets.

The workflow constructs a complete repository snapshot for each release. Clients
download the current signed commit; historical repository objects are not required
for ordinary updates. Reviewed bundles remain in GitHub releases for archival use.

## Install after rollout

```sh
flatpak remote-add --user --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
flatpak remote-add --user --if-not-exists keylight-control \
  https://geoffbelknap.github.io/keylight-control/keylight-control.flatpakrepo
flatpak install --user keylight-control io.github.geoffbelknap.keylight-control//master
```

Desktop installation can use
`https://geoffbelknap.github.io/keylight-control/keylight-control.flatpakref`.
Subsequent releases arrive through the desktop updater or `flatpak update`.

## Migrate an existing installation after rollout

Quit Key Light Control, add the two remotes above, and run:

```sh
flatpak install --user --reinstall keylight-control io.github.geoffbelknap.keylight-control//master
flatpak info --user --show-origin io.github.geoffbelknap.keylight-control
flatpak update --user
```

The origin must now be `keylight-control`. Reinstallation preserves the app's
preferences and custom light names; do not use `uninstall --delete-data`.
An existing remote named `keylight-control` must point to the URL above and trust
the official signing key; inspect `flatpak remotes --user --show-details` if the
name is already in use. A development build newer than the published release may
be replaced during this explicit migration, so migrate to a release containing
the desired fixes.

Do not re-enable stale `*-origin` development repositories as a migration step.
Keep development builds in a separate Flatpak user installation by setting
`XDG_DATA_HOME`, `XDG_CONFIG_HOME`, and `XDG_CACHE_HOME` to a dedicated test directory
for every build/install/run/update command. The integration test demonstrates
this isolation without touching the developer's installed app.

## Regression coverage

Run `bash tests/check_flatpak_updates.sh` with Flatpak, OSTree, and GnuPG installed.
It uses temporary data/config/cache directories and a temporary signing key. It
reproduces the stale-origin failure, migrates using the commands above, verifies a
subsequent signed update, and checks that a fresh generated bundle uses the hosted
origin. These checks run in ordinary CI and before repository publication.

See the [Flatpak hosting documentation](https://docs.flatpak.org/en/latest/hosting-a-repository.html)
for signed repository and GitHub Pages distribution details.
