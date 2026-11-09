"""World Monthly Reports: who made waves across every loaded league last month."""
import random
from datetime import date

from fastapi import APIRouter, HTTPException, Query

import stats_model as sm
from core import db, active_career, now_iso
from editor_api import LIVE
from sample_reader import GROUP, LEAGUE_INFO, LEAGUES, WOMEN

router = APIRouter(prefix="/api/world")
KEEP = ("unique_id", "name", "age", "club", "league", "country", "positions", "value", "minutes", "appearances", "goals", "assists", "avg_rating", "last_move", "gender")
MONTH_STATS = [("goals", "Goals"), ("assists", "Assists"), ("contrib", "Goal contributions"), ("rating", "Average match rating"), ("minutes", "Minutes played")]
P90 = ["npxg", "xa", "kp", "chc", "progp", "drb", "tkw", "prr", "pwon", "padbc", "savep", "xgp"]
AWARDS = [("attacker", "Attacker of the Month", {"ST", "AM", "W"}), ("defender", "Defender of the Month", {"CB", "FB"}),
          ("goalie", "Goalkeeper of the Month", {"GK"}), ("u21", "U21 Player of the Month", None)]


def country_of(league: str) -> str:
    return (LEAGUE_INFO.get(league) or ("Other",))[0]


def compact(pool: list) -> list:
    return [{k: p.get(k) for k in KEEP} | {"p90": p.get("stats") or (sm.sample_stats(p) if not LIVE else None) or {}} for p in pool]


async def record_month(career_id: str, pool_doc: dict):
    """Called after every save read: keeps one compact world snapshot per in-game month."""
    month = pool_doc["game_date"][:7]
    await db.world_months.update_one({"career_id": career_id, "month": month},
                                     {"$set": {"save_no": pool_doc["save_no"], "season": pool_doc["season"], "game_date": pool_doc["game_date"],
                                               "players": compact(pool_doc["players"]), "tables": pool_doc.get("tables"), "at": now_iso()}}, upsert=True)


def _norm(s: str) -> str:
    import leagues_api
    return leagues_api.norm(s)


def name_unnamed(tables: list, pool: list, workbook: list) -> dict:
    """Names 'Competition 123' tables from the league strength workbook: same country, tier by average club reputation, team count as tie-break.
    Renames the league on the tables and on every pool player in place; returns old -> new."""
    if not tables:
        return {}
    taken = {_norm(a) for t in tables if not t["league"].startswith("Competition ") for a in [t["league"]]}
    renames = {}
    for country in {t["country"] for t in tables}:
        mine = sorted([t for t in tables if t["country"] == country and not t.get("women")], key=lambda t: -(t.get("reputation") or 0))
        cands = [r for r in workbook if r.get("country") == country and _norm(r["name"]) not in taken and not any(_norm(a) in taken for a in r.get("aliases") or [])]
        cands.sort(key=lambda r: (r.get("tier") or 99, r.get("rank") or 9999))
        for expected, t in enumerate(mine, 1):
            if not t["league"].startswith("Competition ") or not cands:
                continue
            best = min(cands, key=lambda r: abs((r.get("tier") or len(cands) + expected) - expected) * 2 + (0 if r.get("teams") == len(t["rows"]) else 1))
            cands.remove(best)
            renames[t["league"]] = best["name"]
            t.update(league=best["name"], named_from_workbook=True)
    for p in pool:
        if p.get("league") in renames:
            p["league"] = renames[p["league"]]
    return renames


def _month_rows(cur: dict, prev: dict | None) -> list:
    same = prev and prev["season"] == cur["season"]
    before = {p["unique_id"]: p for p in prev["players"]} if prev else {}
    out = []
    for p in cur["players"]:
        o = before.get(p["unique_id"]) if same else None
        mins = (p["minutes"] or 0) - ((o or {}).get("minutes") or 0)
        apps = (p["appearances"] or 0) - ((o or {}).get("appearances") or 0)
        r2, a2 = p.get("avg_rating"), p.get("appearances") or 0
        r1, a1 = (o or {}).get("avg_rating"), (o or {}).get("appearances") or 0
        rating = round((r2 * a2 - (r1 or 0) * a1) / (a2 - a1), 2) if r2 and a2 > a1 else None
        g = (p["goals"] or 0) - ((o or {}).get("goals") or 0)
        a = (p.get("assists") or 0) - ((o or {}).get("assists") or 0)
        out.append(p | {"m_minutes": max(0, mins), "m_apps": max(0, apps), "m_rating": rating if rating and 3 <= rating <= 10 else r2 if not o else None,
                        "m_goals": max(0, g), "m_assists": max(0, a), "country": p.get("country") or country_of(p["league"]), "group": GROUP.get((p["positions"] or ["M (C)"])[0], "CM")})
    return out


def _table(league: str, months: int, rows_by_club: dict) -> list:
    """SAMPLE league table for the browser preview: four rounds a month, results weighted by squad rating."""
    clubs = LEAGUES[league]
    pts = {c: {"club": c, "p": 0, "w": 0, "d": 0, "l": 0, "gf": 0, "ga": 0, "pts": 0} for c in clubs}
    power = {c: sum(x.get("avg_rating") or 6.5 for x in rows_by_club.get(c, [])) / max(1, len(rows_by_club.get(c, []))) for c in clubs}
    for rnd in range(months * 4):
        rng = random.Random(f"{league}-{rnd}")
        n = len(clubs)
        order = clubs[rnd % n:] + clubs[:rnd % n]
        if n % 2:
            order = order[1:]
        rng.shuffle(order)
        for h, a in zip(order[::2], order[1::2]):
            gh = max(0, round(rng.gauss(1.4 + (power[h] - power[a]) * 1.5, 1.1)))
            ga = max(0, round(rng.gauss(1.1 + (power[a] - power[h]) * 1.5, 1.0)))
            for c, f, ag in ((h, gh, ga), (a, ga, gh)):
                t = pts[c]
                t["p"] += 1
                t["gf"] += f
                t["ga"] += ag
                t["w" if f > ag else "d" if f == ag else "l"] += 1
                t["pts"] += 3 if f > ag else 1 if f == ag else 0
    table = sorted(pts.values(), key=lambda t: (-t["pts"], -(t["gf"] - t["ga"]), -t["gf"], t["club"]))
    return [t | {"pos": i + 1, "gd": t["gf"] - t["ga"]} for i, t in enumerate(table)]


def _months_played(game_date: str) -> int:
    return (date.fromisoformat(game_date).month - 7) % 12


def _tables(cur: dict, prev: dict | None, rows: list, country: str | None) -> list:
    if cur.get("tables"):
        same = prev and prev["season"] == cur["season"]
        before = {(t["league"], r["club"]): r["pos"] for t in (prev or {}).get("tables") or [] for r in t["rows"]} if same else {}
        return [t | {"women": False, "rows": [r | {"move": before[(t["league"], r["club"])] - r["pos"] if (t["league"], r["club"]) in before else 0} for r in t["rows"]]}
                for t in cur["tables"] if not country or t["country"] == country]
    if LIVE:
        return []
    by_club = {}
    for r in rows:
        by_club.setdefault(r["club"], []).append(r)
    out = []
    for lg in LEAGUES:
        if country and country_of(lg) != country:
            continue
        now = _table(lg, _months_played(cur["game_date"]), by_club)
        before = {t["club"]: t["pos"] for t in _table(lg, _months_played(prev["game_date"]), by_club)} if prev and prev["season"] == cur["season"] else {}
        out.append({"league": lg, "country": country_of(lg), "women": lg in WOMEN, "rows": [t | {"move": before[t["club"]] - t["pos"] if t["club"] in before else 0} for t in now]})
    return out


def _transfers(rows: list, prev: dict | None) -> list:
    if not prev:
        return []
    before = {p["unique_id"]: p for p in prev["players"]}
    out = []
    for r in rows:
        o = before.get(r["unique_id"])
        if o and o["club"] != r["club"]:
            fee = (r.get("last_move") or {}).get("fee")
            out.append({"unique_id": r["unique_id"], "name": r["name"], "age": r["age"], "from_club": o["club"], "from_league": o["league"], "to_club": r["club"],
                        "to_league": r["league"], "country": r["country"], "from_country": o.get("country") or country_of(o["league"]), "fee": fee or r["value"], "estimated": not fee})
    return sorted(out, key=lambda t: -t["fee"])


def _lead(rows: list, key: str, n: int, p90: bool = False) -> list:
    if p90:
        vals = [(r["p90"].get(key), r) for r in rows if r["p90"].get(key) is not None and (r["minutes"] or 0) >= 450]
    else:
        get = {"goals": "m_goals", "assists": "m_assists", "minutes": "m_minutes", "rating": "m_rating"}.get(key)
        vals = [((r["m_goals"] + r["m_assists"]) if key == "contrib" else r[get], r) for r in rows if key != "rating" or (r["m_apps"] >= 2 and r["m_rating"])]
    vals = sorted([v for v in vals if v[0]], key=lambda v: -v[0])[:n]
    return [{"unique_id": r["unique_id"], "name": r["name"], "age": r["age"], "club": r["club"], "league": r["league"], "value": round(v, 2) if isinstance(v, float) else v} for v, r in vals]


def _score(r: dict, kind: str) -> float:
    rt = r["m_rating"] or 0
    if kind == "goalie":
        return rt * 12 + ((r["p90"].get("savep") or 70) - 70) * 0.2
    if kind == "defender":
        return rt * 12 + r["m_minutes"] / 90 * 0.4 + r["m_goals"] * 1.5
    return rt * 10 + r["m_goals"] * 4 + r["m_assists"] * 3


def _awards(rows: list, min_mins: int) -> dict:
    out = {}
    for key, label, groups in AWARDS:
        pool = [r for r in rows if r["m_minutes"] >= min_mins and r["m_rating"] and (r["age"] < 21 if groups is None else r["group"] in groups)]
        top = sorted(pool, key=lambda r: -_score(r, "goalie" if key == "goalie" else "defender" if key == "defender" else "attacker"))[:3]
        out[key] = {"label": label, "picks": [{"unique_id": r["unique_id"], "name": r["name"], "age": r["age"], "club": r["club"], "league": r["league"],
                                               "rating": r["m_rating"], "goals": r["m_goals"], "assists": r["m_assists"], "minutes": r["m_minutes"]} for r in top]}
    return out


def _money(v: int) -> str:
    return f"€{v / 1e6:.1f}m" if v >= 1e6 else f"€{v // 1000}k"


def _nth(n: int) -> str:
    return f"{n}{'th' if 10 <= n % 100 <= 20 else {1: 'st', 2: 'nd', 3: 'rd'}.get(n % 10, 'th')}"


def _news(rows: list, tables: list, transfers: list, awards: dict, scope: str) -> list:
    ev = []
    for t in transfers[:4]:
        ev.append((50 + t["fee"] / 1e6, t["country"], "Transfer", f"{t['name']} joins {t['to_club']} from {t['from_club']} for {'about ' if t['estimated'] else ''}{_money(t['fee'])}"))
    for tb in tables:
        if not tb["rows"]:
            continue
        top, second = tb["rows"][0], tb["rows"][1] if len(tb["rows"]) > 1 else None
        if top["move"] > 0:
            ev.append((42, tb["country"], "Title race", f"{top['club']} go top of the {tb['league']}"))
        elif second:
            ev.append((26 + (top["pts"] - second["pts"]), tb["country"], "Title race", f"{top['club']} stay top of the {tb['league']}, {top['pts'] - second['pts']} point(s) clear"))
        for t in tb["rows"]:
            if t["move"] >= 2:
                ev.append((15 + t["move"] * 3, tb["country"], "On the rise", f"{t['club']} climb {t['move']} places to {_nth(t['pos'])} in the {tb['league']}"))
    for r in rows:
        if r["m_goals"] >= 3:
            ev.append((18 + r["m_goals"] * 5, r["country"], "In form", f"{r['name']} scores {r['m_goals']} for {r['club']} this month"))
        if r["age"] < 21 and (r["m_rating"] or 0) >= 7.2 and r["m_apps"] >= 2:
            ev.append((22 + (r["m_rating"] - 7) * 20, r["country"], "Emerging talent", f"{r['age']}-year-old {r['name']} shines for {r['club']} (average {r['m_rating']})"))
    for a in awards.values():
        if a["picks"]:
            w = a["picks"][0]
            ev.append((36, country_of(w["league"]), "Award", f"{w['name']} ({w['club']}) is {scope} {a['label']}"))
    for r in sorted([r for r in rows if r["m_apps"] >= 2 and r["m_rating"]], key=lambda r: -r["m_rating"])[:12]:
        ev.append((8 + r["m_rating"], r["country"], "Top performer", f"{r['name']} averages {r['m_rating']} for {r['club']} this month"))
    ev.sort(key=lambda e: -e[0])
    return [{"tag": t, "country": c, "text": s} for _, c, t, s in ev]


@router.get("/report")
async def report(country: str | None = Query(None, max_length=60), month: str | None = Query(None, pattern=r"^\d{4}-\d{2}$")):
    c = await active_career()
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0})
    if not pool:
        raise HTTPException(404, "No save read yet")
    if not await db.world_months.find_one({"career_id": c["id"], "month": pool["game_date"][:7]}, {"_id": 1}):
        await record_month(c["id"], pool)
    months = [d["month"] async for d in db.world_months.find({"career_id": c["id"]}, {"_id": 0, "month": 1}).sort("month", 1)]
    month = month if month in months else months[-1]
    cur = await db.world_months.find_one({"career_id": c["id"], "month": month}, {"_id": 0})
    prev = await db.world_months.find_one({"career_id": c["id"], "month": {"$lt": month}}, {"_id": 0}, sort=[("month", -1)])
    rows_all = [r for r in _month_rows(cur, prev) if r.get("gender") != "F"]
    countries = sorted({r["country"] for r in rows_all})
    if country and country not in countries:
        raise HTTPException(404, "That country isn't in your loaded leagues")
    rows = [r for r in rows_all if not country or r["country"] == country]
    tables = _tables(cur, prev, rows_all, country)
    transfers = [t for t in _transfers(rows_all, prev) if not country or country in (t["country"], t["from_country"])]
    awards = _awards(rows, 180 if prev and prev["season"] == cur["season"] else 360)
    news = _news(rows, tables, transfers, awards, f"{country}'s" if country else "the World")
    u21 = [r for r in rows if r["age"] < 21]
    leaders = [{"key": k, "label": lab, "kind": "month", "rows": _lead(rows, k, 10), "u21": _lead(u21, k, 5)} for k, lab in MONTH_STATS]
    leaders += [{"key": k, "label": sm.METRICS[k][0], "kind": "p90", "rows": _lead(rows, k, 10, True), "u21": _lead(u21, k, 5, True)} for k in P90 if k in sm.METRICS]
    return {"month": month, "months": months, "game_date": cur["game_date"], "from": prev["game_date"] if prev else None, "season_so_far": not (prev and prev["season"] == cur["season"]),
            "country": country, "countries": [{"country": k, "leagues": sorted({r["league"] for r in rows_all if r["country"] == k})} for k in countries],
            "news": news[:5] if country else news[:12], "tables": tables, "transfers": transfers[:10], "leaders": [x for x in leaders if x["rows"]], "awards": awards,
            "sample": not LIVE, "tables_note": None if tables else "No league tables in this save yet. FM only keeps a table once its clubs have played a match.",
            "names_note": ("Some competitions show as 'Competition 123': neither the save nor your league strength workbook has their names." if any(t["league"].startswith("Competition ") for t in tables)
                           else "League names marked * come from your league strength workbook, matched by country and level." if any(t.get("named_from_workbook") for t in tables) else None)}
