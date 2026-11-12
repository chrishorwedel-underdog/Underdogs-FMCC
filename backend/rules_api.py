from typing import Literal, Union

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from pymongo.errors import DuplicateKeyError

import rules_engine as RE
from core import db, active_career, now_iso, new_id, latest_two
from population import contexts

router = APIRouter(prefix="/api/rules")
Module = Literal["elite", "breakout", "dp", "squad", "scouting", "reports", "development"]


class Condition(BaseModel):
    field: Literal[tuple(RE.FIELDS)]  # type: ignore[valid-type]
    op: Literal[">=", "<=", "=", "!="]
    value: Union[float, str]


class Action(BaseModel):
    target: Literal["ca", "pa"]
    min: int = Field(ge=-30, le=30)
    max: int = Field(ge=-30, le=30)


class Rule(BaseModel):
    id: str = Field(min_length=1, max_length=40)
    name: str = Field(min_length=1, max_length=60)
    enabled: bool = True
    join: Literal["and", "or"] = "and"
    timing: Literal["monthly", "season_end", "on_demand", "after_matches"] = "season_end"
    max_value: int = Field(200, ge=1, le=200)
    conditions: list[Condition] = Field(min_length=1, max_length=8)
    action: Action


class Scope(BaseModel):
    my_club: bool = True
    all_players: bool = False
    nations: list[str] = Field(default_factory=list, max_length=200)
    leagues: list[str] = Field(default_factory=list, max_length=200)


class Caps(BaseModel):
    max_players: int = Field(500, ge=1, le=100000)
    max_pa_change: int = Field(8, ge=1, le=30)


class RulesData(BaseModel):
    rules: list[Rule] | None = Field(None, max_length=30)
    params: dict[str, float] | None = None
    scope: Scope | None = None
    caps: Caps | None = None


class SaveIn(BaseModel):
    data: RulesData
    expected_version: int
    note: str = Field("", max_length=120)


class ResetIn(BaseModel):
    expected_version: int


class TestIn(BaseModel):
    rule: Rule


async def current(career_id: str, module: str) -> dict:
    doc = await db.rules.find_one({"career_id": career_id, "module": module}, {"_id": 0}, sort=[("version", -1)])
    return doc or {"module": module, "version": 0, "data": RE.PRESETS[module], "created_at": None, "note": "Preset"}


def validate(module: str, data: RulesData) -> dict:
    preset = RE.PRESETS[module]
    if module in RE.PARAM_MODULES:
        if not data.params or set(data.params) != set(preset["params"]):
            raise HTTPException(422, "These settings don't match this module")
        for k, v in data.params.items():
            lo, hi = RE.PARAM_LIMITS[k]
            if not lo <= v <= hi:
                raise HTTPException(422, f"{k} must be between {lo} and {hi}")
        return {"params": data.params}
    if data.rules is None:
        raise HTTPException(422, "Rules are missing")
    ids = [r.id for r in data.rules]
    if len(ids) != len(set(ids)):
        raise HTTPException(422, "Each rule needs its own id")
    out = {"rules": [r.model_dump() for r in data.rules]}
    if module == "dp":
        out["scope"] = (data.scope or Scope(**preset["scope"])).model_dump()
        out["caps"] = (data.caps or Caps(**preset["caps"])).model_dump()
    return out


async def save_version(career_id: str, module: str, data: dict, expected: int, note: str) -> dict:
    cur = await current(career_id, module)
    if cur["version"] != expected:
        raise HTTPException(409, "These rules were changed somewhere else. Reload to see the latest version.")
    doc = {"id": new_id(), "career_id": career_id, "module": module, "version": expected + 1, "data": data, "created_at": now_iso(), "note": note}
    try:
        await db.rules.insert_one(dict(doc))
    except DuplicateKeyError:
        raise HTTPException(409, "These rules were changed at the same moment. Reload and try again.")
    return doc


@router.get("/{module}")
async def get_rules(module: Module):
    c = await active_career()
    cur = await current(c["id"], module)
    hist = await db.rules.find({"career_id": c["id"], "module": module}, {"_id": 0, "version": 1, "created_at": 1, "note": 1}).sort("version", -1).to_list(50)
    changed_at, prev = {}, _items(RE.PRESETS[module])
    async for v in db.rules.find({"career_id": c["id"], "module": module}, {"_id": 0, "data": 1, "created_at": 1}).sort("version", 1):
        now = _items(v["data"])
        changed_at |= {k: v["created_at"] for k in now if now[k] != prev.get(k)}
        prev = now
    return {"module": module, "version": cur["version"], "data": cur["data"], "history": hist, "defaults": RE.PRESETS[module], "changed_at": changed_at,
            "fields": {k: v for k, v in RE.FIELDS.items() if k not in ("ca", "pa")},
            "kind": "params" if module in RE.PARAM_MODULES else "rules"}


def _items(data: dict) -> dict:
    if data.get("params") is not None:
        return dict(data["params"])
    out = {r["id"]: r for r in data.get("rules") or []}
    return out | {k: data[k] for k in ("scope", "caps") if k in data}


class ImpactIn(BaseModel):
    data: RulesData


@router.post("/{module}/impact")
async def rules_impact(module: Module, body: ImpactIn):
    """How many players a draft would affect, before it is saved. Never shows amounts or ability."""
    c = await active_career()
    draft = validate(module, body.data)
    cur = (await current(c["id"], module))["data"]
    if module in RE.REWARD_MODULES:
        scope = cur.get("scope") if module == "dp" else {"my_club": True, "nations": [], "leagues": []}
        ctxs = await contexts(c, scope)
        pick = lambda rules, x: RE.first_match(rules, x)  # noqa: E731
        hit = sum(pick(cur["rules"], x) != pick(draft["rules"], x) for x in ctxs)
        return {"affected": hit, "population": len(ctxs), "note": "Players whose matching rule or its reward would change with this draft."}
    changed = {k for k in draft["params"] if draft["params"][k] != cur["params"].get(k)}
    if module == "scouting":
        import scouting_api
        pool = (await scouting_api._pool(c))["players"]
        top = lambda p: [x["unique_id"] for x in sorted(scouting_api.score_players(pool, p, None), key=lambda x: -x["score"])[:100]]  # noqa: E731
        a, b = top(cur["params"]), top(draft["params"])
        return {"affected": sum(1 for i, u in enumerate(b) if i >= len(a) or a[i] != u), "population": len(pool), "note": "Players whose place in the top 100 of your rankings would move."}
    own = await contexts(c, {"my_club": True, "nations": [], "leagues": []})
    if module == "reports":
        snaps = await latest_two(c["id"])
        before = {p["unique_id"]: p["ca"] for p in snaps[1]["players"]} if len(snaps) > 1 else {}
        label = lambda d, p: "up" if d >= p["rising"] else "down" if d <= p["falling"] else ""  # noqa: E731
        diffs = [p["ca"] - before[p["unique_id"]] for p in snaps[0]["players"] if p["unique_id"] in before] if snaps else []
        return {"affected": sum(label(d, cur["params"]) != label(d, draft["params"]) for d in diffs), "population": len(diffs), "note": "Squad players whose rising or falling label would change in the latest report."}
    youth = [x for x in own if x["age"] <= 21]
    if module == "squad":
        import squad_api as SQ
        a, b = await SQ.squad_outcome(c, cur["params"]), await SQ.squad_outcome(c, draft["params"])
        return {"affected": sum(a[u] != b.get(u) for u in a), "population": len(a), "note": "Squad players whose Development XI place, registration or minutes flag would change."}
    if module == "development":
        import plans_api as PL
        snaps = await latest_two(c["id"])
        mins = PL.month_minutes(snaps[0], snaps[1] if len(snaps) > 1 else None) if snaps else {}
        plans = await PL.latest_plans(c["id"])
        def needs(p, x):
            t = plans[x["unique_id"]]["minutes_target"] if x["unique_id"] in plans else (int(p["default_target"]) if x["age"] < 21 else None)
            return bool(t) and mins.get(x["unique_id"], 0) < t * p["needs_pct"] / 100
        players = snaps[0]["players"] if snaps else []
        return {"affected": sum(needs(cur["params"], x) != needs(draft["params"], x) for x in players), "population": len(players), "note": "Squad players whose 'needs minutes' flag would change."}
    if not changed:
        n = 0
    elif module == "development" or changed <= {"target_minutes", "max_youth"}:
        n = len(youth)
    else:
        n = len(own)
    return {"affected": n, "population": len(own), "note": "Squad players these settings cover." if module == "squad" else "Under-21 squad players these targets cover."}


@router.put("/{module}")
async def put_rules(module: Module, body: SaveIn):
    c = await active_career()
    doc = await save_version(c["id"], module, validate(module, body.data), body.expected_version, body.note or "Edited")
    return {"version": doc["version"]}


@router.post("/{module}/reset")
async def reset_rules(module: Module, body: ResetIn):
    c = await active_career()
    doc = await save_version(c["id"], module, RE.PRESETS[module], body.expected_version, "Reset to default")
    return {"version": doc["version"]}


@router.post("/{module}/import")
async def import_rules(module: Module, body: SaveIn):
    c = await active_career()
    doc = await save_version(c["id"], module, validate(module, body.data), body.expected_version, body.note or "Imported preset")
    return {"version": doc["version"]}


@router.post("/{module}/test")
async def test_rule(module: Literal["elite", "breakout", "dp"], body: TestIn):
    """Shows only how many players qualify and who. Never applies anything or shows amounts."""
    c = await active_career()
    rules_doc = await current(c["id"], module)
    scope = rules_doc["data"].get("scope") if module == "dp" else {"my_club": True, "nations": [], "leagues": []}
    ctxs = await contexts(c, scope)
    if module == "elite":
        nominated = {n["unique_id"] for n in await active_nominees(c["id"], "elite")}
        ctxs = [x for x in ctxs if x["unique_id"] in nominated] or ctxs
    hits = [x for x in ctxs if RE.matches(body.rule.model_dump(), x)]
    return {"count": len(hits), "population": len(ctxs), "names": [f"{h['name']} ({h['club']})" for h in hits[:40]]}


async def active_nominees(career_id: str, module: str) -> list:
    pipeline = [{"$match": {"career_id": career_id, "module": module}}, {"$sort": {"revision": -1}},
                {"$group": {"_id": "$unique_id", "doc": {"$first": "$$ROOT"}}}, {"$replaceRoot": {"newRoot": "$doc"}},
                {"$match": {"status": "active"}}, {"$project": {"_id": 0}}]
    return await db.nominations.aggregate(pipeline).to_list(None)
