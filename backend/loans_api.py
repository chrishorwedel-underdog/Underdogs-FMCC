"""Loan Manager: grade a possible loan (A+ to F) and track loanees. Facilities aren't in the save yet, so they're never guessed."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core import db, active_career, now_iso
from scout_api import _data

router = APIRouter(prefix="/api/loans")
STARTERS = {"CB": 2, "CM": 2, "W": 2, "FB": 2}
GRADES = [(93, "A+"), (87, "A"), (82, "A-"), (77, "B+"), (72, "B"), (67, "B-"), (62, "C+"), (57, "C"), (52, "C-"), (46, "D+"), (40, "D"), (34, "D-"), (0, "F")]


def _letter(s: float) -> str:
    return next(g for lim, g in GRADES if s >= lim)


def assess(x: dict, club_players: list) -> dict:
    g = x.get("group")
    mates = sorted([p for p in club_players if p.get("group") == g and p["unique_id"] != x["unique_id"]], key=lambda p: -(p.get("grade_global") or 0))
    mine = x.get("grade_global") or 0
    rank = 1 + sum(1 for p in mates if (p.get("grade_global") or 0) > mine)
    n = STARTERS.get(g, 1)
    minutes = 90 if rank <= n else 55 if rank == n + 1 else 25 if rank == n + 2 else 8
    league = club_players[0].get("league_mult") or 0.8 if club_players else 0.8
    lvl = max(0, min(100, 100 * (league - 0.55) / 0.45))
    dev = 100 if x["age"] <= 21 else 75 if x["age"] <= 23 else 50
    score = 0.55 * minutes + 0.25 * lvl + 0.20 * dev
    role = "a regular starter" if rank <= n else "rotation" if rank == n + 1 else "a bench option" if rank == n + 2 else "rarely used"
    reason = f"Would likely be {role} (#{rank} at {x.get('cohort', g)}) in a league rated ×{round(league, 2)}" + (", a good step for his age" if x["age"] <= 21 and rank <= n else "")
    depth = [{"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "grade": p.get("grade_global")} for p in mates[:6]]
    return {"grade": _letter(score), "score": round(score), "reason": reason, "rank": rank, "expected_minutes_pct": minutes, "depth": depth,
            "league": club_players[0].get("league") if club_players else None, "facilities": None, "facilities_note": "Facilities aren't in the save yet"}


class TryIn(BaseModel):
    unique_id: int
    club: str = Field(min_length=1, max_length=80)


@router.get("/clubs")
async def clubs():
    _, data = await _data()
    return sorted({x["club"] for x in data["players"] if not x.get("own") and x.get("club") and x.get("source") == "save" and x.get("gender", "M") == "M"})


@router.post("/try")
async def try_loan(body: TryIn):
    _, data = await _data()
    x = next((p for p in data["players"] if p["unique_id"] == body.unique_id and p.get("own")), None)
    if not x:
        raise HTTPException(404, "Pick a player from your own squad")
    club = [p for p in data["players"] if p.get("club") == body.club and not p.get("own") and p.get("gender", "M") == x.get("gender", "M")]
    if not club:
        raise HTTPException(404, "That club isn't in the scouting data")
    return {"player": {"unique_id": x["unique_id"], "name": x["name"], "age": x["age"], "group": x.get("group")}, "club": body.club} | assess(x, club)


@router.post("/track")
async def track(body: TryIn):
    c, data = await _data()
    if not any(p["unique_id"] == body.unique_id and p.get("own") for p in data["players"]) or not any(p.get("club") == body.club for p in data["players"]):
        raise HTTPException(404, "Pick one of your players and a club from the save")
    await db.loans.update_one({"career_id": c["id"], "unique_id": body.unique_id}, {"$set": {"club": body.club, "at": now_iso(), "active": True}}, upsert=True)
    return {"ok": True}


@router.delete("/track/{uid}")
async def untrack(uid: int):
    c = await active_career()
    await db.loans.delete_one({"career_id": c["id"], "unique_id": uid})
    return {"ok": True}


def trend(x: dict) -> tuple:
    r, m = x.get("avg_rating"), x.get("minutes") or 0
    if r is None or m < 270:
        return "down", "red", "Hardly playing"
    if r >= 7.2 and m >= 900:
        return "up", "gold", f"Excellent: {r} average over {m} minutes"
    if r >= 6.7:
        return "up", "green", f"Going well: {r} average"
    return "down", "red", f"Struggling: {r} average"


@router.get("")
async def loans():
    c, data = await _data()
    by = {p["unique_id"]: p for p in data["players"]}
    pool = {p["unique_id"]: p for p in (await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}) or {"players": []})["players"]}
    snap = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}, sort=[("save_no", -1)]) or {"players": []}
    pool |= {p["unique_id"]: p for p in snap["players"]}
    rows = []
    async for t in db.loans.find({"career_id": c["id"], "active": True}, {"_id": 0}):
        x = by.get(t["unique_id"])
        if not x:
            continue
        x = x | {k: pool.get(t["unique_id"], {}).get(k) for k in ("avg_rating", "goals", "assists")}
        arrow, tone, why = trend(x)
        rows.append({"unique_id": x["unique_id"], "name": x["name"], "age": x["age"], "club": t["club"], "league": next((p.get("league") for p in data["players"] if p.get("club") == t["club"]), None),
                     "minutes": x.get("minutes"), "avg_rating": x.get("avg_rating"), "goals": x.get("goals"), "assists": x.get("assists"),
                     "facilities": None, "arrow": arrow, "tone": tone, "why": why})
    return {"rows": rows, "note": "Stats are this season's, from the latest save. Facilities aren't in the save yet."}
