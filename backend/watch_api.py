"""Watchlist alerts and the weekly "What changed" panel. Uses FMCC grades and scouting views only; real CA/PA are never stored or shown here."""
import os
from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db, active_career, now_iso
import stats_model as sm

router = APIRouter(prefix="/api/watch")
SOURCE = {"dp": "Dynamic Potential review", "editor": "Player & Teams Editor", "punish": "Punish a Club", "elite": "Elite Training", "breakout": "Breakout Player",
          "shortlist": "FM shortlist", "seed": "Seed a Surname", "creator": "Player Creator", "lineup": "Squad lineup", "dof": "Director of Football"}
SOURCE_LINK = {"dp": "/dynamic-potential", "editor": "/editor", "punish": "/punish", "elite": "/elite-training", "breakout": "/breakout"}


def _free(club) -> bool:
    return not club or str(club).lower() in {"free agent", "free agents", "none", "unattached"}


def _view(x: dict) -> dict:
    return {"name": x["name"], "club": x.get("club"), "grade": x.get("grade_global"), "value": x.get("value") or 0,
            "contract_end": x.get("contract_end"), "months_left": x.get("months_left"), "own": bool(x.get("own"))}


def changes_between(a: dict, b: dict) -> list:
    """What moved between two views of one player: grade ±2, value ±10%, or any contract status change."""
    out = []
    if a.get("grade") is not None and b.get("grade") is not None and abs(b["grade"] - a["grade"]) >= 2:
        out.append(("grade", f"Grade {'rose' if b['grade'] > a['grade'] else 'fell'} from {a['grade']} to {b['grade']}", "up" if b["grade"] > a["grade"] else "down"))
    if a.get("value") and b.get("value") is not None and abs(b["value"] - a["value"]) / a["value"] >= 0.10:
        up = b["value"] > a["value"]
        out.append(("value", f"Value {'rose' if up else 'fell'} from £{a['value'] / 1e6:.1f}m to £{b['value'] / 1e6:.1f}m", "up" if up else "down"))
    if _free(b.get("club")) and not _free(a.get("club")):
        out.append(("contract", f"Became a free agent (left {a.get('club')})", "info"))
    elif a.get("club") != b.get("club") and not _free(b.get("club")):
        out.append(("contract", f"Transferred from {a.get('club') or 'free agency'} to {b.get('club')}", "info"))
    elif b.get("contract_end") and a.get("contract_end") and b["contract_end"] > a["contract_end"]:
        out.append(("contract", f"Signed a new deal until {b['contract_end'][:4]}", "up"))
    elif (b.get("months_left") is not None and b["months_left"] <= 6) and not (a.get("months_left") is not None and a["months_left"] <= 6):
        out.append(("contract", f"Entered the last 6 months of his contract ({b.get('contract_end')})", "down"))
    return out


async def _current(c: dict) -> tuple[dict, dict]:
    data = await sm.build(c)
    if not data["players"]:
        raise HTTPException(404, "No scouting data yet. Read a save first.")
    return data, {x["unique_id"]: x for x in data["players"] if x.get("source") == "save"}


async def _save_no(c: dict) -> int:
    s = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "save_no": 1}, sort=[("save_no", -1)])
    return s["save_no"] if s else -1


async def _mark(c: dict, save_no: int, game_date: str, by: dict) -> None:
    watched = {w["unique_id"] async for w in db.watchlist.find({"career_id": c["id"]}, {"unique_id": 1})}
    rows = {str(u): _view(x) for u, x in by.items() if x.get("own") or u in watched}
    await db.grade_marks.update_one({"career_id": c["id"], "save_no": save_no}, {"$setOnInsert": {"career_id": c["id"], "save_no": save_no, "game_date": game_date, "at": now_iso(), "players": rows}}, upsert=True)


async def check(c: dict) -> int:
    """Runs once per save read: compares every watched player with what FMCC last saw and raises bell notices."""
    from notify_api import _add
    save_no = await _save_no(c)
    if save_no < 0 or c.get("watch_checked_save") == save_no:
        return 0
    data, by = await _current(c)
    await _mark(c, save_no, data.get("game_date") or "", by)
    n = 0
    async for w in db.watchlist.find({"career_id": c["id"]}, {"_id": 0}):
        x = by.get(w["unique_id"])
        if not x:
            continue
        now = _view(x)
        for kind, text, tone in changes_between(w["last"], now):
            n += 1
            await _add(c["id"], "watch", f"watch:{w['unique_id']}:{save_no}:{kind}", f"{now['name']}: {text.split(' (')[0][0].lower()}{text.split(' (')[0][1:]}", text + ".", data.get("game_date") or "")
            await db.notices.update_one({"career_id": c["id"], "key": f"watch:{w['unique_id']}:{save_no}:{kind}"}, {"$set": {"link": f"/scouting?tab=watchlist&player={w['unique_id']}"}})
            await db.watchlist.update_one({"career_id": c["id"], "unique_id": w["unique_id"]},
                                          {"$push": {"log": {"$each": [{"kind": kind, "text": text, "tone": tone, "game_date": data.get("game_date"), "at": now_iso()}], "$slice": -20}}})
        await db.watchlist.update_one({"career_id": c["id"], "unique_id": w["unique_id"]}, {"$set": {"last": now}})
    await db.careers.update_one({"id": c["id"]}, {"$set": {"watch_checked_save": save_no}})
    return n


class WatchIn(BaseModel):
    unique_id: int


@router.get("")
async def watchlist():
    c = await active_career()
    rows = await db.watchlist.find({"career_id": c["id"]}, {"_id": 0, "career_id": 0}).sort("added_at", -1).to_list(500)
    return {"rows": [r | {"latest": (r.get("log") or [None])[-1]} for r in rows], "ids": [r["unique_id"] for r in rows]}


@router.post("")
async def add(body: WatchIn):
    c = await active_career()
    _, by = await _current(c)
    x = by.get(body.unique_id)
    if not x:
        raise HTTPException(404, "That player isn't in your save")
    await db.watchlist.update_one({"career_id": c["id"], "unique_id": body.unique_id},
                                  {"$setOnInsert": {"career_id": c["id"], "unique_id": body.unique_id, "added_at": now_iso(), "last": _view(x), "log": []}}, upsert=True)
    return {"ok": True, "name": x["name"]}


@router.delete("/{uid}")
async def remove(uid: int):
    c = await active_career()
    r = await db.watchlist.delete_one({"career_id": c["id"], "unique_id": uid})
    if not r.deleted_count:
        raise HTTPException(404, "That player isn't on your watchlist")
    return {"ok": True}


def _parse(s: str) -> datetime:
    return datetime.fromisoformat(s)


@router.get("/digest")
async def digest():
    """What changed since your last visit (up to 7 days), from what FMCC saw when reading the save. Nothing is estimated."""
    c = await active_career()
    await check(c)
    now = datetime.now(timezone.utc)
    prev, last = c.get("digest_prev_visit"), c.get("digest_visit")
    if not last or now - _parse(last) > timedelta(minutes=30):
        prev, last = last, now.isoformat()
        await db.careers.update_one({"id": c["id"]}, {"$set": {"digest_prev_visit": prev, "digest_visit": last}})
    start = max(_parse(prev) if prev else now - timedelta(days=7), now - timedelta(days=7))
    save_no = await _save_no(c)
    marks = await db.grade_marks.find({"career_id": c["id"], "save_no": {"$lt": save_no}}, {"_id": 0}).sort("save_no", -1).to_list(50)
    base = next((m for m in marks if _parse(m["at"]) <= start), None) or next((m for m in reversed(marks) if _parse(m["at"]) > start), None)
    cur = await db.grade_marks.find_one({"career_id": c["id"], "save_no": save_no}, {"_id": 0}) or {"players": {}}
    ratings, contracts = [], []
    if base:
        for uid, now_p in cur["players"].items():
            old = base["players"].get(uid)
            if not now_p.get("own"):
                continue
            if not old:
                contracts.append({"unique_id": int(uid), "name": now_p["name"], "text": f"Joined the squad, contract until {(now_p.get('contract_end') or '')[:4] or 'unknown'}", "tone": "up"})
                continue
            for kind, text, tone in changes_between(old, now_p):
                (ratings if kind == "grade" else contracts if kind == "contract" else []).append({"unique_id": int(uid), "name": now_p["name"], "text": text, "tone": tone})
    applied = await db.changes.find({"career_id": c["id"], "status": "applied", "applied_at": {"$gte": start.isoformat()}},
                                    {"_id": 0, "source": 1, "player_name": 1, "club": 1, "unique_id": 1, "applied_at": 1}).sort("applied_at", -1).to_list(200)
    groups: dict = {}
    for a in applied:
        g = groups.setdefault(a.get("source") or "other", {"source": a.get("source"), "label": SOURCE.get(a.get("source"), "FMCC change"), "count": 0, "names": [], "link": SOURCE_LINK.get(a.get("source"), "/changes")})
        g["count"] += 1
        nm = a.get("player_name") or a.get("club")
        if nm and nm not in g["names"] and len(g["names"]) < 4:
            g["names"].append(nm)
    watch = []
    async for w in db.watchlist.find({"career_id": c["id"]}, {"_id": 0, "unique_id": 1, "last.name": 1, "log": 1}):
        for e in w.get("log") or []:
            if _parse(e["at"]) >= start:
                watch.append({"unique_id": w["unique_id"], "name": w["last"]["name"], "text": e["text"], "tone": e["tone"]})
    ratings.sort(key=lambda r: r["tone"] != "up")
    return {"since": start.isoformat(), "compared_save": base and base["save_no"] + 1, "current_save": save_no + 1, "sample": os.environ.get("FMCC_READER", "sample") == "sample",
            "ratings": ratings[:12], "contracts": contracts[:12], "applied": list(groups.values()), "watch": watch[:12],
            "total": len(ratings) + len(contracts) + sum(g["count"] for g in groups.values()) + len(watch)}
