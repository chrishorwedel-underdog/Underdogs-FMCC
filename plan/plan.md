# FMCC Polish Round: Easier Lookups, Branded Comparisons, Tidier Layout

A round of improvements to FM Command Centre that makes stats easier to look up and tidies the layout.
It brands the Radar Compare card, adds a weekly "What changed" summary, adds Watchlist alerts and moves the download button into the footer.

## Who it's for
Football Manager players using FMCC alongside their save, in the browser preview and in FMCC for Windows.

## Core features and experience
1. **Stat lookup in Ctrl K search**: typing a stat name or its short form (for example "xA", "npxG" or "tackles") shows matching stats in the search results. Picking one opens the stat glossary at that stat.
2. **Glossary shows where each stat is used**: every glossary entry lists the screens that show that stat (for example Scout Players, Squad or Club Analysis). Each screen name is a link that goes there.
3. **Club-branded Radar Compare card**: the saved or printed card shows your club crest, club name and club colours. If the save has no colours yet, the card uses the current FMCC theme colours.
4. **Fix Print firing twice**: one click on Print on the Radar Compare card opens the print window once.
5. **Replace the last "Loading…" texts**: the remaining screens that still show plain "Loading…" text get shaped placeholders instead, matching the rest of the app.
6. **Weekly "What changed" panel on Home**: shows what has changed since your last visit:
   - players whose ratings rose or fell, using scouting views only (real CA/PA are never shown)
   - contracts that started, were extended or are now ending soon
   - FMCC changes that were applied to the save (for example Dynamic Potential reviews, edits and punishments)
   - each item links to the player or screen it is about, and the panel can be collapsed.
7. **Watchlist alerts**:
   - a star or "Watch" button on any player (Scout Players, Squad and player profiles) adds them to your watchlist.
   - you get a bell notice when a watched player's grade, value or contract status changes. Contract status covers a new deal, entering the last 6 months, free agency or a transfer.
   - a Watchlist view in Scout Players lists everyone you watch, with their latest change. You can remove anyone from there.
   - your watchlist is kept for each career. Watched players' changes also appear in the "What changed" panel.
8. **White group names in the left menu**: the group headings (My Club, Player Development, Recruitment, Reports, Utilities) turn white so they are easier to read. In high-contrast mode they stay as readable as they are now.
9. **Finance strip lines up with the page box**: the finance strip becomes exactly as wide as the "What this page does" box, with its five boxes spaced equally across the full width. On phones it keeps scrolling sideways in one line.
10. **Close the "What this page does" boxes completely**:
    - each box gets an X that hides it on that screen.
    - Settings gets an on/off switch, "Show 'What this page does' boxes". Turning it on brings back every box you closed.
    - this is remembered for each career.
11. **Smaller download button in the footer**: the large "Download FMCC for Windows" box leaves the page and becomes a small "Download for Windows" link in the bottom footer, next to Project Safety, Downloads, Appearance and Features.
    - hovering over it shows the version, release date, file size and build status.
    - the note "The installer isn't code-signed yet, so Windows may say it protected your PC. Choose More info, then Run anyway." no longer shows anywhere on its own. It appears only after the download button is clicked, as a short message that stays until you close it, while the download starts.

## User flow
- Press Ctrl K anywhere, type "xA" and pick "Expected assists". The glossary opens on that stat and lists the screens that show it. Click "Scout Players" to go there.
- In Scout Players, star a player to watch them. When their value, grade or contract changes after the next save read, the bell shows a notice that links to the player.
- Open Home and read the "What changed" panel for this week's rises, falls, contracts, applied changes and watchlist news.
- Open Radar Compare, add players and save or print the card. It now shows your crest and club colours, and Print opens once.
- Close a "What this page does" box with its X. To bring the boxes back, or to switch them off everywhere, use the switch in Settings.
- Click the small download link in the footer. The installer starts downloading, and a short message explains what to do if Windows says it protected your PC.

## UI/UX feel
These changes follow the existing FMCC look, themes, kit accent, text size and accessibility settings. The menu group names become white but stay small. The finance strip and the page box line up along the same edges. The footer download link uses the same small style as the other footer links, with a green dot when a fresh build is available. The "What changed" panel and watchlist use the same card style and red, green and gold meanings as the rest of Home.

## Implementation phases
- **Phase 1 (built now)**: all eleven items above.
- **Phase 2**: a weekly digest bell notice or email, a digest history you can look back through, and custom alert rules per watched player (for example "only tell me if value drops below £5m").
- **Phase 3**: Radar Compare card style choices (light, dark, kit) and one-click sharing of the card image.

## Assumptions
- The "What changed" panel covers the period since your last visit, up to a maximum of 7 days. It only shows changes FMCC saw when reading your save; nothing is estimated. In the browser preview it uses sample data, which is labelled as sample.
- Rating rises and falls in both the panel and watchlist alerts use FMCC's grades and scouting views only. Real CA/PA are never shown.
- Watchlist alerts trigger on any change in grade of 2 or more points, a value change of 10% or more, or any change in contract status. Watchlist changes are checked each time FMCC reads the save.
- The existing Scout Players shortlist stays as it is. The watchlist is separate and only drives alerts.
- Closing one box hides it only on that screen. The Settings switch controls all boxes, and turning it back on brings back every box you closed. The setting is saved for each career.
- The crest and club colours come from the save when FMCC can read them. Otherwise the theme colours and the club's initials badge are used.
- Stat lookup shows at most 5 stat results so screen and player results stay visible.
- The footer download link only shows where the download box shows today, so it stays hidden where downloading isn't offered.
- The "Print twice" problem will be fixed on both the browser and Windows versions. Windows behaviour can only be confirmed on a Windows PC.
- Everything here is built in preview. Production stays as it is until you publish again.
