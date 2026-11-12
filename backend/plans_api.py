from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from core import db, active_career, latest_two, month_minutes, now_iso, new_id, next_revision, season_start_ca
from rules_api import current as current_rules

router = APIRouter(prefix="/api")
LOANS = {"none": "Stay at the club", "loan_lower": "Loan to a lower league", "loan_same": "Loan to a club at our level", "loan_abroad": "Loan abroad"}
MONTH_NOTES = [(3, "big", "Big step forward this month"), (1, "up", "Improving this month"), (0, "flat", "Holding steady this month"), (None, "down", "Slipped back a little this month")]
SEASON_NOTES = [(6, "big", "Strong progress this season"), (1, "up", "Some progress this season"), (0, "flat", "No change yet this season"), (None, "down", "Behind where he started the season")]


def _note(delta: int, notes: list) -> dict:
    """Plain-words progress; the underlying ability number never leaves the backend."""
    for floor, tone, text in notes:
        if floor is None or delta >= floor:
            return {"tone": tone, "text": text}


def _trend(vals: list) -> list:
    """Direction of each save-to-save step only (up/flat/down), never the size."""
    return ["up" if b > a else "down" if b < a else "flat" for a, b in zip(vals, vals[1:])]



async def latest_plans(career_id: str) -> dict:
    pipeline = [{"$match": {"career_id": career_id}}, {"$sort": {"revision": -1}}, {"$group": {"_id": "$unique_id", "doc": {"$first": "$$ROOT"}}},
                {"$replaceRoot": {"newRoot": "$doc"}}, {"$project": {"_id": 0}}]
    return {d["unique_id"]: d async for d in db.plans.aggregate(pipeline)}


@router.get("/development")
async def development():
    c = await active_career()
    snaps = await latest_two(c["id"])
    if not snaps:
        raise HTTPException(404, "No save read yet")
    latest = snaps[0]
    mins = month_minutes(latest, snaps[1] if len(snaps) > 1 else None)
    params = (await current_rules(c["id"], "development"))["data"]["params"]
    plans = await latest_plans(c["id"])
    prev = {p["unique_id"]: p for p in snaps[1]["players"]} if len(snaps) > 1 else {}
    start = await season_start_ca(c["id"], latest["season"])
    recent = await db.snapshots.find({"career_id": c["id"]}, {"_id": 0, "players.unique_id": 1, "players.ca": 1}).sort("save_no", -1).limit(6).to_list(6)
    hist = [{p["unique_id"]: p["ca"] for p in s["players"]} for s in reversed(recent)]
    rows = []
    for p in latest["players"]:
        uid = p["unique_id"]
        plan = plans.get(uid)
        target = plan["minutes_target"] if plan else (int(params["default_target"]) if p["age"] < 21 else None)
        gain = (p["ca"] - plan["start_ca"]) if plan and plan.get("start_ca") is not None else None
        goal = (plan["goal_ca"] - plan["start_ca"]) if plan and plan.get("goal_ca") and plan.get("start_ca") is not None else None
        apps = p.get("appearances") or 0
        if plan:
            plan = {k: v for k, v in plan.items() if k not in ("goal_ca", "start_ca")} | {"goal_gain": goal}
        rows.append({"unique_id": uid, "name": p["name"], "age": p["age"], "positions": p["positions"],
                     "progress_month": _note(p["ca"] - prev[uid]["ca"], MONTH_NOTES) if uid in prev else None, "progress_season": _note(p["ca"] - start[uid], SEASON_NOTES) if uid in start else None,
                     "trend": _trend([h[uid] for h in hist if uid in h]), "starts": p.get("starts"), "sub_apps": p.get("sub_apps"),
                     "goals": p.get("goals", 0), "assists": p.get("assists", 0), "appearances": apps, "avg_rating": p.get("avg_rating"),
                     "minutes_per_game": round(p["minutes"] / apps) if apps else None,
                     "month_minutes": mins[uid], "season_minutes": p["minutes"], "plan": plan, "target": target,
                     "needs_minutes": bool(target) and mins[uid] < target * params["needs_pct"] / 100,
                     "goal_so_far": gain, "goal_progress": round(max(0, min(100, gain / goal * 100))) if goal and gain is not None else None})
    rows.sort(key=lambda r: (r["plan"] is None, r["age"]))
    return {"game_date": latest["game_date"], "rows": rows, "loans": LOANS, "params": params}


class PlanIn(BaseModel):
    unique_id: int
    minutes_target: int = Field(ge=0, le=1000)
    loan: Literal["none", "loan_lower", "loan_same", "loan_abroad"] = "none"
    goal_gain: int | None = Field(None, ge=1, le=60)
    note: str = Field("", max_length=300)
    expected_revision: int = Field(ge=0)


@router.post("/development/plans")
async def save_plan(body: PlanIn):
    """Plans are append-only: revising one keeps every earlier version."""
    c = await active_career()
    latest = (await latest_two(c["id"]))[0]
    p = next((x for x in latest["players"] if x["unique_id"] == body.unique_id), None)
    if not p:
        raise HTTPException(404, "This player is no longer in your squad")
    rev = await next_revision("plans", {"career_id": c["id"], "unique_id": body.unique_id})
    if rev - 1 != body.expected_revision:
        raise HTTPException(409, "This plan was changed somewhere else. Reload to see the latest version.")
    goal = {"start_ca": p["ca"], "goal_ca": min(200, p["ca"] + body.goal_gain)} if body.goal_gain else {"start_ca": p["ca"], "goal_ca": None}
    doc = body.model_dump(exclude={"expected_revision", "goal_gain"}) | goal | {"id": new_id(), "career_id": c["id"], "revision": rev, "name": p["name"],
                                                             "saved_at": now_iso(), "game_date": latest["game_date"]}
    try:
        await db.plans.insert_one(dict(doc))
    except DuplicateKeyError:
        raise HTTPException(409, "This plan was saved at the same moment somewhere else. Reload and try again.")
    return {"revision": rev}


@router.get("/development/plans/{unique_id}/history")
async def plan_history(unique_id: int):
    c = await active_career()
    out = await db.plans.find({"career_id": c["id"], "unique_id": unique_id}, {"_id": 0}).sort("revision", -1).to_list(100)
    for h in out:
        g, s = h.pop("goal_ca", None), h.pop("start_ca", None)
        h["goal_gain"] = g - s if g and s is not None else None
    return out


@router.get("/reports/months")
async def report_months():
    c = await active_career()
    snaps = await db.snapshots.find({"career_id": c["id"]}, {"_id": 0, "save_no": 1, "game_date": 1, "season": 1}).sort("save_no", 1).to_list(None)
    by_month = {}
    for s in snaps:
        by_month[s["game_date"][:7]] = s
    return list(by_month.values())


@router.get("/reports/compare")
async def report_compare(a: int = Query(ge=0), b: int = Query(ge=0)):
    c = await active_career()
    sa = await db.snapshots.find_one({"career_id": c["id"], "save_no": a}, {"_id": 0})
    sb = await db.snapshots.find_one({"career_id": c["id"], "save_no": b}, {"_id": 0})
    if not sa or not sb:
        raise HTTPException(404, "Report month not found")
    params = (await current_rules(c["id"], "reports"))["data"]["params"]
    pa_ = {p["unique_id"]: p for p in sa["players"]}
    rows = []
    for p in sb["players"]:
        o = pa_.get(p["unique_id"])
        if not o:
            continue
        d = p["ca"] - o["ca"]
        mins = p["minutes"] - o["minutes"] if sa["season"] == sb["season"] else p["minutes"]
        rows.append({"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "ca_change": d, "assists": p.get("assists", 0) - (o.get("assists", 0) if sa["season"] == sb["season"] else 0),
                     "minutes": mins, "avg_rating": p.get("avg_rating"), "goals": p.get("goals", 0) - (o.get("goals", 0) if sa["season"] == sb["season"] else 0),
                     "trend": "rising" if d >= params["rising"] else "falling" if d <= params["falling"] else "steady"})
    rows.sort(key=lambda r: -r["ca_change"])
    ids_b = {p["unique_id"] for p in sb["players"]}
    return {"from": sa["game_date"], "to": sb["game_date"], "rows": rows, "params": params,
            "summary": {"total_change": sum(r["ca_change"] for r in rows), "rising": sum(r["trend"] == "rising" for r in rows),
                        "falling": sum(r["trend"] == "falling" for r in rows),
                        "joined": [p["name"] for p in sb["players"] if p["unique_id"] not in pa_],
                        "left": [p["name"] for p in sa["players"] if p["unique_id"] not in ids_b]}}
