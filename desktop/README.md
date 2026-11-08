# FMCC Windows program

The installer is built automatically on GitHub (`.github/workflows/windows-installer.yml`), on a Windows machine.

1. Save this project to your GitHub repository.
2. On GitHub, open **Actions → Windows installer → Run workflow**. Or push a version tag such as `v0.2.0` to also publish a GitHub release.
3. Download `FMCC-Setup-<version>.exe` from the finished run (Artifacts) or the release page.

What the build contains:
- the FMCC screens and server, with a real save reader that uses fmsave 0.10.0 (`backend/fmsave_reader.py`);
- a private local database (MongoDB `mongod.exe`) that stores data in `%APPDATA%\FMCC`;
- a program window (pywebview, which uses Microsoft Edge WebView2, built into Windows 10/11);
- FMLibreEditor's command-line tool (`fmlibre-probe`, GPL-3.0, built from tozmoz/FMLibreEditor v0.5.0) for live game changes in FM27;
- the Connections screen, which downloads BepInEx 6 IL2CPP x64 and FMMatchLens (0.7.1 for FM27, 0.6.1 for FM26) from their official release pages when you click Install;
- automatic reading of each new save while FMCC is open.

Not in this build yet:
- reading FMMatchLens `.fmlens` match archives into FMCC's Matches page (format not documented);
- live changes beyond PA and CA, and a signed installer.

None of the Windows-only parts (live game writes, add-on install, save watcher, admin restart) have been run against a real game yet.

The build records your repository name automatically, so FMCC's own update check finds your releases.
