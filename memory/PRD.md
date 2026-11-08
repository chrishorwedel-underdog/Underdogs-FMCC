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

## Backlog
- P0 Windows packaging: real fmsave reader + FMLibreEditor hidden editor adapters, save-folder watcher, installer (GitHub Actions), real file swap for updates.
- P1: per-90 trends in Monthly Reports; in-app OpenAI key field for the Windows build.
- P2: restore inside a transaction; GitHub token for update checks; user-saved named presets beyond export/import; registration presets per real league.

## Next tasks
Windows packaging with the real fmsave reader, FMLibreEditor editor and FMMatchLens data.
