"""Player Creator for NEW careers: makes a batch of free-agent players (nationality, ethnicity, skin tone, ages, positions,
ability) as an FMCC editor data file, with matching NG_Regens faces. Existing players are never changed. Whether FM accepts
the file is UNCONFIRMED until tested on a PC (Test checklist)."""
import asyncio
import json
import random
import re
from datetime import date
from pathlib import Path
from typing import Literal, Optional
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field, model_validator

import editor_api
from core import db, active_career, latest_two, now_iso, new_id, audit

router = APIRouter(prefix="/api/creator")
ETHNICITIES = ["Northern European", "Mediterranean / Hispanic", "North African / Middle Eastern", "African / Caribbean", "Asian", "South East Asian",
               "Pacific Islander", "Native American", "Native Australian", "Mixed race", "East Asian"]
POSITIONS = ["GK", "DC", "DL", "DR", "DM", "MC", "AML", "AMR", "AMC", "ST"]
# Name lists (more in data/names.json); nations without a list use the closest one and say so.
NAMES = {
    "England": (["Harry", "Jack", "Oliver", "George", "Charlie", "Alfie", "Callum", "Jamie", "Lewis", "Ryan"], ["Smith", "Taylor", "Brown", "Walker", "Wright", "Hughes", "Turner", "Clarke", "Hall", "Ward"]),
    "Spain": (["Pablo", "Sergio", "Álvaro", "Hugo", "Javier", "Diego", "Marcos", "Iker", "Adrián", "Raúl"], ["García", "Martínez", "López", "Sánchez", "Romero", "Navarro", "Torres", "Ruiz", "Molina", "Ortega"]),
    "Italy": (["Luca", "Marco", "Matteo", "Andrea", "Lorenzo", "Davide", "Federico", "Simone", "Riccardo", "Pietro"], ["Rossi", "Bianchi", "Romano", "Greco", "Conti", "Marino", "Ricci", "Gallo", "Costa", "Fontana"]),
    "France": (["Lucas", "Hugo", "Théo", "Nathan", "Enzo", "Mathis", "Louis", "Maxime", "Bastien", "Yanis"], ["Martin", "Bernard", "Dubois", "Moreau", "Laurent", "Girard", "Lefèvre", "Mercier", "Fournier", "Blanc"]),
    "Germany": (["Lukas", "Finn", "Jonas", "Leon", "Niklas", "Tim", "Felix", "Paul", "Moritz", "Jan"], ["Müller", "Schmidt", "Fischer", "Weber", "Wagner", "Becker", "Hoffmann", "Koch", "Richter", "Wolf"]),
    "Portugal": (["João", "Tiago", "Rúben", "Diogo", "Gonçalo", "Rafael", "André", "Nuno", "Pedro", "Rui"], ["Silva", "Santos", "Ferreira", "Pereira", "Costa", "Oliveira", "Rodrigues", "Martins", "Sousa", "Gomes"]),
    "Brazil": (["Gabriel", "Lucas", "Matheus", "Vinícius", "Rodrigo", "Caio", "Thiago", "Felipe", "Bruno", "Igor"], ["Souza", "Lima", "Alves", "Carvalho", "Ribeiro", "Araújo", "Barbosa", "Rocha", "Nascimento", "Mendes"]),
    "Argentina": (["Santiago", "Mateo", "Facundo", "Nicolás", "Agustín", "Lautaro", "Franco", "Thiago", "Julián", "Valentín"], ["González", "Rodríguez", "Fernández", "Gómez", "Díaz", "Pérez", "Álvarez", "Romero", "Sosa", "Acosta"]),
    "Netherlands": (["Daan", "Sem", "Luuk", "Bram", "Jesse", "Thijs", "Milan", "Ruben", "Stijn", "Joep"], ["de Jong", "Jansen", "de Vries", "van Dijk", "Bakker", "Visser", "Smit", "Meijer", "Mulder", "Bos"]),
    "Nigeria": (["Chidi", "Emeka", "Tunde", "Ifeanyi", "Samuel", "Victor", "Kelechi", "Ademola", "Uche", "Femi"], ["Okafor", "Adeyemi", "Nwosu", "Balogun", "Eze", "Okonkwo", "Bello", "Obi", "Adebayo", "Nnamdi"]),
    "Ghana": (["Kwame", "Kofi", "Yaw", "Kwabena", "Kojo", "Emmanuel", "Isaac", "Daniel", "Kwesi", "Ebo"], ["Mensah", "Owusu", "Boateng", "Asante", "Appiah", "Osei", "Agyeman", "Danso", "Amponsah", "Ofori"]),
    "Japan": (["Haruto", "Ren", "Sota", "Yuto", "Kaito", "Riku", "Daiki", "Kenta", "Shota", "Takumi"], ["Sato", "Suzuki", "Takahashi", "Tanaka", "Watanabe", "Ito", "Yamamoto", "Nakamura", "Kobayashi", "Kato"]),
    "South Korea": (["Min-jun", "Seo-jun", "Ji-ho", "Do-yun", "Jun-woo", "Hyun-woo", "Ji-hoon", "Woo-jin", "Sung-min", "Tae-yang"], ["Kim", "Lee", "Park", "Choi", "Jung", "Kang", "Cho", "Yoon", "Jang", "Lim"]),
    "Morocco": (["Youssef", "Hamza", "Ayoub", "Mehdi", "Anas", "Achraf", "Bilal", "Zakaria", "Ilyas", "Soufiane"], ["El Amrani", "Benali", "Haddad", "Ziani", "Bouzid", "Alaoui", "Mansouri", "Idrissi", "Chakir", "Tahiri"]),
    "United States": (["Tyler", "Brandon", "Ethan", "Mason", "Logan", "Caleb", "Austin", "Jordan", "Cole", "Chase"], ["Johnson", "Williams", "Miller", "Davis", "Anderson", "Thomas", "Moore", "Jackson", "White", "Harris"]),
}
DEFAULT_ETH = {"Nigeria": "African / Caribbean", "Ghana": "African / Caribbean", "Japan": "East Asian", "South Korea": "East Asian", "Morocco": "North African / Middle Eastern",
               "Spain": "Mediterranean / Hispanic", "Italy": "Mediterranean / Hispanic", "Portugal": "Mediterranean / Hispanic", "Brazil": "Mixed race", "Argentina": "Mediterranean / Hispanic"}
CLOSEST = {"Scotland": "England", "Wales": "England", "Ireland": "England", "Belgium": "Netherlands", "Austria": "Germany", "Switzerland": "Germany", "Mexico": "Spain",
           "Colombia": "Spain", "Uruguay": "Argentina", "Senegal": "France", "Ivory Coast": "France", "Cameroon": "France", "Algeria": "Morocco", "Tunisia": "Morocco",
           "Egypt": "Morocco", "China": "South Korea", "Australia": "England", "Canada": "United States"}
ID_BASE = 2_100_000_000
# Typical skin tone range per ethnicity, used only when the range is left at the full 1-20.
ETH_SKIN = {"Northern European": (1, 5), "Mediterranean / Hispanic": (3, 9), "North African / Middle Eastern": (5, 11), "African / Caribbean": (13, 20),
            "Asian": (5, 12), "South East Asian": (6, 12), "Pacific Islander": (8, 14), "Native American": (7, 13), "Native Australian": (13, 19),
            "Mixed race": (6, 15), "East Asian": (2, 7)}
NAMES |= {k: tuple(v) for k, v in json.loads((Path(__file__).parent / "data" / "names.json").read_text(encoding="utf-8")).items()}
DEFAULT_ETH |= {"Senegal": "African / Caribbean", "Ivory Coast": "African / Caribbean", "Cameroon": "African / Caribbean", "Algeria": "North African / Middle Eastern",
                "Tunisia": "North African / Middle Eastern", "Egypt": "North African / Middle Eastern", "Saudi Arabia": "North African / Middle Eastern",
                "Turkey": "Mediterranean / Hispanic", "Greece": "Mediterranean / Hispanic", "Mexico": "Mediterranean / Hispanic", "Colombia": "Mixed race",
                "Uruguay": "Mediterranean / Hispanic", "Chile": "Mediterranean / Hispanic", "Ecuador": "Mixed race", "Paraguay": "Mediterranean / Hispanic", "China": "East Asian"}
PRESETS = {
    "academy": ("Academy intake", "A mixed youth intake: 15-17, raw today, high ceilings",
                {"count": 16, "age_lo": 15, "age_hi": 17, "ca_lo": 40, "ca_hi": 85, "pa_lo": 110, "pa_hi": 175, "height_lo": 165, "height_hi": 192}),
    "wonderkids": ("Wonderkids", "A handful of 16-19s who could become world class",
                   {"count": 8, "age_lo": 16, "age_hi": 19, "ca_lo": 90, "ca_hi": 130, "pa_lo": 165, "pa_hi": 195, "height_lo": 170, "height_hi": 192}),
    "hidden_gems": ("Hidden gems abroad", "20-24s from smaller football nations, decent now with room to grow",
                    {"count": 20, "age_lo": 20, "age_hi": 24, "ca_lo": 100, "ca_hi": 135, "pa_lo": 130, "pa_hi": 160, "height_lo": 170, "height_hi": 192,
                     "nations": [{"nation": n, "weight": 1} for n in ("Ecuador", "Paraguay", "Senegal", "Ghana", "Serbia", "Croatia", "Denmark", "South Korea")]}),
    "veterans": ("Veteran free agents", "30-35s who can still do a job on a short deal",
                 {"count": 15, "age_lo": 30, "age_hi": 35, "ca_lo": 115, "ca_hi": 150, "pa_lo": 120, "pa_hi": 155, "height_lo": 172, "height_hi": 192}),
    "keepers": ("Goalkeeper pool", "Keepers of every age to fill your goalkeeping depth",
                {"count": 10, "age_lo": 17, "age_hi": 33, "ca_lo": 70, "ca_hi": 140, "pa_lo": 110, "pa_hi": 165, "height_lo": 185, "height_hi": 200, "positions": ["GK"]}),
}


class NationIn(BaseModel):
    nation: str = Field(min_length=2, max_length=40)
    weight: int = Field(default=1, ge=1, le=10)


class BatchIn(BaseModel):
    name: str = Field(default="", max_length=60)
    count: int = Field(default=20, ge=1, le=200)
    nations: list[NationIn] = Field(min_length=1, max_length=20)
    ethnicities: list[str] = Field(default_factory=list, max_length=len(ETHNICITIES))
    skin_lo: int = Field(default=1, ge=1, le=20)
    skin_hi: int = Field(default=20, ge=1, le=20)
    age_lo: int = Field(default=16, ge=15, le=40)
    age_hi: int = Field(default=21, ge=15, le=40)
    positions: list[str] = Field(default_factory=lambda: list(POSITIONS), min_length=1)
    ca_lo: int = Field(default=60, ge=1, le=200)
    ca_hi: int = Field(default=110, ge=1, le=200)
    pa_lo: int = Field(default=120, ge=1, le=200)
    pa_hi: int = Field(default=170, ge=1, le=200)
    foot: Literal["any", "right", "left", "both"] = "any"
    height_lo: int = Field(default=170, ge=150, le=210)
    height_hi: int = Field(default=192, ge=150, le=210)
    faces: bool = True
    seed: int = Field(default=1, ge=0, le=999_999)

    @model_validator(mode="after")
    def ranges(self):
        for lo, hi, label in ((self.skin_lo, self.skin_hi, "Skin tone"), (self.age_lo, self.age_hi, "Age"), (self.ca_lo, self.ca_hi, "Current ability"),
                              (self.pa_lo, self.pa_hi, "Potential ability"), (self.height_lo, self.height_hi, "Height")):
            if lo > hi:
                raise ValueError(f"{label}: the lowest value is above the highest")
        if bad := [e for e in self.ethnicities if e not in ETHNICITIES]:
            raise ValueError(f"Unknown ethnicity: {bad[0]}")
        if bad := [p for p in self.positions if p not in POSITIONS]:
            raise ValueError(f"Unknown position: {bad[0]}")
        return self


async def layer() -> dict:
    d = await db.name_layers.find_one({"_id": "installed"}, {"_id": 0, "names": 1}) or {}
    return d.get("names") or {}


def pools(nation: str, extra: dict) -> tuple:
    src = nation if nation in NAMES or nation in extra else CLOSEST.get(nation, "England")
    out = []
    for i, part in enumerate(("first", "last")):
        base = list(NAMES[src][i]) if src in NAMES else []
        have = set(base)
        out.append([(n, "built-in") for n in base] + [(n, "update") for n in (extra.get(src) or {}).get(part, []) if n not in have])
    return src, out[0], out[1]


def counts(extra: dict) -> dict:
    res = {}
    for n in sorted(set(NAMES) | set(extra)):
        _, first, last = pools(n, extra)
        res[n] = {"builtin": sum(s == "built-in" for _, s in first + last), "update": sum(s == "update" for _, s in first + last)}
    return res


def generate(b: BatchIn, game_date: str, start_id: int, extra: Optional[dict] = None) -> list:
    extra = extra or {}
    rng = random.Random(b.seed * 7919 + b.count)
    gd = date.fromisoformat(game_date[:10])
    pool = [n.nation for n in b.nations for _ in range(n.weight)]
    out, seen = [], set()
    for i in range(b.count):
        nation = rng.choice(pool)
        src, first, last = pools(nation, extra)
        for _ in range(20):
            fn, ln = rng.choice(first), rng.choice(last)
            name = (fn[0], ln[0])
            if name not in seen:
                break
        seen.add(name)
        age = rng.randint(b.age_lo, b.age_hi)
        ca = rng.randint(b.ca_lo, b.ca_hi)
        pa = max(ca, rng.randint(b.pa_lo, b.pa_hi))
        foot = b.foot if b.foot != "any" else rng.choices(["right", "left", "both"], [70, 24, 6])[0]
        eth = rng.choice(b.ethnicities) if b.ethnicities else DEFAULT_ETH.get(nation) or (extra.get(nation) or {}).get("ethnicity") or "Northern European"
        lo, hi = ETH_SKIN.get(eth, (1, 20)) if (b.skin_lo, b.skin_hi) == (1, 20) else (b.skin_lo, b.skin_hi)
        out.append({"id": start_id + i, "first_name": name[0], "last_name": name[1], "name": f"{name[0]} {name[1]}", "nationality": nation,
                    "names_from": src if src != nation else None, "name_source": "update" if "update" in (fn[1], ln[1]) else "built-in", "ethnicity": eth,
                    "skin_tone": rng.randint(lo, hi), "age": age, "dob": date(gd.year - age, rng.randint(1, 12), rng.randint(1, 28)).isoformat(),
                    "position": rng.choice(b.positions), "ca": ca, "pa": pa, "foot": foot, "height": rng.randint(b.height_lo, b.height_hi), "club": "Free agent", "face": None})
    return out


def _folder(c: dict) -> Path:
    return Path(c["save_folder"]).parent / "editor data" if editor_api.LIVE else editor_api.ROOT / "preview_fm" / "editor data"


def _xml(c: dict, name: str, players: list) -> str:
    rows = "\n".join("    <record id=\"new_person\"" + "".join(f" {k}={quoteattr(str(p[k]))}" for k in ("id", "first_name", "last_name", "nationality", "ethnicity",
                     "skin_tone", "dob", "position", "ca", "pa", "foot", "height", "club")) + "/>" for p in players)
    return ('<?xml version="1.0" encoding="UTF-8"?>\n<!-- Made by FMCC Player Creator for a NEW career. Whether FM accepts this file is unconfirmed until it is tested on your PC. -->\n'
            f'<record id="fmcc_new_players">\n  <string id="edition" value={quoteattr(c["edition"])}/>\n  <string id="batch" value={quoteattr(name)}/>\n'
            f'  <list id="db_changes">\n{rows}\n  </list>\n</record>\n')


def _write(folder: Path, fname: str, text: str) -> str:
    folder.mkdir(parents=True, exist_ok=True)
    (folder / fname).write_text(text, encoding="utf-8")
    return str(folder / fname)


async def _latest(cid: str) -> list:
    pipe = [{"$match": {"career_id": cid}}, {"$sort": {"revision": -1}}, {"$group": {"_id": "$bid", "doc": {"$first": "$$ROOT"}}}, {"$match": {"doc.status": "active"}}]
    return [d["doc"] async for d in db.creator_batches.aggregate(pipe)]


async def _game_date(c: dict) -> str:
    s = await latest_two(c["id"])
    return s[0]["game_date"] if s else date.today().isoformat()


async def _next_id(cid: str) -> int:
    rows = await _latest(cid)
    return max([p["id"] for d in rows for p in d["players"]] + [ID_BASE - 1]) + 1


@router.get("/meta")
async def meta():
    c = await active_career()
    ng = await editor_api.ng_index(c)
    extra = await layer()
    return {"presets": [{"key": k, "name": n, "about": a, "settings": s} for k, (n, a, s) in PRESETS.items()], "edition": c["edition"], "ethnicities": ETHNICITIES, "positions": POSITIONS,
            "name_lists": sorted(set(NAMES) | set(extra)), "closest": {k: v for k, v in CLOSEST.items() if k not in extra}, "name_counts": counts(extra),
            "nations": sorted(set(NAMES) | set(CLOSEST) | set(extra) | set(ng.get("folders") or {})), "ng_installed": ng["installed"],
            "ng_folders": sorted(ng.get("folders") or {}), "desktop": editor_api.LIVE}


@router.post("/preview")
async def preview(body: BatchIn):
    c = await active_career()
    players = generate(body, await _game_date(c), await _next_id(c["id"]), await layer())
    by = lambda k: {v: sum(p[k] == v for p in players) for v in sorted({p[k] for p in players})}  # noqa: E731
    return {"players": players[:60], "count": len(players), "by_nation": by("nationality"), "by_position": by("position"),
            "borrowed_names": sorted({p["nationality"] for p in players if p["names_from"]})}


async def _faces(c: dict, players: list) -> dict:
    ng = await editor_api.ng_index(c)
    if not ng["installed"]:
        return {"given": 0, "missing": len(players), "why": "NG_Regens isn't installed"}
    mapping = (await db.settings.find_one({"_id": "app"}, {"_id": 0, "nation_folders": 1}) or {}).get("nation_folders") or {}
    mine = await editor_api.latest(c["id"], "face")
    used = {f["file"] for f in ng["faces"].values()} | {r["value"].get("ng_file") for r in mine.values() if r.get("value")}
    given = 0
    for p in players:
        folder = await editor_api._ng_face(c, {"unique_id": p["id"], "name": p["name"], "nationality": p["nationality"]}, ng, used, mapping)
        if folder:
            p["face"] = folder
            given += 1
    if given:
        await editor_api.rebuild(c)
    return {"given": given, "missing": len(players) - given, "why": None if given == len(players) else "No NG_Regens folder matches some nationalities (set them in Player & Teams Editor)"}


@router.post("/batches")
async def create(body: BatchIn):
    c = await active_career()
    players = generate(body, await _game_date(c), await _next_id(c["id"]), await layer())
    faces = await _faces(c, players) if body.faces else {"given": 0, "missing": len(players), "why": "Faces switched off"}
    bid = new_id()
    name = body.name.strip() or f"{len(players)} new players"
    fname = f"FMCC Players - {re.sub(r'[^A-Za-z0-9 ._-]', '', name)[:40]} - {bid[:6]}.xml"
    xml = _xml(c, name, players)
    path = await asyncio.to_thread(_write, _folder(c), fname, xml)
    doc = {"id": new_id(), "bid": bid, "career_id": c["id"], "revision": 1, "status": "active", "name": name, "settings": body.model_dump(), "players": players,
           "faces": faces, "file_name": fname, "file_path": path, "xml": xml, "at": now_iso()}
    await db.creator_batches.insert_one(dict(doc))
    await audit(c["id"], "players created", "creator", f"{name}: {len(players)} free agents, {faces['given']} faces")
    return {k: v for k, v in doc.items() if k not in ("_id", "career_id", "xml")} | {"placed": editor_api.LIVE}


@router.get("/batches")
async def batches():
    c = await active_career()
    return sorted(({k: v for k, v in d.items() if k not in ("_id", "career_id", "xml", "players")} | {"count": len(d["players"]), "sample": d["players"][:6]}
                   for d in await _latest(c["id"])), key=lambda d: d["at"], reverse=True)


async def _one(cid: str, bid: str) -> dict:
    d = await db.creator_batches.find_one({"career_id": cid, "bid": bid}, {"_id": 0}, sort=[("revision", -1)])
    if not d or d["status"] != "active":
        raise HTTPException(404, "Batch not found")
    return d


@router.get("/batches/{bid}/file")
async def download(bid: str):
    d = await _one((await active_career())["id"], bid)
    return Response(d["xml"], media_type="application/xml", headers={"Content-Disposition": f'attachment; filename="{d["file_name"]}"'})


@router.delete("/batches/{bid}")
async def remove(bid: str):
    c = await active_career()
    d = await _one(c["id"], bid)
    p = Path(d["file_path"])
    if p.parent == _folder(c) and p.name.startswith("FMCC Players - "):
        await asyncio.to_thread(p.unlink, True)
    for pl in d["players"]:
        if pl.get("face"):
            await editor_api.add_revision(c, "face", pl["id"], pl["name"], None, "Created player removed")
    if any(pl.get("face") for pl in d["players"]):
        await editor_api.rebuild(c)
    await db.creator_batches.insert_one({k: v for k, v in d.items() if k != "id"} | {"id": new_id(), "revision": d["revision"] + 1, "status": "removed", "at": now_iso()})
    await audit(c["id"], "players removed", "creator", f"{d['name']}: file deleted, faces released")
    return {"ok": True}
