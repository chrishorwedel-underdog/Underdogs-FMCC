# FMCC on GitHub, with Automatic Windows Installer Releases

FMCC's code moves into a public GitHub repository. Every change saved there automatically builds a fresh Windows installer (FMCC-Setup.exe) and publishes it as the newest release.
The website's download button always offers that newest installer, with its version number and date.

## Who it's for
- The owner, who wants the code safely on GitHub and a new installer out after every change, without building anything by hand.
- FM players visiting the website, who want one button that downloads the current version of FMCC for Windows.

## Core features and experience

**Moving the code to GitHub**
- The code is sent to GitHub with the "Save to GitHub" button in the Emergent chat box. It connects the owner's GitHub account and creates or picks a repository; there are no commands to type.
- The repository is public, so anyone can see the code. This matches FMCC's GPL-3.0 open-source licence and the credits already shown in the app.
- Each later "Save to GitHub" sends the newest changes to the same repository.
- Private settings never go to GitHub. This covers keys, the database address and the preview environment files.

**Automatic installer builds**
- Every save to the main branch starts a build on GitHub's Windows machines. This uses the free GitHub Actions minutes that public repositories get.
- The build packages FMCC into one installer, FMCC-Setup.exe. That includes the app, its built-in parts (fmsave, FMLibreEditor, FMMatchLens support files, the league strength data and the name lists) and a Start-menu shortcut.
- Each successful build is published as a new GitHub release:
  - It gets an automatic version number that goes up on every build, for example v0.2.14.
  - Short release notes list the changes since the last release.
- If a build fails, nothing is published, and the website keeps offering the last good installer. GitHub emails the owner about the failed build.
- Name-list updates for the Player Creator (`fmcc-names.json`) are attached to the same releases. That turns on the name-update check already in the app.

**Website download**
- The download button on the website's front page shows the latest version, the release date and the file size. It downloads FMCC-Setup.exe straight from GitHub.
- The website is pointed at the repository once, through the existing release-repository setting.
  - Until that setting is filled in, the button keeps saying the download isn't set up yet.
- A short note under the button explains the warning Windows will show, because the installer is unsigned. It says to choose "More info", then "Run anyway", so first-time users aren't put off.
- Inside the Windows program, the download button stays hidden. FMCC's existing update check uses the same releases to tell users when a newer version is out.

## User flow
1. The owner clicks "Save to GitHub" in Emergent and connects GitHub the first time.
2. GitHub builds the installer by itself. A few minutes later a new release appears with FMCC-Setup.exe attached.
3. The owner gives FMCC the repository name once, in the secure keys card, then re-publishes the website.
4. A visitor opens the website, clicks "Download for Windows" and runs the installer.
5. Whenever the owner makes a change and saves to GitHub again, a new installer appears. The website and the installed app both pick it up.

## UI/UX feel
- The download button keeps its current look. It adds a version tag, the release date and size, and the small Windows-warning note.
- In the app, "a new version is available" uses the existing update card in Settings. There's no new screen.

## Implementation phases
- **Phase 1 (built now, MVP):**
  - The repository setup guide in the app's docs.
  - The automatic build-and-release on every save to main, with automatic version numbers and release notes.
  - Name-list files attached to releases.
  - The website download button showing the version, date and size, plus the unsigned-installer note.
  - The in-app update check reading the same releases.
- **Phase 2:**
  - Code signing, to remove the Windows warning once a certificate is bought.
  - A download count, and a "What's new" panel on the website built from the release notes.
- **Phase 3:**
  - Separate test builds for trying changes before they go to everyone.
  - Updates that install themselves inside the app with one click, plus a portable (no-install) zip.

## Assumptions
- The repository is public (chosen). There's no access key, and the website links straight to GitHub's download.
- A new installer is built and published on every change saved to the main branch (chosen). Version numbers go up automatically, and there's no separate "beta" channel.
- The installer is not code-signed for now (chosen). Windows SmartScreen will warn on first run.
- The owner has, or will create, a free GitHub account. Moving the code is done with Emergent's "Save to GitHub" button, not by hand.
- The repository name is given to FMCC once through the secure keys card. It is never written into the code.
- GitHub's free Actions minutes for public repositories cover these builds.
- The installer and its built-in parts follow their licences:
  - FMLibreEditor is GPL-3.0, which fits FMCC's GPL-3.0 licence.
  - fmsave and FMMatchLens are MIT, and BepInEx is LGPL-2.1.
  - Third-party packs (NG_Regens, the sortitoutsi Real Name Fix, logo and kit packs) are never included. The app keeps sending users to their official downloads.
- Installing and running on the owner's Windows PC is still unverified until the first real installer is tested there.
