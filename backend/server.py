import asyncio
import hashlib
import json
import logging
import os
import uuid
from contextlib import suppress
from datetime import datetime, timezone, timedelta
from pathlib import Path
from typing import Literal

from dotenv import load_dotenv
from fastapi import FastAPI, APIRouter, HTTPException, Query
from motor.motor_asyncio import AsyncIOMotorClient
from pydantic import BaseModel, Field
from pymongo import ASCENDING, DESCENDING, IndexModel
from starlette.middleware.cors import CORSMiddleware

ROOT_DIR = Path(__file__).parent
load_dotenv(ROOT_DIR / '.env')

import dashboard  # noqa: E402
import sample_reader  # noqa: E402
import updates  # noqa: E402

client = AsyncIOMotorClient(os.environ['MONGO_URL'])
db = client[os.environ['DB_NAME']]
logger = logging.getLogger(__name__)

INDEXES: dict[str, list[IndexModel]] = {
    "careers": [IndexModel([("id", ASCENDING)], name="id", unique=True)],
    "identities": [IndexModel([("career_id", ASCENDING), ("unique_id", ASCENDING)], name="career_uid", unique=True)],
    "snapshots": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("career_id", ASCENDING), ("save_no", DESCENDING)], name="career_save", unique=True),
    ],
    "backups": [IndexModel([("id", ASCENDING)], name="id", unique=True), IndexModel([("created_at", DESCENDING)], name="created_desc")],
    "components": [IndexModel([("key", ASCENDING)], name="key", unique=True)],
}
BACKUP_COLLECTIONS = ["settings", "careers", "identities", "snapshots"]
MAX_AUTO_BACKUPS = 20
io_lock = asyncio.Lock()


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)


def now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


app = FastAPI()
api = APIRouter(prefix="/api")


# ---------- models ----------
Edition = Literal["FM26", "FM27"]


class DetectIn(BaseModel):
    edition: Edition = "FM27"


class CareerIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    club_name: str = Field(min_length=1, max_length=60)
    edition: Edition


class SetupIn(CareerIn):
    save_folder: str = Field(min_length=3, max_length=300)


class FolderIn(BaseModel):
    save_folder: str = Field(min_length=3, max_length=300)
    expected_career_id: str


class AutoInstallIn(BaseModel):
    auto_install: bool


# ---------- helpers ----------
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


def checksum(data: dict) -> str:
    return hashlib.sha256(json.dumps(data, sort_keys=True, default=str).encode()).hexdigest()


async def dump_data() -> dict:
    return {c: await db[c].find({}, {"_id": 0} if c != "settings" else {}).to_list(None) for c in BACKUP_COLLECTIONS}


async def create_backup(reason: str, automatic: bool) -> dict:
    data = await dump_data()
    doc = {"id": str(uuid.uuid4()), "created_at": now_iso(), "reason": reason, "automatic": automatic,
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


async def read_next_save(career: dict) -> dict:
    """Read the next save into a snapshot. Players are matched by the game's unique ID, never by name."""
    save_no = career.get("next_save_no", 0)
    await create_backup(f"{career['name']}: before reading save #{save_no + 1}", automatic=True)
    save = sample_reader.read_save(save_no, career["club_name"])
    snap = {"id": str(uuid.uuid4()), "career_id": career["id"], "save_no": save_no, "read_at": now_iso(),
            "reader": sample_reader.READER_NAME, **save}
    await db.snapshots.insert_one(dict(snap))
    for p in save["players"]:
        await db.identities.update_one(
            {"career_id": career["id"], "unique_id": p["unique_id"]},
            {"$set": {"name": p["name"], "last_seen_save": save_no, "last_seen_date": save["game_date"]},
             "$setOnInsert": {"first_seen_save": save_no, "first_seen_date": save["game_date"]}}, upsert=True)
    res = await db.careers.update_one({"id": career["id"], "next_save_no": save_no},
                                      {"$set": {"next_save_no": save_no + 1, "last_read_at": snap["read_at"], "last_game_date": save["game_date"]}})
    if res.modified_count != 1:
        raise HTTPException(409, "This career changed while the save was being read. Try again.")
    return {"save_no": save_no, "file_name": save["file_name"], "game_date": save["game_date"], "players": len(save["players"])}


async def new_career(body: CareerIn, save_folder: str) -> dict:
    career = {"id": str(uuid.uuid4()), "name": body.name.strip(), "club_name": body.club_name.strip(), "edition": body.edition,
              "save_folder": save_folder, "reader": "sample", "next_save_no": 0, "created_at": now_iso(),
              "last_read_at": None, "last_game_date": None}
    await db.careers.insert_one(dict(career))
    await read_next_save(career)
    await db.settings.update_one({"_id": "app"}, {"$set": {"active_career_id": career["id"]}}, upsert=True)
    return career


# ---------- setup & careers ----------
@api.get("/state")
async def state():
    s = await get_settings()
    career = None
    if s.get("active_career_id"):
        career = await db.careers.find_one({"id": s["active_career_id"]}, {"_id": 0})
    return {"setup_complete": s.get("setup_complete", False), "career": career, "sample_mode": True,
            "auto_install_updates": s.get("auto_install_updates", False), "last_update_check": s.get("last_update_check")}


@api.post("/setup/detect")
async def setup_detect(body: DetectIn):
    return sample_reader.detect_install(body.edition)


@api.post("/setup/complete")
async def setup_complete(body: SetupIn):
    async with io_lock:
        s = await get_settings()
        if s.get("setup_complete"):
            raise HTTPException(409, "Setup is already finished")
        career = await new_career(body, body.save_folder.strip())
        await db.settings.update_one({"_id": "app"}, {"$set": {"setup_complete": True, "auto_install_updates": False}}, upsert=True)
    latest = (await latest_two(career["id"]))[0]
    return {"career": career, "health": [
        {"key": "link", "label": "Game link ready", "ok": True, "detail": f"Read {len(latest['players'])} players from {latest['file_name']} (sample save)"},
        {"key": "analytics", "label": "Match analytics", "ok": False, "detail": "Not set up yet. FMMatchLens setup arrives in stage 4."},
        {"key": "dof", "label": "DOF chat", "ok": False, "detail": "Not set up yet. Your OpenAI key is added in stage 4."},
    ]}


@api.get("/careers")
async def list_careers():
    s = await get_settings()
    rows = await db.careers.find({}, {"_id": 0}).sort("created_at", 1).to_list(100)
    return [r | {"active": r["id"] == s.get("active_career_id")} for r in rows]


@api.post("/careers")
async def create_career(body: CareerIn):
    async with io_lock:
        c = await active_career()
        return await new_career(body, c["save_folder"])


@api.post("/careers/{career_id}/activate")
async def activate_career(career_id: str):
    if not await db.careers.find_one({"id": career_id}):
        raise HTTPException(404, "Career not found")
    await db.settings.update_one({"_id": "app"}, {"$set": {"active_career_id": career_id}}, upsert=True)
    return {"ok": True}


@api.put("/careers/active/folder")
async def set_folder(body: FolderIn):
    c = await active_career()
    if c["id"] != body.expected_career_id:
        raise HTTPException(409, "The active career changed in another window. Reload and try again.")
    await db.careers.update_one({"id": c["id"]}, {"$set": {"save_folder": body.save_folder.strip()}})
    return {"ok": True}


# ---------- saves ----------
@api.post("/saves/read")
async def read_save():
    async with io_lock:
        return await read_next_save(await active_career())


@api.get("/saves")
async def list_saves():
    c = await active_career()
    return await db.snapshots.find({"career_id": c["id"]}, {"_id": 0, "players": 0}).sort("save_no", -1).limit(50).to_list(50)


# ---------- home / squad ----------
@api.get("/home")
async def home():
    c = await active_career()
    snaps = await latest_two(c["id"])
    if not snaps:
        raise HTTPException(404, "No save read yet")
    b = await db.backups.find_one({}, {"_id": 0, "created_at": 1}, sort=[("created_at", -1)])
    return dashboard.compute(snaps[0], snaps[1] if len(snaps) > 1 else None, b["created_at"] if b else None) | {"read_at": snaps[0]["read_at"]}


@api.get("/squad")
async def squad():
    c = await active_career()
    snaps = await latest_two(c["id"])
    if not snaps:
        return {"players": [], "departed": []}
    latest, prev = snaps[0], (snaps[1] if len(snaps) > 1 else None)
    before = {p["unique_id"]: p for p in prev["players"]} if prev else {}
    names = {}
    for p in latest["players"]:
        names[p["name"]] = names.get(p["name"], 0) + 1
    xi_ids = {s["player"]["unique_id"] for s in dashboard.best_xi(latest["players"]) if s["player"]}
    idents = {i["unique_id"]: i for i in await db.identities.find({"career_id": c["id"]}, {"_id": 0}).to_list(None)}
    players = []
    for p in latest["players"]:
        prior = before.get(p["unique_id"])
        players.append(p | {"ca_change": p["ca"] - prior["ca"] if prior else None,
                            "is_new": idents.get(p["unique_id"], {}).get("first_seen_save") == latest["save_no"] and latest["save_no"] > 0,
                            "shared_name": names[p["name"]] > 1, "in_best_xi": p["unique_id"] in xi_ids})
    current = {p["unique_id"] for p in latest["players"]}
    departed = [i for i in idents.values() if i["unique_id"] not in current]
    return {"game_date": latest["game_date"], "save_no": latest["save_no"], "players": players, "departed": departed}


@api.get("/players/search")
async def search_players(q: str = Query("", max_length=60)):
    c = await active_career()
    snaps = await latest_two(c["id"])
    if not snaps:
        return []
    ql = q.lower().strip()
    hits = [p for p in snaps[0]["players"] if ql in p["name"].lower()] if ql else snaps[0]["players"]
    return [{"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "positions": p["positions"]} for p in hits[:8]]


@api.get("/players/{unique_id}")
async def player_detail(unique_id: int):
    c = await active_career()
    ident = await db.identities.find_one({"career_id": c["id"], "unique_id": unique_id}, {"_id": 0})
    if not ident:
        raise HTTPException(404, "Player not found in this career")
    snaps = await db.snapshots.find({"career_id": c["id"], "players.unique_id": unique_id},
                                    {"_id": 0, "save_no": 1, "game_date": 1, "players.$": 1}).sort("save_no", 1).to_list(None)
    history = [{"save_no": s["save_no"], "game_date": s["game_date"], "ca": s["players"][0]["ca"], "minutes": s["players"][0]["minutes"]} for s in snaps]
    return {"identity": ident, "latest": snaps[-1]["players"][0] if snaps else None, "history": history}


# ---------- updates ----------
async def run_update_check() -> list:
    for key, name, role, repo, bundled in updates.COMPONENTS:
        existing = await db.components.find_one({"key": key}, {"_id": 0}) or {}
        installed = existing.get("installed_version", bundled)
        row = {"key": key, "name": name, "role": role, "repo": repo, "installed_version": installed, "checked_at": now_iso()}
        if not repo:
            row |= {"status": "no_source", "latest_version": None, "message": "Release page not set yet"}
        else:
            try:
                rel = await updates.fetch_latest(repo)
                newer = rel["tag"] and updates.is_newer(rel["tag"], installed)
                row |= {"latest_version": rel["tag"], "release_url": rel["url"], "status": "update_available" if newer else "up_to_date", "message": None}
            except Exception as exc:
                logger.warning("update check %s failed: %s", repo, exc)
                row |= {"status": "check_failed", "message": "Couldn't reach the release page"}
        await db.components.update_one({"key": key}, {"$set": row, "$setOnInsert": {"history": []}}, upsert=True)
    await db.settings.update_one({"_id": "app"}, {"$set": {"last_update_check": now_iso()}}, upsert=True)
    return await db.components.find({}, {"_id": 0}).to_list(None)


@api.get("/updates")
async def get_updates():
    s = await get_settings()
    last = s.get("last_update_check")
    if not last or datetime.fromisoformat(last) < datetime.now(timezone.utc) - timedelta(days=7):
        rows = await run_update_check()
    else:
        rows = await db.components.find({}, {"_id": 0}).to_list(None)
    order = [c[0] for c in updates.COMPONENTS]
    return {"last_check": (await get_settings()).get("last_update_check"), "components": sorted(rows, key=lambda r: order.index(r["key"]))}


@api.post("/updates/check")
async def check_updates():
    last = (await get_settings()).get("last_update_check")
    if not last or datetime.fromisoformat(last) < datetime.now(timezone.utc) - timedelta(minutes=2):
        async with io_lock:
            await run_update_check()
    return await get_updates()


@api.post("/updates/{key}/apply")
async def apply_update(key: str):
    async with io_lock:
        comp = await db.components.find_one({"key": key}, {"_id": 0})
        if not comp or comp.get("status") != "update_available":
            raise HTTPException(409, "No update available for this component")
        entry = {"from": comp["installed_version"], "to": comp["latest_version"], "at": now_iso(), "result": "installed"}
        await db.components.update_one({"key": key}, {"$set": {"installed_version": comp["latest_version"], "previous_version": comp["installed_version"], "status": "up_to_date"},
                                                      "$push": {"history": entry}})
        return {"ok": True, "installed_version": comp["latest_version"]}


@api.post("/updates/{key}/rollback")
async def rollback_update(key: str):
    async with io_lock:
        comp = await db.components.find_one({"key": key}, {"_id": 0})
        if not comp or not comp.get("previous_version"):
            raise HTTPException(409, "There is no earlier version to go back to")
        entry = {"from": comp["installed_version"], "to": comp["previous_version"], "at": now_iso(), "result": "rolled back"}
        await db.components.update_one({"key": key}, {"$set": {"installed_version": comp["previous_version"], "previous_version": None,
                                                               "status": "update_available"}, "$push": {"history": entry}})
        return {"ok": True}


@api.put("/settings/auto-install")
async def set_auto_install(body: AutoInstallIn):
    await db.settings.update_one({"_id": "app"}, {"$set": {"auto_install_updates": body.auto_install}}, upsert=True)
    return {"ok": True}


# ---------- backups ----------
@api.get("/backups")
async def list_backups():
    return await db.backups.find({}, {"_id": 0, "data": 0}).sort("created_at", -1).limit(30).to_list(30)


@api.post("/backups")
async def backup_now():
    async with io_lock:
        return await create_backup("Manual backup", automatic=False)


@api.post("/backups/{backup_id}/restore")
async def restore_backup(backup_id: str):
    async with io_lock:
        b = await db.backups.find_one({"id": backup_id}, {"_id": 0})
        if not b:
            raise HTTPException(404, "Backup not found")
        if checksum(b["data"]) != b["checksum"]:
            raise HTTPException(422, "This backup failed its integrity check and was not restored")
        prefs = await get_settings()
        await create_backup("Before restoring a backup", automatic=False)
        for col in BACKUP_COLLECTIONS:
            await db[col].delete_many({})
            if b["data"][col]:
                await db[col].insert_many([dict(d) for d in b["data"][col]])
        keep = {k: prefs.get(k) for k in ("auto_install_updates", "last_update_check")}
        await db.settings.update_one({"_id": "app"}, {"$set": keep}, upsert=True)
        return {"ok": True, "restored_from": b["created_at"]}


app.include_router(api)
app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
                   allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.on_event("startup")
async def start_index_build():
    app.state.index_task = asyncio.create_task(ensure_indexes())


@app.on_event("shutdown")
async def shutdown_db_client():
    app.state.index_task.cancel()
    with suppress(asyncio.CancelledError):
        await app.state.index_task
    client.close()
