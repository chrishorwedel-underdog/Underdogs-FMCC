# FMCC: guided tour, ideas from FMST26, FM Dossier and fmOS, and those apps in Updates

FMCC adds a click-through tour for new users and rebuilds the best ideas from three other Football Manager apps inside Scout Players and Squad.
The apps themselves can be launched from FMCC when installed, and their new versions are tracked in Settings → Updates.

## Who it's for
One manager running an FM26 or FM27 career next to the game. They want a deeper Moneyball engine (their own formulas and sharper filters), to know which signings fit their tactic, and a cheaper like-for-like replacement when a player leaves.

## Core features and experience

### 1. Guided tour
- Starts automatically the first time FMCC opens after setup.
- Steps through every sidebar page in order (Home, Dynamic Potential, Breakout Player, Scout Players, Monthly Reports, Moneyball, Squad, Development, Elite Training, Matches, Player & Teams Editor), then Project Safety, Game changes and the Director of Football button.
- On each step:
  - FMCC opens that page;
  - the menu item is highlighted;
  - a small card says in two or three lines what the page does, with Back, Next and Skip tour.
- It finishes on Home with "You're ready".
- It can be replayed at any time from a "Take the tour" button in Settings and the help button in the top bar.
- It uses the same wording as the "What this page does" cards, so the two always agree.

### 2. Formula builder (the FMST26 idea)
- In Scout Players → a new **Formulas** tab, you write your own stat. For example: `(npxg + xa) / 2`, `tkw + intc * 0.8`, `npg - npxg`.
- **What a formula can use:**
  - every stat FMCC already has, plus minutes, age, value, wage, grade and computed stats;
  - + − × ÷, brackets, min, max, abs and if.
- **Chaining:** a formula can use another of your formulas.
- **Where formulas appear:**
  - as columns in the Players table;
  - as X/Y on the Scatter chart;
  - in filters and in the Compare tab.
- **Percentiles:** each formula gets a percentile rank against a pool you pick:
  - the whole save;
  - the same position;
  - the same league;
  - your current filter.
- **Checks and history:**
  - a live preview shows the result for 5 sample players while you type;
  - errors (unknown stat, division by zero, a formula that uses itself) are shown in plain words;
  - every saved formula is kept as a new version, never overwritten.
- **Limit:** up to 30 formulas.

### 3. Advanced filters and percentile filters (FMST26)
- **A filter builder:**
  - conditions joined with AND / OR;
  - groups inside groups.
- **Kinds of conditions:**
  - **Value:** for example, "minutes ≥ 900".
  - **Stat against stat:** for example, "npg < npxg" (finishing below expectation).
  - **Percentile:** for example, "top 10% of central midfielders for progressive passes".
- **Percentile settings:** you pick the pool (whole save, same position or same league). Every stat cell can show a green-to-red heat colour by percentile.
- **Saving:** filters save with the existing saved searches and work in every view (Full, Fair play, Moneyball).
- **Fair play:** filters only use what your scouts know, so nothing hidden can be found by filtering.

### 4. Quadrant chart and replacement search (fmOS)
- **Quadrant chart** (Deals & Offers → Quadrant):
  - performance is on one axis and total cost (fee + wages over the contract) on the other;
  - for performance you pick the global grade, a computed stat or one of your formulas;
  - the four zones are labelled Hidden gems, Stars, Overpriced and Avoid;
  - you click any dot to open the profile.
- **Replacement search:**
  - a "Find a replacement" button sits on every profile;
  - it lists players with the same playing style (the workbook's similarity engine), filtered by your caps (max fee, max wage, max age);
  - results are sorted by similarity and cheapness, with the saving shown against the player being replaced;
  - from My Club you can do the same for any of your own players who are leaving or ageing.

### 5. Tactic fit and squad gaps (FM Dossier)
- **Importing:** in Squad → a new **Tactic fit** tab, you import an FM tactic file (.fmf) or pick one of FMCC's formations. FMCC reads the formation, positions and roles from the file.
- **Fit:** every player in your squad is rated for every slot of that tactic:
  - for both the in-possession and out-of-possession role where the file has them;
  - using the same role ratings as Squad.
- **Squad gaps:** each slot gets a rating for the starter, the backup and depth. The weakest slots are listed first.
- **Fixing a gap:** clicking a gap opens Scout Players with a ready-made search for that role, within reach of your club's budget and reputation.
- **History:** every imported tactic is kept, so you can switch between tactics and compare them.

### 6. The three apps inside FMCC
- **Connections** gets a card for each app:
  - **FMST26 and FM Dossier** (Windows programs): FMCC looks for them on the PC, shows Installed / Not installed and a version, and offers an **Open** button. If either isn't installed, a **Get it** link goes to its official page.
  - **fmOS** (a website): it opens in your browser.
- **Settings → Updates** lists FMST26, FM Dossier and fmOS next to ScoutSheet, BepInEx and FMMatchLens. For each, FMCC:
  - checks their official page or changelog once a week (and when you press Check);
  - shows the installed and latest version and what changed, with a link to download.
- **No automatic installs for these three:** their files aren't FMCC's to redistribute, so FMCC never downloads or installs them. You update them yourself; FMCC tells you when.
- Credits in Settings name all three as feature inspiration.

### 7. A cleaner, symmetrical Home page
- **Today:** the six module cards sit on the left, with a narrower column on the right for Needs your attention and Next match. This leaves the page lopsided and empty at the edges.
- **New layout:** the page fills the screen width, and everything is balanced on one centre line.
  - **Top:** a full-width welcome band, with the greeting and today's status on the left and the backup and next-match chips on the right, aligned to the same height.
  - **Middle:** the six module cards in an even 3 × 2 grid. All cards are the same size, with their numbers lined up.
  - **Bottom:** two equal halves side by side, Needs your attention and Next match, at the same height.
- **Bigger throughout:** text, numbers, icons, card padding and spacing all go up about one size, so the page reads comfortably on a large monitor without feeling empty.
- **Smaller screens:** the grid steps down to 2 columns, then 1, and the two bottom halves stack.
- **Nothing removed:** the same information and links stay; only the arrangement and sizes change.

## User flow
1. A new user finishes setup and lands on the new, balanced Home page; the tour starts. They click Next through each page, or skip it and replay it later from Settings.
2. In Scout Players → Formulas, they write `npg - npxg`, check the preview and save it. It appears as a column and on the Scatter chart.
3. In Players, they build a filter: central midfielders, top 10% for progressive passes, AND npg below npxg, AND age ≤ 24. Then they save it.
4. In Squad → Tactic fit, they import their .fmf tactic. The left-back slot shows as the biggest gap, so they click it and get a search for that role within budget.
5. They open a target's profile, press Find a replacement on their ageing striker, and check the Quadrant chart for hidden gems.
6. Settings → Updates shows that FM Dossier has a new version; they click through to download it.

## UI/UX feel
The same dark FMCC look. The tour is a soft spotlight on the menu item, with a compact card beside it and a step counter (4 of 14). The formula editor is a monospace box with stat suggestions as you type and a live result strip underneath. The filter builder uses nested rounded groups with AND/OR pills. The quadrant chart has four faintly tinted zones with their labels in the corners.

## Implementation phases
**Phase 1 (built now)**
- The cleaner, symmetrical and larger Home page.
- The guided tour (first launch, replayable).
- The formula builder with chaining, percentiles and versions.
- Advanced and percentile filters, and percentile heat colours.
- The quadrant chart and replacement search.
- Tactic fit and squad gaps from .fmf files.
- The three apps in Connections (detect, Open, Get it) and in Settings → Updates (version checks, no installs).

**Phase 2**
- fmOS-style "price explained": a fee broken into age, potential, position, club reputation, contract and form.
- FM Dossier's Shape Advisor: ranking many formations against your squad.
- Formulas shared as files you can import and export.

**Phase 3**
- Value and form history charts per player across seasons.
- The Director of Football uses your formulas and tactic gaps when it answers.

## Assumptions
- **No code from the three apps:** none of their code is used, because their licences aren't confirmed. FMST26 and FM Dossier are closed Windows programs, and fmOS is a website. "Incorporate" therefore means:
  - their ideas are rebuilt inside FMCC;
  - FMCC launches them when they're installed;
  - FMCC tracks their versions.
- **Update checks:** these read each app's public page or changelog. If a page changes its layout, that app shows "Couldn't check" rather than a wrong version.
- **Finding the installed apps:** FMCC looks in their usual install folders. If one is installed somewhere else, you can point FMCC at it once.
- **Tactic files:** reading .fmf files depends on FM's tactic file format. The format will be checked on a real FM26/FM27 file. Until then, picking one of FMCC's formations does the same job, and the browser preview uses a SAMPLE tactic.
- **Live game reading:** FMST26 and FM Dossier read the game live; FMCC keeps reading your saves as it does now. Live reading isn't part of this plan.
- **Total cost:** the quadrant chart uses value plus wage × contract months left. Bonuses aren't in the save, so they're left out.
- **Formula safety:** formulas are calculated by FMCC's own maths parser, never run as code. Up to 30 formulas, each up to 300 characters.
- **Preview data:** match stats and players are SAMPLE data, as they are now.
- **The tour:** it runs once per FMCC install. Replaying it never changes any data.
- **Home sizes:** "a little bigger" is read as about one size up for text and spacing on Home only. Other pages keep their current sizes.
