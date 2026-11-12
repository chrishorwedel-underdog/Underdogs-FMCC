from typing import Literal

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
    c = await active_career()
    snap = await latest_snapshot(c["id"])
    rules = await current_rules(c["id"], "elite")
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    month = snap["game_date"][:7]
    items_total = {"queued": 0, "skipped_duplicates": 0, "not_qualified": 0}
    for n in await active_nominees(c["id"], "elite"):
        x = ctxs.get(n["unique_id"])
        r = RE.first_match(rules["data"]["rules"], x) if x else None
        if not r:
            items_total["not_qualified"] += 1
            continue
        award_id = f"elite-{month}"
        if await db.changes.find_one({"key": f"{c['id']}:elite:{award_id}:{x['unique_id']}:{r['action']['target']}"}, {"_id": 1}):
            items_total["skipped_duplicates"] += 1
            continue
        delta = RE.capped(x[r["action"]["target"]], RE.roll(r, f"{c['id']}:{award_id}:{x['unique_id']}"), r["max_value"])
        await _award(c, f"elite:{month}:{x['unique_id']}", "elite", x, r, rules["version"], "awarded", delta)
        res = await queue_changes(c, "elite", award_id, [{"unique_id": x["unique_id"], "name": x["name"], "field": r["action"]["target"], "delta": delta}])
        items_total["queued"] += res["queued"]
        items_total["auto_applied"] = items_total.get("auto_applied") or res["auto_applied"]
        items_total["skipped_duplicates"] += res["skipped_duplicates"]
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


# ---------- Annual Breakout ----------
@router.get("/breakout")
async def breakout():
    c = await active_career()
    snap = await latest_snapshot(c["id"])
    rules = await current_rules(c["id"], "breakout")
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    noms = {n["unique_id"]: n for n in await active_nominees(c["id"], "breakout")}
    reviews = await latest_awards(c["id"], "breakout", f"breakout:{snap['season']}:")
    cands = []
    for x in ctxs.values():
        r = RE.first_match(rules["data"]["rules"], x)
        if r or x["unique_id"] in noms or x["unique_id"] in reviews:
            rv = reviews.get(x["unique_id"])
            cands.append({k: x[k] for k in ("unique_id", "name", "age", "minutes", "avg_rating", "ca_growth", "goals", "assists")} |
                         {"category": r["name"] if r else None, "rule_id": r["id"] if r else None, "nominated": x["unique_id"] in noms,
                          "nomination_note": noms.get(x["unique_id"], {}).get("note"), "review": {k: rv[k] for k in ("status", "category", "revision", "revisions", "note", "award_key")} if rv else None})
    cands.sort(key=lambda r: (r["category"] is None, -(r["avg_rating"] or 0)))
    month = int(snap["game_date"][5:7])
    return {"season": snap["season"], "season_over": month in (5, 6), "rules": [{"id": r["id"], "name": r["name"]} for r in rules["data"]["rules"] if r["enabled"]],
            "candidates": cands, "rules_version": rules["version"]}


@router.post("/breakout/nominations")
async def breakout_nominate(body: NominateIn):
    c = await active_career()
    return await _nominate(c, "breakout", body.unique_id, "active", body.note)


class ReviewIn(BaseModel):
    unique_id: int
    rule_id: str | None = None
    decision: Literal["provisional", "rejected"]
    note: str = Field("", max_length=300)


@router.post("/breakout/review")
async def breakout_review(body: ReviewIn):
    """Provisional reviews are append-only revisions; nothing is written to the game yet."""
    c = await active_career()
    snap = await latest_snapshot(c["id"])
    rules = await current_rules(c["id"], "breakout")
    x = next((p for p in await own_contexts(c) if p["unique_id"] == body.unique_id), None)
    if not x:
        raise HTTPException(404, "This player is no longer in your squad")
    key = f"breakout:{snap['season']}:{x['unique_id']}"
    cur = (await latest_awards(c["id"], "breakout", key)).get(x["unique_id"])
    if cur and cur["status"] == "official":
        raise HTTPException(409, "This award is already official and can't be changed")
    r = next((r for r in rules["data"]["rules"] if r["id"] == body.rule_id), None) if body.rule_id else RE.first_match(rules["data"]["rules"], x)
    if body.decision == "provisional" and not r:
        raise HTTPException(422, "Pick an award category")
    rev = await _award(c, key, "breakout", x, r, rules["version"], body.decision, note=body.note)
    return {"revision": rev}


@router.post("/breakout/finalise", dependencies=need("breakout"))
async def breakout_finalise():
    """Make provisional awards official, roll the reward within the rule's range and queue it as a game change."""
    c = await active_career()
    snap = await latest_snapshot(c["id"])
    rules = await current_rules(c["id"], "breakout")
    by_id = {r["id"]: r for r in rules["data"]["rules"]}
    ctxs = {x["unique_id"]: x for x in await own_contexts(c)}
    done = 0
    for uid, aw in (await latest_awards(c["id"], "breakout", f"breakout:{snap['season']}:")).items():
        if aw["status"] != "provisional" or uid not in ctxs or aw["rule_id"] not in by_id:
            continue
        r, x = by_id[aw["rule_id"]], ctxs[uid]
        delta = RE.capped(x[r["action"]["target"]], RE.roll(r, f"{c['id']}:{aw['award_key']}"), r["max_value"])
        await _award(c, aw["award_key"], "breakout", x, r, rules["version"], "official", delta, aw.get("note", ""))
        await queue_changes(c, "breakout", aw["award_key"], [{"unique_id": uid, "name": x["name"], "field": r["action"]["target"], "delta": delta}])
        done += 1
    await audit(c["id"], "breakout picks official", "breakout", f"{done} Breakout pick(s) made official for {snap['season']}")
    return {"official": done}


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
