"""Stage 3: change queue, batches, audit trail and undo. The game editor here is the SAMPLE editor (no FM in this environment)."""
import asyncio
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo import ReturnDocument
from pymongo.errors import DuplicateKeyError

import sample_reader
from core import db, active_career, create_backup, audit, now_iso, new_id, get_settings, logger

router = APIRouter(prefix="/api")
SOURCES = {"elite": "Elite Training", "breakout": "Annual Breakout", "dp": "Dynamic Potential"}
STEP_DELAY = 0.12
_tasks: dict[str, asyncio.Task] = {}


async def reveal_dp() -> bool:
    return bool((await get_settings()).get("reveal_dp", False))


def public(ch: dict, reveal: bool) -> dict:
    out = {k: v for k, v in ch.items() if k not in ("key",)}
    if ch.get("hidden") and not reveal:
        out["delta"] = None
    return out


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
    batch = await start_batch(career, ids) if ids and mode == "auto" else None
    return {"queued": len(ids), "skipped_duplicates": skipped, "auto_applied": bool(batch), "batch_id": batch["id"] if batch else None}


async def start_batch(career: dict, ids: list) -> dict:
    if not sample_reader.editor_supports(career["edition"]):
        raise HTTPException(422, f"The game editor doesn't support {career['edition']}")
    backup = await create_backup(f"{career['name']}: before game change batch ({len(ids)})", automatic=False)
    claimed = await db.changes.update_many({"id": {"$in": ids}, "career_id": career["id"], "status": "queued"}, {"$set": {"status": "approved"}})
    if claimed.modified_count == 0:
        raise HTTPException(409, "These changes were already applied or are being applied")
    batch = {"id": new_id(), "career_id": career["id"], "created_at": now_iso(), "status": "running", "total": claimed.modified_count,
             "done": 0, "backup_id": backup["id"], "change_ids": ids}
    await db.batches.insert_one(dict(batch))
    await db.changes.update_many({"id": {"$in": ids}, "status": "approved"}, {"$set": {"batch_id": batch["id"]}})
    await audit(career["id"], "batch started", "editor", f"Batch of {batch['total']} change(s), backup saved first", batch_id=batch["id"])
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
            await db.game_edits.update_one({"career_id": ch["career_id"], "unique_id": ch["unique_id"]}, {"$inc": {ch["field"]: ch["delta"]}}, upsert=True)
            await db.changes.update_one({"id": ch["id"]}, {"$set": {"status": "applied", "applied_at": now_iso()}})
            await db.batches.update_one({"id": batch_id}, {"$inc": {"done": 1}})
            detail = f"{ch['field'].upper()} {'+' if ch['delta'] > 0 else ''}{ch['delta']}"
            await audit(ch["career_id"], "applied", ch["source"], detail, ch["unique_id"], ch["player_name"], batch_id, ch["hidden"])
            await asyncio.sleep(STEP_DELAY)
    except Exception as exc:
        logger.error("batch %s failed: %s", batch_id, exc)
        await db.batches.update_one({"id": batch_id}, {"$set": {"status": "paused", "error": "Stopped after an error. Resume to continue."}})


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
    batches = await db.batches.find({"career_id": c["id"]}, {"_id": 0, "change_ids": 0}).sort("created_at", -1).limit(20).to_list(20)
    return {"modes": {k: (c.get("change_modes") or {}).get(k, "ask") for k in SOURCES}, "sources": SOURCES, "reveal_dp": reveal,
            "edition": c["edition"], "editor_ok": sample_reader.editor_supports(c["edition"]),
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


@router.post("/changes/apply")
async def apply_changes(body: IdsIn):
    c = await active_career()
    b = await start_batch(c, body.ids)
    return {"batch_id": b["id"], "total": b["total"]}


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
    if b["status"] not in ("done", "paused"):
        raise HTTPException(409, "Pause or finish the batch before undoing it")
    await db.batches.update_one({"id": batch_id}, {"$set": {"status": "undoing"}})
    undone = 0
    async for ch in db.changes.find({"batch_id": batch_id, "status": "applied"}, {"_id": 0}):
        claimed = await db.changes.update_one({"id": ch["id"], "status": "applied"}, {"$set": {"status": "undone", "undone_at": now_iso()}})
        if claimed.modified_count:
            await db.game_edits.update_one({"career_id": c["id"], "unique_id": ch["unique_id"]}, {"$inc": {ch["field"]: -ch["delta"]}})
            undone += 1
    await db.changes.update_many({"batch_id": batch_id, "status": "approved"}, {"$set": {"status": "queued", "batch_id": None}})
    await db.batches.update_one({"id": batch_id}, {"$set": {"status": "undone"}})
    await audit(c["id"], "batch undone", "editor", f"{undone} change(s) reversed", batch_id=batch_id)
    return {"undone": undone}


@router.get("/audit")
async def get_audit(limit: int = 200):
    c = await active_career()
    reveal = await reveal_dp()
    rows = await db.audit.find({"career_id": c["id"]}, {"_id": 0}).sort("at", -1).limit(min(limit, 500)).to_list(500)
    return [r | ({"detail": "included"} if r.get("hidden") and not reveal else {}) for r in rows]
