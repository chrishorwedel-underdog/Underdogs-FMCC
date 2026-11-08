# Saved Presets and Updatable Name Lists for Player Creator

Player Creator lets users save their own batch settings as named presets and reuse them in any career.
FMCC's built-in names can also be topped up with name-list updates that FMCC publishes, and the added names mix in with the built-in ones.

## Who it's for
FM players who make new careers with created players. They want their usual batch setups one click away, and they want name variety that keeps growing without them editing files by hand.

## Core features and experience

**Saved presets**
- "Save as preset" stores the current form (count, nations, ages, ability, height, positions, ethnicities, skin range, face matching) under a name the user picks.
- Saved presets show up next to the built-in ones (Academy intake, Wonderkids, and so on), marked "Yours", in every career.
- Users can rename, overwrite with the current settings, or delete their presets. Built-in presets can't be changed, but they can be saved as a copy.
- If a saved preset names a country FMCC no longer knows, the preset still loads. That country is left out, and a note says so.

**Layered name lists**
- Names come from two layers, combined for each country:
  1. Built-in names that ship with FMCC.
  2. Name-list updates published by FMCC. These are added to the built-in names and never replace them. Duplicate names are only counted once.
- Each country's name count shows how many names come from each layer, for example "Senegal: 24 built-in + 40 from update".
- A country that gets names from an update stops borrowing from its closest neighbour's list.
- "Check for name updates" compares the installed list with the latest published one. It shows what's new (countries added, names added) and installs it only after the user confirms. The previous version is kept so it can be rolled back.
- Players already created keep their names. The new names only affect batches made later.

**Working alongside the sortitoutsi Real Name Fix**
- The Real Name Fix changes the names of clubs, competitions, awards and stadiums. It doesn't contain names by nationality, so it can't fill FMCC's name lists.
- FMCC and the Real Name Fix sit side by side without touching each other's files:
  - The fix lives in the game's database folders.
  - FMCC's created-player files go into editor data under FMCC's own file name.
  - FMCC never deletes, moves or changes the fix's files.
- FMCC's name updates are built and published by FMCC. They are not copied from sortitoutsi.

## User flow
1. Open Player & Teams Editor, then Creator. Pick a preset or fill in the form.
2. Click "Save as preset" and name it. It's now available in every career.
3. Optionally click "Check for name updates", review what's new, then confirm or skip.
4. Preview the batch. Each name shows which layer it came from. Then create.

## UI/UX feel
- The same style as the current Creator tab. "Yours" presets appear in the existing preset row with a small tag.
- The name-update panel works like the existing release-download box. It says plainly when no update channel is set up yet.
- Every action gets a short confirmation. Deleting a preset asks first.

## Implementation phases
- **Phase 1 (built now, MVP):**
  - Save, rename, overwrite and delete presets, available in every career.
  - The two-layer name list with per-country counts and a per-name source tag.
  - "Check for name updates" with preview, confirm and roll back.
- **Phase 2:**
  - A personal layer on top, so users can add or hide names for any country themselves.
  - Export and import presets as a file to share with friends.
- **Phase 3:**
  - Add names from a list the user supplies, such as a spreadsheet of names per country.
  - Warn when a created player's name matches someone already in the user's game database.

## Assumptions
- Presets are stored per FMCC install, not per user account (FMCC has no accounts).
- Name updates use the same publishing channel as the Windows installer download. That channel isn't set up yet, so until it is, the update check says "not set up yet" and only built-in names are used.
  - In this browser preview, the update check is shown with a sample update file, clearly labelled as a sample.
- An update can only add names or countries. It never removes built-in names.
- Names that match famous real players aren't added to FMCC's published lists, so batches don't accidentally create a real star.
- Nothing is verified in the real game until it's tested on the user's PC.
