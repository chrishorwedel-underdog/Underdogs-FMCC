# FMCC: Seed Your Surname into Football Manager

Seed Your Surname adds your own surname (or several) to Football Manager's name pool. The game then uses it for newly generated youth players ("newgens") of the nationalities you choose.
It creates low-ability people who carry the surname, for a new career on FM26 and FM27. On a running FM27 save it can also rename existing people.

## Who it's for
- You, whose surname isn't in the game and who wants to see it on future youth intakes.
- Any FMCC user who wants a family name, friends' names or a club's surname tradition to appear in their careers.

## Core features and experience

### How FM picks newgen names (shown to the user in one line)
- FM builds newgen names from the real people already in its database for each nationality: players, staff, referees and journalists.
- The more people of a nationality who carry a surname, the more often newgens of that nationality get it.
- So FMCC seeds the surname by adding people who carry it. Seeding doesn't guarantee a newgen gets the name; it raises the odds.

### 1. Choose the surname(s)
- Enter one or more surnames, up to 5.
- Each surname can be checked against your save: "Not found in this save", or "Already used by 3 people".

### 2. Choose nationalities and how many people to create
- **Add nationalities:** search and add as many as you like, for example England, Ireland and Scotland.
- **Set the numbers:** for each nationality, choose how many people to create in each category:
  - **Players:** low-ability free agents or youth players
  - **Staff:** coaches, scouts and physios without a club
  - **Referees**
  - **Journalists**
- **Shortcuts:** quick presets of Light (10 per nationality), Strong (40) and Very strong (100) set every category at once, and you can then adjust each number.
- **"All" buttons:** turn every category on or off for one nationality, or for all of them.
- **Live total:** shows something like "Creating 180 people across 3 nationalities".
- **Strength meter:** gives a plain hint for each nationality. Around 50 or more people with the surname makes it a common name for that nation; a handful makes it rare. This is shown as guidance, not a promise.

### 3. Who gets created
- **First names:** typical first names for each nationality, so the people look natural, for example "Liam Underdog" for Ireland or "Jack Underdog" for England.
- **Gender:** all seeded people are men. Women's names would also feed men's newgens.
- **Birth details:** every person gets the chosen nationality, a believable birth date for their role, and a birthplace in that country.
- **Seeded players:**
  - They get low, randomised attributes and potential, so they never become stars and never change the competitive balance.
  - They are a mix of free agents and youth players at lower-level clubs of that nationality.
- **Staff:** they get low, randomised ability and no club.
- **Referees and journalists:** they get typical low values.

### 4. Two ways to apply it
1. **New career (FM26 and FM27, recommended):**
   - FMCC makes an editor data file that creates all of these people.
   - When you start a new career, you pick the file from the database list at the top right.
   - Names added this way stay in the pool for that whole career.
2. **Current save (FM27 only):**
   - FMCC can't add brand-new people to a running save. Instead it renames existing low-profile people of each chosen nationality to carry the surname: unattached staff, retired players, journalists, referees, and unattached or youth players with very low ability.
   - Their first names stay; only their surname changes.
   - These go into the pending-changes queue with the usual backup, preview, confirmation, read-back check and undo.
   - If the save has fewer suitable people than you asked for, FMCC tells you how many it could find.
   - Whether renames in a running save change the newgen name pool is unconfirmed, so it's on the Test checklist.

### 5. Saved seedings
- Each seeding is kept in history, with its surnames, nationalities, counts and the date it was made.
- Any seeding can be downloaded again or removed. Removing one deletes FMCC's file from the editor data folder and withdraws any queued renames.
- A short summary is shown before anything is made, for example: "Underdog: 40 players, 20 staff, 10 referees and 10 journalists for England and Ireland (160 people)".

## User flow
1. Open **Player & Teams Editor → Seed a Surname**.
2. Type the surname. FMCC shows whether it is already in your save.
3. Add nationalities and set the number of players, staff, referees and journalists for each, or pick a preset.
4. Check the summary and the strength meter.
5. Choose **Make the new-career file**, and pick it from the database list when you start a new career. Or, on FM27, choose **Queue renames on my current save** and approve them in Game changes.
6. Over the following seasons, youth intakes of those nationalities can include players with the surname.

## UI/UX feel
- The same dark FMCC style, as a new tab inside Player & Teams Editor. There's no new sidebar entry.
- A clean table with one row per nationality and one column per category, using number steppers and "All" toggles.
- A strength meter per nationality, from "Rare" (amber) through "Common" (green).
- Plain-English notes everywhere and no technical terms. Notes about what is unconfirmed use amber, never alarms.

## Implementation phases
- **Phase 1 (built now, MVP):**
  - the Seed a Surname tab
  - checking a surname against the save
  - nationalities with counts for players, staff, referees and journalists, plus presets and "All" toggles
  - typical first names per nationality, and low randomised ability for players and staff
  - the summary and strength meter
  - the new-career editor data file (downloaded in the browser preview, placed in the FM folder on Windows)
  - FM27 current-save renames through Game changes
  - saved seedings with removal
  - a new Test checklist item

  It is all checked in the browser preview with the sample save.
- **Phase 2:**
  - You test on your PC.
  - Confirm FM26 and FM27 accept the file and that the surname appears in newgens.
  - Adjust the default counts based on what you see.
- **Phase 3:**
  - first-name seeding, so your first name is used too
  - seeding a whole family, such as several surnames weighted differently
  - sharing a seeding file with friends

## Assumptions
- FM builds newgen names from the people in its database for each nationality. This comes from Sports Interactive community guidance, not from official documentation, so the effect is described as "more likely", never guaranteed.
- You chose both ways to apply it. Creating new people only works through the new-career file. On a running save, FMCC can only rename existing people, which you said is acceptable.
- All four categories (players, staff, referees and journalists) are available, and you choose the count for each nationality.
- First names are typical for each nationality, chosen by FMCC. All seeded people are men.
- Seeded players and staff have low, randomised ability and potential, so they don't affect the game.
- Up to 5 surnames, and up to 500 people per seeding. That keeps the file and the queue manageable, and you can make more seedings.
- The preset counts (10, 40 and 100) and the rough "about 50 makes it common" guide come from community advice and may be adjusted after your PC test.
- The editor data file is FMCC's own XML. Whether FM accepts it is confirmed only on your PC, and goes on the Test checklist alongside the Punish a Club file.
- In the browser preview, the file is made for download and renames are applied to the sample save only.
- Names can't be removed from a career once it has started with the file. Removing a seeding only affects future careers and any changes still waiting in the queue.
