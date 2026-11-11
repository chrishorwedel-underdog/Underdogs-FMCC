# Getting the fixed FMCC for Windows onto your PC

The startup fix was built, but the website's Download button still gives out v0.2.11 from Nov 10, which is the version with the "127.0.0.1 refused to connect" error. This plan gets the fixed installer published, and makes the Download button show whether the version on offer is the newest one.

## Who it's for
Football Manager players, starting with you, who install FMCC from the website and need the version they download to be the latest working one.

## What happened
- You pressed Save to GitHub, but no new installer was published after Nov 10. The build that makes the installer either failed or never ran.
- The new build includes a check that starts the packaged FMCC on a Windows machine before publishing. If FMCC doesn't start there, the build stops on purpose, so a broken installer never reaches the website. That check, or the packaging step just before it, is the most likely place the build stopped.
- The installer you ran is therefore still the old one. Its window opens before FMCC's engine is ready, waits, and then shows the browser's error page. That matches "nothing happens for a while, then the error".

## Core features and experience
- **A fixed installer on the Download button.** The reason the latest build stopped is found and fixed, and the build is re-run until a new version (v0.2.12 or later) is published with the startup fix. That version must pass the check that starts it on a Windows machine before publishing.
- **Honest Download button.** Next to the version, the website shows the state of the newest build:
  - "Latest version", when the newest build is the one on offer
  - "A new version is being built, check back in a few minutes", while a build is running
  - "The newest build didn't finish, so this is the last working version", when the latest build failed. The working version is still offered.
- **What you'll see once you install it.** FMCC opens on its own dark loading screen with the logo within a second or two, then switches to the app. If it can't start, it shows the reason in plain words, with Try again, Open log file and Copy details. You won't see the browser error page again.
- **Version in the app.** The footer shows the installed version, so you can confirm you're on the new one.

## User flow
1. The fix is built and published. You'll be told when the new version is on the Download button.
2. On the website, the Download button shows the new version number and "Latest version".
3. Download and run the installer. It closes any open FMCC first. Your data is kept.
4. Open FMCC. The loading screen appears, then the app.
5. If the app doesn't appear, press Copy details on the problem screen and paste it into the chat.

## UI/UX feel
- The build status is one short line under the version on the Download card, in the card's existing style. It's calm, has no technical words, and uses a small coloured dot: green for latest, amber while building, grey when the last working version is shown.
- The rest of the Download card stays as it is.

## Implementation phases
**Phase 1 – MVP (built now)**
- Find which step stopped the latest build and fix it so the build publishes a new installer.
- Keep the check that starts FMCC on a Windows machine before publishing, and make it report the reason in plain words when it fails.
- The build status line on the website's Download card.
- Confirm the new version and date appear on the Download button.

**Phase 2**
- One-click fixes on FMCC's problem screen, for example using a free connection or restoring from the latest backup.
- Confirm the in-app update prompt works end to end on a real PC.

**Phase 3**
- A signed installer, which needs a paid code-signing certificate from you.
- An uninstall choice to keep or remove your FMCC data.
- Export and import of all your FMCC data for a new PC.

## Assumptions
- The build runs on GitHub when you press Save to GitHub. Its overall result and which step failed can be read publicly. If the detailed build log is needed and can't be read without signing in, you'll be asked for a read-only GitHub access key through a secure form, not in chat.
- You'll need to press Save to GitHub once more after the fix, because the build only runs from what's on GitHub.
- Until the new version is published, the Download button keeps offering v0.2.11, with the "last working version" status line.
- The fix is only confirmed once you install the new version on your PC. The Windows check in the build makes it very likely, but it isn't the same as your PC.
- Your existing data, if any was created, is kept.
- The installer stays unsigned, so Windows still shows its warning: choose More info, then Run anyway.
