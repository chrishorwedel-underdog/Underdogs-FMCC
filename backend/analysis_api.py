"""Stats Table, Role Fit, Player Dossier, Transfer Market and Club Analysis: FMCC's own scouting and recruitment screens,
built from the save FMCC already reads. Never exposes real CA/PA. Estimated values are FMCC's own (fitted to the save's values)."""
import math
from datetime import date
from typing import Optional

from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel

import stats_model as sm
from core import db, active_career, latest_two
from editor_api import LIVE
from features_api import need
from sample_reader import GROUP

router = APIRouter(prefix="/api/analysis")
HIDDEN = {"ca", "pa", "ability", "potential"}
POS_GROUP = {"GK": "GK", "CB": "CB", "FB": "FB", "DM": "DM", "CM": "CM", "AM": "AM", "W": "W", "ST": "ST"}
G = lambda p: GROUP.get((p.get("positions") or ["M (C)"])[0], "CM")  # noqa: E731

# FM role: name, positions it's played in, attributes with the ball, attributes without the ball
ROLES = {
    "gk": ("Goalkeeper", ["GK"], ["kicking", "passing", "composure"], ["handling", "reflexes", "aerial_reach", "command_of_area", "positioning", "one_on_ones"]),
    "sk": ("Sweeper Keeper", ["GK"], ["kicking", "passing", "first_touch", "composure", "vision"], ["reflexes", "one_on_ones", "command_of_area", "acceleration", "anticipation"]),
    "cd": ("Central Defender", ["D (C)"], ["passing", "composure"], ["tackling", "marking", "heading", "positioning", "strength", "jumping_reach", "anticipation"]),
    "bpd": ("Ball-Playing Defender", ["D (C)"], ["passing", "vision", "first_touch", "technique", "composure"], ["tackling", "marking", "heading", "positioning", "anticipation"]),
    "ncb": ("No-Nonsense Centre-Back", ["D (C)"], ["strength"], ["tackling", "marking", "heading", "positioning", "jumping_reach", "strength"]),
    "lib": ("Libero", ["D (C)"], ["passing", "first_touch", "dribbling", "vision", "technique", "composure"], ["tackling", "marking", "positioning", "anticipation", "decisions"]),
    "wcb": ("Wide Centre-Back", ["D (C)"], ["crossing", "dribbling", "passing", "stamina"], ["tackling", "marking", "positioning", "pace", "heading"]),
    "fb": ("Full-Back", ["D (L)", "D (R)"], ["crossing", "passing", "stamina"], ["tackling", "marking", "positioning", "anticipation", "work_rate"]),
    "wb": ("Wing-Back", ["D (L)", "D (R)", "WB (L)", "WB (R)"], ["crossing", "dribbling", "passing", "off_the_ball", "stamina", "acceleration"], ["tackling", "marking", "work_rate", "pace", "positioning"]),
    "cwb": ("Complete Wing-Back", ["WB (L)", "WB (R)"], ["crossing", "dribbling", "technique", "flair", "off_the_ball", "stamina", "acceleration"], ["work_rate", "tackling", "pace"]),
    "ifb": ("Inverted Full-Back", ["D (L)", "D (R)"], ["passing", "first_touch", "composure", "decisions"], ["tackling", "marking", "positioning", "anticipation", "strength"]),
    "iwb": ("Inverted Wing-Back", ["D (L)", "D (R)", "WB (L)", "WB (R)"], ["passing", "first_touch", "technique", "vision", "decisions", "composure"], ["tackling", "positioning", "work_rate", "stamina"]),
    "dm": ("Defensive Midfielder", ["DM"], ["passing", "composure"], ["tackling", "positioning", "anticipation", "work_rate", "decisions", "marking"]),
    "anc": ("Anchor", ["DM"], ["passing", "composure"], ["tackling", "marking", "positioning", "anticipation", "decisions", "strength"]),
    "bwm": ("Ball-Winning Midfielder", ["DM", "M (C)"], ["passing"], ["tackling", "work_rate", "stamina", "anticipation", "strength", "pace", "decisions"]),
    "dlp": ("Deep-Lying Playmaker", ["DM", "M (C)"], ["passing", "first_touch", "technique", "vision", "composure", "decisions"], ["positioning", "anticipation", "tackling"]),
    "reg": ("Regista", ["DM"], ["passing", "first_touch", "technique", "vision", "flair", "composure", "decisions", "off_the_ball"], ["anticipation"]),
    "rp": ("Roaming Playmaker", ["DM", "M (C)"], ["passing", "first_touch", "technique", "vision", "dribbling", "off_the_ball", "decisions"], ["work_rate", "stamina", "anticipation"]),
    "hb": ("Half-Back", ["DM"], ["passing", "composure"], ["tackling", "marking", "positioning", "anticipation", "decisions", "strength", "jumping_reach"]),
    "cm": ("Central Midfielder", ["M (C)"], ["passing", "first_touch", "technique", "decisions"], ["tackling", "work_rate", "stamina", "positioning"]),
    "bbm": ("Box-to-Box Midfielder", ["M (C)"], ["passing", "off_the_ball", "finishing", "first_touch", "stamina"], ["tackling", "work_rate", "stamina", "anticipation"]),
    "mez": ("Mezzala", ["M (C)"], ["passing", "dribbling", "technique", "off_the_ball", "vision", "flair", "acceleration"], ["work_rate", "decisions"]),
    "car": ("Carrilero", ["M (C)"], ["passing", "first_touch", "decisions"], ["tackling", "positioning", "work_rate", "stamina", "anticipation"]),
    "ap": ("Advanced Playmaker", ["M (C)", "AM (C)", "AM (L)", "AM (R)"], ["passing", "first_touch", "technique", "vision", "flair", "composure", "decisions"], ["work_rate"]),
    "am": ("Attacking Midfielder", ["AM (C)"], ["first_touch", "dribbling", "passing", "technique", "off_the_ball", "flair", "finishing"], ["work_rate"]),
    "ss": ("Shadow Striker", ["AM (C)"], ["finishing", "first_touch", "dribbling", "off_the_ball", "composure", "acceleration"], ["work_rate", "anticipation"]),
    "en": ("Enganche", ["AM (C)"], ["passing", "first_touch", "technique", "vision", "composure", "flair"], []),
    "w": ("Winger", ["M (L)", "M (R)", "AM (L)", "AM (R)"], ["crossing", "dribbling", "technique", "pace", "acceleration", "flair"], ["work_rate", "stamina"]),
    "if": ("Inside Forward", ["AM (L)", "AM (R)"], ["finishing", "dribbling", "first_touch", "technique", "off_the_ball", "acceleration", "composure"], ["work_rate"]),
    "iw": ("Inverted Winger", ["M (L)", "M (R)", "AM (L)", "AM (R)"], ["crossing", "dribbling", "passing", "technique", "vision", "acceleration"], ["work_rate"]),
    "wp": ("Wide Playmaker", ["M (L)", "M (R)", "AM (L)", "AM (R)"], ["passing", "first_touch", "technique", "vision", "dribbling", "decisions"], ["work_rate"]),
    "dw": ("Defensive Winger", ["M (L)", "M (R)"], ["crossing", "technique"], ["tackling", "work_rate", "stamina", "positioning", "anticipation"]),
    "raum": ("Raumdeuter", ["AM (L)", "AM (R)"], ["finishing", "off_the_ball", "composure", "first_touch", "acceleration"], ["anticipation", "decisions"]),
    "af": ("Advanced Forward", ["ST"], ["finishing", "first_touch", "dribbling", "technique", "off_the_ball", "composure", "acceleration"], ["work_rate"]),
    "pf": ("Pressing Forward", ["ST"], ["finishing", "first_touch", "off_the_ball", "composure"], ["work_rate", "stamina", "pace", "acceleration", "anticipation", "decisions"]),
    "p": ("Poacher", ["ST"], ["finishing", "off_the_ball", "composure", "first_touch", "anticipation"], []),
    "tf": ("Target Forward", ["ST"], ["heading", "strength", "jumping_reach", "finishing", "first_touch", "composure"], ["work_rate"]),
    "dlf": ("Deep-Lying Forward", ["ST"], ["passing", "first_touch", "technique", "vision", "composure", "off_the_ball", "finishing"], ["work_rate"]),
    "f9": ("False Nine", ["ST"], ["passing", "first_touch", "dribbling", "technique", "vision", "flair", "off_the_ball"], ["work_rate"]),
    "cf": ("Complete Forward", ["ST"], ["finishing", "first_touch", "heading", "dribbling", "passing", "technique", "off_the_ball", "composure"], ["work_rate", "strength"]),
}


async def _weights(cid: str) -> dict:
    d = await db.role_weights.find_one({"career_id": cid}, {"_id": 0}) or {}
    return d.get("roles") or {}


def fit(p: dict, key: str, w: dict) -> tuple:
    a = p.get("attributes") or {}
    _, _, inb, outb = ROLES[key]
    ww = w.get(key) or {}
    def pct(attrs):
        if not attrs:
            return None
        tot = sum(ww.get(x, 1) for x in attrs) or 1
        return round(sum(a.get(x, 10) * ww.get(x, 1) for x in attrs) / tot * 5)
    i, o = pct(inb), pct(outb)
    both = [x for x in (i, o) if x is not None]
    return i, o, round(sum(both) / len(both)) if both else 0


def fits(p: dict, w: dict, natural_only=False) -> list:
    pos = set(p.get("positions") or [])
    out = []
    for k, (name, roles_pos, _, _) in ROLES.items():
        nat = bool(pos & set(roles_pos))
        if natural_only and not nat:
            continue
        i, o, f = fit(p, k, w)
        out.append({"role": k, "name": name, "with_ball": i, "without_ball": o, "fit": f, "natural": nat})
    return sorted(out, key=lambda r: (not r["natural"], -r["fit"]))


def _years_left(p: dict, gd: date) -> Optional[float]:
    try:
        return (date.fromisoformat(p["contract_end"][:10]) - gd).days / 365
    except Exception:
        return None


def _model(rows: list) -> tuple:
    """log(value) against best natural role fit, fitted to the save's own values."""
    pts = [(r["_q"], math.log(r["value"])) for r in rows if r.get("value") and r["value"] > 0]
    if len(pts) < 5:
        return 9.0, 0.09, 1e4, 1e8
    lo, hi = math.exp(min(y for _, y in pts)), math.exp(max(y for _, y in pts))
    mx, my = sum(x for x, _ in pts) / len(pts), sum(y for _, y in pts) / len(pts)
    var = sum((x - mx) ** 2 for x, _ in pts) or 1
    b = sum((x - mx) * (y - my) for x, y in pts) / var
    return my - b * mx, b, lo, hi


def estimate(r: dict, model: tuple, league_q: dict, avg_q: float, gd: date) -> dict:
    age, yl, g = r.get("age") or 25, _years_left(r, gd), G(r)
    f = {"Age": 0.3 if age <= 20 else 0.12 if age <= 23 else 0 if age <= 28 else -0.15 if age <= 30 else -0.35,
         "Position": {"ST": .1, "AM": .08, "W": .05, "GK": -.2}.get(g, 0),
         "Club": max(-.25, min(.25, (league_q.get(r.get("league"), avg_q) - avg_q) / 25)),
         "Reputation": .1 if (r.get("appearances") or 0) >= 10 else -.1 if (r.get("appearances") or 0) < 3 else 0,
         "Contract": -.35 if yl is not None and yl < 1 else -.15 if yl is not None and yl < 2 else .1 if yl is not None and yl > 3 else 0,
         "Form": max(-.2, min(.2, ((r.get("avg_rating") or 6.8) - 6.8) * .25)) if r.get("appearances") else 0}
    base = min(model[3] * 1.2, max(model[2] * 0.5, math.exp(model[0] + model[1] * r["_q"])))
    if r.get("value"):
        base = math.sqrt(base * r["value"])
    v = base
    for x in f.values():
        v *= 1 + x
    step = 10 ** max(3, int(math.log10(max(v, 1))) - 1)
    return {"value": int(round(v / step) * step), "factors": [{"name": k, "pct": round(x * 100)} for k, x in f.items()]}


async def _world(c: dict) -> tuple:
    snaps = await latest_two(c["id"])
    if not snaps:
        raise HTTPException(404, "No save read yet")
    gd = date.fromisoformat(snaps[0]["game_date"][:10])
    pool = (await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}) or {}).get("players") or []
    own = [p | {"club": c["club_name"], "league": p.get("league") or "Your league", "own": True, "gender": p.get("gender", "M")} for p in snaps[0]["players"]]
    seen, rows = set(), []
    w = await _weights(c["id"])
    for p in own + pool:
        if p["unique_id"] in seen:
            continue
        seen.add(p["unique_id"])
        best = fits(p, w, natural_only=True)[:3] or fits(p, w)[:1]
        r = {k: v for k, v in p.items() if k not in HIDDEN and k != "attributes"} | {"attributes": p.get("attributes") or {}, "group": G(p), "own": bool(p.get("own"))}
        r["_q"] = best[0]["fit"] if best else 0
        r["top_roles"] = best
        r["p90"] = p.get("stats") or (sm.sample_stats(p) if not LIVE else None) or {}
        rows.append(r)
    league_q, by = {}, {}
    for r in rows:
        by.setdefault(r.get("league"), []).append(r["_q"])
    league_q = {k: sum(v) / len(v) for k, v in by.items()}
    avg_q = sum(r["_q"] for r in rows) / max(1, len(rows))
    model = _model(rows)
    for r in rows:
        e = estimate(r, model, league_q, avg_q, gd)
        r["est_value"], r["value_factors"], r["years_left"] = e["value"], e["factors"], _years_left(r, gd)
        r["role_fit"] = r.pop("_q")
    return rows, gd, snaps


def _public(r: dict) -> dict:
    return {k: v for k, v in r.items() if k not in HIDDEN}


@router.get("/meta", dependencies=need("scouting"))
async def meta():
    groups = {"General": [["age", "Age"], ["minutes", "Minutes"], ["appearances", "Apps"], ["avg_rating", "Avg rating"], ["goals", "Goals"], ["assists", "Assists"],
                          ["est_value", "Est. value"], ["wage", "Wage"], ["years_left", "Contract years left"], ["role_fit", "Best role fit %"]]}
    for k, (label, kind, *_rest) in sm.METRICS.items():
        g = "Goalkeeping" if _rest[-1] else {"att": "Attacking", "def": "Defending", "pct": "Passing"}.get(kind, "Attacking")
        if k in ("passc", "progp", "ppc", "pcmp", "kp", "xa", "chc", "acr", "crc", "xakp", "xakq", "plost", "epl"):
            g = "Passing"
        groups.setdefault(g, []).append([f"p90.{k}", label])
    from roles import GK_ATTRS, OUTFIELD_ATTRS, SHARED_ATTRS
    groups["Attributes"] = [[f"attributes.{a}", a.replace("_", " ").title()] for a in OUTFIELD_ATTRS + SHARED_ATTRS + GK_ATTRS]
    groups["Physical"] = [[f"attributes.{a}", a.replace("_", " ").title()] for a in ("pace", "acceleration", "stamina", "strength", "jumping_reach")] + [["p90.spr", "Sprints / 90"]]
    return {"groups": groups, "roles": [{"key": k, "name": v[0], "positions": v[1], "with_ball": v[2], "without_ball": v[3]} for k, v in ROLES.items()],
            "sample": not LIVE}


@router.get("/table", dependencies=need("scouting"))
async def table():
    c = await active_career()
    rows, gd, _ = await _world(c)
    return {"game_date": gd.isoformat(), "rows": [_public(r) for r in rows], "sample": not LIVE}


@router.get("/player/{uid}")
async def dossier(uid: int):
    c = await active_career()
    rows, gd, snaps = await _world(c)
    r = next((x for x in rows if x["unique_id"] == uid), None)
    if not r:
        raise HTTPException(404, "Player not found in the save")
    w = await _weights(c["id"])
    hist = []
    async for m in db.world_months.find({"career_id": c["id"]}, {"_id": 0, "month": 1, "players": {"$elemMatch": {"unique_id": uid}}}).sort("month", 1):
        if m.get("players") and m["players"][0].get("value") is not None:
            hist.append({"month": m["month"], "value": m["players"][0]["value"], "club": m["players"][0].get("club")})
    for s in sorted(await db.snapshots.find({"career_id": c["id"], "players.unique_id": uid}, {"_id": 0, "game_date": 1, "players.$": 1}).to_list(50), key=lambda s: s["game_date"]):
        hist.append({"month": s["game_date"][:7], "value": s["players"][0].get("value"), "club": c["club_name"]}) if s["players"][0].get("value") else None
    return _public(r) | {"roles": fits(r, w), "value_history": hist, "game_date": gd.isoformat()}


@router.get("/similar/{uid}")
async def similar(uid: int, kind: str = Query("similar", pattern="^(similar|cheaper|younger)$")):
    c = await active_career()
    rows, _, _ = await _world(c)
    r = next((x for x in rows if x["unique_id"] == uid), None)
    if not r:
        raise HTTPException(404, "Player not found in the save")
    a = r["attributes"]
    def dist(x):
        b = x["attributes"]
        return math.sqrt(sum((a.get(k, 10) - b.get(k, 10)) ** 2 for k in a)) + 3 * (x["group"] != r["group"])
    cands = [x for x in rows if x["unique_id"] != uid and x["group"] == r["group"] and x.get("gender") == r.get("gender")]
    if kind == "cheaper":
        cands = [x for x in cands if x["est_value"] <= 0.6 * r["est_value"]]
    elif kind == "younger":
        cands = [x for x in cands if (x.get("age") or 99) < (r.get("age") or 0)]
    return [_public(x) | {"similarity": max(0, round(100 - dist(x) * 2.2))} for x in sorted(cands, key=dist)[:10]]


class WeightsIn(BaseModel):
    weights: dict[str, float]


@router.put("/roles/{key}")
async def set_weights(key: str, body: WeightsIn):
    if key not in ROLES:
        raise HTTPException(404, "Unknown role")
    ok = set(ROLES[key][2]) | set(ROLES[key][3])
    if any(k not in ok or not 0 <= v <= 5 for k, v in body.weights.items()):
        raise HTTPException(422, "Weights are 0 to 5, for the role's own attributes")
    c = await active_career()
    await db.role_weights.update_one({"career_id": c["id"]}, {"$set": {f"roles.{key}": body.weights}}, upsert=True)
    return {"ok": True}


@router.delete("/roles/{key}")
async def reset_weights(key: str):
    c = await active_career()
    await db.role_weights.update_one({"career_id": c["id"]}, {"$unset": {f"roles.{key}": ""}})
    return {"ok": True}


@router.get("/roles")
async def get_weights():
    return await _weights((await active_career())["id"])


def _row(r: dict, why: str = "") -> dict:
    keys = ("unique_id", "name", "age", "club", "league", "nationality", "positions", "group", "est_value", "wage", "contract_end", "years_left", "role_fit", "top_roles", "gender", "own", "last_move")
    return {k: r.get(k) for k in keys} | ({"why": why} if why else {})


@router.get("/market", dependencies=need("market"))
async def market():
    c = await active_career()
    rows, gd, _ = await _world(c)
    rows = [r for r in rows if not r["own"]]
    free = [r for r in rows if (r.get("club") or "Free agent") in ("Free agent", "", "Unattached")]
    expiring = sorted([r for r in rows if r["years_left"] is not None and r["years_left"] <= 1 and r not in free], key=lambda r: -r["est_value"])
    clauses = sorted([r for r in rows if r.get("release_clause")], key=lambda r: r["release_clause"])
    u21 = sorted([r for r in rows if (r.get("age") or 99) <= 21], key=lambda r: -r["est_value"])
    loans = [r for r in rows if r.get("loan_listed")]
    months = await db.world_months.find({"career_id": c["id"]}, {"_id": 0, "month": 1, "players.unique_id": 1, "players.club": 1, "players.value": 1, "players.name": 1, "players.league": 1}).sort("month", -1).limit(2).to_list(2)
    changes = []
    if len(months) == 2:
        old = {p["unique_id"]: p for p in months[1]["players"]}
        for p in months[0]["players"]:
            o = old.get(p["unique_id"])
            if not o:
                continue
            if o.get("club") != p.get("club"):
                changes.append({"kind": "move", "unique_id": p["unique_id"], "name": p["name"], "league": p.get("league"), "text": f"{o.get('club') or 'Free agent'} → {p.get('club') or 'Free agent'}"})
            elif o.get("value") and p.get("value") and abs(p["value"] - o["value"]) / o["value"] >= 0.15:
                changes.append({"kind": "value", "unique_id": p["unique_id"], "name": p["name"], "league": p.get("league"), "text": f"Value {'up' if p['value'] > o['value'] else 'down'} {round(abs(p['value'] - o['value']) / o['value'] * 100)}%"})
    return {"game_date": gd.isoformat(), "since": months[1]["month"] if len(months) == 2 else None, "my_league": next((r.get("league") for r in rows if r.get("club") == c["club_name"]), None),
            "lists": {"expiring": [_row(r) for r in expiring[:50]], "free": [_row(r) for r in sorted(free, key=lambda r: -r["est_value"])[:50]],
                      "clauses": [_row(r) | {"release_clause": r["release_clause"]} for r in clauses[:50]], "u21": [_row(r) for r in u21[:50]], "loans": [_row(r) for r in loans[:50]]},
            "notes": {"clauses": None if clauses else "This save doesn't show release clauses yet", "loans": None if loans else "This save doesn't show loan-listed players yet"},
            "changes": changes[:200], "rankings": [_row(r) for r in sorted(rows, key=lambda r: -r["est_value"])[:300]], "sample": not LIVE}


@router.get("/club", dependencies=need("club"))
async def club():
    c = await active_career()
    rows, gd, snaps = await _world(c)
    own = [r for r in rows if r["own"]]
    others = [r for r in rows if not r["own"] and r.get("gender") == (own[0].get("gender") if own else "M")]
    order = ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"]
    names = {"GK": "goalkeeper", "CB": "centre-back", "FB": "full-back", "DM": "defensive midfield", "CM": "central midfield", "AM": "attacking midfield", "W": "wing", "ST": "striker"}
    need_n = {"GK": 2, "CB": 3, "FB": 3, "DM": 2, "CM": 3, "AM": 1, "W": 2, "ST": 2}
    pos = {}
    for g in order:
        ps = sorted([r for r in own if r["group"] == g], key=lambda r: -r["role_fit"])
        pos[g] = {"group": g, "label": names[g], "count": len(ps), "best": ps[0]["role_fit"] if ps else 0, "avg_top2": round(sum(r["role_fit"] for r in ps[:2]) / 2) if ps else 0,
                  "avg_age": round(sum(r.get("age") or 0 for r in ps) / len(ps), 1) if ps else None, "players": [r["name"] for r in ps]}
    todo = []
    for g in order:
        p = pos[g]
        if p["count"] < need_n[g]:
            todo.append({"score": 90 - p["count"] * 15, "title": f"Not enough cover at {p['label']}", "evidence": f"{p['count']} player(s): {', '.join(p['players']) or 'nobody'}. A squad usually wants {need_n[g]}.",
                         "link": f"/scouting?tab=stats&group={g}"})
        if p["avg_age"] and p["avg_age"] >= 30:
            todo.append({"score": 55, "title": f"Ageing {p['label']} group", "evidence": f"Average age {p['avg_age']}.", "link": f"/scouting?tab=stats&group={g}&maxage=23"})
    starters = sorted(own, key=lambda r: -(r.get("minutes") or 0))[:11]
    ending = [r for r in starters if r["years_left"] is not None and r["years_left"] <= 1]
    if ending:
        todo.append({"score": 80 + len(ending), "title": f"{len(ending)} starter{'s' if len(ending) > 1 else ''}' contracts end within a year", "evidence": ", ".join(f"{r['name']} ({r['contract_end']})" for r in ending),
                     "link": "/squad"})
    weak = sorted((p for p in pos.values() if p["count"]), key=lambda p: p["avg_top2"])[:3]
    for p in weak:
        todo.append({"score": 60 - weak.index(p) * 5, "title": f"Weakest area: {p['label']}", "evidence": f"Your best two there average a {p['avg_top2']}% role fit, the lowest in your squad.", "link": f"/scouting?tab=stats&group={p['group']}"})
    todo.sort(key=lambda t: -t["score"])
    target = weak[0] if weak else None
    ideas = {}
    if target:
        g, best = target["group"], target["best"]
        own_vals = sorted(r["est_value"] for r in own) or [0]
        budget = own_vals[len(own_vals) // 2] * 1.5
        cand = [r for r in others if r["group"] == g]
        ideas = {"position": target["label"],
                 "upgrade": [_row(r, f"{r['role_fit']}% fit vs your best {best}%") for r in sorted([r for r in cand if r["role_fit"] > best], key=lambda r: -r["role_fit"])[:5]],
                 "affordable": [_row(r, f"{r['role_fit']}% fit, about {round(r['est_value'] / max(1, budget) * 100)}% of a typical squad price") for r in sorted([r for r in cand if r["role_fit"] >= best - 3 and r["est_value"] <= budget], key=lambda r: r["est_value"])[:5]],
                 "successor": [_row(r, f"Age {r.get('age')}, already {r['role_fit']}% fit") for r in sorted([r for r in cand if (r.get("age") or 99) <= 21 and r["role_fit"] >= best - 10], key=lambda r: -r["role_fit"])[:5]]}
    return {"game_date": gd.isoformat(), "club": c["club_name"], "todo": todo[:10], "positions": [pos[g] for g in order], "ideas": ideas, "sample": not LIVE}
