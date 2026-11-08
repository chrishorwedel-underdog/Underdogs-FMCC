"""Scout Players: ScoutSheet's views (Full, Fair play, Moneyball), search, profiles, My Club, fair price, Deal Finder, Offers, and the
FMDataLab-style analytics (stats table, percentiles, computed stats, possession adjustment, scatter, breakdown, role scores, HTML import)."""
import csv
import io
import re
import zlib
from html.parser import HTMLParser
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException, Query, UploadFile, File
from fastapi.responses import Response
from pydantic import BaseModel, Field

import lab_api
import roles
import stats_model as sm
from core import db, active_career, now_iso, new_id, audit, next_revision, logger

router = APIRouter(prefix="/api/scout")
View = Literal["full", "fair", "moneyball"]
PRESETS = {"wonderkids": "Wonderkids (21 or under, high potential)", "expiring": "Contracts ending within 12 months",
           "bargains": "Selling well under fair price", "top_grade": "Top graded (global grade 60+)", "young_regulars": "23 or under with 900+ minutes"}
GROUPS = {"GK": "Goalkeeper", "CB": "Centre-back", "FB": "Full-back", "DM": "Defensive midfield", "CM": "Central midfield", "AM": "Attacking midfield", "W": "Winger", "ST": "Striker"}


def mask(x: dict, view: str) -> dict:
    """Fair play shows only what your scouts would; Moneyball switches attributes off completely."""
    o = {k: v for k, v in x.items() if k not in ("z",)}
    if view == "full":
        return o
    for k in ("ca", "pa", "hidden", "personality"):
        o[k] = None
    o["best_role"] = None
    if view == "moneyball":
        o["attributes"] = None
    elif x.get("attributes"):
        spread = round((100 - x["knowledge"]) / 20)
        o["attributes"] = {k: [max(1, v - spread), min(20, v + spread)] for k, v in x["attributes"].items()}
    return o


def _value_of(x: dict, key: str, mode: str = "p90"):
    if key.startswith("f:"):
        return (x.get("f") or {}).get(key[2:])
    if key.startswith("c:"):
        return x["computed"].get(key[2:])
    if key in sm.METRICS:
        v = (x["adj"] if mode == "adjusted" else x["p90"]).get(key)
        if v is None:
            return None
        if mode == "adjusted" and sm.METRICS[key][1] != "pct":
            v = v * x["league_mult"]
        if mode == "total" and sm.METRICS[key][1] != "pct":
            v = v * x["minutes"] / 90
        return round(v, 3)
    return x.get({"grade": "grade_global", "local": "grade_local"}.get(key, key))


def _filter(data: dict, f: dict, view: str) -> list:
    q = (f.get("q") or "").lower().strip()
    out = []
    for x in data["players"]:
        if x["gender"] != f.get("gender", "M") or (f.get("source", "save") != x["source"]):
            continue
        if q and q not in x["name"].lower() and q not in (x["club"] or "").lower():
            continue
        if f.get("group") and x["group"] != f["group"] or f.get("league") and x["league"] != f["league"]:
            continue
        if f.get("max_value") and (x["value"] or 0) > f["max_value"] or f.get("max_wage") and (x["wage"] or 0) > f["max_wage"]:
            continue
        if not (f.get("min_age", 15) <= (x["age"] or 0) <= f.get("max_age", 45)) or x["minutes"] < f.get("min_minutes", 0):
            continue
        p = f.get("preset")
        if p == "wonderkids" and not (x["age"] <= 21 and ((x["pa"] or 0) >= 150 if view == "full" else (x["grade_global"] or 0) >= 52)):
            continue
        if p == "expiring" and not (x["months_left"] is not None and x["months_left"] <= 12):
            continue
        if p == "bargains" and not (x["fair_price"] and x["value"] and x["value"] < .8 * x["fair_price"] and not x["own"]):
            continue
        if p == "top_grade" and not (x["grade_global"] or 0) >= 60:
            continue
        if p == "young_regulars" and not (x["age"] <= 23 and x["minutes"] >= 900):
            continue
        if f.get("adv") and not lab_api.match(x, f["adv"], data):
            continue
        out.append(x)
    key, desc = f.get("sort", "grade"), f.get("dir", "desc") == "desc"
    if view != "full" and key in ("ca", "pa"):
        key = "grade"
    out.sort(key=lambda x: (_value_of(x, key, f.get("mode", "p90")) is None, -(_value_of(x, key, f.get("mode", "p90")) or 0) if desc else (_value_of(x, key, f.get("mode", "p90")) or 0)))
    return out


def _row(x: dict, view: str, mode: str) -> dict:
    m = mask(x, view)
    return {k: m.get(k) for k in ("unique_id", "name", "age", "nationality", "club", "league", "positions", "group", "cohort", "ca", "pa", "value", "wage", "minutes",
                                  "own", "source", "months_left", "contract_end", "grade_global", "grade_local", "fair_price", "confidence", "best_role",
                                  "poss_mult", "league_mult", "league_scored", "league_note", "computed", "phases", "actions", "linked", "f")} | {
        "stats": {k: _value_of(x, k, mode) for k in sm.METRICS if x["p90"].get(k) is not None}, "pct": x["pct"]}


class Filters(BaseModel):
    view: View = "full"
    mode: Literal["total", "p90", "adjusted"] = "p90"
    gender: Literal["M", "F"] = "M"
    source: Literal["save", "html"] = "save"
    q: str = Field(default="", max_length=60)
    group: Optional[str] = Field(default=None, pattern="^(GK|CB|FB|DM|CM|AM|W|ST)$")
    league: Optional[str] = Field(default=None, max_length=80)
    preset: Optional[str] = Field(default=None, pattern="^(wonderkids|expiring|bargains|top_grade|young_regulars)$")
    max_value: Optional[int] = Field(default=None, ge=0)
    max_wage: Optional[int] = Field(default=None, ge=0)
    min_age: int = Field(default=15, ge=14, le=45)
    max_age: int = Field(default=45, ge=14, le=50)
    min_minutes: int = Field(default=0, ge=0)
    sort: str = Field(default="grade", max_length=30)
    dir: Literal["asc", "desc"] = "desc"
    limit: int = Field(default=100, ge=1, le=500)
    adv: Optional[dict] = None


async def _data():
    c = await active_career()
    data = await sm.build(c)
    if not data["players"]:
        raise HTTPException(404, "No scouting data yet. Read a save first.")
    await _record_seasons(c, data)
    await lab_api.attach(c, data)
    return c, data


async def _record_seasons(c: dict, data: dict):
    """Keeps each season's numbers for the career, because FM itself deletes old seasons' stats."""
    if not data.get("season") or data.get("recorded") == data["season"]:
        return
    from pymongo import UpdateOne
    ops = [UpdateOne({"career_id": c["id"], "unique_id": x["unique_id"], "season": data["season"]},
                     {"$set": {"club": x["club"], "league": x["league"], "minutes": x["minutes"], "grade": x["grade_global"], "p90": x["p90"], "value": x["value"],
                               "at": now_iso()}}, upsert=True) for x in data["players"] if x["source"] == "save" and x["minutes"]]
    if ops:
        await db.stat_history.bulk_write(ops)
    data["recorded"] = data["season"]


@router.get("/meta")
async def meta():
    _, data = await _data()
    return {"metrics": [{"key": k, "label": v[0], "kind": v[1]} for k, v in sm.METRICS.items()], "presets": PRESETS, "groups": GROUPS,
            "leagues": sorted({x["league"] for x in data["players"] if x["league"]}), "roles": [{"key": k, "name": f"{v[0]} ({v[1]})"} for k, v in roles.ROLES.items()],
            "archetypes": [{"key": a["key"], "name": a["name"]} for a in data["archetypes"].values()], "game_date": data["game_date"],
            "formulas": [{"key": k, "name": v["name"]} for k, v in (data.get("formulas") or {}).items()],
            "min_minutes": {"percentiles": sm.MIN_PCT, "fair_price": sm.MIN_PRICE}, "sample": not sm.LIVE,
            "html_imports": await db.html_imports.count_documents({"status": "active"})}


@router.post("/players")
async def players(f: Filters):
    _, data = await _data()
    rows = _filter(data, f.model_dump(), f.view)
    return {"total": len(rows), "rows": [_row(x, f.view, f.mode) for x in rows[:f.limit]]}


@router.post("/export")
async def export(f: Filters):
    _, data = await _data()
    rows = _filter(data, f.model_dump(), f.view)
    buf = io.StringIO()
    w = csv.writer(buf)
    keys = [k for k in sm.METRICS]
    hide = f.view != "full"
    w.writerow(["Name", "Age", "Club", "League", "Positions"] + ([] if hide else ["CA", "PA"]) + ["Value", "Wage", "Minutes", "Global grade", "Fair price"] + [sm.METRICS[k][0] for k in keys])
    for x in rows:
        w.writerow([x["name"], x["age"], x["club"], x["league"], ", ".join(x["positions"] or [])] + ([] if hide else [x["ca"], x["pa"]])
                   + [x["value"], x["wage"], x["minutes"], x["grade_global"], x["fair_price"]] + [_value_of(x, k, f.mode) for k in keys])
    return Response(buf.getvalue(), media_type="text/csv", headers={"Content-Disposition": 'attachment; filename="fmcc-scouting.csv"'})


def _report(x: dict) -> str:
    pct = sorted(((v, sm.METRICS[k][0]) for k, v in x["pct"].items()), reverse=True)
    if not pct:
        return f"{x['name']} hasn't played enough ({x['minutes']} minutes) for a report. FMCC needs {sm.MIN_PCT}."
    s = ", ".join(n.lower() for _, n in pct[:3])
    w = ", ".join(n.lower() for _, n in pct[-2:])
    gap = (x["pa"] or 0) - (x["ca"] or 0)
    out = f"{x['name']} ({x['age']}, {x['club']}) grades {x['grade_global']} globally as a {x['cohort'].lower()}. Best at {s}; weakest at {w}."
    if x.get("best_role"):
        out += f" Best suited to {x['best_role']}."
    if x.get("personality"):
        out += f" Personality: {x['personality']}."
    if gap >= 25:
        out += f" Plenty of room to grow ({x['ca']} now, {x['pa']} potential)."
    if x["months_left"] is not None and x["months_left"] <= 12:
        out += f" Only {x['months_left']} months left on his contract."
    return out


@router.get("/player/{uid}")
async def profile(uid: int, view: View = "full"):
    c, data = await _data()
    x = data["by_uid"].get(uid)
    if not x:
        raise HTTPException(404, "Player not found")
    seasons = await db.stat_history.find({"career_id": c["id"], "unique_id": uid}, {"_id": 0, "career_id": 0}).sort("season", 1).to_list(50)
    reports = await db.dof_reports.find({"career_id": c["id"], "unique_id": uid}, {"_id": 0}).sort("at", -1).to_list(5)
    sim = sm.similar(data, x)
    return mask(x, view) | {"similar": sim, "report": _report(x) if view == "full" else None,
                            "role_ratings": roles.role_ratings(x)[:5] if view == "full" and x.get("attributes") else [],
                            "seasons": seasons, "dof_reports": reports, "labels": {k: v[0] for k, v in sm.METRICS.items()},
                            "profile_keys": [sm.LABEL2KEY[m["metric"]] for m in sorted(sm.WEIGHTS.get(x["cohort"], []), key=lambda m: -m["weight"])
                                             if m["metric"] in sm.LABEL2KEY][:12]}


class SearchIn(BaseModel):
    name: str = Field(min_length=1, max_length=60)
    filters: dict


@router.get("/searches")
async def searches():
    c = await active_career()
    rows = await sm.latest_docs("saved_searches", c["id"], "key")
    return [r for r in rows.values() if r.get("status") == "active"]


@router.post("/searches")
async def save_search(body: SearchIn):
    c = await active_career()
    f = Filters(**{k: v for k, v in body.filters.items() if k in Filters.model_fields}).model_dump()
    key = re.sub(r"[^a-z0-9]+", "-", body.name.lower()).strip("-") or new_id()[:8]
    rev = await next_revision("saved_searches", {"career_id": c["id"], "key": key})
    await db.saved_searches.insert_one({"id": new_id(), "career_id": c["id"], "key": key, "name": body.name.strip(), "filters": f, "revision": rev, "status": "active", "at": now_iso()})
    return {"key": key}


@router.delete("/searches/{key}")
async def delete_search(key: str):
    c = await active_career()
    cur = (await sm.latest_docs("saved_searches", c["id"], "key")).get(key)
    if not cur or cur["status"] != "active":
        raise HTTPException(404, "Saved search not found")
    await db.saved_searches.insert_one({k: v for k, v in cur.items() if k not in ("_id",)} | {"id": new_id(), "revision": cur["revision"] + 1, "status": "deleted", "at": now_iso()})
    return {"ok": True}


@router.get("/myclub")
async def my_club(view: View = "full"):
    _, data = await _data()
    out = []
    for g, label in GROUPS.items():
        own = [x for x in data["players"] if x["own"] and x["group"] == g]
        graded = [x for x in own if x["grade_global"] is not None]
        best = max(graded, key=lambda x: x["grade_global"]) if graded else None
        out.append({"group": g, "label": label, "players": len(own), "best": best and {"unique_id": best["unique_id"], "name": best["name"], "grade": best["grade_global"]},
                    "rating": best["grade_global"] if best else 0, "depth": round(sum(x["grade_global"] for x in graded) / len(graded), 1) if graded else 0})
    return sorted(out, key=lambda r: r["rating"])


@router.get("/myclub/{group}")
async def improvers(group: str, view: View = "full", max_value: Optional[int] = Query(None, ge=0)):
    if group not in GROUPS:
        raise HTTPException(404, "Unknown position")
    _, data = await _data()
    own = [x["grade_global"] for x in data["players"] if x["own"] and x["group"] == group and x["grade_global"] is not None]
    bar = max(own) if own else 0
    rows = [x for x in data["players"] if not x["own"] and x["gender"] == "M" and x["group"] == group and (x["grade_global"] or 0) > bar
            and (not max_value or (x["value"] or 0) <= max_value)]
    rows.sort(key=lambda x: -((x["grade_global"] - bar) / max(1, (x["value"] or 1) / 1e6) ** .3))
    return {"bar": bar, "rows": [_row(x, view, "p90") | {"gain": round(x["grade_global"] - bar, 1)} for x in rows[:30]]}


@router.get("/deals")
async def deals(view: View = "full", gender: Literal["M", "F"] = "M"):
    _, data = await _data()
    rows = [x for x in data["players"] if not x["own"] and x["gender"] == gender and x["fair_price"] and x["value"] and x["value"] < .8 * x["fair_price"]]
    rows.sort(key=lambda x: x["value"] / x["fair_price"])
    return [_row(x, view, "p90") | {"discount": round((1 - x["value"] / x["fair_price"]) * 100)} for x in rows[:40]]


class OfferIn(BaseModel):
    unique_id: int
    amount: int = Field(ge=0, le=2_000_000_000)
    direction: Literal["buy", "sell"] = "buy"


@router.post("/offer")
async def offer(body: OfferIn):
    c, data = await _data()
    x = data["by_uid"].get(body.unique_id)
    if not x:
        raise HTTPException(404, "Player not found")
    if not x["fair_price"]:
        return {"verdict": "Not enough minutes", "detail": f"A fair price needs at least {sm.MIN_PRICE} minutes; he has {x['minutes']}.", "fair_price": None, "ratio": None}
    r = body.amount / x["fair_price"]
    if body.direction == "buy":
        verdict = "Good deal" if r <= .9 else "Fair" if r <= 1.1 else "Overpaying" if r <= 1.3 else "Well over fair price"
    else:
        verdict = "Great sale" if r >= 1.2 else "Fair" if r >= .9 else "Under fair price" if r >= .7 else "Well under fair price"
    await audit(c["id"], "offer checked", "scouting", f"{body.direction} {x['name']} for £{body.amount:,}: {verdict}", x["unique_id"], x["name"])
    return {"verdict": verdict, "fair_price": x["fair_price"], "ratio": round(r, 2), "confidence": x["confidence"]}


@router.get("/computed")
async def computed():
    c = await active_career()
    arch = await sm.archetypes(c["id"])
    return {"items": list(arch.values()), "custom_count": sum(1 for a in arch.values() if not a["builtin"]),
            "metrics": [{"key": k, "label": v[0]} for k, v in sm.METRICS.items()]}


class ComputedIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    metrics: dict[str, int]
    phases: dict[str, Literal["in", "out"]] = {}


@router.put("/computed/{key}")
async def save_computed(key: str, body: ComputedIn):
    c = await active_career()
    arch = await sm.archetypes(c["id"])
    if any(m not in sm.METRICS for m in body.metrics) or any(not 0 <= w <= 10 for w in body.metrics.values()):
        raise HTTPException(422, "Each weight goes from 0 to 10, on stats FMCC knows")
    builtin = key in sm.ARCHETYPES
    if not builtin:
        if not re.fullmatch(r"[a-z0-9_-]{2,30}", key):
            raise HTTPException(422, "Bad key")
        if not 3 <= len(body.metrics) <= 12:
            raise HTTPException(422, "A custom computed stat uses 3 to 12 stats")
        if key not in arch and sum(1 for a in arch.values() if not a["builtin"]) >= 6:
            raise HTTPException(409, "You already have 6 custom computed stats")
    elif set(body.metrics) != set(sm.ARCHETYPES[key][1]):
        raise HTTPException(422, "Built-in archetypes keep their stats; change the weights only")
    rev = await next_revision("computed_stats", {"career_id": c["id"], "key": key})
    await db.computed_stats.insert_one({"id": new_id(), "career_id": c["id"], "key": key, "name": body.name.strip(), "metrics": body.metrics,
                                        "phases": body.phases, "revision": rev, "status": "active", "at": now_iso()})
    await audit(c["id"], "computed stat saved", "scouting", f"{body.name}: " + ", ".join(f"{m} {w}" for m, w in body.metrics.items()))
    return {"ok": True, "revision": rev}


@router.delete("/computed/{key}")
async def delete_computed(key: str):
    """Custom stats are removed; built-in archetypes go back to their default weights. Both are kept in history."""
    c = await active_career()
    arch = await sm.archetypes(c["id"])
    if key not in arch:
        raise HTTPException(404, "Computed stat not found")
    rev = await next_revision("computed_stats", {"career_id": c["id"], "key": key})
    doc = {"id": new_id(), "career_id": c["id"], "key": key, "name": arch[key]["name"], "revision": rev, "at": now_iso()}
    if key in sm.ARCHETYPES:
        doc |= {"metrics": arch[key]["defaults"], "phases": arch[key]["phases"], "status": "active"}
    else:
        doc |= {"metrics": arch[key]["metrics"], "status": "deleted"}
    await db.computed_stats.insert_one(doc)
    return {"ok": True}


@router.get("/tactical")
async def tactical(key: str, in_w: int = Query(5, ge=0, le=10), out_w: int = Query(5, ge=0, le=10), view: View = "full",
                   gender: Literal["M", "F"] = "M", group: Optional[str] = None):
    """Tactical archetype search: the archetype's in-possession and out-of-possession parts weighted separately."""
    _, data = await _data()
    a = data["archetypes"].get(key)
    if not a:
        raise HTTPException(404, "Archetype not found")
    ins = {m: w for m, w in a["metrics"].items() if a["phases"].get(m, "in") == "in"}
    outs = {m: w for m, w in a["metrics"].items() if a["phases"].get(m) == "out"}
    rows = []
    for x in data["players"]:
        if not x["pct"] or x["gender"] != gender or (group and x["group"] != group) or (not group and a.get("groups") and x["group"] not in a["groups"]):
            continue
        si, so = sm._score(x, ins) if ins else None, sm._score(x, outs) if outs else None
        parts = [(si, in_w), (so, out_w)]
        tot = sum(w for s, w in parts if s is not None)
        if not tot:
            continue
        rows.append((round(sum(s * w for s, w in parts if s is not None) / tot), si, so, x))
    rows.sort(key=lambda r: -r[0])
    return [_row(x, view, "p90") | {"score": s, "in_score": si, "out_score": so} for s, si, so, x in rows[:50]]


@router.get("/possession")
async def possession():
    c = await active_career()
    _, data = await _data()
    clubs = sorted({x["club"] for x in data["players"] if x["club"] and x["source"] == "save"})
    hist = await sm.latest_docs("possession", c["id"], "club")
    return {"own": c["club_name"], "rows": [{"club": cl, "value": (hist.get(cl) or {}).get("value"), "revision": (hist.get(cl) or {}).get("revision", 0),
                                              "own": cl == c["club_name"]} for cl in sorted(clubs, key=lambda n: n != c["club_name"])],
            "matchlens": "Possession from FMMatchLens matches arrives once FMCC can read its match files; until then, enter it here."}


class PossIn(BaseModel):
    value: Optional[float] = Field(default=None, ge=20, le=80)


@router.put("/possession/{club}")
async def set_possession(club: str, body: PossIn):
    c = await active_career()
    rev = await next_revision("possession", {"career_id": c["id"], "club": club})
    await db.possession.insert_one({"id": new_id(), "career_id": c["id"], "club": club, "value": body.value, "revision": rev, "at": now_iso()})
    await audit(c["id"], "possession", "scouting", f"{club} possession: {body.value if body.value is not None else 'cleared'}")
    return {"ok": True}


@router.get("/scatter")
async def scatter(x: str = Query(..., max_length=30), y: str = Query(..., max_length=30), mode: Literal["total", "p90", "adjusted"] = "p90",
                  gender: Literal["M", "F"] = "M", group: Optional[str] = None, min_minutes: int = Query(sm.MIN_PCT, ge=0)):
    _, data = await _data()
    pts = []
    for p in data["players"]:
        if p["gender"] != gender or (group and p["group"] != group) or p["minutes"] < min_minutes:
            continue
        vx, vy = _value_of(p, x, mode), _value_of(p, y, mode)
        if vx is not None and vy is not None:
            pts.append({"unique_id": p["unique_id"], "name": p["name"], "club": p["club"], "own": p["own"], "x": vx, "y": vy})
    avg = lambda k: round(sum(q[k] for q in pts) / len(pts), 3) if pts else None  # noqa: E731
    return {"points": pts, "avg_x": avg("x"), "avg_y": avg("y")}


@router.get("/breakdown")
async def breakdown(ids: str = Query(..., max_length=200), key: str = Query(..., max_length=30)):
    _, data = await _data()
    a = data["archetypes"].get(key)
    if not a:
        raise HTTPException(404, "Computed stat not found")
    try:
        want = [int(i) for i in ids.split(",") if i][:4]
    except ValueError:
        raise HTTPException(422, "Bad player ids")
    tot = sum(a["metrics"].values()) or 1
    out = []
    for uid in want:
        x = data["by_uid"].get(uid)
        if x:
            out.append({"unique_id": uid, "name": x["name"], "score": x["computed"].get(key),
                        "parts": {sm.METRICS[m][0]: round((x["pct"].get(m) or 0) * w / tot, 1) for m, w in a["metrics"].items()}})
    return {"name": a["name"], "players": out}


@router.get("/roles")
async def role_scores(role: str, gender: Literal["M", "F"] = "M", limit: int = Query(60, le=200)):
    if role not in roles.ROLES:
        raise HTTPException(404, "Unknown role")
    _, data = await _data()
    rows = [(roles.role_rating(x, role), x) for x in data["players"] if x.get("attributes") and x["gender"] == gender]
    rows.sort(key=lambda r: -r[0])
    return [{"unique_id": x["unique_id"], "name": x["name"], "age": x["age"], "club": x["club"], "positions": x["positions"], "rating": r,
             "natural": bool(set(x["positions"] or []) & set(roles.ROLE_POSITIONS[role]))} for r, x in rows[:limit]]


# ---------- FM HTML export import ----------
class _Table(HTMLParser):
    def __init__(self):
        super().__init__()
        self.rows, self.cur, self.cell, self.inside = [], None, None, False

    def handle_starttag(self, tag, attrs):
        if tag == "tr":
            self.cur = []
        elif tag in ("td", "th") and self.cur is not None:
            self.cell = ""

    def handle_endtag(self, tag):
        if tag in ("td", "th") and self.cur is not None and self.cell is not None:
            self.cur.append(self.cell.strip())
            self.cell = None
        elif tag == "tr" and self.cur:
            self.rows.append(self.cur)
            self.cur = None

    def handle_data(self, d):
        if self.cell is not None:
            self.cell += d


def _num(s: str):
    s = (s or "").replace(",", "").replace("£", "").replace("€", "").replace("$", "").strip()
    m = re.match(r"^-?\d+(\.\d+)?", s)
    if not m:
        return None
    v = float(m.group(0))
    return v * 1e6 if s.lower().endswith("m") else v * 1e3 if s.lower().endswith("k") else v


def _positions(s: str) -> list:
    s = (s or "").upper()
    out = []
    for tag, pos in (("GK", "GK"), ("D (C", "D (C)"), ("D (L", "D (L)"), ("D (R", "D (R)"), ("WB", "WB (L)"), ("DM", "DM"), ("M (C", "M (C)"),
                     ("AM (C", "AM (C)"), ("AM (L", "AM (L)"), ("AM (R", "AM (R)"), ("ST", "ST")):
        if tag in s:
            out.append(pos)
    return out or ["M (C)"]


def parse_html(raw: bytes, fname: str) -> list:
    t = _Table()
    t.feed(raw.decode("utf-8", errors="ignore"))
    if len(t.rows) < 2:
        return []
    head = [h.lower() for h in t.rows[0]]
    col = lambda *names: next((head.index(n) for n in names if n in head), None)  # noqa: E731
    ci = {k: col(*v) for k, v in {"name": ("name", "player"), "uid": ("uid", "unique id"), "club": ("club", "team"), "age": ("age",), "pos": ("position", "pos", "best pos"),
                                  "nat": ("nat", "nationality"), "mins": ("mins", "minutes"), "gls": ("gls", "goals"), "ast": ("ast", "assists"), "xg": ("xg",),
                                  "value": ("transfer value", "value", "est. value"), "wage": ("wage",), "league": ("division", "league", "based")}.items()}
    if ci["name"] is None:
        return []
    out = []
    for r in t.rows[1:]:
        g = lambda k: r[ci[k]] if ci[k] is not None and ci[k] < len(r) else ""  # noqa: E731
        if not g("name"):
            continue
        uid = _num(g("uid"))
        mins = int(_num(g("mins")) or 0)
        p90 = lambda v: round((v or 0) / mins * 90, 3) if mins else None  # noqa: E731
        stats = {k: p90(_num(g(src))) for k, src in (("gls", "gls"), ("npg", "gls"), ("ast", "ast"), ("npxg", "xg")) if ci[src] is not None} if mins else None
        out.append({"unique_id": int(uid) if uid else -(zlib.crc32(f"{g('name')}|{g('club')}".encode()) % 10_000_000) - 1, "linked": bool(uid),
                    "name": g("name"), "club": g("club") or "Unknown club", "league": g("league") or None, "age": int(_num(g("age")) or 0),
                    "nationality": g("nat"), "positions": _positions(g("pos")), "minutes": mins, "appearances": 0, "value": int(_num(g("value")) or 0),
                    "wage": int(_num(g("wage")) or 0), "stats": stats or None, "file": fname, "ca": None, "pa": None, "attributes": None})
    return out


@router.post("/import-html")
async def import_html(files: list[UploadFile] = File(...)):
    """Imports one or more FM HTML exports. Players without a UID column stay 'Not linked' to any save player."""
    c = await active_career()
    if len(files) > 20:
        raise HTTPException(413, "Up to 20 files at once")
    players, names = [], []
    for f in files:
        raw = await f.read(20 * 1024 * 1024 + 1)
        if len(raw) > 20 * 1024 * 1024:
            raise HTTPException(413, f"{f.filename} is over 20 MB")
        got = parse_html(raw, f.filename or "export.html")
        if not got:
            raise HTTPException(422, f"{f.filename}: no player table found. Export a view from FM with Print screen → Web page.")
        players += got
        names.append(f.filename)
    imp = {"id": new_id(), "career_id": c["id"], "files": names, "players": players, "status": "active", "at": now_iso()}
    await db.html_imports.insert_one(dict(imp))
    linked = sum(1 for p in players if p["linked"])
    await audit(c["id"], "HTML import", "scouting", f"{len(players)} players from {len(names)} file(s); {linked} linked by UID")
    return {"id": imp["id"], "players": len(players), "linked": linked}


@router.get("/imports")
async def imports():
    c = await active_career()
    rows = await db.html_imports.find({"career_id": c["id"], "status": "active"}, {"_id": 0, "players": 0}).sort("at", -1).to_list(50)
    for r in rows:
        r["count"] = len((await db.html_imports.find_one({"id": r["id"]}, {"_id": 0, "players.name": 1}))["players"])
    return rows


@router.delete("/imports/{imp_id}")
async def remove_import(imp_id: str):
    c = await active_career()
    res = await db.html_imports.update_one({"career_id": c["id"], "id": imp_id, "status": "active"}, {"$set": {"status": "removed", "removed_at": now_iso()}})
    if not res.modified_count:
        raise HTTPException(404, "Import not found")
    return {"ok": True}


# ---------- preferences and DOF reports ----------
class PrefsIn(BaseModel):
    currency: Literal["GBP", "EUR", "USD"] = "GBP"
    wages: Literal["week", "month", "year"] = "week"


@router.get("/prefs")
async def get_prefs():
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "scout_prefs": 1}) or {}
    return s.get("scout_prefs") or {"currency": "GBP", "wages": "week"}


@router.put("/prefs")
async def set_prefs(body: PrefsIn):
    await db.settings.update_one({"_id": "app"}, {"$set": {"scout_prefs": body.model_dump()}}, upsert=True)
    return body.model_dump()


@router.post("/player/{uid}/dof-report")
async def dof_report(uid: int):
    """Your Director of Football writes a scouting report from the Moneyball numbers only (no attributes)."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    from dof_api import api_key, MODEL
    c, data = await _data()
    x = data["by_uid"].get(uid)
    if not x:
        raise HTTPException(404, "Player not found")
    if not x["pct"]:
        raise HTTPException(409, f"He needs at least {sm.MIN_PCT} minutes for a numbers-only report")
    key = api_key()
    if not key:
        raise HTTPException(409, "Add your OpenAI key in Settings to get reports from your Director of Football")
    top = sorted(x["pct"].items(), key=lambda kv: -kv[1])
    facts = (f"Player: {x['name']}, {x['age']}, {x['cohort']} at {x['club']} ({x['league']}). Minutes {x['minutes']}. Global grade {x['grade_global']} "
             f"(league multiplier {x['league_mult']}). Value £{x['value'] or 0:,}. Fair price {'£' + format(x['fair_price'], ',') if x['fair_price'] else 'not enough minutes'}. "
             f"Contract months left: {x['months_left']}. Percentiles vs same position: " + "; ".join(f"{sm.METRICS[k][0]} {v}" for k, v in top)
             + ". Archetype scores: " + "; ".join(f"{data['archetypes'][k]['name']} {v}" for k, v in x["computed"].items() if v is not None))
    chat = LlmChat(api_key=key, session_id=f"dof-report-{uid}-{new_id()}", system_message=(
        "You are the Director of Football in FMCC, a Football Manager companion. Write a short Moneyball scouting report (120-180 words) "
        "from the numbers given only. Never mention attributes, CA or PA. Cover strengths, weaknesses, price versus fair price, and a clear recommendation.")).with_model(*MODEL)
    try:
        text = await chat.send_message(UserMessage(text=facts))
    except Exception as exc:
        logger.warning("dof report failed: %s", exc)
        raise HTTPException(502, "Your Director of Football couldn't write the report just now. Please try again.")
    doc = {"id": new_id(), "career_id": c["id"], "unique_id": uid, "name": x["name"], "text": str(text).strip(), "at": now_iso(), "season": data["season"]}
    await db.dof_reports.insert_one(dict(doc))
    return {k: v for k, v in doc.items() if k != "career_id"}
