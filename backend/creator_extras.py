"""Player Creator: saved presets (per FMCC install) and layered name-list updates."""
import json
import logging
import os
import re
from pathlib import Path
from typing import Optional

import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import editor_api
from creator_api import NAMES, CLOSEST, ETHNICITIES, BatchIn, layer, counts
from core import db, active_career, now_iso, new_id, audit

router = APIRouter(prefix="/api/creator")
logger = logging.getLogger(__name__)
SAMPLE = Path(__file__).parent / "data" / "names_update_sample.json"
NAME_RE = re.compile(r"^[^\W\d_][^\W\d_' .-]*(?:[' .-][^\W\d_]+)*$")


async def _audit(action: str, detail: str):
    try:
        c = await active_career()
    except HTTPException:
        return
    await audit(c["id"], action, "creator", detail)


# ---------- presets ----------
class PresetIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    settings: BatchIn


class PresetPatch(BaseModel):
    name: Optional[str] = Field(default=None, min_length=1, max_length=40)
    settings: Optional[BatchIn] = None


def _store(s: BatchIn) -> dict:
    return s.model_dump(exclude={"seed"})


async def _taken(name: str, pid: str = ""):
    if await db.creator_presets.find_one({"name_key": name.strip().lower(), "pid": {"$ne": pid}, "deleted": {"$ne": True}}):
        raise HTTPException(409, f"You already have a preset called \"{name.strip()}\"")


async def _known() -> set:
    known = set(NAMES) | set(CLOSEST) | set(await layer())
    try:
        known |= set((await editor_api.ng_index(await active_career())).get("folders") or {})
    except HTTPException:
        pass
    return known


@router.get("/presets")
async def list_presets():
    known = await _known()
    out = []
    async for d in db.creator_presets.find({"deleted": {"$ne": True}}, {"_id": 0}).sort("name_key", 1):
        s = d["settings"]
        dropped = [n["nation"] for n in s["nations"] if n["nation"] not in known]
        nations = [n for n in s["nations"] if n["nation"] in known] or [{"nation": "England", "weight": 1}]
        note = f"FMCC no longer knows {', '.join(dropped)}, so it was left out" + ("; England used instead" if len(dropped) == len(s["nations"]) else "") if dropped else None
        out.append({"pid": d["pid"], "name": d["name"], "settings": s | {"nations": nations}, "dropped": dropped, "note": note, "updated_at": d["updated_at"]})
    return out


@router.post("/presets")
async def save_preset(body: PresetIn):
    await _taken(body.name)
    doc = {"pid": new_id(), "name": body.name.strip(), "name_key": body.name.strip().lower(), "settings": _store(body.settings), "created_at": now_iso(), "updated_at": now_iso()}
    await db.creator_presets.insert_one(dict(doc))
    await _audit("preset saved", doc["name"])
    return {k: v for k, v in doc.items() if k not in ("_id", "name_key")}


@router.patch("/presets/{pid}")
async def update_preset(pid: str, body: PresetPatch):
    d = await db.creator_presets.find_one({"pid": pid, "deleted": {"$ne": True}}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Preset not found")
    upd = {"updated_at": now_iso()}
    if body.name:
        await _taken(body.name, pid)
        upd |= {"name": body.name.strip(), "name_key": body.name.strip().lower()}
    if body.settings:
        upd["settings"] = _store(body.settings)
    await db.creator_presets.update_one({"pid": pid}, {"$set": upd})
    await _audit("preset changed", f"{d['name']}" + (f" renamed to {upd['name']}" if body.name else "") + (" · settings overwritten" if body.settings else ""))
    return {"pid": pid, "name": upd.get("name", d["name"])}


@router.delete("/presets/{pid}")
async def delete_preset(pid: str):
    d = await db.creator_presets.find_one_and_update({"pid": pid, "deleted": {"$ne": True}}, {"$set": {"deleted": True, "deleted_at": now_iso()}})
    if not d:
        raise HTTPException(404, "Preset not found")
    await _audit("preset deleted", d["name"])
    return {"ok": True}


# ---------- name-list updates ----------
def _clean(raw) -> dict:
    if not isinstance(raw, dict) or not isinstance(raw.get("names"), dict) or not isinstance(raw.get("version"), str):
        raise ValueError("The name update file isn't in FMCC's format")
    names = {}
    for nation, v in list(raw["names"].items())[:300]:
        if not isinstance(nation, str) or not 2 <= len(nation) <= 40 or not isinstance(v, dict):
            continue
        entry = {}
        for part in ("first", "last"):
            seen = []
            for n in (v.get(part) or [])[:1000]:
                n = n.strip() if isinstance(n, str) else ""
                if 1 < len(n) <= 30 and NAME_RE.match(n) and n not in seen:
                    seen.append(n)
            entry[part] = seen
        if entry["first"] and entry["last"]:
            if v.get("ethnicity") in ETHNICITIES:
                entry["ethnicity"] = v["ethnicity"]
            names[nation.strip()] = entry
    return {"version": raw["version"][:40], "sample": bool(raw.get("sample")), "names": names}


async def _published() -> dict:
    repo = (os.environ.get("FMCC_RELEASE_REPO") or "").strip().removeprefix("https://").removeprefix("github.com/").strip("/")
    if not repo:
        if editor_api.LIVE:
            return {"set_up": False, "message": "The name update channel isn't set up yet, so only FMCC's built-in names are used"}
        return {"set_up": True, "data": _clean(json.loads(SAMPLE.read_text(encoding="utf-8")) | {"sample": True})}
    try:
        async with httpx.AsyncClient(timeout=10, follow_redirects=True) as client:
            r = await client.get(f"https://github.com/{repo}/releases/latest/download/fmcc-names.json")
    except httpx.HTTPError as exc:
        logger.warning("Name update check failed: %s", type(exc).__name__)
        return {"set_up": True, "message": "Couldn't reach the update channel. Try again later"}
    if r.status_code == 404:
        return {"set_up": True, "message": "No name update has been published yet"}
    try:
        return {"set_up": True, "data": _clean(r.json())}
    except ValueError as exc:
        return {"set_up": True, "message": str(exc)}


def _diff(current: dict, new: dict) -> dict:
    added, countries = {}, []
    for nation, v in new.items():
        have = current.get(nation) or {}
        base = NAMES.get(nation, ((), ()))
        f = [n for n in v["first"] if n not in base[0] and n not in have.get("first", [])]
        lst = [n for n in v["last"] if n not in base[1] and n not in have.get("last", [])]
        if nation not in NAMES and nation not in current:
            countries.append(nation)
        if f or lst:
            added[nation] = {"first": len(f), "last": len(lst), "examples": [f"{a} {b}" for a, b in zip(f[:3], lst[:3])]}
    return {"countries_added": sorted(countries), "names_added": added, "total_added": sum(x["first"] + x["last"] for x in added.values())}


async def _installed() -> dict:
    return await db.name_layers.find_one({"_id": "installed"}, {"_id": 0}) or {}


@router.get("/names")
async def names_state():
    d = await _installed()
    extra = d.get("names") or {}
    rows = [{"nation": k, **v} for k, v in counts(extra).items()]
    prev = d.get("previous")
    return {"installed": {k: d.get(k) for k in ("version", "sample", "installed_at")} if d.get("version") else None,
            "can_rollback": bool(d.get("version")), "rollback_to": (prev or {}).get("version") or "built-in names only",
            "countries": rows, "total": {"builtin": sum(r["builtin"] for r in rows), "update": sum(r["update"] for r in rows)}}


@router.get("/names/check")
async def names_check():
    pub = await _published()
    if "data" not in pub:
        return {"set_up": pub["set_up"], "message": pub["message"], "available": False}
    d, data = await _installed(), pub["data"]
    diff = _diff(d.get("names") or {}, data["names"])
    return {"set_up": True, "message": None, "version": data["version"], "sample": data["sample"], "installed": d.get("version"),
            "available": data["version"] != d.get("version") and bool(diff["total_added"]), **diff}


class InstallIn(BaseModel):
    version: str = Field(min_length=1, max_length=40)


@router.post("/names/install")
async def names_install(body: InstallIn):
    pub = await _published()
    if "data" not in pub:
        raise HTTPException(409, pub["message"])
    data = pub["data"]
    if data["version"] != body.version:
        raise HTTPException(409, "The published list changed since you checked. Check again")
    d = await _installed()
    if d.get("version") == data["version"]:
        raise HTTPException(409, "This name list is already installed")
    current = d.get("names") or {}
    merged = {n: dict(v) for n, v in current.items()}
    for n, v in data["names"].items():
        old = merged.get(n) or {"first": [], "last": []}
        merged[n] = {"first": old["first"] + [x for x in v["first"] if x not in old["first"]], "last": old["last"] + [x for x in v["last"] if x not in old["last"]]}
        if v.get("ethnicity") or old.get("ethnicity"):
            merged[n]["ethnicity"] = v.get("ethnicity") or old.get("ethnicity")
    prev = {k: d.get(k) for k in ("version", "sample", "names", "installed_at")} if d.get("version") else None
    await db.name_layers.replace_one({"_id": "installed"}, {"version": data["version"], "sample": data["sample"], "names": merged, "installed_at": now_iso(), "previous": prev}, upsert=True)
    diff = _diff(current, data["names"])
    await _audit("name list installed", f"{data['version']}{' (sample)' if data['sample'] else ''}: {diff['total_added']} names, {len(diff['countries_added'])} new countries")
    return {"version": data["version"], **diff}


@router.post("/names/rollback")
async def names_rollback():
    d = await _installed()
    if not d.get("version"):
        raise HTTPException(409, "Only the built-in names are in use, so there's nothing to roll back")
    prev = d.get("previous")
    await db.name_layers.replace_one({"_id": "installed"}, (prev or {"version": None, "sample": False, "names": {}, "installed_at": None}) | {"previous": None, "rolled_back_from": d["version"]})
    await _audit("name list rolled back", f"{d['version']} → {(prev or {}).get('version') or 'built-in names only'}")
    return {"now": (prev or {}).get("version") or "built-in names only"}
