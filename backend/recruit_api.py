"""Recruitment Lab: role and philosophy scores, indices, compare, shortlist board, DOF picks, extra stats and benchmarks."""
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

import roles
import stats_model as sm
from core import db, active_career, now_iso, new_id, audit
from sample_reader import GROUP

router = APIRouter(prefix="/api/recruit")
View = Literal["full", "fair", "moneyball"]

INDICES = {"chance_creation": ("Chance creation", ["xa", "kp", "chc", "ccr"]), "ball_security": ("Ball security", ["passc", "plost", "epl"]),
           "progression": ("Ball progression", ["progp", "ppc", "drb"]), "shot_threat": ("Shot threat", ["npxg", "sot", "xgs"]),
           "finishing": ("Finishing", ["npg", "xgo", "sha"]), "ball_winning": ("Ball winning", ["tkw", "intc", "pwon", "tkr"]),
           "pressing": ("Pressing", ["prr", "pwon", "ktk"]), "engine": ("Engine", ["spr", "pwon"]), "aerial": ("Aerial", ["aerw", "aerr"]),
           "box_defending": ("Box defending", ["blk", "padbc", "khkt"]), "discipline": ("Discipline", ["err", "mlg"]), "crossing": ("Crossing", ["crc", "acr"])}
TRAITS = {"keep_ball": ("Keep the ball", ["passc", "plost", "pcmp"]), "available": ("Always available", ["pcmp", "ppc"]),
          "hurt": ("Move it to hurt", ["progp", "ppc", "drb", "xa"]), "win_back": ("Win it back in five", ["pwon", "prr", "tkw"]),
          "front_foot": ("Defend on the front foot", ["intc", "ktk", "aerr"]), "intensity": ("Intensity", ["spr", "pwon", "prr"])}
GROUPS = {"Shooting": ["npxg", "npg", "sot", "sha", "xgs"], "Creating": ["xa", "kp", "chc", "ccr"], "Possession": ["passc", "pcmp", "progp", "drb", "plost"],
          "Aerial": ["aerw", "aerr"], "Out of possession": ["tkw", "intc", "pwon", "prr", "blk"]}
GOOD = {"Model Citizen", "Model Professional", "Perfectionist", "Resolute", "Professional", "Driven", "Determined", "Very Ambitious", "Ambitious", "Born Leader", "Iron Willed"}
BAD = {"Temperamental", "Unambitious", "Low Determination", "Slack", "Casual", "Mercenary", "Low Self-Belief", "Volatile", "Spineless"}
EXTRA = {"shots": "Shots / 90", "conv": "Conversion %", "gax": "Goals above xG / 90", "security": "Ball security %", "pass_att": "Passes attempted / 90",
         "contrib": "Goal contributions / 90", "xgxa": "Non-penalty xG + xA / 90", "tklint": "Tackles + interceptions / 90", "min_share": "Share of minutes %"}


def avg(vals):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals)) if vals else None


def extra(x: dict, season_minutes: int) -> dict:
    p = x["p90"] or {}
    g = lambda k: p.get(k)  # noqa: E731
    out = {}
    if g("sot") is not None and g("sha"):
        out["shots"] = round(g("sot") / (g("sha") / 100), 2)
        if g("npg") is not None and out["shots"]:
            out["conv"] = round(g("npg") / out["shots"] * 100, 1)
    if g("npg") is not None and g("npxg") is not None:
        out["gax"] = round(g("npg") - g("npxg"), 2)
    if g("pcmp") is not None and g("plost") is not None and g("pcmp") + g("plost"):
        out["security"] = round(100 - g("plost") / (g("pcmp") + g("plost")) * 100, 1)
    if g("pcmp") is not None and g("passc"):
        out["pass_att"] = round(g("pcmp") / (g("passc") / 100), 1)
    if g("gls") is not None and g("ast") is not None:
        out["contrib"] = round(g("gls") + g("ast"), 2)
    if g("npxg") is not None and g("xa") is not None:
        out["xgxa"] = round(g("npxg") + g("xa"), 2)
    if g("tkw") is not None and g("intc") is not None:
        out["tklint"] = round(g("tkw") + g("intc"), 2)
    if season_minutes:
        out["min_share"] = round(min(100, x["minutes"] / season_minutes * 100), 1)
    return out


def role_metrics(role: str) -> list:
    cohort = sm.COHORT[GROUP[roles.ROLE_POSITIONS[role][0]]]
    ms = sorted(sm.WEIGHTS.get(cohort, []), key=lambda m: -m["weight"])
    return [(sm.LABEL2KEY[m["metric"]], m["weight"]) for m in ms if m["metric"] in sm.LABEL2KEY][:8]


def role_score(x: dict, role: str):
    pct = x.get("pct") or {}
    ws = [(k, w) for k, w in role_metrics(role) if pct.get(k) is not None]
    tot = sum(w for _, w in ws)
    return round(sum(pct[k] * w for k, w in ws) / tot) if tot else None


def natural_roles(x: dict) -> list:
    return [r for r, ps in roles.ROLE_POSITIONS.items() if set(ps) & set(x.get("positions") or [])]


def traits(x: dict) -> dict:
    return {k: avg([(x.get("pct") or {}).get(m) for m in ms]) for k, (_, ms) in TRAITS.items()}


def philosophy(x: dict, weights: dict):
    t = traits(x)
    ws = [(k, weights.get(k, 1)) for k in TRAITS if t[k] is not None and weights.get(k, 1) > 0]
    tot = sum(w for _, w in ws)
    return round(sum(t[k] * w for k, w in ws) / tot) if tot else None


def indices(x: dict) -> dict:
    out = {k: {"label": l, "value": avg([(x.get("pct") or {}).get(m) for m in ms])} for k, (l, ms) in INDICES.items()}
    gax = (x["p90"] or {}).get("npg", 0) - (x["p90"] or {}).get("npxg", 0) if x["p90"] else 0
    out["finishing"]["luck"] = gax > .15
    return out


def character(label: Optional[str]) -> dict:
    if not label:
        return {"result": "unknown", "text": "Personality not known (your scouts haven't seen enough, or this view hides it)"}
    return {"result": "pass" if label in GOOD else "fail" if label in BAD else "caution", "text": label}


def league_word(x: dict, ours: float) -> str:
    d = (x.get("league_mult") or 1) - ours
    return "Much stronger" if d > .08 else "Slightly stronger" if d > .03 else "Similar" if d >= -.03 else "Slightly weaker" if d >= -.08 else "Much weaker"


async def _ctx():
    import scout_api
    c, data = await scout_api._data()
    w = await db.philosophy.find_one({"career_id": c["id"]}, {"_id": 0}, sort=[("revision", -1)])
    data["_phil"] = (w or {}).get("weights") or {k: 1 for k in TRAITS}
    own = [x for x in data["players"] if x["own"]]
    data["_ours"] = own[0]["league_mult"] if own else 1.0
    data["_season_min"] = max([x["minutes"] for x in data["players"]] or [0])
    return c, data


def _get(data: dict, uid: int) -> dict:
    x = data["by_uid"].get(uid)
    if not x:
        raise HTTPException(404, "Player not found")
    return x


def starter_for(data: dict, role: str):
    pos = set(roles.ROLE_POSITIONS[role])
    own = [x for x in data["players"] if x["own"] and set(x.get("positions") or []) & pos]
    best = max(own, key=lambda x: role_score(x, role) or 0, default=None)
    return ({"unique_id": best["unique_id"], "name": best["name"], "score": role_score(best, role)} if best else None)


def card(x: dict, data: dict, role: str, view: str, base=None) -> dict:
    import scout_api
    m = scout_api.mask(x, view)
    s = role_score(x, role)
    return {k: m.get(k) for k in ("unique_id", "name", "age", "club", "league", "positions", "value", "wage", "months_left", "personality", "own")} | {
        "score": s, "gain": (s - base) if s is not None and base is not None else None, "philosophy": philosophy(x, data["_phil"]),
        "natural": role in natural_roles(x), "league_word": league_word(x, data["_ours"])}


# ---------- profile ----------
@router.get("/player/{uid}")
async def profile(uid: int, role: Optional[str] = None, view: View = "full"):
    import scout_api
    c, data = await _ctx()
    x = _get(data, uid)
    m = scout_api.mask(x, view)
    nat = natural_roles(x) or ["cd"]
    role = role if role in roles.ROLES else nat[0]
    pct = x.get("pct") or {}
    needs = [{"key": k, "label": sm.METRICS[k][0], "raw": (x["p90"] or {}).get(k), "pct": pct.get(k), "weight": w} for k, w in role_metrics(role)]
    idx = indices(x)
    good = [v["label"] for v in idx.values() if (v["value"] or 0) >= 70]
    weak = [v["label"] for v in idx.values() if v["value"] is not None and v["value"] < 35]
    fit = sorted(({"role": r, "name": f"{roles.ROLES[r][0]} ({roles.ROLES[r][1]})", "score": role_score(x, r), "philosophy": philosophy(x, data["_phil"])} for r in roles.ROLES),
                 key=lambda r: -(r["score"] or 0))[:5]
    cohort = [o for o in data["players"] if o["cohort"] == x["cohort"] and o["league"] == x["league"] and o["p90"]]
    bench = {}
    for k, _ in role_metrics(role):
        vals = sorted(o["p90"][k] for o in cohort if o["p90"].get(k) is not None)
        if vals:
            bench[k] = {"league_avg": round(sum(vals) / len(vals), 2), "top10": round(vals[int(len(vals) * .9)] if len(vals) > 1 else vals[0], 2)}
    hist = await db.stat_history.find({"career_id": c["id"], "unique_id": uid}, {"_id": 0}).sort("season", -1).to_list(2)
    trend = {}
    if len(hist) == 2:
        a, b = hist[0].get("p90") or {}, hist[1].get("p90") or {}
        trend = {k: round(a[k] - b[k], 2) for k in a if k in b and a[k] is not None and b[k] is not None}
    pipe = await db.pipeline.find({"career_id": c["id"], "unique_id": uid}, {"_id": 0, "career_id": 0}).sort("at", -1).to_list(30)
    tactic_roles = [s["role"] for s in roles.formation_meta("433")["slots"]]
    return {"player": {k: m.get(k) for k in ("unique_id", "name", "age", "nationality", "club", "league", "positions", "value", "wage", "contract_end", "months_left",
                                               "minutes", "personality", "confidence", "best_role", "grade_global", "fair_price", "own")}
            | {"height": (x.get("attributes") or {}).get("height") if view == "full" else None, "foot": (x.get("attributes") or {}).get("foot") if view == "full" else None,
               "avg_rating": x.get("avg_rating"), "league_word": league_word(x, data["_ours"])},
            "role": role, "role_name": f"{roles.ROLES[role][0]} ({roles.ROLES[role][1]})", "role_options": list(dict.fromkeys(tactic_roles + nat + list(roles.ROLES))),
            "role_labels": {r: f"{v[0]} ({v[1]})" for r, v in roles.ROLES.items()}, "role_score": role_score(x, role), "philosophy": philosophy(x, data["_phil"]),
            "character": character(m.get("personality")), "needs": needs, "benchmarks": bench, "trend": trend, "traits": traits(x), "weights": data["_phil"],
            "trait_labels": {k: v[0] for k, v in TRAITS.items()}, "indices": idx, "extra": {EXTRA[k]: v for k, v in extra(x, data["_season_min"]).items()},
            "summary": {"strengths": good[:4], "weak": weak[:3]}, "fit": fit, "similar": sm.similar(data, x, n=6), "pipeline": pipe}


class PhilIn(BaseModel):
    weights: dict[str, int] = Field(min_length=1)


@router.get("/philosophy")
async def get_phil():
    c = await active_career()
    w = await db.philosophy.find_one({"career_id": c["id"]}, {"_id": 0}, sort=[("revision", -1)])
    return {"weights": (w or {}).get("weights") or {k: 1 for k in TRAITS}, "labels": {k: v[0] for k, v in TRAITS.items()}, "revision": (w or {}).get("revision", 0)}


@router.put("/philosophy")
async def put_phil(body: PhilIn):
    c = await active_career()
    if set(body.weights) - set(TRAITS) or any(not 0 <= v <= 5 for v in body.weights.values()):
        raise HTTPException(422, "Each weight must be between 0 and 5")
    prev = await get_phil()
    rev = prev["revision"] + 1
    await db.philosophy.insert_one({"id": new_id(), "career_id": c["id"], "weights": {k: body.weights.get(k, 1) for k in TRAITS}, "revision": rev, "at": now_iso()})
    await audit(c["id"], "philosophy saved", "scouting", ", ".join(f"{TRAITS[k][0]} {v}" for k, v in body.weights.items()))
    return {"ok": True, "revision": rev}


STAGES = ("Watching", "Scouted", "Bid", "Signed", "Rejected")


class PipeIn(BaseModel):
    stage: Literal[STAGES]
    note: str = Field(default="", max_length=500)


@router.put("/pipeline/{uid}")
async def set_stage(uid: int, body: PipeIn):
    c, data = await _ctx()
    x = _get(data, uid)
    await db.pipeline.insert_one({"id": new_id(), "career_id": c["id"], "unique_id": uid, "stage": body.stage, "note": body.note.strip(), "at": now_iso()})
    await audit(c["id"], "pipeline", "scouting", f"{x['name']}: {body.stage}", uid, x["name"])
    return {"ok": True}


async def stages(cid: str) -> dict:
    pipe = [{"$match": {"career_id": cid}}, {"$sort": {"at": -1}}, {"$group": {"_id": "$unique_id", "stage": {"$first": "$stage"}}}]
    return {d["_id"]: d["stage"] async for d in db.pipeline.aggregate(pipe)}


# ---------- compare ----------
@router.get("/compare")
async def compare(ids: str = Query(..., max_length=120), view: View = "full"):
    _, data = await _ctx()
    try:
        uids = [int(i) for i in ids.split(",") if i][:4]
    except ValueError:
        raise HTTPException(422, "Bad player list")
    xs = [_get(data, u) for u in uids]
    pool = [o for o in data["players"] if o["cohort"] == xs[0]["cohort"] and o["p90"]]
    groups = []
    for g, ks in GROUPS.items():
        rows = []
        for k in ks:
            vals = sorted(o["p90"][k] for o in pool if o["p90"].get(k) is not None)
            if not vals:
                continue
            cells = [{"raw": None if x["minutes"] < sm.MIN_PCT else (x["p90"] or {}).get(k), "pct": None if x["minutes"] < sm.MIN_PCT else (x.get("pct") or {}).get(k)} for x in xs]
            best = max((i for i, c_ in enumerate(cells) if c_["pct"] is not None), key=lambda i: cells[i]["pct"], default=None)
            rows.append({"key": k, "label": sm.METRICS[k][0], "median": vals[len(vals) // 2], "cells": cells, "best": best})
        groups.append({"group": g, "rows": rows})
    fit_roles = list(dict.fromkeys(r for x in xs for r in natural_roles(x)))[:6]
    import scout_api
    return {"players": [{k: scout_api.mask(x, view).get(k) for k in ("unique_id", "name", "age", "club", "value", "own")} for x in xs], "groups": groups,
            "roles": [{"role": r, "name": roles.ROLES[r][0], "scores": [role_score(x, r) for x in xs]} for r in fit_roles],
            "radar": [{"axis": v[0], **{f"p{i}": indices(x)[k]["value"] for i, x in enumerate(xs)}} for k, v in INDICES.items()],
            "sit": [{"unique_id": o["unique_id"], "name": o["name"], "own": o["own"], "x": o["p90"].get("npxg"), "y": o["p90"].get("npg"), "sel": o["unique_id"] in uids}
                    for o in pool if o["p90"].get("npxg") is not None and o["p90"].get("npg") is not None and o["minutes"] >= sm.MIN_PCT]}


# ---------- explore ----------
@router.get("/explore")
async def explore(x: str = "npxg", y: str = "xa", group: Optional[str] = None, role: Optional[str] = None, view: View = "full"):
    import scouting_api
    c, data = await _ctx()
    if x not in sm.METRICS or y not in sm.METRICS:
        raise HTTPException(422, "Pick two stats")
    sl = await scouting_api.shortlisted(c["id"])
    pts = [o for o in data["players"] if o["minutes"] >= sm.MIN_PCT and o["p90"].get(x) is not None and o["p90"].get(y) is not None and (not group or o["group"] == group)]
    if not pts:
        return {"points": [], "count": 0, "target": 0, "mx": None, "my": None, "ranked": []}
    mx, my = sorted(o["p90"][x] for o in pts)[len(pts) // 2], sorted(o["p90"][y] for o in pts)[len(pts) // 2]
    out = []
    for o in pts:
        kind = "own" if o["own"] else "shortlist" if o["unique_id"] in sl else "target" if o["p90"][x] > mx and o["p90"][y] > my else "pool"
        out.append({"unique_id": o["unique_id"], "name": o["name"], "club": o["club"], "x": o["p90"][x], "y": o["p90"][y], "kind": kind})
    role = role if role in roles.ROLES else None
    ranked = sorted((card(o, data, role, view) for o in pts if not o["own"]), key=lambda r: -(r["score"] or 0))[:15] if role else []
    return {"points": out, "count": len(out), "target": sum(p["kind"] == "target" for p in out), "mx": mx, "my": my, "ranked": ranked,
            "labels": {x: sm.METRICS[x][0], y: sm.METRICS[y][0]}}


# ---------- shortlist board ----------
class SlotIn(BaseModel):
    slot: str = Field(max_length=10)


@router.get("/board")
async def board(formation: str = "433", view: View = "full"):
    import scouting_api
    c, data = await _ctx()
    if formation not in roles.FORMATIONS:
        raise HTTPException(404, "Unknown formation")
    slots = roles.formation_meta(formation)["slots"]
    sl = await scouting_api.shortlisted(c["id"])
    st = await stages(c["id"])
    moved_pipe = [{"$match": {"career_id": c["id"], "formation": formation}}, {"$sort": {"at": -1}}, {"$group": {"_id": "$unique_id", "slot": {"$first": "$slot"}}}]
    moved = {d["_id"]: d["slot"] async for d in db.board_slots.aggregate(moved_pipe)}
    cols = [{"slot": s["key"], "label": s["label"], "role": s["role"], "role_name": s["role_name"], "starter": starter_for(data, s["role"]), "players": []} for s in slots]
    by = {col["slot"]: col for col in cols}
    for uid in sl:
        x = data["by_uid"].get(uid)
        if not x:
            continue
        key = moved.get(uid) if moved.get(uid) in by else max(cols, key=lambda col: (bool(set(x.get("positions") or []) & set(next(s["positions"] for s in slots if s["key"] == col["slot"]))),
                                                                                     role_score(x, col["role"]) or 0))["slot"]
        col = by[key]
        col["players"].append(card(x, data, col["role"], view, (col["starter"] or {}).get("score")) | {"stage": st.get(uid, "Watching")})
    for col in cols:
        col["players"].sort(key=lambda p: -(p["score"] or 0))
    return {"formation": formation, "columns": cols}


@router.put("/board/{uid}")
async def move(uid: int, body: SlotIn, formation: str = "433"):
    c = await active_career()
    if body.slot not in {s["key"] for s in roles.formation_meta(formation)["slots"]}:
        raise HTTPException(422, "Unknown slot")
    await db.board_slots.insert_one({"id": new_id(), "career_id": c["id"], "unique_id": uid, "formation": formation, "slot": body.slot, "at": now_iso()})
    return {"ok": True}


# ---------- DOF picks ----------
class PicksIn(BaseModel):
    role: str = Field(max_length=10)
    budget: int = Field(ge=0)
    max_wage: int = Field(ge=0)
    skip_refuse: bool = True
    skip_against: bool = True
    include_not_for_sale: bool = False
    view: View = "full"


def refuse_likely(x: dict, data: dict) -> bool:
    return (x.get("league_mult") or 1) - data["_ours"] > .05 and x["minutes"] >= data["_season_min"] * .7


async def picks_for(data: dict, b: PicksIn) -> dict:
    if b.role not in roles.ROLES:
        raise HTTPException(422, "Pick a role")
    starter = starter_for(data, b.role)
    base = (starter or {}).get("score") or 0
    pos_group = GROUP[roles.ROLE_POSITIONS[b.role][0]]
    pool, left = [], []
    for x in data["players"]:
        if x["own"] or x["gender"] != "M" or x["group"] != pos_group or x["minutes"] < sm.MIN_PCT:
            continue
        s = role_score(x, b.role)
        if s is None:
            continue
        why = ("over budget" if (x["value"] or 0) > b.budget else "wage too high" if (x["wage"] or 0) > b.max_wage
               else "not for sale" if x.get("not_for_sale") and not b.include_not_for_sale
               else "likely to refuse" if b.skip_refuse and refuse_likely(x, data)
               else "against your philosophy" if b.skip_against and (philosophy(x, data["_phil"]) or 50) < 35 else None)
        (left if why else pool).append((x, s, why))
    used = set()

    def take(rows, n=2):
        out = []
        for x, s, _ in rows:
            if x["unique_id"] not in used and len(out) < n:
                used.add(x["unique_id"])
                out.append(x)
        return out
    cols = {
        "Dream": take(sorted((r for r in pool if (r[0]["league_mult"] or 1) > data["_ours"]), key=lambda r: -r[1])),
        "Upgrade": take(sorted((r for r in pool if r[1] - base >= 10 and 22 <= r[0]["age"] <= 29 and (r[0]["value"] or 0) <= b.budget / 2), key=lambda r: -r[1])),
        "Value": take(sorted(pool, key=lambda r: -(r[1] / max(1, (r[0]["value"] or 0) / 1e6)))),
        "Squad player": take(sorted((r for r in pool if abs((r[0]["league_mult"] or 1) - data["_ours"]) <= .05 and r[0]["minutes"] >= 900), key=lambda r: (r[0]["value"] or 0, -r[1]))),
        "Prospect": take(sorted((r for r in pool if r[0]["age"] <= 21), key=lambda r: -r[1])),
    }
    reasons = {"Dream": "Best score in a stronger league within budget", "Upgrade": "Beats your starter by 10+ and is 22-29", "Value": "Most score per £",
               "Squad player": "Proven at your level, cheap cover", "Prospect": "Top for his age group (21 or under)"}

    def tags(x, s):
        t = []
        if b.role not in natural_roles(x):
            t.append(f"Retrain to {roles.ROLES[b.role][0]}")
        if (x["league_mult"] or 1) - data["_ours"] > .08:
            t.append("Big step down for him")
        ph = philosophy(x, data["_phil"])
        if ph is not None:
            t.append(f"Philosophy {ph}")
        if x["months_left"] is not None and x["months_left"] <= 6:
            t.append("Contract expiring")
        elif x["months_left"] is not None and x["months_left"] <= 12:
            t.append("Final year")
        if refuse_likely(x, data):
            t.append("Might refuse (estimate)")
        return t
    out = {k: [card(x, data, b.role, b.view, base) | {"reason": reasons[k], "tags": tags(x, role_score(x, b.role))} for x in v] for k, v in cols.items()}
    strong = sorted(left, key=lambda r: -r[1])[:3]
    return {"role": b.role, "role_name": roles.ROLES[b.role][0], "starter": starter, "columns": out,
            "left_out": [{"name": x["name"], "score": s, "why": why} for x, s, why in strong]}


@router.post("/picks")
async def picks(body: PicksIn):
    _, data = await _ctx()
    return await picks_for(data, body)
