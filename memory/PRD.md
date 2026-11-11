# FMCC — PRD

## Original problem statement
Build the FM Command Centre (FMCC): an all-in-one Director of Football companion for Football Manager 26/27 that reads saves, plans across six linked modules (Squad Management, Squad Development, Scout Window/Moneyball, Monthly Reports, Elite Training, Annual Breakout/Dynamic Potential), and later writes decisions back into the game. It uses tools such as fmsave, FMLibreEditor, FMMatchLens and BepInEx, and gives credit to FM Player Analyzer. Identity continuity uses the game's unique IDs, never names alone. Histories are append-only. Data uses verified backups. Full plan: /app/plan/plan.md. Approved mockup: /app/plan/mockup.html.

User choices (stage 1): build Stage 1 as planned; use a sample squad for the save reader; browser preview only, no Windows installer yet; tighten the sidebar so "Ask your DOF" always fits.

## Architecture
- FastAPI (`/app/backend/server.py`) + MongoDB, React (CRA + react-query) frontend.
- `sample_reader.py`: a SAMPLE save reader shaped like fmsave records. It is MOCKED because fmsave needs Python 3.12 and real saves.
- `dashboard.py`: computes the Home screen (4-3-3 Best XI, weak spot, U21 minutes, changes since the last save, contracts, weeks to season end).
- `updates.py`: live GitHub releases check for fmsave, FMLibreEditor, FMMatchLens and BepInEx. FMCC's repo comes from the `FMCC_RELEASE_REPO` env, which is not set yet.
- Collections: settings, careers, identities (career_id + unique_id), snapshots (one per save read), backups (sha256-verified full copy), components.
- No login (single-user desktop program).

## User personas
One FM manager on Windows who runs long careers.

## Core requirements (static)
See /app/plan/plan.md (stages 1–4, phases 2–3).

## Implemented (2026-11-08) — Stage 1
- First-run setup wizard: find FM (sample), match analytics (later), career name, OpenAI key (later), then a health check.
- Career profiles (FM26/FM27): create, switch and edit the save folder.
- Save reading through the top-bar refresh button. Each read takes an automatic verified backup first and is guarded against concurrent reads.
- Identity matching by game ID: "Same name" tag, "New" tag, "No longer in your squad" list.
- Home dashboard: six cards, Needs your attention, next match.
- Squad table with filters and a player sheet showing ability history.
- Ctrl K command palette.
- Settings: live update check (weekly auto + manual), update now / rollback (records only in preview), auto-install toggle, backups with verify and restore (pre-restore backup), credits.
- Sidebar tightened to fit at 768px height.

## Implemented (2026-11-08) — Stages 2 and 3 (browser preview, sample save)
- Squad: role ratings (14 roles, 0–100), 4-3-3 / 4-2-3-1 pitch with Best XI and Development XI, swap from the depth chart, saved lineups (append-only versions, stale-save and concurrency checks), depth chart, weakest positions, registration check (senior size, homegrown, U21).
- Scouting: about 130 sample players at other clubs ranked by role fit, potential, age and value; shortlist (append-only); Moneyball comparison of up to 4 players with over/under-performance flags.
- Squad Development plans (minutes, loan, CA goal, append-only history). Monthly Reports comparing months.
- Elite Training: nominations, training evidence, PA boosts queued (blocked from being queued twice in a month).
- Annual Breakout: nominations, provisional reviews (revisions), official awards that queue game changes.
- Dynamic Potential: My club / leagues / nations scope with an overlap-safe count, review list, caps, values hidden unless revealed.
- Rules tab in every module: plain-sentence builder or parameter sentences, versions/history, reset, export/import, Test this rule.
- Stage 3: change queue, Ask me first / Apply automatically per source, a verified backup before each batch, background batches with progress, pause/resume, undo, audit trail, idempotency keys. The game editor is the SAMPLE editor (MOCKED): changes reach the sample save on the next read.

## Implemented (2026-11-08) — Stage 4 (browser preview)
- Matches: one-click FMMatchLens + BepInEx install (MOCKED: install simulated, matches are SAMPLE FMMatchLens-shaped data, 4 per save read), match summary, xG timeline, momentum, chalkboard (shots, passes, defensive, heat map) with team/half/player/pass-type filters and hover details, player match cards, season per-90 table with trends. Replays: disabled button (FMMatchLens viewer in the Windows program).
- Match evidence: 'Seen vs us' opponents in Scouting, per-90 fields (xG, xA, key passes, pressures, defensive actions) in every rule builder.
- DOF chat (REAL): OpenAI gpt-5.6-terra via the Emergent universal key in the preview (OPENAI_API_KEY env overrides it). Streaming, typing indicator, saved per-career conversations, suggested questions, squad/plans/matches/scouting context, drafted actions (lineup, shortlist, nomination, plan) saved only on Accept, never reveals Dynamic Potential values.

## Implemented (2026-11-08) — Windows program build setup (not yet run)
- `.github/workflows/windows-installer.yml`: on a Windows GitHub runner it builds the screens, packages the server with Python 3.12 + fmsave 0.10.0 + MongoDB mongod.exe + pywebview using PyInstaller, and builds `FMCC-Setup-<version>.exe` with Inno Setup (artifact; a release on `v*` tags). Preview .env files are deleted before the build.
- `desktop/launcher.py`: starts the local database in %APPDATA%\FMCC, the server on 127.0.0.1:8765 serving the built screens, and the program window.
- `backend/fmsave_reader.py`: real save reader (UNVERIFIED with real saves). It reads the newest .fm in the career's folder and skips an unchanged file. Real-mode FM folder detection.
- The desktop mode hides the sample banners and adds an OpenAI key field (stored in %APPDATA%\FMCC\config.json).
- Not built: FMMatchLens .fmlens archive reading and the real BepInEx 6 + FMMatchLens install (format undocumented; FMMatchLens needs BepInEx 6 IL2CPP bleeding edge, not the 5.x release tracked in Updates), the real FMLibreEditor writes, a save-folder watcher, code signing.

## Implemented (2026-11-08) — Match add-on, automatic save reading, live game changes, original sidebar
- Connections screen (`/connections`, `backend/connections_api.py`, `fm_game.py`): finds Steam FM, shows BepInEx 6 / FMMatchLens plugin / dashboard status, one-click install (FM closed, never overwrites, records every added file, verifies FMMatchLens SHA256SUMS, rolls back on failure), remove exactly those files, BepInEx log check, open dashboard, restart as admin. SIMULATED in the browser preview.
- Automatic save reading (Windows program): watcher in `server.py` reads a save once it stops changing, skips duplicates, notices with a 'Check my save' link; Settings switch (default on).
- Project Safety page: Check my save report (`GET /api/saves/{n}/check`), backups, game-change record.
- Live game changes (`live_editor.py` + `changes_api.py`): exact-change preview (current/new values, checks) then one Apply batch; checks FM27 running, known build, safety checks, same save, verified save-file backup; read-back per change; stops on failure and returns the rest to the queue; undo puts old values back when the same save is loaded; approver and old/new values recorded; append-only audit. FM26 stays read-only. Auto-apply is off in the Windows program. The preview uses the SAMPLE editor. UNVERIFIED against a real game.
- Workflow builds fmlibre-probe (v0.5.0) from source into the installer. Updates list tracks BepInEx 6 bleeding edge.
- Sidebar restored: Project Safety, Appearance (Coming soon) links; Home, Dynamic Potential, Breakout Player, Scout Players, Monthly Reports, Moneyball, Squad, Development, Elite Training, Matches; 'Chat with your Director of Football'. The Awards page was split into the Dynamic Potential and Breakout Player pages.
- Tested: iteration_4 (backend 12/12, frontend flows); the batch-detail layout, the approver label and the newest save selection were fixed afterwards.

## Implemented (2026-11-08) — Player & Teams Editor (first build)
- `/editor` (`backend/editor_api.py`, `pages/PlayerTeamsEditor.jsx`, `components/editor/*`). Faces: reads a user-installed NG_Regens pack (its config.xml), never edits it; upload or remove a face, give a face from NG_Regens to everyone without one (nationality -> folder, automatic when the names match, otherwise you pick the folder), or swap in another NG_Regens picture. FMCC writes its own `graphics/FMCC/config.xml` + PNGs (person uid and r-uid records, club logos). Club logos upload/remove; club renames go into `fmcc_club_names.lnc` (CLUB_LONG/SHORT_NAME_CHANGE); 'Write again' rewrites the files. Every face/logo/name decision is an append-only revision (`branding` collection) with history.
- Club attributes: read through FMLibreEditor (`get club`) in the Windows program, SAMPLE values in the preview; edits are queued as Game changes (entity club, absolute target) and go through the batch preview, checks, backup, read-back and undo. Not editable: owner personality, separate world reputation, club name through the editor.
- Preview uses a sandbox folder (`backend/preview_fm`, gitignored) with a SAMPLE stand-in NG_Regens pack. UNVERIFIED against real FM, NG_Regens or the real .lnc path (looks for data/database/db/<highest>/lnc/all).
- Tested: iteration_5 (14 API tests + UI). Fixed afterwards: the editor mode switch is hidden (club edits always ask), names reject control characters and quotes, 'Another NG_Regens' shows only when a folder exists, the undo label uses the attribute name.
- Logo Creator (2026-11-08): 'Create with ChatGPT' on a club's logo card. GPT Image 1.5 designs an original badge from the club's name (the rename if set), 1-3 colours, a style (classic crest, modern minimal, retro roundel, animal emblem), an optional name on the badge, and notes. The background is made transparent. The draft is previewed on dark and light backgrounds; nothing changes until 'Use this logo'. Tested in iteration_7 (13/13 + regression).
- Licensing fix (2026-11-08, `backend/licensing_api.py`, editor tab 'Licensing fix'). As the user chose: it reads community real-names fix .lnc files (FM's name-file folder = active in FM; imported copies are applied by FMCC) and lists unlicensed clubs (save name != real name) and competitions. It finds real logos in logo packs already in the graphics folder (config.xml club logo records). Apply writes CLUB/COMP name lines into FMCC's .lnc. Manual fix: real name and short name, stadium name (by FM stadium ID, STADIUM_NAME_CHANGE), year founded (a Game change through FMLibreEditor), competition name by ID. Nicknames aren't possible (no lnc command, no FMLibreEditor support). The preview uses a SAMPLE fix file and logo pack. 'Pick face' on every player opens a picker. NG_Regens tab: browse any nationality folder page by page (default is the player's nationality), see which player uses each picture, click to use it. 'Create with ChatGPT' tab: GPT Image 1.5 (Emergent key in the preview, your OpenAI key in the Windows program) draws a draft of a made-up person from the age, nationality and your notes; nothing changes until 'Use this face'. Paths are checked to stay inside NG_Regens; drafts are tied to the player. Tested in iteration_6 (22/22 + regression). Note: the playbook's gpt-image-1 isn't available on the key; gpt-image-1.5 is used.

## Implemented (2026-11-08) — Plan phases 1-3: ScoutSheet + FMDataLab analytics, league strength, graphics tools
- Engine `backend/stats_model.py`: 48 metrics from the user's workbook (FM26_Player_Rating_and_Similarity_Model.xlsx -> `backend/data/opta_leagues.json` 181 leagues, Opta averages 10 Aug 2026, reference 92.789, exponent 1.5; `position_weights.json`). Robust z vs same-position cohort, metric scores, analytical/output raws, reliability, local grade, global grade = 20 + (local - 20) x league multiplier; workbook similarity engine; fair price = median value of 8 nearest (grade, age, contract); confidence by minutes; minutes rule 400 (percentiles, grades) / 900 (fair price); possession adjustment; 8 archetypes (position-limited) + up to 6 custom computed stats; actions per 90; phase scores. SAMPLE match stats in the preview.
- `scout_api.py` (/api/scout): Full / Fair play / Moneyball masking, filters, presets, saved searches (revisions), CSV export, profile, My Club, Deal Finder, Offers, computed stats, tactical in/out-of-possession search, possession table (revisions), scatter, breakdown, role scores, FM HTML import (UID-linked or 'Not linked'), currency/wage prefs, DOF reports from Moneyball numbers (LLM), season history (`stat_history`).
- `leagues_api.py`: matching save leagues by country + name (unsure ones flagged), reputation placement for leagues not on the list, multiplier edits, recalculate preview/apply, list import (xlsx/csv), duplicates. Women's leagues are not adjusted.
- Best XI now uses an optimal assignment (Hungarian) in `roles.py`.
- `graphics_api.py`: kits (upload, ChatGPT with 8 templates, bulk up to 10 clubs), pack browser, staged bulk import (zip/pictures, 5,000 / 500 MB / 5 MB limits, write, per-item undo), pack check (report only). Kits written as club/ID/kits/home|away|third in FMCC's config.
- ScoutSheet listed in Updates (no public repo found; set SCOUTSHEET_REPO to enable checks). Credits updated. Possession from FMMatchLens NOT built (format unknown).
- Tested: iteration_9 (39/43 + UI). Fixed afterwards: HTML rows no longer override save players, cache key uses active imports, 'linked' flag, no grades under 400 minutes, Fair play hides best role and role ratings, archetypes limited to their positions, max-age input clamped, Compare tab respects the view, £0 display, adjusted marker only on adjusted stats.
- Module guides (2026-11-08): every sidebar page (and Project Safety, DOF) opens with a 'What this page does' card listing its features and how it works; it can be collapsed per page. The DOF button text is one size larger and centred.

## Implemented (2026-11-08) — Guided tour, FMST26 / fmOS / FM Dossier ideas, new Home
- Guided tour (`components/Tour.jsx`): 14 steps, starts by itself the first time, can be replayed from the top bar (?) and Settings; it never changes data.
- `backend/lab_api.py`: your own formulas (safe expression parser, chaining with f_, cycle checks, max 30, revisions, import/export) shown in Players columns, Scatter, Quadrant and advanced filters; advanced filter (AND/OR groups, value, stat vs stat, percentile; hidden fields blocked in Fair play/Moneyball); heat colours; quadrant (performance vs cost) on Deals & Offers; Find a replacement and Price explained on profiles; season history chart; Squad 'Tactic fit' (formation or .fmf import, starter/backup/depth per slot, squad gaps linking to Scout Players, shape advisor); DOF sees formulas and gaps.
- Connections 'Other FM apps' card: FM Dossier (official page), FMST26 and fmOS (no official page set yet). Open uses a path you set (Windows program only). Updates list them as 'You update it yourself'. Credits added (no code used).
- Home redesign: welcome band, 3-column equal module cards, two equal bottom panels, one size larger on Home only.
- Tested: iteration_10 (33/35 + Stage 10 regression 42/42 + UI). Fixed afterwards: field whitelist in filters/quadrant, CA/PA sort blocked outside Full view, bad filter values no longer crash, similar players same gender, replacement caps of 0, Squad gap links filter Scout Players, quadrant axis, formula preview reset. Remaining 2 test failures are test-order/revision-count artifacts.
- Known limit: Tactic fit ranks each slot separately, so one player can be the starter in two slots. .fmf reading only finds the formation text; FMST26/fmOS release pages unverified.

## Implemented (2026-11-08) — Smarter Tactic fit, app pages, formula starter pack, setup page
- Tactic fit uses optimal assignment in three layers (starters, then backups, then depth), so each player appears once.
- FMST26 (https://www.fmscout.com/a-fmst-26.html) and fmOS (https://fmos.it/, Windows/Mac app) official pages are linked in Connections and checked in Updates (shows the latest version; you update it yourself).
- Formula starter pack: 10 ready-made formulas in Scout Players > Formulas (Try, Add, Add all; respects the 30 limit and reports skipped ones).
- First-run setup redesigned: bigger logo, title, step cards and card; edition selector and Find button on one line (also on mobile).
- Tested: iteration_11 (14/14 new + 35/35 Stage 11 regression + UI). Fixed afterwards: starter pack limit handling, one-line selector at 390px.

- (2026-11-08) Tactic fit cards add "(club, age N)" next to players whose name appears more than once. Setup: Find Football Manager title and text centred, Find button on the right and green. Self-checked with screenshots (desktop + 390px) and the API.

## Implemented (2026-11-08) — Approved plan: polished setup, smarter DOF, installer + test checklist, Punish a Club
- Setup (`backend/setup_api.py`, `pages/Setup.jsx`): steps Find FM (green ticks for game folder, save folder, save count + newest save; Choose folder if anything fails; club/career names), Match analytics (optional, off), DOF key (real check; Windows saves the key), Health check (save readable, backup folder writable, FM version, FM running; green/amber/red with a fix). Progress is saved and resumed (`setup_progress`, cleared on completion).
- DOF (`dof_api.py`): context includes Tactic fit (starter/backup/depth), squad gaps, formulas with values, transfer budget and candidates per gap (best, affordable, young). New `suggestions` action: cards with gap, reason, numbers, over-budget tag, Add to shortlist, Open profile (`/scouting?player=`). Only real non-own players are kept. New quick prompts.
- Installer: the workflow also builds on push to main; output `FMCC-Setup.exe`. Settings > Testing (`testing_api.py`, `TestingCard.jsx`): 8 PC tests with pass/fail and notes (append-only), unsigned-warning help, Export report (JSON with results and log, personal paths hidden).
- Punish a Club (`punish_api.py`, `pages/Punish.jsx`, sidebar after Player & Teams Editor): club search, 12 penalties with settings, presets Light/Heavy/The full 115, summary, FMCC XML editor-data file (in the preview: download only), queue balance/reputation/training/youth facilities on FM27 (source 'punish'), saved punishments (revisions); removing one deletes its file and withdraws its queued changes. Morale, FFP, sponsors, stadium, points, relegation and embargo are new-career only. The XML format FM expects is UNCONFIRMED (Test checklist item).
- Tested: iteration_12 (23/23 + UI). Fixed afterwards: candidates when grades are missing, affordable candidates, punish source label, withdraw on remove, progress ignored after setup, card styling.

## Implemented (2026-11-08) — Recruitment Lab, countdowns, notification centre
- `backend/recruit_api.py`: stat-based role score (penalised off-position), philosophy (6 traits, editable weights with revisions), character test from personality, 12 indices (luck flag), extra stats (shots, conversion, goals above xG, ball security, passes attempted, contributions, npxG+xA, tackles+interceptions, minutes share), league benchmarks, trend arrows, similar players, pipeline (append-only); Compare (up to 4: profile strips, radar, pizzas, role fit, npxG vs goals); Explore (own/target/pool/shortlist, medians, counts, ranked by role); Shortlist board by 4-3-3 slot (unique starters, move, DOF picks); DOF picks (Dream/Upgrade/Value/Squad player/Prospect, filters, tags, left out). The DOF chat gets the picks for the biggest gap.
- `backend/notify_api.py`: in-game countdowns (windows and season dates estimated), contract expiries, missed months (Make it late = labelled record, or Dismiss), notices (8 types, deduped, read/clear hides only), per-type prefs, sidebar badges.
- Frontend: `components/scout/Recruit.jsx` (Explore, Shortlist board, DOF picks, Compare, ProfileLab in the profile sheet), `components/Notify.jsx` (bell, Up next on Home, PageCountdown on pages, settings), Raw switch in the top bar.
- Tested: iteration_13 (33/34 new + regression + full UI). Fixed afterwards: position-aware role scores, empty compare 422, board move only for shortlisted players, unique board starters, league wording, weight dots, bell closes on outside click.
- Not built: 'new since last save' counts on saved searches; foul/card/distance/header-attempt stats (not in the save data yet); late reports are a labelled record, not a regenerated report page.

## Implemented (2026-11-08) — Download button
- GET /api/setup/download reads FMCC_RELEASE_REPO (owner/repo, backend env) and links to the latest GitHub release's .exe (version, size, date; cached 10 min). Hidden inside the Windows program. Shown on the setup page (front page) and on Home. Until the repo is set, or before a release exists, the button is greyed out with a plain message.
- Releases are published by the workflow when a v* tag is pushed (pushes to main only build an artifact).

## Implemented (2026-11-08) — New league strength list
- `backend/data/opta_leagues.json` rebuilt from the user's `Global_League_Strength_and_Player_Model.xlsx` (copy kept in `backend/data/sources/`): 408 rated competitions (mean Opta club strength, snapshot 6 Nov 2026, research 8 Nov 2026), plus median, quartiles, top-five mean, rated clubs, evidence, tier, type, competition ID and aliases from the Competition Register. 169 unrated competitions are kept under `unrated` (no score, never treated as weak).
- Reference = benchmark mean 92.099 (Premier League). Multiplier formula unchanged: (strength ÷ 92.099)^1.5. Note: the workbook calls the 1.5 exponent "retired" and suggests an additive scenario formula with beta left blank by default; not adopted yet.
- Matching now also uses each competition's aliases (e.g. "English Premier League"). Highland Football League now matches "Highland / Lowland Leagues" instead of being estimated.
- Stage 10 tests updated to the new names and count; 43/43 pass.

## Implemented (2026-11-08) — No-strength-score tag and league comparison
- `leagues_api.no_score()`: every save league gets `scored` and a plain `no_score` reason (women's league; not on the workbook's list; listed in the workbook but unrated, matched within the same country only). Passed to players as `league_scored` / `league_note`.
- "No strength score" tag (with the reason on hover) in the Players table, the player profile (plus a note line), the Leagues table, and DOF pick tags; the profile's league-strength line says "Not known" for these players.
- GET /api/leagues/compare?source=&target=&grade= (save league names or list keys = competition IDs, so same-named leagues like "Premier League" stay distinct): both strengths, multipliers, ranks, gap and %, the grade's global value and the equivalent local grade in the target league, plus the workbook's beta scenarios (0, 0.5, 1) with a caveat. Leagues tab "Compare two leagues" card (swap, grade input); profile link "Compare his league" pre-fills it.
- Self-tested: API checks, screenshots, Stage 10 suite 42/43 (test_offer_verdicts passes on its own; order-dependent flake).

## Implemented (2026-11-08) — Player Creator (new careers)
- `backend/creator_api.py` + `components/editor/CreatorTab.jsx` (new "Player Creator" tab in Player & Teams Editor). Batch generator: count (1–200), weighted nationalities, ethnicity mix (11 FM groups; none = typical for the nation), skin tone range (1–20), age, positions, CA, PA (never below CA), height, preferred foot, a shuffle number (same number = same players). Preview first, then make.
- All created players are free agents; existing players keep their clubs (running careers: names only, as agreed). IDs start at 2,100,000,000.
- Built-in sample name lists for 15 nations; other nations borrow the closest list and the preview says so.
- Faces: NG_Regens picture from the matching nationality folder (unused ones first), written to FMCC's graphics output; batches report how many got faces.
- Output: FMCC XML editor data file (download in the preview; placed in the FM editor data folder in the Windows program). Format UNCONFIRMED; added to the Test checklist ("Created players appear in a new career"). Batches are saved with revisions; removing one deletes its file and releases its faces.
- Self-tested: API (meta, preview, validation, create with 5/8 faces, file, delete) and screenshots.
- (2026-11-08) Name lists: `backend/data/names.json` adds 37 nations (52 total, 12 first + 12 last names each, common names rather than famous players); the closest-list fallback stays for the rest. Typical skin tone per ethnicity when the range is left at 1–20. Presets: Academy intake, Wonderkids, Hidden gems abroad (8 smaller football nations), Veteran free agents, Goalkeeper pool; they fill in the form and can be adjusted. Self-tested with the API and a screenshot.

## Backlog
- P0 Windows packaging: real fmsave reader + FMLibreEditor hidden editor adapters, save-folder watcher, installer (GitHub Actions), real file swap for updates.
- P1: per-90 trends in Monthly Reports; in-app OpenAI key field for the Windows build.
- P2: restore inside a transaction; GitHub token for update checks; user-saved named presets beyond export/import; registration presets per real league.

## Next tasks
- P0: run the Windows build and test it on the user's PC (Connections checks, Check my save, one small FM27 batch).
- P1: Player & Teams Editor (user request): faces built on a user-installed NG_Regens (read its config.xml; FMCC writes its own graphics folder for missing/custom faces), club logos via config.xml, club renames via .lnc files, club attributes through FMLibreEditor (reputation, balance, budgets, facilities, supporters, stadium). Owner personality, separate world reputation and club name writes aren't supported by FMLibreEditor yet; research fm-editor.
- P1: reading .fmlens into Matches once the format is known; live changes beyond PA/CA.
- P2: signed installer; merging Squad and Development; real Appearance settings.
Windows packaging with the real fmsave reader, FMLibreEditor editor and FMMatchLens data.

## 2026-11-08 Saved presets, name-list updates, Downloads you need
- Player Creator: saved presets per FMCC install (`creator_extras.py`, db.creator_presets, soft delete), rename/overwrite/delete, "Yours" tag, unknown nations dropped with a note. Two-layer names: built-in + installed update (db.name_layers) with per-country counts, per-name "update" tag, check/install/roll back. Update channel = `fmcc-names.json` on the FMCC_RELEASE_REPO latest release (not set up); browser preview uses SAMPLE `data/names_update_sample.json`.
- Downloads you need (`extras_api.py`, page /extras, top link "Downloads", compact card in Setup's last step): NG_Regens (needed; starts the NG_Regens Manager installer from Downloads), sortitoutsi Real Name Fix (needed; backs up and swaps dbc/edt/lnc in every db version folder, keeps fmcc_club_names.lnc, copies .fmf to editor data), logo/kit packs (optional; unzipped into graphics with backups of replaced files), FMST26/fmOS/FM Dossier (optional apps, links only), built-in list. Update check: NG_Regens version read from ngregens.org; sortitoutsi blocks automatic checks (403), so it's manual. Packs aren't bundled (third-party rights).
- Tested: iteration_14 and iteration_15 (backend 33/34; the same-second backup clash was fixed afterwards and checked with curl).
- Unverified on Windows: os.startfile for the installer, the real game folder layout (shared/data/database/db), FM27 Real Name Fix availability.
- (2026-11-08) Missing pack reminder: `components/PackBanner.jsx` shows a small banner on Player faces (NG_Regens) and Licensing fix (Real Name Fix) when the pack isn't found, with Get it, Install it / Downloads you need, and a hide button (remembered per pack in this browser). Licensing tab refreshes the pack status after its scan. Self-tested with screenshots (desktop + 390px, NG_Regens missing simulated in the browser).


## 2026-11-08 GitHub + automatic Windows installer releases
- `.github/workflows/windows-installer.yml`: every push to main (or Run workflow) builds on windows-latest, version `v0.2.<run_number>`, writes `release_repo.txt` + `version.txt` into the package, builds FMCC-Setup.exe (Inno Setup), makes `fmcc-names.json` from `release/fmcc-names.json` with the release version, release notes from git log since the last tag + SmartScreen note, publishes a GitHub release (make_latest) with both files. Failed build = nothing published.
- `desktop/launcher.py` sets FMCC_VERSION from version.txt; `updates.py` uses it for FMCC's own update check. `.gitignore` now ignores `.env` files. `desktop/README.md` is the setup guide (Save to GitHub, public repo, FMCC_RELEASE_REPO in the keys card, re-publish).
- Website download box: version, release date, size, unsigned-installer note (checked with a mocked release response). Real release flow not run yet: needs the repository and FMCC_RELEASE_REPO.


- (2026-11-08) Repo: chrishorwedel-underdog/Underdogs-FMCC (public). First build run 42532773413 succeeded: release v0.2.1 with FMCC-Setup.exe (73.5 MB) + fmcc-names.json. `updates.release_repo()` normalises FMCC_RELEASE_REPO (owner/repo, github.com link, .git, git@) and is used by setup download, name updates and FMCC's update check. Workflow tweaks for the next build: Inno Setup install fallback, release notes skip checkpoint/auto-generated lines. FMCC_RELEASE_REPO must be entered in the keys card (requested), then re-publish. Installer not yet run on a real PC.
- (2026-11-08) FMCC_RELEASE_REPO saved. Preview checked: download box shows v0.2.1 · Nov 8, 2026 · 73.5 MB with the SmartScreen note; name-update check reads the real fmcc-names.json (v0.2.1); FMCC update check reads the repo (installed version now always the running build's version, "dev" in preview).

## 2026-11-08 Hidden CA/PA, World Monthly Reports, competition XIs, extra formations
- Real CA/PA never shown: removed from Squad table, player sheet (chart now "CA gained across saves"), Scout table/profile/CSV (API masks ca/pa in every view), Development, report tables, Creator preview; /api/squad and /api/squad/plan no longer send ca/pa; DOF context uses ability words (`_tier`) and the system prompt forbids CA/PA numbers. Creator CA/PA input ranges kept (settings for new players).
- Sidebar: "Your workspace" removed; Project Safety / Downloads / Appearance moved under Punish a Club, one per line (`.botlinks`).
- Copy: Breakout says FMCC picks the season's Breakout Player and the winner gets a CA bonus (eyebrow, guide, tour, sidebar sub). Scout Players: "a combination of match stats and advanced analytics".
- Squad lineup: Best, Development, Domestic (league registration), Cup (rests the `cup_rest`=4 most-used regulars) and UEFA XI (List A `uefa_max` 25 / `uefa_min_homegrown` 8 + U21 List B). 22 formations (`roles.EXTRA_FORMATIONS`); up to 3 extra tactics per browser (localStorage) via a dropdown.
- Development: CA gained (month + season), goals, assists, mins/game, avg rating; plan goal is "CA to gain" (stores start_ca/goal_ca, shows +x of +N).
- Player Creator: own "Batch name and seed" card with definitions and a New seed button.
- World Monthly Reports (`world_api.py`, db.world_months one compact world snapshot per month, written on each save read): 12 world stories (5 per country, transfers capped at 4), league tables with movement (SAMPLE simulated; real tables need fixture reading, not available), 10 biggest transfers (club changes between months; fee from save or ≈ value), top 10 + U21 top 5 for month stats and per-90 analytics, Attacker/Defender/Goalkeeper/U21 of the Month with 2 runners-up, world + per-country. Sample pool now has assists and some club moves.
- (2026-11-09) Windows reader reads the world (`fmsave_reader.py`): every club in a league table from `league_tables()` (names from fmsave's name map or "Competition <id>", country = table/club nation via players' nationality names), players from those clubs with season stats (summed per player, rating weighted), per-90 analytics mapped to FMCC metric keys (npxg, xa, kp, chc, progp, drb, tkw, pwon, xgp, padbc, prr, savep), latest transfer + fee from `transfers()`, top 4000 by minutes. Tables stored per month in world_months and used by World Monthly Reports with position movement. Checked against a fake fmsave module (tests/test_fmsave_world_reader.py); field names follow fmsave's docs and are UNVERIFIED on a real save.
- (2026-11-09) Real league names: `world_api.name_unnamed` runs on every save read. It names "Competition <id>" tables from the league strength workbook (career's uploaded list or the built-in one): same country, level from average club reputation vs workbook tier, team count as tie-break. Leagues that already have names are skipped, and women's tables are left alone. Renames tables and pool players (so scouting multipliers match too), audits the count, and marks the tables with * plus a note. Tests: tests/test_world_league_names.py, tests/test_fmsave_world_reader.py (3 passed).
- (2026-11-09) Fix league names: pencil on every table in World Monthly Reports opens an input with workbook league names suggested for that country; Save stores a rename keyed by the save's original name (db.league_names, append-only revisions, audited); "Automatic" goes back to the save/workbook name. Your names win over automatic naming on every later save read and rename pool players too (scouting/league strength follow). Applied to stored months at report time. Also fixed sample tables when a club has no players in the sample pool. Tests: tests/test_world_league_names.py (3) + reader test pass; checked with curl and a screenshot.
- (2026-11-09) Award history: GET /api/world/award-history?country= works out every stored month's winners (Attacker, Defender, Goalkeeper, U21), newest first, from world_months, and applies your league renames. Shown as the "World / <country> award history" card under the monthly awards in World Monthly Reports. Checked with curl and screenshots (desktop + 390px, the table scrolls sideways).
- (2026-11-09) Player Creator: seed now has its own marked "Seed a Surname" section (pc-name-seed) explaining that the seed decides each player's first name and surname plus face/age/details, same seed = same names, New seed = fresh names; Batch name is a separate field above it. Default batch ranges for created players: CA 30–60, PA 60–100 (user asked "top PA 60, top CA 100"; PA can't be below CA, so it was read as top CA 60 / top PA 100). Built-in presets keep their own ranges. Dynamic Potential league/nation lists: 32px right padding so the switches sit away from the scroll bar. Checked with a screenshot and a preview call.
- (2026-11-09) Sidebar: logo doubled (clamp 80–192px, 12.4vh) and menu boxes 150% taller (min-height clamp 36–72px, 5.8vh). On short screens the sidebar now scrolls to reach the DOF button.
- (2026-11-09) Appearance page (/appearance, lib/appearance.js, saved per browser): text size 100/112/125/140% (zoom on .app plus top-level dialogs and toasts; popovers stay unzoomed so they line up), themes (Dark, Pure black, Dim grey, Midnight blue), 7 accent colours, animations and film grain switches, Reset. The sidebar logo now has one menu box height of space below it. Tested: iteration_17 and iteration_18 (100%).
- (2026-11-09) Squad tactics from the save: the reader returns your club's tactics (fmsave `save.tactics()`; the sample save has 3 SAMPLE tactics). They are stored with each snapshot, and `roles.match_tactic` maps each to the closest FMCC formation by its position codes, or by a shape in its name. /api/squad/plan defaults to the first save tactic and sends formations as ordered [key,label] lists; it falls back to 4-3-3/4-2-3-1 if the save has none. Up to 3 extra tactics as before. Tested: iteration_19, iteration_20; tests/test_tactics_from_save.py. Not yet checked on a real save.
- (2026-11-09) World Monthly Reports by World > Continent > Nation > League: continents come from the workbook's confed column; continent/country/league params on /api/world/report and /award-history; selects, breadcrumbs, scope buttons; news 12/8/5. Tested: iteration_20 (backend 100%); the mobile grid overflow was fixed afterwards.







- Tested: iteration_16 (backend 20/21, frontend 95%); fixed afterwards: youth_minutes CA leak, Breakout copy consistency, news balance + ordinals, odd-sized sample leagues, labelled remove buttons, Reports tab in URL.



## 2026-11-09
- World Monthly Reports: World / Continent / Nation / League levels (continent from workbook confederation column). Awards counted by where the player plays at every level.
- Continent award tally (World level): per season, World Player of the Month awards incl. runners-up (3/2/1 pts) per continent; season picker. API GET /api/world/continent-tally. Tested iteration_21 (all pass).
- Sidebar: logo gap halved, nav boxes 15% shorter.
- Project Safety, Downloads and Appearance moved from the sidebar into a centred footer bar at the bottom of the app (components/AppFooter.jsx), also visible on mobile.
- Footer version tag (AppFooter VersionTag): shows installed FMCC version from /api/updates (fmcc component), pulsing dot when status=update_available; links to Settings. Shows "FMCC preview build" when version is dev (browser preview).
- One-click update: footer dot opens an "Update now" popover (VersionTag.jsx) → POST /api/fmcc/install downloads FMCC-Setup.exe from the latest GitHub release to %APPDATA%\FMCC\updates, then the Windows launcher closes FMCC and runs it with /SILENT /CLOSEAPPLICATIONS; fmcc.iss reopens FMCC after a silent install. Preview returns 409 (Windows only).
- What's New popup (WhatsNew.jsx): GET /api/fmcc/whats-new shows the release-note bullets once after the installed version changes; POST /api/fmcc/whats-new/seen. First install doesn't show it. Tested iteration_22 (all pass, UI states via mocks; real Windows install not yet verified).
- Seed a Surname: own tab between Player Creator and Clubs (SeedTab.jsx, SeedResults.jsx, backend seed_api.py /api/seed/*). Surname; New save (new players + staff by position/role, written to an editor data file with NG_Regens faces) or Current save (renames existing low-profile players: free agents, youngsters, fringe players, not your club, ability kept; staff left out because staff aren't read from saves yet). Nationality counts must add up to the total; ethnicity, player and staff age-mix sliders; skin, height, CA ≤60, PA ≤100 ranges. Create shows editable results; Seed The Surname applies. History with file download/remove. Live-save renaming via FMLibreEditor is UNVERIFIED.
- Player Creator is now "One player" (SingleCreator.jsx, creator_single.py /api/creator/single): name, known-as, two nationalities, DOB, club, ethnicity, skin, height, weight, feet, 14 position levels, CA/PA 1–200, auto-filled then editable attributes, 10 personality traits, face; create/edit/download/delete. "Batch of players" toggle keeps the old batch tools (seed section removed, Shuffle names button).
- Fixed: editor data XML no longer has duplicate id attributes (unique_id). Tested iteration_23 + fixes (draft.mode confirm, cell resync/clamp, form restored from draft, cleaner validation messages, file renamed on edit).
- Seed a Surname now renames staff in running saves too: fmsave_reader._staff reads save.staff() (job titles on FM27 only; skips human manager), stored as pools.staff; sample_reader.sample_staff for preview. Low-profile staff = backroom roles at other clubs (never Manager/board, CA ≤120); role matched via ROLE_JOBS, nationality preferred, "closest" tag when not matched. Live rename uses FMLibreEditor "set staff" — UNVERIFIED.
- Every seeded player (created or renamed) gets "Keep History After Retirement" on: keep_history attribute in the new-save XML; live set keep_history_after_retirement=1 after renaming (UNVERIFIED field name).
- Seed a Surname page redesigned (SeedTab.jsx + SeedParts.jsx): 4 numbered steps (surname + save type; big Players/Staff steppers with quick picks and auto split "Balanced squad"/"Typical backroom" or custom; nationality share sliders auto-converted to exact counts; age presets or custom), "Fine-tune" accordion (ethnicity, skin, height, CA ≤60/PA ≤100, faces/own club), sticky summary bar with Create + Seed The Surname. Form saved in localStorage.
- Dynamic Potential: "All loaded players" switch (scope.all_players) covers your squad + every player in loaded leagues; hides My club/League/Nation lists while on. Per-run cap (Rules) still applies. Tested iteration_24 (backend 30/30; stepper sync, custom-age start, mobile bar fixed after).
- Per-career Features (features_api.py /api/features; pages/Features.jsx; FeatureGate.jsx): "Choose your features" shown once per career after its first save read (careers.features_seen), 13 cards (Home always on + 12 switches incl. DOF), footer "Features" link. Off = greyed/locked menu item (toast hint), direct URL redirects Home, countdowns/notices/dots/Home cards hidden, run endpoints 409 (dp/run, elite/queue, breakout/finalise, dof stream). Nothing deleted; world monthly data still recorded.
- Menu dot: /api/notify returns badge_items for a hover tooltip; opening a page POSTs /api/notify/read-page to clear its dot. Tour Home text explains the dot.
- Seed a Surname step 3: − / + per nationality (moves one person from/to the largest other share; total fixed; min 1). Tested iteration_25 (backend 12/12, frontend 100%).
- Text sizes Normal 100% (default), Large 112%, Larger 125%, Largest 140% (a 115/130/142.5/155% scale with an always-fit menu was tried and reverted at the user's request; anyone who saved one of those sizes is mapped back).
- Built-in scouting/recruitment suite (analysis_api.py /api/analysis/*): Stats Table tab in Scout Players (130 columns incl. per-90, attributes and 40 role fits; percentile shading; Compare against; AND/OR + top/bottom % filters; saved views in localStorage; CSV), Role Fit for 40 FM roles with/without ball + editable weightings (db.role_weights), Player Dossier side panel (estimated value with 6 factors, value history from world_months/snapshots, contract, roles, attributes, similar/cheaper/younger, compare up to 5 with radar), Transfer Market page (lists, changes since last save, rankings), Club Analysis page (what to do first, where to strengthen, Upgrade/Affordable/Successor ideas). Feature switches "market" and "club". Estimated value = FMCC's own: log-value fitted to the save's values vs best role fit, clamped and blended with the game value, times factors. Never exposes CA/PA.
- Downloads: one "Download & install" button per pack (NG_Regens fetched from ngregens.org in the Windows program; sortitoutsi packs open the page, FMCC watches Downloads up to 30 min and installs automatically; "Installed ✓"/"Update"). FM Dossier, fmOS, FMST26 removed from Downloads. Tested iteration_26 + fixes (own league for "My league" changes, 100+ columns, mobile Club Analysis, compare labels, per-attribute weight saves, rankings gender filter); backend 43 tests pass.
- Phase 2/3 backlog: .fmf tactic import + slot fit, "Try in XI", national team builder, backroom staff search, shortlists to/from FM, scout-knowledge ranges; custom formula stats, scatter charts, "Will he join?", injury risk, club/competition profiles.
- Try in XI (shadow signings): "Try in XI" button in the Player Dossier adds up to 3 non-squad players (localStorage fmcc-try-xi); Squad → Lineup shows a Try in XI card with best-XI strength before → after, who drops out and a slot-by-slot Now vs With-trial table. GET /api/squad/try-xi?add=…&formation=…. Nothing is written to FM. Tested iteration_27 (backend 100%); chips order/spacing, inline icon and stale-id pruning fixed after.













## 2026-11-11 Shortlist to FM + Tactic fit upgrade
- User: "Shortlist To FM: Let you send your trial players and shortlists straight into your FM shortlist" / "Tactic Import: Let you load a tactic file and see how well each squad player fits every slot in it"
- Choices: queued as game change; tactic from upload/build AND save's tactics; ranked fit per slot.
- Shortlist to FM: POST /api/scouting/send-to-fm queues entity "shortlist" changes (source "Shortlist to FM"); buttons in Try in XI card, Scouting Shortlist tab, Dossier. Sample mode applies into fm_shortlist collection (undo supported). LIVE Windows: preflight blocks with a clear message (game editor can't write FM's shortlist yet) — UNVERIFIED / not supported on real FM yet.
- Tactic fit (components/squad/TacticFit.jsx, lab_api.py): save tactics (save-N ids) + imported .fmf + built (any formation, role per slot); every slot ranks the whole squad by attribute-only fit; save/delete built tactics. Save tactic roles not read yet (default roles).
- Tested: iteration_28 (backend 17/17), follow-up UI fixes (initial select sync, delete reset, import label, toast grammar, batch dialog wording) verified by screenshot.


## 2026-11-11 Punish a Club: multi-year points deduction
- User: "In punish a club, add the ability to apply a multi-year points deduction". Choices: set each season yourself; up to 10 seasons.
- Points penalty params: seasons (1-10), points (season 1), s2..s10 (1-120 each). Summary "−20 / −10 / −5 points over 3 seasons (35 in total)"; new-career file writes one penalty record per season. Presets unchanged (1 season). Still new-career only. FM accepting the file is UNCONFIRMED.
- Verified via curl (valid/invalid inputs, file output) and screenshot (desktop + mobile).


## 2026-11-11 Automatic download + apply of made files
- User: "When I click Seed a Surname, the file should be automatically downloaded and applied. This goes for any edited/created/adjusted file."
- Seed a Surname (new save), Player Creator (single create/edit and batches), Punish a Club now auto-download their file (lib/autoDownload.js). On Windows the file is also placed in FM's editor data folder (as before). Punish on FM27 also auto-queues its current-save penalties in Game changes (approval step kept for save safety). Current-save seeds apply renames directly (no file).
- Tested: iteration_29 (all flows pass). Known: current-save rename seeds have no undo button in Seeded surnames list.


## 2026-11-11 Windows app starts reliably (Phase 1 of approved plan "FMCC for Windows: a standalone app that starts every time")
- Problem: installed app opened on "127.0.0.1 refused to connect". Likely causes fixed: window opened before the engine; packaged server crashed silently (no console streams for uvicorn; server modules shipped as data so FastAPI/Pillow/openpyxl etc. weren't bundled); errors never shown.
- desktop/launcher.py rewritten: single copy (mutex FMCCSingleInstance, focuses open window), loading screen first (desktop/startup_pages.py, loading-logo.png), ordered start (install check, data-folder write check, leftover data-store cleanup, ports, mongod, uvicorn.Server, /api/ping), plain-words problem screen with Try again / Open log file / Copy details, clean shutdown (uvicorn exit + mongod shutdown command), rotating log %APPDATA%\FMCC\logs\fmcc-startup.log, `--selftest` mode.
- backend/server.py: /api/ping (desktop only). Workflow: backend modules bundled as code (--paths backend + hidden imports), backend/data bundled, CI self-test of packaged exe blocks publishing on failure. Inno: AppMutex, CloseApplications, old _internal removed on install (data in %APPDATA%\FMCC untouched). requirements-desktop: Pillow, openpyxl.
- Verified on Linux with a simulated install: clean start/stop, port-in-use message, leftover data store stopped; screens rendered. NOT verified on Windows yet - needs Save to GitHub -> CI build -> install on PC.
- Phase 2/3 backlog: one-click self-fix, end-to-end update check on a PC, signed installer, uninstall keep/remove data, export/import.

## 2026-11-11 Getting the fixed installer published (approved plan)
- Found: GitHub build #12 (commit 35483d6) failed at "Start the packaged program and check it answers" after 7s; v0.2.11 (old launcher) is still the latest release. Job logs need repo admin; annotations are public.
- Likely cause found and fixed: Windows reads text files as cp1252 by default; leagues_api/stats_model read non-ASCII JSON without encoding -> server crashed at import on Windows (also explains the original "refused to connect"). Fixed encodings (leagues_api, stats_model, dof_api config, launcher config). dof_api LLM import made lazy so a chat package problem can't block startup. All backend modules import under an ASCII locale; simulated install self-test passes.
- CI self-test step: reliable exit code, 4-min limit, posts startup/output/data-store log tail as a public annotation + job summary on failure.
- Download card: build status line from GitHub Actions (green Latest version / amber being built / grey last working version). /api/setup/download returns `build`; cache 2 min.
- Pending: user presses Save to GitHub; confirm v0.2.12+ publishes; user installs on PC.

- 2026-11-11 Build #13 (with encoding fix) got past import of data files; self-test annotation showed: FastAPI 'Form data requires python-multipart'. Fixed: python-multipart added to desktop/requirements-desktop.txt + hidden imports; new CI step "Check the server loads with the packaged requirements" catches missing packages before packaging. Awaiting user Save to GitHub -> build #14.
- 2026-11-11 Build #14 PASSED the Windows self-test; v0.2.14 published (FMCC-Setup.exe). Not yet installed on user's PC.

## 2026-11-11 "New version ready" corner card (approved plan, Phase 1)
- backend/self_update.py: GET /api/fmcc/update-card (installed Windows program only: install_hook set and version != dev; quiet on offline/errors; newer than installed; respects per-version 24h snooze in settings.update_snooze), POST /api/fmcc/update-card/snooze?version=.
- frontend VersionTag.jsx: UpdateCard (checked once per start, appears 3s after load, bottom-right above footer, up to 3 notes, Update now = existing one-click install, Not now = 24h snooze); shared useInstall hook; App.js renders it. Footer dot/prompt unchanged.
- Verified: backend logic via mocked release (show, snooze, newer version brings it back, offline quiet); card render via mocked API on desktop + mobile. Website returns show:false. Update now end-to-end on a real PC not confirmed.
- Phase 2/3 backlog: What's new page for all versions since installed; Settings switch for the card; auto-install on close; stable vs test channel.




## 2026-11-11 Dynamic Potential rebuilt to the Underdog FM rulesheet + four themes (approved plan, Phase 1)
- backend/dp_engine.py: rulesheet defaults (score weights, metric groups per position, stand-ins, reverse stats, score bands, tiers, decline, age table, growth/decline tapers, winter, limits, batch size), validation, percentile scoring, tier caps, decline requirements, age deduction, point-by-point tapers, winter advance (half, max +4), season settlement, floors/caps, plain-words reasons. Never returns real CA/PA.
- backend/dp_api.py (/api/dp): settings (one set for all careers, history, reset section/all, restore; malformed -> 422), season (winter date suggested from winter window, locked after first review, ages fixed at season start), overview counts, POST /review/{winter|season_end} (batches, rerun safe, again=true recomputes with revision and never re-applies), records + detail, decide (latest revision only; winter records blocked once season-end settled). Season-end supersedes pending winter records (prevents double growth) and requires game date after the winter date. Auto changes go through queue_changes + start_batch (backup first); exceptions wait in Needs your review.
- Old GET /api/dp moved to GET /api/dp/scope (scope/all loaded players switch kept); old /dp/run no longer used by UI.
- Frontend: DynamicPotentialPage tabs Overview / Needs your review / Settings / Who's reviewed (components/dp/*). Guide text updated.
- Themes: Light, FM24, FM26, FM27 (lib/appearance.js, Appearance previews, theme-light CSS overrides, --top var). FM27 top bar uses FM27 colours; club colours not readable from saves yet.
- Tested: iteration_30 + fixes; backend/tests/test_dp_rulesheet.py 17/17 pass. Sample save: small comparison groups and missing role stats -> mostly needs_review / ratings-only (expected). Real-save stats availability unverified.
- Phase 2/3 backlog: balance preview, compare settings sets, export records, club trends, review reminders, settings presets; FM27 club colours from save.

