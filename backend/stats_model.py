"""FMCC's scouting engine: ScoutSheet-style views and FMDataLab-style analytics, graded with the FM26 Player Rating & Similarity Model workbook.
Browser preview: match stats are SAMPLE numbers generated from each player's attributes."""
import json
import math
import os
import random
import statistics
import zlib
from datetime import date
from pathlib import Path

import roles
from core import db, latest_snapshot
from sample_reader import GROUP

DATA = Path(__file__).parent / "data"
WEIGHTS = json.loads((DATA / "position_weights.json").read_text(encoding="utf-8"))
LIVE = os.environ.get("FMCC_READER") == "fmsave"
MIN_PCT, MIN_PRICE = 400, 900
CACHE: dict = {}

# key: label, kind (att = attacking count, def = defensive count, pct = rate, not possession-adjusted), mean, sd, drivers ("-" = lowers it), GK only
METRICS = {
    "xgp": ("xG prevented / 90", "def", 0.0, .12, ["reflexes", "one_on_ones"], True), "savep": ("Save percentage", "pct", 70, 6, ["reflexes", "handling"], True),
    "saves": ("Saves / 90", "def", 2.8, .8, ["reflexes"], True), "gc": ("Goals conceded / 90", "def", 1.2, .3, ["-reflexes", "-command_of_area"], True),
    "mlg": ("Mistakes leading to goals / 90", "def", .03, .02, ["-decisions", "-composure"], False), "csr": ("Clean-sheet rate", "pct", 30, 10, ["command_of_area", "reflexes"], True),
    "passc": ("Pass completion", "pct", 80, 6, ["passing", "technique", "composure"], False), "progp": ("Progressive passes / 90", "att", 4, 2, ["passing", "vision"], False),
    "plost": ("Possession lost / 90", "att", 9, 3, ["-first_touch", "-composure"], False), "aerr": ("Aerial-duel win rate", "pct", 52, 10, ["heading", "jumping_reach", "strength"], False),
    "padint": ("Possession-adjusted interceptions / 90", "def", 1.6, .6, ["anticipation", "positioning"], False), "tkr": ("Tackle win rate", "pct", 65, 8, ["tackling"], False),
    "pwl": ("Possession-won / possession-lost ratio", "pct", 1.0, .35, ["tackling", "decisions"], False), "err": ("Errors / mistakes / 90", "def", .06, .03, ["-decisions", "-composure"], False),
    "padbc": ("Possession-adjusted blocks + clearances / 90", "def", 4, 1.5, ["positioning", "heading"], False), "tkw": ("Tackles won / 90", "def", 1.3, .5, ["tackling", "work_rate"], False),
    "aerw": ("Aerial duels won / 90", "def", 2, 1, ["heading", "jumping_reach"], False), "intc": ("Interceptions / 90", "def", 1.4, .5, ["anticipation", "positioning"], False),
    "blk": ("Blocks / 90", "def", .6, .3, ["positioning", "marking"], False), "khkt": ("Key headers + key tackles / 90", "def", .5, .25, ["heading", "tackling"], False),
    "xa": ("Expected assists / 90", "att", .1, .06, ["vision", "passing", "crossing"], False), "crc": ("Cross completion", "pct", 25, 8, ["crossing"], False),
    "drr": ("Successful-dribble rate", "pct", 55, 12, ["dribbling", "flair"], False), "epl": ("Errors + possession losses / 90", "att", 10, 3, ["-first_touch", "-decisions"], False),
    "acr": ("Accurate crosses / 90", "att", .8, .5, ["crossing"], False), "drb": ("Successful dribbles / 90", "att", 1, .7, ["dribbling", "acceleration"], False),
    "kp": ("Open-play key passes / 90", "att", .8, .5, ["vision", "passing"], False), "ast": ("Assists / 90", "att", .08, .06, ["vision", "passing"], False),
    "gls": ("Goals / 90", "att", .1, .1, ["finishing", "off_the_ball"], False), "spr": ("Sprints / 90", "att", 20, 6, ["pace", "stamina"], False),
    "xakp": ("Expected assists or key-pass rate", "pct", 2.5, 1, ["vision"], False), "prr": ("Successful-pressure rate", "pct", 30, 6, ["work_rate", "anticipation"], False),
    "pwon": ("Possession won / 90", "def", 6, 2, ["tackling", "anticipation", "work_rate"], False), "ppc": ("Progressive passes completed / 90", "att", 3, 1.5, ["passing", "vision"], False),
    "ktk": ("Key tackles / 90", "def", .2, .1, ["tackling"], False), "ccr": ("Chance-creation rate", "pct", 3, 1.2, ["vision", "technique"], False),
    "npxg": ("Non-penalty expected goals / 90", "att", .12, .1, ["off_the_ball", "finishing"], False), "tpr": ("Tackle or pressure success rate", "pct", 40, 8, ["tackling", "work_rate"], False),
    "pcmp": ("Passes completed / 90", "att", 45, 12, ["passing", "composure"], False), "xakq": ("Chance quality: xA per key pass", "pct", .1, .04, ["vision"], False),
    "sha": ("Shooting accuracy", "pct", 40, 10, ["finishing", "composure"], False), "off": ("Offsides / 90", "att", .3, .2, ["-decisions"], False),
    "npg": ("Non-penalty goals / 90", "att", .12, .12, ["finishing", "composure"], False), "sot": ("Shots on target / 90", "att", .6, .4, ["finishing", "technique"], False),
    "chc": ("Chances created / 90", "att", 1.2, .6, ["vision", "passing"], False), "xgo": ("Regressed xG overperformance", "pct", 0, .05, ["finishing", "composure"], False),
    "fd": ("Fouls drawn / 90", "att", 1.2, .6, ["dribbling", "flair"], False), "xgs": ("Average xG per shot", "pct", .12, .04, ["off_the_ball", "anticipation"], False),
}
LABEL2KEY = {v[0]: k for k, v in METRICS.items()}
NEUTRAL = {"pcmp", "plost", "spr", "epl", "progp", "ppc"}
POSM = {"GK": (.05, .2), "CB": (.3, 1.4), "FB": (.7, 1.0), "DM": (.5, 1.3), "CM": (.8, .9), "AM": (1.2, .5), "W": (1.2, .5), "ST": (1.4, .35)}
COHORT = {"GK": "Goalkeeper", "CB": "Centre-back", "FB": "Full-back", "DM": "Defensive midfielder", "CM": "Central midfielder",
          "AM": "Attacking midfielder", "W": "Winger / wide forward", "ST": "Striker"}
DIRECTION = {LABEL2KEY[m["metric"]]: m["direction"] for ms in WEIGHTS.values() for m in ms if m["metric"] in LABEL2KEY}
PHASES = {"finishing": ["npxg", "npg", "sha", "xgs", "sot"], "creating": ["xa", "kp", "chc", "ccr", "progp"],
          "carrying": ["drb", "drr", "ppc", "spr"], "defending": ["tkw", "intc", "tkr", "aerr", "pwon"]}
ACTIONS = {"Defensive actions": {"tkw": 1, "intc": 1, "blk": .5, "pwon": .5, "aerw": .5}, "Progressive actions": {"progp": 1, "drb": 1, "ppc": .5},
           "Box involvement": {"npxg": 5, "sot": 1, "kp": .5, "xa": 5}}
# key: name, {metric: (weight 0-10, phase in/out)}
ARCHETYPES = {
    "bpd": ("Ball-Playing Defender", {"progp": (8, "in"), "passc": (6, "in"), "ppc": (6, "in"), "aerr": (5, "out"), "intc": (6, "out"), "tkr": (5, "out")}),
    "box_crasher": ("Box Crasher", {"npxg": (9, "in"), "npg": (7, "in"), "sot": (5, "in"), "xgs": (5, "in"), "pwon": (3, "out")}),
    "pressing_fwd": ("Pressing Forward", {"prr": (9, "out"), "pwon": (7, "out"), "tkw": (4, "out"), "npxg": (6, "in"), "xa": (4, "in")}),
    "dlp": ("Deep-Lying Playmaker", {"progp": (9, "in"), "ppc": (7, "in"), "passc": (6, "in"), "xa": (4, "in"), "intc": (4, "out")}),
    "ball_winner": ("Ball-Winning Midfielder", {"tkw": (9, "out"), "pwon": (8, "out"), "intc": (7, "out"), "tkr": (6, "out"), "passc": (3, "in")}),
    "inverted_winger": ("Inverted Winger", {"npxg": (7, "in"), "drb": (7, "in"), "xa": (6, "in"), "sha": (4, "in"), "fd": (3, "in"), "prr": (3, "out")}),
    "overlap_fb": ("Overlapping Full-back", {"acr": (8, "in"), "crc": (6, "in"), "xa": (6, "in"), "spr": (6, "in"), "tkr": (5, "out"), "intc": (4, "out")}),
    "sweeper_keeper": ("Sweeper Keeper", {"progp": (8, "in"), "passc": (7, "in"), "xgp": (7, "out"), "savep": (5, "out")}),
}
ARCH_GROUPS = {"bpd": ["CB"], "box_crasher": ["CM", "AM", "W", "ST"], "pressing_fwd": ["ST", "W", "AM"], "dlp": ["DM", "CM"], "ball_winner": ["DM", "CM"],
               "inverted_winger": ["W", "AM"], "overlap_fb": ["FB"], "sweeper_keeper": ["GK"]}
HIDDEN = ["consistency", "important_matches", "injury_proneness", "versatility", "professionalism", "ambition", "pressure", "temperament", "loyalty", "controversy"]


def cohort_of(p: dict) -> str:
    return "Wing-back" if p["positions"][0].startswith("WB") else COHORT[GROUP[p["positions"][0]]]


def _rng(uid: int, salt: str) -> random.Random:
    return random.Random(uid * 1009 + zlib.crc32(salt.encode()))


def sample_stats(p: dict) -> dict | None:
    """SAMPLE per-90 numbers for the browser preview, built from the player's attributes and position."""
    if not p.get("minutes"):
        return None
    g, a, out = GROUP[p["positions"][0]], p.get("attributes", {}), {}
    for k, (_, kind, mean, sd, drivers, gk_only) in METRICS.items():
        if gk_only and g != "GK":
            continue
        if g == "GK" and not gk_only and k not in ("passc", "progp", "plost", "mlg"):
            continue
        drv = sum((-1 if d[0] == "-" else 1) * (a.get(d.lstrip("-"), 10) - 10) / 10 for d in drivers) / max(1, len(drivers)) + (p.get("ca", 120) - 120) / 200
        pm = 1 if kind == "pct" or k in NEUTRAL else POSM[g][0 if kind == "att" else 1]
        v = mean * pm * (1 + .35 * drv) + sd * _rng(p["unique_id"], k).gauss(0, 1) * .7 * (pm if kind != "pct" else 1)
        if k not in ("xgp", "xgo"):
            v = max(0.0, v)
        out[k] = round(min(v, 100) if kind == "pct" and mean > 5 else v, 3)
    return out


def sample_hidden(p: dict) -> dict:
    r = _rng(p["unique_id"], "hidden")
    return {h: r.randint(3, 19) for h in HIDDEN}


def personality(h: dict) -> str:
    if h["professionalism"] >= 17 and h["ambition"] >= 15:
        return "Model Citizen"
    if h["temperament"] <= 6 or h["controversy"] >= 16:
        return "Volatile"
    if h["professionalism"] >= 15:
        return "Professional"
    if h["ambition"] >= 16:
        return "Driven"
    if h["pressure"] >= 16:
        return "Resolute"
    return "Balanced" if h["professionalism"] >= 9 else "Casual"


def months_left(contract_end: str | None, game_date: str) -> int | None:
    if not contract_end:
        return None
    a, b = date.fromisoformat(game_date), date.fromisoformat(contract_end)
    return max(0, (b.year - a.year) * 12 + b.month - a.month)


def _med_mad(vals: list) -> tuple:
    med = statistics.median(vals)
    mad = statistics.median([abs(v - med) for v in vals]) or (statistics.pstdev(vals) / 1.4826 if len(vals) > 1 else 0) or 1e-6
    return med, mad


async def _state_key(c: dict) -> tuple:
    import leagues_api
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "save_no": 1, "game_date": 1})
    counts = [await db[x].count_documents({"career_id": c["id"]}) for x in ("possession", "computed_stats")]
    counts.append(",".join(sorted([d["id"] async for d in db.html_imports.find({"career_id": c["id"], "status": "active"}, {"id": 1})])))
    mult = await leagues_api.multipliers(c)
    return (c["id"], (pool or {}).get("save_no"), *counts, json.dumps(mult, sort_keys=True)), mult


async def latest_docs(col: str, career_id: str, key: str) -> dict:
    pipeline = [{"$match": {"career_id": career_id}}, {"$sort": {"revision": -1}}, {"$group": {"_id": f"${key}", "doc": {"$first": "$$ROOT"}}}]
    return {d["_id"]: {k: v for k, v in d["doc"].items() if k != "_id"} async for d in db[col].aggregate(pipeline)}


async def archetypes(career_id: str) -> dict:
    """Built-in archetypes (with your weight edits) plus up to 6 custom computed stats."""
    edits = await latest_docs("computed_stats", career_id, "key")
    out = {k: {"key": k, "name": n, "metrics": {m: w for m, (w, _) in ms.items()}, "phases": {m: ph for m, (_, ph) in ms.items()}, "builtin": True, "groups": ARCH_GROUPS[k],
               "defaults": {m: w for m, (w, _) in ms.items()}} for k, (n, ms) in ARCHETYPES.items()}
    for k, e in edits.items():
        if e.get("status") == "deleted":
            out.pop(k, None)
        elif k in out:
            out[k]["metrics"] = e["metrics"]
            out[k]["revision"] = e["revision"]
        else:
            out[k] = {"key": k, "name": e["name"], "metrics": e["metrics"], "phases": e.get("phases") or {}, "builtin": False, "defaults": None, "revision": e["revision"]}
    for a in out.values():
        a["changed"] = sorted(m for m, w in a["metrics"].items() if a["defaults"] and a["defaults"].get(m) != w)
    return out


async def build(c: dict) -> dict:
    key, mult = await _state_key(c)
    if CACHE.get("key") == key:
        return CACHE["data"]
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0}) or {"players": [], "game_date": None}
    try:
        snap = await latest_snapshot(c["id"])
    except Exception:
        snap = {"players": [], "game_date": pool.get("game_date")}
    gd = pool.get("game_date") or snap.get("game_date")
    poss = {k: v["value"] for k, v in (await latest_docs("possession", c["id"], "club")).items() if v.get("value")}
    ours = poss.get(c["club_name"])
    raw = [p | {"club": c["club_name"], "league": c.get("league") or "Premier Division", "own": True, "value": p.get("value") or 0, "source": "save"} for p in snap["players"]]
    raw += [p | {"own": False, "source": "save"} for p in pool["players"]]
    async for imp in db.html_imports.find({"career_id": c["id"], "status": "active"}, {"_id": 0}):
        raw += [p | {"own": False, "source": "html", "import_id": imp["id"]} for p in imp["players"]]
    players = []
    for p in raw:
        stats = p.get("stats") if p.get("stats") is not None else (None if LIVE or p["source"] == "html" else sample_stats(p))
        hidden = p.get("hidden") or (None if LIVE or p["source"] == "html" else sample_hidden(p))
        lm = mult.get(p["league"], {}).get("multiplier", 1.0) if p.get("league") else 1.0
        lmeta = mult.get(p.get("league") or "", {})
        theirs = poss.get(p["club"])
        pa = ours / theirs if ours and theirs and not p["own"] else 1.0
        adj, p90 = {}, stats or {}
        for k, v in p90.items():
            kind = METRICS[k][1]
            adj[k] = v if kind == "pct" else round(v * (pa if kind == "att" else 1 / pa), 3)
        r = _rng(p.get("unique_id") or 0, "know")
        players.append({**{k: p.get(k) for k in ("unique_id", "name", "age", "nationality", "club", "league", "positions", "ca", "pa", "value", "wage",
                                                 "minutes", "appearances", "attributes", "own", "source", "import_id", "contract_end", "linked")},
                        "gender": p.get("gender", "M"), "league_scored": lmeta.get("scored", True), "league_note": lmeta.get("no_score"), "group": GROUP.get(p["positions"][0], "CM") if p.get("positions") else "CM", "cohort": cohort_of(p) if p.get("positions") else "Central midfielder",
                        "p90": p90, "adj": adj, "poss_mult": round(pa, 3), "league_mult": round(lm, 3), "hidden": hidden,
                        "personality": personality(hidden) if hidden else None, "knowledge": 100 if p["own"] else 20 + r.randint(0, 80),
                        "months_left": months_left(p.get("contract_end"), gd) if gd else None, "minutes": p.get("minutes") or 0})
    _grade(players)
    arch = await archetypes(c["id"])
    for x in players:
        x["phases"] = {ph: _avg([x["pct"].get(m) for m in ms]) for ph, ms in PHASES.items()} if x["pct"] else {}
        x["computed"] = {k: _score(x, a["metrics"]) if not a.get("groups") or x["group"] in a["groups"] else None for k, a in arch.items()} if x["pct"] else {}
        x["actions"] = {n: round(sum(x["p90"].get(m, 0) * w for m, w in ws.items()), 2) for n, ws in ACTIONS.items()} if x["p90"] else {}
        x["confidence"] = "Low" if x["minutes"] < MIN_PRICE else "Medium" if x["minutes"] < 1800 else "High"
        if x.get("attributes"):
            b = roles.best_role(x)
            x["best_role"] = f"{b['name']} ({b['duty']})"
    _fair_prices(players)
    by_uid = {p["unique_id"]: p for p in players if p.get("unique_id") and p["source"] == "html"}
    by_uid |= {p["unique_id"]: p for p in players if p.get("unique_id") and p["source"] == "save"}
    data = {"players": players, "by_uid": by_uid, "game_date": gd, "archetypes": arch,
            "possession": poss, "season": pool.get("season")}
    CACHE.update(key=key, data=data)
    return data


def _avg(vals: list):
    vals = [v for v in vals if v is not None]
    return round(sum(vals) / len(vals)) if vals else None


def _score(x: dict, weights: dict):
    tot = sum(w for m, w in weights.items() if x["pct"].get(m) is not None)
    return round(sum(w * x["pct"][m] for m, w in weights.items() if x["pct"].get(m) is not None) / tot) if tot else None


def _grade(players: list):
    """Workbook pipeline: robust z vs same-position cohort, metric score, analytical/output raws, reliability, local and global grade."""
    groups: dict = {}
    for x in players:
        groups.setdefault(x["cohort"], []).append(x)
    for cohort, xs in groups.items():
        base = [x for x in xs if x["minutes"] >= MIN_PCT] or [x for x in xs if x["minutes"]]
        stats = {}
        for k in METRICS:
            vals = [x["adj"][k] for x in base if x["adj"].get(k) is not None]
            if len(vals) >= 3:
                stats[k] = (_med_mad(vals), sorted(vals))
        wts = WEIGHTS.get(cohort, [])
        for x in xs:
            x["z"], x["pct"], x["grade_local"], x["grade_global"] = {}, {}, None, None
            if not x["adj"]:
                continue
            for k, ((med, mad), srt) in stats.items():
                v = x["adj"].get(k)
                if v is None:
                    continue
                d = DIRECTION.get(k, -1 if k in ("plost", "epl", "err", "mlg", "gc", "off") else 1)
                x["z"][k] = d * (v - med) / (1.4826 * mad)
                below = sum(1 for s in srt if s <= v) / len(srt) * 100
                x["pct"][k] = round(below if d > 0 else 100 - below + 100 / len(srt))
                x["pct"][k] = max(0, min(100, x["pct"][k]))
            if x["minutes"] < MIN_PCT:
                x["pct"] = {}
            parts = {}
            for m in wts:
                k = LABEL2KEY.get(m["metric"])
                if k in x["z"]:
                    s = max(20, min(100, 50 + 15 * x["z"][k]))
                    a = parts.setdefault(m["category"], [0, 0])
                    a[0] += m["weight"] * s
                    a[1] += m["weight"]
            if not parts or x["minutes"] < MIN_PCT:
                continue
            A = parts["Analytical"][0] / parts["Analytical"][1] if parts.get("Analytical", [0, 0])[1] else 50
            O = parts["Actual"][0] / parts["Actual"][1] if parts.get("Actual", [0, 0])[1] else A
            m = x["minutes"]
            a_s, o_s = 50 + m / (m + 450) * (A - 50), 50 + m / (m + 1200) * (O - 50)
            local = .75 * a_s + .25 * o_s
            x["grade_local"] = round(local, 1)
            x["grade_global"] = round(20 + (local - 20) * x["league_mult"], 1)


def _fair_prices(players: list):
    """ScoutSheet-style fair price: the median value of the 8 most similar players in your save (grade, age, contract)."""
    market = [x for x in players if not x["own"] and x["value"] and x["grade_global"] and x["minutes"] >= MIN_PRICE]
    for x in players:
        x["fair_price"] = None
        if x["minutes"] < MIN_PRICE or x["grade_global"] is None:
            continue
        yrs = (x["months_left"] or 24) / 12
        near = sorted((abs(o["grade_global"] - x["grade_global"]) / 4 + abs(o["age"] - x["age"]) / 2 + abs((o["months_left"] or 24) / 12 - yrs), o["value"])
                      for o in market if o["unique_id"] != x["unique_id"])[:8]
        if len(near) >= 4:
            x["fair_price"] = int(statistics.median(v for _, v in near) // 25_000 * 25_000)


def similar(data: dict, x: dict, n: int = 8) -> list:
    """Workbook similarity engine: profile distance on weighted z-scores plus ability proximity, same position only."""
    wts = {LABEL2KEY[m["metric"]]: m["weight"] for m in WEIGHTS.get(x["cohort"], []) if m["metric"] in LABEL2KEY}
    if not x["z"] or x["grade_global"] is None:
        return []
    out = []
    for o in data["players"]:
        if o is x or o["cohort"] != x["cohort"] or o["gender"] != x["gender"] or not o["z"] or o["grade_global"] is None:
            continue
        have = [k for k in wts if k in x["z"]]
        if not have or sum(1 for k in have if k in o["z"]) / len(have) < .8:
            continue
        d = math.sqrt(sum(wts[k] * (x["z"][k] - o["z"].get(k, 0)) ** 2 for k in have) / sum(wts[k] for k in have))
        prof = 100 * math.exp(-.5 * (d / 1.25) ** 2)
        abil = 100 * math.exp(-.5 * ((o["grade_global"] - x["grade_global"]) / 10) ** 2)
        out.append({"unique_id": o["unique_id"], "name": o["name"], "club": o["club"], "age": o["age"], "grade": o["grade_global"], "value": o["value"],
                    "style": round(prof), "ability": round(abil), "similarity": round(.8 * prof + .2 * abil)})
    return sorted(out, key=lambda r: -r["similarity"])[:n]
