"""Club History: permanent season archive, trophy cabinet, records, analytical leaders, milestones, Hall of Fame and season comparison.
Only uses what FMCC read from the save (plus FMCC's own awards). Missing figures stay None ("Unavailable"). True CA/PA are never stored here."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

from core import db, active_career, now_iso, new_id, audit

router = APIRouter(prefix="/api/history")
SQUAD_KEYS = ("unique_id", "name", "age", "positions", "appearances", "minutes", "goals", "assists", "avg_rating", "homegrown")
MIN_RATE_MINUTES = 900
LEADERS = [("goals", "Goals", "regular"), ("assists", "Assists", "regular"), ("appearances", "Appearances", "regular"), ("starts", "Starts", "regular"), ("minutes", "Minutes", "regular"),
           ("avg_rating", "Average rating (min 900 minutes)", "regular"), ("clean_sheets", "Clean sheets (goalkeepers)", "regular"), ("tackles", "Tackles", "regular"), ("duels_won", "Duels won", "regular"),
           ("npxg", "Non-penalty xG", "analytical"), ("xa", "Expected assists", "analytical"), ("xgxa", "xG + xA", "analytical"), ("progp", "Progressive passes", "analytical"),
           ("prgc", "Progressive carries", "analytical"), ("xgp", "Goals prevented", "analytical")]


def _honour_kind(h: dict) -> str:
    k = str(h.get("kind") or h.get("stage") or "").lower()
    return "promotion" if "promot" in k else "runner_up" if "runner" in k or k == "final_lost" else "playoff" if "playoff" in k or "play-off" in k else "trophy"


async def _match_stats(cid: str, season: str) -> dict:
    """Per-match facts for one season, from MatchLens imports when present."""
    ms = await db.matches.find({"career_id": cid, "season": season}, {"_id": 0, "id": 1, "date": 1, "opponent": 1, "home": 1, "score": 1, "attendance": 1, "competition": 1, "players": 1}).sort("date", 1).to_list(400)
    per: dict = {}
    for m in ms:
        us, them = (m.get("score") or [None, None])[:2] if isinstance(m.get("score"), list) else (None, None)
        for p in m.get("players") or []:
            if p.get("team") != "us":
                continue
            a = per.setdefault(p["unique_id"], {"starts": 0, "clean_sheets": 0, "xg": 0.0, "xa": 0.0, "duels_won": 0, "tackles": 0, "best_match_goals": 0, "best_match": None})
            a["starts"] += 1 if p.get("started", p.get("minutes", 0) >= 60) else 0
            a["xg"] += p.get("xg") or 0
            a["xa"] += p.get("xa") or 0
            a["duels_won"] += p.get("duels_won") or 0
            a["tackles"] += p.get("tackles") or 0
            if them == 0 and str(p.get("pos", "")).upper().startswith("GK"):
                a["clean_sheets"] += 1
            if (p.get("goals") or 0) > a["best_match_goals"]:
                a["best_match_goals"], a["best_match"] = p["goals"], m["id"]
    return {"matches": ms, "per": per}


async def _build_season(c: dict, season: str, snaps: list, completed: bool, prior_apps: set) -> dict:
    last = snaps[-1]
    hist = last.get("history") or {}
    wm = await db.world_months.find_one({"career_id": c["id"], "season": season, "tables": {"$ne": None}}, {"_id": 0, "tables": 1}, sort=[("game_date", -1)])
    league = None
    for t in (wm or {}).get("tables") or []:
        r = next((r for r in t["rows"] if r["club"] == last["club_name"]), None)
        if r:
            league = {"division": t["league"], "pos": r["pos"], "played": r["p"], "w": r["w"], "d": r["d"], "l": r["l"], "pts": r["pts"], "gf": r["gf"], "ga": r["ga"], "gd": r["gd"], "of": len(t["rows"])}
    ms = await _match_stats(c["id"], season)
    sh = {h["unique_id"]: h.get("p90") or {} async for h in db.stat_history.find({"career_id": c["id"], "season": season, "club": last["club_name"]}, {"_id": 0, "unique_id": 1, "p90": 1})}
    awards = {}
    async for a in db.awards.find({"career_id": c["id"], "status": {"$in": ["official", "awarded"]}, "award_key": {"$regex": f":{season}:|:{season[:4]}-(0[7-9]|1[0-2]):|:{int(season[:4]) + 1}-0[1-6]:"}}, {"_id": 0}):
        awards.setdefault(a["unique_id"], []).append("Breakout Player" if a["module"] == "breakout" else "Elite Training graduate")
    squad = []
    for p in last["players"]:
        row = {k: p.get(k) for k in SQUAD_KEYS}
        m, v = ms["per"].get(p["unique_id"]), sh.get(p["unique_id"], {})
        mins = p.get("minutes") or 0
        tot = lambda k: round(v[k] * mins / 90, 1) if v.get(k) is not None and mins else None  # noqa: E731
        row |= {"starts": m["starts"] if m else None, "clean_sheets": m["clean_sheets"] if m else None, "tackles": m["tackles"] if m else None, "duels_won": m["duels_won"] if m else None,
                "best_match_goals": m["best_match_goals"] if m else None, "best_match": m["best_match"] if m else None,
                "npxg": tot("npxg"), "xa": tot("xa"), "progp": tot("progp"), "prgc": tot("prgc"), "xgp": tot("xgp"), "awards": awards.get(p["unique_id"], []),
                "debut": prior_apps is not None and bool(p.get("appearances")) and p["unique_id"] not in prior_apps}
        row["xgxa"] = round(row["npxg"] + row["xa"], 1) if row["npxg"] is not None and row["xa"] is not None else None
        squad.append(row)
    top = max(squad, key=lambda r: r["goals"] or 0, default=None)
    import finance_api
    fin = last.get("finance") or {}
    first_ids = {p["unique_id"] for p in snaps[0]["players"]}
    last_ids = {p["unique_id"] for p in last["players"]}
    dp = await db.changes.count_documents({"career_id": c["id"], "source": "dp", "status": "applied", "season": season})
    honours = [h | {"kind": _honour_kind(h), "season": h.get("season") or season} for h in hist.get("honours") or [] if (h.get("season") or season) == season]
    return {"career_id": c["id"], "season": season, "status": "Completed" if completed else "In Progress", "club": last["club_name"], "game_date": last["game_date"],
            "league": league, "cups": hist.get("cups") or [], "honours": honours, "individual": hist.get("awards") or [], "save_milestones": hist.get("milestones") or [],
            "squad": squad, "top_scorer": {"unique_id": top["unique_id"], "name": top["name"], "goals": top["goals"]} if top and top["goals"] else None,
            "recruitment": {"arrivals": [p["name"] for p in last["players"] if p["unique_id"] not in first_ids], "departures": [p["name"] for p in snaps[0]["players"] if p["unique_id"] not in last_ids],
                            "spent": fin.get("transfer_spent"), "received": fin.get("transfer_received"),
                            "net": (fin["transfer_received"] - fin["transfer_spent"]) if fin.get("transfer_received") is not None and fin.get("transfer_spent") is not None else None},
            "academy": {"debuts": [r["name"] for r in squad if r["debut"] and r["homegrown"]], "homegrown_minutes": sum(r["minutes"] or 0 for r in squad if r["homegrown"]),
                        "elite": [r["name"] for r in squad if "Elite Training graduate" in r["awards"]], "dp_changes": dp},
            "growth": {"attendance": hist.get("attendance"), "capacity": hist.get("capacity"), "stadium": hist.get("stadium"), "wage_bill": fin.get("wage_bill"), "facilities": hist.get("facilities"), "academy_level": hist.get("academy")},
            "manager": hist.get("manager"), "matches": [{k: m.get(k) for k in ("id", "date", "opponent", "home", "score", "attendance", "competition")} for m in ms["matches"]],
            "sources": [{"save_no": s["save_no"] + 1, "file": s.get("file_name"), "reader": s.get("reader"), "game_date": s["game_date"]} for s in snaps], "updated_at": now_iso()}


def _fill(old: dict, new: dict) -> dict:
    """Completed seasons are kept as they happened; later imports only fill gaps (None/empty), never duplicate."""
    out = dict(old)
    for k, v in new.items():
        if out.get(k) in (None, [], {}):
            out[k] = v
        elif isinstance(v, dict) and isinstance(out.get(k), dict):
            out[k] = {**v, **{kk: vv for kk, vv in out[k].items() if vv not in (None, [], {})}}
    out["sources"] = list({s["save_no"]: s for s in (old.get("sources") or []) + new["sources"]}.values())
    return out


async def archive(c: dict) -> list:
    snaps = await db.snapshots.find({"career_id": c["id"]}, {"_id": 0, "save_no": 1, "season": 1, "game_date": 1, "club_name": 1, "players": 1, "finance": 1, "history": 1, "file_name": 1, "reader": 1}).sort("save_no", 1).to_list(500)
    seasons: dict = {}
    for s in snaps:
        seasons.setdefault(s["season"], []).append(s)
    order, prior, out = sorted(seasons), set(), []
    for i, season in enumerate(order):
        completed = i < len(order) - 1
        old = await db.season_archive.find_one({"career_id": c["id"], "season": season}, {"_id": 0})
        if old and old["status"] == "Completed":
            doc = old
        else:
            doc = await _build_season(c, season, seasons[season], completed, prior if i else None)
            if old:
                doc = _fill(doc, old) if not completed else _fill(old, doc) | {"status": "Completed"}
            await db.season_archive.update_one({"career_id": c["id"], "season": season}, {"$set": doc}, upsert=True)
        prior |= {r["unique_id"] for r in doc["squad"] if r.get("appearances")}
        out.append(doc)
    return out


def _summary(s: dict) -> dict:
    lg = s.get("league") or {}
    cup = max(s.get("cups") or [], key=lambda x: len(str(x.get("stage") or "")), default=None)
    return {"season": s["season"], "status": s["status"], "division": lg.get("division"), "finish": lg.get("pos"), "of": lg.get("of"), "points": lg.get("pts"),
            "best_cup": f"{cup.get('competition')}: {cup.get('stage')}" if cup else None, "top_scorer": s.get("top_scorer"),
            "honours": [f"{h.get('competition')}" + (" (promotion)" if h["kind"] == "promotion" else " (runners-up)" if h["kind"] == "runner_up" else "") for h in s.get("honours") or []]}


@router.get("/seasons")
async def seasons():
    c = await active_career()
    return {"seasons": [_summary(s) for s in reversed(await archive(c))]}


@router.get("/seasons/{y1}/{y2}")
async def season_page(y1: str, y2: str):
    c = await active_career()
    await archive(c)
    s = await db.season_archive.find_one({"career_id": c["id"], "season": f"{y1}/{y2}"}, {"_id": 0})
    if not s:
        raise HTTPException(404, "That season isn't in your history")
    return s


def _tenure(c: dict, season: str, first: str | None) -> bool:
    return bool(first) and season >= first


async def _milestones(c: dict, arch: list) -> list:
    ms = []
    if arch:
        ms.append({"id": f"start-{arch[0]['season']}", "season": arch[0]["season"], "date": arch[0]["sources"][0]["game_date"], "title": f"FMCC starts following {arch[0]['club']}", "kind": "club", "link": f"/club-history?season={arch[0]['season']}"})
    divs = []
    for s in arch:
        for name in s["academy"]["debuts"]:
            r = next(r for r in s["squad"] if r["name"] == name)
            ms.append({"id": f"debut-{r['unique_id']}", "season": s["season"], "title": f"Homegrown debut: {name}", "kind": "academy", "unique_id": r["unique_id"]})
        for h in s["honours"]:
            ms.append({"id": f"honour-{s['season']}-{h.get('competition')}", "season": s["season"], "title": f"{'Promoted' if h['kind'] == 'promotion' else 'Won'}: {h.get('competition')}", "kind": "honour", "link": f"/club-history?season={s['season']}"})
        for m in s.get("save_milestones") or []:
            ms.append({"id": f"save-{s['season']}-{m.get('title')}", "season": s["season"], "title": m.get("title") or "Club milestone", "kind": "club", "date": m.get("date")})
        d = (s.get("league") or {}).get("division")
        if d and d not in divs:
            if divs:
                ms.append({"id": f"div-{s['season']}-{d}", "season": s["season"], "title": f"First season in {d}", "kind": "club", "link": f"/club-history?season={s['season']}"})
            divs.append(d)
    async for a in db.awards.find({"career_id": c["id"], "module": "breakout", "status": "official"}, {"_id": 0}):
        ms.append({"id": f"breakout-{a['award_key']}", "season": a["award_key"].split(":")[1], "title": f"Breakout Player: {a['name']}", "kind": "award", "unique_id": a["unique_id"]})
    pins = {p["id"]: p async for p in db.history_pins.find({"career_id": c["id"]}, {"_id": 0})}
    for m in ms:
        m["pinned"] = m["id"] in pins
    ms += [p | {"pinned": True, "kind": "pinned"} for p in pins.values() if p.get("custom")]
    return sorted(ms, key=lambda m: (m["season"], m.get("date") or ""), reverse=True)


@router.get("/cabinet")
async def cabinet(scope: str = "save"):
    c = await active_career()
    arch = await archive(c)
    first = arch[0]["season"] if arch else None
    hon = []
    for s in arch:
        for h in s["honours"]:
            hon.append(h | {"tenure": True, "link_season": s["season"]})
    if scope == "full":
        snap = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "history.honours": 1}, sort=[("save_no", -1)]) or {}
        for h in (snap.get("history") or {}).get("honours") or []:
            if (h.get("season") or "") < (first or ""):
                hon.append(h | {"kind": _honour_kind(h), "tenure": False, "pre_save": True})
    hon.sort(key=lambda h: h.get("season") or "", reverse=True)
    import awards_api
    tro = await awards_api.trophies()
    individual = [{"season": s["season"], **a} for s in arch for a in s["individual"]]
    done = [s for s in arch if s["status"] == "Completed"]
    ms = await _milestones(c, arch)
    return {"scope": scope, "latest": hon[0] if hon else None, "last_three": [_summary(s) for s in reversed(done[-3:])], "in_progress": _summary(arch[-1]) if arch and arch[-1]["status"] != "Completed" else None,
            "trophies": [h for h in hon if h["kind"] == "trophy"], "promotions": [h for h in hon if h["kind"] in ("promotion", "playoff")], "runner_up": [h for h in hon if h["kind"] == "runner_up"],
            "totals": {"trophies": sum(h["kind"] == "trophy" for h in hon), "promotions": sum(h["kind"] in ("promotion", "playoff") for h in hon), "runner_up": sum(h["kind"] == "runner_up" for h in hon)},
            "individual": individual, "fmcc_awards": tro, "timeline": ms[:8], "first_season": first}


@router.get("/milestones")
async def milestones():
    c = await active_career()
    return {"milestones": await _milestones(c, await archive(c))}


class PinIn(BaseModel):
    id: str | None = None
    title: str = Field("", max_length=120)
    note: str = Field("", max_length=400)
    season: str | None = Field(None, max_length=9)


@router.post("/pins")
async def pin(body: PinIn):
    c = await active_career()
    if body.id:
        await db.history_pins.update_one({"career_id": c["id"], "id": body.id}, {"$setOnInsert": {"career_id": c["id"], "id": body.id, "at": now_iso()}}, upsert=True)
        return {"ok": True}
    if not body.title.strip() or not body.season:
        raise HTTPException(422, "A pinned moment needs a title and a season")
    doc = {"career_id": c["id"], "id": f"pin-{new_id()}", "custom": True, "title": body.title.strip(), "note": body.note.strip(), "season": body.season, "at": now_iso()}
    await db.history_pins.insert_one(dict(doc))
    await audit(c["id"], "history pin", "history", f"Pinned moment: {doc['title']} ({doc['season']})")
    return {"ok": True, "id": doc["id"]}


@router.delete("/pins/{pid:path}")
async def unpin(pid: str):
    c = await active_career()
    r = await db.history_pins.delete_one({"career_id": c["id"], "id": pid})
    if not r.deleted_count:
        raise HTTPException(404, "That moment isn't pinned")
    return {"ok": True}


def _season_of(d: str | None) -> str | None:
    if not d or len(d) < 7:
        return None
    y = int(d[:4]) if int(d[5:7]) >= 7 else int(d[:4]) - 1
    return f"{y}/{str(y + 1)[2:]}"


def _progress(items: list, better) -> list:
    """Walk seasons in order; every time the record is broken, the new holder joins the list."""
    holders = []
    for it in items:
        if it["value"] is None:
            continue
        if not holders or better(it["value"], holders[-1]["value"]):
            holders.append(it)
    return list(reversed(holders))


def _rec(key, label, items, higher=True, unit=""):
    h = _progress(items, (lambda a, b: a > b) if higher else (lambda a, b: a < b))
    return {"key": key, "label": label, "unit": unit, "holder": h[0] if h else None, "previous": h[1:4], "available": bool(h)}


@router.get("/records")
async def records(scope: str = "league"):
    c = await active_career()
    arch = await archive(c)
    team, players, matches_r, transfers = [], [], [], []
    lg = [(s, s["league"]) for s in arch if s.get("league")]
    ev = lambda s, v, **k: {"season": s["season"], "value": v, "link": f"/club-history?season={s['season']}", **k}  # noqa: E731
    if scope == "league":
        team += [_rec("pts", "Most points", [ev(s, l["pts"]) for s, l in lg]), _rec("ppg", "Best points per game", [ev(s, round(l["pts"] / l["played"], 2) if l["played"] else None) for s, l in lg]),
                 _rec("gf", "Most goals", [ev(s, l["gf"]) for s, l in lg]), _rec("ga", "Fewest conceded", [ev(s, l["ga"]) for s, l in lg], higher=False)]
    allm = [m | {"season": s["season"]} for s in arch for m in s["matches"] if isinstance(m.get("score"), list) and len(m["score"]) == 2]
    if scope == "league":
        allm = [m for m in allm if not m.get("competition") or "league" in str(m["competition"]).lower()]

    def runs(pred, home=False):
        best, cur, start = None, 0, None
        for m in sorted(allm, key=lambda m: m["date"]):
            if home and not m.get("home"):
                continue
            if pred(m["score"][0], m["score"][1]):
                cur, start = cur + 1, start or m
                if not best or cur > best["value"]:
                    best = {"season": start["season"], "value": cur, "date": start["date"], "link": f"/matches?match={start['id']}"}
            else:
                cur, start = 0, None
        return [best] if best else []
    team += [_rec("cs", "Most clean sheets", [ev(s, sum(1 for m in allm if m["season"] == s["season"] and m["score"][1] == 0) if allm else None) for s in arch]),
             _rec("unbeaten", "Longest unbeaten run", runs(lambda a, b: a >= b), unit=" matches"), _rec("wins", "Longest winning run", runs(lambda a, b: a > b), unit=" matches"),
             _rec("home_unbeaten", "Longest home unbeaten run", runs(lambda a, b: a >= b, home=True), unit=" matches")]
    pl = lambda s, r, v: ev(s, v, unique_id=r["unique_id"], name=r["name"])  # noqa: E731
    for key, label, gk in [("appearances", "Most appearances", False), ("goals", "Most goals", False), ("assists", "Most assists", False), ("tackles", "Most tackles", False), ("duels_won", "Most duels won", False), ("clean_sheets", "Most clean sheets (goalkeepers)", True)]:
        season_items = [max([pl(s, r, r.get(key)) for r in s["squad"] if r.get(key) is not None and (not gk or "GK" in (r.get("positions") or []))] or [ev(s, None)], key=lambda x: x["value"] or 0) for s in arch]
        totals: dict = {}
        for s in arch:
            for r in s["squad"]:
                if r.get(key) is not None and (not gk or "GK" in (r.get("positions") or [])):
                    t = totals.setdefault(r["unique_id"], {"unique_id": r["unique_id"], "name": r["name"], "value": 0, "season": "Whole save", "link": None})
                    t["value"] += r[key]
        players.append(_rec(key, f"{label} in a season", season_items) | {"save": max(totals.values(), key=lambda t: t["value"], default=None)})
    debuts = [pl(s, r, r["age"]) for s in arch for r in s["squad"] if r["debut"] and r.get("age")]
    scorers = [pl(s, r, r["age"]) for s in arch for r in s["squad"] if (r.get("goals") or 0) > 0 and r.get("age")]
    players += [_rec("youngest_debut", "Youngest debutant", sorted(debuts, key=lambda x: x["season"]), higher=False, unit=" years"),
                _rec("youngest_scorer", "Youngest scorer", sorted(scorers, key=lambda x: x["season"]), higher=False, unit=" years"),
                _rec("match_goals", "Most goals in a match", [pl(s, r, r["best_match_goals"]) | {"link": f"/matches?match={r['best_match']}"} for s in arch for r in s["squad"] if r.get("best_match_goals")])]
    rated = [pl(s, r, r["avg_rating"]) for s in arch for r in s["squad"] if (r.get("minutes") or 0) >= MIN_RATE_MINUTES and r.get("avg_rating")]
    players.append(_rec("avg_rating", f"Best average rating (min {MIN_RATE_MINUTES} minutes)", sorted(rated, key=lambda x: x["season"])))
    mrow = lambda m, v: {"season": m["season"], "value": v, "date": m["date"], "name": f"{'vs' if m.get('home') else 'at'} {m['opponent']} {m['score'][0]}-{m['score'][1]}", "link": f"/matches?match={m['id']}"}  # noqa: E731
    by = lambda f: [mrow(m, f(m)) for m in sorted(allm, key=lambda m: m["date"])]  # noqa: E731
    matches_r += [_rec("big_win", "Biggest win", [x for x in by(lambda m: m["score"][0] - m["score"][1]) if x["value"] > 0], unit=" goal margin"),
                  _rec("heavy_loss", "Heaviest defeat", [x for x in by(lambda m: m["score"][1] - m["score"][0]) if x["value"] > 0], unit=" goal margin"),
                  _rec("high_score", "Highest-scoring match", by(lambda m: m["score"][0] + m["score"][1]), unit=" goals"),
                  _rec("attendance", "Highest attendance", [x for x in by(lambda m: m.get("attendance")) if x["value"]])]
    h2h: dict = {}
    for m in allm:
        o = h2h.setdefault(m["opponent"], {"opponent": m["opponent"], "p": 0, "w": 0, "d": 0, "l": 0})
        o["p"] += 1
        o["w" if m["score"][0] > m["score"][1] else "d" if m["score"][0] == m["score"][1] else "l"] += 1
    pool = (await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players.unique_id": 1, "players.name": 1, "players.club": 1, "players.last_move": 1}) or {}).get("players") or []
    club = arch[-1]["club"] if arch else None
    homegrown = {r["unique_id"] for s in arch for r in s["squad"] if r.get("homegrown")}
    buys = [{"season": _season_of(p["last_move"].get("date")), "value": p["last_move"]["fee"], "unique_id": p["unique_id"], "name": p["name"], "date": p["last_move"].get("date")} for p in pool if (p.get("last_move") or {}).get("fee") and p.get("club") == club]
    sales = [{"season": _season_of(p["last_move"].get("date")), "value": p["last_move"]["fee"], "unique_id": p["unique_id"], "name": p["name"], "date": p["last_move"].get("date")} for p in pool if (p.get("last_move") or {}).get("fee") and p["last_move"].get("from_club") == club]
    transfers += [_rec("fee_paid", "Record fee paid", sorted(buys, key=lambda x: x["date"] or ""), unit=" £"), _rec("fee_received", "Record fee received", sorted(sales, key=lambda x: x["date"] or ""), unit=" £"),
                  _rec("profit", "Highest profit on a sale", []), _rec("academy_sale", "Highest fee for an academy graduate", sorted([x for x in sales if x["unique_id"] in homegrown], key=lambda x: x["date"] or ""), unit=" £")]
    return {"scope": scope, "team": team, "players": players, "matches": matches_r, "h2h": sorted(h2h.values(), key=lambda o: -o["p"])[:8], "transfers": transfers, "min_minutes": MIN_RATE_MINUTES}


def _ranked(s: dict, key: str) -> list:
    ok = lambda r: r.get(key) is not None and (key != "avg_rating" or (r.get("minutes") or 0) >= MIN_RATE_MINUTES) and (key != "clean_sheets" or "GK" in (r.get("positions") or []))  # noqa: E731
    return sorted([{"unique_id": r["unique_id"], "name": r["name"], "value": r[key] + 0, "minutes": r["minutes"]} for r in s["squad"] if ok(r)], key=lambda r: -r["value"])


@router.get("/leaders")
async def leaders(season: str | None = None, mode: str = "season"):
    """Season: top five per stat. All-time: each season's leader (current season included), ranked."""
    c = await active_career()
    arch = await archive(c)
    s = next((x for x in arch if x["season"] == season), arch[-1] if arch else None)
    if not s:
        return {"mode": mode, "season": None, "seasons": [], "leaders": []}
    out = []
    for key, label, group in LEADERS:
        if mode == "alltime":
            rows = sorted([top[0] | {"season": x["season"], "current": x["status"] == "In Progress"} for x in arch if (top := _ranked(x, key))], key=lambda r: -r["value"])
        else:
            rows = _ranked(s, key)[:5]
        out.append({"key": key, "label": label, "group": group, "rows": rows, "available": bool(rows)})
    return {"mode": mode, "season": s["season"], "status": s["status"], "seasons": [x["season"] for x in reversed(arch)], "leaders": out,
            "completed": sum(x["status"] == "Completed" for x in arch), "min_minutes": MIN_RATE_MINUTES}


@router.get("/compare")
async def compare(a: str, b: str):
    c = await active_career()
    arch = {s["season"]: s for s in await archive(c)}
    if a not in arch or b not in arch:
        raise HTTPException(404, "Pick two seasons from your history")

    def facts(s):
        lg = s.get("league") or {}
        mins = sum(r["minutes"] or 0 for r in s["squad"])
        return {"season": s["season"], "status": s["status"], "division": lg.get("division"), "finish": lg.get("pos"), "ppg": round(lg["pts"] / lg["played"], 2) if lg.get("played") else None,
                "gd_pg": round(lg["gd"] / lg["played"], 2) if lg.get("played") else None, "squad_age": round(sum((r["age"] or 0) * (r["minutes"] or 0) for r in s["squad"]) / mins, 1) if mins else None,
                "academy_minutes": s["academy"]["homegrown_minutes"], "attendance": s["growth"]["attendance"], "spend": s["recruitment"]["spent"]}
    return {"a": facts(arch[a]), "b": facts(arch[b])}


class HofIn(BaseModel):
    unique_id: int
    note: str = Field("", max_length=300)


@router.get("/hall-of-fame")
async def hall_of_fame():
    c = await active_career()
    arch = await archive(c)
    out = []
    async for h in db.hall_of_fame.find({"career_id": c["id"]}, {"_id": 0}).sort("at", 1):
        seasons = [s | {"row": r} for s in arch for r in s["squad"] if r["unique_id"] == h["unique_id"]]
        honours = sorted({a for s in seasons for a in s["row"]["awards"]})
        best = []
        async for m in db.matches.find({"career_id": c["id"], "players": {"$elemMatch": {"unique_id": h["unique_id"], "team": "us"}}}, {"_id": 0, "id": 1, "date": 1, "opponent": 1, "score": 1, "players.$": 1}).limit(200):
            p = m["players"][0]
            best.append({"id": m["id"], "date": m["date"], "opponent": m["opponent"], "score": m.get("score"), "rating": p.get("rating"), "goals": p.get("goals")})
        best = sorted(best, key=lambda m: -(m["rating"] or 0))[:3]
        out.append({"unique_id": h["unique_id"], "name": h["name"], "note": h.get("note"), "inducted": h["at"],
                    "seasons": [{"season": s["season"], "apps": s["row"]["appearances"], "goals": s["row"]["goals"], "assists": s["row"]["assists"], "avg_rating": s["row"]["avg_rating"]} for s in seasons],
                    "totals": {k: sum((s["row"].get(k) or 0) for s in seasons) for k in ("appearances", "goals", "assists", "minutes")}, "honours": honours, "defining_matches": best})
    return {"members": out}


@router.post("/hall-of-fame")
async def induct(body: HofIn):
    c = await active_career()
    arch = await archive(c)
    r = next((r for s in arch for r in s["squad"] if r["unique_id"] == body.unique_id), None)
    if not r:
        raise HTTPException(404, "Only players who have played for your club in this save can be inducted")
    await db.hall_of_fame.update_one({"career_id": c["id"], "unique_id": body.unique_id}, {"$setOnInsert": {"career_id": c["id"], "unique_id": body.unique_id, "name": r["name"], "note": body.note, "at": now_iso()}}, upsert=True)
    await audit(c["id"], "hall of fame", "history", f"{r['name']} inducted into the Hall of Fame")
    return {"ok": True, "name": r["name"]}


@router.delete("/hall-of-fame/{uid}")
async def remove_hof(uid: int):
    c = await active_career()
    r = await db.hall_of_fame.delete_one({"career_id": c["id"], "unique_id": uid})
    if not r.deleted_count:
        raise HTTPException(404, "That player isn't in the Hall of Fame")
    return {"ok": True}


@router.get("/players")
async def club_players():
    """Everyone who has played for the club in this save (for Hall of Fame picking)."""
    c = await active_career()
    seen: dict = {}
    for s in await archive(c):
        for r in s["squad"]:
            if r.get("appearances"):
                t = seen.setdefault(r["unique_id"], {"unique_id": r["unique_id"], "name": r["name"], "apps": 0, "goals": 0})
                t["apps"] += r["appearances"] or 0
                t["goals"] += r["goals"] or 0
    return {"players": sorted(seen.values(), key=lambda p: -p["apps"])}



def _fmt(v, unit: str) -> str:
    if unit == " £":
        return f"£{v:,.0f}"
    return f"{v}{unit}"


def _who(h: dict) -> str:
    return h.get("name") or h["season"]


async def check_records(c: dict) -> None:
    """Bell notice when a club record changes hands. The first check only remembers today's holders."""
    from notify_api import _add
    found = {}
    for scope in ("league", "all"):
        r = await records(scope)
        cats = ["team", "players", "matches", "transfers"] if scope == "league" else ["team", "matches"]
        for cat in cats:
            for rec in r[cat]:
                if rec["holder"]:
                    found[f"{scope}:{rec['key']}"] = (rec, scope)
    state = await db.record_state.find_one({"career_id": c["id"]}, {"_id": 0}) or {}
    seen = state.get("holders")
    sig = lambda h: f"{h.get('unique_id', '')}|{h['season']}|{h.get('date', '')}"  # noqa: E731
    now = {k: sig(rec["holder"]) for k, (rec, _) in found.items()}
    if seen is not None:
        snap = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "game_date": 1}, sort=[("save_no", -1)]) or {}
        for k, (rec, scope) in found.items():
            if k not in seen or seen[k] == now[k]:
                continue
            h = rec["holder"]
            label = rec["label"] + (" (all competitions)" if scope == "all" else "")
            prev = rec["previous"][0] if rec["previous"] else None
            text = f"{_fmt(h['value'], rec['unit'])} in {h['season']}." + (f" Previous record: {_who(prev)}, {_fmt(prev['value'], rec['unit'])}." if prev else " First time this record has been set.")
            link = f"/squad?player={h['unique_id']}" if h.get("unique_id") else h.get("link") or "/club-history?tab=records"
            await _add(c["id"], "record", f"record:{k}:{now[k]}", f"New club record: {label}" + (f" by {h['name']}" if h.get("name") else ""), text, snap.get("game_date") or "", link)
    await db.record_state.update_one({"career_id": c["id"]}, {"$set": {"career_id": c["id"], "holders": now}}, upsert=True)
