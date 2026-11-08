"""Ideas rebuilt from FMST26 (formulas, advanced filters), fmOS (quadrant, replacement, price explained) and FM Dossier (tactic fit, shape advisor).
None of their code is used. Formulas are worked out by FMCC's own maths parser, never run as code."""
import ast
import json
import os
import re
import subprocess
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

import roles
import stats_model as sm
from core import db, active_career, latest_snapshot, now_iso, new_id, audit, next_revision
from sample_reader import GROUP

router = APIRouter(prefix="/api")
LIVE = os.environ.get("FMCC_READER") == "fmsave"
OPS = (ast.Expression, ast.BinOp, ast.UnaryOp, ast.Constant, ast.Name, ast.Call, ast.Compare, ast.BoolOp, ast.Load, ast.Add, ast.Sub, ast.Mult,
       ast.Div, ast.USub, ast.UAdd, ast.Gt, ast.Lt, ast.GtE, ast.LtE, ast.Eq, ast.NotEq, ast.And, ast.Or)
FUNCS = {"min", "max", "abs", "iff"}
BASE_NAMES = {"minutes", "age", "value", "wage", "grade"}
MAX_FORMULAS = 30


class FormulaError(ValueError):
    pass


def parse(expr: str):
    src = re.sub(r"\bif\s*\(", "iff(", expr.strip())
    try:
        tree = ast.parse(src, mode="eval")
    except SyntaxError:
        raise FormulaError("The formula isn't complete. Check the brackets and signs.")
    names = set()
    for n in ast.walk(tree):
        if not isinstance(n, OPS):
            raise FormulaError("Only numbers, stats, + − × ÷, brackets, min, max, abs and if are allowed.")
        if isinstance(n, ast.Call) and not (isinstance(n.func, ast.Name) and n.func.id in FUNCS):
            raise FormulaError("Only min, max, abs and if can be used as functions.")
        if isinstance(n, ast.Constant) and not isinstance(n.value, (int, float)):
            raise FormulaError("Only numbers can be written as values.")
        if isinstance(n, ast.Name) and n.id not in FUNCS:
            names.add(n.id)
    return tree, names


def _ev(n, env):
    if isinstance(n, ast.Expression):
        return _ev(n.body, env)
    if isinstance(n, ast.Constant):
        return float(n.value)
    if isinstance(n, ast.Name):
        return env.get(n.id)
    if isinstance(n, ast.UnaryOp):
        v = _ev(n.operand, env)
        return None if v is None else (-v if isinstance(n.op, ast.USub) else v)
    if isinstance(n, ast.BinOp):
        a, b = _ev(n.left, env), _ev(n.right, env)
        if a is None or b is None:
            return None
        if isinstance(n.op, ast.Div):
            return None if b == 0 else a / b
        return a + b if isinstance(n.op, ast.Add) else a - b if isinstance(n.op, ast.Sub) else a * b
    if isinstance(n, ast.Compare):
        a = _ev(n.left, env)
        for op, c in zip(n.ops, n.comparators):
            b = _ev(c, env)
            if a is None or b is None:
                return None
            ok = {ast.Gt: a > b, ast.Lt: a < b, ast.GtE: a >= b, ast.LtE: a <= b, ast.Eq: a == b, ast.NotEq: a != b}[type(op)]
            if not ok:
                return 0.0
            a = b
        return 1.0
    if isinstance(n, ast.BoolOp):
        vals = [_ev(v, env) for v in n.values]
        return float(all(vals) if isinstance(n.op, ast.And) else any(vals))
    if isinstance(n, ast.Call):
        args = [_ev(a, env) for a in n.args]
        f = n.func.id
        if f == "iff":
            if len(args) != 3:
                raise FormulaError("if needs three parts: if(condition, then, otherwise)")
            return None if args[0] is None else (args[1] if args[0] else args[2])
        if any(a is None for a in args) or not args:
            return None
        return abs(args[0]) if f == "abs" else min(args) if f == "min" else max(args)
    return None


def env_of(x: dict) -> dict:
    e = {k: v for k, v in x["p90"].items()} | {"minutes": x["minutes"], "age": x["age"], "value": x["value"], "wage": x["wage"], "grade": x["grade_global"]}
    e |= {f"c_{k}": v for k, v in x.get("computed", {}).items()}
    return e


async def formulas(cid: str) -> dict:
    rows = await sm.latest_docs("formulas", cid, "key")
    return {k: v for k, v in rows.items() if v.get("status") == "active"}


def order(fs: dict) -> list:
    """Formulas in dependency order; raises on a formula that uses itself."""
    seen, out, stack = set(), [], set()

    def visit(k):
        if k in stack:
            raise FormulaError(f"'{fs[k]['name']}' ends up using itself.")
        if k in seen:
            return
        stack.add(k)
        for n in parse(fs[k]["expr"])[1]:
            if n.startswith("f_") and n[2:] in fs:
                visit(n[2:])
        stack.discard(k)
        seen.add(k)
        out.append(k)
    for k in fs:
        visit(k)
    return out


def check_names(names: set, fs: dict, archetypes: dict):
    bad = [n for n in names if n not in sm.METRICS and n not in BASE_NAMES and not (n.startswith("c_") and n[2:] in archetypes) and not (n.startswith("f_") and n[2:] in fs)]
    if bad:
        raise FormulaError(f"Unknown stat: {', '.join(sorted(bad))}.")


async def attach(c: dict, data: dict):
    fs = await formulas(c["id"])
    key = json.dumps(sorted((k, v["revision"]) for k, v in fs.items()))
    if data.get("fkey") == key:
        return
    trees = {}
    try:
        for k in order(fs):
            trees[k] = parse(fs[k]["expr"])[0]
    except FormulaError:
        pass
    for x in data["players"]:
        env = env_of(x)
        x["f"] = {}
        for k, t in trees.items():
            v = _ev(t, env)
            x["f"][k] = None if v is None else round(v, 3)
            env[f"f_{k}"] = v
    data["fkey"], data["formulas"], data["pct_cache"] = key, fs, {}


def value(x: dict, field: str):
    if field.startswith("f:"):
        return (x.get("f") or {}).get(field[2:])
    if field.startswith("c:"):
        return x["computed"].get(field[2:])
    if field in sm.METRICS:
        return x["p90"].get(field)
    return x.get({"grade": "grade_global"}.get(field, field))


def pct_of(data: dict, x: dict, field: str, pool: str):
    k = (field, pool, x["cohort"] if pool == "position" else x["league"] if pool == "league" else "")
    cache = data.setdefault("pct_cache", {})
    if k not in cache:
        vals = sorted(v for o in data["players"] if o["gender"] == x["gender"] and o["minutes"] >= sm.MIN_PCT
                      and (pool != "position" or o["cohort"] == x["cohort"]) and (pool != "league" or o["league"] == x["league"])
                      for v in [value(o, field)] if v is not None)
        cache[k] = vals
    v, vals = value(x, field), cache[k]
    if v is None or not vals or x["minutes"] < sm.MIN_PCT:
        return None
    import bisect
    return round(bisect.bisect_right(vals, v) / len(vals) * 100)


CMP = {">": lambda a, b: a > b, ">=": lambda a, b: a >= b, "<": lambda a, b: a < b, "<=": lambda a, b: a <= b, "=": lambda a, b: a == b}


def match(x: dict, node: dict, data: dict) -> bool:
    """Advanced filter tree: {op: and|or, items: [...]} with value, stat-vs-stat and percentile conditions."""
    if "items" in node:
        res = [match(x, i, data) for i in node["items"][:30]]
        return (all(res) if node.get("op", "and") == "and" else any(res)) if res else True
    cmp = CMP.get(node.get("cmp", ">="))
    if not cmp:
        return False
    kind = node.get("kind")
    if kind == "stat":
        a, b = value(x, node.get("a", "")), value(x, node.get("b", ""))
    elif kind == "pct":
        a, b = pct_of(data, x, node.get("field", ""), node.get("pool", "position")), node.get("value")
    else:
        a, b = value(x, node.get("field", "")), node.get("value")
    return a is not None and b is not None and cmp(a, float(b))


# ---------- formulas ----------
class FormulaIn(BaseModel):
    name: str = Field(min_length=1, max_length=40)
    expr: str = Field(min_length=1, max_length=300)


async def _ctx():
    import scout_api
    c, data = await scout_api._data()
    await attach(c, data)
    return c, data


@router.get("/scout/formulas")
async def list_formulas():
    c = await active_career()
    return {"items": list((await formulas(c["id"])).values()), "limit": MAX_FORMULAS,
            "names": sorted(BASE_NAMES) + list(sm.METRICS) + [f"c_{k}" for k in sm.ARCHETYPES]}


@router.post("/scout/formulas/preview")
async def preview(body: FormulaIn):
    c, data = await _ctx()
    try:
        tree, names = parse(body.expr)
        check_names(names, data["formulas"], data["archetypes"])
    except FormulaError as e:
        return {"ok": False, "error": str(e)}
    sample = [x for x in data["players"] if x["minutes"] >= sm.MIN_PCT][:5]
    out = []
    for x in sample:
        env = env_of(x) | {f"f_{k}": v for k, v in (x.get("f") or {}).items()}
        v = _ev(tree, env)
        out.append({"name": x["name"], "value": None if v is None else round(v, 3)})
    return {"ok": True, "rows": out, "note": "Blank results mean a stat is missing or there was a division by zero."}


@router.put("/scout/formulas/{key}")
async def save_formula(key: str, body: FormulaIn):
    if not re.fullmatch(r"[a-z0-9_]{1,30}", key):
        raise HTTPException(422, "Use lowercase letters, numbers and _ for the short name")
    c, data = await _ctx()
    fs = dict(data["formulas"])
    if key not in fs and len(fs) >= MAX_FORMULAS:
        raise HTTPException(409, f"You already have {MAX_FORMULAS} formulas")
    try:
        _, names = parse(body.expr)
        fs[key] = {"name": body.name, "expr": body.expr}
        check_names(names, fs, data["archetypes"])
        order(fs)
    except FormulaError as e:
        raise HTTPException(422, str(e))
    rev = await next_revision("formulas", {"career_id": c["id"], "key": key})
    await db.formulas.insert_one({"id": new_id(), "career_id": c["id"], "key": key, "name": body.name.strip(), "expr": body.expr.strip(), "revision": rev, "status": "active", "at": now_iso()})
    await audit(c["id"], "formula saved", "scouting", f"{body.name}: {body.expr}")
    return {"ok": True, "revision": rev}


@router.delete("/scout/formulas/{key}")
async def delete_formula(key: str):
    c = await active_career()
    fs = await formulas(c["id"])
    if key not in fs:
        raise HTTPException(404, "Formula not found")
    users = [v["name"] for k, v in fs.items() if k != key and f"f_{key}" in parse(v["expr"])[1]]
    if users:
        raise HTTPException(409, f"Used by {', '.join(users)}. Change those first.")
    await db.formulas.insert_one({k: v for k, v in fs[key].items()} | {"id": new_id(), "revision": fs[key]["revision"] + 1, "status": "deleted", "at": now_iso()})
    return {"ok": True}


class ImportIn(BaseModel):
    formulas: list[dict] = Field(max_length=MAX_FORMULAS)


@router.post("/scout/formulas/import")
async def import_formulas(body: ImportIn):
    done = []
    for f in body.formulas:
        key = re.sub(r"[^a-z0-9_]", "_", str(f.get("key", "")).lower())[:30]
        await save_formula(key, FormulaIn(name=str(f.get("name", key))[:40], expr=str(f.get("expr", ""))[:300]))
        done.append(key)
    return {"imported": done}


# ---------- quadrant, replacement, price explained ----------
@router.get("/scout/quadrant")
async def quadrant(perf: str = "grade", gender: str = "M", group: Optional[str] = None):
    _, data = await _ctx()
    pts = []
    for x in data["players"]:
        if x["own"] or x["gender"] != gender or (group and x["group"] != group) or x["minutes"] < sm.MIN_PCT or not x["value"]:
            continue
        p = value(x, perf)
        if p is not None:
            cost = x["value"] + (x["wage"] or 0) * (x["months_left"] or 24) * 4.345
            pts.append({"unique_id": x["unique_id"], "name": x["name"], "club": x["club"], "perf": p, "cost": int(cost)})
    if not pts:
        return {"points": [], "mid_perf": None, "mid_cost": None}
    mp, mc = sorted(q["perf"] for q in pts)[len(pts) // 2], sorted(q["cost"] for q in pts)[len(pts) // 2]
    for q in pts:
        q["zone"] = ("Stars" if q["cost"] >= mc else "Hidden gems") if q["perf"] >= mp else ("Overpriced" if q["cost"] >= mc else "Avoid")
    return {"points": pts, "mid_perf": mp, "mid_cost": mc}


@router.get("/scout/replacement/{uid}")
async def replacement(uid: int, max_value: Optional[int] = None, max_wage: Optional[int] = None, max_age: Optional[int] = None):
    _, data = await _ctx()
    x = data["by_uid"].get(uid)
    if not x:
        raise HTTPException(404, "Player not found")
    rows = []
    for s in sm.similar(data, x, n=80):
        o = data["by_uid"][s["unique_id"]]
        if o["own"] or (max_value and (o["value"] or 0) > max_value) or (max_wage and (o["wage"] or 0) > max_wage) or (max_age and o["age"] > max_age):
            continue
        cheap = 1 - min(1, (o["value"] or 0) / max(1, x["value"] or o["value"] or 1))
        rows.append(s | {"wage": o["wage"], "saving": (x["value"] or 0) - (o["value"] or 0), "rank": round(s["similarity"] * .75 + cheap * 25, 1)})
    return {"target": {"name": x["name"], "value": x["value"]}, "rows": sorted(rows, key=lambda r: -r["rank"])[:20]}


@router.get("/scout/price/{uid}")
async def price_explained(uid: int, view: str = "full"):
    """Why his price is what it is: each factor compared with players of his position in the save."""
    _, data = await _ctx()
    x = data["by_uid"].get(uid)
    if not x:
        raise HTTPException(404, "Player not found")
    peers = [o for o in data["players"] if o["cohort"] == x["cohort"] and o["value"] and not o["own"]]
    med = lambda k: sorted(o[k] for o in peers if o.get(k) is not None)[len(peers) // 2] if peers else None  # noqa: E731
    out = []

    def add(f, up, detail):
        out.append({"factor": f, "effect": "raises" if up else "lowers", "detail": detail})
    if med("age") is not None:
        add("Age", x["age"] < med("age"), f"{x['age']} vs {med('age')} typical for his position")
    if view == "full" and x.get("pa") and x.get("ca"):
        add("Potential", x["pa"] - x["ca"] >= 20, f"{x['pa'] - x['ca']} points of room to grow")
    add("Position", (med("value") or 0) > sorted(o["value"] for o in data["players"] if o["value"])[len(data["players"]) // 2], f"{x['cohort']}s are valued at {med('value'):,} in the middle" if med("value") else x["cohort"])
    add("Club and league", x["league_mult"] >= .85, f"league multiplier {x['league_mult']}")
    if x["months_left"] is not None:
        add("Contract", x["months_left"] > 24, f"{x['months_left']} months left")
    if x["grade_global"] is not None and med("grade_global") is not None:
        add("Form", x["grade_global"] > med("grade_global"), f"grade {x['grade_global']} vs {med('grade_global')} typical")
    return {"value": x["value"], "fair_price": x["fair_price"], "factors": out, "note": "FM doesn't publish its valuation formula; these are the factors that usually move a price, compared with his position in your save."}


# ---------- tactic fit and shape advisor ----------
def _formation_from_file(raw: bytes) -> Optional[str]:
    txt = raw.decode("latin-1", errors="ignore")
    for m in re.finditer(r"\b(\d)-(\d)-(\d)(?:-(\d))?\b", txt):
        key = "".join(g for g in m.groups() if g)
        if key in roles.FORMATIONS:
            return key
    return None


class TacticIn(BaseModel):
    formation: str = Field(pattern="^(" + "|".join(roles.FORMATIONS) + ")$")
    name: str = Field(default="", max_length=60)


async def _add_tactic(c: dict, formation: str, name: str, source: str) -> dict:
    doc = {"id": new_id(), "career_id": c["id"], "formation": formation, "name": name or roles.FORMATIONS[formation][0], "source": source, "at": now_iso()}
    await db.tactics.insert_one(dict(doc))
    await audit(c["id"], "tactic added", "squad", f"{doc['name']} ({source})")
    return {k: v for k, v in doc.items() if k != "career_id"}


@router.post("/squad/tactics")
async def add_tactic(body: TacticIn):
    return await _add_tactic(await active_career(), body.formation, body.name, "FMCC formation")


@router.post("/squad/tactics/import")
async def import_tactic(file: UploadFile = File(...)):
    c = await active_career()
    raw = await file.read(2 * 1024 * 1024 + 1)
    if not (file.filename or "").lower().endswith(".fmf") or len(raw) > 2 * 1024 * 1024:
        raise HTTPException(422, "Choose an FM tactic file (.fmf, up to 2 MB)")
    f = _formation_from_file(raw)
    if not f:
        raise HTTPException(422, "FMCC couldn't read the formation from this file yet (FM's tactic format isn't documented). Pick one of FMCC's formations instead.")
    return await _add_tactic(c, f, Path(file.filename).stem[:60], f"Imported from {file.filename}")


@router.get("/squad/tactics")
async def list_tactics():
    c = await active_career()
    return await db.tactics.find({"career_id": c["id"]}, {"_id": 0, "career_id": 0}).sort("at", -1).to_list(50)


def fit(players: list, formation: str) -> list:
    out = []
    for s in roles.formation_meta(formation)["slots"]:
        rated = sorted(({"unique_id": p["unique_id"], "name": p["name"], "rating": roles.role_rating(p, s["role"]), "natural": roles.eligible(p, s)} for p in players),
                       key=lambda r: (-r["natural"], -r["rating"]))
        top = [r for r in rated if r["natural"]][:3]
        score = round(sum(w * (top[i]["rating"] if i < len(top) else 0) for i, w in enumerate((.6, .3, .1))), 1)
        out.append({"slot": s["key"], "label": s["label"], "role": s["role"], "role_name": s["role_name"], "group": GROUP.get(s["positions"][0], "CM"),
                    "starter": top[0] if top else None, "backup": top[1] if len(top) > 1 else None, "depth": top[2] if len(top) > 2 else None,
                    "score": score, "all": rated[:8]})
    return out


@router.get("/squad/tactic-fit")
async def tactic_fit(formation: str = "433"):
    if formation not in roles.FORMATIONS:
        raise HTTPException(404, "Unknown formation")
    c = await active_career()
    slots = fit((await latest_snapshot(c["id"]))["players"], formation)
    return {"formation": roles.FORMATIONS[formation][0], "slots": slots, "gaps": sorted(slots, key=lambda s: s["score"])[:3],
            "note": "FM tactic files hold in- and out-of-possession roles; FMCC rates the in-possession role until it can read them."}


@router.get("/squad/shapes")
async def shapes():
    c = await active_career()
    players = (await latest_snapshot(c["id"]))["players"]
    out = []
    for k, (name, _) in roles.FORMATIONS.items():
        form = roles.formation_meta(k)
        depth = roles.depth_chart(players, form)
        out.append({"key": k, "name": name, "strength": roles.strength(roles.best_xi(players, form, depth), depth),
                    "depth": round(sum(s["score"] for s in fit(players, k)) / len(form["slots"]), 1)})
    return sorted(out, key=lambda r: -r["strength"])


# ---------- the three apps ----------
APPS = [("fmdossier", "FM Dossier", "windows", "https://fmdossier.dev/"), ("fmst26", "FMST26", "windows", os.environ.get("FMST26_URL")),
        ("fmos", "fmOS", "web", os.environ.get("FMOS_URL"))]


@router.get("/apps")
async def apps():
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "app_paths": 1}) or {}
    paths = s.get("app_paths") or {}
    out = []
    for key, name, kind, url in APPS:
        p = paths.get(key)
        installed = (Path(p).exists() if p else False) if LIVE else None
        out.append({"key": key, "name": name, "kind": kind, "url": url, "path": p, "installed": installed})
    return {"desktop": LIVE, "apps": out}


class PathIn(BaseModel):
    path: str = Field(min_length=3, max_length=400)


@router.put("/apps/{key}/path")
async def set_app_path(key: str, body: PathIn):
    if key not in {a[0] for a in APPS if a[2] == "windows"}:
        raise HTTPException(404, "Unknown app")
    if not body.path.lower().endswith(".exe"):
        raise HTTPException(422, "Point FMCC at the app's .exe file")
    await db.settings.update_one({"_id": "app"}, {"$set": {f"app_paths.{key}": body.path}}, upsert=True)
    return {"ok": True}


@router.post("/apps/{key}/open")
async def open_app(key: str):
    if not LIVE:
        raise HTTPException(409, "Opening other programs works in the Windows program, not in the browser preview")
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "app_paths": 1}) or {}
    p = (s.get("app_paths") or {}).get(key)
    if not p or not Path(p).exists():
        raise HTTPException(404, "FMCC can't find this app. Point it at the .exe first.")
    subprocess.Popen([p], close_fds=True)
    return {"ok": True}
