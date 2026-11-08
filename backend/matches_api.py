from typing import Literal

from fastapi import APIRouter, HTTPException

from core import db, active_career

router = APIRouter(prefix="/api")
PER90 = ["goals", "assists", "xg", "xa", "shots", "key_passes", "prog_passes", "duels_won", "pressures", "def_actions"]


async def season_per90(career_id: str, season: str | None = None, team: Literal["us", "them", None] = None) -> dict:
    q = {"career_id": career_id} | ({"season": season} if season else {})
    agg = {}
    async for m in db.matches.find(q, {"_id": 0, "players": 1, "opponent": 1, "date": 1}):
        for p in m["players"]:
            if team and p["team"] != team:
                continue
            a = agg.setdefault(p["unique_id"], {"unique_id": p["unique_id"], "name": p["name"], "team": p["team"], "club": m["opponent"] if p["team"] == "them" else None,
                                                "matches": 0, "minutes": 0, "rating_sum": 0.0, "passes": 0, "passes_completed": 0, **{k: 0 for k in PER90}, "last_seen": m["date"]})
            a["matches"] += 1
            a["minutes"] += p["minutes"]
            a["rating_sum"] += p["rating"]
            a["passes"] += p["passes"]
            a["passes_completed"] += p["passes_completed"]
            a["last_seen"] = max(a["last_seen"], m["date"])
            for k in PER90:
                a[k] += p[k]
    for a in agg.values():
        f = 90 / max(1, a["minutes"])
        a["per90"] = {k: round(a[k] * f, 2) for k in PER90}
        a["avg_rating"] = round(a.pop("rating_sum") / a["matches"], 2)
        a["pass_pct"] = round(a["passes_completed"] / max(1, a["passes"]) * 100)
    return agg


async def matchlens_state() -> dict:
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "matchlens": 1}) or {}
    return s.get("matchlens") or {"installed": False}


@router.get("/matches")
async def list_matches():
    c = await active_career()
    rows = await db.matches.find({"career_id": c["id"]}, {"_id": 0, "id": 1, "date": 1, "opponent": 1, "home": 1, "score": 1, "xg": 1, "season": 1}).sort("date", -1).to_list(200)
    return {"matches": rows, "matchlens": await matchlens_state(), "edition": c["edition"]}


@router.get("/matches/season")
async def season_view():
    c = await active_career()
    latest = await db.matches.find_one({"career_id": c["id"]}, {"_id": 0, "season": 1}, sort=[("date", -1)])
    if not latest:
        return {"season": None, "players": []}
    agg = await season_per90(c["id"], latest["season"], "us")
    trend = {}
    async for m in db.matches.find({"career_id": c["id"], "season": latest["season"]}, {"_id": 0, "date": 1, "players.unique_id": 1, "players.rating": 1, "players.team": 1}).sort("date", 1):
        for p in m["players"]:
            if p["team"] == "us":
                trend.setdefault(p["unique_id"], []).append(p["rating"])
    return {"season": latest["season"], "players": sorted([a | {"trend": trend.get(u, [])[-8:]} for u, a in agg.items()], key=lambda a: -a["avg_rating"])}


@router.get("/matches/{match_id}")
async def get_match(match_id: str):
    c = await active_career()
    m = await db.matches.find_one({"career_id": c["id"], "id": match_id}, {"_id": 0})
    if not m:
        raise HTTPException(404, "Match not found")
    return m

