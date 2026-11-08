from typing import Literal

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

from core import db, active_career, latest_two, month_minutes, now_iso, new_id, next_revision
from rules_api import current as current_rules

router = APIRouter(prefix="/api")
LOANS = {"none": "Stay at the club", "loan_lower": "Loan to a lower league", "loan_same": "Loan to a club at our level", "loan_abroad": "Loan abroad"}


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
    rows = []
    for p in latest["players"]:
        plan = plans.get(p["unique_id"])
        target = plan["minutes_target"] if plan else (int(params["default_target"]) if p["age"] < 21 else None)
        rows.append({"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "positions": p["positions"], "ca": p["ca"], "pa": p["pa"],
                     "month_minutes": mins[p["unique_id"]], "season_minutes": p["minutes"], "plan": plan, "target": target,
                     "needs_minutes": bool(target) and mins[p["unique_id"]] < target * params["needs_pct"] / 100,
                     "goal_progress": round(min(100, p["ca"] / plan["goal_ca"] * 100)) if plan and plan.get("goal_ca") else None})
    rows.sort(key=lambda r: (r["plan"] is None, r["age"]))
    return {"game_date": latest["game_date"], "rows": rows, "loans": LOANS, "params": params}


class PlanIn(BaseModel):
    unique_id: int
    minutes_target: int = Field(ge=0, le=1000)
    loan: Literal["none", "loan_lower", "loan_same", "loan_abroad"] = "none"
    goal_ca: int | None = Field(None, ge=1, le=200)
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
    doc = body.model_dump(exclude={"expected_revision"}) | {"id": new_id(), "career_id": c["id"], "revision": rev, "name": p["name"],
                                                             "saved_at": now_iso(), "game_date": latest["game_date"]}
    try:
        await db.plans.insert_one(dict(doc))
    except DuplicateKeyError:
        raise HTTPException(409, "This plan was saved at the same moment somewhere else. Reload and try again.")
    return {"revision": rev}


@router.get("/development/plans/{unique_id}/history")
async def plan_history(unique_id: int):
    c = await active_career()
    return await db.plans.find({"career_id": c["id"], "unique_id": unique_id}, {"_id": 0}).sort("revision", -1).to_list(100)


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
        rows.append({"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "ca_from": o["ca"], "ca_to": p["ca"], "ca_change": d,
                     "minutes": mins, "avg_rating": p.get("avg_rating"), "goals": p.get("goals", 0) - (o.get("goals", 0) if sa["season"] == sb["season"] else 0),
                     "trend": "rising" if d >= params["rising"] else "falling" if d <= params["falling"] else "steady"})
    rows.sort(key=lambda r: -r["ca_change"])
    ids_b = {p["unique_id"] for p in sb["players"]}
    return {"from": sa["game_date"], "to": sb["game_date"], "rows": rows, "params": params,
            "summary": {"total_change": sum(r["ca_change"] for r in rows), "rising": sum(r["trend"] == "rising" for r in rows),
                        "falling": sum(r["trend"] == "falling" for r in rows),
                        "joined": [p["name"] for p in sb["players"] if p["unique_id"] not in pa_],
                        "left": [p["name"] for p in sa["players"] if p["unique_id"] not in ids_b]}}
