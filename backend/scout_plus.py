"""Scout Players extras: Moneyball lists, Find Similar Players (by player or by target numbers) and the Youth Intake Tracker."""
import calendar
import math
from datetime import date

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field, field_validator

import stats_model as sm
from core import db, active_career, latest_two
from scout_api import _data

router = APIRouter(prefix="/api")
TOP5 = ["Premier League", "LaLiga", "La Liga", "Bundesliga", "Serie A", "Ligue 1"]
# Typical FM youth intake dates by league. Estimates: check the nation's info screen in your game and set your own date.
INTAKE = {"Premier League": "03-15", "Championship": "03-15", "LaLiga": "03-15", "La Liga": "03-15", "Bundesliga": "03-20", "Serie A": "03-25",
          "Ligue 1": "03-10", "Eredivisie": "03-20", "Liga Portugal": "03-25", "Scottish Premiership": "03-10", "MLS": "02-15", "Brasileirão": "11-15"}


def _p(x: dict) -> dict:
    return {k: x.get(k) for k in ("unique_id", "name", "age", "club", "league", "positions", "group", "value", "wage", "minutes", "grade_global", "fair_price", "own")}


@router.get("/scout/moneyball")
async def moneyball():
    _, data = await _data()
    pool = [x for x in data["players"] if not x.get("own") and x.get("gender", "M") == "M" and x.get("source") == "save" and x.get("value") and x.get("grade_global") is not None and (x.get("minutes") or 0) >= sm.MIN_PRICE]
    bargains = sorted([x for x in pool if x.get("fair_price") and x["fair_price"] >= 1.3 * x["value"] and x["grade_global"] >= 45], key=lambda x: -x["fair_price"] / x["value"])[:15]
    vfm = sorted(pool, key=lambda x: -x["grade_global"] / math.log10(max(x["value"], 100_000)))[:15]
    med = {}
    for x in pool:
        med.setdefault(x["cohort"], []).append(x["value"])
    med = {k: sorted(v)[len(v) // 2] for k, v in med.items()}
    under = sorted([x for x in pool if x["value"] <= med[x["cohort"]] and x["grade_global"] >= 50], key=lambda x: -x["grade_global"])[:15]
    return {"bargains": [_p(x) | {"why": f"Fair price {round(x['fair_price'] / x['value'], 1)}× his value"} for x in bargains],
            "vfm": [_p(x) | {"why": f"Grade {x['grade_global']} for the money"} for x in vfm],
            "undervalued": [_p(x) | {"why": f"Grade {x['grade_global']} per-90 output, valued below a typical {x['cohort'].lower()}"} for x in under],
            "sample": not sm.LIVE}


class SimilarIn(BaseModel):
    unique_id: int | None = None
    targets: dict[str, float] = Field(default_factory=dict)
    mode: str = Field("p90", pattern="^(p90|total)$")
    group: str | None = None
    max_age: int = Field(45, ge=14, le=50)


@router.post("/scout/similar")
async def similar(body: SimilarIn):
    _, data = await _data()
    if body.unique_id is not None:
        x = next((p for p in data["players"] if p["unique_id"] == body.unique_id), None)
        if not x:
            raise HTTPException(404, "That player isn't in the scouting data")
        own = {p["unique_id"] for p in data["players"] if p.get("own")}
        rows = [r for r in sm.similar(data, x, 40) if r["age"] <= body.max_age and r["unique_id"] not in own][:15]
        return {"base": _p(x), "rows": rows, "how": "Playing style (weighted per-90 profile) and level, same position group"}
    keys = [k for k in body.targets if k in sm.METRICS]
    if not keys:
        raise HTTPException(422, "Pick at least one number to match")
    out = []
    for p in data["players"]:
        if p.get("own") or p.get("gender", "M") != "M" or (body.group and p.get("group") != body.group) or p["age"] > body.max_age or (p.get("minutes") or 0) < sm.MIN_PCT:
            continue
        src = p["p90"] if body.mode == "p90" else {k: (v or 0) * (p.get("minutes") or 0) / 90 for k, v in p["p90"].items() if v is not None}
        have = [k for k in keys if src.get(k) is not None]
        if len(have) < len(keys):
            continue
        sd = {k: sm.METRICS[k][3] * (1 if body.mode == "p90" else max(1, (p.get("minutes") or 0) / 90)) for k in keys}
        d = math.sqrt(sum(((src[k] - body.targets[k]) / (sd[k] or 1)) ** 2 for k in keys) / len(keys))
        out.append(_p(p) | {"similarity": round(100 * math.exp(-.5 * (d / 1.25) ** 2)), "values": {k: round(src[k], 2) for k in keys}})
    return {"rows": sorted(out, key=lambda r: -r["similarity"])[:15], "how": "Closeness to your numbers, scaled by how much each stat usually varies"}


def intake_day(year: int, mmdd: str) -> date:
    m, d = (int(v) for v in mmdd.split("-"))
    return date(year, m, min(d, calendar.monthrange(year, m)[1]))


def _next(gd: date, mmdd: str) -> date:
    t = intake_day(gd.year, mmdd)
    return t if t >= gd else intake_day(gd.year + 1, mmdd)


async def intake_state(c: dict) -> dict:
    snaps = await latest_two(c["id"])
    if not snaps:
        raise HTTPException(404, "No save read yet")
    gd = date.fromisoformat(snaps[0]["game_date"][:10])
    leagues = sorted({t.get("name") for t in (snaps[0].get("tables") or []) if t.get("name")} | {p.get("league") for p in (await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players.league": 1}) or {"players": []})["players"] if p.get("league")})
    prefs = c.get("youth_intake") or {}
    on = set(prefs.get("enabled") if "enabled" in prefs else [x for x in leagues if x in TOP5])
    own = prefs.get("dates") or {}
    rows = []
    for lg in leagues:
        mmdd = own.get(lg) or INTAKE.get(lg, "03-15")
        t = _next(gd, mmdd)
        rows.append({"league": lg, "on": lg in on, "date": t.isoformat(), "days": (t - gd).days, "estimated": lg not in own, "mmdd": mmdd})
    return {"game_date": gd.isoformat(), "rows": sorted(rows, key=lambda r: (not r["on"], r["days"])), "prev_date": snaps[1]["game_date"][:10] if len(snaps) > 1 else None}


@router.get("/youth-intake")
async def youth_intake():
    return await intake_state(await active_career())


class IntakeIn(BaseModel):
    league: str = Field(min_length=1, max_length=80)
    on: bool | None = None
    mmdd: str | None = Field(None, pattern=r"^(0[1-9]|1[0-2])-(0[1-9]|[12]\d|3[01])$")

    @field_validator("mmdd")
    @classmethod
    def real_day(cls, v):
        if v:
            m, d = (int(x) for x in v.split("-"))
            if d > calendar.monthrange(2028, m)[1]:
                raise ValueError("That day doesn't exist in that month")
        return v


@router.put("/youth-intake")
async def set_intake(body: IntakeIn):
    c = await active_career()
    st = await intake_state(c)
    if body.league not in {r["league"] for r in st["rows"]}:
        raise HTTPException(404, "That league isn't in your save")
    prefs = c.get("youth_intake") or {}
    on = set(prefs.get("enabled") if "enabled" in prefs else [r["league"] for r in st["rows"] if r["on"]])
    if body.on is not None:
        on = on | {body.league} if body.on else on - {body.league}
    dates = prefs.get("dates") or {}
    if body.mmdd:
        dates[body.league] = body.mmdd
    await db.careers.update_one({"id": c["id"]}, {"$set": {"youth_intake": {"enabled": sorted(on), "dates": dates}}})
    return {"ok": True}
