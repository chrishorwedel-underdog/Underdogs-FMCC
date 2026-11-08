# FMCC: smoother setup, a smarter Director of Football, and a Windows installer you can test

FM Command Centre is a Windows companion for Football Manager. It plans your squad, scouts players, tracks development and makes safe, reversible changes to your saves.
This round makes first-run setup clearer, has the Director of Football use your own formulas and tactic, and produces an installer to test on your PC with real FM26 and FM27 saves.

## Who it's for
- You, as the first real user, testing on your own Windows PC with FM26 and FM27 installed through Steam.
- Later, other FM players installing FMCC for the first time with no help.

## Core features and experience

### 1. Polished setup
- **Step 1, Find Football Manager:** after Find, a green tick confirms each item found: the game folder, the save folder, and how many saves are in it, with the newest save's name and date. If something isn't found, a plain message explains why and offers **Choose folder**.
- **Step 2, Analytics:** the choice is explained in one sentence. Analytics stays optional and off unless you turn it on.
- **Step 3, Director of Football key:** the key field shows whether the key works before you continue (a tick or a plain error). This step can be skipped.
- **Step 4, Health check:** results are shown as a checklist: save readable, backup folder writable, FM version detected, FM running or closed. Each item is green, amber or red, with a one-line fix for anything not green.
- Setup remembers your progress. If you close FMCC halfway, it reopens on the same step.
- The look, sizing and layout stay as already approved (large and centred, with the selector and the green Find button on one line).

### 2. Smarter Director of Football
- The DOF reads your squad gaps, your Tactic fit (starter, backup and depth for each position) and your own formulas, including the starter pack.
- When you ask things like "who should I sign at left back?", it suggests players, says which gap each one fills, and quotes the formula numbers it used.
- It checks suggestions against your budget, wage limit and age preferences, if you've given them.
- Each suggestion has **Add to shortlist** and **Open profile** buttons. As before, the DOF never changes the game. Anything it proposes goes into the pending-changes queue for you to approve.
- New quick prompts: "Fill my biggest gap", "Cheapest upgrade for my XI", "Young player to develop".

### 3. Windows installer ready to test
- A downloadable Windows installer (`FMCC-Setup.exe`) is built automatically, with a desktop shortcut and a Start-menu entry.
- The installer isn't signed yet, so Windows will show a "Windows protected your PC" warning on first run. A short page explains how to get past it.
- Once installed, FMCC uses your real FM26 and FM27 saves instead of the sample squad.
- A **Test checklist** page (Settings → Testing) lists what to try on your PC and lets you mark each item pass or fail, with an optional note:
  - setup finds FM
  - a real save is read (correct date and player count)
  - a backup is created and restored
  - automatic save reading picks up a new save
  - a queued FM27 change is previewed, applied, verified and undone
  - FMMatchLens installs and is removed cleanly
  - faces and logos appear in-game
  - a Punish a Club file shows up in FM's new-career database list and its penalties take effect
- **Export report** saves your results and FMCC's logs as one file you can send back. Personal file paths are hidden.
- Live game editing stays FM27-only and keeps every existing safeguard: a verified backup first, a preview, your confirmation, a read-back check, undo and an audit history. FM26 stays read-only.

### 4. Punish a Club (any club)
Inspired by sortitoutsi's "Punish Manchester City" tool, but it works for any club in your database: search, then pick the club.
- **Penalties you can switch on, each with its own setting:**
  - **Sporting:** points deduction (choose the number of points), forced relegation, forced player releases, lower player and staff morale, fans' hatred of the club.
  - **Transfers:** a transfer embargo (choose the number of years and an age limit).
  - **Money:** wipe the bank balance, add financial-fair-play losses, cancel sponsorship income.
  - **Reputation and facilities:** lower club reputation, stadium capacity, and training and youth facilities.
- **Presets:** "Light", "Heavy" and "The full 115", which you can adjust afterwards.
- **A summary before anything is made**, in plain words, for example "Arsenal: −15 points, two-year transfer ban for over-21s, bank balance set to 0".
- **Two ways to apply it:**
  1. **New career (FM26 and FM27):** FMCC creates an editor data file and puts it in your FM editor data folder. When you start a new career, you pick it from the database dropdown at the top right. Every penalty is available this way.
  2. **Current save (FM27 only):** penalties FMCC can change in a running save (money, reputation, facilities, morale) go into the pending-changes queue, with the usual backup, preview, confirmation, read-back check and undo. Points deductions, relegation and transfer embargoes appear as "new career only", because they can't be changed safely mid-season.
- You can save several punishments (for example one per rival club). Each is kept in your history and can be removed, and FMCC deletes its own file from the editor data folder when you remove one.
- Credited in Settings → Credits as inspiration. None of its code or files are used.

## User flow
1. You download and run the installer, then open FMCC from the desktop.
2. In setup, you pick FM26 or FM27 and click the green Find button. You see what was found, optionally add a DOF key, then run the health check.
3. FMCC reads your latest real save and opens on Home.
4. Optionally, in Punish a Club you pick a club and penalties, check the summary, then create the new-career file or queue the changes on your current FM27 save.
5. You ask the DOF to fill a gap, and it suggests players with reasons. You shortlist them or queue changes for approval.
6. You work through the Test checklist, export the report and send it back. The next round then fixes whatever failed.

## UI/UX feel
- Same dark FMCC style. Setup keeps its new large, centred look.
- Results use clear status colours: green for found or passed, amber for needs attention, red for failed. Each comes with plain-English explanations and no technical error codes.
- DOF suggestions appear as cards in the chat, with a short reason and the numbers behind it.

## Implementation phases
- **Phase 1 (built now, MVP):**
  - polished setup (found-items ticks, choose-folder fallback, key check, health checklist, resume where you left off)
  - DOF using gaps, tactic fit and formulas, with suggestion cards and new quick prompts
  - an automatic installer build
  - the in-app Test checklist with Export report
  - Punish a Club: club search, every penalty, presets, a summary, the new-career file, the FM27 current-save queue, and saved punishments
  - These are checked in the browser preview, where real saves are replaced by the sample squad.
- **Phase 2:**
  - You test on your PC with FM26 and FM27 and send the report.
  - Fixes for what fails: real-save reading, automatic save pickup, FM27 live changes with undo, FMMatchLens install, in-game faces and logos.
  - FM27 support is only called verified once it passes your tests.
- **Phase 3:**
  - FMMatchLens match import (needs a sample match file or a format description)
  - a signed installer to remove the Windows warning
  - automatic in-app updates of FMCC itself
  - formula sharing codes

## Assumptions
- Steam installs only, on Windows 10 or 11. Mac isn't covered.
- The installed app's DOF uses a key you enter in setup step 3. The browser preview keeps using the existing preview key.
- The installer stays unsigned for now, so the Windows warning is expected.
- Nothing from your PC is sent anywhere automatically. You choose to export and send the test report.
- Budget, wage and age limits for the DOF come from your existing settings and rules. Nothing new is invented.
- Third-party packs (NG_Regens, logo packs, the real-names fix) are still not bundled. FMCC reads them only if you've installed them.
- Punish a Club gets its own sidebar entry under the club tools, next to Player & Teams Editor.
- FMCC writes its own editor data file (XML). FM26 and FM27 accepting it can only be confirmed on your PC, so it's on the Test checklist.
- In the browser preview, the file is created and shown for download but not placed in an FM folder, and current-save changes are applied to the sample squad only.
- Phase 1 can't prove real-game behaviour. Everything that needs your PC is listed on the Test checklist rather than claimed as working.
