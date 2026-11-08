# FMCC Windows program

The installer is built automatically on GitHub (`.github/workflows/windows-installer.yml`), on a Windows machine.

1. Save this project to your GitHub repository.
2. On GitHub, open **Actions → Windows installer → Run workflow**. Or push a version tag such as `v0.2.0` to also publish a GitHub release.
3. Download `FMCC-Setup-<version>.exe` from the finished run (Artifacts) or the release page.

What the build contains:
- the FMCC screens and server, with a real save reader that uses fmsave 0.10.0 (`backend/fmsave_reader.py`);
- a private local database (MongoDB `mongod.exe`) that stores data in `%APPDATA%\FMCC`;
- a program window (pywebview, which uses Microsoft Edge WebView2, built into Windows 10/11).

Not in this build yet:
- reading FMMatchLens `.fmlens` match archives and the real one-click BepInEx 6 + FMMatchLens install;
- the real hidden game editor (FMLibreEditor). Game changes stay inside FMCC.

The build records your repository name automatically, so FMCC's own update check finds your releases.
