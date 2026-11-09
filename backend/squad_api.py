from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

import roles
from core import db, active_career, latest_two, month_minutes, now_iso, new_id, next_revision
from rules_api import current as current_rules

router = APIRouter(prefix="/api")
Formation = Literal[tuple(roles.ALL_FORMATIONS)]


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


def _registered(players: list, max_senior: int, min_hg: int) -> list:
    """Senior list by role rating, shrunk by each missing homegrown player; under-21s are always eligible."""
    seniors = sorted([x for x in players if x["age"] >= 21], key=lambda x: -roles.best_role(x)["rating"])
    hg = [x for x in seniors if x.get("homegrown")][:min_hg]
    places = max_senior - max(0, min_hg - len(hg))
    rest = [x for x in seniors if x not in hg][:max(0, places - len(hg))]
    return hg + rest + [x for x in players if x["age"] < 21]


def _xi(players: list, form: dict, full_depth: dict) -> dict:
    depth = roles.depth_chart(players, form)
    if any(not depth[s["key"]] for s in form["slots"]):
        return {}
    slots = roles.best_xi(players, form, depth)
    return {"slots": slots, "strength": roles.strength(slots, full_depth)}


def competition_xis(players: list, form: dict, depth: dict, best: dict, info: dict, params: dict) -> dict:
    """Domestic XI: strongest league-registered side. Cup XI: rests the most-used regulars. UEFA XI: strongest side from the UEFA List A + B."""
    by = {p["unique_id"]: p for p in players}
    max_senior, min_hg = int(params.get("max_senior", 25)), int(params.get("min_homegrown", 8))
    rest_n, uefa_max, uefa_hg = int(params.get("cup_rest", 4)), int(params.get("uefa_max", 25)), int(params.get("uefa_min_homegrown", 8))
    league = _registered(players, max_senior, min_hg)
    dom = _xi(league, form, depth) or {"slots": best, "strength": roles.strength(best, depth)}
    rested = sorted(dom["slots"].values(), key=lambda u: -info[u]["month_minutes"])[:rest_n]
    cup = _xi([p for p in players if p["unique_id"] not in rested], form, depth) or dom
    uefa_list = _registered(players, uefa_max, uefa_hg)
    uefa = _xi(uefa_list, form, depth) or dom
    left_out = [by[u]["name"] for u in by if u not in {p["unique_id"] for p in uefa_list}]
    name = lambda u: info[u]["name"]  # noqa: E731
    return {
        "domestic": dom | {"why": [["acc", f"Strongest side from your league squad list ({max_senior} seniors, at least {min_hg} homegrown, under-21s free)."],
                                    ["blu", "Use it for league matches."]]},
        "cup": cup | {"rested": [name(u) for u in rested], "why": [["amb", f"Rests the {len(rested)} most-used regulars this month: {', '.join(name(u) for u in rested) or 'nobody'}."],
                                                              ["blu", "Everyone else picked on role rating, so fringe and young players get a game."]]},
        "uefa": uefa | {"left_out": left_out, "why": [["acc", f"Strongest side from your UEFA List A ({uefa_max} places, at least {uefa_hg} homegrown) plus List B under-21s."],
                                                     ["amb" if left_out else "blu", f"Not registered: {', '.join(left_out)}." if left_out else "Everyone fits on the UEFA lists."]]}}


async def team_tactics(c: dict) -> dict:
    """Your club's tactics from the latest save, as FMCC formation key -> label (empty if the save has none)."""
    snap = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "tactics": 1}, sort=[("save_no", -1)]) or {}
    out = {}
    for t in snap.get("tactics") or []:
        k = roles.match_tactic(t)
        if k and k not in out:
            shape = roles.ALL_FORMATIONS[k][0]
            out[k] = t["name"] if shape in (t.get("name") or "") else f"{t.get('name') or 'Tactic'} ({shape})"
    return out


@router.get("/squad/plan")
async def squad_plan(formation: Optional[Formation] = None):
    c = await active_career()
    yours = await team_tactics(c)
    main = yours or {k: v[0] for k, v in roles.FORMATIONS.items()}
    formation = formation or next(iter(main))
    latest, form, depth, info, params = await _plan_inputs(c, formation)
    rules = {k: int(v) for k, v in params.items()}
    best = roles.best_xi(latest["players"], form, depth)
    dev, picked, dev_why = roles.development_xi(best, form, depth, info, rules)
    labels = {s["key"]: s["label"] for s in form["slots"]}
    weak = [{"slot": s["key"], "label": s["label"], "best": depth[s["key"]][0]["rating"] if depth[s["key"]] else 0,
             "options": len(depth[s["key"]])} for s in form["slots"]]
    saved = await db.lineups.find_one({"career_id": c["id"], "formation": formation}, {"_id": 0}, sort=[("revision", -1)])
    for i in info.values():
        i.pop("ca", None)
    youth = sorted([{"unique_id": u, **i} for u, i in info.items() if i["u21"]], key=lambda y: y["month_minutes"])
    return {"formation": form, "formations": main, "from_save": bool(yours), "all_formations": {k: v[0] for k, v in roles.ALL_FORMATIONS.items()},
            "save_no": latest["save_no"], "game_date": latest["game_date"], "players": info, "depth": depth, "rules": rules,
            **competition_xis(latest["players"], form, depth, best, info, params),
            "best": {"slots": best, "strength": roles.strength(best, depth), "why": roles.best_why(best, form, depth, info, rules)},
            "dev": {"slots": dev, "strength": roles.strength(dev, depth), "why": dev_why, "youth": picked},
            "weak": sorted(weak, key=lambda w: w["best"]), "youth_minutes": youth, "saved": saved,
            "weak_spot": roles.weak_spot(best, depth, labels)}


class LineupIn(BaseModel):
    formation: Formation
    kind: Literal["best", "dev", "domestic", "cup", "uefa", "custom"]
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
           "name": body.name or {"best": "Best XI", "dev": "Development XI", "domestic": "Domestic XI", "cup": "Cup XI", "uefa": "UEFA XI", "custom": "Custom lineup"}[body.kind],
           "saved_at": now_iso()}
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
