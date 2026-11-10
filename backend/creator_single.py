"""Player Creator: build one player in detail (name, nationality, looks, positions, attributes, personality, ability) for a NEW career.
Saved as an FMCC editor data file, with an NG_Regens face. Whether FM accepts the file is UNCONFIRMED until tested on a PC."""
import asyncio
import re
from datetime import date
from pathlib import Path
from typing import Literal, Optional
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

import creator_api as cr
import editor_api
import sample_reader
from core import db, active_career, now_iso, new_id, audit
from roles import GK_ATTRS

router = APIRouter(prefix="/api/creator/single")
ID_BASE = 2_180_000_000
POSITIONS = ["GK", "D (L)", "D (C)", "D (R)", "WB (L)", "WB (R)", "DM", "M (L)", "M (C)", "M (R)", "AM (L)", "AM (C)", "AM (R)", "ST"]
LEVELS = [(20, "Natural"), (15, "Accomplished"), (10, "Competent"), (5, "Unconvincing")]
GROUPS = {
    "Technical": ["crossing", "dribbling", "finishing", "first_touch", "heading", "marking", "passing", "tackling", "technique"],
    "Mental": ["anticipation", "composure", "decisions", "flair", "off_the_ball", "positioning", "vision", "work_rate"],
    "Physical": ["acceleration", "jumping_reach", "pace", "stamina", "strength"],
    "Goalkeeping": GK_ATTRS,
}
ATTRS = [a for g in GROUPS.values() for a in g]
PERSONALITY = ["adaptability", "ambition", "controversy", "loyalty", "pressure", "professionalism", "sportsmanship", "temperament", "determination", "leadership"]
NAME_RE = r"^[^\W\d_]+(?:[ '\-.][^\W\d_]+)*$"


class SingleIn(BaseModel):
    first_name: str = Field(min_length=1, max_length=30)
    last_name: str = Field(min_length=1, max_length=40)
    common_name: str = Field(default="", max_length=40)
    nationality: str = Field(min_length=2, max_length=40)
    second_nationality: str = Field(default="", max_length=40)
    dob: date
    ethnicity: str
    skin_tone: int = Field(ge=1, le=20)
    height: int = Field(ge=150, le=210)
    weight: int = Field(ge=50, le=110)
    left_foot: int = Field(ge=1, le=20)
    right_foot: int = Field(ge=1, le=20)
    positions: dict[str, int] = Field(min_length=1)
    ca: int = Field(ge=1, le=200)
    pa: int = Field(ge=1, le=200)
    attributes: dict[str, int]
    personality: dict[str, int]
    club: str = Field(default="Free agent", max_length=60)
    faces: bool = True

    @model_validator(mode="after")
    def check(self):
        for k in ("first_name", "last_name"):
            v = " ".join(getattr(self, k).split())
            if not re.match(NAME_RE, v):
                raise ValueError("Names can only have letters, spaces, hyphens, dots and apostrophes")
            setattr(self, k, v)
        if self.ethnicity not in cr.ETHNICITIES:
            raise ValueError("Unknown ethnicity")
        if bad := [p for p in self.positions if p not in POSITIONS]:
            raise ValueError(f"Unknown position: {bad[0]}")
        if not any(v == 20 for v in self.positions.values()):
            raise ValueError("Give the player at least one Natural position")
        if any(v not in {lv for lv, _ in LEVELS} for v in self.positions.values()):
            raise ValueError("Position levels are Natural, Accomplished, Competent or Unconvincing")
        if set(self.attributes) != set(ATTRS) or any(not 1 <= v <= 20 for v in self.attributes.values()):
            raise ValueError("Every attribute needs a value from 1 to 20")
        if set(self.personality) != set(PERSONALITY) or any(not 1 <= v <= 20 for v in self.personality.values()):
            raise ValueError("Every personality trait needs a value from 1 to 20")
        if self.pa < self.ca:
            raise ValueError("Potential ability can't be below current ability")
        return self


def _main_pos(positions: dict) -> str:
    p = max(positions, key=lambda k: (positions[k], -POSITIONS.index(k)))
    return {"M (L)": "AM (L)", "M (R)": "AM (R)"}.get(p, p)


@router.get("/meta")
async def meta():
    return {"positions": POSITIONS, "levels": [{"value": v, "label": lab} for v, lab in LEVELS], "groups": GROUPS, "personality": PERSONALITY,
            "ethnicities": cr.ETHNICITIES, "nations": sorted(set(cr.NAMES) | set(cr.CLOSEST) | set(await cr.layer())), "desktop": editor_api.LIVE}


class AutoIn(BaseModel):
    positions: dict[str, int] = Field(min_length=1)
    ca: int = Field(ge=1, le=200)
    variation: int = Field(default=1, ge=0, le=999_999)


@router.post("/auto-attributes")
async def auto_attributes(body: AutoIn):
    if bad := [p for p in body.positions if p not in POSITIONS]:
        raise HTTPException(422, f"Unknown position: {bad[0]}")
    raw = sample_reader.attributes(body.variation + 1, [_main_pos(body.positions)], body.ca)
    return {a: raw.get(a, 10) for a in ATTRS}


def _xml(c: dict, p: dict) -> str:
    base = " ".join(f"{'unique_id' if k == 'id' else k}={quoteattr(str(p[k]))}" for k in ("id", "first_name", "last_name", "common_name", "nationality", "second_nationality", "dob", "ethnicity",
                                                               "skin_tone", "height", "weight", "left_foot", "right_foot", "ca", "pa", "club"))
    pos = "".join(f'\n      <position id={quoteattr(k)} value="{v}"/>' for k, v in p["positions"].items())
    attrs = "".join(f'\n      <attribute id={quoteattr(k)} value="{v}"/>' for k, v in {**p["attributes"], **p["personality"]}.items())
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!-- Made by FMCC Player Creator for a NEW career. Whether FM accepts this file is unconfirmed until it is tested on your PC. -->\n'
            f'<record id="fmcc_new_player">\n  <string id="edition" value={quoteattr(c["edition"])}/>\n  <list id="db_changes">\n    <record id="new_person" {base}>{pos}{attrs}\n    </record>\n  </list>\n</record>\n')


async def _save(c: dict, body: SingleIn, old: Optional[dict]) -> dict:
    pid = old["player"]["id"] if old else max([d["player"]["id"] async for d in db.creator_singles.find({"career_id": c["id"], "player.id": {"$type": "number"}}, {"_id": 0, "player.id": 1})] + [ID_BASE - 1]) + 1
    p = body.model_dump(mode="json") | {"id": pid, "name": body.common_name.strip() or f"{body.first_name} {body.last_name}", "face": (old or {}).get("player", {}).get("face")}
    if body.faces and not p["face"]:
        await cr._faces(c, [p])
    fname = f"FMCC Player - {re.sub(r'[^A-Za-z0-9 ._-]', '', p['name'])[:40] or 'Player'} - {pid}.xml"
    if old and old.get("file_name") != fname:
        f = Path(old["file_path"])
        if f.parent == cr._folder(c) and f.name.startswith("FMCC Player - "):
            await asyncio.to_thread(f.unlink, True)
    xml = _xml(c, p)
    path = await asyncio.to_thread(cr._write, cr._folder(c), fname, xml)
    return {"player": p, "file_name": fname, "file_path": path, "xml": xml, "at": now_iso()}


def _public(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in ("_id", "career_id", "xml")} | {"placed": editor_api.LIVE}


@router.post("")
async def create(body: SingleIn):
    c = await active_career()
    doc = {"id": new_id(), "career_id": c["id"], "status": "active"} | await _save(c, body, None)
    await db.creator_singles.insert_one(dict(doc))
    await audit(c["id"], "player created", "creator", f"{doc['player']['name']} ({doc['file_name']})")
    return _public(doc)


async def _one(cid: str, sid: str) -> dict:
    d = await db.creator_singles.find_one({"career_id": cid, "id": sid, "status": "active"}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Player not found")
    return d


@router.put("/{sid}")
async def update(sid: str, body: SingleIn):
    c = await active_career()
    old = await _one(c["id"], sid)
    upd = await _save(c, body, old)
    await db.creator_singles.update_one({"id": sid}, {"$set": upd})
    await audit(c["id"], "player edited", "creator", upd["player"]["name"])
    return _public(old | upd)


@router.get("")
async def list_players():
    c = await active_career()
    return [_public(d) for d in await db.creator_singles.find({"career_id": c["id"], "status": "active"}, {"_id": 0, "xml": 0}).sort("at", -1).to_list(200)]


@router.get("/{sid}/file")
async def download(sid: str):
    d = await _one((await active_career())["id"], sid)
    return Response(d["xml"], media_type="application/xml", headers={"Content-Disposition": f'attachment; filename="{d["file_name"]}"'})


@router.delete("/{sid}")
async def remove(sid: str):
    c = await active_career()
    d = await _one(c["id"], sid)
    f = Path(d["file_path"])
    if f.parent == cr._folder(c) and f.name.startswith("FMCC Player - "):
        await asyncio.to_thread(f.unlink, True)
    if d["player"].get("face"):
        await editor_api.add_revision(c, "face", d["player"]["id"], d["player"]["name"], None, "Created player removed")
        await editor_api.rebuild(c)
    await db.creator_singles.update_one({"id": sid}, {"$set": {"status": "removed", "removed_at": now_iso()}})
    await audit(c["id"], "player removed", "creator", f"{d['player']['name']}: file deleted")
    return {"ok": True}
