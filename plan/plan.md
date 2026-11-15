# FMCC Site Audit and Improvement Round

FM Command Centre is a companion app for Football Manager. It reads your save and helps you run your club, develop players, scout, and track history.
This round fixes what the audit found: CA/PA leaks, slow or rough screens, inconsistent layouts, and a few obvious gaps.

## Who it's for
- The FMCC owner and anyone else who plays a Football Manager career with FMCC beside it.
- They want quick answers on a single screen and nothing that spoils the game by showing true CA/PA.

## Audit findings

### 1. CA/PA rule (highest priority; a standing rule)
Actual CA/PA must never be shown, hinted at with numbers, or included in exports.
These places still show CA numbers or CA changes, or may do so:
- **Squad table:** the "Ability gained since last save" column shows +/- CA numbers.
- **Monthly Reports comparison:** each player's CA change and the squad's total CA change appear as numbers.
- **Scout club deals:** a "Gain" column, which needs checking.
- **Other places to check:** Dynamic Potential review, Balance Preview, Elite Training evidence, the player panel History tab, the DOF chat, CSV exports, bell notices, staff screens, and any tooltip or "title" text that mentions CA.
- **Data sent to the app:** some screens receive raw CA values even when they don't display them. Any app user can read these in the browser.

### 2. Speed and things that feel broken
- **Home** is slow: it makes many separate requests (celebrations, record watch, what changed, up next, notices).
- **Club History** rebuilds the season archive on every visit. The bell also rechecks every record each time it refreshes.
- **Large tables** draw every row at once: Scout Players (100 rows × many columns) and the Transfer Market.
- **Opening Home** sometimes lands on the last page you visited instead.
- **Old pages** still use plain text placeholders, with no loading state or friendly empty state.

### 3. Easier to use
- **Inconsistent tables:** sorting, resizing and sticky headers work differently from table to table.
- **Long, mixed Home page:** celebrations, record watch, up next, what changed and module cards are all stacked with no clear order.
- **Phone use:** wide tables need sideways scrolling and have no card view on small screens.
- **Labels:** some still use developer wording or short forms, such as "Mins", "xGP" and "version 1".
- **Ctrl+K search:** it can't jump to Club History seasons, records or Hall of Fame players.

### 4. Missing features
- **Hall of Fame:** there's no way to write a note when you induct a player. The backend already supports it.
- **Development goals:** there's no bell notice when a youngster reaches his goal.
- **Club History:** the records and season pages can't be printed or saved as a page.
- **Tables:** column choices aren't remembered per table; only widths are.

## Core features and experience (Phase 1)

**CA/PA sweep across the whole app**
- Every CA or PA number and change is replaced with plain words such as "Big step forward", "Improving", "Holding steady" or "Slipped back a little".
- Up/down trend lines show direction only.
- Raw CA/PA values are removed from everything the app receives, in every screen, export, notice and DOF reply.
- A final check covers every page to confirm nothing is left.

**Faster Home and Club History**
- Home loads in one request, with smooth placeholders while it loads.
- The Club History archive is only rebuilt when a new save has been read.
- The record check runs once per save read, not on every bell refresh.
- Big tables show rows in pages of 50 with a "Show more" button.

**Redesigned Home**
- A clear top-to-bottom order:
  1. Greeting and next match
  2. Up next (urgent first)
  3. One "Highlights" strip, combining celebrations and record watch into swipeable cards
  4. What changed
  5. Module shortcuts
- Each section can be collapsed, and that choice is remembered.

**One table style everywhere**
- Every main table shares the same behaviour:
  - click a heading to sort
  - drag edges to resize
  - the header stays visible while scrolling
  - numbers are right-aligned
  - spacing is the same
  - widths and sort order are remembered for each career
- On phones, tables switch to stacked player cards.

**Clearer wording and navigation**
- Full stat names replace short forms where there's room.
- Ctrl+K search also finds Club History seasons, records and Hall of Fame players.
- Opening Home always shows Home.

**Small missing pieces**
- Hall of Fame tribute note.
- "Goal reached" bell notice for development plans.

## User flow
1. Open FMCC. Home appears quickly: greeting, then urgent items, then highlights, then what changed.
2. Click into any module. Its table behaves the same as every other table.
3. On a phone, the same screens show cards instead of wide tables.
4. Nowhere in the app shows a CA or PA number, including exports and the DOF chat.

## UI/UX feel
- The existing themes, kit accent, club colours, text sizes and high-contrast mode are kept.
- Calmer, more consistent spacing, with one heading style and one table style.
- Gold stays reserved for records and celebrations.
- Pages may be rearranged noticeably where it helps, as you allowed.

## Implementation phases
- **Phase 1 (built now):** everything above. That's the CA/PA sweep, the speed fixes, the Home redesign, one table style with phone cards, wording and search fixes, the Hall of Fame note and the goal-reached notice.
- **Phase 2:** printable or saveable Club History pages and season reports, remembered column choices for each table, and a Squad card view with filters.
- **Phase 3:** a broader redesign of remaining pages (Transfer Market, Editor, Punish a Club, Settings) to the new standard, plus a guided first-run tour for new careers.

## Assumptions
- "Never show CA/PA" also covers indirect numbers: CA changes, CA-based goals, staff CA, and CSV exports.
- FMCC may still use CA/PA privately for its own calculations, such as awards, grades and Dynamic Potential.
- Grades (for example "56.9 global") stay, because they are FMCC's own scouting score, not CA.
- No data is deleted. Saved plans, widths and settings for each career carry over.
- Real Windows and real-save behaviour can't be verified here; only the preview and sample save are checked.
- Live production only changes when you publish again.
