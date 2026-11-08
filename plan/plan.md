# FMCC — All-in-One Director of Football for Football Manager 26/27

FMCC (FM Command Centre, from Underdog Podcasts) is a single, simple Windows program for one Football Manager career.
It reads your saves on its own, plans and decides across six linked modules, and writes decisions back into the running game, with save reading and game editing built in.

## Who it's for
One FM manager on Windows who runs long careers. They want one program that handles club operations, player development and recruitment, changes the game automatically, and never needs setup, other tools or manual editing.

## How it runs
- **One program, one install:** a single Windows installer puts FMCC in the Start menu. Nothing else needs to be downloaded, installed or opened. It needs no account or login and works offline. An internet connection is only used to check for updates.
- **Built-in save reader:** **fmsave** (MIT licence) is packaged inside the program. The program watches your FM save folder and reads each save automatically, including autosaves.
- **Built-in game editor:** **FMLibreEditor** (GPL-3.0 licence) is packaged inside the program and runs hidden in the background. It writes changes into the running game, such as CA/PA awards, Elite Training boosts and Dynamic Potential adjustments. You never see its window.
- **Your control:** each kind of change has its own setting. "Apply automatically" is the default and applies the change at the next safe moment. "Ask me first" waits for one click from you.
- **Safety net:** before each batch of changes, the program copies your save. It checks each change against the current in-game value, records every change in an audit trail, and never applies the same award twice.
- **Automatic data backups:** the program's own data is backed up automatically, and you can restore it from inside the app.
- **Built-in match analytics (FMMatchLens):** FMMatchLens (MIT licence) is included.
  - **One-click setup:** the first-run setup installs its game add-on into FM for you, together with BepInEx, the mod loader it needs.
  - **Automatic match data:** from then on, every match you play is recorded automatically, with events, shots, xG, passes and pitch positions. FMCC reads this data on its own, so you never open FMMatchLens or export anything.

## Updates
- **Weekly automatic check:** once a week, the program checks for new versions of five things: FMCC itself, its built-in save reader (fmsave), its built-in game editor (FMLibreEditor), the FMMatchLens add-on and its add-on loader (BepInEx).
- **Manual check:** a "Check for updates" button in Settings (and in the Ctrl K search) runs the same check for all five at any time. Each is listed with its current version and an "Up to date" or "Update available" label.
- **How an update is applied:** the program shows a short notice ("New game editor version available — supports FM27 patch X"). An "Update now" button downloads the update, checks it and swaps it in. Updates never install while FM changes are being applied.
- **Rollback:** if a new reader or editor version fails its first check against your save or game, the program automatically goes back to the previous version and tells you.
- **Optional auto-install:** a setting lets updates install on their own without asking.
- **After an FM patch:** if FM was patched and the built-in reader or editor doesn't support it yet, the program shows "Game link paused — waiting for update". It keeps your plans and awards queued, and checks daily until a fix arrives.

## Core features and experience
1. **Career profiles**: separate careers for FM26 and FM27, each with its own club, seasons and history.
2. **Game link status**: a single indicator showing that FM is detected, the last save was read, changes are applied, and everything is up to date.
3. **Identity matching**: players are matched across saves by the game's unique ID, never by name alone.
4. **Home dashboard**: six module cards with key numbers and alerts, such as expiring contracts, weak positions, stalled youngsters and pending game changes, plus a "Needs your attention" list and the next match.
5. **Squad Management**: depth charts per formation, saved lineups, weaknesses by position, an automatic Best XI, and an automatic Development XI.
    - **Role ratings:** every player is rated for each FM role and duty, for example Ball-Playing Defender (Defend) or Inside Forward (Attack). The lineup pickers, weakness view and scouting all use these ratings.
    - **Squad registration check:** checks your squad against each competition's rules, including squad size, homegrown and club-trained quotas, foreign-player limits and under-21 lists. It warns you before a breach, suggests who to register or leave out, and flags signings that would cause a problem.
6. **Squad Development**: minutes plans, loan plans and development goals per player, with progress tracked automatically.
7. **Scout Window and Moneyball**: automatic scouting of every player in the save, with rankings by role fit, age, potential and value, plus shortlists, comparisons and value-for-money scoring.
    - **Performance evidence in rankings:** rankings also use real match performance from FMMatchLens, such as xG, xA, key passes, progressive passes, duels won, pressures and defensive actions per 90 minutes. A player is scored on both "how good the game says he is" and "how well he actually plays".
    - **Players seen against you:** opponents who play against your team are added to Scouting automatically, with their match stats, and labelled "Seen vs us".
    - **Over/under-performance flags:** Moneyball flags players whose performance beats or falls short of their rating and price.
8. **Match Analytics**: a Sofascore/Opta-style view of every match you play.
    - **Match summary:** a match rating, an xG timeline and the momentum of the game.
    - **Chalkboard:** shot maps, pass maps, heat maps and defensive-action maps. Each can be filtered by player, team, half or type of action. Hovering a shot shows the player, minute and xG.
    - **Player match card:** a rating and key stats for each player.
    - **Season view:** per-90 stats for your squad, with trends across matches.
    - **Replays and highlights:** goal replays and match highlights open in the built-in FMMatchLens viewer, inside the FMCC window.
9. **Monthly Reports**: an automatic squad snapshot each in-game month, and comparisons between snapshots.
10. **Elite Training**: nominations, training evidence taken from the save, and PA boosts applied under your rules.
11. **Annual Breakout and Dynamic Potential**: nominations, reviews and official awards at the end of each season, with CA/PA changes written into the game. Breakout cases are backed by real match evidence, such as an xG rise or a per-90 improvement.
    - **Who Dynamic Potential applies to:** a simple "Applies to" panel. "My club" is on by default. Below it are two searchable lists, **Nations** and **Leagues**, each with on/off toggles and "Select all" / "Clear" buttons.
      - **Leagues:** switching a league on includes every player at every club in it.
      - **Nations:** switching a nation on includes every player of that nationality, wherever they play.
      - **Overlap:** a player covered by more than one toggle is only counted once.
    - **Live count:** the panel shows how many players are covered, for example "Covers 3,412 players in 4 leagues and 2 nations".
    - **Same rules everywhere:** the same reward rules apply to every covered player. Optional caps limit adjustments to a maximum number of players or a maximum PA change per player each season.
    - **Evidence for other clubs:** for players outside your club, Dynamic Potential uses the evidence available in the save: minutes, season stats, match ratings, age and ability growth between saves. FMMatchLens match stats are added when the player has faced your team.
    - **Applying many changes at once:** changes are applied in batches, with one save backup before each batch, an audit entry for every player and the usual protection against applying twice. When it finishes, a summary shows who was covered, without values. For example: "Dynamic Potential applied: 214 players in Serie A and Eredivisie". Each batch can be undone from the audit trail.
    - **Review mode:** a "Review before applying" toggle shows only which teams and players are included, grouped by league and club. You can untick individual players or whole clubs before anything is written. The list never shows whether a player goes up or down, or by how much.
    - **Changes stay hidden:** to keep the game immersive, the actual Dynamic Potential changes are never shown in the program. This covers the review, the summary, the audit trail and the DOF chat. You find out how players develop by playing FM.
      - **What the audit trail shows:** which players were included and when, with no values.
      - **What is still kept:** the program records the exact values internally, so undo and the protection against applying twice still work.
      - **Optional reveal:** a "Show Dynamic Potential details" switch in Settings reveals the values. It is off by default.
12. **Append-only history**: revising a plan or an award keeps every earlier version.
13. **Fully editable rules in every module**: each module has its own **Rules** tab, and every setting in it can be changed.
    - **What counts and by how much:** the conditions a player must meet, how much he improves, when it happens and who it applies to.
    - **Plain-sentence rule builder:** every rule reads like a sentence, with editable blanks. For example: "If a player is **under 21** and plays at least **1,500 minutes** with an average rating of **7.0+**, raise PA by **3 to 8**." You can add, remove, reorder or switch off any rule, and combine conditions with "and" or "or".
    - **Conditions available:** anything the program knows, including:
      - age, minutes, appearances, match rating, goals and assists
      - xG, xA and other per-90 match stats
      - training rating, ability growth between saves, current and potential ability
      - position, league level, club and nationality
    - **Amounts and limits:** fixed or random-range changes, separate CA and PA amounts, and caps per player, per season and per run. Minimum and maximum ability limits ensure a rule can never push a player past a set value.
    - **Timing:** each rule can run monthly, at season end, after a set number of matches, or on demand.
    - **What each module lets you edit:**
      - **Squad Development:** minutes targets and what counts as "needs minutes".
      - **Development XI:** how youth minutes are balanced against team strength.
      - **Scouting and Moneyball:** ranking weights, role definitions and value-for-money scoring.
      - **Monthly Reports:** which stats are tracked and what counts as rising or falling.
      - **Elite Training:** nomination criteria and PA boosts.
      - **Annual Breakout:** award categories, criteria and rewards.
      - **Dynamic Potential:** growth and decline rules and their scope.
    - **Starting point and safety:** each module starts with a sensible preset, and "Reset to default" restores it. You can save your own presets, then copy them between careers or export and import them.
    - **Rule history:** rule changes are kept as dated versions, so every award shows which version of the rules produced it. Changing a rule only affects future runs, never changes already applied.
    - **Test a rule:** a "Test this rule" button shows how many players would currently qualify, without applying anything. For Dynamic Potential it shows only the count and names, never the values.
14. **Performance in every module**:
    - Monthly Reports include per-90 trends.
    - The Development XI and Squad Development consider recent match form.
    - The DOF chat can answer questions like "Who is my most effective presser?" or "Which striker is underperforming his xG?"
15. **DOF chat**: a Director of Football you can talk to inside the program, powered by OpenAI (model **gpt-5.6-terra**).
    - Answers stream in word by word, with a typing indicator first.
    - Each conversation is saved per career, so you can return to it later.
    - Suggested questions sit above the message box, one click to ask.
    - It sees your current squad, plans, reports, rankings, match data and history, so it can answer questions like "Who should start the cup game to give my U21s minutes?" or "Which veteran should I sell this summer?"
    - It can draft actions such as a lineup, a shortlist, a nomination or a development plan. A drafted action is only saved after you click "Accept". Anything it proposes that would change the game always asks you first, even when that kind of change is otherwise set to apply automatically.
16. **Search everything (Ctrl K)**: one search box, opened from the top bar or with Ctrl K, finds any player, screen or action ("Check for updates", "Ask DOF…"). It works fully from the keyboard.

## User flow
1. Install and open FMCC. On first run, it finds your FM save folder automatically (you can change it if needed) and asks for a career name.
2. Play FM normally, with FMCC open alongside it or minimised to the system tray.
3. Each save updates Home within moments.
4. Make decisions in the modules. Changes the game needs are applied automatically.
5. At the end of each season, awards are finalised and written into the game.
6. Updates arrive weekly, or whenever you press "Check for updates".

## UI/UX feel
A premium data studio: calm, precise and expensive-looking, like a professional analytics tool, built first for ease of use. Someone new should understand any screen within seconds. The updated mockup is in /app/plan/mockup.html, with four clickable screens: Home, Squad (Best XI / Development XI), Matches (chalkboard) and DOF Chat. It now includes the new colour-coded sidebar, the larger logo, the red DOF button and the larger text.
- **Brand:** the FMCC bulldog logo ("From Underdog Podcasts") sits large and round in the top-left corner of the sidebar, next to the FMCC name. It also appears on the installer, the Windows taskbar icon and the first-run screen. The program is called **FMCC** everywhere.
- **Colour:** a near-black graphite background with soft layered panels. One fixed accent colour, an electric blue taken from the logo, is used for primary buttons, highlights and your team's data. Green, amber and red are used only for meaning (good, needs attention, warning) inside the screens. The two exceptions are the sidebar, where each section has its own colour, and the "Ask your DOF" button, which uses the red from the logo. The colours never change with your club.
- **Typography:** all text is one size larger than in the first mockup, across every screen, the top bar and the sidebar. A clean modern sans-serif is used for text, a monospaced font for numbers so figures line up, and an elegant italic serif for a few headline accents ("Good evening, *Boss.*").
- **Depth and texture:** subtle film grain, a faint dot grid behind the header, glass-blur top bar and pop-ups, and soft glows around key elements.
- **Buttons that react:**
  - Primary buttons glow, have a light sheen that sweeps across on hover, lean slightly towards the cursor, and show a ripple where you click.
  - Secondary buttons and filter chips lift on hover. Toggles slide a coloured knob between options.
  - Completed actions turn into a "Done" tick, fade out the related item and show a small confirmation in the corner.
- **Living data:**
  - Numbers count up when a screen opens, sparklines draw themselves, the Best XI rating fills a ring gauge, and progress bars grow in.
  - On the pitch, switching between Best XI and Development XI glides the players into their new positions. Hovering a player shows his role and role rating.
  - On the chalkboard, shots, passes and actions pop in one by one, and switching map type re-animates them.
- **Cards:** each card has a soft spotlight that follows the cursor. Module cards on Home tilt slightly in 3D as you hover them.
- **Navigation:** one wider sidebar of large, rounded, colour-coded buttons, in the style of the reference picture you sent. Nothing is hidden in nested menus. Screens open with a short staggered reveal.
  - **Each button:** a coloured icon tile, a bold name and a short subtitle. Every section keeps its own colour:
    - Home (lime): "Your club at a glance"
    - Squad (teal): "Lineups and depth charts"
    - Development (blue): "Minutes and growth plans"
    - Scouting (cyan): "Targets and Moneyball"
    - Matches (orange): "Chalkboard and match stats"
    - Reports (violet): "See the bigger picture"
    - Elite Training (pink): "Nurture your next generation"
    - Awards (gold): "Breakout and Dynamic Potential"
  - **Selected and hover:** the selected button fills with its colour and glows. Other buttons slide slightly and brighten their border on hover. Counts such as "4" on Development stay on the right.
  - **Ask your DOF:** a big, softly pulsing button in the logo's red sits near the bottom, reading "Ask your DOF · Chat with your Director of Football".
  - **Settings:** sits below it, as a quieter grey button reading "Updates, sounds and safety".
- **Home talks to you:** it opens with a greeting and a one-line status ("Everything is up to date. Three things need your attention today"), which updates as you deal with items. Six cards each show one big number, one plain sentence, one small chart and one "Open" link.
- **Plain language everywhere:** "4 youngsters need minutes" instead of a data table. Every automatic suggestion includes a short "Why this…" explanation.
- **One clear action per screen:** for example "Use this lineup" or "Accept". Secondary options stay quiet.
- **Always-visible game link:** a pulsing pill in the top bar ("Game linked · save read 2 min ago") shows green, amber or red.
- **Motion control:** full motion is on by default. A "Reduce motion" switch in the top bar and in Settings turns off all movement and effects instantly. It also turns on automatically if Windows is set to reduce animations.
- **Sounds:** subtle sounds are on by default: a soft click when you navigate, a short chime when an action is confirmed, and a gentle tone when the DOF finishes a drafted action. A speaker button in the top bar and a switch in Settings turn them off.
- **First-run setup:** one simple guided screen of four steps, each with a progress tick.
  1. **Find Football Manager:** the program finds FM and your save folder automatically and shows "Found FM26/FM27 ✓". A "Change" button is there if it guessed wrong.
  2. **Install match analytics:** one "Install" button adds the FMMatchLens add-on and its loader to FM, with a progress bar and a "Done ✓" at the end. If FM is open, the program asks you to close it first. Windows may show one permission prompt. You can skip this step and do it later from Settings.
  3. **Name your career:** club and career name, filled in from your latest save.
  4. **Add your OpenAI key (optional):** for the DOF chat. You can skip it and add it later.
- **Built in, nothing to install:** the save reader and game editor are already inside the program, so they need no setup step.
- **Health check at the end:** the setup finishes with a quick check showing "Game link ready", "Match analytics ready" and "DOF ready", or a plain explanation of anything that isn't ready yet.

## Implementation phases
- **Phase 1 (MVP, built now):** the all-in-one Windows program and installer, in the new FMCC design, with:
  - the built-in save reader and game editor
  - weekly and manual update checks with automatic rollback
  - career profiles and the Home dashboard
  - all six modules in working form
  - the automatic Best XI, Development XI, full scouting and rankings
  - append-only history, data backups and the audit trail
  - the DOF chat powered by OpenAI
  - built-in FMMatchLens with one-click add-on setup, the Match Analytics module (chalkboard and match stats), and performance evidence in Scouting, Moneyball, Development, Reports and Awards
  - Ctrl K search, sounds and the reduce-motion switch
- **Phase 1 build stages:** Phase 1 is built in four stages. Each stage ends with a Windows installer you can test on your PC before the next stage starts.
  1. **Foundation and save reading:**
     - **Built:** the program window in the new design (logo, sidebar, top bar, animations, sounds, reduce-motion, Ctrl K search), installer, first-run setup (find FM, name career), career profiles, built-in save reader with automatic save watching, player identity matching, Home dashboard (showing real squad data), weekly/manual update checks with rollback, and data backups.
     - **You test:** does it install, find FM, and show your real squad after each save? Does it look and feel right?
  2. **All planning modules and rules:**
     - **Built:**
       - **Squad:** role ratings, depth charts, saved lineups, Best XI, Development XI, weak-position view and squad registration check.
       - **Scouting:** automatic rankings, shortlists and Moneyball comparisons.
       - **Development and reports:** Squad Development plans (minutes and loans), Monthly Reports, Elite Training, Annual Breakout, and Dynamic Potential with nation/league scope and hidden values.
       - **Rules:** the Rules tab with the plain-sentence rule builder in every module, presets, rule history and "Test this rule".
       - **Awards:** calculated and queued, but not yet written to the game.
     - **You test:** do lineups, rankings, registration warnings, rules, reports and nominations look right for your save?
  3. **Automatic game changes:**
     - **Built:** built-in game editor running hidden, change queue, "Apply automatically / Ask me first" settings, save backup before each batch, audit trail, undo, protection against applying twice, and large batch runs with progress and pause.
     - **You test:** do awards and Dynamic Potential changes actually appear in FM? This is the riskiest stage, and fixes are most likely here.
  4. **Match analytics and DOF chat:**
     - **Built:**
       - **Match analytics:** one-click FMMatchLens and BepInEx install, and the Matches module (summary, xG timeline, chalkboard, player cards, season per-90 stats and replays).
       - **Match evidence:** feeds Scouting, Moneyball, Development, Reports and Awards, and adds "Seen vs us" opponents.
       - **DOF chat:** uses your OpenAI key.
     - **You test:** are matches recorded and shown, and does the DOF give useful answers?
- **Order of the stages:** each stage relies on the one before it. You can stop, pause or change direction after any stage, and everything built so far keeps working on its own.
- **Phase 2:** multi-season trend charts, recruitment planning that uses Moleman-style "willing to join" information, and scouting with match stats for players who have never faced your team.
- **Phase 3:** a macOS version, deeper links between development, rotation and transfer decisions, and an FM27 adapter verified against each game patch.

## Assumptions
- **Accent colour from the logo:** electric blue from the logo stays the main accent inside the screens, leaving green, amber and red free to mean good, attention and warning.
- **Logo red on the DOF button:** the logo's red is used for the DOF button. It is never used for warnings in the sidebar, so the two aren't confused. Warnings inside screens keep their own, slightly softer red.
- **Sidebar colours and subtitles:** each section's colour and subtitle were chosen to echo your reference picture. Both can be changed before the build. The section colours appear only in the sidebar, so the screens stay calm.
- **Same logo as before:** the FMCC bulldog logo you already sent is used, shown larger and in a round frame. A transparent PNG would give the sharpest edge, but isn't needed.
- **Larger text means a wider sidebar:** the bigger buttons and text make the sidebar about 50 pixels wider, so the main area is slightly narrower on small screens.
- **Logo background:** the logo you sent has a white background. FMCC removes it automatically so the logo sits cleanly on the dark interface. In the mockup it sits on a round white frame for now.
- **Logo in small sizes:** at taskbar and tray size, the full logo with text is too detailed, so the bulldog head inside the circle is used on its own there.
- **Sounds are original and quiet:** the sounds are short, soft tones made for FMCC, never louder than your system volume. They only play for your own actions and finished DOF drafts, never at random.
- **Reduce motion follows Windows:** if Windows "Show animations" is turned off, FMCC starts with reduced motion on. You can still switch it back.
- **Match stats only cover matches you play:** FMMatchLens records matches your team plays. Match stats in Scouting therefore cover your own players and opponents you have faced. Other players are still ranked using save data such as ratings, attributes, potential and basic season stats from the save.
- **FMMatchLens version support:** FMMatchLens currently states support for FM26 (version 26.3) on Windows. FM27 match analytics depends on FMMatchLens adding FM27 support. Until then, the Match Analytics module shows "Waiting for FM27 support" and everything else works.
- **Mod loader added to FM:** the add-on and BepInEx are installed into FM's game folder. Both can be removed with one click from Settings. FM updates can temporarily disable them until a new version is released, and the weekly check picks that up.
- **Replays use the FMMatchLens viewer:** replays and highlights use FMMatchLens's own viewer, shown inside FMCC, rather than being rebuilt. The chalkboard and stats are rebuilt in FMCC's own design.
- **FM Player Analyzer is used as a reference, not built in:** FM Player Analyzer is a standalone desktop program with no way for another program to control it, and it mostly repeats planned features (Best XI, weaknesses, signings, youth). Its useful ideas, role ratings and squad registration checks, are rebuilt natively in FMCC, credited under its GPL-3.0 licence. Because nothing from it is installed, it is not part of the update checks.
- **Registration rules start from presets:** competition rules start from presets for major leagues and can be edited in the Rules tab, because FM rules differ by league and season.
- **Large Dynamic Potential runs:** leagues and nations selected for Dynamic Potential only cover players held in your save; FM's loaded database decides which leagues have full player data. Applying changes to thousands of players can take several minutes, and runs while FM is open, ideally during a holiday or between matches. The program shows its progress and can be paused.
- **Store versions of FM:** the one-click add-on install is designed for the Steam version of FM. Game Pass (Microsoft Store) versions keep their game files locked, so the match analytics add-on may not install there. The program detects this and explains it, and everything else still works.
- **Open-source licence:** FMLibreEditor's GPL-3.0 licence allows it to be included only if FMCC is also shared as open source under GPL-3.0, with credit to fmsave and FMLibreEditor inside the program. FMCC will be released that way. The FMCC name and bulldog logo remain yours; the licence covers the code.
- **Where updates come from:** updates for the reader and editor come from the official fmsave and FMLibreEditor release pages. Updates for FMCC come from your own GitHub repository.
- **Testing in two steps:** this environment runs Linux and has no Football Manager. Screens, logic, packaging and the update checker are built and tested here, and an automated Windows build produces the installer. The first test with the real game happens on your PC, and some fixes after it are expected.
- **Hidden editor not yet confirmed:** running FMLibreEditor hidden and controlled by the program relies on its command-line and scripting support, which isn't confirmed in detail yet. If that proves impossible, fm-editor (also GPL-3.0) is used instead. If neither works, automatic writing pauses and awards stay queued in the program.
- **Fresh build:** this is a new project, separate from your existing FM Command Centre repository and PR #77.
- **When changes stick:** changes become permanent when FM next saves. If FM is closed, they wait until it is open again.
- **Single-player only:** live editing is used at your own discretion.
- **Windows may warn at install:** Windows may show a "Windows protected your PC" warning on first install, because the installer isn't code-signed. You can click past it.
- **Rules, not AI:** ratings, rankings, the Development XI and every reward use your editable rules. The DOF chat explains and discusses them but doesn't replace them.
- **Sample presets:** each module's starting preset uses example values you can change completely.
- **Your own OpenAI key:** the DOF chat uses your own OpenAI API key, entered once in Settings and stored securely on your PC. OpenAI bills your account for each conversation. The program can't come with a built-in key, because it is released as open source and any included key could be copied.
- **DOF chat needs the internet:** without a connection or a key, the DOF chat is unavailable and everything else works normally.
- **Data sent to OpenAI:** the DOF chat only sends OpenAI a summary of your career data and your messages, nothing else from your PC.
- **Mockup data is placeholder:** names and numbers in [brackets] in the mockup are placeholders; in the program they come from your save.
