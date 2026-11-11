# The Best of FM Dossier, fmOS and FMST26, Built Into FMCC

FMCC gets its own versions of the most useful screens from FM Dossier, fmOS and FMST26. Nothing extra has to be downloaded, installed or updated.
They work from the save FMCC already reads, are ready as soon as FMCC opens, and update together with FMCC.

## Who it's for
- FMCC users who currently run FM Dossier, fmOS or FMST26 alongside FMCC, and want one program instead of four.
- Data-minded managers who scout with stats, per-90 numbers and role fit rather than star ratings.

## Why rebuild instead of bundle
- **The three programs can't be bundled:**
  - All three are closed programs owned by their makers.
  - FMST26 may only be downloaded from FMScout.
  - FM Dossier needs its own licence key.
- **FMCC builds its own versions instead:** its own screens and calculations, inspired by what those programs do. No code, data, names or artwork are copied from them, and they are never mentioned as part of FMCC.

## Core features and experience

### 1. Stats Table (inside Scout Players), inspired by FMST26
- **The table:** every loaded player in one sortable table with 100+ columns across General, Attacking, Passing, Defending, Goalkeeping and Physical. It includes per-90 figures (goals, assists, xG, xA, shots, tackles, pressures, progressive passes) and attributes.
- **Percentile shading:** each cell is shaded green to red by where the player ranks.
- **"Compare against":** you choose the group a player is ranked against: the whole save, one league, one position, or your current filter.
- **Advanced filters:** combine conditions with AND / OR, for example "Finishing 15+ AND age under 23 AND league = Eredivisie". You can also filter on percentiles, such as "top 10% for progressive passes among midfielders".
- **Views:** save and reload column views and filter sets by name.
- **Export:** send what's on screen to a spreadsheet (CSV).
- **Quick filters:** position, club, league, minimum minutes, gender, and "leave out my club".

### 2. Role Fit for every role, inspired by FM Dossier
- **What it rates:** every player is rated for every FM role at every position he can play, with the ball and without it, as a fit percentage.
- **Your weightings:** you can change any role's weighting, for example making Pace count more for a Pressing Forward.
- **Where it shows:** role fit appears in the Stats Table, in Player Dossiers and as a filter ("best Inside Forwards under 21").

### 3. Player Dossier, inspired by all three
- **One screen per player:**
  - Attributes in colour bands.
  - Positions on a pitch.
  - Top role fits, with and without the ball.
  - Contract: wage, end date, release clause and loan details.
  - This season's stats and form.
- **Estimated value with reasons:** FMCC's own estimate, built from six factors shown as + / − %: age, position, club, reputation, contract length and form.
- **Value over time:** a chart built from every save FMCC has read.
- **Similar players:** one click finds a similar player, a cheaper one (up to 60% of the price) or a younger one.
- **Compare:** put up to 5 players side by side with overlaid radars, per-90 stats and role fit.

### 4. Transfer Market (new menu page), inspired by fmOS
- **Ready-made lists:** contracts ending within a year, free agents, lowest release clauses, best under-21s, and loan-listed players.
- **What changed since your last save:** transfers, loans, new contracts and value changes, for the world, your league, your club or your watch list.
- **Rankings:** by estimated value, for the world, a league, a club, a country, a position or an age group.
- **Club and league pages:** squad value by position, average age, number of foreign players, and clubs ranked by value.

### 5. Club Analysis (new menu page), inspired by FM Dossier
- **"What to do first":** a ranked list for your club, such as "No cover at left-back" or "Two starters' contracts end this season". Each item shows the evidence behind it and links straight to a filtered search.
- **Where to strengthen:** your weakest positions, judged against your save's own tactics.
- **Signing ideas:** three groups, Upgrade, Affordable and Successor. Each shows why it was picked and its estimated price and wage.

### 6. Always on, always current
- **Always ready:** the new screens are ready the moment FMCC opens and refresh after every save read, with no extra program to start.
- **One update:** they update with FMCC's normal one-click update.
- **Features page:** Transfer Market and Club Analysis get their own on/off switches there, like every other feature.

### 7. Downloads page: one "Download & install" button per pack
- **One button:** each pack (NG_Regens, Real Name Fix, logo pack, kit pack) gets a single **Download & install** button, replacing "Get it" and "Start installer" / "Install from Downloads".
- **Packs FMCC can fetch itself (NG_Regens Manager):** FMCC downloads the installer from the official site, shows progress, then starts it. If several files are offered, it picks the one for Windows.
- **Packs behind a sign-in (sortitoutsi: Real Name Fix, logos, kits):**
  - sortitoutsi only lets signed-in members download, so FMCC can't fetch these by itself.
  - One press opens the official page. FMCC then watches your Downloads folder, and the moment the file lands it installs it automatically, with the usual backups and no second button.
  - While it waits, the button shows "Waiting for the download…" with a Cancel link, and it stops waiting after 30 minutes.
- **Already installed:** the button changes to **Update** when a newer version is posted, and to **Installed ✓** when you're up to date.
- **Real Name Fix:** it still asks one confirmation before replacing the game's name folders, and it still asks you to close FM first.
- **FM Dossier, fmOS and FMST26:** they're removed from the Downloads page, because their features are now built into FMCC.

## User flow
1. The user opens FMCC and reads a save as usual.
2. In Scout Players, the new Stats Table tab shows every loaded player. The user filters for under-23 ball-playing defenders in the top 20% for progressive passes.
3. The user opens a player's dossier and sees his role fit, estimated value with its reasons, and similar cheaper options. They add him to the shortlist.
4. In Transfer Market, the user checks which players' contracts end this year and what changed since the last save.
5. On Club Analysis, the user reads the ranked "what to do first" list and follows a link to a ready-made search.

## UI/UX feel
- **Look:** the same dark FMCC look. The Stats Table is dense, like a spreadsheet, with a sticky header and sticky name column, and percentile shading that's easy to read at a glance.
- **Dossiers:** open in a side panel, so the table stays in place behind them.
- **Club Analysis:** calm and clear, with short, plain sentences and the evidence one click away.

## Implementation phases
- **Phase 1 (MVP, built now):**
  - The Stats Table with per-90 columns, percentile shading, "Compare against", AND / OR and percentile filters, saved views and CSV export
  - Role Fit for every role, with and without the ball, with editable weightings
  - The Player Dossier: estimated value with reasons, value over time, similar / cheaper / younger, compare up to 5 players
  - The Transfer Market page: ready-made lists, "what changed since your last save" and value rankings
  - The Club Analysis page: "what to do first" list and signing ideas
  - Feature switches for the two new pages
  - The single "Download & install" button on the Downloads page, with FM Dossier, fmOS and FMST26 removed from it
- **Phase 2:**
  - Tactic import (.fmf) with a fit rating for each squad slot
  - "Try in XI" shadow signings on the Squad page
  - National team builder from every eligible player
  - "Upgrade your backroom" staff search
  - Shortlists sent to and from FM
  - Scout mode: attributes shown as ranges based on what your scouts know
- **Phase 3:**
  - Custom stats built from a formula
  - Scatter charts (any stat against any other)
  - "Will he join?" chance with reasons
  - Injury history with a risk level
  - Club and competition profiles with finances and facilities

## Assumptions
- **No Current or Potential Ability, anywhere:** real CA/PA are never shown, used as filters or used as columns, as already agreed. Values and role fit are built from attributes, stats, age, contract and reputation.
- **Save reads only:** data comes from FMCC's normal save reads, not from the game's live memory. There's no second-by-second "live" mode.
- **Unconfirmed on a real save:** how much stats and contract detail a real save gives depends on what FMCC's save reader can see. Real-save coverage stays unconfirmed until it's tested on a PC; in the preview everything runs on the SAMPLE save.
- **Left out:**
  - fmOS Arena, the online ranking: it needs online servers and other players.
  - Skins and adboards: they change game files.
  - Faces: FMCC already has them.
- **Estimated values are FMCC's own:** FMCC works them out itself, not with the formula of any of the three programs or of any outside website.
- **No code or data from the three programs:** none of it is used or bundled, and none of them is named inside FMCC.
- **Menu placement:** only two new menu pages, Transfer Market and Club Analysis. The Stats Table and Role Fit live inside Scout Players, and dossiers open from anywhere a player's name appears.
- **Existing Moneyball page:** it stays as it is and gains a link to compare players in the new dossier view.
- **Downloads, no sortitoutsi sign-in:** FMCC never asks for or stores your sortitoutsi sign-in. You download those packs on their site while signed in as normal, and FMCC takes over from there.
- **Downloads waiting time:** the 30-minute wait for a download is a default.
- **Downloads in the preview:** fetching and installing packs works only in the Windows program. In the browser preview, the button uses SAMPLE files.
