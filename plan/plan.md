# Feature Picker for Each Career, Menu Dot Explanation and Nationality − / +

The first time a career's save loads, FMCC opens a "Choose your features" page. It explains every left-menu page in plain words and lets the user switch each feature on or off for that career. Features that are off are greyed out and locked in the menu, and stop all their automatic work, until they're switched on again. The plan also includes the menu-dot explanation and the − / + nationality buttons proposed earlier.

## Who it's for
- New FMCC users who have never used the program and need to know what each page does.
- Experienced users who only want some features active in a given career.

## Core features and experience

### 1. "Choose your features" page
- **When it appears:** once per career, straight after that career's save is read for the first time. It doesn't appear again for that career. Every existing career sees it once, on its next save read.
- **What's on it:** one card per left-menu feature, each with its colour and icon, name, a plain 2–3 sentence explanation, an example of what it does in practice, and an on/off switch.
- **Starting point:** every feature starts **on**. There are "Turn all on" and "Turn all off" buttons, and a **Done** button that goes to Home.
- **Changing your mind:** a new **Features** link in the footer, next to Project Safety, Downloads and Appearance, opens the same page any time. Changes apply immediately.
- **Home is always on.** The footer pages (Project Safety, Downloads, Appearance, Features) and Settings aren't features and are always available.
- **Draft feature descriptions** (editable, written for first-time users):
  - **Home:** Your club at a glance: squad summary, your next match, what needs your attention and what's coming up in your save. Always on.
  - **Dynamic Potential:** Lets player potential rise or fall based on how players actually perform and develop, using rules you control. You review every suggested change before it goes into your game.
  - **Breakout Player:** Once a season, FMCC picks the player who broke out the most and gives them a current-ability bonus in your save.
  - **Scout Players:** Ranks every player in your save by how well they fit each role, their age, potential and value, so you can build shortlists quickly.
  - **World Monthly Reports:** Each in-game month, the news across the world, a continent, a nation or a league. Top stories, tables, the biggest transfers, stat leaders and Players of the Month.
  - **Moneyball:** Compares transfer targets side by side on value for money and fit, to help you decide who to buy.
  - **Squad:** Your best lineups and depth charts for league, cup and European games, using your save's own tactics.
  - **Development:** Minutes and growth plans for each young player, tracked automatically from every save, with how much each has improved.
  - **Elite Training:** Nominate your most promising youngsters; FMCC checks their training and can boost their potential under your rules.
  - **Matches:** A detailed view of every match: chances (xG), a chalkboard, player ratings and replays.
  - **Player & Teams Editor:** Faces, club logos, kits, names, a player creator and Seed a Surname.
  - **Punish a Club:** Hand out penalties to any club, such as points deductions, fines or transfer bans.
  - **Chat with your Director of Football:** An assistant that knows your squad, plans and history; ask it questions or for suggestions.

### 2. What "off" means
- **In the menu:** the item is greyed out (no colour) and locked. Clicking it does nothing except show a small hint: "Turned off for this career. Turn it on in Features." The Director of Football button greys out the same way.
- **In the background:** an off feature does no automatic work. It sends no reminders or countdowns, shows no menu dot, makes no suggested game changes and gives no awards. For example:
  - Dynamic Potential makes no suggestions.
  - Breakout Player gives no award.
  - Elite Training does no intake and gives no boosts.
  - Development doesn't check minutes targets.
  - Monthly Reports sends no "report ready" notices.
  - Scouting sends no shortlist contract alerts.
  - The Director of Football makes no suggestions.
- **Kept safe:** nothing already made is deleted. Changes already waiting in Game changes stay there to approve or reject. World Monthly Reports keeps quietly saving each month's data, so its history is complete if it's turned back on.
- **Home links:** Home's cards and "Up next" items for off features are hidden.

### 3. Menu "something new" dot, explained
- **What it means today:** the page has at least one unread notification from the top-bar bell.
  - On Home: "New save read" notices, and countdowns due within 7 days.
  - On other pages: their own notices, such as a report ready, game changes waiting or a DOF suggestion.
- **Change:** opening a page now marks that page's notifications as read, so its dot clears. They stay in the bell's list as read.
- **Tooltip:** hovering the dot or its menu item lists what's unread, for example "New: New save read: 1 Mar 2028 · Dynamic Potential review in 5 days. Opening this page clears the dot."
- **Tour:** the guided tour's Home step gains one line explaining the dot.

### 4. − / + on each nationality (Seed a Surname, step 3)
- **The buttons:** − and + sit next to each nationality's "% · N people" figure. Each press gives that nationality one person more or fewer.
- **Fixed total:** the total from step 2 never changes. The person comes from, or goes to, the other nationalities, largest share first.
- **Minimum of 1:** each nationality keeps at least 1 person; use × to remove one. − is disabled at 1, and + is disabled when every other nationality is at 1.
- **The slider:** it still works for rough changes and moves to match after − / +.

## User flow
1. The user creates or switches to a career, and FMCC reads its save for the first time.
2. The "Choose your features" page opens. The user reads each card, switches off what they don't want, and presses Done.
3. Home opens. The left menu shows the chosen features in colour and the rest greyed out and locked.
4. Later, the user opens Features from the footer and turns something on or off. The menu updates straight away.

## UI/UX feel
- **The page:** calm and welcoming, like a setup step. A short intro line ("Pick what FMCC does in this career. You can change this any time."), then a two-column grid of feature cards on desktop, one column on phones.
- **Cards:** each card's accent colour matches its menu item; when switched off, the card fades to grey to preview the menu look.
- **Greyed menu items:** shown in muted grey with no colour or glow, keeping the same size and order.

## Implementation phases
- **Phase 1 (MVP, built now):**
  - The Choose your features page, shown once per career after its first save read
  - The Features footer link
  - Per-career on/off switches, with off features greyed and locked in the menu and their background work and reminders stopped
  - The menu-dot tooltip, with opening a page clearing its dot
  - The − / + nationality buttons
- **Phase 2:**
  - Ready-made feature sets ("Just the essentials", "Everything", "Development focus")
  - Copying one career's choices to another
  - Clickable notices in the dot tooltip
  - A typed number box for each nationality
- **Phase 3:**
  - A short "what you're missing" summary on Home for off features
  - An Appearance setting to hide menu dots
  - Locking a nationality's count

## Assumptions
- **Per career:** choices belong to each career, not to the whole app.
- **Defaults:** every feature starts on; Home is always on; the footer pages and Settings can't be switched off.
- **Existing careers:** each sees the page once, on its next save read.
- **Director of Football:** it counts as a feature that can be switched off.
- **Monthly data:** it keeps being saved while World Monthly Reports is off, so no history is lost.
- **Switching off keeps work:** turning a feature off never deletes data or changes already waiting; turning it back on carries on from where it was.
- **Locked items:** clicking a locked item shows the hint only and never opens the page.
- **Wording:** the feature descriptions above are drafts and will be shown as written unless changed.
- **Menu dot:** opening a page clears only that page's notifications. The tooltip is desktop-only (the side menu is hidden on phones).
- **Nationality − / +:** each press changes one person and the step 2 total stays fixed.
