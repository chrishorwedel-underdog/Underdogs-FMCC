# FMCC — Match add-on, automatic save reading, live game changes and the original sidebar

FMCC on Windows can now:
- install the FMMatchLens match add-on with one click;
- read each new save automatically as soon as FM writes it;
- apply your approved changes to your running FM27 game through FMLibreEditor.

The sidebar also goes back to its original section names.

## Who it's for
One manager playing Football Manager on Steam for Windows, with offline single-player saves, running FMCC next to the game.

## Core features and experience

**1. One-click match add-on install (FMMatchLens)**
- **Connections screen:** a new screen that finds your Steam FM folder and shows whether each piece is installed: BepInEx 6 (the add-on loader), the FMMatchLens plugin and the FMMatchLens dashboard.
- **"Install match add-on" button.** After you confirm, it puts in:
  - BepInEx 6 IL2CPP x64, the version FMMatchLens requires;
  - the right FMMatchLens version for your game: 0.7.1 for FM27 or 0.6.1 for FM26;
  - the FMMatchLens dashboard.
- **FM must be closed while installing.** FMCC tells you if it's running.
- **Every file FMCC adds is recorded,** so "Remove match add-on" takes out exactly those files and nothing else.
- **After installing,** FMCC asks you to start FM once until the main menu appears. It then checks BepInEx's log and marks the add-on as working, or says what went wrong.
- **"Open match dashboard" button** opens FMMatchLens's own dashboard for live matches and saved `.fmlens` matches.
- **Matches page:** FMCC's own Matches page keeps showing labelled sample data. Reading `.fmlens` files there waits until their format is known.
- **Updates:** the Updates list tracks BepInEx 6 instead of 5.x.

**2. Automatic reading when a new save appears**
- **Watching the folder:** while FMCC is open, it watches the career's save folder. When FM finishes writing a save, FMCC waits until the file stops changing, then reads it.
- **A notice shows what was read:** the in-game date and the number of players, with a link to the "Check my save" report.
- **Duplicates are skipped:** a save FMCC has already read is skipped, as is a file still being written.
- **On/off setting:** "Read new saves automatically" in Settings, on by default. The refresh button still works.

**3. Writing changes into the real game (FM27 on Steam)**
- **What it applies:** FMCC applies the changes it already queues (potential changes from Dynamic Potential, Elite Training and Breakout Player). It uses FMLibreEditor's command-line tool, which is built into the FMCC installer.
- **One approval per batch:** the change queue lists every change in the batch, each player's current and new value. One "Apply batch" confirmation applies them all.
- **Checks before applying:**
  - FM27 is running, with the save that matches your FMCC career loaded;
  - FMLibreEditor recognises this game version and passes its safety checks;
  - FMCC has made a verified copy of the newest save file;
  - no change in the batch has already been applied (no duplicate awards).
- **While applying:** each change is read back to confirm it took. If one fails, the rest of the batch stops, and FMCC lists the changes already made.
- **Undo:** each change keeps its old value, so "Undo batch" puts it back while the same save is loaded.
- **Record:** each applied batch is recorded with who approved it, when, each old and new value, and the result. These records are only ever added to, never edited.
- **Keeping the changes:** a reminder appears after applying: press Continue in FM, then save your game.
- **When nothing is applied:**
  - FM26 saves stay read-only, because FMLibreEditor only supports FM27;
  - on an FM27 version FMLibreEditor doesn't recognise, FMCC applies nothing and says why.
- **Admin permission:** if Windows blocks access to the game, FMCC asks to restart itself as administrator.

**4. Sidebar restored to the original sections**
- **Order, top to bottom:**
  1. Project Safety and Appearance, as plain links at the top.
  2. Home, Dynamic Potential, Breakout Player, Scout Players, Monthly Reports, Moneyball, Squad, Development, Elite Training and Matches, as cards.
  3. "Chat with your Director of Football" at the bottom.
- **What the new entries open:**
  - Project Safety opens backups, save checks and the game-change record.
  - Appearance opens a page marked "Coming soon".
  - Moneyball opens the comparison in Scouting.
- **"Awards" removed:** the word "Awards" disappears from the screens. Dynamic Potential and Breakout Player become separate pages, and the history kept for them is unchanged.
- **Fit:** the whole sidebar fits on an 800px-high screen.

## User flow
1. Open FMCC → Connections → Install match add-on → start FM once → the add-on shows as working.
2. Play FM. Each time FM saves, FMCC reads the save automatically and shows a notice.
3. Plan in Dynamic Potential, Breakout Player or Elite Training. The changes go into the queue.
4. With FM27 running and the same save loaded, open the queue, review the batch and press Apply batch.
5. FMCC backs up the save, applies and checks each change, and records the batch.
6. Press Continue in FM, then save. FMCC reads that save automatically and shows the new values.

## UI/UX feel
The same dark FMCC look, with the sidebar styled like the original screenshot. Connections uses green, amber and red status labels with one clear action button per tool. The batch screen is a plain table of old and new values, with a prominent red "Apply batch" button and the reminder to save in FM.

## Implementation phases
**Phase 1 (built now)**
- The match add-on install, removal and status check.
- Automatic save reading.
- Live game changes with batch approval, backup, checks, undo and the change record.
- FMLibreEditor's command-line tool built into the installer.
- The Connections screen.
- The original sidebar.

**Phase 2**
- Reading FMMatchLens `.fmlens` matches into FMCC's Matches page, once a sample match file is shared or the format is documented.
- Live changes beyond potential: attributes, morale, fitness, contracts.

**Phase 3**
- A signed installer, so Windows stops showing its "protect your PC" warning: through Microsoft's signing service or a bought certificate.
- Merging Squad and Development, and real Appearance settings.

## Assumptions
- **Steam only:** you play on Steam, so the match add-on install targets the Steam FM folder only.
- **Unsigned installer:** Windows will keep showing its "protect your PC" warning when you install (click "More info" → "Run anyway").
- **Matches reading:** "Leave match data for later" still applies. The add-on gets installed and checked, but FMCC doesn't read its matches yet.
- **Downloads:** the add-on files are downloaded from the official BepInEx and FMMatchLens release pages when you click Install. They aren't bundled into the installer.
- **FMLibreEditor's license:** its command-line tool is built from its open-source code into the installer. Its GPL-3.0 license and source link ship with FMCC.
- **Automatic reading:** it only runs while FMCC is open.
- **Testing:** nothing here can be tested against a real game or save from this build environment. It gets proven on your PC through the Connections status checks and the "Check my save" report.
- **Sidebar details:** Breakout Player's subtitle ("This season's breakout nominations") and its colour are new, because it wasn't in the original screenshot.
