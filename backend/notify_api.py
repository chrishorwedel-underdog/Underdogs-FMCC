"""In-game countdowns, missed-date notices and the in-app notification centre. Nothing is backfilled silently."""
from datetime import date, timedelta
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db, active_career, now_iso, new_id
import features_api

router = APIRouter(prefix="/api/notify")
TYPES = {"youth": "Youth intake happened", "report": "New monthly report", "missed": "Missed dates", "countdown": "Countdown reaching 7 days", "changes": "Game changes waiting",
         "save": "New save read", "updates": "Add-on updates", "dof": "DOF suggestions waiting", "contract": "Shortlisted player enters his final year"}
PAGE = {"report": "/reports", "missed": "/reports", "countdown": "/", "changes": "/changes", "save": "/", "updates": "/settings", "dof": "/dof", "contract": "/scouting?tab=shortlist", "youth": "/scouting?tab=youth"}


def _d(s: str) -> date:
    return date.fromisoformat(s[:10])


def _first_next_month(d: date) -> date:
    return date(d.year + (d.month == 12), d.month % 12 + 1, 1)


def _next(d: date, month: int, day: int = 1) -> date:
    t = date(d.year, month, day)
    return t if t > d else date(d.year + 1, month, day)


def span(days: int) -> str:
    if days <= 0:
        return "today"
    m, r = divmod(days, 30)
    return f"in {days} day{'s' if days != 1 else ''}" if not m else f"in {m} month{'s' if m > 1 else ''}" + (f" {r} day{'s' if r != 1 else ''}" if r else "")


def countdowns(gd: date, players: list) -> list:
    rows = [("reports", "Monthly report", _first_next_month(gd), "/reports", False, 31),
            ("development", "Monthly minutes targets checked", _first_next_month(gd), "/development", False, 31),
            ("dp", "Dynamic Potential review", min(_next(gd, 1), _next(gd, 7)), "/dynamic-potential", True, 182),
            ("elite", "Elite Training intake", min(_next(gd, 9), _next(gd, 1)), "/elite-training", True, 182),
            ("breakout", "Breakout Player of the season", _next(gd, 5, 31), "/breakout", True, 365),
            ("window", "January window opens", _next(gd, 1), "/scouting", True, 365),
            ("window", "Summer window opens", _next(gd, 6, 9), "/scouting", True, 365)]
    out = [{"key": f"{k}:{t.isoformat()}", "page": k, "label": l, "date": t.isoformat(), "days": (t - gd).days, "text": f"{l} {span((t - gd).days)}", "link": link,
            "estimated": est, "progress": max(0, min(100, round(100 - (t - gd).days / tot * 100)))} for k, l, t, link, est, tot in rows]
    for p in players:
        if p.get("contract_end"):
            t = _d(p["contract_end"])
            if 0 <= (t - gd).days <= 183:
                out.append({"key": f"contract:{p['unique_id']}:{t.isoformat()}", "page": "squad", "label": f"{p['name']}'s contract ends", "date": t.isoformat(),
                            "days": (t - gd).days, "text": f"{p['name']}'s contract ends {span((t - gd).days)}", "link": "/squad?view=players", "estimated": False,
                            "progress": max(0, min(100, round(100 - (t - gd).days / 183 * 100)))})
    return sorted(out, key=lambda r: r["days"])


async def _snaps(cid: str) -> list:
    return await db.snapshots.find({"career_id": cid}, {"_id": 0, "save_no": 1, "game_date": 1, "read_at": 1, "players.unique_id": 1, "players.name": 1,
                                                        "players.contract_end": 1}).sort("save_no", 1).to_list(500)


def missed(snaps: list) -> list:
    out = []
    for a, b in zip(snaps, snaps[1:]):
        m = _first_next_month(_d(a["game_date"]))
        while m < date(_d(b["game_date"]).year, _d(b["game_date"]).month, 1):
            out.append({"key": f"missed:{m:%Y-%m}", "month": f"{m:%B %Y}", "nearest_save": b["save_no"] + 1, "nearest_date": b["game_date"],
                        "text": f"The {m:%B} report was missed because no save was read in {m:%B %Y}."})
            m = _first_next_month(m)
    return out


async def prefs() -> dict:
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "notify_prefs": 1}) or {}
    return {k: True for k in TYPES} | (s.get("notify_prefs") or {})


async def _add(cid: str, typ: str, key: str, title: str, text: str, game_date: str):
    await db.notices.update_one({"career_id": cid, "key": key}, {"$setOnInsert": {"id": new_id(), "career_id": cid, "key": key, "type": typ, "title": title, "text": text,
                                                                                 "link": PAGE[typ], "game_date": game_date, "at": now_iso(), "read": False, "hidden": False}}, upsert=True)


async def sync(c: dict) -> None:
    import scouting_api
    snaps = await _snaps(c["id"])
    if not snaps:
        return
    last = snaps[-1]
    gd = _d(last["game_date"])
    for s in snaps[-3:]:
        await _add(c["id"], "save", f"save:{s['save_no']}", f"New save read: {_d(s['game_date']):%-d %b %Y}", f"Save #{s['save_no'] + 1} was read.", s["game_date"])
    for a, b in zip(snaps, snaps[1:]):
        if _d(a["game_date"]).month != _d(b["game_date"]).month:
            addr = ((await db.settings.find_one({"_id": "app"}, {"_id": 0, "address": 1})) or {}).get("address") or "Boss"
            await _add(c["id"], "report", f"report:{_d(a['game_date']):%Y-%m}", f"{_d(a['game_date']):%B} report ready", f"Your monthly squad report is in Monthly Reports, {addr}.", b["game_date"])
    if len(snaps) > 1:
        import scout_plus
        prev = _d(snaps[-2]["game_date"])
        try:
            rows = (await scout_plus.intake_state(c))["rows"]
        except (HTTPException, ValueError):
            rows = []
        for r in rows:
            t = scout_plus.intake_day(gd.year, r["mmdd"])
            if r["on"] and prev < t <= gd:
                await _add(c["id"], "youth", f"youth:{r['league']}:{t.year}", f"Youth intake: {r['league']}", f"The {r['league']} youth intake happened on {t:%-d %B}. New youngsters are in the save.", last["game_date"])
    done = {d["key"] async for d in db.missed_dates.find({"career_id": c["id"]}, {"key": 1})}
    for m in missed(snaps):
        if m["key"] not in done:
            await _add(c["id"], "missed", m["key"], f"{m['month']} report missed", m["text"], last["game_date"])
    for cd in countdowns(gd, []):
        if 0 <= cd["days"] <= 7:
            await _add(c["id"], "countdown", f"cd:{cd['key']}", cd["text"][0].upper() + cd["text"][1:], "Coming up soon in your save.", last["game_date"])
    pending = await db.changes.count_documents({"career_id": c["id"], "status": "queued"})
    if pending:
        await _add(c["id"], "changes", f"changes:{last['save_no']}:{pending}", f"{pending} game change{'s' if pending > 1 else ''} waiting", "Approve or reject them in Game changes.", last["game_date"])
    async for comp in db.components.find({"status": "update_available"}, {"_id": 0, "key": 1, "name": 1, "latest_version": 1}):
        await _add(c["id"], "updates", f"update:{comp['key']}:{comp.get('latest_version')}", f"{comp.get('name', comp['key'])} update available", f"Version {comp.get('latest_version')} is out.", last["game_date"])
    convs = [d["id"] async for d in db.dof_conversations.find({"career_id": c["id"]}, {"id": 1})]
    waiting = await db.dof_messages.count_documents({"conversation_id": {"$in": convs}, "draft.status": "pending"})
    if waiting:
        await _add(c["id"], "dof", f"dof:{last['save_no']}:{waiting}", f"{waiting} DOF suggestion{'s' if waiting > 1 else ''} waiting", "Open the DOF chat to accept or dismiss.", last["game_date"])
    sl = await scouting_api.shortlisted(c["id"])
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players.unique_id": 1, "players.name": 1, "players.contract_end": 1}) or {"players": []}
    for p in pool["players"]:
        if p["unique_id"] in sl and p.get("contract_end") and 0 <= (_d(p["contract_end"]) - gd).days <= 365:
            await _add(c["id"], "contract", f"contract:{p['unique_id']}:{p['contract_end'][:4]}", f"{p['name']} enters his final year", f"Contract ends {_d(p['contract_end']):%-d %b %Y}.", last["game_date"])


@router.get("/countdowns")
async def get_countdowns():
    c = await active_career()
    snaps = await _snaps(c["id"])
    if not snaps:
        return {"game_date": None, "items": [], "missed": []}
    done = {d["key"]: d async for d in db.missed_dates.find({"career_id": c["id"]}, {"_id": 0})}
    offs = features_api.off(c)
    items = [x for x in countdowns(_d(snaps[-1]["game_date"]), [p for p in await _own(c)]) if features_api.COUNTDOWN.get(x["page"]) not in offs]
    return {"game_date": snaps[-1]["game_date"], "items": items,
            "missed": [m | {"handled": done.get(m["key"])} for m in missed(snaps)] if "reports" not in offs else []}


async def _own(c: dict) -> list:
    s = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}, sort=[("save_no", -1)])
    return (s or {}).get("players") or []


class MissedIn(BaseModel):
    action: Literal["late", "dismiss"]


@router.post("/missed/{key}")
async def handle_missed(key: str, body: MissedIn):
    c = await active_career()
    m = next((m for m in missed(await _snaps(c["id"])) if m["key"] == key), None)
    if not m:
        raise HTTPException(404, "That missed date isn't in this career")
    doc = {"id": new_id(), "career_id": c["id"], "key": key, "action": body.action, "at": now_iso(),
           "label": f"Late {m['month']} report, made from save #{m['nearest_save']} ({m['nearest_date']})" if body.action == "late" else "Dismissed"}
    await db.missed_dates.update_one({"career_id": c["id"], "key": key}, {"$setOnInsert": doc}, upsert=True)
    await db.notices.update_many({"career_id": c["id"], "key": key}, {"$set": {"read": True}})
    return {"ok": True, "label": doc["label"]}


@router.get("")
async def notices():
    c = await active_career()
    await sync(c)
    p = await prefs()
    offs = features_api.off(c)
    rows = await db.notices.find({"career_id": c["id"], "hidden": False, "type": {"$in": [k for k, v in p.items() if v]}}, {"_id": 0, "career_id": 0}).sort("at", -1).to_list(100)
    rows = [r for r in rows if not features_api.path_off(r["link"], offs) and not (r["type"] == "countdown" and _cd_off(r["key"], offs))]
    badges = sorted({r["link"].split("?")[0] for r in rows if not r["read"]})
    return {"items": rows, "unread": sum(not r["read"] for r in rows), "badges": badges,
            "badge_items": {b: [r["title"] for r in rows if not r["read"] and r["link"].split("?")[0] == b][:5] for b in badges}}


def _cd_off(key: str, offs: set) -> bool:
    return features_api.COUNTDOWN.get(key.split(":")[1] if key.count(":") >= 1 else "") in offs


class PageIn(BaseModel):
    path: str


@router.post("/read-page")
async def read_page(body: PageIn):
    """Opening a page marks its notices read, so its menu dot clears."""
    c = await active_career()
    links = [v for v in PAGE.values() if v.split("?")[0] == body.path]
    r = await db.notices.update_many({"career_id": c["id"], "read": False, "link": {"$in": links}}, {"$set": {"read": True}})
    return {"ok": True, "marked": r.modified_count}


@router.post("/{nid}/read")
async def mark_read(nid: str):
    c = await active_career()
    await db.notices.update_one({"career_id": c["id"], "id": nid}, {"$set": {"read": True}})
    return {"ok": True}


@router.post("/read-all")
async def read_all():
    c = await active_career()
    await db.notices.update_many({"career_id": c["id"]}, {"$set": {"read": True}})
    return {"ok": True}


@router.post("/clear")
async def clear():
    c = await active_career()
    await db.notices.update_many({"career_id": c["id"]}, {"$set": {"hidden": True, "read": True}})
    return {"ok": True}


@router.get("/prefs")
async def get_prefs():
    return {"prefs": await prefs(), "labels": TYPES}


@router.put("/prefs")
async def put_prefs(body: dict[str, bool]):
    if set(body) - set(TYPES):
        raise HTTPException(422, "Unknown notification type")
    await db.settings.update_one({"_id": "app"}, {"$set": {f"notify_prefs.{k}": v for k, v in body.items()}}, upsert=True)
    return {"ok": True}
