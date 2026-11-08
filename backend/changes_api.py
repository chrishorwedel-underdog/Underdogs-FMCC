"""Change queue, batches, audit trail and undo. Browser preview: the SAMPLE editor. Windows program: FMLibreEditor writes into the running FM27."""
import asyncio
import os
from datetime import datetime, timezone, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

import sample_reader
from core import db, active_career, create_backup, audit, now_iso, new_id, get_settings, logger, latest_two

router = APIRouter(prefix="/api")
SOURCES = {"elite": "Elite Training", "breakout": "Breakout Player", "dp": "Dynamic Potential"}
LIVE = os.environ.get("FMCC_READER") == "fmsave"
HIDE = ("delta", "current", "new", "old_value", "new_value")
STEP_DELAY = 0.12
_tasks: dict[str, asyncio.Task] = {}


async def reveal_dp() -> bool:
    return bool((await get_settings()).get("reveal_dp", False))


def public(ch: dict, reveal: bool) -> dict:
    out = {k: v for k, v in ch.items() if k not in ("key",)}
    if ch.get("hidden") and not reveal:
        out |= {k: None for k in HIDE if k in out}
    return out


def clamp(v: int) -> int:
    return max(1, min(200, v))


def approver() -> str:
    return os.environ.get("USERNAME") or "Manager" if LIVE else "Manager (browser preview)"


async def preflight(c: dict) -> list:
    """Checks before anything is written to the game. Every check must pass."""
    if not LIVE:
        return [{"key": "preview", "label": "Browser preview: the sample editor is used", "ok": sample_reader.editor_supports(c["edition"]),
                 "detail": "Changes go into the sample save, not into Football Manager"}]
    import fm_game
    import live_editor
    checks = []

    def add(key, label, ok, detail):
        checks.append({"key": key, "label": label, "ok": bool(ok), "detail": detail})
    if c["edition"] != "FM27":
        add("edition", "FM27 save", False, "FM26 saves stay read-only, because FMLibreEditor only supports FM27")
        return checks
    root = await asyncio.to_thread(fm_game.game_root, "FM27")
    running = await asyncio.to_thread(fm_game.fm_running, root)
    add("running", "FM27 is running", running, "Running" if running else "Start FM27 and load this career's save")
    if not running:
        return checks
    try:
        h = await asyncio.to_thread(live_editor.health)
    except live_editor.AdminNeeded as exc:
        raise HTTPException(403, str(exc))
    except Exception as exc:
        add("editor", "FMLibreEditor can connect to FM27", False, str(exc))
        return checks
    add("version", "FMLibreEditor recognises this game version", h["known_build"],
        f"Profile {h['profile']}" if h["known_build"] else f"Build {h['build'] or 'unknown'} is new to FMLibreEditor, so FMCC applies nothing")
    add("safety", "FMLibreEditor's safety checks pass", not h["failed_checks"], "; ".join(h["failed_checks"]) or "All passed")
    snaps = await latest_two(c["id"])
    ok, detail = False, "Read a save of this career first"
    if snaps:
        sample, bad = snaps[0]["players"][:3], []
        for p in sample:
            try:
                _, name = await asyncio.to_thread(live_editor.read, p["unique_id"], "ca")
            except Exception:
                name = ""
            a, b = name.casefold(), p["name"].casefold()
            if not a or (a not in b and b not in a):
                bad.append(p["name"])
        ok = not bad
        detail = f"{len(sample)} of your players found under the same game IDs" if ok else f"Not found in the loaded game: {', '.join(bad)}"
        if ok and h["game_date"] and h["game_date"] < snaps[0]["game_date"]:
            ok, detail = False, "The loaded game is older than the last save FMCC read"
    add("same_save", "The loaded save matches this career", ok, detail)
    return checks


async def current_values(c: dict, chs: list) -> dict:
    if LIVE:
        import live_editor
        out = {}
        for ch in chs:
            try:
                v, _ = await asyncio.to_thread(live_editor.read, ch["unique_id"], ch["field"])
                out[ch["id"]] = v if v > 0 else None
            except Exception:
                out[ch["id"]] = None
        return out
    snaps = await latest_two(c["id"])
    players = {p["unique_id"]: p for p in snaps[0]["players"]} if snaps else {}
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}) or {"players": []}
    for p in pool["players"]:
        players.setdefault(p["unique_id"], p)
    return {ch["id"]: players.get(ch["unique_id"], {}).get(ch["field"]) for ch in chs}


async def queue_changes(career: dict, source: str, award_id: str, items: list, hidden: bool = False) -> dict:
    """Queue game changes. The idempotency key stops the same award being queued or applied twice."""
    ids, skipped = [], 0
    for it in items:
        if it["delta"] == 0:
            continue
        doc = {"id": new_id(), "career_id": career["id"], "source": source, "award_id": award_id, "unique_id": it["unique_id"],
               "player_name": it["name"], "club": it.get("club"), "field": it["field"], "delta": it["delta"], "hidden": hidden,
               "status": "queued", "created_at": now_iso(), "batch_id": None,
               "key": f"{career['id']}:{source}:{award_id}:{it['unique_id']}:{it['field']}"}
        try:
            await db.changes.insert_one(dict(doc))
            ids.append(doc["id"])
        except DuplicateKeyError:
            skipped += 1
    if ids:
        await audit(career["id"], "queued", source, f"{len(ids)} change(s) queued", hidden=hidden)
    mode = (career.get("change_modes") or {}).get(source, "ask")
    batch = await start_batch(career, ids) if ids and mode == "auto" and not LIVE else None
    return {"queued": len(ids), "skipped_duplicates": skipped, "auto_applied": bool(batch), "batch_id": batch["id"] if batch else None}


async def start_batch(career: dict, ids: list, expected: dict | None = None) -> dict:
    checks = await preflight(career)
    failed = [x for x in checks if not x["ok"]]
    if failed:
        raise HTTPException(409, "Nothing was applied: " + "; ".join(f"{x['label']}: {x['detail']}" for x in failed))
    save_backup = None
    if LIVE:
        import live_editor
        try:
            save_backup = await asyncio.to_thread(live_editor.backup_save, career["save_folder"])
        except Exception as exc:
            raise HTTPException(422, f"Nothing was applied: {exc}")
    backup = await create_backup(f"{career['name']}: before game change batch ({len(ids)})", automatic=False)
    claimed = await db.changes.update_many({"id": {"$in": ids}, "career_id": career["id"], "status": "queued"}, {"$set": {"status": "approved"}})
    if claimed.modified_count == 0:
        raise HTTPException(409, "These changes were already applied or are being applied")
    batch = {"id": new_id(), "career_id": career["id"], "created_at": now_iso(), "status": "running", "total": claimed.modified_count,
             "done": 0, "backup_id": backup["id"], "change_ids": ids, "live": LIVE, "approved_by": approver(), "approved_at": now_iso(),
             "save_backup": save_backup, "checks": checks, "expected": expected or {}}
    await db.batches.insert_one(dict(batch))
    await db.changes.update_many({"id": {"$in": ids}, "status": "approved"}, {"$set": {"batch_id": batch["id"]}})
    await audit(career["id"], "batch approved", "editor", f"Batch of {batch['total']} change(s) approved by {batch['approved_by']}"
                + (f", save backed up to {save_backup['file']}" if save_backup else ", backup saved first"), batch_id=batch["id"])
    _spawn(batch["id"])
    return batch


def _spawn(batch_id: str):
    if batch_id not in _tasks or _tasks[batch_id].done():
        _tasks[batch_id] = asyncio.create_task(run_batch(batch_id))


async def run_batch(batch_id: str):
    try:
        while True:
            b = await db.batches.find_one({"id": batch_id}, {"_id": 0})
            if not b or b["status"] != "running":
                return
            ch = await db.changes.find_one_and_update({"batch_id": batch_id, "status": "approved"}, {"$set": {"status": "applying"}},
                                                      projection={"_id": 0}, return_document=ReturnDocument.AFTER)
            if not ch:
                await db.batches.update_one({"id": batch_id, "status": "running"}, {"$set": {"status": "done", "finished_at": now_iso()}})
                await audit(b["career_id"], "batch finished", "editor", f"{b['done']} change(s) applied", batch_id=batch_id)
                return
            try:
                old, new = await apply_one(ch, b)
            except Exception as exc:
                await stop_batch(b, ch, exc)
                return
            await db.changes.update_one({"id": ch["id"]}, {"$set": {"status": "applied", "applied_at": now_iso(), "old_value": old, "new_value": new, "result": "read back OK" if LIVE else "sample save"}})
            await db.batches.update_one({"id": batch_id}, {"$inc": {"done": 1}})
            detail = f"{ch['field'].upper()} {old} → {new}" if old is not None else f"{ch['field'].upper()} {'+' if ch['delta'] > 0 else ''}{ch['delta']}"
            await audit(ch["career_id"], "applied", ch["source"], detail, ch["unique_id"], ch["player_name"], batch_id, ch["hidden"])
            await asyncio.sleep(STEP_DELAY)
    except Exception as exc:
        logger.error("batch %s failed: %s", batch_id, exc)
        await db.batches.update_one({"id": batch_id}, {"$set": {"status": "paused", "error": "Stopped after an error. Resume to continue."}})


async def apply_one(ch: dict, b: dict) -> tuple:
    exp = (b.get("expected") or {}).get(ch["id"])
    if not LIVE:
        await db.game_edits.update_one({"career_id": ch["career_id"], "unique_id": ch["unique_id"]}, {"$inc": {ch["field"]: ch["delta"]}}, upsert=True)
        return exp, (None if exp is None else clamp(exp + ch["delta"]))
    import live_editor
    old, _ = await asyncio.to_thread(live_editor.read, ch["unique_id"], ch["field"])
    if exp is not None and old != exp:
        raise live_editor.EditorError("the value in the game changed since the preview")
    if old <= 0:
        raise live_editor.EditorError("this value is stored as a range in the game and can't be changed safely")
    new = clamp(old + ch["delta"])
    await asyncio.to_thread(live_editor.write, ch["unique_id"], ch["field"], new)
    return old, new


async def stop_batch(b: dict, ch: dict, exc: Exception):
    await db.changes.update_one({"id": ch["id"]}, {"$set": {"status": "failed", "error": str(exc)[:300], "failed_at": now_iso()}})
    back = await db.changes.update_many({"batch_id": b["id"], "status": "approved"}, {"$set": {"status": "queued", "batch_id": None}})
    done = await db.batches.find_one({"id": b["id"]}, {"_id": 0, "done": 1})
    msg = f"Stopped at {ch['player_name']}: {exc}. {done['done']} change(s) were made before that; {back.modified_count} went back to the queue."
    await db.batches.update_one({"id": b["id"]}, {"$set": {"status": "stopped", "error": msg, "finished_at": now_iso()}})
    await audit(b["career_id"], "batch stopped", "editor", msg, ch["unique_id"], ch["player_name"], b["id"], ch["hidden"])


async def resume_unfinished():
    await db.batches.update_many({"status": "running"}, {"$set": {"status": "paused"}})
    await db.changes.update_many({"status": "applying"}, {"$set": {"status": "approved"}})
    await db.changes.update_many({"status": "approved", "batch_id": None}, {"$set": {"status": "queued"}})


async def stop_all():
    """Called before a restore so no batch keeps writing into restored data."""
    await db.batches.update_many({"status": "running"}, {"$set": {"status": "paused"}})
    for t in list(_tasks.values()):
        t.cancel()
    _tasks.clear()


class IdsIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=20000)


class PreviewIn(BaseModel):
    ids: list[str] = Field(min_length=1, max_length=500)


class ApplyIn(BaseModel):
    preview_id: str


class ModeIn(BaseModel):
    source: Literal["elite", "breakout", "dp"]
    mode: Literal["auto", "ask"]


class RevealIn(BaseModel):
    reveal: bool


@router.get("/changes")
async def list_changes():
    c = await active_career()
    reveal = await reveal_dp()
    queued = await db.changes.find({"career_id": c["id"], "status": "queued"}, {"_id": 0}).sort("created_at", 1).to_list(5000)
    batches = await db.batches.find({"career_id": c["id"]}, {"_id": 0, "change_ids": 0, "expected": 0}).sort("created_at", -1).limit(20).to_list(20)
    return {"modes": {k: (c.get("change_modes") or {}).get(k, "ask") for k in SOURCES}, "sources": SOURCES, "reveal_dp": reveal,
            "edition": c["edition"], "editor_ok": c["edition"] == "FM27" if LIVE else sample_reader.editor_supports(c["edition"]),
            "live": LIVE, "auto_allowed": not LIVE,
            "queued": [public(x, reveal) for x in queued], "batches": batches}


@router.put("/changes/modes")
async def set_mode(body: ModeIn):
    c = await active_career()
    await db.careers.update_one({"id": c["id"]}, {"$set": {f"change_modes.{body.source}": body.mode}})
    await audit(c["id"], "setting", body.source, f"{SOURCES[body.source]}: {'apply automatically' if body.mode == 'auto' else 'ask me first'}")
    return {"ok": True}


@router.put("/changes/reveal")
async def set_reveal(body: RevealIn):
    await db.settings.update_one({"_id": "app"}, {"$set": {"reveal_dp": body.reveal}}, upsert=True)
    return {"ok": True}


@router.post("/changes/preview")
async def preview_changes(body: PreviewIn):
    """The exact-change preview: each player's current and new value, plus every check. Applying needs this preview."""
    c = await active_career()
    ids = list(dict.fromkeys(body.ids))
    chs = await db.changes.find({"id": {"$in": ids}, "career_id": c["id"], "status": "queued"}, {"_id": 0, "key": 0}).sort("created_at", 1).to_list(None)
    if len(chs) != len(ids):
        raise HTTPException(409, "Some of these changes were already applied, rejected or are being applied. Reload the queue.")
    checks = await preflight(c)
    ready = all(x["ok"] for x in checks)
    cur = await current_values(c, chs) if ready else {}
    unreadable = [ch["player_name"] for ch in chs if ready and cur.get(ch["id"]) is None]
    if LIVE and ready:
        checks.append({"key": "values", "label": "Every current value can be read", "ok": not unreadable, "detail": ", ".join(unreadable[:5]) or "All read"})
    checks += [{"key": "backup", "label": "A verified copy of the newest save is made first" if LIVE else "A verified FMCC backup is made first", "ok": True, "detail": "Made when you press Apply batch"},
               {"key": "dupes", "label": "No change in this batch was applied before", "ok": True, "detail": "Each reward can only be applied once"}]
    ready = all(x["ok"] for x in checks)
    pid = new_id()
    await db.previews.insert_one({"id": pid, "career_id": c["id"], "ids": ids, "expected": cur, "at": now_iso(), "used": False, "ready": ready})
    reveal = await reveal_dp()
    rows = [public(ch | {"current": cur.get(ch["id"]), "new": None if cur.get(ch["id"]) is None else clamp(cur[ch["id"]] + ch["delta"])}, reveal) for ch in chs]
    return {"preview_id": pid, "rows": rows, "checks": checks, "ready": ready, "live": LIVE}


@router.post("/changes/apply")
async def apply_changes(body: ApplyIn):
    c = await active_career()
    since = (datetime.now(timezone.utc) - timedelta(minutes=15)).isoformat()
    p = await db.previews.find_one_and_update({"id": body.preview_id, "career_id": c["id"], "used": False, "ready": True, "at": {"$gte": since}},
                                              {"$set": {"used": True}}, projection={"_id": 0})
    if not p:
        raise HTTPException(409, "This preview is out of date or was already used. Review the batch again.")
    b = await start_batch(c, p["ids"], p["expected"])
    return {"batch_id": b["id"], "total": b["total"], "live": LIVE}


@router.post("/changes/reject")
async def reject_changes(body: IdsIn):
    c = await active_career()
    r = await db.changes.update_many({"id": {"$in": body.ids}, "career_id": c["id"], "status": "queued"}, {"$set": {"status": "rejected"}})
    await audit(c["id"], "rejected", "editor", f"{r.modified_count} queued change(s) rejected")
    return {"rejected": r.modified_count}


async def _batch(c: dict, batch_id: str) -> dict:
    b = await db.batches.find_one({"id": batch_id, "career_id": c["id"]}, {"_id": 0})
    if not b:
        raise HTTPException(404, "Batch not found")
    return b


@router.post("/changes/batches/{batch_id}/pause")
async def pause_batch(batch_id: str):
    c = await active_career()
    r = await db.batches.update_one({"id": (await _batch(c, batch_id))["id"], "status": "running"}, {"$set": {"status": "paused"}})
    if not r.modified_count:
        raise HTTPException(409, "This batch isn't running")
    return {"ok": True}


@router.post("/changes/batches/{batch_id}/resume")
async def resume_batch(batch_id: str):
    c = await active_career()
    r = await db.batches.update_one({"id": (await _batch(c, batch_id))["id"], "status": "paused"}, {"$set": {"status": "running", "error": None}})
    if not r.modified_count:
        raise HTTPException(409, "This batch isn't paused")
    _spawn(batch_id)
    return {"ok": True}


@router.post("/changes/batches/{batch_id}/undo")
async def undo_batch(batch_id: str):
    c = await active_career()
    b = await _batch(c, batch_id)
    if b["status"] not in ("done", "paused", "stopped", "partly undone"):
        raise HTTPException(409, "Pause or finish the batch before undoing it")
    if LIVE:
        failed = [x for x in await preflight(c) if not x["ok"]]
        if failed:
            raise HTTPException(409, "Undo needs FM27 running with the same save loaded: " + "; ".join(x["detail"] for x in failed))
    await db.batches.update_one({"id": batch_id}, {"$set": {"status": "undoing"}})
    undone = 0
    for ch in await db.changes.find({"batch_id": batch_id, "status": "applied"}, {"_id": 0}).sort("applied_at", -1).to_list(None):
        if LIVE:
            import live_editor
            try:
                cur, _ = await asyncio.to_thread(live_editor.read, ch["unique_id"], ch["field"])
                if ch.get("old_value") is None or cur != ch.get("new_value"):
                    raise live_editor.EditorError("the value in the game changed since it was applied, so it was left alone")
                await asyncio.to_thread(live_editor.write, ch["unique_id"], ch["field"], ch["old_value"])
            except Exception as exc:
                msg = f"Undo stopped at {ch['player_name']}: {exc}. {undone} change(s) were put back."
                await db.batches.update_one({"id": batch_id}, {"$set": {"status": "partly undone", "error": msg}})
                await audit(c["id"], "undo stopped", "editor", msg, ch["unique_id"], ch["player_name"], batch_id, ch["hidden"])
                return {"undone": undone, "error": msg}
        claimed = await db.changes.update_one({"id": ch["id"], "status": "applied"}, {"$set": {"status": "undone", "undone_at": now_iso()}})
        if claimed.modified_count:
            if not LIVE:
                await db.game_edits.update_one({"career_id": c["id"], "unique_id": ch["unique_id"]}, {"$inc": {ch["field"]: -ch["delta"]}})
            await audit(c["id"], "undone", ch["source"], f"{ch['field'].upper()} put back" + (f" to {ch['old_value']}" if ch.get("old_value") is not None else ""),
                        ch["unique_id"], ch["player_name"], batch_id, ch["hidden"])
            undone += 1
    await db.changes.update_many({"batch_id": batch_id, "status": "approved"}, {"$set": {"status": "queued", "batch_id": None}})
    await db.batches.update_one({"id": batch_id}, {"$set": {"status": "undone"}})
    await audit(c["id"], "batch undone", "editor", f"{undone} change(s) reversed", batch_id=batch_id)
    return {"undone": undone}


@router.get("/changes/batches/{batch_id}")
async def batch_detail(batch_id: str):
    c = await active_career()
    b = await _batch(c, batch_id)
    reveal = await reveal_dp()
    rows = await db.changes.find({"batch_id": batch_id}, {"_id": 0, "key": 0}).sort("created_at", 1).to_list(None)
    return {k: v for k, v in b.items() if k not in ("change_ids", "expected")} | {"changes": [public(r, reveal) for r in rows]}


@router.get("/audit")
async def get_audit(limit: int = 200):
    c = await active_career()
    reveal = await reveal_dp()
    rows = await db.audit.find({"career_id": c["id"]}, {"_id": 0}).sort("at", -1).limit(min(limit, 500)).to_list(500)
    return [r | ({"detail": "included"} if r.get("hidden") and not reveal else {}) for r in rows]
