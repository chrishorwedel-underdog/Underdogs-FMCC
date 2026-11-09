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
import roles  # noqa: E402
import sample_reader  # noqa: E402
import updates  # noqa: E402
from core import (db, client, logger, io_lock, BACKUP_COLLECTIONS, EXTRA_INDEXES, now_iso, get_settings, active_career,  # noqa: E402
                  latest_two, checksum, create_backup)
from squad_api import router as squad_router  # noqa: E402
from scouting_api import router as scouting_router  # noqa: E402
from plans_api import router as plans_router  # noqa: E402
from awards_api import router as awards_router  # noqa: E402
from rules_api import router as rules_router  # noqa: E402
from changes_api import router as changes_router, resume_unfinished, stop_all  # noqa: E402
from matches_api import router as matches_router  # noqa: E402
from dof_api import router as dof_router  # noqa: E402
from connections_api import router as connections_router  # noqa: E402
from editor_api import router as editor_router  # noqa: E402
from licensing_api import router as licensing_router  # noqa: E402
from leagues_api import router as leagues_router  # noqa: E402
from scout_api import router as scout_router  # noqa: E402
from graphics_api import router as graphics_router  # noqa: E402
from lab_api import router as lab_router  # noqa: E402
from setup_api import router as setup_router  # noqa: E402
from testing_api import router as testing_router  # noqa: E402
from punish_api import router as punish_router  # noqa: E402
from recruit_api import router as recruit_router  # noqa: E402
from notify_api import router as notify_router  # noqa: E402
from creator_api import router as creator_router  # noqa: E402
from creator_extras import router as creator_extras_router  # noqa: E402
from extras_api import router as extras_router  # noqa: E402
import world_api  # noqa: E402
import sample_matches  # noqa: E402

INDEXES: dict[str, list[IndexModel]] = {
    "careers": [IndexModel([("id", ASCENDING)], name="id", unique=True)],
    "identities": [IndexModel([("career_id", ASCENDING), ("unique_id", ASCENDING)], name="career_uid", unique=True)],
    "snapshots": [
        IndexModel([("id", ASCENDING)], name="id", unique=True),
        IndexModel([("career_id", ASCENDING), ("save_no", DESCENDING)], name="career_save", unique=True),
    ],
    "backups": [IndexModel([("id", ASCENDING)], name="id", unique=True), IndexModel([("created_at", DESCENDING)], name="created_desc")],
    "components": [IndexModel([("key", ASCENDING)], name="key", unique=True)],
} | EXTRA_INDEXES


async def ensure_indexes() -> None:
    for collection, models in INDEXES.items():
        for model in models:
            try:
                await db[collection].create_indexes([model])
            except Exception as exc:
                logger.error("ensure_indexes(%s.%s): %s", collection, model.document["name"], exc)


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


class AutoReadIn(BaseModel):
    auto_read: bool


# ---------- helpers ----------
READER = os.environ.get("FMCC_READER", "sample")


def _read_save_file(career: dict, save_no: int, edits: dict) -> dict:
    if READER != "fmsave":
        return sample_reader.read_save(save_no, career["club_name"], edits)
    import fmsave_reader
    path = fmsave_reader.latest_save(career["save_folder"])
    if not path:
        raise HTTPException(404, "No .fm save found in your save folder")
    if career.get("last_file") == f"{path.name}:{path.stat().st_mtime}":
        raise HTTPException(409, "No new save since the last read")
    try:
        return fmsave_reader.read_save(path, career["club_name"])
    except Exception as exc:
        logger.error("fmsave read failed: %s", exc)
        raise HTTPException(422, f"FMCC couldn't read {path.name}: {exc}")


async def read_next_save(career: dict) -> dict:
    """Read the next save into a snapshot. Players are matched by the game's unique ID, never by name."""
    save_no = career.get("next_save_no", 0)
    await create_backup(f"{career['name']}: before reading save #{save_no + 1}", automatic=True)
    edits = {e["unique_id"]: e for e in await db.game_edits.find({"career_id": career["id"]}, {"_id": 0}).to_list(None)}
    save = await asyncio.to_thread(_read_save_file, career, save_no, edits)
    pool = save.pop("pool")
    club_list = save.pop("clubs", None)
    tables = save.pop("tables", None)
    if tables:
        import leagues_api
        from core import audit
        renames = world_api.name_unnamed(tables, pool, (await leagues_api.opta_list(career["id"]))["leagues"])
        if renames:
            await audit(career["id"], "league names", "world", f"{len(renames)} unnamed competition(s) named from the league strength workbook")
    file_mtime = save.pop("file_mtime", None)
    snap = {"id": str(uuid.uuid4()), "career_id": career["id"], "save_no": save_no, "read_at": now_iso(),
            "reader": sample_reader.READER_NAME, **save}
    await db.snapshots.insert_one(dict(snap))
    old_pool = await db.pools.find_one({"career_id": career["id"]}, {"_id": 0, "season": 1, "season_start_ca": 1}) or {}
    start = old_pool.get("season_start_ca", {}) if old_pool.get("season") == save["season"] else {}
    for p in pool:
        start.setdefault(str(p["unique_id"]), p["ca"])
    await db.pools.update_one({"career_id": career["id"]}, {"$set": {"save_no": save_no, "season": save["season"], "game_date": save["game_date"],
                                                                    "players": pool, "season_start_ca": start} | ({"clubs": club_list} if club_list else {})}, upsert=True)
    await world_api.record_month(career["id"], {"save_no": save_no, "season": save["season"], "game_date": save["game_date"], "players": pool, "tables": tables})
    ml = (await db.settings.find_one({"_id": "app"}, {"_id": 0, "matchlens": 1}) or {}).get("matchlens") or {}
    if ml.get("installed") and READER == "sample":
        opponents = sorted({p["club"] for p in pool if p["league"] == "Premier Division"})
        for m in sample_matches.play_month(save_no, save["game_date"], career["club_name"], save["players"], pool, opponents):
            await db.matches.update_one({"career_id": career["id"], "save_no": save_no, "match_no": m["match_no"]},
                                        {"$setOnInsert": m | {"id": str(uuid.uuid4()), "career_id": career["id"], "season": save["season"]}}, upsert=True)
    for p in save["players"]:
        await db.identities.update_one(
            {"career_id": career["id"], "unique_id": p["unique_id"]},
            {"$set": {"name": p["name"], "last_seen_save": save_no, "last_seen_date": save["game_date"]},
             "$setOnInsert": {"first_seen_save": save_no, "first_seen_date": save["game_date"]}}, upsert=True)
    res = await db.careers.update_one({"id": career["id"], "next_save_no": save_no},
                                      {"$set": {"next_save_no": save_no + 1, "last_read_at": snap["read_at"], "last_game_date": save["game_date"],
                                                "last_file": f"{save['file_name']}:{file_mtime}" if file_mtime else None}})
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
    return {"setup_complete": s.get("setup_complete", False), "career": career, "sample_mode": READER == "sample",
            "auto_install_updates": s.get("auto_install_updates", False), "last_update_check": s.get("last_update_check"),
            "auto_read_saves": s.get("auto_read_saves", True)}


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
        await db.settings.update_one({"_id": "app"}, {"$set": {"setup_complete": True, "auto_install_updates": False}, "$unset": {"setup_progress": ""}}, upsert=True)
    latest = (await latest_two(career["id"]))[0]
    return {"career": career, "health": [
        {"key": "link", "label": "Game link ready", "ok": True, "detail": f"Read {len(latest['players'])} players from {latest['file_name']}" + (" (sample save)" if READER == "sample" else "")},
        {"key": "analytics", "label": "Match analytics", "ok": False, "detail": "Not set up yet. Install the match add-on from Connections."},
        {"key": "dof", "label": "DOF chat", "ok": READER == "sample", "detail": "Ready (preview key)" if READER == "sample" else "Add your OpenAI key in Settings."},
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


@api.get("/saves/{save_no}/check")
async def check_save(save_no: int):
    """'Check my save': what FMCC read from one save, so a real-save read can be verified on your PC."""
    c = await active_career()
    snap = await db.snapshots.find_one({"career_id": c["id"], "save_no": save_no}, {"_id": 0})
    if not snap:
        raise HTTPException(404, "That save hasn't been read in this career")
    prev = await db.snapshots.find_one({"career_id": c["id"], "save_no": {"$lt": save_no}}, {"_id": 0, "players.unique_id": 1, "players.name": 1}, sort=[("save_no", -1)])
    before = {p["unique_id"]: p["name"] for p in prev["players"]} if prev else {}
    now = {p["unique_id"]: p for p in snap["players"]}
    gaps = {"birth date": sum(1 for p in snap["players"] if not p.get("birth_date")), "average rating": sum(1 for p in snap["players"] if p.get("avg_rating") is None),
            "potential (PA)": sum(1 for p in snap["players"] if not p.get("pa")), "attributes": sum(1 for p in snap["players"] if not any((p.get("attributes") or {}).values()))}
    renamed = [f"{before[u]} → {p['name']}" for u, p in now.items() if u in before and before[u] != p["name"]]
    return {"save_no": save_no, "file_name": snap["file_name"], "game_date": snap["game_date"], "read_at": snap["read_at"], "reader": snap["reader"],
            "club_name": snap.get("club_name"), "players": len(now), "same_ids": sum(1 for u in now if u in before),
            "new_players": [p["name"] for u, p in now.items() if prev and u not in before], "left": [n for u, n in before.items() if u not in now],
            "renamed": renamed, "gaps": {k: v for k, v in gaps.items() if v}, "first": prev is None}


@api.get("/notices")
async def notices():
    c = await active_career()
    return await db.notices.find({"career_id": c["id"], "seen": False}, {"_id": 0}).sort("at", 1).to_list(20)


@api.post("/notices/{notice_id}/seen")
async def notice_seen(notice_id: str):
    await db.notices.update_one({"id": notice_id}, {"$set": {"seen": True}})
    return {"ok": True}


@api.put("/settings/auto-read")
async def set_auto_read(body: AutoReadIn):
    await db.settings.update_one({"_id": "app"}, {"$set": {"auto_read_saves": body.auto_read}}, upsert=True)
    return {"ok": True}


async def watch_saves():
    """Windows program: reads each new save once FM has finished writing it (the file stops changing)."""
    import time
    import fmsave_reader
    last_seen, failed = {}, set()
    while True:
        await asyncio.sleep(3)
        try:
            s = await get_settings()
            if not s.get("auto_read_saves", True) or not s.get("active_career_id"):
                continue
            c = await db.careers.find_one({"id": s["active_career_id"]}, {"_id": 0})
            path = c and await asyncio.to_thread(fmsave_reader.latest_save, c["save_folder"])
            if not path:
                continue
            st = path.stat()
            sig = f"{path.name}:{st.st_mtime}"
            if sig == c.get("last_file") or sig in failed:
                continue
            if last_seen.get(sig) != st.st_size or time.time() - st.st_mtime < 5:
                last_seen = {sig: st.st_size}
                continue
            async with io_lock:
                c = await db.careers.find_one({"id": c["id"]}, {"_id": 0})
                try:
                    r = await read_next_save(c)
                    note = {"kind": "save_read", **r}
                except HTTPException as exc:
                    if exc.status_code == 409:
                        continue
                    failed.add(sig)
                    note = {"kind": "save_failed", "file_name": path.name, "message": exc.detail}
            await db.notices.insert_one({"id": str(uuid.uuid4()), "career_id": c["id"], "at": now_iso(), "seen": False, **note})
        except asyncio.CancelledError:
            raise
        except Exception as exc:
            logger.warning("save watcher: %s", exc)


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
    pending = await db.changes.count_documents({"career_id": c["id"], "status": "queued"})
    return dashboard.compute(snaps[0], snaps[1] if len(snaps) > 1 else None, b["created_at"] if b else None) | {"read_at": snaps[0]["read_at"], "pending_changes": pending}


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
    form = roles.formation_meta("433")
    xi_ids = set(roles.best_xi(latest["players"], form, roles.depth_chart(latest["players"], form)).values())
    idents = {i["unique_id"]: i for i in await db.identities.find({"career_id": c["id"]}, {"_id": 0}).to_list(None)}
    players = []
    for p in latest["players"]:
        prior = before.get(p["unique_id"])
        players.append({k: v for k, v in p.items() if k not in ("ca", "pa")} | {"ca_change": p["ca"] - prior["ca"] if prior else None,
                            "is_new": idents.get(p["unique_id"], {}).get("first_seen_save") == latest["save_no"] and latest["save_no"] > 0,
                            "shared_name": names[p["name"]] > 1, "in_best_xi": p["unique_id"] in xi_ids, "best_role": roles.best_role(p)})
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
    latest = snaps[-1]["players"][0] if snaps else None
    return {"identity": ident, "latest": latest, "history": history, "role_ratings": roles.role_ratings(latest)[:6] if latest else []}


# ---------- updates ----------
async def run_update_check() -> list:
    for key, name, role, repo, bundled in updates.COMPONENTS:
        existing = await db.components.find_one({"key": key}, {"_id": 0}) or {}
        installed = bundled if key == "fmcc" else existing.get("installed_version", bundled)
        row = {"key": key, "name": name, "role": role, "repo": repo, "installed_version": installed, "checked_at": now_iso()}
        if not repo:
            row |= {"status": "no_source", "latest_version": None, "message": "Release page not set yet"}
        elif repo.startswith("page:"):
            try:
                rel = await updates.fetch_page_version(repo[5:])
                row |= {"latest_version": rel, "release_url": repo[5:], "status": "manual" if rel else "check_failed", "manual": True,
                        "message": f"Latest {rel}. FMCC never installs it; download it from its page." if rel else "Couldn't read the version from its page"}
            except Exception:
                row |= {"status": "check_failed", "manual": True, "release_url": repo[5:], "message": "Couldn't reach its page"}
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
        await stop_all()
        await create_backup("Before restoring a backup", automatic=False)
        for col in BACKUP_COLLECTIONS:
            await db[col].delete_many({})
            if b["data"][col]:
                await db[col].insert_many([dict(d) for d in b["data"][col]])
        keep = {k: prefs.get(k) for k in ("auto_install_updates", "last_update_check", "matchlens", "auto_read_saves") if k in prefs}
        await db.settings.update_one({"_id": "app"}, {"$set": keep}, upsert=True)
        await resume_unfinished()
        return {"ok": True, "restored_from": b["created_at"]}


app.include_router(api)
for r in (squad_router, scouting_router, plans_router, awards_router, rules_router, changes_router, matches_router, dof_router, connections_router, editor_router, licensing_router, leagues_router, scout_router, graphics_router, lab_router, setup_router, testing_router, punish_router, recruit_router, notify_router, creator_router, creator_extras_router, extras_router, world_api.router):
    app.include_router(r)
if os.environ.get("FMCC_STATIC_DIR"):
    from fastapi.responses import FileResponse
    from fastapi.staticfiles import StaticFiles
    _static = Path(os.environ["FMCC_STATIC_DIR"])
    app.mount("/static", StaticFiles(directory=_static / "static"), name="static")

    @app.get("/{path:path}", include_in_schema=False)
    async def spa(path: str):
        f = _static / path
        return FileResponse(f if path and f.is_file() else _static / "index.html")

app.add_middleware(CORSMiddleware, allow_credentials=True, allow_origins=os.environ.get('CORS_ORIGINS', '*').split(','),
                   allow_methods=["*"], allow_headers=["*"])
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')


@app.on_event("startup")
async def start_index_build():
    app.state.index_task = asyncio.create_task(ensure_indexes())
    asyncio.create_task(resume_unfinished())
    if READER == "fmsave":
        app.state.watcher = asyncio.create_task(watch_saves())


@app.on_event("shutdown")
async def shutdown_db_client():
    app.state.index_task.cancel()
    with suppress(asyncio.CancelledError):
        await app.state.index_task
    client.close()
