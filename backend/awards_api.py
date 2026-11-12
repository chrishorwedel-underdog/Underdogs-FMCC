from datetime import datetime

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

import rules_engine as RE
from features_api import need
from changes_api import queue_changes
from core import db, active_career, latest_snapshot, now_iso, new_id, next_revision, audit
from population import contexts, own_contexts
from rules_api import current as current_rules, active_nominees, save_version, Scope

router = APIRouter(prefix="/api")


class NominateIn(BaseModel):
    unique_id: int
    note: str = Field("", max_length=300)


async def _nominate(c: dict, module: str, uid: int, status: str, note: str):
    snap = await latest_snapshot(c["id"])
    p = next((x for x in snap["players"] if x["unique_id"] == uid), None)
    if not p:
        raise HTTPException(404, "This player is no longer in your squad")
    rev = await next_revision("nominations", {"career_id": c["id"], "module": module, "unique_id": uid})
    await db.nominations.insert_one({"id": new_id(), "career_id": c["id"], "module": module, "unique_id": uid, "name": p["name"], "revision": rev,
                                     "status": status, "note": note, "at": now_iso(), "game_date": snap["game_date"], "season": snap["season"]})
    return {"revision": rev}


def _rule_text(r: dict) -> str:
    a = r["action"]
    return f"{'Raise' if a['min'] >= 0 else 'Lower'} {a['target'].upper()} by {abs(a['min'])} to {abs(a['max'])}"


# ---------- Elite Training ----------
@router.get("/elite")
async def elite():
    c = await active_career()
    rules = (await current_rules(c["id"], "elite"))
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    noms = [n for n in await active_nominees(c["id"], "elite") if n["unique_id"] in ctxs]
    evidence = {}
    async for s in db.snapshots.find({"career_id": c["id"]}, {"_id": 0, "game_date": 1, "players.unique_id": 1, "players.training_rating": 1}).sort("save_no", 1):
        for p in s["players"]:
            evidence.setdefault(p["unique_id"], []).append({"date": s["game_date"], "rating": p.get("training_rating")})
    out = []
    for n in noms:
        x = ctxs[n["unique_id"]]
        r = RE.first_match(rules["data"]["rules"], x)
        out.append(n | {"age": x["age"], "training_rating": x["training_rating"], "ca_growth": x["ca_growth"],
                        "evidence": evidence.get(n["unique_id"], [])[-8:], "rule": r["name"] if r else None, "preview": _rule_text(r) if r else None})
    nominated = {n["unique_id"] for n in noms}
    suggestions = sorted([x for x in ctxs.values() if x["unique_id"] not in nominated and x["age"] <= 21], key=lambda x: -(x["training_rating"] or 0))[:5]
    return {"nominees": out, "suggestions": [{k: s[k] for k in ("unique_id", "name", "age", "training_rating")} for s in suggestions],
            "rules_version": rules["version"]}


@router.post("/elite/nominations")
async def elite_nominate(body: NominateIn):
    c = await active_career()
    return await _nominate(c, "elite", body.unique_id, "active", body.note)


@router.post("/elite/nominations/{uid}/withdraw")
async def elite_withdraw(uid: int):
    c = await active_career()
    return await _nominate(c, "elite", uid, "withdrawn", "Withdrawn")


@router.post("/elite/queue", dependencies=need("elite"))
async def elite_queue():
    """Work out PA boosts for nominees under the current rules and queue them as game changes."""
    return await run_elite(await active_career())


async def auto_elite(c: dict) -> dict | None:
    """Each Elite Training session (January and September saves) runs once, automatically, for everyone nominated."""
    if "elite" in __import__("features_api").off(c):
        return None
    snap = await latest_snapshot(c["id"])
    if not snap or int(snap["game_date"][5:7]) not in (1, 9) or c.get("elite_session_done") == snap["game_date"][:7]:
        return None
    await db.careers.update_one({"id": c["id"]}, {"$set": {"elite_session_done": snap["game_date"][:7]}})
    res = await run_elite(c)
    if res["queued"]:
        from notify_api import _add
        await _add(c["id"], "elite", f"elite-session:{snap['game_date'][:7]}", f"Elite Training session finished: {res['queued']} player(s) improved",
                   "See the summary on Home and in Elite Training.", snap["game_date"])
    return res


async def run_elite(c: dict) -> dict:
    snap = await latest_snapshot(c["id"])
    rules = await current_rules(c["id"], "elite")
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    month = snap["game_date"][:7]
    items_total = {"queued": 0, "skipped_duplicates": 0, "not_qualified": 0, "auto_applied": False}
    items = []
    award_id = f"elite-{month}"
    for n in await active_nominees(c["id"], "elite"):
        x = ctxs.get(n["unique_id"])
        r = RE.first_match(rules["data"]["rules"], x) if x else None
        if not r:
            items_total["not_qualified"] += 1
            continue
        if await db.changes.find_one({"key": f"{c['id']}:elite:{award_id}:{x['unique_id']}:{r['action']['target']}"}, {"_id": 1}):
            items_total["skipped_duplicates"] += 1
            continue
        delta = RE.capped(x[r["action"]["target"]], RE.roll(r, f"{c['id']}:{award_id}:{x['unique_id']}"), r["max_value"])
        await _award(c, f"elite:{month}:{x['unique_id']}", "elite", x, r, rules["version"], "awarded", delta)
        items.append({"unique_id": x["unique_id"], "name": x["name"], "field": r["action"]["target"], "delta": delta})
    if items:
        res = await queue_changes(c, "elite", award_id, items)
        items_total |= {"queued": res["queued"], "auto_applied": res["auto_applied"], "skipped_duplicates": items_total["skipped_duplicates"] + res["skipped_duplicates"]}
    return items_total


async def _award(c, award_key, module, x, rule, rules_version, status, delta=None, note=""):
    rev = await next_revision("awards", {"career_id": c["id"], "award_key": award_key})
    try:
        await db.awards.insert_one({"id": new_id(), "career_id": c["id"], "award_key": award_key, "module": module, "revision": rev,
                                    "unique_id": x["unique_id"], "name": x["name"], "rule_id": rule["id"] if rule else None,
                                    "category": rule["name"] if rule else None, "rules_version": rules_version, "status": status,
                                    "delta": delta, "field": rule["action"]["target"] if rule else None, "note": note, "at": now_iso()})
    except DuplicateKeyError:
        raise HTTPException(409, "This award was changed at the same moment. Reload and try again.")
    return rev


async def latest_awards(career_id: str, module: str, prefix: str) -> dict:
    pipeline = [{"$match": {"career_id": career_id, "module": module, "award_key": {"$regex": f"^{prefix}"}}}, {"$sort": {"revision": -1}},
                {"$group": {"_id": "$award_key", "doc": {"$first": "$$ROOT"}, "revisions": {"$sum": 1}}},
                {"$replaceRoot": {"newRoot": {"$mergeObjects": ["$doc", {"revisions": "$revisions"}]}}}, {"$project": {"_id": 0}}]
    return {d["unique_id"]: d async for d in db.awards.aggregate(pipeline)}


# ---------- Annual Breakout (automatic) ----------
MIN_MINUTES = 900


async def _past_winners(career_id: str) -> dict:
    return {d["unique_id"]: d async for d in db.awards.find({"career_id": career_id, "module": "breakout", "status": "official"}, {"_id": 0})}


async def _standings(c: dict) -> dict:
    """First-team players (22+) ranked against their teammates by FMCC's position-fair season grade."""
    import stats_model as sm
    snap = await latest_snapshot(c["id"])
    data = await sm.build(c)
    grades = {x["unique_id"]: x for x in data["players"] if x.get("own")}
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    winners = await _past_winners(c["id"])
    rows = []
    for uid, x in ctxs.items():
        g = grades.get(uid) or {}
        why = ("Under 21: not first team" if (x["age"] or 0) <= 21 else "Already won it" if uid in winners else
               f"Under {MIN_MINUTES} minutes" if (x["minutes"] or 0) < MIN_MINUTES else "No season grade yet" if g.get("grade_global") is None else None)
        rows.append({"unique_id": uid, "name": x["name"], "age": x["age"], "minutes": x["minutes"], "avg_rating": x["avg_rating"],
                     "position": (g.get("cohort") or ""), "grade": g.get("grade_global"), "eligible": why is None, "reason": why})
    ok = sorted([r for r in rows if r["eligible"]], key=lambda r: (-(r["grade"] or 0), -(r["avg_rating"] or 0)))
    n = len(ok)
    for i, r in enumerate(ok):
        r["rank"] = i + 1
        r["teammate_pct"] = round(100 * (n - 1 - i) / (n - 1)) if n > 1 else 100
    rest = sorted([r for r in rows if not r["eligible"]], key=lambda r: -(r["grade"] or 0))
    return {"snap": snap, "ctxs": ctxs, "ranked": ok, "ineligible": rest, "winners": winners}


async def auto_breakout(c: dict) -> dict | None:
    """At season end (May/June save), pick the top eligible teammate and apply the reward automatically. Once per season, once per player career."""
    if "breakout" in __import__("features_api").off(c):
        return None
    snap = await latest_snapshot(c["id"])
    if not snap or int(snap["game_date"][5:7]) not in (5, 6):
        return None
    if await db.awards.find_one({"career_id": c["id"], "module": "breakout", "status": "official", "award_key": {"$regex": f"^breakout:{snap['season']}:"}}, {"_id": 1}):
        return None
    s = await _standings(c)
    if not s["ranked"]:
        return None
    w = s["ranked"][0]
    x = s["ctxs"][w["unique_id"]]
    rules = await current_rules(c["id"], "breakout")
    on = [r for r in rules["data"]["rules"] if r["enabled"]]
    r = RE.first_match(on, x) or (on[0] if on else None)
    if not r:
        return None
    key = f"breakout:{snap['season']}:{x['unique_id']}"
    delta = RE.capped(x[r["action"]["target"]], RE.roll(r, f"{c['id']}:{key}"), r["max_value"])
    await _award(c, key, "breakout", x, r, rules["version"], "official", delta, f"Season grade {w['grade']}")
    res = await queue_changes(c, "breakout", key, [{"unique_id": x["unique_id"], "name": x["name"], "field": r["action"]["target"], "delta": delta}])
    await audit(c["id"], "breakout winner", "breakout", f"{x['name']} is Breakout Player of {snap['season']} (grade {w['grade']}), applied automatically")
    from notify_api import _add
    await _add(c["id"], "breakout", f"breakout-win:{snap['season']}", f"{x['name']} is your Breakout Player of {snap['season']}",
               f"Best season among your first-team players (grade {w['grade']}). His reward was {'applied to your save' if res.get('auto_applied') else 'added to Game changes for your review'}.", snap["game_date"])
    return {"unique_id": x["unique_id"], "name": x["name"]}


@router.get("/breakout")
async def breakout():
    c = await active_career()
    await auto_breakout(c)
    s = await _standings(c)
    snap = s["snap"]
    pool = {**{x["unique_id"]: x for x in s["ranked"]}}
    this = next((w for w in s["winners"].values() if w["award_key"].startswith(f"breakout:{snap['season']}:")), None)
    past = sorted([{"season": w["award_key"].split(":")[1], "unique_id": w["unique_id"], "name": w["name"], "note": w.get("note")} for w in s["winners"].values()], key=lambda w: w["season"], reverse=True)
    return {"season": snap["season"], "season_over": int(snap["game_date"][5:7]) in (5, 6), "min_minutes": MIN_MINUTES,
            "winner": {"unique_id": this["unique_id"], "name": this["name"], "note": this.get("note")} if this else None,
            "leader": s["ranked"][0] if s["ranked"] and not this else None, "standings": s["ranked"], "ineligible": s["ineligible"], "past": past, "_n": len(pool)}


# ---------- Home celebration cards (general terms only; true CA/PA never shown) ----------
def _size(delta) -> str:
    d = abs(delta or 0)
    return "a small" if d <= 2 else "a solid" if d <= 5 else "a big"


def _benefit(field: str, delta) -> str:
    what = "potential (how good he can become)" if field == "pa" else "current ability (how good he is now)"
    return f"{_size(delta).capitalize()} boost to his {what}"


@router.get("/celebrations")
async def celebrations():
    c = await active_career()
    snap = await latest_snapshot(c["id"])
    if not snap:
        return {"cards": []}
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    cards, gd = [], snap["game_date"]
    months_since = lambda ym: (int(gd[:4]) - int(ym[:4])) * 12 + int(gd[5:7]) - int(ym[5:7])  # noqa: E731
    bo = await db.awards.find_one({"career_id": c["id"], "module": "breakout", "status": "official"}, {"_id": 0}, sort=[("at", -1)])
    if bo:
        season = bo["award_key"].split(":")[1]
        end_year = f"20{season[5:7]}" if len(season) >= 7 else gd[:4]
        if months_since(f"{end_year}-05") <= 4:
            x = ctxs.get(bo["unique_id"]) or {}
            cards.append({"id": f"breakout-{season}", "kind": "breakout", "title": f"{bo['name']} is your Breakout Player of {season}", "unique_id": bo["unique_id"],
                          "stats": {k: x.get(k) for k in ("appearances", "minutes", "goals", "assists", "avg_rating")}, "note": bo.get("note"),
                          "reward": _benefit(bo.get("field") or "pa", bo.get("delta")) + ", already applied to your save."})
    last = await db.awards.find_one({"career_id": c["id"], "module": "elite", "status": "awarded"}, {"_id": 0, "award_key": 1}, sort=[("at", -1)])
    if last:
        ym = last["award_key"].split(":")[1]
        if months_since(ym) <= 2:
            rows = await db.awards.find({"career_id": c["id"], "module": "elite", "status": "awarded", "award_key": {"$regex": f"^elite:{ym}:"}}, {"_id": 0}).to_list(50)
            label = datetime.strptime(ym, "%Y-%m").strftime("%B %Y")
            cards.append({"id": f"elite-{ym}", "kind": "elite", "title": f"Elite Training session finished ({label})",
                          "players": [{"unique_id": r["unique_id"], "name": r["name"], "age": (ctxs.get(r["unique_id"]) or {}).get("age"),
                                       "benefit": _benefit(r.get("field") or "pa", r.get("delta")), "category": r.get("category")} for r in rows],
                          "summary": f"{len(rows)} player{'s' if len(rows) != 1 else ''} earned a development boost from their training. It's already in your save."})
    return {"cards": cards}


@router.get("/awards/{award_key}/history")
async def award_history(award_key: str):
    c = await active_career()
    return await db.awards.find({"career_id": c["id"], "award_key": award_key}, {"_id": 0, "delta": 0}).sort("revision", -1).to_list(50)


# ---------- Dynamic Potential (values never shown) ----------
@router.get("/dp/scope")
async def dp():
    c = await active_career()
    rules = await current_rules(c["id"], "dp")
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players.nationality": 1, "players.league": 1}) or {"players": []}
    nations, leagues = {}, {}
    for p in pool["players"]:
        nations[p["nationality"]] = nations.get(p["nationality"], 0) + 1
        leagues[p["league"]] = leagues.get(p["league"], 0) + 1
    scope = rules["data"]["scope"]
    covered = await contexts(c, scope)
    runs = await db.audit.find({"career_id": c["id"], "source": "dp", "action": "run"}, {"_id": 0}).sort("at", -1).limit(5).to_list(5)
    return {"scope": scope, "caps": rules["data"]["caps"], "version": rules["version"], "covered": len(covered),
            "covered_leagues": len(scope["leagues"]), "covered_nations": len(scope["nations"]),
            "nations": [{"name": k, "count": v} for k, v in sorted(nations.items())], "leagues": [{"name": k, "count": v} for k, v in sorted(leagues.items())],
            "runs": runs}


class ScopeIn(BaseModel):
    scope: Scope
    expected_version: int


@router.put("/dp/scope")
async def dp_scope(body: ScopeIn):
    c = await active_career()
    cur = await current_rules(c["id"], "dp")
    data = dict(cur["data"], scope=body.scope.model_dump())
    doc = await save_version(c["id"], "dp", data, body.expected_version, "Changed who it applies to")
    return {"version": doc["version"]}


@router.get("/dp/review")
async def dp_review():
    """Who is included, grouped by league and club. Never whether a player goes up or down."""
    c = await active_career()
    rules = await current_rules(c["id"], "dp")
    groups = {}
    for x in await contexts(c, rules["data"]["scope"]):
        groups.setdefault(x["league"], {}).setdefault(x["club"], []).append({"unique_id": x["unique_id"], "name": x["name"]})
    return [{"league": lg, "clubs": [{"club": cl, "players": ps} for cl, ps in sorted(clubs.items())]} for lg, clubs in sorted(groups.items())]


class RunIn(BaseModel):
    exclude_ids: list[int] = Field(default_factory=list, max_length=20000)
    exclude_clubs: list[str] = Field(default_factory=list, max_length=2000)


@router.post("/dp/run", dependencies=need("dp"))
async def dp_run(body: RunIn):
    c = await active_career()
    snap = await latest_snapshot(c["id"])
    rules = await current_rules(c["id"], "dp")
    caps = rules["data"]["caps"]
    excl_ids, excl_clubs = set(body.exclude_ids), set(body.exclude_clubs)
    items, leagues = [], set()
    for x in await contexts(c, rules["data"]["scope"]):
        if x["unique_id"] in excl_ids or x["club"] in excl_clubs or len(items) >= caps["max_players"]:
            continue
        r = RE.first_match(rules["data"]["rules"], x)
        if not r:
            continue
        delta = RE.roll(r, f"{c['id']}:dp:{snap['season']}:{x['unique_id']}")
        delta = max(-caps["max_pa_change"], min(caps["max_pa_change"], delta))
        delta = RE.capped(x[r["action"]["target"]], delta, r["max_value"])
        items.append({"unique_id": x["unique_id"], "name": x["name"], "club": x["club"], "field": r["action"]["target"], "delta": delta})
        leagues.add(x["league"])
    res = await queue_changes(c, "dp", f"dp-{snap['season']}", items, hidden=True)
    summary = f"Dynamic Potential queued: {res['queued']} players in {', '.join(sorted(leagues)) or 'no leagues'}"
    await audit(c["id"], "run", "dp", summary, hidden=False)
    return res | {"summary": summary}
