# Backup Save Reader for FM27 Saves

FMCC reads every save with two free save readers instead of one. It keeps the better result, so saves from FM27 updates the main reader doesn't fully support still load in setup and on every later save read.

## Why not NG_Regens
- NG_Regens Manager is closed source, and its save reader only collects player IDs and nationalities to assign faces. FMCC can't reuse it.
- What NG_Regens does show is that FM27 saves from different game updates can be read reliably.
- fm-open-scout is a free, open (MIT) save reader. It reads FM24, FM26 and FM27 saves, including FM27 updates it hasn't seen before, by working out the save's layout itself. It reads every player's club, contract, attributes and details.
- fmsave (version 0.12.5) stays as the main reader. It fully supports only one FM27 game version, 27.0.0.

## Who it's for
Anyone using the FMCC Windows program with an FM27 save that the main reader only partly reads, starting with the "Chris Horwedel - Wrexham 27" career.

## Core features and experience
1. **Two readers on every save read.** Setup's save check and every later save read run both readers on the same save, one after the other.
2. **Better result kept.** FMCC compares what each reader got:
   - whether it found your club;
   - how many of your players it found;
   - how many parts of the save it had to skip.
   It then builds one result from both.
3. **Main reader wins on conflicts.** If both readers have a value and they differ, such as a player's club or contract date, FMCC uses the main reader's value. The backup reader only fills gaps:
   - your club;
   - missing players;
   - missing details such as positions, contracts or club for a player.
4. **Club detection uses both.** The backup reader's clubs and players feed into the club-finding steps already built (your managed club, your manager's employer, the club name in the save file name, the typed name). If both readers fail, the "Pick your club" list combines clubs from both.
5. **Quiet unless something fails.** Setup and Settings don't show version notes when a read works. If a read fails or parts are skipped, the message says in plain words:
   - which FM version the save comes from;
   - which reader had trouble and what was skipped;
   - what to try next.
6. **CA/PA stays private.** The backup reader also reads ability figures. FMCC uses them only for its own internal calculations and never shows them anywhere, the same rule as now.

## User flow
1. Scan the PC and choose the Wrexham 27 save. FMCC checks it with both readers automatically.
2. "Read OK: Wrexham…" appears and the names fill in. If the club still can't be found, the "Pick your club" list appears as now.
3. Continue through setup as normal.
4. Later save reads use both readers too. Home, Squad and the other pages work from the combined result.
5. If a read has trouble, the error or notice names the FM version, the reader that struggled and what to try.

## UI/UX feel
- No new screens, buttons or settings. The only visible changes are a successful read where the main reader used to fail, and clearer wording when something goes wrong.
- While a save is being checked, the setup status says "Reading the save with both readers… this can take a minute or two."

## Implementation phases
- **Phase 1 (built now):** both readers on every save read, combining results with the main reader winning on conflicts, club detection and the club list using both, plain-words failure messages naming the FM version and the reader, and the backup reader bundled in the Windows installer.
- **Phase 2:** a "Change club" option in Settings, using the same club picker, for a career whose club was detected wrongly.
- **Phase 3:** a "Save reader report" button that builds a summary of which readers read which parts of a save, with no player names, ready to send to the reader authors.

## Assumptions
- fm-open-scout's Windows save reader is bundled inside the FMCC installer, so nothing downloads on first use and the save never leaves the PC.
- Running both readers makes each save read slower, roughly twice as long.
- If the backup reader fails or isn't present, FMCC carries on with the main reader alone, exactly as it does today.
- fm-open-scout is a small, new project with few users. Its results are treated as "unconfirmed", the same as unverified main-reader fields.
- The backup reader covers players, clubs and contracts. Stats, league tables, history, finances and tactics still come only from the main reader. If the main reader can't read those, they stay empty rather than guessed.
- Both readers' licences (MIT) allow bundling. fm-open-scout is added to the Credits list and the Updates card.
- In the browser preview, the backup reader is simulated with sample data. Whether it reads the real Wrexham save is only known once the new Windows build runs on your PC.
