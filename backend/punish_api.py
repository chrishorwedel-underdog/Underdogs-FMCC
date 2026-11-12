"""Punish a Club: pick any club and penalties. Makes an FMCC editor data file for new careers (FM26 and FM27),
and queues the penalties that can be changed in a running FM27 save as Game changes. Inspired by sortitoutsi's
'Punish Manchester City'; none of its code or files are used. FM accepting the file is UNCONFIRMED until tested on a PC."""
import asyncio
import os
import re
from pathlib import Path
from typing import Optional
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db, active_career, now_iso, new_id, audit

router = APIRouter(prefix="/api/punish")
LIVE = os.environ.get("FMCC_READER") == "fmsave"
ROOT = Path(__file__).parent

# key: (group, label, {param: (min, max, default, unit)}, live club field or None, why it's new-career only)
PENALTIES = {
    "points": ("Sporting", "Points deduction", {"seasons": (1, 10, 1, "seasons"), "points": (1, 120, 15, "points")}, None, "Points can't be changed safely mid-season"),
    "relegation": ("Sporting", "Forced relegation", {}, None, "Relegation is decided when the season is set up"),
    "releases": ("Sporting", "Forced player releases", {"players": (1, 15, 3, "players")}, None, "Releasing players mid-season would break contracts in the save"),
    "morale": ("Sporting", "Lower player and staff morale", {"amount": (1, 20, 5, "levels")}, None, "FMCC can't change morale in a running save yet"),
    "fans": ("Sporting", "Fans hate the club", {}, None, "Supporter feelings are set at the start of a career"),
    "embargo": ("Transfers", "Transfer embargo", {"years": (1, 5, 2, "years"), "age_limit": (16, 40, 21, "age limit")}, None, "Transfer embargoes can't be changed safely mid-season"),
    "wipe_bank": ("Money", "Wipe the bank balance", {}, "balance", None),
    "ffp": ("Money", "Add financial-fair-play losses", {"millions": (1, 1000, 50, "£m")}, None, "FFP history is set at the start of a career"),
    "sponsors": ("Money", "Cancel sponsorship income", {}, None, "Sponsorship deals are set at the start of a career"),
    "reputation": ("Reputation and facilities", "Lower club reputation", {"amount": (100, 5000, 1500, "points")}, "reputation", None),
    "stadium": ("Reputation and facilities", "Lower stadium capacity", {"percent": (5, 80, 30, "%")}, None, "Stadium capacity can't be changed safely mid-season"),
    "facilities": ("Reputation and facilities", "Lower training and youth facilities", {"levels": (1, 15, 5, "levels")}, "training,youth_facilities", None),
}
PRESETS = {
    "light": ("Light", {"points": {"points": 6}, "reputation": {"amount": 500}}),
    "heavy": ("Heavy", {"points": {"points": 30}, "embargo": {"years": 2, "age_limit": 21}, "wipe_bank": {}, "reputation": {"amount": 2000}, "facilities": {"levels": 4}}),
    "full115": ("The full 115", {"points": {"points": 115}, "relegation": {}, "releases": {"players": 5}, "morale": {"amount": 10}, "fans": {},
                                 "embargo": {"years": 3, "age_limit": 16}, "wipe_bank": {}, "ffp": {"millions": 500}, "sponsors": {},
                                 "reputation": {"amount": 4000}, "stadium": {"percent": 50}, "facilities": {"levels": 8}}),
}
WORDS = {1: "one", 2: "two", 3: "three", 4: "four", 5: "five"}


def season_points(v: dict) -> list:
    """Points for each season of a deduction: season 1 is `points`, later seasons are s2..s10."""
    return [v["points"]] + [v[f"s{i}"] for i in range(2, v.get("seasons", 1) + 1)]


class PunishIn(BaseModel):
    club_uid: int
    penalties: dict[str, dict[str, int]] = Field(min_length=1, max_length=len(PENALTIES))
    name: str = Field(default="", max_length=60)


def clean(pens: dict) -> dict:
    out = {}
    for k, params in pens.items():
        if k not in PENALTIES:
            raise HTTPException(422, f"Unknown penalty: {k}")
        spec = PENALTIES[k][2]
        vals = {}
        for p, (lo, hi, default, unit) in spec.items():
            v = int(params.get(p, default))
            if not lo <= v <= hi:
                raise HTTPException(422, f"{PENALTIES[k][1]}: {unit} must be between {lo} and {hi}")
            vals[p] = v
        if k == "points":
            for i in range(2, vals["seasons"] + 1):
                v = int(params.get(f"s{i}", vals["points"]))
                if not 1 <= v <= 120:
                    raise HTTPException(422, f"Points deduction: season {i} points must be between 1 and 120")
                vals[f"s{i}"] = v
        out[k] = vals
    return out


def phrase(k: str, v: dict) -> str:
    return {
        "points": lambda: f"−{v['points']} points" if v.get("seasons", 1) == 1 else
        f"−{' / −'.join(map(str, season_points(v)))} points over {v['seasons']} seasons ({sum(season_points(v))} in total)",
        "relegation": lambda: "relegated",
        "releases": lambda: f"{v['players']} players released",
        "morale": lambda: f"morale down {v['amount']}",
        "fans": lambda: "the fans turn on the club",
        "embargo": lambda: f"{WORDS.get(v['years'], v['years'])}-year transfer ban" + (f" for over-{v['age_limit']}s" if v["age_limit"] > 16 else ""),
        "wipe_bank": lambda: "bank balance set to 0",
        "ffp": lambda: f"£{v['millions']}m FFP losses",
        "sponsors": lambda: "sponsorship income cancelled",
        "reputation": lambda: f"reputation −{v['amount']}",
        "stadium": lambda: f"stadium capacity −{v['percent']}%",
        "facilities": lambda: f"training and youth facilities −{v['levels']}",
    }[k]()


def describe(club: dict, pens: dict, edition: str) -> dict:
    rows = []
    for k, v in pens.items():
        g, label, _, live, why = PENALTIES[k]
        can_live = bool(live) and edition == "FM27"
        rows.append({"key": k, "group": g, "label": label, "text": phrase(k, v), "current_save": can_live,
                     "why_not": None if can_live else (why or "Live changes are FM27 only")})
    return {"summary": f"{club['name']}: " + ", ".join(r["text"] for r in rows), "rows": rows}


async def _club(c: dict, uid: int) -> dict:
    import editor_api
    return await editor_api.club(c, uid)


def _folder(c: dict) -> Path:
    return Path(c["save_folder"]).parent / "editor data" if LIVE else ROOT / "preview_fm" / "editor data"


def _xml(c: dict, club: dict, pens: dict, summary: str) -> str:
    def row(k: str, v: dict) -> str:
        if k == "points":
            return "\n".join(f'    <record id="penalty" type="points" label={quoteattr(PENALTIES[k][1])} season="{i}" points="{p}"/>'
                             for i, p in enumerate(season_points(v), 1))
        return (f'    <record id="penalty" type={quoteattr(k)} label={quoteattr(PENALTIES[k][1])}'
                + "".join(f" {p}={quoteattr(str(x))}" for p, x in v.items()) + "/>")
    rows = "\n".join(row(k, v) for k, v in pens.items())
    return ('<?xml version="1.0" encoding="UTF-8"?>\n'
            "<!-- Made by FMCC Punish a Club. Whether FM accepts this file is unconfirmed until it is tested on your PC. -->\n"
            f'<record id="fmcc_punishment">\n  <string id="edition" value={quoteattr(c["edition"])}/>\n'
            f'  <large id="club_unique_id" value="{club["uid"]}"/>\n  <string id="club_name" value={quoteattr(club["name"])}/>\n'
            f'  <string id="summary" value={quoteattr(summary)}/>\n  <list id="db_changes">\n{rows}\n  </list>\n</record>\n')


def _write(folder: Path, name: str, text: str) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    p = folder / name
    p.write_text(text, encoding="utf-8")
    return str(p)


async def _latest(c: dict) -> list:
    pipe = [{"$match": {"career_id": c["id"]}}, {"$sort": {"revision": -1}}, {"$group": {"_id": "$pid", "doc": {"$first": "$$ROOT"}}}, {"$match": {"doc.status": "active"}}]
    out = [{k: v for k, v in d["doc"].items() if k not in ("_id", "career_id", "xml")} async for d in db.punishments.aggregate(pipe)]
    return sorted(out, key=lambda d: d["at"], reverse=True)


async def _one(c: dict, pid: str) -> dict:
    d = await db.punishments.find_one({"career_id": c["id"], "pid": pid}, {"_id": 0}, sort=[("revision", -1)])
    if not d or d["status"] != "active":
        raise HTTPException(404, "Punishment not found")
    return d


@router.get("/meta")
async def meta():
    c = await active_career()
    return {"edition": c["edition"], "desktop": LIVE,
            "penalties": [{"key": k, "group": g, "label": l, "params": [{"key": p, "min": a, "max": b, "default": d, "unit": u} for p, (a, b, d, u) in ps.items()],
                           "current_save": bool(live)} for k, (g, l, ps, live, _) in PENALTIES.items()],
            "presets": [{"key": k, "name": n, "penalties": p} for k, (n, p) in PRESETS.items()]}


@router.get("/clubs")
async def search_clubs(q: str = ""):
    import editor_api
    c = await active_career()
    q = q.strip().lower()
    return [x for x in await editor_api.clubs(c) if q in x["name"].lower()][:20]


@router.post("/preview")
async def preview(body: PunishIn):
    c = await active_career()
    return describe(await _club(c, body.club_uid), clean(body.penalties), c["edition"])


@router.get("")
async def list_punishments():
    return await _latest(await active_career())


@router.post("")
async def create(body: PunishIn):
    c = await active_career()
    club = await _club(c, body.club_uid)
    pens = clean(body.penalties)
    d = describe(club, pens, c["edition"])
    pid = new_id()
    fname = f"FMCC Punish - {re.sub(r'[^A-Za-z0-9 ._-]', '', club['name'])[:40]} - {pid[:6]}.xml"
    xml = _xml(c, club, pens, d["summary"])
    path = await asyncio.to_thread(_write, _folder(c), fname, xml)
    doc = {"id": new_id(), "pid": pid, "career_id": c["id"], "revision": 1, "status": "active", "club": club, "name": body.name.strip() or f"Punish {club['name']}",
           "penalties": pens, "summary": d["summary"], "rows": d["rows"], "file_name": fname, "file_path": path, "xml": xml, "queued": False, "at": now_iso()}
    await db.punishments.insert_one(dict(doc))
    await audit(c["id"], "punishment made", "punish", d["summary"])
    return {k: v for k, v in doc.items() if k not in ("career_id", "xml")} | {"placed": LIVE}


@router.get("/{pid}/file")
async def download(pid: str):
    d = await _one(await active_career(), pid)
    return Response(d["xml"], media_type="application/xml", headers={"Content-Disposition": f'attachment; filename="{d["file_name"]}"'})


@router.post("/{pid}/queue")
async def queue_current(pid: str):
    """Current FM27 save only: money, reputation and facilities go into Game changes (backup, preview, confirm, read-back, undo)."""
    import editor_api
    from changes_api import queue_club_edit, auto_apply
    c = await active_career()
    if c["edition"] != "FM27":
        raise HTTPException(409, "Changing a running save is FM27 only. FM26 saves stay read-only; use the new-career file.")
    d = await _one(c, pid)
    fields = {f["key"]: f for f in await editor_api.club_values(c, d["club"]["uid"])}
    queued, skipped = [], []
    for k, v in d["penalties"].items():
        live = PENALTIES[k][3]
        if not live:
            skipped.append(PENALTIES[k][1])
            continue
        for fk in live.split(","):
            f = fields.get(fk)
            if not f:
                skipped.append(PENALTIES[k][1])
                continue
            target = 0 if k == "wipe_bank" else max(f["min"] if f["min"] is not None else 0, f["value"] - v.get("amount", v.get("levels", 0)))
            if fk in ("training", "youth_facilities"):
                target = max(1, target)
            if target != f["value"]:
                await queue_club_edit(c, d["club"], fk, f"{f['label']} (Punish a Club)", target, source="punish", award_id=pid)
                queued.append(f["label"])
    await db.punishments.insert_one({k: v for k, v in d.items() if k != "id"} | {"id": new_id(), "revision": d["revision"] + 1, "queued": True, "at": now_iso()})
    res = await auto_apply(c, "punish", pid) if queued else {}
    return {"queued": queued, "new_career_only": sorted(set(skipped))} | res


@router.delete("/{pid}")
async def remove(pid: str):
    c = await active_career()
    d = await _one(c, pid)
    p = Path(d["file_path"])
    if p.parent == _folder(c) and p.name.startswith("FMCC Punish - "):
        await asyncio.to_thread(p.unlink, True)
    dropped = await db.changes.update_many({"career_id": c["id"], "source": "punish", "award_id": pid, "status": "queued"}, {"$set": {"status": "rejected"}})
    await db.punishments.insert_one({k: v for k, v in d.items() if k != "id"} | {"id": new_id(), "revision": d["revision"] + 1, "status": "removed", "at": now_iso()})
    await audit(c["id"], "punishment removed", "punish", d["summary"] + (f" ({dropped.modified_count} queued change(s) withdrawn)" if dropped.modified_count else ""))
    return {"ok": True, "withdrawn": dropped.modified_count}
