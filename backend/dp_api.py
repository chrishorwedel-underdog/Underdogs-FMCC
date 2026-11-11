"""Dynamic Potential, rebuilt to the Underdog FM rulesheet: winter and season-end reviews, editable settings (one set for
all careers), review records that never show real CA or PA, and automatic apply with review exceptions."""
from datetime import date
from typing import Literal

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import dp_engine as E
from changes_api import queue_changes, start_batch
from core import db, active_career, latest_snapshot, now_iso, new_id, audit
from features_api import need
from population import contexts
from rules_api import current as current_rules

router = APIRouter(prefix="/api/dp")
HIDE = {"_id": 0, "career_id": 0}


async def settings_doc() -> dict:
    d = await db.dp_settings.find_one({}, {"_id": 0}, sort=[("version", -1)])
    return d or {"version": 0, "data": E.defaults(), "note": "Rulesheet defaults", "at": None}


def _diff(data: dict) -> list:
    return [k for k in E.SECTIONS if data.get(k) != E.DEFAULTS[k]]


@router.get("/settings")
async def get_settings():
    d = await settings_doc()
    hist = await db.dp_settings.find({}, {"_id": 0, "data": 0}).sort("version", -1).to_list(30)
    return d | {"defaults": E.DEFAULTS, "changed": _diff(d["data"]), "history": hist, "labels": {"positions": E.POS_LABEL, "metrics": E.METRIC_LABEL}}


async def _save(data: dict, note: str) -> dict:
    try:
        errs = E.validate(data)
    except (KeyError, IndexError, TypeError, ValueError, AttributeError) as exc:
        errs = [f"Settings are incomplete or have a wrong value ({type(exc).__name__}: {exc})"]
    if errs:
        raise HTTPException(422, "; ".join(errs))
    cur = await settings_doc()
    doc = {"version": cur["version"] + 1, "data": data, "note": note[:120], "at": now_iso()}
    await db.dp_settings.insert_one(dict(doc))
    return {"version": doc["version"], "changed": _diff(data)}


class SettingsIn(BaseModel):
    data: dict
    note: str = Field("Edited settings", max_length=120)


@router.put("/settings")
async def put_settings(body: SettingsIn):
    return await _save(body.data, body.note)


@router.post("/settings/reset")
async def reset_settings(section: str | None = None):
    if section and section not in E.SECTIONS:
        raise HTTPException(404, "Unknown section")
    data = (await settings_doc())["data"]
    data = E.defaults() if not section else data | {section: E.defaults()[section]}
    return await _save(data, f"Reset {section or 'everything'} to the rulesheet")


@router.post("/settings/restore/{version}")
async def restore_settings(version: int):
    d = await db.dp_settings.find_one({"version": version}, {"_id": 0})
    if not d and version != 0:
        raise HTTPException(404, "That settings version isn't in the history")
    return await _save((d or {"data": E.defaults()})["data"], f"Restored version {version}")


def _suggest_winter(season: str) -> str:
    return f"{int(season.split('/')[0]) + 1}-01-01"


async def _season(c: dict) -> dict:
    snap = await latest_snapshot(c["id"])
    s = await db.dp_seasons.find_one({"career_id": c["id"], "season": snap["season"]}, HIDE)
    if not s:
        s = {"season": snap["season"], "winter_date": _suggest_winter(snap["season"]), "suggested": True, "ages": {}, "at": now_iso()}
        await db.dp_seasons.insert_one(dict(s) | {"career_id": c["id"]})
    return s | {"game_date": snap["game_date"]}


class SeasonIn(BaseModel):
    winter_date: date


@router.put("/season")
async def set_season(body: SeasonIn):
    c = await active_career()
    s = await _season(c)
    if await db.dp_records.count_documents({"career_id": c["id"], "season": s["season"]}):
        raise HTTPException(409, "The season's halves are fixed once a review has run")
    await db.dp_seasons.update_one({"career_id": c["id"], "season": s["season"]}, {"$set": {"winter_date": body.winter_date.isoformat(), "suggested": False}})
    return {"ok": True}


async def _latest_records(cid: str, season: str, kind: str | None = None) -> list:
    m = {"career_id": cid, "season": season} | ({"kind": kind} if kind else {})
    pipe = [{"$match": m}, {"$sort": {"revision": -1}}, {"$group": {"_id": {"k": "$kind", "u": "$unique_id"}, "d": {"$first": "$$ROOT"}}}]
    return [{k: v for k, v in x["d"].items() if k not in ("_id", "career_id")} async for x in db.dp_records.aggregate(pipe)]


@router.get("")
async def overview():
    c = await active_career()
    s = await _season(c)
    recs = await _latest_records(c["id"], s["season"])
    rules = await current_rules(c["id"], "dp")
    covered = len(await contexts(c, rules["data"]["scope"]))
    done = {k: [r for r in recs if r["kind"] == k] for k in ("winter", "season_end")}
    stage = "season_done" if done["season_end"] else "winter_done" if done["winter"] else "before_winter"
    cur = done["season_end"] or done["winter"]
    counts = {"rising": sum(r["change"] > 0 and r["status"] in ("auto", "approved") for r in cur), "falling": sum(r["change"] < 0 and r["status"] in ("auto", "approved") for r in cur),
              "steady": sum(r["status"] in ("none", "rejected", "superseded") for r in cur),
              "held": sum(r["status"] in ("held", "flag") for r in cur), "review": sum(r["status"] == "needs_review" for r in cur)}
    st = await settings_doc()
    return {"season": s["season"], "game_date": s["game_date"], "winter_date": s["winter_date"], "winter_suggested": s.get("suggested", False), "stage": stage,
            "next_review": "winter" if stage == "before_winter" else "season_end" if stage == "winter_done" else None, "counts": counts, "covered": covered,
            "reviewed": {k: len(v) for k, v in done.items()}, "settings_version": st["version"], "settings_changed": _diff(st["data"]), "scope": rules["data"]["scope"]}


async def _evidence(c: dict, s: dict, kind: str) -> tuple:
    """Season evidence per player: minutes (senior/youth), halves split at the winter date, half ratings. Ages fixed at season start."""
    snaps = await db.snapshots.find({"career_id": c["id"], "season": s["season"]}, {"_id": 0, "game_date": 1, "players.unique_id": 1, "players.minutes": 1,
                                                                                    "players.avg_rating": 1, "players.age": 1}).sort("save_no", 1).to_list(None)
    first = {}
    for sn in snaps:
        if sn["game_date"] <= s["winter_date"]:
            for p in sn["players"]:
                first[p["unique_id"]] = (p.get("minutes") or 0, p.get("avg_rating"))
    ages = dict(s.get("ages") or {})
    for sn in snaps[:1]:
        for p in sn["players"]:
            ages.setdefault(str(p["unique_id"]), p["age"])
    return first, ages


def _ev(x: dict, first: dict, ages: dict, kind: str, h_rating) -> dict:
    mins = x.get("minutes") or 0
    youth = x.get("youth_minutes") or 0
    known = x["unique_id"] in first or kind == "winter"
    h1, r1 = first.get(x["unique_id"], (mins, x.get("avg_rating"))) if known else (None, None)
    h2 = mins - h1 if known else None
    r2 = None
    if known and h2 and r1 is not None and x.get("avg_rating") is not None and kind == "season_end":
        r2 = round((x["avg_rating"] * mins - r1 * h1) / h2, 2) if h2 > 0 else None
    return {"minutes": mins, "senior_minutes": mins - youth, "youth_minutes": youth, "senior_share": 100 * (mins - youth) / mins if mins else 0,
            "halves_known": known and kind == "season_end" and (x["unique_id"] in first), "h1": h1 or 0, "h2": h2 or 0,
            "h1_rating_pct": h_rating(r1), "h2_rating_pct": h_rating(r2), "age": int(ages.get(str(x["unique_id"]), x["age"]))}


class ReviewIn(BaseModel):
    again: bool = False


@router.post("/review/{kind}", dependencies=need("dp"))
async def run_review(kind: Literal["winter", "season_end"], body: ReviewIn):
    c = await active_career()
    s = await _season(c)
    st = await settings_doc()
    S = st["data"]
    if kind == "season_end" and s["game_date"] <= s["winter_date"]:
        raise HTTPException(409, "The season-end review runs after the final match; your save is still before the winter review date")
    rules = await current_rules(c["id"], "dp")
    targets = sorted(await contexts(c, rules["data"]["scope"]), key=lambda x: x["unique_id"])
    everyone = await contexts(c, {"all_players": True})
    first, ages = await _evidence(c, s, kind)
    await db.dp_seasons.update_one({"career_id": c["id"], "season": s["season"]}, {"$set": {"ages": ages}})
    prev = {r["unique_id"]: r for r in await _latest_records(c["id"], s["season"], kind)}
    winter = {r["unique_id"]: r for r in await _latest_records(c["id"], s["season"], "winter")}
    todo = [x for x in targets if body.again or x["unique_id"] not in prev][:S["batch_size"]]
    by_pos = {}
    for x in everyone:
        by_pos.setdefault(x["position"], []).append(x)
    band = S["score"]["level_band"]
    recs, items = [], []
    for x in todo:
        start = x["ca"] - (x.get("ca_growth") or 0)
        group = [g for g in by_pos.get(x["position"], []) if g["unique_id"] != x["unique_id"] and abs((g["ca"] - (g.get("ca_growth") or 0)) - start) <= band]
        sc = E.score_player(x, group, S)
        h_vals = [g.get("avg_rating") for g in group]
        ev = _ev(x, first, ages, kind, lambda r: E.percentile(h_vals, r))
        w = winter.get(x["unique_id"])
        w_applied = w["change"] if w and kind == "season_end" and w["status"] in ("auto", "approved") else 0
        rec = E.assess(x, sc, ev, S, kind, w_applied, w_applied, len(group))
        old = prev.get(x["unique_id"])
        if old and old["status"] in ("auto", "approved") and old["change"]:
            rec = rec | {"status": old["status"], "change": old["change"], "correction": f"Earlier decision kept: {old['change']:+d} already applied",
                         "recomputed_change": rec["change"]}
        doc = {"id": new_id(), "career_id": c["id"], "season": s["season"], "kind": kind, "unique_id": x["unique_id"], "name": x["name"], "club": x["club"],
               "league": x["league"], "position": x["position"], "revision": (old["revision"] + 1) if old else 1, "settings_version": st["version"],
               "evidence": {k: v for k, v in ev.items() if k != "senior_share"} | {"senior_share": round(ev["senior_share"])},
               "score": {k: v for k, v in sc.items()}, "at": now_iso(), "game_date": s["game_date"]} | rec
        recs.append(doc)
        if rec["status"] == "auto" and rec["change"] and not (old and old["status"] in ("auto", "approved")):
            items.append({"unique_id": x["unique_id"], "name": x["name"], "club": x["club"], "field": "pa", "delta": rec["change"]})
    if recs:
        await db.dp_records.insert_many([dict(r) for r in recs])
    if kind == "season_end":
        stale = [w for u, w in winter.items() if w["status"] in ("needs_review", "held", "flag") and u in {r["unique_id"] for r in recs}]
        if stale:
            await db.dp_records.insert_many([{k: v for k, v in w.items() if k != "id"} | {"id": new_id(), "career_id": c["id"], "revision": w["revision"] + 1, "status": "superseded",
                                               "change": 0, "reason": "Replaced by the season-end review, which settles the whole season", "at": now_iso()} for w in stale])
    applied = await _apply(c, s["season"], kind, items)
    left = len([x for x in targets if x["unique_id"] not in prev and x["unique_id"] not in {r["unique_id"] for r in recs}])
    summary = f"{'Winter' if kind == 'winter' else 'Season-end'} review: {len(recs)} players reviewed, {len(items)} changes sent to your save" + (f", {left} still to review" if left else "")
    await audit(c["id"], "run", "dp", summary, hidden=False)
    return {"reviewed": len(recs), "applied": applied, "remaining": left, "summary": summary}


async def _apply(c: dict, season: str, kind: str, items: list, tag: str = "") -> dict:
    if not items:
        return {"queued": 0, "started": False}
    award = f"{season}-{kind}{tag}"
    res = await queue_changes(c, "dp", award, items, hidden=True)
    ids = [d["id"] async for d in db.changes.find({"career_id": c["id"], "source": "dp", "award_id": award, "status": "queued"}, {"id": 1})]
    started, why = False, None
    if ids:
        try:
            await start_batch(c, ids)
            started = True
        except HTTPException as exc:
            why = exc.detail
    return {"queued": res["queued"], "started": started, "waiting_reason": why}


@router.get("/records")
async def records(kind: Literal["winter", "season_end"] | None = None, status: str | None = None):
    c = await active_career()
    s = await _season(c)
    out = await _latest_records(c["id"], s["season"], kind)
    if status:
        out = [r for r in out if r["status"] == status]
    return sorted(out, key=lambda r: (-abs(r["change"]), r["name"]))


@router.get("/records/{uid}")
async def record(uid: int):
    c = await active_career()
    s = await _season(c)
    out = await db.dp_records.find({"career_id": c["id"], "season": s["season"], "unique_id": uid}, HIDE).sort([("kind", -1), ("revision", -1)]).to_list(20)
    if not out:
        raise HTTPException(404, "No review for this player this season")
    return out


class DecideIn(BaseModel):
    approve: bool


@router.post("/records/{rid}/decide")
async def decide(rid: str, body: DecideIn):
    c = await active_career()
    r = await db.dp_records.find_one({"id": rid, "career_id": c["id"]}, {"_id": 0})
    if not r or r["status"] not in ("needs_review", "held", "flag"):
        raise HTTPException(409, "This review doesn't need a decision")
    newer = await db.dp_records.find_one({"career_id": c["id"], "season": r["season"], "kind": r["kind"], "unique_id": r["unique_id"], "revision": {"$gt": r["revision"]}}, {"_id": 1})
    if newer:
        raise HTTPException(409, "This review was already decided or replaced. Reload the list.")
    if r["kind"] == "winter" and await db.dp_records.count_documents({"career_id": c["id"], "season": r["season"], "kind": "season_end", "unique_id": r["unique_id"]}):
        raise HTTPException(409, "The season-end review has already settled this season for this player")
    new = {k: v for k, v in r.items() if k != "id"} | {"id": new_id(), "revision": r["revision"] + 1, "status": "approved" if body.approve and r["change"] else "rejected",
                                                       "decided_at": now_iso(), "change": r["change"] if body.approve else 0}
    await db.dp_records.insert_one(dict(new))
    res = await _apply(c, r["season"], r["kind"], [{"unique_id": r["unique_id"], "name": r["name"], "club": r["club"], "field": "pa", "delta": r["change"]}], "-approved") \
        if body.approve and r["change"] else {"queued": 0}
    await audit(c["id"], "review decided", "dp", f"{r['name']}: {'approved' if body.approve else 'rejected'}", hidden=False)
    return {"status": new["status"]} | res
