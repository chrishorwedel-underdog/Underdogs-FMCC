# FMCC Polish Pass: Radar Compare and Friendlier First Use

This pass adds Radar Compare and a set of changes that make FM Command Centre easier to pick up and more consistent to look at.
Nothing is removed. Ease of use comes first, so new users get the full program with clearer guidance and calmer screens.

## Status of today's earlier plan
All three phases of today's quality-of-life plan are built. Some items are still open:
- Player & Teams Editor and Punish a Club changes still wait in Game changes. Fixed in Phase 1.
- In Squad and Development rules, "who it affects" counts every player the setting covers, not just the players who would actually change. Fixed in Phase 3.
- On phones, the top bar wraps onto several lines. Fixed in Phase 1.
- Lineups are saved in FMCC only, because the game editor can't write FM's team selection. This stays as it is.
- Nothing has been checked against a real FM save on Windows. This needs a Windows PC with FM running.

## Who it's for
- New FMCC users opening the program for the first time.
- Regular users who want screens that look and behave the same everywhere.

## Core features and experience

### Radar Compare
- Overlays players' radars in one chart, each player in a different colour, with a legend.
- Three radar choices:
  - **Role fit:** the stats that matter for a chosen role.
  - **Phases of play:** finishing, creating, carrying and defending.
  - **Attributes by area.**
- Pick a role to get a plain verdict, such as "Player A fits this role better: stronger in 4 of 6 areas", with the biggest gaps named.
- **Where it's available:**
  - a "Compare with…" button on every player profile in Scout Players and Squad, which opens a player search
  - the Compare tool in Scout Players
- Works for your own players and players at other clubs. No real CA/PA is used or shown.
- **Phase 3 additions:**
  - compare up to four players at once
  - a comparison card you can print or save as an image

### Automatic applying for every module
- Player & Teams Editor edits and Punish a Club penalties go into the save straight away. The bell lists what changed.
- The "Review changes before applying" switch in Features also covers these two modules.

### First-use guidance (regular mode, no starter mode)
- The walkthrough tour and the "What this page does" guides stay. The tour can be restarted from Settings.
- "What this page does" guides start collapsed after your first visit to each page.
- Short tips appear the first time a screen is opened. Each tip can be dismissed and stays gone.
- Where a term is jargon, the visible label uses plain words and the short stat name appears on hover.
- A page that needs a save which hasn't been read yet says "Read a save first" and has a button to read one.

### Look and polish
- **Phone top bar:** the club name and main buttons fit on one line. Less-used buttons move into a "More" menu.
- **Contract countdowns:** grouped into one "Contracts ending (N)" chip that opens the list, instead of one chip per player.
- **Page headers:** every page uses the same layout of title, one-line purpose and then tabs, with at most one main button.
- **Tables:** the same row height, number alignment, hover state and pinned player column across the app.
- **Loading:** shaped placeholders replace "Loading…" text.
- **Ongoing cleanup:** spacing, wording, button labels and clutter are tidied across all pages as the work goes. The aim is fewer things on first view, with advanced options one click away.

### Exact impact counts (Phase 3)
- "Check who it affects" in Squad and Development rules counts exactly the players whose result would change, as the other modules already do.

## User flow
1. Open any player and press "Compare with…". Pick a second player and a role, then read the overlaid radar and the verdict. In Phase 3, add up to two more players and save or print the comparison card.
2. Make an edit in Player & Teams Editor or set a penalty in Punish a Club. It applies straight away and the bell lists it.
3. A new user takes the tour and sees a one-time tip on each new screen. Every page has the same layout, and a "Read a save first" message appears where it's needed.

## UI/UX feel
- Calm and consistent: the same header, table, loading and empty-state patterns on every page.
- Radars use Data Hub styling, with each player in a distinct colour that stays readable in high contrast.
- Current themes, kit accent, text sizes and accessibility settings are unchanged.

## Implementation phases
All three phases are built now, as one project, in order:
- **Phase 1:**
  - Radar Compare for two players, from profiles and from the Compare tool
  - automatic applying for Player & Teams Editor and Punish a Club
  - the phone top bar fix
  - "What this page does" guides collapsed by default after the first visit
  - grouped contract countdowns
- **Phase 2:**
  - one-time screen tips
  - "Read a save first" messages
  - the plain-label pass
  - consistent page headers and table styling
  - loading placeholders
  - the cleanup pass across all pages
- **Phase 3:**
  - exact "who it affects" counts in Squad and Development rules
  - Radar Compare for up to four players
  - the printable comparison card, also saved as an image

## Assumptions
- The role verdict counts the radar areas where each player scores higher and names the biggest differences. It is guidance, not a guarantee.
- Comparisons follow the current scouting view (Full, Fair play or Moneyball). In Fair play, a range of attribute values is plotted at its middle.
- If a player doesn't have enough minutes, the stat-based radars show the matching empty message instead of a misleading shape.
- With four players, only the first two are compared in the verdict. The others are shown on the chart and in a table of the gaps.
- The comparison card is saved as an image on this computer. No sharing service is used.
- Editor and Punish a Club changes need FMCC for Windows with the game connected. In browser or sample mode they only change sample data, but they still send a notification.
- Tips and collapsed guides are remembered on this computer and apply to every career.
- The cleanup pass changes layout, wording and spacing only. Features and data stay as they are.
