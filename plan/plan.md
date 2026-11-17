# Squad Picks by Natural Position and Star Ratings

The Depth chart, Lineup / Best XI and everything built on them pick players only for positions they actually play in Football Manager. They rank those players by their in-FM current ability, shown as star ratings in place of the 0–100 role numbers.

## Who it's for
FMCC users planning their squad from a real save, who want depth charts and lineups that match the way Football Manager itself sees the squad.

## Core features and experience
- **Who can go in a position:**
  - A player can fill the position FM lists first for him.
  - He can also fill any other position where FM rates him **Natural**.
  - He will no longer appear in positions he can't play. For example, a centre back stops showing up at Left Back unless FM rates him Natural there.
- **Ranking:** Within each position, players are ordered by their in-FM current ability, best first. The role rating no longer decides the order.
- **Star ratings:**
  - Each player shows ½ to 5 stars, measured against your own squad in the same way FM's coach stars work. Your best players sit near 5 stars at any level of football.
  - Stars appear wherever a 0–100 role number used to be.
  - No ability number appears anywhere, including tooltips, exports, notices and the Director of Football chat.
- **Short positions:**
  - If a position has too few players who play there, FMCC fills the gap with the next-best players from nearby positions. For example, a right back can cover right wing, and a defensive midfielder can cover centre back.
  - Those players carry an "Out of position" tag and always sit below the players who play there naturally.
- **No role numbers:** The 0–100 role ratings are removed from the Depth chart and Lineup. Only stars are shown.
- **Weakest positions:** This list is worked out from the stars of the best natural option in each position. It shows "x natural options" counting only the players who play there first or are rated Natural there. Each position appears only once, so Defensive Midfield is no longer listed twice.
- **Everything built on these picks follows the same rules:**
  - Lineup / Best XI
  - Depth chart
  - Weakest positions
  - Tactic fit
  - the Home items "weakest position in the Best XI" and "best option there"
  - the Registration and Loan Manager suggestions that use depth order
- **Your own order still wins:** If you've dragged players into a set order for a tactic, FMCC keeps that order. The new rules only shape FMCC's own suggestions and newly added players.

## User flow
1. Read a save as usual.
2. Open Squad → Depth chart. Each position lists natural players first, by stars. Any out-of-position cover comes after them, with its tag.
3. Open Lineup. The Best XI uses only natural players where possible, picking the highest-star players.
4. Check Weakest positions to see where the squad is thin.

## UI/UX feel
- The cards and drag-to-reorder look the same as now. The bar and number on each row are replaced by stars, in the existing accent colour.
- The "Out of position" tag is small and amber, next to the player's name.
- The note under Weakest positions changes to explain that stars compare players within your squad, as FM's coach stars do.

## Implementation phases
1. **Phase 1 (MVP, built now):**
   - natural-position-only picks
   - ranking by in-FM current ability
   - squad-relative stars replacing role numbers
   - nearby-position cover with a tag when a position is short
   - Weakest positions fixed
   - every Squad surface and Home item that depends on these picks updated
2. **Phase 2:**
   - a "Show role fit" option for any position, to see how well each natural player suits that tactic's role, in words such as "Good fit" or "Poor fit"
   - stars on the Players tab and in the player card
3. **Phase 3:**
   - stars measured against the league as well as your squad
   - a squad-planning view that shows which positions will lose stars next season through ageing, expiring contracts and loans

## Assumptions
- Both choices for "primary position" were picked, so a player is eligible at his first-listed position and at every position FM rates him Natural. When he qualifies in several, he can appear in each of them.
- "Natural" means FM's own Natural rating for that position. If the save doesn't give these ratings for a player, only his first-listed position counts.
- Stars come in half-star steps. The best player in the squad is set at 5 stars, and everyone else is placed against him, as FM's coach stars are. No numbers sit behind the stars on screen.
- Nearby positions for cover:
  - goalkeepers: none, so the slot stays short and shows a note
  - centre back: defensive midfield
  - full back: wing-back and centre back
  - defensive midfield: central midfield and centre back
  - central midfield: defensive and attacking midfield
  - attacking midfield: central midfield and wing
  - wing: attacking midfield, wing-back and striker
  - striker: attacking midfield and wing
- Tactic roles, such as "Ball-Playing Defender (Defend)", still label each position. They no longer change who is picked or in what order.
- Player orders you've already set yourself are kept as they are.
- The change applies in both the Windows program and the browser preview. The preview uses the sample save.
