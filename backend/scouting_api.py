import math
from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import roles
from core import db, active_career, latest_snapshot, now_iso, new_id
from matches_api import season_per90
from rules_api import current as current_rules

router = APIRouter(prefix="/api/scouting")


async def _pool(c: dict) -> dict:
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0})
    if not pool:
        raise HTTPException(404, "No scouting data yet. Read a save first.")
    return pool


async def shortlisted(career_id: str) -> set:
    pipeline = [{"$match": {"career_id": career_id}}, {"$sort": {"at": -1}}, {"$group": {"_id": "$unique_id", "status": {"$first": "$status"}}},
                {"$match": {"status": "active"}}]
    return {d["_id"] async for d in db.shortlist.aggregate(pipeline)}


def score_players(players: list, params: dict, role: str | None) -> list:
    values = sorted(p["value"] for p in players)
    n = max(1, len(values) - 1)
    w = {k: params[k] for k in ("w_role", "w_potential", "w_age", "w_value")}
    total_w = sum(w.values()) or 1
    out = []
    for p in players:
        fit = roles.role_rating(p, role) if role else roles.best_role(p)["rating"]
        best = roles.best_role(p)
        age_s = max(0, min(100, (32 - p["age"]) / 15 * 100))
        val_s = 100 - values.index(p["value"]) / n * 100
        score = (w["w_role"] * fit + w["w_potential"] * p["pa"] / 2 + w["w_age"] * age_s + w["w_value"] * val_s) / total_w
        perf = ((p["avg_rating"] or 6.0) - 6.0) * 25 + 50
        vfm_raw = (fit * 0.7 + perf * 0.3) / (max(p["value"], 100_000) / 1_000_000) ** 0.35
        diff = (p["avg_rating"] - (6.0 + (p["ca"] - 100) / 100)) if p["avg_rating"] else 0
        flag = "over" if diff >= params["over_threshold"] else "under" if diff <= -params["over_threshold"] else None
        out.append({k: p[k] for k in ("unique_id", "name", "age", "nationality", "club", "league", "positions", "ca", "pa", "value", "wage",
                                      "minutes", "avg_rating", "goals")} |
                   {"fit": fit, "best_role": f"{best['name']} ({best['duty']})", "score": round(score), "vfm_raw": vfm_raw, "flag": flag})
    top = max([x["vfm_raw"] for x in out] or [1])
    for x in out:
        x["vfm"] = round(x.pop("vfm_raw") / top * 100)
    return out


@router.get("/meta")
async def meta():
    c = await active_career()
    pool = await _pool(c)
    return {"roles": [{"key": k, "name": f"{v[0]} ({v[1]})"} for k, v in roles.ROLES.items()],
            "leagues": sorted({p["league"] for p in pool["players"]}), "count": len(pool["players"]), "game_date": pool["game_date"]}


@router.get("/rankings")
async def rankings(role: str | None = None, league: str | None = None, max_age: int = Query(40, ge=15, le=45), q: str = Query("", max_length=60),
                   sort: Literal["score", "vfm", "fit", "pa", "value"] = "score", shortlist_only: bool = False):
    c = await active_career()
    if role and role not in roles.ROLES:
        raise HTTPException(422, "Unknown role")
    pool = await _pool(c)
    params = (await current_rules(c["id"], "scouting"))["data"]["params"]
    players = [p for p in pool["players"] if (not role or set(p["positions"]) & set(roles.ROLE_POSITIONS[role]))]
    scored = score_players(players, params, role)
    sl = await shortlisted(c["id"])
    seen = await season_per90(c["id"], pool.get("season"), "them")
    ql = q.lower().strip()
    rows = [r | {"shortlisted": r["unique_id"] in sl, "seen_vs_us": seen.get(r["unique_id"], {}).get("matches", 0),
                 "match_rating": seen.get(r["unique_id"], {}).get("avg_rating"), "per90": seen.get(r["unique_id"], {}).get("per90")} for r in scored if r["age"] <= max_age and (not league or r["league"] == league)
            and (not ql or ql in r["name"].lower() or ql in r["club"].lower()) and (not shortlist_only or r["unique_id"] in sl)]
    rows.sort(key=lambda r: r[sort] if sort != "value" else -r["value"], reverse=True)
    return {"total": len(rows), "rows": rows[:80], "weights": params}


class ShortlistIn(BaseModel):
    unique_id: int
    action: Literal["add", "remove"]


@router.post("/shortlist")
async def shortlist(body: ShortlistIn):
    c = await active_career()
    pool = await _pool(c)
    if body.unique_id not in {p["unique_id"] for p in pool["players"]}:
        raise HTTPException(404, "Player not found in the scouting pool")
    await db.shortlist.insert_one({"id": new_id(), "career_id": c["id"], "unique_id": body.unique_id,
                                   "status": "active" if body.action == "add" else "removed", "at": now_iso()})
    return {"ok": True}


class SendIn(BaseModel):
    ids: list[int] = Field(min_length=1, max_length=200)


@router.post("/send-to-fm")
async def send_to_fm(body: SendIn):
    """Queue players for FM's own shortlist; they go in with your other game changes."""
    from changes_api import queue_shortlist
    c = await active_career()
    by = {p["unique_id"]: p for p in (await _pool(c))["players"]}
    found = [by[u] for u in dict.fromkeys(body.ids) if u in by]
    if not found:
        raise HTTPException(404, "None of these players are in the scouting pool")
    return await queue_shortlist(c, found) | {"not_found": len(set(body.ids)) - len(found)}


@router.get("/compare")
async def compare(ids: str = Query(..., max_length=200)):
    c = await active_career()
    try:
        wanted = [int(x) for x in ids.split(",") if x][:4]
    except ValueError:
        raise HTTPException(422, "Bad player ids")
    pool = await _pool(c)
    own = (await latest_snapshot(c["id"]))["players"]
    params = (await current_rules(c["id"], "scouting"))["data"]["params"]
    everyone = {p["unique_id"]: p for p in own} | {p["unique_id"]: p for p in pool["players"]}
    found = [everyone[i] for i in wanted if i in everyone]
    own_ids = {p["unique_id"] for p in own}
    scored = {s["unique_id"]: s for s in score_players([p | {"club": p.get("club", c["club_name"]), "league": p.get("league", "My club"),
                                                               "value": p.get("value", 0) or 1_000_000} for p in found], params, None)}
    keys = ["passing", "technique", "vision", "decisions", "pace", "finishing", "tackling", "positioning"]
    return [scored[p["unique_id"]] | {"own": p["unique_id"] in own_ids, "roles": roles.role_ratings(p)[:3],
                                      "attributes": {k: p["attributes"].get(k) for k in keys}} for p in found]


def fmt_value(v: int) -> str:
    return f"£{v / 1_000_000:.1f}m" if v >= 1_000_000 else f"£{math.floor(v / 1000)}k"
