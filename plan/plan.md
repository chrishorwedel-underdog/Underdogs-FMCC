# FMCC: Recruitment Lab scouting, in-game countdowns and a notification centre

FM Command Centre is a Windows companion for Football Manager. It plans squads, scouts players, tracks development and makes safe, reversible changes to your saves.
This round turns scouting into a full Recruitment Lab, inspired by the screenshots you shared. It also adds countdowns to every date-based feature and in-app notifications. The guiding rule: a very deep feature set that stays easy to find and use.

## Who it's for
- You, as the main user: an FM player who wants professional-level recruitment analytics without spreadsheets.
- New FMCC users, who should reach any feature in one or two clicks without a manual.

## Core features and experience

### 1. Design rule for this round: deep but easy
- New depth lives where you already look:
  - recruitment inside Scout Players and the player profile
  - countdowns on Home and on each page
  - notifications behind one bell in the top bar
- Summary first, detail on demand: the advanced parts sit in tabs or behind "Show more".
- Every stat and index has a one-line explanation on hover. Every notice and recommendation links straight to where you act on it.
- One switch in the top bar flips every table and chart between percentiles and raw numbers.

### 2. Recruitment Lab (inside Scout Players)
The screenshots are used as inspiration, not copied one to one. Anything here that FMCC already has is upgraded rather than duplicated.

**a. Explore chart (an upgraded Scatter)**
- Your club's players, the target zone (above both medians), the rest of the pool and your shortlist each have their own marker.
- Median lines are shown, and key players are labelled.
- A count line reads like "1,074 players plotted, 370 in the target zone".
- Clicking a dot opens the player.
- Saved searches show how many players are new since the last save read.
- Below the chart is a ranked list by role score.

**b. Shortlist board by tactic slot**
- One column per position in your tactic, headed by your current starter and his score.
- Shortlisted players are listed under their slot, ranked by score. Each shows how much better he is than your starter (for example "▲ 23"), plus age, value, philosophy fit and a status.
- You can move a player to another slot. Empty slots offer "DOF picks".

**c. Compare (up to four players)**
- **Percentile profile:** stats grouped into Shooting, Creating, Possession, Aerial and Out of possession.
  - Each player is a coloured dot on a 0–100 strip with the pool median marked.
  - Raw values sit alongside, with the best in each row underlined.
  - A dash shows when he has too few attempts for a stat to mean anything.
- **Three views:** Profile, Overlay radar and Pizzas.
- **Role fit table:** each compared player's score in the roles of his position.
- **Where they sit:** a chart of non-penalty xG against goals for every player in that position, with a "goals = xG" line and your club's players highlighted.

**d. Player profile, rebuilt**
- **Header:**
  - age, height and preferred foot, nationality
  - minutes and average rating, best role
  - value, wage, contract and years left, personality
  - how strong his league is compared with yours (for example "Slightly stronger")
  - a confidence badge from his minutes
  - quick actions: Add to compare, Show in Explore, Export report
- **Assess as:** pick any role. The roles in your tactic are offered first. You then see:
  - **Role score:** what the role needs.
  - **Philosophy score:** how well he fits your style.
  - **Character test:** from his personality.
- **What the role needs:** the role's key stats, each with a bar, raw value, weight (shown as dots) and percentile.
- **Your philosophy:** six style traits, each with a weight you can edit:
  - Keep the ball
  - Always available
  - Move it to hurt
  - Win it back in five
  - Defend on the front foot
  - Intensity

  These weights are saved and kept in your history.
- **Summary:** strengths and weak spots written in plain words from his numbers.
- **Role fit:** his top 5 roles, each with a role score and a philosophy score. Click a role to assess him in it.
- **Indices** (percentile averages, 0–100):
  - Chance creation
  - Ball security
  - Ball progression
  - Shot threat
  - Finishing, with a "luck" flag when his goals run far ahead of his xG
  - Ball winning
  - Pressing
  - Engine
  - Aerial
  - Box defending
  - Discipline
  - Crossing
- **Similar players:** same position, closest percentile profile, with value and score.
- **Pipeline and notes:** Watching → Scouted → Bid → Signed, or Rejected, with your notes. Every step is kept in history.

**e. DOF picks: ten recommendations for one role**
- **Inputs:** pick a role or slot, set the transfer budget and maximum wage, and choose filters:
  - leave out players likely to refuse
  - leave out players who go against your philosophy
  - include players who aren't for sale
- Your current starter is shown as the benchmark.
- **Five columns, two players each:**
  - **Dream:** best score in a stronger league that fits your budget.
  - **Upgrade:** beats your starter by 10 or more, aged 22–29, up to half the budget.
  - **Value:** most score per £.
  - **Squad player:** proven at your level, cheap cover.
  - **Prospect:** 21 or under, ranked against his age group.
- **Each card shows:** score, gain over your starter, value, wage, contract and a one-line reason. Tags include "Retrain to …", "Big step down for him", "Philosophy 79", "Final year" and "Contract expiring". Buttons: Shortlist, Compare and Open.
- **"Considered and left out":** a line naming strong players excluded for budget, wage or not being for sale.
- **"Add all to the shortlists"** and **"Compare top four"**.
- The DOF chat uses the same picks when you ask who to sign.

**f. New stats**, used across all of the above and in Formulas, filters and the DOF. Each appears only when your save has the numbers:
- shots per 90 and conversion %
- goals above xG per 90
- ball security (the share of touches that don't lose the ball)
- passes attempted per 90
- headers won per 90 and header win %
- pressures completed per 90
- goal contributions per 90
- non-penalty xG + xA per 90
- tackles + interceptions per 90
- distance covered per 90
- fouls committed and cards per 90
- average rating and share of minutes played
- for goalkeepers: clean-sheet rate, xG prevented and goals conceded per 90

There's also a **league benchmark** for each stat (league average and the top-10% mark) and **trend arrows** showing the change since the previous save.

### 3. Countdowns and missed-date notices (in-game dates from your latest save)
- **"Up next" strip on Home:** countdowns such as "Monthly report in 12 days", "Dynamic Potential review in 1 month 3 days" and "January window opens in 41 days". Each links to its page.
- **The same countdowns on their own pages:** Monthly Reports, Dynamic Potential, Breakout Player, Elite Training, Development (monthly minutes targets) and your squad's contract expiries.
- **Missed-date notices:** if a save jumps past a date without the event being handled, a notice explains it, for example "The October report was missed because no save was read in October". It offers to make it late from the nearest save, clearly labelled, or to dismiss it. Nothing is backfilled silently.
- Countdowns only move when a new save is read.

### 4. Notification centre (inside FMCC only)
- **A bell in the top bar** shows an unread count and a list grouped into Today, This month in-game and Earlier. Each notice can be opened or marked read.
- **Sidebar badges:** a small dot on pages with something new, for example Monthly Reports when a new report is ready.
- **What creates a notice:**
  - a new monthly league report
  - a missed date
  - a countdown reaching 7 in-game days
  - game changes waiting for approval
  - a new save read
  - add-on updates available
  - a DOF pick or suggestion still waiting
  - shortlisted players whose contract enters its final year
- **Settings → Notifications:** switch each type on or off. Everything is on by default.
- Notices are kept in history; clearing them only hides them.

## User flow
1. You save in FM. FMCC reads the save, and the bell shows "New save read: 1 Nov 2027" and "October report ready".
2. Home's "Up next" strip shows what's coming. You click "January window opens in 41 days".
3. In Scout Players → DOF picks you choose your weakest slot, set the budget and see ten picks across Dream, Upgrade, Value, Squad player and Prospect.
4. You open a pick's profile, assess him in your tactic's role, check his indices and similar players, then add him to Compare against your starter.
5. You shortlist the best two. They appear on the Shortlist board under that slot, marked Watching, and you move them along the pipeline as you scout and bid.

## UI/UX feel
- The same dark FMCC style, with a tighter "lab" feel in scouting:
  - bold condensed headings
  - a gold highlight for your club
  - one colour per compared player (A, B, C, D)
  - green / amber / red only for good / middling / poor
- Dense where it helps (tables, strips), calm everywhere else.
- Countdowns are short chips with a small progress ring. Missed dates use amber, never alarms.

## Implementation phases
- **Phase 1 (built now, MVP):**
  - the Explore chart upgrade
  - the Shortlist board by slot
  - the four-player Compare with Profile, Overlay and Pizzas, Role fit and Where they sit
  - the rebuilt player profile, with Assess as, role and philosophy scores, character test, indices, summary, similar players, and pipeline and notes
  - DOF picks, with its five columns and filters
  - the new stats, league benchmarks and trend arrows
  - the raw-numbers switch
  - the Home "Up next" strip and page countdowns
  - missed-date notices
  - the notification bell, sidebar badges and notification settings

  All of this is checked in the browser preview with the sample save.
- **Phase 2:**
  - check the new stats and indices against your real FM26 and FM27 saves on your PC, and adjust them
  - your own reminders (for example, "remind me 30 in-game days before X's contract ends")
  - team-level analytics (your style compared with the league)
- **Phase 3:**
  - shareable scouting reports as an image or PDF
  - season-over-season comparison of saved searches
  - philosophy presets shared between careers

## Assumptions
- Countdowns use in-game dates from your latest save, and notifications appear inside FMCC only, as you chose.
- Transfer windows and season dates come from the save when available. Otherwise they use each league's usual dates and are marked "estimated".
- **"Likely to refuse"** is estimated from league strength, club reputation and his role at his current club, and is shown as a tag, never as a certainty. **"Not for sale"** is only used when the save says so.
- **Personality and the character test** come from FM's personality labels. Hidden attributes are never shown in the Fair play or Moneyball views.
- **The six philosophy traits** are built from the stats FMCC already has. Their default weights are even, and you can change them.
- New stats appear only when the save contains the numbers. In the preview they come from the sample save.
- Values are shown in your chosen currency (£ by default), not €.
- Existing pages keep their places. Explore, Shortlist board, Compare and DOF picks are tabs inside Scout Players (Compare and Scatter are upgraded, not duplicated). No new sidebar entries are added.
- The Recruitment Lab screenshots are used for ideas only: no code or images are copied. They're credited as inspiration in Settings.
