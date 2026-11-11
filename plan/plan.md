# FMCC for Windows: a standalone app that starts every time

The Download button on the FMCC website installs FMCC as a self-contained Windows program. It runs entirely on your PC, reads your Football Manager saves directly and keeps your data on your computer.

## Who it's for
Football Manager players who install FMCC from the website and expect it to open like any other PC program: no internet needed for daily use, no setup and no technical steps.

## The problem today
After installing, the FMCC window opens on an error page: "Hmmm… can't reach this page – 127.0.0.1 refused to connect". The window opens before FMCC's own engine has started, or the engine fails to start, so there is nothing for the window to show. The installed app never gets past this point.

## Core features and experience
- **Everything in the installer.** One download installs everything FMCC needs, including the part that stores your data, and it all runs on your PC. Nothing else to install or sign up for.
- **Works offline.** Once installed, FMCC runs without internet. A connection is only used to check for FMCC updates and to download the optional packs from the Downloads page.
- **Data stays on your PC.** Careers, history, settings, created players, punishments and backups are kept in your Windows user folder. Nothing is sent to the website. Updating or reinstalling FMCC keeps them.
- **Loading screen.** When FMCC opens you see an FMCC-branded loading screen, never a browser error page. It switches to the app as soon as the app is ready.
- **Plain reason if it can't start.** If FMCC fails to start, the loading screen says why in everyday words, says what to try, and offers:
  - **Try again**
  - **Open log file**, a text file you can send for help
  - **Copy details**

  Problems it recognises by name:
  - FMCC is already open
  - another program is using the connection FMCC needs on your PC
  - Windows security or antivirus blocked part of FMCC
  - the data folder can't be written to
  - a file is missing from the install, with advice to reinstall
- **One copy at a time.** Opening FMCC while it's already running brings the open window to the front instead of starting a second copy that fails.
- **Clean shutdown.** Closing the window stops everything FMCC started, so nothing keeps running in the background and the next start is clean.
- **Website download link.** The website's Download button always points to the latest fixed installer, and its version label is the version you actually get.

## User flow
1. Press **Download FMCC for Windows** on the website.
2. Run the installer. Windows may warn that the installer isn't signed; choose More info, then Run anyway. Then finish the short setup.
3. FMCC opens from the Start menu or desktop shortcut. The loading screen shows for a few seconds.
4. The app appears, ready to read your FM saves.
5. If something goes wrong at step 3, the loading screen explains it and offers Try again, Open log file or Copy details.

## UI/UX feel
- The loading screen uses FMCC's dark look and logo, with a quiet progress indicator and a single status line, for example "Starting FMCC…" or "Getting your data ready…".
- Error messages are short, calm and written for non-technical players, with one clear next step. Technical detail stays in the log file.

## Implementation phases
**Phase 1 – MVP (built now)**
- Every installed part starts in order, and the window waits for FMCC to be ready before showing it.
- The loading screen and the plain-reason error screen, including Try again, Open log file and Copy details.
- The single-copy rule and clean shutdown.
- A startup log in the data folder.
- Data saved in the Windows user folder and kept through updates and reinstalls.
- The website's Download button and version label point to the new installer.

**Phase 2**
- A self-check on the error screen that fixes common causes in one click. For example, it can move to a free connection on your PC or rebuild a damaged data store from the latest backup.
- The update prompt is confirmed end to end on a real PC: download, install, restart into the new version with data intact.

**Phase 3**
- A signed installer so Windows stops showing the "protected your PC" warning. This needs a paid code-signing certificate from you.
- An uninstall option to keep or remove your FMCC data.
- Export and import of all your data, for moving to a new PC.

## Assumptions
- The installed app does not depend on the website at all: no account and no sign-in. The website stays a separate place to try FMCC and download it.
- Your data on the website and your data on your PC are separate and are not merged.
- Windows 10 and 11 (64-bit) are supported. Mac and Linux are not.
- The installer stays unsigned in Phase 1, so the Windows warning remains until Phase 3.
- The exact reason your PC refused the connection can't be seen from here. Phase 1 fixes the startup order and covers the known failure causes. Whether it starts cleanly on your PC is only confirmed once you install the new version. If it still fails, the new error screen and log file will show why.
- A new installer version is published to the website's Download button once Phase 1 is built. You will need to download and reinstall it once.
- Data from earlier installs, if any was created, is kept and used by the new version.
