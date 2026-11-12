# FMCC Quality-of-Life Upgrade: Cleaner, Calmer, Easier

This upgrade gives FM Command Centre a less daunting look and feel without removing any features. Complex tools stay, but they sit behind simpler screens, clearer groups and sensible defaults.

## Who it's for
- New FMCC users who currently face too many options at once.
- Experienced users who want faster navigation, consistent rules screens and fewer manual steps.
- Players who need larger text, higher contrast or screen-reader-friendly tables.

## Core features and experience

### Standing rules (apply everywhere)
- True PA/CA is never shown and can't be revealed anywhere. This includes screens, filters, columns, exports, tooltips and any raw-data view.
- Automatic applying is the default. When a rule or setting produces player changes (including PA/CA changes), they go to the save straight away and a notification lists what changed.
- A "Review changes before applying" switch in the Features area turns on manual approval for anyone who wants it. It is off by default.

### Navigation
- The Home menu item is removed. Clicking the FMCC logo at the top left goes back to Home.
- The menu is grouped like this, alphabetical within each group:
  - **My Club:** Matches, Squad
  - **Player Development:** Breakout Player, Development, Dynamic Potential, Elite Training
  - **Recruitment:** Scout Players, Transfer Market
  - **Reports:** Club Analysis, World Monthly Reports
  - **Utilities:** Player & Teams Editor, Punish a Club
- Moneyball leaves the menu and becomes part of Scout Players.
- Chat with your Director of Football stays as the separate button at the bottom of the menu.

### Home: one "Up Next in Your Save" area
- A distinct panel at the top of Home, with its own background and border, combines "Up Next in your save" and "Needs your attention" in one list.
- Urgent items come first and are clearly marked. Each item has one clear action button.

### Finance strip (every screen, just under the top bar)
- A slim strip shows FFP compliance, wage-to-turnover ratio, transfer money spent this year, transfer budget remaining and bank balance.
- Each figure is coloured red (trouble), green (healthy) or gold (excellent), with a short reason shown on hover or focus.
- Missing figures show "Not in save yet" instead of a misleading number.

### Same rules screen in every module
- Dynamic Potential's "Settings" and the "Rules" in other modules all use one layout. Each rule shows:
  - its current value and default
  - a plain-language explanation
  - when it was last changed
- Before saving a change, a preview shows how many players it would affect.
- Any single rule can be reset to its default without resetting the whole module.
- **Dynamic Potential's recent rebuild is kept intact.** Its rulesheet calculations, winter and season-end reviews, settings history, scope switch and Balance Preview stay exactly as they are. Only two things change:
  - its Settings tab uses the shared rules layout, with the existing settings history supplying the "last changed" details
  - its "Needs Review" approval queue is used only when the manual-approval switch is on; otherwise those changes apply automatically and appear in the notification

### Scout Players (stage 2)
- A much simpler first screen with a search box, a few common filters and a results table. Advanced options sit behind a "More filters" panel.
- A Moneyball tab with bargains, value for money and undervalued per-90 performers.
- **Find Similar Players:** pick a player or enter target numbers (basic or per-90, such as xG, xA, key tackles and progressive passes) to see the closest matches with a similarity score.
- **Youth Intake Tracker:**
  - a calendar of youth intake dates, with the top 5 leagues on by default and any league switchable on or off
  - running countdowns to each intake
  - an FMCC bell notification as soon as an intake happens
- **Easier tables:**
  - the player column stays pinned
  - columns use standard short names (for example npxG and OP-KP), with full names on hover and focus
  - common filters stay visible while scrolling

### Squad (stage 2)
- Lineups and depth charts can be edited, and changes apply to the save automatically.
- **Loan Manager**, a clearly separate section:
  - **Try a loan:** pick the loanee and a possible club to see that club's depth chart, where the player fits, and a letter grade (A+ to F, with pluses and minuses) with a one-line reason.
  - **Track loanees:** for each loanee, see their league, minutes, stats, facilities and development trend. A red down arrow means in trouble, a green up arrow means going well and a gold up arrow means excellent.
- Squad and Club Analysis use the same assessment, so they always agree on the weakest position.

### Polish everywhere (stage 3)
- **Radar charts and heatmaps:** these replace plain text and bars for player attributes and metric breakdowns, styled like the game's Data Hub.
- **Screens remembered exactly as you left them, per career:**
  - filters, sort order, columns, formation, comparison picks and scroll position
  - closing a dossier returns you to the same player in the same table
- **Helpful empty states:** each one says why it is empty (filters, too few minutes, missing data or nobody qualifies). It also offers a matching action, such as loosening a threshold or showing who is closest to qualifying.
- **Accessibility mode:**
  - high-contrast colour options
  - font-size controls (building on the existing text-size setting)
  - tables that work with screen readers
  - visible keyboard focus

## User flow
1. Open FMCC and land on Home. The "Up Next in Your Save" panel lists what needs doing, and the finance strip shows the club's money health at a glance.
2. Use the grouped menu to reach a module, then click the FMCC logo to return Home.
3. In any module, open Rules. Change a value, see how many players it affects, then save. Changes apply automatically and a notification confirms them.
4. (Stage 2) Scout from one simple screen, switch to Moneyball, Similar Players or Youth Intake, and get a bell alert when an intake happens.
5. (Stage 2) In Squad, drag players in the lineup or depth chart, grade a potential loan and keep an eye on loanee arrows.

## UI/UX feel
- Calm and uncluttered: fewer buttons on first view, and advanced options one click away.
- Consistent patterns: the same rules screen, the same empty-state style and the same colour meaning everywhere (red trouble, green healthy, gold excellent).
- The current themes, kit accent and club colours stay as they are.

## Implementation phases
- **Phase 1 (MVP, built now):**
  - new grouped and alphabetised menu, with the Home item removed and the logo linking Home
  - combined "Up Next in Your Save" panel on Home
  - finance strip
  - automatic applying by default with notifications, plus the manual-approval switch in Features
  - all PA/CA viewing removed
  - one consistent rules screen across all modules, with preview counts and per-rule reset
- **Phase 2:**
  - Scout Players simplification with Moneyball folded in, and the Moneyball menu item removed
  - Find Similar Players
  - Youth Intake Tracker
  - easier tables
  - editable lineups and depth charts
  - Loan Manager
  - Squad and Club Analysis agreeing on the weakest position
- **Phase 3:**
  - radar charts and heatmaps
  - screens remembered per career
  - explanatory empty states
  - high-contrast and accessibility mode

## Assumptions
- Until phase 2, Moneyball stays reachable from its current menu item. It is removed when it moves into Scout Players.
- Automatic applying needs FMCC for Windows with the save or game connected. In browser or sample mode, changes still show notifications but only affect sample data.
- Finance colour thresholds:
  - wage-to-turnover: gold below 50%, green 50–70%, red above 70%
  - FFP: gold if comfortably compliant, green if compliant, red if at risk or breaching
  - spent, budget and bank: judged against the club's own budget and turnover
- The finance strip reads whatever the save provides. Figures the save doesn't contain are labelled as missing, never estimated.
- Youth intake alerts use the FMCC bell only, with no Windows pop-up.
- Loan grades run A+ to F with pluses and minuses. They are based on expected minutes, league level, facilities and fit with the player's development.
- Disabling a module in the per-career feature picker still never deletes its data.
- Real FM save behaviour (finance figures, automatic applying, lineup writes, loan data, intake dates) can only be confirmed on a Windows PC with FM running.
