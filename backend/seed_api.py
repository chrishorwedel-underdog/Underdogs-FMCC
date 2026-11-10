"""Seed a Surname: spread one surname across new or existing low-profile players and staff.
New saves: an FMCC editor data file of new people. Current saves: existing low-profile players are renamed (ability unchanged).
Whether FM accepts the file, and renaming inside a running save, are UNCONFIRMED until tested on a PC."""
import asyncio
import random
import re
from datetime import date
from typing import Literal, Optional
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

import creator_api as cr
import editor_api
from core import db, active_career, latest_two, now_iso, new_id, audit

router = APIRouter(prefix="/api/seed")
CA_CAP, PA_CAP = 60, 100
ID_BASE = 2_150_000_000
POSITIONS = cr.POSITIONS
POS_MATCH = {"GK": {"GK"}, "DC": {"D (C)"}, "DL": {"D (L)", "WB (L)"}, "DR": {"D (R)", "WB (R)"}, "DM": {"DM"}, "MC": {"M (C)"},
             "AML": {"AM (L)", "M (L)"}, "AMR": {"AM (R)", "M (R)"}, "AMC": {"AM (C)"}, "ST": {"ST"}}
STAFF = {
    "Front office": ["Director of Football", "Technical Director", "General Manager", "Chief Executive", "Head of Recruitment", "Loan Manager"],
    "Coaches": ["Assistant Manager", "First-Team Coach", "Goalkeeping Coach", "Fitness Coach", "Set-Piece Coach", "Youth Coach", "Head of Youth Development"],
    "Scouts": ["Chief Scout", "Scout", "Recruitment Analyst"],
    "Medical": ["Head Physio", "Physio", "Head of Sports Science", "Sports Scientist", "Club Doctor"],
    "Analysts": ["Head of Performance Analysis", "Performance Analyst", "Data Analyst"],
}
ROLES = [r for g in STAFF.values() for r in g]
PLAYER_AGES = [("youth", "Youth", 15, 17), ("young", "Young", 18, 21), ("prime", "Prime", 22, 27), ("experienced", "Experienced", 28, 31), ("veteran", "Veteran", 32, 36)]
STAFF_AGES = [("early", "Early career", 25, 34), ("established", "Established", 35, 44), ("senior", "Senior", 45, 54), ("veteran", "Veteran", 55, 64), ("elder", "Elder", 65, 72)]
NAME_RE = r"^[^\W\d_]+(?:[ '\-][^\W\d_]+)*$"


class NationCount(BaseModel):
    nation: str = Field(min_length=2, max_length=40)
    count: int = Field(ge=0, le=300)


class EthShare(BaseModel):
    ethnicity: str
    share: int = Field(default=1, ge=1, le=10)


class SeedIn(BaseModel):
    surname: str = Field(min_length=2, max_length=40)
    mode: Literal["new", "current"] = "new"
    players: dict[str, int] = Field(default_factory=dict)
    staff: dict[str, int] = Field(default_factory=dict)
    nations: list[NationCount] = Field(min_length=1, max_length=20)
    ethnicities: list[EthShare] = Field(default_factory=list, max_length=len(cr.ETHNICITIES))
    player_ages: dict[str, int] = Field(default_factory=lambda: {"young": 1, "prime": 1})
    staff_ages: dict[str, int] = Field(default_factory=lambda: {"established": 1, "senior": 1})
    skin_lo: int = Field(default=1, ge=1, le=20)
    skin_hi: int = Field(default=20, ge=1, le=20)
    height_lo: int = Field(default=170, ge=150, le=210)
    height_hi: int = Field(default=192, ge=150, le=210)
    ca_lo: int = Field(default=30, ge=1, le=CA_CAP)
    ca_hi: int = Field(default=CA_CAP, ge=1, le=CA_CAP)
    pa_lo: int = Field(default=60, ge=1, le=PA_CAP)
    pa_hi: int = Field(default=PA_CAP, ge=1, le=PA_CAP)
    include_own_club: bool = False
    faces: bool = True
    seed: int = Field(default=1, ge=0, le=999_999)

    @model_validator(mode="after")
    def check(self):
        self.surname = " ".join(self.surname.split())
        if not re.match(NAME_RE, self.surname):
            raise ValueError("The surname can only have letters, spaces, hyphens and apostrophes")
        if bad := [k for k in self.players if k not in POSITIONS] + [k for k in self.staff if k not in ROLES]:
            raise ValueError(f"Unknown position or role: {bad[0]}")
        if any(v < 0 or v > 100 for v in [*self.players.values(), *self.staff.values()]):
            raise ValueError("Each position or role can have 0 to 100 people")
        total = self.total
        if not 1 <= total <= 300:
            raise ValueError("Pick between 1 and 300 people in the breakdown")
        if sum(n.count for n in self.nations) != total:
            raise ValueError(f"The nationality counts add up to {sum(n.count for n in self.nations)}, but the breakdown has {total} people")
        if bad := [e.ethnicity for e in self.ethnicities if e.ethnicity not in cr.ETHNICITIES]:
            raise ValueError(f"Unknown ethnicity: {bad[0]}")
        for ages, bands, who in ((self.player_ages, PLAYER_AGES, "player"), (self.staff_ages, STAFF_AGES, "staff")):
            if any(k not in {b[0] for b in bands} or not 0 <= v <= 10 for k, v in ages.items()):
                raise ValueError(f"Unknown {who} age group")
        if sum(self.players.values()) and not sum(self.player_ages.values()):
            raise ValueError("Pick at least one player age group")
        if sum(self.staff.values()) and not sum(self.staff_ages.values()):
            raise ValueError("Pick at least one staff age group")
        for lo, hi, label in ((self.skin_lo, self.skin_hi, "Skin tone"), (self.height_lo, self.height_hi, "Height"),
                              (self.ca_lo, self.ca_hi, "Current ability"), (self.pa_lo, self.pa_hi, "Potential ability")):
            if lo > hi:
                raise ValueError(f"{label}: the lowest value is above the highest")
        return self

    @property
    def total(self) -> int:
        return sum(self.players.values()) + sum(self.staff.values())


def _band(rng, shares: dict, bands: list) -> tuple:
    keys = [b for b in bands if shares.get(b[0])]
    b = rng.choices(keys, [shares[k[0]] for k in keys])[0]
    return b[1], rng.randint(b[2], b[3])


def _first(rng, nation: str, extra: dict) -> str:
    return rng.choice(cr.pools(nation, extra)[1])[0]


def _eth(rng, b: SeedIn, nation: str, extra: dict) -> str:
    if b.ethnicities:
        return rng.choices([e.ethnicity for e in b.ethnicities], [e.share for e in b.ethnicities])[0]
    return cr.DEFAULT_ETH.get(nation) or (extra.get(nation) or {}).get("ethnicity") or "Northern European"


def generate(b: SeedIn, game_date: str, extra: dict) -> list:
    """New people, one per slot in the breakdown; nationality counts are exact."""
    rng = random.Random(b.seed * 104729 + b.total)
    gd = date.fromisoformat(game_date[:10])
    slots = [("player", p) for p, n in b.players.items() for _ in range(n)] + [("staff", r) for r, n in b.staff.items() for _ in range(n)]
    nations = [n.nation for n in b.nations for _ in range(n.count)]
    rng.shuffle(nations)
    out = []
    for i, ((kind, job), nation) in enumerate(zip(slots, nations)):
        band, age = _band(rng, b.player_ages if kind == "player" else b.staff_ages, PLAYER_AGES if kind == "player" else STAFF_AGES)
        eth = _eth(rng, b, nation, extra)
        lo, hi = cr.ETH_SKIN.get(eth, (1, 20)) if (b.skin_lo, b.skin_hi) == (1, 20) else (b.skin_lo, b.skin_hi)
        ca = rng.randint(b.ca_lo, b.ca_hi)
        first = _first(rng, nation, extra)
        out.append({"pid": f"s{i}", "id": None, "kind": kind, "position": job if kind == "player" else None, "role": job if kind == "staff" else None,
                    "first_name": first, "last_name": b.surname, "nationality": nation, "ethnicity": eth, "skin_tone": rng.randint(lo, hi), "age": age, "age_group": band,
                    "dob": date(gd.year - age, rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
                    "height": rng.randint(b.height_lo, b.height_hi) if kind == "player" else None, "ca": ca, "pa": max(ca, rng.randint(b.pa_lo, b.pa_hi)),
                    "foot": rng.choices(["right", "left", "both"], [70, 24, 6])[0] if kind == "player" else None, "club": "Free agent", "face": None})
    return out


def _low_profile(p: dict, own: str, include_own: bool) -> bool:
    """Free agents, youngsters and fringe players: never your club's (unless asked) or anyone established."""
    if not include_own and p.get("club") == own:
        return False
    free = (p.get("club") or "Free agent") in ("Free agent", "", "Unattached")
    return free or (p.get("age") or 99) <= 18 or (p.get("ca") or 999) <= 90 or (p.get("minutes") or 0) < 90


def match_existing(b: SeedIn, pool: list, own: str, taken: set, extra: dict) -> tuple:
    """Pick existing low-profile players for each player slot; their ability, club and age stay as they are."""
    rng = random.Random(b.seed * 15485863 + b.total)
    want_nat = [n.nation for n in b.nations for _ in range(n.count)]
    rng.shuffle(want_nat)
    cands = [p for p in pool if p.get("gender") != "F" and p["unique_id"] not in taken and _low_profile(p, own, b.include_own_club)]
    rng.shuffle(cands)
    used, out, missing = set(), [], 0
    bands = {k: (lo, hi) for k, _, lo, hi in PLAYER_AGES if b.player_ages.get(k)}
    slots = [p for p, n in b.players.items() for _ in range(n)]
    for i, (pos, nat) in enumerate(zip(slots, want_nat)):
        def score(p):
            return (3 * (p.get("nationality") == nat) + 3 * bool(POS_MATCH[pos] & set(p.get("positions") or []))
                    + any(lo <= (p.get("age") or 0) <= hi for lo, hi in bands.values()))
        best = max((p for p in cands if p["unique_id"] not in used), key=score, default=None)
        if not best:
            missing += 1
            continue
        used.add(best["unique_id"])
        first, *rest = best["name"].split(" ", 1)
        out.append({"pid": f"s{i}", "id": best["unique_id"], "kind": "player", "position": (best.get("positions") or [pos])[0], "role": None,
                    "current_name": best["name"], "first_name": _first(rng, best.get("nationality") or nat, extra), "last_name": b.surname,
                    "nationality": best.get("nationality"), "age": best.get("age"), "club": best.get("club") or "Free agent", "league": best.get("league"),
                    "matched_nation": best.get("nationality") == nat, "matched_position": bool(POS_MATCH[pos] & set(best.get("positions") or []))})
    return out, missing


async def _game_date(c: dict) -> str:
    s = await latest_two(c["id"])
    return s[0]["game_date"] if s else date.today().isoformat()


async def _taken(cid: str) -> set:
    return {d["uid"] async for d in db.seed_renames.find({"career_id": cid, "status": "applied"}, {"_id": 0, "uid": 1})}


def _public(d: dict) -> dict:
    return {k: v for k, v in d.items() if k not in ("_id", "career_id", "xml")}


@router.get("/meta")
async def meta():
    c = await active_career()
    snaps = await latest_two(c["id"])
    extra = await cr.layer()
    return {"positions": POSITIONS, "staff": STAFF, "ethnicities": cr.ETHNICITIES, "player_ages": [{"key": k, "label": lab, "lo": lo, "hi": hi} for k, lab, lo, hi in PLAYER_AGES],
            "staff_ages": [{"key": k, "label": lab, "lo": lo, "hi": hi} for k, lab, lo, hi in STAFF_AGES], "caps": {"ca": CA_CAP, "pa": PA_CAP},
            "nations": sorted(set(cr.NAMES) | set(cr.CLOSEST) | set(extra)), "suggested_mode": "current" if len(snaps) and snaps[0].get("save_no", 0) > 0 else "new",
            "desktop": editor_api.LIVE, "club": c["club_name"]}


@router.post("/create")
async def create(body: SeedIn):
    c = await active_career()
    extra = await cr.layer()
    note = None
    if body.mode == "new":
        people = generate(body, await _game_date(c), extra)
    else:
        pool = (await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}) or {}).get("players") or []
        people, missing = match_existing(body, pool, c["club_name"], await _taken(c["id"]), extra)
        staff = sum(body.staff.values())
        notes = [f"{missing} player slot(s) had no low-profile player left to rename"] if missing else []
        if staff:
            notes.append(f"{staff} staff were left out: FMCC can't read staff from a running save yet, so staff can only be seeded into a new save")
        note = ". ".join(notes) or None
        if not people:
            raise HTTPException(409, note or "No low-profile players found to rename")
    draft = {"career_id": c["id"], "settings": body.model_dump(), "mode": body.mode, "surname": body.surname, "people": people, "note": note, "at": now_iso()}
    await db.seed_drafts.replace_one({"career_id": c["id"]}, draft, upsert=True)
    return _public(draft)


@router.get("/draft")
async def draft():
    c = await active_career()
    d = await db.seed_drafts.find_one({"career_id": c["id"]}, {"_id": 0})
    return _public(d) if d and d.get("people") else None


class PersonPatch(BaseModel):
    first_name: Optional[str] = Field(None, min_length=1, max_length=30)
    last_name: Optional[str] = Field(None, min_length=1, max_length=40)
    nationality: Optional[str] = Field(None, min_length=2, max_length=40)
    position: Optional[str] = None
    role: Optional[str] = None
    age: Optional[int] = Field(None, ge=15, le=75)
    height: Optional[int] = Field(None, ge=150, le=210)
    ethnicity: Optional[str] = None
    skin_tone: Optional[int] = Field(None, ge=1, le=20)
    ca: Optional[int] = Field(None, ge=1, le=CA_CAP)
    pa: Optional[int] = Field(None, ge=1, le=PA_CAP)


@router.patch("/draft/{pid}")
async def edit(pid: str, body: PersonPatch):
    c = await active_career()
    d = await db.seed_drafts.find_one({"career_id": c["id"]}, {"_id": 0})
    p = next((x for x in (d or {}).get("people", []) if x["pid"] == pid), None)
    if not p:
        raise HTTPException(404, "That person isn't in the results")
    ch = body.model_dump(exclude_none=True)
    for k in ("first_name", "last_name"):
        if k in ch:
            ch[k] = " ".join(ch[k].split())
            if not re.match(NAME_RE, ch[k]):
                raise HTTPException(422, "Names can only have letters, spaces, hyphens and apostrophes")
    if d["mode"] == "current":
        ch = {k: v for k, v in ch.items() if k in ("first_name", "last_name")}
    if ch.get("position") and (p["kind"] != "player" or ch["position"] not in POSITIONS):
        raise HTTPException(422, "Pick a position from the list")
    if ch.get("role") and (p["kind"] != "staff" or ch["role"] not in ROLES):
        raise HTTPException(422, "Pick a role from the list")
    if ch.get("ethnicity") and ch["ethnicity"] not in cr.ETHNICITIES:
        raise HTTPException(422, "Unknown ethnicity")
    p |= ch
    if d["mode"] == "new":
        p["pa"] = max(p["pa"], p["ca"])
        if "age" in ch:
            gd = date.fromisoformat((await _game_date(c))[:10])
            p["dob"] = date(gd.year - p["age"], *map(int, p["dob"][5:10].split("-"))).isoformat()
    await db.seed_drafts.update_one({"career_id": c["id"]}, {"$set": {"people": d["people"]}})
    return p


@router.delete("/draft/{pid}")
async def drop(pid: str):
    c = await active_career()
    r = await db.seed_drafts.update_one({"career_id": c["id"]}, {"$pull": {"people": {"pid": pid}}})
    if not r.modified_count:
        raise HTTPException(404, "That person isn't in the results")
    return {"ok": True}


def _xml(c: dict, surname: str, people: list) -> str:
    def rec(p):
        keys = ("id", "first_name", "last_name", "nationality", "ethnicity", "skin_tone", "dob", "ca", "pa", "club") + (("position", "foot", "height") if p["kind"] == "player" else ("role",))
        return f"    <record id=\"new_{'person' if p['kind'] == 'player' else 'staff'}\"" + "".join(f" {'unique_id' if k == 'id' else k}={quoteattr(str(p[k]))}" for k in keys) + "/>"
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!-- Made by FMCC Seed a Surname for a NEW career. Whether FM accepts this file is unconfirmed until it is tested on your PC. -->\n'
            f'<record id="fmcc_seed_surname">\n  <string id="edition" value={quoteattr(c["edition"])}/>\n  <string id="surname" value={quoteattr(surname)}/>\n'
            f'  <list id="db_changes">\n' + "\n".join(rec(p) for p in people) + '\n  </list>\n</record>\n')


async def _rename_live(uid: int, first: str, last: str) -> Optional[str]:
    import live_editor
    try:
        await asyncio.to_thread(live_editor.run, "set", "player", uid, "first_name", first)
        await asyncio.to_thread(live_editor.run, "set", "player", uid, "second_name", last)
        return None
    except Exception as exc:
        return str(exc)[:200]


@router.post("/apply")
async def apply():
    c = await active_career()
    d = await db.seed_drafts.find_one({"career_id": c["id"]}, {"_id": 0})
    if not d or not d["people"]:
        raise HTTPException(409, "Press Create first, then Seed The Surname")
    sid = new_id()
    people = d["people"]
    if d["mode"] == "new":
        start = max([p["id"] for b in await db.seed_batches.find({"career_id": c["id"], "status": "active"}, {"_id": 0, "people.id": 1}).to_list(None) for p in b["people"]] + [ID_BASE - 1]) + 1
        for i, p in enumerate(people):
            p["id"] = start + i
        players = [p | {"name": f"{p['first_name']} {p['last_name']}"} for p in people if p["kind"] == "player"]
        faces = await cr._faces(c, players) if d["settings"].get("faces") and players else {"given": 0, "missing": len(players), "why": None if players else "No players"}
        by_id = {p["id"]: p.get("face") for p in players}
        for p in people:
            p["face"] = by_id.get(p["id"])
        fname = f"FMCC Seed - {re.sub(r'[^A-Za-z0-9 ._-]', '', d['surname'])[:30] or 'Surname'} - {sid[:6]}.xml"
        xml = _xml(c, d["surname"], people)
        path = await asyncio.to_thread(cr._write, cr._folder(c), fname, xml)
        result = {"placed": editor_api.LIVE, "file_name": fname, "file_path": path, "faces": faces, "failed": 0}
    else:
        failed = 0
        for p in people:
            err = await _rename_live(p["id"], p["first_name"], p["last_name"]) if editor_api.LIVE else None
            p["error"] = err
            failed += bool(err)
            await db.seed_renames.insert_one({"career_id": c["id"], "seed_id": sid, "uid": p["id"], "old_name": p["current_name"], "new_name": f"{p['first_name']} {p['last_name']}",
                                              "status": "failed" if err else "applied", "error": err, "at": now_iso()})
        xml, result = None, {"placed": editor_api.LIVE, "failed": failed, "sample": not editor_api.LIVE}
    doc = {"id": sid, "career_id": c["id"], "mode": d["mode"], "surname": d["surname"], "people": people, "status": "active", "xml": xml, "at": now_iso()} | result
    await db.seed_batches.insert_one(dict(doc))
    await db.seed_drafts.update_one({"career_id": c["id"]}, {"$set": {"people": [], "applied_as": sid}})
    await audit(c["id"], "surname seeded", "seed", f"{d['surname']}: {len(people)} {'new people' if d['mode'] == 'new' else 'players renamed'}")
    return _public(doc)


@router.get("/history")
async def history():
    c = await active_career()
    rows = await db.seed_batches.find({"career_id": c["id"], "status": "active"}, {"_id": 0, "xml": 0, "career_id": 0}).sort("at", -1).to_list(50)
    return [r | {"count": len(r["people"]), "names": [f"{p['first_name']} {p['last_name']}" for p in r["people"][:5]], "people": None} for r in rows]


@router.get("/history/{sid}/file")
async def file(sid: str):
    c = await active_career()
    d = await db.seed_batches.find_one({"career_id": c["id"], "id": sid, "status": "active"}, {"_id": 0})
    if not d or not d.get("xml"):
        raise HTTPException(404, "No file for this seed")
    return Response(d["xml"], media_type="application/xml", headers={"Content-Disposition": f'attachment; filename="{d["file_name"]}"'})


@router.delete("/history/{sid}")
async def remove(sid: str):
    c = await active_career()
    d = await db.seed_batches.find_one({"career_id": c["id"], "id": sid, "status": "active"}, {"_id": 0})
    if not d:
        raise HTTPException(404, "Seed not found")
    if d["mode"] != "new":
        raise HTTPException(409, "Renames in a running save can't be undone from here; rename them back in FM")
    from pathlib import Path
    p = Path(d["file_path"])
    if p.parent == cr._folder(c) and p.name.startswith("FMCC Seed - "):
        await asyncio.to_thread(p.unlink, True)
    for pl in d["people"]:
        if pl.get("face"):
            await editor_api.add_revision(c, "face", pl["id"], f"{pl['first_name']} {pl['last_name']}", None, "Seeded person removed")
    if any(pl.get("face") for pl in d["people"]):
        await editor_api.rebuild(c)
    await db.seed_batches.update_one({"id": sid}, {"$set": {"status": "removed", "removed_at": now_iso()}})
    await audit(c["id"], "seed removed", "seed", f"{d['surname']}: file deleted")
    return {"ok": True}
