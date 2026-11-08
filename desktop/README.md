# FMCC Windows program

## Putting FMCC on GitHub (one time)
1. In the Emergent chat box, click **Save to GitHub**, connect your GitHub account and create a **public** repository (for example `fmcc`). Choose the `main` branch.
2. Private settings stay out of GitHub: `.env` files are listed in `.gitignore`, and the build deletes any that slip through.
3. Every later **Save to GitHub** sends the newest changes to the same repository.

## Automatic installer releases
Each save to `main` runs `.github/workflows/windows-installer.yml` on GitHub's Windows machines (free minutes for public repositories). A few minutes later a new release appears:
- version `v0.2.<build number>`, going up on every build;
- `FMCC-Setup.exe` (the installer, with a Start-menu shortcut and an optional desktop shortcut);
- `fmcc-names.json`, the Player Creator's name-list update (edit `release/fmcc-names.json` to add names; only common names, never famous players);
- release notes listing the changes since the last release, plus the "More info → Run anyway" note for the unsigned installer.

If a build fails, nothing is published, the previous release stays the newest, and GitHub emails you. You can also start a build by hand: **Actions → Windows installer → Run workflow**.

## Pointing the website at the releases (one time)
Give FMCC the repository name (`your-github-name/fmcc`) as `FMCC_RELEASE_REPO` in the secure keys card, then re-publish the website. The front-page button then shows the newest version, release date and size, and downloads `FMCC-Setup.exe` straight from GitHub. Until then it says the download isn't set up yet. Inside the Windows program the button stays hidden; Settings → Updates uses the same releases to say when a newer version is out (the build records the repository and version itself).

## What the build contains
- the FMCC screens and server, with a real save reader that uses fmsave 0.10.0 (MIT) (`backend/fmsave_reader.py`);
- a private local database (MongoDB `mongod.exe`) that stores data in `%APPDATA%\FMCC`;
- a program window (pywebview, which uses Microsoft Edge WebView2, built into Windows 10/11);
- FMLibreEditor's command-line tool (`fmlibre-probe`, GPL-3.0, built from tozmoz/FMLibreEditor v0.5.0, with its licence and source link) for live game changes in FM27;
- the league strength data and the built-in name lists;
- the Connections screen, which downloads BepInEx 6 (LGPL-2.1) and FMMatchLens (MIT; 0.7.1 for FM27, 0.6.1 for FM26) from their official release pages when you click Install.

Never included: NG_Regens, the sortitoutsi Real Name Fix, logo or kit packs. FMCC sends users to their official downloads ("Downloads you need").

Not in this build yet: code signing (Windows SmartScreen warns on first run), reading FMMatchLens `.fmlens` archives, live changes beyond PA and CA.

None of the Windows-only parts (installer, live game writes, add-on install, save watcher, admin restart) have been run on a real PC yet.
