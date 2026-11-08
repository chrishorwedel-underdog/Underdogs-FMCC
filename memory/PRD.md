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

## Backlog
- P0 Stage 2: role ratings, depth charts, saved lineups, Best/Development XI, registration check, Scouting rankings, Moneyball, Squad Development plans, Monthly Reports, Elite Training, Breakout, Dynamic Potential scope, Rules builder, append-only history.
- P0 Windows packaging: real fmsave reader adapter, save-folder watcher, installer (GitHub Actions), real file swap for updates.
- P1 Stage 3: hidden game editor, change queue, audit trail, undo, protection against applying twice.
- P1 Stage 4: FMMatchLens setup, Matches module, DOF chat (OpenAI gpt-5.6-terra, user's key).
- P2: restore inside a transaction; GitHub token for update-check rate limits.

## Next tasks
Stage 2 planning modules, or Windows packaging with the real fmsave reader.
