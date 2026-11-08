# One-Time Code Download Link, Then Push to GitHub as "Underdogs-FMCC"

Emergent has no zip download, so FMCC's preview gets a temporary link that downloads the project's code as one zip, with keys left out.
The owner unzips it and pushes it to a new public GitHub repository called Underdogs-FMCC, which starts the automatic Windows installer builds.

## Who it's for
- The owner (Pro plan, computer browser, Windows PC), who can't find Save to GitHub and wants the code on GitHub.
- FM players visiting the website, who will download FMCC-Setup.exe once releases exist.

## Core features and experience
**The download link**
- A single link to a zip of FMCC's code (`Underdogs-FMCC-source.zip`), shared in the chat. It isn't shown anywhere in FMCC's screens or on the published website.
- The link carries a long random code, so it can't be guessed. It stops working after 24 hours, and any extra copies can be made on request.
- What's inside:
  - All of FMCC's code and data files, including the hidden `.github` folder that builds the installer.
  - The `release` name list, the docs and `.gitignore`.
- Left out:
  - Keys and private settings (`.env` files).
  - The test login file, test reports and the preview sandbox folders.
  - Installed packages (`node_modules`) and build caches. GitHub's build installs these itself.
- Before the link is shared, the zip is checked to confirm that no `.env` file or key-like value is inside.

**Pushing it to GitHub (owner, one time)**
1. Install Git for Windows (git-scm.com) with the default options.
2. On github.com, create an empty **public** repository named **Underdogs-FMCC**. Leave README, .gitignore and licence unticked.
3. Open the link, save the zip, and unzip it to a folder such as `Documents\Underdogs-FMCC`.
4. In that folder, type `cmd` in the address bar, then run these commands, with your GitHub username in place of YOUR-NAME:
   ```
   git init
   git add .
   git commit -m "FMCC first upload"
   git branch -M main
   git remote add origin https://github.com/YOUR-NAME/Underdogs-FMCC.git
   git push -u origin main
   ```
5. Sign in to GitHub in the browser window that opens.

**After the push**
- The installer build starts on GitHub by itself. A few minutes later, release v0.2.1 with FMCC-Setup.exe appears under **Releases**. The **Actions** tab shows progress or errors.
- The builder opens the secure keys card for `YOUR-NAME/Underdogs-FMCC`. After the website is re-published, the download button shows the version, date and size.

**Later updates**
- Ask the builder for a fresh link and unzip it over the same folder, so the hidden `.git` folder stays.
- Then run `git add .`, `git commit -m "FMCC update"` and `git push`. Each push makes a new release.
- If the Save to GitHub button appears later, it replaces these manual steps.

## User flow
1. The builder shares the download link in the chat.
2. The owner installs Git, creates the empty repository, unzips the code and runs the commands.
3. The owner checks Actions, then Releases, and tells the builder it's done.
4. The owner enters `YOUR-NAME/Underdogs-FMCC` in the secure card and re-publishes the website.
5. The download button goes live.

## UI/UX feel
- No change to FMCC's screens. The link is a plain file download in the browser.

## Implementation phases
- **Phase 1 (now, MVP):**
  - The temporary code-download link, with keys and test files left out and checked.
  - Push guidance.
  - Setting the release repository through the secure card.
  - Fixing the first GitHub build if it fails.
- **Phase 2:**
  - "What's new" from the release notes under the website's download button.
  - A download count.
- **Phase 3:**
  - Code signing to remove the Windows warning.
  - Separate test builds.

## Assumptions
- The link is served from the preview app, which must be running when it's opened. It lasts 24 hours.
- Sharing the link in chat is acceptable, because the same code becomes public on GitHub anyway. Keys are never in the zip.
- The repository is Underdogs-FMCC (a hyphen instead of the space), public, on main, and created empty.
- The app keeps the name "FMCC". Only the repository is called Underdogs-FMCC.
- The owner uses Windows and the Command Prompt.
- Installing on the owner's PC remains unverified until the first real installer is tested.
