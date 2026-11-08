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
