# Fix Pages That Break on Real FM27 Save Data, Make Grey Text Readable, Find NG_Regens Automatically, Fix Seed a Surname, Show the Club Logo, Add New-Game Defaults, and Fix the Director of Football Key

Breakout Player, Dynamic Potential, Elite Training and Scout Players work in the FMCC Windows program even when some players in a save have details FMCC doesn't expect. On dark themes, all the hard-to-read grey text across FMCC becomes soft white. NG_Regens faces that are already installed are recognised, with a "Find it automatically" button and a "Choose it myself" fallback.

## Who it's for
Anyone using the FMCC Windows program, starting with the Wrexham 27 career, where:
- Breakout Player, Dynamic Potential (Overview) and Elite Training stay on their loading bars;
- Scout Players shows "Something went wrong. Please try again." on Find players and on Similar players searches, such as "Callum Doyle";
- grey text on dark themes is hard to read. Examples on Club Analysis: the line under each "What to do first" item, the heatmap area names and column headings, and the radar chart labels.
- FMCC says NG_Regens newgen faces aren't installed when they are, and offers to install the NG_Regens Manager from Downloads again.
- Seed a Surname says "50 player slot(s) had no low-profile player left to rename" and "40 staff were left out: FMCC hasn't read any staff from this save yet", in a save with about 500,000 players loaded.
- Entering an OpenAI key for the Director of Football chat fails with an error. The chat page only says "Add your OpenAI key in Settings".

## Why the OpenAI key is rejected
- FMCC tests a key by asking one specific, very new model for a one-word reply. Many personal OpenAI accounts can't use that model yet. The test then fails even when the key itself is fine.
- Every kind of failure gives the same message: "That key didn't work. Check it's copied in full and that your OpenAI account has credit." It doesn't say whether the key is wrong, has no credit, can't use that model, or couldn't reach OpenAI.
- A key is only saved after a successful test, so a good key can never be stored.

## Why Seed a Surname finds nobody
- **Players:** Seed a Surname only looks at FMCC's scouting snapshot of the save, not the whole database. That snapshot keeps just the busiest 4,000 players who have match minutes in the leagues FMCC read tables for. Those are exactly the established players Seed a Surname must avoid. The free agents, youngsters and fringe players it wants are almost never in it. If the league tables couldn't be read, the snapshot is empty.
- **Staff:** staff come only from the main save reader's staff list. If that part of the save is skipped, FMCC stores an empty list and reports that no staff were read. The backup reader doesn't read staff.
- FMCC's bundled game editor (FMLibreEditor) can already list every player and every member of staff in a running FM27 game, but Seed a Surname doesn't use it yet.

## Why NG_Regens isn't found
- FMCC only checks one exact spot: a settings file inside the NG_Regens folder of the current career's FM graphics folder.
- An NG_Regens install usually has the face folders (Afroamerican, Afrocaribbean and so on) directly inside the NG_Regens folder, with no such settings file.
- FMCC only looks in the graphics folder for the career's own FM edition. Faces installed with the NG_Regens Manager for FM26 can sit in the Football Manager 26 graphics folder, or a OneDrive Documents copy, while the career is FM27.

## Why the pages break
- These pages all start by building a profile of every player they cover from the latest save read: your squad, and for Scout Players and Dynamic Potential, players at other clubs too.
- That step stops completely if a single player's details don't match what FMCC expects. Examples:
  - a combined position written like "D/WB (R)" or "AM (RLC)";
  - a player with no position;
  - a missing nationality, age or club.

  Saves from FM27 updates the main reader only partly supports, or filled in by the backup reader, make this much more likely. One such player among thousands is enough to break the whole page or search.
- When that happens, the loading pages never get an answer back, and Scout Players shows the generic error.
- Breakout Player also runs its season-end winner check first on every visit. If that check fails, the page doesn't load either.

## Core features and experience
1. **Every FM position style read.** FMCC understands every position form FM uses, including combined and multi-side ones like "D/WB (R)" and "AM (RLC)".
2. **One unreadable player can't break a page.**
   - **Your squad (Breakout Player, Dynamic Potential, Elite Training):** a player with odd or missing details is still listed. He's grouped as midfield for position-fair grading until his position can be read, and missing details are shown as blank.
   - **Scouting results (Find players, Similar players, Youth intake, Lists, Compare, Moneyball):** a player whose data can't be read is left out, and the rest show as normal. A small note says how many were left out, such as "3 players left out: their save data couldn't be read".
3. **Never stuck loading.** If a page or search still fails, a plain message with a "Try again" button replaces the loading bars or the generic error.
   - Example: "FMCC couldn't search the scouting data from your latest save. Try again, or read a newer save."
   - If nothing comes back after about 30 seconds, the page says it's still working, then shows the message.
4. **Content even with missing stats.**
   - **Breakout Player:** your squad, with "No season grade yet" where a grade can't be worked out.
   - **Dynamic Potential:** who's covered and the review schedule, with a note about players whose stats can't be read.
   - **Elite Training:** nominees and suggestions, with "No training rating yet" where needed.
   - **Scout Players:** players without readable match stats still appear in name and club searches. They show "—" for missing numbers and rank below players with stats.
5. **Automatic checks never block a page.** The Breakout season-end winner check and the Elite Training session check run separately. If one fails, the page still shows, with a note that it will run on the next save read. Each still runs only once and never applies twice.
6. **Readable text on dark themes.** Every grey or dimmed text colour on dark themes becomes one soft white, the same as the main text.
   - This covers notes, small print, table headings, labels, chart labels, placeholders, the "last checked" lines, the footer and the left menu's group names.
   - Hierarchy comes from size, weight and spacing only. Nothing is dimmed.
   - Disabled buttons and inputs still look faded, so it stays clear they can't be pressed.
   - Coloured text (green, amber, red status tags, links and the club colours) stays as it is.
7. **NG_Regens found where it really is.**
   - FMCC recognises an NG_Regens install by its face folders and face images, not only by one settings file.
   - It checks the graphics folders of FM26 and FM27, under Documents and OneDrive Documents.
   - It also recognises the NG_Regens Manager program itself, when it's installed in Program Files or AppData.
8. **"Find it automatically" button.** Shown on NG_Regens wherever FMCC says it isn't installed: the Player faces banner, Packs to download in setup, and Downloads you need.
   - It searches the FM folders, Documents, OneDrive, Program Files and AppData, and finishes within seconds.
   - When it finds the faces, the banner changes to "Installed ✓" and Player faces uses that folder.
   - If it finds several copies, FMCC uses the one with the most faces and says which folder it chose.
9. **"Choose it myself".** If the search finds nothing, you can pick the NG_Regens folder yourself.
   - FMCC checks the folder really holds faces before accepting it, and says so in plain words if it doesn't.
   - The chosen or found folder is remembered for that career and checked again on each visit. If it moves or is deleted, FMCC says so and offers both buttons again.
10. **Seed a Surname uses your whole database.**
   - On every save read, FMCC keeps a separate list of every low-profile player in the save: free agents, players aged 18 and under, fringe players with under 90 minutes this season, and low-ability players. It draws from both save readers, not the 4,000-player scouting snapshot.
   - With around 500,000 players loaded, every slot should be filled.
   - The same rules as now still apply: your club's players are left out unless you ask, and established players are never touched. Each person can only be seeded once.
   - Players and staff are matched to your chosen nationalities, positions or jobs, and age groups, as now.
11. **Staff read from three places, in order:**
   - the main save reader's staff list, which supports FM27 staff jobs;
   - if the save's staff can't be read, FMLibreEditor's list of every staff member in your running FM27 game, when FM is open with the save loaded;
   - if neither is available, a plain message saying which to try, such as "Open FM with this save loaded, then press Create again".
   Board members, managers and anyone without a contract are still never picked.
12. **Clearer results.** After Create, a line shows how many players and staff were found to choose from, such as "Chose from 61,240 low-profile players and 8,912 staff". If any slot is still empty, it says exactly why, such as "no low-profile Welsh goalkeepers aged 18-21", rather than a general message.
13. **Your club's logo in the top bar.** The badge next to the club name shows the club's logo from your installed logo pack instead of initials like "WR".
   - FMCC finds the logo by the club's ID in the logo pack inside your FM graphics folder, the same folder Logos & kits already uses.
   - If no logo is found, the initials stay as they are now.
   - Switching careers shows that career's club logo.
14. **Defaults for new games.** A new "Defaults for new games" section in Settings saves settings you want in every career you start from now on.
   - **What can be saved:**
     - Punish a Club penalties;
     - Seed a Surname setups;
     - which features are on or off;
     - appearance and text size;
     - the rules for Dynamic Potential, Elite Training and Breakout Player.
   - **Save from your current career:** one "Save as default" action per area copies what you've set up in the current career. Each area also has "Clear default".
   - **In setup:** when you start a new career, a "Your defaults" step lists each saved default with a switch, all on. Switch any off for that career only.
   - **Punish a Club and Seed a Surname wait for the first save read, then apply.**
     - A club penalty only applies if that club exists in the new save, matched by name and country.
     - Seed a Surname runs with the saved setup on the players and staff of the new save.
     - Anything that can't apply gets a bell notice saying why, such as "Rival FC isn't in this save".
   - **The rest apply from the start:** features, appearance and rules are used as soon as the new career is created.
   - Existing careers never change when you save or clear a default.
15. **OpenAI key that works.**
   - The key test picks the best model your OpenAI account can use: first the current Director of Football model, then the next newest ones in order. The chat then uses that model, and the page header shows it, for example "GPT-5.2 · your OpenAI key".
   - Each failure gets its own message in plain words:
     - "OpenAI didn't accept this key. Copy it again from platform.openai.com."
     - "Your OpenAI account has no credit left. Add credit and try again."
     - "FMCC couldn't reach OpenAI. Check your internet connection or firewall."
     - "This key works, but your account can't use any of FMCC's chat models yet."
   - The key is saved only on your PC, never shown again after saving, and never sent anywhere except OpenAI.
   - The same fix applies to the key step in setup and the key card in Settings.
16. **Add the key on the chat page.** While no working key is connected, the chat page shows a key box with "Check and connect" instead of "Add your OpenAI key in Settings".
   - Once connected, the box disappears and the chat is ready straight away.
   - Replacing or removing the key afterwards stays in Settings.
17. **Rules and privacy unchanged.** Eligibility, schedules, rewards, grades and search filters stay as they are. CA/PA is never shown.

## User flow
1. Open any of the four pages, or run a search in Scout Players.
2. The content or results appear as normal, with all text in soft white on dark themes.
3. If some data couldn't be read: the same content with "No … yet" markers or a "players left out" note.
4. If something still failed: a plain message with "Try again". Pressing it retries without leaving the page.

## UI/UX feel
- Same pages, tabs, tables and styling as now. The loading bars only show while FMCC is actually working.
- Soft white text everywhere on dark themes. Light themes keep their dark text unchanged.
- Notes and errors use the existing amber note style, in one or two short sentences, placed just above the table or results.
- On mobile, messages and the "Try again" button sit full width above the content.

## Implementation phases
- **Phase 1 (built now):**
  - every FM position style is read;
  - squad pages keep players with odd or missing details;
  - scouting results leave out unreadable players, with a count;
  - these four pages and Scout Players' searches always finish, with a plain message and "Try again" on failure;
  - automatic checks can't block a page;
  - every other page using the same loading bars or the generic error gets the same "message and Try again" treatment;
  - all grey text becomes soft white on every dark theme;
  - NG_Regens recognised by its face folders across FM26 and FM27 folders, with "Find it automatically" and "Choose it myself", remembered per career;
  - Seed a Surname picks from every low-profile player in the save, reads staff from the save or the running game, and explains any empty slot;
  - the club logo from your logo pack in the top bar;
  - "Defaults for new games" in Settings, a "Your defaults" step in setup, and Punish a Club and Seed a Surname applying after the first save read;
  - an OpenAI key test that falls back to the best model your account can use, with clear failure messages, plus a key box on the chat page while no key is connected.
- **Phase 2:** a "Data check" line on these pages, such as "23 of 26 players have readable season stats". Tapping it lists the players FMCC couldn't fully read.
- **Phase 3:** plain-word grade bands on Breakout Player and Scout Players, such as "Excellent season", with a short breakdown of each grade.

## Assumptions
- The same fix applies to the Windows program and the browser preview. The exact player details that break your Wrexham 27 save can only be confirmed once the new Windows build runs on your PC. The preview uses sample data.
- "Left out" in scouting means the player doesn't appear in that search's results. He still exists in your save and can appear once a later save read gives FMCC readable data.
- Players in your own squad are never left out of squad pages. Only their unreadable details are blank.
- Missing details are never guessed.
- Error messages give the reason in plain words, without technical detail. The full detail goes into FMCC's log file.
- "Soft white" is a slightly warm off-white (close to #E8ECF2), used for all body and secondary text on dark themes. The high-contrast setting keeps its pure white.
- Text-size settings and per-career appearance settings stay as they are.
- Only NG_Regens gets the automatic search for now. Real Name Fix, logo and kit packs keep their current checks.
- The search never moves, copies or changes any files. It only reads folder names and counts face images.
- "Install it" stays available as a separate choice. Finding an existing install hides the install prompt.
- In the browser preview, the search runs on sample folders. The real search only runs in the Windows program.
- The low-profile player and staff lists are kept only on your PC, with names, ages, nationalities, positions or jobs and clubs. Ability stays internal, as it does everywhere else.
- The live staff list from the running game is used only when the save's own staff list can't be read, and only while FM is open with the same save loaded. It never changes anything in the game. Renaming still happens through the existing apply step.
- Building the low-profile list makes each save read a little longer, roughly a few extra seconds for 500,000 players.
- "New career" mode, which creates new people in a file, is unchanged.
- The logo shows only in the Windows program, where your logo pack is. The preview keeps the initials.
- Defaults apply to careers started with FMCC's setup, including "Run setup again". They don't apply to careers that already exist.
- Club penalties in a default are matched by club name and country. If several clubs match, FMCC asks in a bell notice which one to use rather than guessing.
- Punish a Club and Seed a Surname defaults follow the same rules as now. Review before applying, if it's turned on for that career, still applies.
- Only one set of defaults is kept. Saving an area again replaces that area's default.
- The model fallback order is: the current DOF model, then GPT-5.2, then GPT-5.1, then GPT-4.1. The chosen model is remembered with the key and checked again whenever the key changes.
- The browser preview keeps using the Emergent universal key. Your own key is only used in the Windows program.
- Automatic checks keep their current timing:
  - Breakout: May or June saves, once per season;
  - Elite Training: January and September saves;
  - Dynamic Potential: winter and season-end reviews.
