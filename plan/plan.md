# Dynamic Potential rebuilt to the rulesheet, plus four new themes

Dynamic Potential is rebuilt around the Underdog FM Dynamic Potential Rulesheet (11 November 2026). Each player's hidden PA moves with how they actually play: a winter review and a season-end review, with every value in the rulesheet editable.
Appearance also gets four new colour themes: Light, FM24, FM26 and FM27.

## Who it's for
Football Manager players running Underdog FM careers who want potential to rise and fall fairly with real on-pitch performance. The system must be explainable to anyone, without showing real CA or PA.

## Core features and experience

### A. Dynamic Potential, rebuilt

**Two reviews a season**
- **Winter review**, at the opening of the winter transfer window: a possible early growth advance.
- **Season-end review**, after the final competitive match: the full-season entitlement, settled against any winter award.
- Before the first review, the season's two halves are set and saved, with the winter review date as the dividing point. FMCC suggests the date from the save's calendar, and it can be changed.
- Each player's age is recorded at the start of the season and used for that whole season.

**What counts as evidence**
- **Counted:** league, cup, continental, playoff, and competitive youth or reserve matches.
- **Loans:** senior loan matches count fully, in the competition and role actually played.
- **Substitute appearances:** they count with their real minutes.
- **Unrated appearances:** they add minutes but no rating.
- **Not counted:** friendlies, internationals and training.
- **Several clubs in one period:** matches across clubs and loans are combined, and each appearance is counted once.
- **Weighting:**
  - Senior performances count fully.
  - Youth and reserve performances count at 75%.
  - B teams playing in senior competitions count as senior.
- **Injuries:** the minimum-minutes rules give the injury protection. There are no injury-day deductions.

**Performance Score (0–100)**
- **55% match-rating percentile and 45% role-output percentile.**
- **Who a player is compared with:** players of the same position and role, in a similar-strength competition, at a similar starting or preseason expected level. This expectation is fixed for the season.
- **Comparison group size:** at least 25 comparison players are needed. With fewer, the assessment is marked "needs your review".
- **Role output** uses three metric groups per position (A 40%, B 35%, C 25%), as listed in the rulesheet:

| Position | A (40%) | B (35%) | C (25%) |
|---|---|---|---|
| Goalkeeper | save percentage or goals prevented | cross claims and sweeping, when available | pass completion and distribution |
| Centre-back | aerial win rate and tackle success | interceptions and tackles won | progressive passing |
| Full-back / wing-back | tackle success and defensive actions | progressive passing | chances created |
| Defensive midfielder | possession won and interceptions | pass completion and ball retention | progressive passing |
| Central midfielder | progressive passing | chances created or key passes | possession won and interceptions |
| Attacking midfielder | expected assists or chances created | progressive passing and carrying, where available | non-penalty expected goals |
| Winger / wide forward | non-penalty expected goals | expected assists or chances created | dribbling and carrying, where available |
| Striker | non-penalty expected goals | non-penalty goals against expected goals | expected assists or chances created |

- **How metrics are combined:**
  - Each metric becomes a percentile first.
  - Counting stats are per 90.
  - Success rates are used only where attempts exist.
  - Several metrics in one group are averaged equally.
  - Bad-outcome stats, such as possession lost, are scored in reverse.
- **Splits:** where verified role or competition splits exist, each is scored separately and combined by playing time.

**Missing statistics (never scored as zero)**
- **Substitutes:** predefined stand-ins are used, for example progressive passing for carrying. The same stand-in is used for the comparison group.
- **A whole group missing from the data:** its weight is shared proportionally between the remaining groups. The 55/45 split stays while at least two role groups are usable, so a goalkeeper rated on shot-stopping and distribution stays eligible.
- **A gap for one player only:** the assessment is shown as provisional, and any automatic decline is held until the gap is resolved.
- **Ratings-only growth:** allowed up to +4. Anything larger needs your review and supporting evidence.
- **Ratings-only decline:** never applied automatically. It can only flag a concern.
- **Unknown half-seasons:** if either half's minutes or ratings can't be established, downward changes are held.
- **Zeros:** a verified zero is valid evidence. A percentage with no recorded attempts is treated as unavailable.

**From score to PA change**
- **Base change** (from the unrounded score):

| Performance Score | Base change |
|---|---|
| 97–100 | +12 |
| 95 to below 97 | +11 |
| 93 to below 95 | +10 |
| 90 to below 93 | +9 |
| 88 to below 90 | +8 |
| 86 to below 88 | +7 |
| 83 to below 86 | +6 |
| 80 to below 83 | +5 |
| 75 to below 80 | +4 |
| 70 to below 75 | +3 |
| 65 to below 70 | +2 |
| 30 to below 65 | 0 |
| 25 to below 30 | −1 |
| 20 to below 25 | −2 |
| 15 to below 20 | −3 |
| 10 to below 15 | −4 |
| Below 10 | −5 |

- **Growth tiers:**

| Tier | Base award | Season-end requirement |
|---|---|---|
| Above expectations | +2 to +4 | 1,100 competitive minutes |
| Excellent | +5 to +8 | 1,400 competitive minutes |
| Exceptional | +9 to +12 | 1,800 senior minutes, including 400 senior minutes in each half; senior-only evidence; rating and role percentiles both 85 or higher |

  - A player who misses a tier's requirements is capped at the highest tier they meet. For example, a score of 91 with 1,500 minutes gives +8.
  - Youth evidence can reach Excellent at most.
  - Ordinary growth can come from a strong sample concentrated in one half.
- **Decline** (every requirement must be met):

| Requirement | Ordinary decline (−1 to −3) | Severe decline (−4 to −5) |
|---|---|---|
| Season minutes | 1,300 | 1,800 |
| Minutes in each half | 300 | 600 |
| Season score | below 30 | below 15 |
| Match-rating percentile in each half | below 35 | below 25 |
| Season rating and role percentiles | both below 35 | both below 35 |
| Evidence | reliable minutes and ratings, at least two usable role groups | same |

  - A player who misses the severe requirements but meets the ordinary ones is capped at −3.
  - Players with under 60% senior minutes are capped at −2.
  - Meeting the minutes only opens the assessment. The performance requirements must also be met.
- **Age deduction from growth only:**

| Age at season start | Deduction |
|---|---|
| 25 or younger | 0 |
| 26 | 1 |
| 27 | 2 |
| 28 | 3 |
| 29 | 4 |
| 30 | 5 |
| 31 | 6 |
| 32 | 7 |
| 33 or older | 8 |

  Growth never goes below 0 after the deduction, and age alone never causes a loss.
- **Growth taper**, applied point by point after the age deduction:

| PA while applying | Share of earned growth |
|---|---|
| 165 or below | 100% |
| 166–174 | 75% |
| 175–184 | 50% |
| 185–199 | 25% |
| 200 | 0% |

  - The band is checked again after each whole point, and leftover fractions are dropped.
  - Example: 174 PA with +12 earned gives +6, ending at 180.
- **Decline taper**, applied point by point and rounded toward zero:

| PA while applying | Share of earned loss |
|---|---|
| 135 or higher | 100% |
| 125–134 | 80% |
| 115–124 | 60% |
| 105–114 | 40% |
| 96–104 | 20% |
| 95 or lower | 0% |

  - For a −5 base loss: 140 PA gives −5, 130 gives −4, 120 gives −3, 110 gives −2, 100 gives −1, and 95 or lower gives 0.
- **Limits:**
  - The loss floor is 95 PA, or the player's current CA if higher.
  - PA never exceeds 200.
  - The seasonal maximum is +12 or −5 before tapering.
  - Players already below 95 can still grow, and are protected from a net seasonal loss.

**Winter advance and season settlement**
- **Winter review steps:**
  1. It needs 550 competitive minutes and enough evidence.
  2. A provisional annual growth amount is worked out from the current score. The season's growth-minute requirements are checked at season-end.
  3. The age deduction and growth taper are applied.
  4. Half of the result is awarded, rounded down, up to a maximum of +4.
  5. The amount actually applied is recorded.
- **Youth and Exceptional limits at winter:** youth evidence has a provisional ceiling of +8. Exceptional needs senior evidence and its thresholds.
- **Poor winter form** only creates a monitoring flag. Losses are only decided at season-end.
- **Avoiding a double taper:** the season-end taper starts from current PA minus this season's Dynamic Potential points. Changes from other systems, such as Elite Training, still count.
- **Settlement:** season-end applies the final entitlement minus the winter award. For example, +6 entitlement with +2 at winter gives +4 more, and −2 entitlement with +2 at winter gives −4.
  - Returning winter points needs 1,300 season minutes, 300 in each half, and a reliable final assessment. Otherwise the winter award is kept.
  - Any entitlement below zero must separately pass the decline requirements and the decline taper.

**Applying changes (automatic, as chosen)**
- **Straight into your save:** review results go in as soon as the review runs, through FMCC's usual game-change process (backup first, read back after).
- **These wait for your approval instead:**
  - ratings-only growth above +4
  - assessments marked "needs your review"
  - declines held for missing evidence
- **Safety and repeat runs:**
  - Running a review again, or re-reading a save, never applies the same change twice.
  - Corrections keep the earlier decision on record.
  - Reviews run in batches of up to 500 players, and the rest carry over.

**Review record for every player**
- **What it shows:**
  - the period and qualifying minutes
  - first-half and second-half minutes
  - match-rating and role percentiles
  - metrics used, stand-ins and missing evidence
  - base result and age deduction
  - the effect of tapering
  - winter points already applied
  - the change, with a plain-words reason
- **What it never shows:** real CA or PA. Only the change, and whether a taper or cap reduced it.

**All values editable**
- **Settings panel:** every number in the rulesheet can be changed in one Dynamic Potential settings panel. This covers weights, percentiles, minutes, score bands, tiers, age table, both tapers, winter rules, caps, floors and the batch size. The metric list for each position can also be changed.
- **One set for all careers**, as chosen. It starts from the rulesheet values, with "Reset to rulesheet" for one section or for everything.
- **Validation:** changes are checked before saving, for example that bands don't overlap and that percentages add up to 100.
- **History:** each saved change is kept, so an earlier set can be restored.
- **Reviews keep their settings:** each review records the settings it used. Changing a value later doesn't change past results.

### B. Four new themes
- **Where:** Light, FM24, FM26 and FM27 appear in Appearance next to the existing themes, each with a colour preview. Colours only: fonts, shapes and layouts stay FMCC's.
- **Light:** white background, light grey panels, dark text and FMCC blue.
- **FM24:** navy and slate with FM24's green.
- **FM26:** deep purple with a bright pink-purple accent.
- **FM27:** charcoal with a softer purple. The top bar uses your club's colours from the loaded save, and FM27's own colours when no club is loaded.
- **Readability:** status colours and text stay readable on every theme, and the choice is remembered.

## User flow
1. Open **Dynamic Potential**.
2. The overview shows:
   - where the season is: before winter, winter done, or season done
   - the next review date
   - counts of players rising, steady, falling, held and needing review
3. Press **Run winter review** or **Run season-end review**. Results appear as player cards, and automatic changes go into the save straight away.
4. Open any player for a plain-words breakdown of score, minutes, evidence, age, taper and final change.
5. Look at **Needs your review** and approve or reject each one.
6. Open **Settings** to change any rule value. A short summary shows what each change means before saving.
7. In Appearance, pick a new theme.

## UI/UX feel
- **Simple on top, full detail below.** The overview is clean and calm, with one main action at a time.
- **Player cards:** each shows a clear up, steady or down signal with the change amount, and a short reason such as "Strong season, 1,620 minutes, age 27 (−2), taper applied".
- **Detail view:** a step-by-step breakdown from score, to base, to age, to taper, to final, with progress bars for percentiles and minutes against each requirement.
- **Settings panel:** grouped into sections with plain labels, short help text beside each value, and clear marks on values that differ from the rulesheet.
- **No real CA or PA anywhere on screen.**

## Implementation phases
**Phase 1 – MVP (built now)**
- The full rulesheet engine: evidence, scoring, missing-statistic handling, tiers, decline, age, both tapers, winter advance and settlement, limits, review records, repeat-run safety and batches.
- Automatic apply, with the "needs your review" exceptions waiting for approval.
- The new Dynamic Potential page: overview, player cards, player detail, review list and full settings panel.
- The four new themes.

**Phase 2**
- Balance preview: run the rules over a save without applying anything, to see how often players rise and fall by position, age and competition (rulesheet section 14).
- Compare two settings sets side by side on the same save.
- Export a season's review records.

**Phase 3**
- Club-wide trends across seasons: who keeps rising, and which leagues produce growth.
- Optional reminders on the review dates.
- Settings presets to share or import.

## Assumptions
- **The rulesheet is the source of truth.** Every default comes from it as written.
- **The old system is replaced.** Past awards are kept unchanged, and the new rules apply from the next review.
- **The "all loaded players" switch stays.** It decides who is reviewed.
- **Winter review date:** FMCC suggests it from the save's winter transfer-window opening, and you can change it.
- **Missing statistics in real saves:** where FM doesn't provide a statistic for a player, such as goals prevented, the missing-statistic rules decide what happens. Which statistics FM27 saves actually provide is only known after reading real saves on a PC.
- **Comparison groups** use players from the same save, matched by position group, role, competition strength and expected level.
- **The browser preview** runs on the sample save. Real-save behaviour still needs your PC.
- **Elite Training** awards stay separate and count toward the current PA reference, as the rulesheet says.
- **Theme colours** are matched from public screenshots, with no game artwork or fonts. FM27 club colours are brightened or darkened when needed to stay readable.
