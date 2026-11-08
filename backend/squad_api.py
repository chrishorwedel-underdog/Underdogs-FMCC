from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

import roles
from core import db, active_career, latest_two, month_minutes, now_iso, new_id, next_revision
from rules_api import current as current_rules

router = APIRouter(prefix="/api")
Formation = Literal["433", "4231"]


async def _plan_inputs(c: dict, formation: str):
    snaps = await latest_two(c["id"])
    if not snaps:
        raise HTTPException(404, "No save read yet")
    latest = snaps[0]
    mins = month_minutes(latest, snaps[1] if len(snaps) > 1 else None)
    form = roles.formation_meta(formation)
    depth = roles.depth_chart(latest["players"], form)
    info = {p["unique_id"]: {"name": p["name"], "age": p["age"], "u21": p["age"] < 21, "month_minutes": mins[p["unique_id"]],
                             "positions": p["positions"], "ca": p["ca"]} for p in latest["players"]}
    params = (await current_rules(c["id"], "squad"))["data"]["params"]
    return latest, form, depth, info, params


@router.get("/squad/plan")
async def squad_plan(formation: Formation = "433"):
    c = await active_career()
    latest, form, depth, info, params = await _plan_inputs(c, formation)
    rules = {k: int(v) for k, v in params.items()}
    best = roles.best_xi(latest["players"], form, depth)
    dev, picked, dev_why = roles.development_xi(best, form, depth, info, rules)
    labels = {s["key"]: s["label"] for s in form["slots"]}
    weak = [{"slot": s["key"], "label": s["label"], "best": depth[s["key"]][0]["rating"] if depth[s["key"]] else 0,
             "options": len(depth[s["key"]])} for s in form["slots"]]
    saved = await db.lineups.find_one({"career_id": c["id"], "formation": formation}, {"_id": 0}, sort=[("revision", -1)])
    youth = sorted([{"unique_id": u, **i} for u, i in info.items() if i["u21"]], key=lambda y: y["month_minutes"])
    return {"formation": form, "formations": {k: v[0] for k, v in roles.FORMATIONS.items()}, "save_no": latest["save_no"], "game_date": latest["game_date"],
            "players": info, "depth": depth, "rules": rules,
            "best": {"slots": best, "strength": roles.strength(best, depth), "why": roles.best_why(best, form, depth, info, rules)},
            "dev": {"slots": dev, "strength": roles.strength(dev, depth), "why": dev_why, "youth": picked},
            "weak": sorted(weak, key=lambda w: w["best"]), "youth_minutes": youth, "saved": saved,
            "weak_spot": roles.weak_spot(best, depth, labels)}


class LineupIn(BaseModel):
    formation: Formation
    kind: Literal["best", "dev", "custom"]
    slots: dict[str, int]
    based_on_save_no: int
    expected_revision: int = Field(ge=0)
    name: str = Field("", max_length=60)


@router.post("/lineups")
async def save_lineup(body: LineupIn):
    """Saved lineups are append-only: every save is a new revision."""
    c = await active_career()
    latest, form, depth, info, _ = await _plan_inputs(c, body.formation)
    if body.based_on_save_no != latest["save_no"]:
        raise HTTPException(409, "A newer save was read since you opened this lineup. Reload to see the latest squad.")
    if set(body.slots) != {s["key"] for s in form["slots"]}:
        raise HTTPException(422, "Every position in the formation needs one player")
    if len(set(body.slots.values())) != len(body.slots):
        raise HTTPException(422, "A player can only appear once in a lineup")
    for slot, uid in body.slots.items():
        if uid not in {r["unique_id"] for r in depth[slot]}:
            raise HTTPException(422, f"{info.get(uid, {}).get('name', 'That player')} can't play {slot} or is no longer in the squad")
    rev = await next_revision("lineups", {"career_id": c["id"], "formation": body.formation})
    if rev - 1 != body.expected_revision:
        raise HTTPException(409, "This lineup was changed somewhere else. Reload to see the latest version.")
    doc = {"id": new_id(), "career_id": c["id"], "formation": body.formation, "kind": body.kind, "slots": body.slots,
           "strength": roles.strength(body.slots, depth), "based_on_save_no": body.based_on_save_no, "revision": rev,
           "name": body.name or {"best": "Best XI", "dev": "Development XI", "custom": "Custom lineup"}[body.kind], "saved_at": now_iso()}
    try:
        await db.lineups.insert_one(dict(doc))
    except DuplicateKeyError:
        raise HTTPException(409, "This lineup was saved at the same moment somewhere else. Reload and try again.")
    return {"revision": rev, "strength": doc["strength"]}


@router.get("/lineups")
async def lineup_history(formation: Formation = "433"):
    c = await active_career()
    return await db.lineups.find({"career_id": c["id"], "formation": formation}, {"_id": 0}).sort("revision", -1).limit(30).to_list(30)


@router.get("/squad/registration")
async def registration():
    c = await active_career()
    latest = (await latest_two(c["id"]))[0]
    p = (await current_rules(c["id"], "squad"))["data"]["params"]
    max_senior, min_hg = int(p["max_senior"]), int(p["min_homegrown"])
    seniors = sorted([x for x in latest["players"] if x["age"] >= 21], key=lambda x: -roles.best_role(x)["rating"])
    u21 = [x for x in latest["players"] if x["age"] < 21]
    registered = seniors[:max_senior]
    left_out = seniors[max_senior:]
    hg = [x for x in registered if x.get("homegrown")]
    checks = [
        {"key": "senior", "label": "Senior squad size", "value": len(seniors), "limit": f"max {max_senior}", "ok": len(seniors) <= max_senior,
         "detail": "Players aged 21 or over count towards the senior list."},
        {"key": "homegrown", "label": "Homegrown players", "value": len(hg), "limit": f"min {min_hg}", "ok": len(hg) >= min_hg,
         "detail": f"Each missing homegrown player removes one senior place ({max(0, min_hg - len(hg))} short)." if len(hg) < min_hg else "Quota met."},
        {"key": "u21", "label": "Under-21 list", "value": len(u21), "limit": "no limit", "ok": True, "detail": "Under-21s can be registered without using a senior place."},
    ]
    suggestions = [f"Leave out {x['name']} (role rating {roles.best_role(x)['rating']}) to stay within {max_senior} seniors." for x in left_out]
    if len(hg) < min_hg:
        suggestions.append(f"Sign or keep {min_hg - len(hg)} more homegrown senior player(s), or your senior list shrinks to {max_senior - (min_hg - len(hg))}.")
    return {"checks": checks, "suggestions": suggestions, "preset": "Example league preset (edit in Rules)",
            "homegrown": [{"unique_id": x["unique_id"], "name": x["name"]} for x in hg]}
