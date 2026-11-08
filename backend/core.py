import asyncio
import hashlib
import json
import logging
import os
import uuid
from datetime import datetime, timezone

from fastapi import HTTPException
from motor.motor_asyncio import AsyncIOMotorClient
from pymongo import ASCENDING, DESCENDING, IndexModel

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
logger = logging.getLogger("fmcc")
io_lock = asyncio.Lock()

BACKUP_COLLECTIONS = ["settings", "careers", "identities", "snapshots", "lineups", "rules", "plans", "shortlist",
                      "nominations", "awards", "changes", "batches", "audit", "game_edits", "pools", "branding", "club_edits", "punishments", "test_results", "philosophy", "pipeline", "board_slots", "notices", "missed_dates", "creator_batches"]
MAX_AUTO_BACKUPS = 20
EXTRA_INDEXES: dict[str, list[IndexModel]] = {
    "lineups": [IndexModel([("career_id", ASCENDING), ("formation", ASCENDING), ("revision", DESCENDING)], name="career_form_rev", unique=True)],
    "rules": [IndexModel([("career_id", ASCENDING), ("module", ASCENDING), ("version", DESCENDING)], name="career_module_ver", unique=True)],
    "plans": [IndexModel([("career_id", ASCENDING), ("unique_id", ASCENDING), ("revision", DESCENDING)], name="career_uid_rev", unique=True)],
    "awards": [IndexModel([("career_id", ASCENDING), ("award_key", ASCENDING), ("revision", DESCENDING)], name="career_award_rev", unique=True)],
    "changes": [IndexModel([("key", ASCENDING)], name="idempotency", unique=True), IndexModel([("career_id", ASCENDING), ("status", ASCENDING)], name="career_status")],
    "game_edits": [IndexModel([("career_id", ASCENDING), ("unique_id", ASCENDING)], name="career_uid", unique=True)],
    "pools": [IndexModel([("career_id", ASCENDING)], name="career", unique=True)],
    "audit": [IndexModel([("career_id", ASCENDING), ("at", DESCENDING)], name="career_at")],
    "branding": [IndexModel([("career_id", ASCENDING), ("kind", ASCENDING), ("target_uid", ASCENDING), ("revision", DESCENDING)], name="career_kind_uid_rev", unique=True)],
}


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def new_id() -> str:
    return str(uuid.uuid4())


async def get_settings() -> dict:
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0})
    return s or {"setup_complete": False, "active_career_id": None, "auto_install_updates": False, "last_update_check": None}


async def active_career() -> dict:
    s = await get_settings()
    if not s.get("active_career_id"):
        raise HTTPException(409, "No active career yet. Finish the first-run setup.")
    c = await db.careers.find_one({"id": s["active_career_id"]}, {"_id": 0})
    if not c:
        raise HTTPException(404, "Active career not found")
    return c


async def latest_two(career_id: str) -> list:
    return await db.snapshots.find({"career_id": career_id}, {"_id": 0}).sort("save_no", -1).limit(2).to_list(2)


async def latest_snapshot(career_id: str) -> dict:
    snaps = await latest_two(career_id)
    if not snaps:
        raise HTTPException(404, "No save read yet")
    return snaps[0]


def month_minutes(latest: dict, prev: dict | None) -> dict:
    before = {p["unique_id"]: p["minutes"] for p in prev["players"]} if prev and prev["season"] == latest["season"] else {}
    return {p["unique_id"]: p["minutes"] - before.get(p["unique_id"], 0) for p in latest["players"]}


async def season_start_ca(career_id: str, season: str) -> dict:
    out = {}
    async for s in db.snapshots.find({"career_id": career_id, "season": season}, {"_id": 0, "players.unique_id": 1, "players.ca": 1}).sort("save_no", 1):
        for p in s["players"]:
            out.setdefault(p["unique_id"], p["ca"])
    return out


def checksum(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


async def dump_data() -> dict:
    return {c: await db[c].find({}, {"_id": 0} if c != "settings" else {}).to_list(None) for c in BACKUP_COLLECTIONS}


async def create_backup(reason: str, automatic: bool) -> dict:
    data = await dump_data()
    doc = {"id": new_id(), "created_at": now_iso(), "reason": reason, "automatic": automatic,
           "checksum": checksum(data), "counts": {k: len(v) for k, v in data.items()}, "data": data}
    await db.backups.insert_one(dict(doc))
    stored = await db.backups.find_one({"id": doc["id"]}, {"_id": 0})
    verified = checksum(stored["data"]) == doc["checksum"]
    await db.backups.update_one({"id": doc["id"]}, {"$set": {"verified": verified}})
    old = await db.backups.find({"automatic": automatic}, {"id": 1, "_id": 0}).sort("created_at", -1).skip(MAX_AUTO_BACKUPS).to_list(None)
    if old:
        await db.backups.delete_many({"id": {"$in": [o["id"] for o in old]}})
    if not verified:
        raise HTTPException(500, "Backup could not be verified")
    return {k: v for k, v in doc.items() if k != "data"} | {"verified": True}


async def audit(career_id: str, action: str, source: str, detail: str, unique_id=None, player_name=None, batch_id=None, hidden=False):
    await db.audit.insert_one({"id": new_id(), "career_id": career_id, "at": now_iso(), "action": action, "source": source,
                               "detail": detail, "unique_id": unique_id, "player_name": player_name, "batch_id": batch_id, "hidden": hidden})


async def next_revision(col: str, query: dict) -> int:
    last = await db[col].find_one(query, {"_id": 0, "revision": 1}, sort=[("revision", -1)])
    return (last["revision"] + 1) if last else 1
