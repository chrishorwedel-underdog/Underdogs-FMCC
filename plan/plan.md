# FMCC: ScoutSheet built in, FMDataLab-style analytics, league strength, and graphics tools

FMCC takes in ScoutSheet's whole scouting app and rebuilds FMDataLab's analytics on top. The result is one deep scouting and Moneyball lab that runs from your own save.
The Player & Teams Editor adds kits, bulk import of a whole folder of pictures, and a full check of every graphics pack.

## Who it's for
One manager running an FM26 or FM27 career next to the game. They want to find undervalued players, judge them on real match output across leagues of different strength, and keep their faces, logos and kits tidy.

## Core features and experience

### 1. ScoutSheet, built in completely (Scout Players)
ScoutSheet's code is free to reuse (MIT licence) and is credited in Settings. Everything it offers, inside FMCC:
- **Three views, switched with one click:**
  - **Full:** everything, including CA, PA, hidden attributes, personality and a written scouting report;
  - **Fair play:** only what your scouts would show you in the game;
  - **Moneyball:** match stats and price only, with attributes switched off.
- **Search:**
  - FM-style search across every player in the save, men and women, with a switch between them;
  - ready-made searches (for example wonderkids and expiring contracts) and saved searches of your own;
  - caps on value and wage.
- **Player profile:**
  - positions on a pitch, phase scores (finishing, creating, carrying, defending) and best role;
  - peer percentiles, a pizza chart, similar players, contract, price and wage;
  - a confidence word: Low, Medium or High, based on minutes played;
  - contract warnings in orange (12 months left) and red (6 months left).
- **My Club:** each position in your squad is rated, weakest first. Clicking one lists the players who would improve it, with their cost.
- **Fair price, Deal Finder and Offers:**
  - each player gets a fair price from similar players in your save;
  - Deal Finder lists the players selling well under it;
  - Offers checks a bid against fair price before you accept or send it.
- **Compare, shortlist and export:** compare players side by side, add them to the FMCC shortlist, and export any list to a CSV file.
- **Currency and wages:** choose £, € or $, and wages per week, month or year.
- **Left out on purpose:**
  - ScoutSheet's usage statistics, which send data to its website;
  - its own self-updater, because FMCC handles updates (below);
  - it never writes to the save, and that stays true.

### 2. ScoutSheet in the automatic updates list
- ScoutSheet appears in Settings → Updates next to BepInEx and FMMatchLens. It shows its version, when FMCC last checked and what changed.
- When ScoutSheet publishes a new release, FMCC:
  - downloads it and checks the file's published checksum;
  - runs its own compatibility checks: the new version must load your current save's players and give the same results on a set of test players;
  - **if the checks pass,** installs it automatically and tells you what changed;
  - **if they fail,** stays on the current version and shows "Update held back" with the reason.
- The previous version is always kept, and "Go back to the previous version" is one click.
- You can switch automatic updates off and check by hand instead.

### 3. Everything that can be taken from FMDataLab (rebuilt, as it has no source code)
- **Stats table:** every stat the save holds (FMDataLab shows 169 columns), as season totals, per 90, and with possession and league adjustments.
- **Percentiles** against players in the same position.
- **Computed stats:** archetype scores built from weighted percentiles, for example Ball-Playing Defender, Box Crasher or Pressing Forward.
  - Each weight goes from 0 to 10, and a warning shows when a weight differs from the default.
  - You can make up to 6 custom computed stats from 3 to 12 stats each.
- **Actions per 90:** weighted sums of raw per-90 stats, for example defensive actions, progressive actions and box involvement.
- **Possession adjustment:**
  - attacking stats are multiplied by your possession ÷ his club's possession;
  - defensive stats are multiplied by his club's possession ÷ your possession;
  - percentage stats are not adjusted;
  - each club's possession is entered in a table, and a marker on each adjusted number shows the multiplier used;
  - a "show raw" toggle shows the numbers before and after adjustment.
- **League multipliers:** your Opta ranking (section 4).
- **Scatter chart:** any two stats on the X and Y axes, with average lines, hovering and click-to-open profiles.
- **Player details compare chart:** each computed stat broken down into its parts, for up to 4 players.
- **Role scores:** an attribute-based suitability for every role, sortable across the whole save.
- **Best XI:** tries every lineup of eligible players for your formation and roles and picks the highest-scoring one. This upgrades the existing Best XI in Squad.
- **Import FM's HTML exports:** an alternative to reading the save, for when the save can't be read. You can import several files at once.
- **Minutes rule:** percentiles and scores need at least 400 minutes, and a fair price needs at least 900. Below that, the player shows "Not enough minutes".

### 4. League strength (Scout Players → Leagues)
- **Your ranking:** your 208-league Opta list from 6 November 2026 comes built in.
  - Formula: multiplier = (Opta rating ÷ 92.1)^1.5. The Premier League is 1.000.
  - Every multiplier can be edited, and edits are kept in the career's history.
- **Matching leagues:** each league in the save is matched to a league on the list automatically, by country and name. Matches FMCC isn't sure about are shown for you to confirm or change.
- **Leagues not on the list:** placed by their reputation in the save.
  - FMCC takes the two leagues on the list whose save reputation is nearest above and below.
  - It fills in an Opta rating between theirs and applies the formula.
  - These leagues are marked "Estimated from reputation".
- **Recalculate from reputations:**
  - re-places every estimated league using the save's current reputations;
  - it shows old and new values before saving;
  - your hand edits stay unless you tick "also reset my edits".
- **Duplicate entries in the list:** Kenyan Premier League (3×); Faroe Islands Premier League, Congolese Ligue 1, Jordanian Pro League and Hong Kong Premier League (2× each); and the Grenadian rows (3 near-identical). FMCC uses the highest-ranked entry for each and lists the rest for you to review.

### 5. Graphics tools (Player & Teams Editor)
- **Kits:** home, away and third kit pictures for any club. Upload them, or create them with ChatGPT from the club colours with a preview first.
- **Pack browser:** a picture grid for any graphics pack, showing each image with the player or club it belongs to.
- **Bulk import a folder or zip:**
  - Files are matched by the ID in their name: a player ID or the `r-` form for faces, and a club ID for logos and kits. Kit files also need a word such as "home" in the name.
  - Everything is staged first: you see what will be added, what will be replaced, and which IDs aren't in the save. Nothing is written until you press "Write to FM", and each item can be undone afterwards.
- **Check my graphics packs:** scans every pack (NG_Regens, logo packs, kit packs and FMCC's own) and lists:
  - missing or broken pictures;
  - IDs set by more than one pack, and which pack's picture FM is likely to show;
  - IDs that aren't in the current save.
  - It only reports. It never edits another pack's files.

## User flow
1. Open Scout Players. ScoutSheet's views are there, and the save is read automatically as it is now.
2. Under Leagues, confirm the unsure league matches and optionally press Recalculate. Enter possession for your club and the rivals you care about.
3. Pick Full, Fair play or Moneyball. Search, sort the stats table, build or tune computed stats, and use the scatter chart to spot outliers.
4. Open a profile, compare up to 4 players, check the fair price, use Deal Finder or Offers, and add targets to the shortlist.
5. In Squad, run Best XI for your formation.
6. In the Player & Teams Editor, add kits, bulk import pictures, then run "Check my graphics packs".
7. Settings → Updates shows ScoutSheet's version and installs new ones by itself after the checks pass.

## UI/UX feel
The same dark FMCC look. The scouting screens are dense and analytical: a sortable table with percentile colour bars, a pizza chart and profile panel, and a scatter chart with average lines. Small markers show where an adjustment was applied. The Full, Fair play and Moneyball switch sits at the top so it is always clear what information is showing.

## Implementation phases
**Phase 1 (built now)**
- All of ScoutSheet inside Scout Players, plus ScoutSheet in the automatic updates list.
- All the FMDataLab-style analytics, including Role scores, the upgraded Best XI and HTML import.
- The league-strength table with your ranking, matching, reputation placement and Recalculate.
- Kits, the pack browser, staged bulk import and the graphics pack check.

**Phase 2**
- Tracking stats across several seasons in the same career, which FM itself deletes.
- Possession figures taken automatically from FMMatchLens matches.
- Tactical archetype searches with weights for in possession and out of possession.

**Phase 3**
- Kit design templates and bulk ChatGPT creation.
- Scouting reports written by your Director of Football from the Moneyball numbers.

## Assumptions
- **Save support:** ScoutSheet officially supports FM26 saves. FM27 support depends on the shared save reader and will be marked "Unverified" until it is shown to work on a real FM27 save. In the browser preview, players and stats are SAMPLE data.
- **Possession:** the save doesn't hold club possession, so you enter it. Until then, nothing is possession-adjusted.
- **FMDataLab:** none of its code is used. Its features and published possession method are rebuilt.
- **FM Pack Manager:** left out completely, as you chose. FMCC's own graphics tools cover its features.
- **ScoutSheet updates:** an update that changes how ScoutSheet works so much that the checks fail is held back, never forced. It is then reported in Updates.
- **Opta list:** built in exactly as you gave it. Only the matching to FM's league names is added.
- **Kit file layout:** kits use FM's usual `club/<ID>/kits/home` style layout in FMCC's own config file. This will be checked on your PC like the other graphics features.
- **Bulk import limit:** up to 5,000 pictures and 500 MB per import, each picture up to 5 MB.
- **History:** every league multiplier edit, possession value, computed-stat weight change and imported picture is kept as a new version, never overwritten.
