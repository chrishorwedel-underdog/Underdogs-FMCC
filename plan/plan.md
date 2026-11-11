# "New version ready" notice in FMCC for Windows

When a newer FMCC installer is published, the Windows program says so with a small, quiet card in the bottom corner, and you can update in one click.
It builds on the existing footer version tag and its update dot, which stay as they are.

## Who it's for
Football Manager players using the installed FMCC for Windows who want to know when there's a newer version without having to check the website.

## Core features and experience
- **Check at start.** Each time FMCC opens, it checks once whether a newer installer is on the Download button. It doesn't check again while it stays open.
- **Small corner card.** If a newer version exists, a small card appears in the bottom corner a few seconds after the app shows. It contains:
  - "FMCC v0.2.x is ready" and "You have v0.2.y"
  - up to three short lines on what changed, taken from the release notes
  - **Update now**, which downloads the installer, closes FMCC, installs it and opens FMCC again (the existing one-click update)
  - **Not now**, which closes the card
- **Reminder after a day.** After **Not now**, the card stays hidden for 24 hours. The next time FMCC opens after that, the card shows again if the update still hasn't been installed.
- **Footer dot stays.** The dot next to the version in the footer still shows until you update. Clicking it opens the same update prompt as before.
- **Quiet when there's nothing new.** No card and no dot when you're on the newest version, or when FMCC can't reach the internet. A failed check is never shown as an error.
- **Website stays the same.** The card only appears in the installed Windows program, never on the website.

## User flow
1. Open FMCC. The app loads as usual.
2. If a newer version is out, the small card slides in at the bottom corner.
3. Press **Update now**. FMCC downloads the installer, closes, installs it and reopens on the new version, with your data kept. Or press **Not now** and carry on.
4. If you chose **Not now**, the card shows again the first time you open FMCC a day or more later. The footer dot reminds you in the meantime.

## UI/UX feel
- A compact card in FMCC's dark style with a soft entrance and a thin accent edge. It doesn't block the page or need an answer.
- Calm wording, no technical terms, and one clear main button (**Update now**).
- It sits above the footer and away from page content, and fits on small windows.

## Implementation phases
**Phase 1 – MVP (built now)**
- One check for a newer version when FMCC starts.
- The bottom-corner card with what changed, **Update now** and **Not now**.
- **Not now** hides the card for 24 hours. This is remembered for each version, so a newer release brings the card back straight away.
- The existing footer dot and update prompt stay as they are.

**Phase 2**
- A full "What's new" page listing the changes in every version since the one you're on.
- A Settings switch to turn the corner card off, keeping only the footer dot.

**Phase 3**
- Optional automatic updates that install the new version the next time FMCC closes.
- A choice between stable releases and early test releases.

## Assumptions
- "Newer installer" means a newer version on the same release page that the website's Download button uses. A build still in progress, or a failed one, doesn't count.
- The 24-hour reminder is checked when FMCC opens. If FMCC is left open for more than a day, the card doesn't reappear until the next start, as there's only one check per start.
- If no release notes are available, the card shows only the version numbers.
- **Update now** relies on the existing one-click update. It hasn't yet been confirmed end to end on a real PC.
- The website, and copies of FMCC not installed from the installer, never show the card.
- The card isn't added to the notifications bell list.
