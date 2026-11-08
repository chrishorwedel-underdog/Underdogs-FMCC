# Connecting the Website Download Button to Underdogs-FMCC Releases

FMCC's code is now on GitHub at chrishorwedel-underdog/Underdogs-FMCC, and its first automatic Windows installer build is running.
This step points the website's download button and FMCC's update check at that repository's releases. It also makes sure the first build finishes and publishes FMCC-Setup.exe.

## Who it's for
- The owner, who wants the website's download button live and a new installer after every GitHub save.
- FM players visiting the website, who click "Download FMCC for Windows".

## Core features and experience
**Release repository setting**
- FMCC is told the repository is `chrishorwedel-underdog/Underdogs-FMCC`. This is set as the release-repository setting in the app's secure settings, never written into the code.
- FMCC accepts the repository in any of the usual forms, such as the full address with `https://github.com/` or with `.git` on the end. A pasted link always works.
- The same setting turns on two other things:
  - The Player Creator's name-update check, which reads `fmcc-names.json` from the newest release.
  - FMCC's own "new version available" check in Settings.

**Website download button**
- **While the first build is still running:** the button says "No release has been published yet".
- **Once a release exists:** it shows the version (v0.2.1 first), the release date and the size, plus the note about Windows' "More info → Run anyway" warning. It downloads FMCC-Setup.exe straight from GitHub.
- The website must be re-published once for the setting to reach the live site.

**First build check**
- If the first GitHub build fails, the owner shares the error from the Actions tab and the builder fixes the build. The next GitHub save then retries it.
- Nothing is published until a build succeeds.

## User flow
1. The builder saves the release-repository setting and confirms the preview's download button can read the repository.
2. The owner waits for the GitHub build to finish, then checks that Releases shows FMCC-Setup.exe.
3. If the build fails, the owner shares the error, the builder fixes it, and the owner saves to GitHub again.
4. The owner re-publishes the website. The live download button shows the newest release.
5. The owner downloads and installs FMCC-Setup.exe on their PC to try it.

## UI/UX feel
- No new screens. The existing download button fills in with the version, date and size.

## Implementation phases
- **Phase 1 (now, MVP):**
  - Set the release repository.
  - Accept full GitHub addresses.
  - Confirm the download button and update checks read the repository.
  - Fix the first build if it fails.
- **Phase 2:**
  - "What's new" from the release notes under the download button.
  - A download count.
- **Phase 3:**
  - Code signing to remove the Windows warning.
  - Separate test builds.

## Assumptions
- The repository is `chrishorwedel-underdog/Underdogs-FMCC`, taken from the address the owner gave. It stays public.
- The release-repository setting is used for both the preview and the published website.
- The repository name isn't a secret, but it is stored with the other settings rather than in the code, as agreed earlier.
- The first build may take 10–20 minutes because it builds FMLibreEditor's tool from source.
- Installing and running FMCC on the owner's PC remains unverified until the first installer is tested there.
