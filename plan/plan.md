# Fix "FMCC couldn't find the club you manage" in setup

FMCC's setup wizard reads a Football Manager save and works out which club you manage. Right now it fails on the "Chris Horwedel - Wrexham 27" save. This fix gives FMCC more ways to find the club, and if they all fail, you pick the club yourself from a list taken from the save.

## Who it's for
Anyone setting up FMCC on Windows whose FM27 save the save reader can't fully read. The first case is the Wrexham 27 career.

## Why it fails today
- The save reader is a third-party tool (fmsave, version 0.12.5) that only fully supports one FM27 game version, 27.0.0. Saves from other FM27 updates may only be partly readable.
- In this save, both ways FMCC finds your club broke: reading "the club you manage" and reading the full club list.
- FMCC's last fallback is to match a club name. The Club box now starts empty, so that fallback had no name to match, and setup stopped with the error.

## Core features and experience
1. **More ways to find your club.** Before giving up, FMCC tries these in order:
   - the club you manage, read directly from the save;
   - the club where the save's human manager (you) is employed;
   - the club name in the save file's name, such as "Wrexham" in "Chris Horwedel - Wrexham 27", matched against the clubs in the save;
   - a name you've typed in the Club box.
2. **Pick your club from a list.** If none of those work, the check doesn't stop with an error. You get a searchable list of clubs read from the save, and choosing one finishes the check.
   - The list shows likely matches first, such as clubs whose name appears in the save file's name.
   - Choosing a club fills in the Club and Career name boxes (for example "Wrexham 27"), the same way the automatic check does. Names you typed yourself are kept.
3. **Your choice is remembered.** That career keeps using the club you picked on every later save read, so you aren't asked again each time.
4. **A plainer error message.** If even the club list can't be read, the message says what happened in plain words and suggests what to try, such as making sure FM is up to date or picking a different save. There's no copy-report button, as you chose.

## User flow
1. Scan the PC, then choose the Wrexham 27 save. FMCC checks it automatically.
2. If FMCC finds the club itself: "Read OK: Wrexham…" appears and the names fill in, as they do now.
3. If not: "Pick your club" appears with a search box and the club list. You choose Wrexham, the check passes, and the names fill in.
4. Continue through setup as normal. Later save reads use Wrexham without asking.

## UI/UX feel
- The club picker appears in place under the save list, in the same dark setup card, styles and spacing used elsewhere in setup.
- On mobile it's a full-width list that scrolls, with large tap targets.
- No new pages or pop-ups.

## Implementation phases
- **Phase 1 (built now):** the extra ways to find your club, the club picker in setup, remembering the chosen club for that career, and the plainer error message.
- **Phase 2:** a "Change club" option in Settings, using the same club picker, for an existing career whose club was detected wrongly.
- **Phase 3:** a note in Settings showing which FM version a save comes from and whether the save reader fully supports it.

## Assumptions
- Only the club detection step changes. Reading of players, stats and history stays the same, and parts the reader can't handle keep being skipped quietly, as now.
- The save reader stays at version 0.12.5, the newest release (14 Nov 2026). No newer version exists to update to.
- The club list includes every club the save reader can read from the save. It's sorted with likely matches first, then by name.
- If the human manager's employer is the only reliable clue, FMCC uses it without asking.
- Your Wrexham save stays on your PC: it's never uploaded or sent anywhere.
- The fix can only be checked in the browser preview with sample saves. Whether it reads the real Wrexham save is confirmed only once you run the new Windows build on your PC.
- Applies to setup and to "Run setup again" in Settings.
