# Clear monthly stats in "The biggest stories"

Each story in "The 12 biggest stories" shows the player's real numbers from that month, picked to suit his position, instead of an unexplained grade like "scores 96". The grey "Other" tag at the end of each line becomes the player's league.

## Who it's for
FMCC users reading the monthly stories who want to see straight away why a player is in the news.

## Core features and experience
- **No more grades:** The "scores 96" style number is removed from every story line.
- **New line format:** Each line reads: tag · player · club · that month's stats · league. For example:
  - *In form* Felipe Clemente, Sociedade Esportiva do Gama SAF: 5 games · 4 goals · 2 assists · 7.9 avg rating · Brazil Série D
- **Stats by position (all from that month only):**
  - Goalkeepers: games, clean sheets, saves, avg rating
  - Defenders and wing-backs: games, tackles won, interceptions, avg rating. Goals or assists are added if he got any.
  - Defensive and central midfielders: games, goals, assists, key passes, avg rating
  - Attacking midfielders, wingers and strikers: games, goals, assists, avg rating
- **Where his position comes from:** the position FM lists first for him. Players with mixed positions use that first one.
- **Missing stats:** A stat the save doesn't give for that player is left out of the line, not shown as 0. If none of a player's stats can be read, that story is left out of the list.
- **League tag:** The grey tag at the end shows the player's league name, for example "Brazil Série D", in place of "Other". If the league can't be read, the tag is left off.
- **Story tags stay:** The tag on the left ("In form" and others) stays as it is.

## User flow
1. Open the monthly section that holds "The 12 biggest stories".
2. Read each line: who, which club, what he did this month, and which league.
3. After the next save read, the stories update with the new month's numbers.

## UI/UX feel
- The current list style stays.
- The stats sit in the main text, separated by " · ", with numbers in the existing monospaced style so they line up when you scan the list.
- The league tag stays small and grey at the end.
- On phones, the stats wrap onto a second line under the player and club.

## Implementation phases
1. **Phase 1 (MVP, built now):** grades removed, stats chosen by position from that month, league tag in place of "Other", missing stats left out.
2. **Phase 2:** Tap a story to open a small card with the player's full month: all his stats plus the games he played.
3. **Phase 3:** The same stats-by-position line used in Monthly Awards nominee lists and in Breakout Player notices.

## Assumptions
- Which 12 stories appear and in what order stays the same as now. FMCC still uses its own ranking behind the scenes, but no number from it is shown.
- "Games" counts every appearance that month, including games as a substitute.
- Avg rating is rounded to one decimal place, as in Football Manager.
- The same format applies to every story type in this list, not only "In form".
