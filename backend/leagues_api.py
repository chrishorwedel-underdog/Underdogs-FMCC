"""League strength: the built-in list (mean Opta club strength from the Global League Strength and Player Model workbook,
408 rated competitions), matched to the save's leagues by name and known aliases.
Leagues not on the list are placed by their save reputation. Every match, multiplier edit and recalculation is kept as a new version."""
import csv
import io
import json
import re
import unicodedata
from pathlib import Path
from typing import Optional

from fastapi import APIRouter, HTTPException, UploadFile, File, Query
from pydantic import BaseModel, Field

import sample_reader
from core import db, active_career, now_iso, new_id, audit, next_revision

router = APIRouter(prefix="/api/leagues")
BUILTIN = json.loads((Path(__file__).parent / "data" / "opta_leagues.json").read_text())
STOP = {"league", "the", "football", "fc", "de", "la", "le", "of", "division", "liga", "pro"}


def norm(s: str) -> str:
    return re.sub(r"[^a-z0-9 ]", " ", unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode().lower()).strip()


def toks(s: str) -> set:
    return set(norm(s).split())


def mult(opta: float, ref: float, exp: float) -> float:
    return round((opta / ref) ** exp, 4)


async def opta_list(cid: str) -> dict:
    doc = await db.league_lists.find_one({"career_id": cid}, {"_id": 0}, sort=[("revision", -1)])
    return doc if doc and doc.get("leagues") else BUILTIN | {"revision": 0}


def dedupe(rows: list) -> tuple:
    best, dups = {}, []
    for r in sorted(rows, key=lambda r: r["rank"]):
        k = (r["country"].lower(), norm(r["name"]))
        if k in best:
            dups.append(r | {"kept": best[k]["rank"]})
        else:
            best[k] = r
    return list(best.values()), dups


async def save_leagues(c: dict) -> list:
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players.league": 1, "players.gender": 1, "leagues": 1}) or {"players": []}
    info = {x["name"]: x for x in pool.get("leagues") or []}
    names = {p["league"]: p.get("gender", "M") for p in pool["players"]}
    names.setdefault(c.get("league") or "Premier Division", "M")
    out = []
    for n, g in sorted(names.items()):
        country, rep, gender = sample_reader.LEAGUE_INFO.get(n, (None, None, g))
        i = info.get(n, {})
        out.append({"name": n, "country": i.get("country", country), "reputation": i.get("reputation", rep), "gender": i.get("gender", gender)})
    return out


def _match(sl: dict, rows: list) -> tuple:
    cands = [r for r in rows if sl["country"] and r["country"].lower() == sl["country"].lower()] or rows
    t = toks(sl["name"]) - STOP or toks(sl["name"])
    def hit(r):
        return max(len(t & toks(n)) / max(1, len(t)) for n in [r["name"], *(r.get("aliases") or [])])
    scored = sorted(((hit(r), -r["rank"], r) for r in cands), key=lambda x: (x[0], x[1]), reverse=True)
    scored = [s for s in scored if s[0] > 0]
    if not scored:
        return None, "estimated", []
    top = scored[0]
    sure = bool(sl["country"]) and top[0] >= .99 and (len(scored) == 1 or scored[1][0] < top[0])
    return top[2], "matched" if sure else "unsure", [s[2]["name"] for s in scored[:5]]


def _place(rep, anchors: list, lo: float, hi: float) -> Optional[dict]:
    """Opta rating between the two listed leagues whose save reputation is nearest above and below (kept within the list's range)."""
    if rep is None or not anchors:
        return None
    above = min((a for a in anchors if a["reputation"] >= rep), key=lambda a: a["reputation"], default=None)
    below = max((a for a in anchors if a["reputation"] <= rep), key=lambda a: a["reputation"], default=None)
    if above and below and above["reputation"] != below["reputation"]:
        f = (rep - below["reputation"]) / (above["reputation"] - below["reputation"])
        opta = below["opta"] + f * (above["opta"] - below["opta"])
    elif len(anchors) >= 2 and not (above and below):
        a, b = sorted(anchors, key=lambda x: abs(x["reputation"] - rep))[:2]
        slope = (a["opta"] - b["opta"]) / ((a["reputation"] - b["reputation"]) or 1)
        opta = a["opta"] + slope * (rep - a["reputation"])
    else:
        opta = (above or below)["opta"]
    return {"opta": round(max(lo, min(hi, opta)), 3), "above": above and above["league"], "below": below and below["league"]}


async def _latest_edits(cid: str, kind: str) -> dict:
    pipeline = [{"$match": {"career_id": cid, "kind": kind}}, {"$sort": {"revision": -1}}, {"$group": {"_id": "$league", "doc": {"$first": "$$ROOT"}}}]
    return {d["_id"]: d["doc"] async for d in db.league_edits.aggregate(pipeline)}


def no_score(r: dict, unrated: list) -> dict:
    """Whether the league's strength comes from the workbook, and if not, why (in plain words)."""
    if r["status"] == "womens":
        return {"scored": False, "no_score": "Women's league: your workbook only rates men's football, so grades aren't league-adjusted"}
    if r["status"] != "estimated":
        return {"scored": True, "no_score": None}
    same = [u | {"rank": 9999} for u in unrated if r.get("country") and (u.get("country") or "").lower() == r["country"].lower()]
    hit, st, _ = _match(r, same) if same else (None, None, None)
    why = f"Your workbook lists {hit['name']} ({hit['country']}) but has no strength score for it" if hit and st == "matched" else "Not on your workbook's list"
    return {"scored": False, "no_score": why + ("; strength estimated from the save's league reputation" if r.get("opta") else "; treated as 1.0"), "unrated_name": hit and st == "matched" and hit["name"]}


async def resolve(c: dict, fresh_estimates: bool = False) -> dict:
    lst = await opta_list(c["id"])
    rows, dups = dedupe(lst["leagues"])
    by_name = {r["name"]: r for r in rows}
    ref, exp = lst["reference"], lst["exponent"]
    matches, medits = await _latest_edits(c["id"], "match"), await _latest_edits(c["id"], "multiplier")
    out = []
    for sl in await save_leagues(c):
        r = {**sl, "candidates": [], "opta_name": None, "opta": None, "status": None}
        if sl["gender"] == "F":
            r["status"] = "womens"
        elif sl["name"] in matches:
            hit = by_name.get(matches[sl["name"]]["value"] or "")
            r |= {"status": "confirmed" if hit else "estimated", "opta_name": hit and hit["name"], "opta": hit and hit["opta"], "rank": hit and hit["rank"]}
            r["candidates"] = _match(sl, rows)[2]
        else:
            hit, st, cands = _match(sl, rows)
            r |= {"status": st, "candidates": cands, "opta_name": hit and hit["name"], "opta": hit and hit["opta"], "rank": hit and hit["rank"]}
        out.append(r)
    anchors = [{"league": r["name"], "reputation": r["reputation"], "opta": r["opta"]} for r in out if r["opta"] is not None and r["reputation"] is not None and r["status"] != "estimated"]
    stored = await db.league_estimates.find_one({"career_id": c["id"]}, {"_id": 0}, sort=[("revision", -1)])
    lo, hi = min(r["opta"] for r in rows), max(r["opta"] for r in rows)
    placed = {r["name"]: _place(r["reputation"], anchors, lo, hi) for r in out if r["status"] == "estimated"}
    if not stored and placed and not fresh_estimates:
        stored = {"career_id": c["id"], "revision": 1, "values": placed, "at": now_iso(), "note": "First placement from reputation"}
        await db.league_estimates.insert_one(dict(stored))
    for r in out:
        if r["status"] == "estimated":
            est = placed.get(r["name"]) if fresh_estimates else ((stored or {}).get("values") or {}).get(r["name"]) or placed.get(r["name"])
            r |= {"opta": est and est["opta"], "between": est and [est["below"], est["above"]]}
        r |= no_score(r, lst.get("unrated") or [])
        base = mult(r["opta"], ref, exp) if r["opta"] else 1.0
        e = medits.get(r["name"])
        r["auto_multiplier"] = base
        r["edited"] = bool(e and e["value"] is not None)
        r["multiplier"] = e["value"] if r["edited"] else base
    return {"leagues": out, "list": {"revision": lst.get("revision", 0), "source": lst.get("source"), "updated": lst.get("updated"), "reference": ref,
                                      "exponent": exp, "count": len(lst["leagues"])}, "rows": rows, "duplicates": dups}


async def multipliers(c: dict) -> dict:
    return {r["name"]: {"multiplier": r["multiplier"], "status": r["status"], "scored": r["scored"], "no_score": r["no_score"]} for r in (await resolve(c))["leagues"]}


def _strength_word(gap: float, pct: float, target: str) -> str:
    if abs(gap) < 2:
        return f"{target} is about the same strength"
    return f"{target} is {abs(gap):.1f} points {'stronger' if gap > 0 else 'weaker'} ({abs(pct):.0f}% {'higher' if gap > 0 else 'lower'})"


@router.get("/compare")
async def compare_leagues(source: str = Query(..., max_length=120), target: str = Query(..., max_length=120), grade: float = Query(70, ge=20, le=100)):
    """Strength gap between two leagues and what FMCC's multiplier does to a player's grade. Arithmetic, not a prediction."""
    c = await active_career()
    d = await resolve(c)
    ref, exp = d["list"]["reference"], d["list"]["exponent"]
    save = {r["name"]: r for r in d["leagues"]}
    listed = {row_key(r): r for r in d["rows"]}

    def pick(name: str) -> dict:
        if name in save:
            r = save[name]
            return {"name": name, "in_save": True, "strength": r["opta"], "multiplier": r["multiplier"], "scored": r["scored"], "note": r["no_score"],
                    "listed_as": r["opta_name"], "rank": r.get("rank") if r["scored"] else None}
        if name in listed:
            r = listed[name]
            return {"name": f"{r['name']} ({r['country']})", "in_save": False, "strength": r["opta"], "multiplier": mult(r["opta"], ref, exp), "scored": True, "note": None,
                    "listed_as": f"{r['name']} ({r['country']})", "rank": r["rank"]}
        raise HTTPException(404, f"{name} isn't in your save or on the list")
    s, t = pick(source), pick(target)
    if s["strength"] is None or t["strength"] is None:
        missing = s if s["strength"] is None else t
        return {"source": s, "target": t, "comparable": False, "summary": f"{missing['name']} has no strength score, so FMCC can't compare these leagues."}
    gap, pct = round(t["strength"] - s["strength"], 2), (t["strength"] - s["strength"]) / s["strength"] * 100
    glob = round(20 + (grade - 20) * s["multiplier"], 1)
    tl_raw = 20 + (glob - 20) / t["multiplier"] if t["multiplier"] else None
    tl = round(min(100, max(20, tl_raw)), 1) if tl_raw is not None else None
    diff = round(tl - grade, 1) if tl is not None else None
    meaning = (f"A grade {grade:g} player in {s['name']} has a global grade of {glob:g}. In {t['name']} that global grade equals a local grade of about {tl:g}"
               + (" (capped at 100)" if tl_raw > 100 else " (floor of 20)" if tl_raw < 20 else "")
               + (f", so expect his grade to {'rise' if diff > 0 else 'drop'} by about {abs(diff):g} against the players there." if diff else ", about the same as now.")) if tl is not None else ""
    return {"source": s, "target": t, "comparable": True, "gap": gap, "gap_pct": round(pct, 1), "grade": grade, "global_grade": glob, "target_local": tl,
            "summary": _strength_word(gap, pct, t["name"]) + f" than {s['name']}.", "meaning": meaning,
            "scenarios": [{"beta": b, "grade": round(min(100, max(20, grade + b * (s["strength"] - t["strength"]))), 1)} for b in (0, .5, 1)],
            "caveat": "These follow FMCC's league multiplier and your workbook's scenario formula. Neither has been tested against real transfers, so treat them as a guide."}


@router.get("")
async def get_leagues():
    c = await active_career()
    d = await resolve(c)
    ref, exp = d["list"]["reference"], d["list"]["exponent"]
    d["rows"] = [r | {"multiplier": mult(r["opta"], ref, exp), "key": row_key(r)} for r in d["rows"]]
    return d


def row_key(r: dict) -> str:
    return r.get("id") or f"{r['name']}|{r.get('country') or ''}"


class MatchIn(BaseModel):
    opta_name: Optional[str] = Field(default=None, max_length=120)


@router.put("/{league}/match")
async def set_match(league: str, body: MatchIn):
    c = await active_career()
    d = await resolve(c)
    if league not in {r["name"] for r in d["leagues"]}:
        raise HTTPException(404, "League not in this save")
    if body.opta_name and body.opta_name not in {r["name"] for r in d["rows"]}:
        raise HTTPException(422, "That league isn't on the list")
    await _edit(c, league, "match", body.opta_name, f"{league} matched to {body.opta_name}" if body.opta_name else f"{league} marked as not on the list")
    return {"ok": True}


class MultIn(BaseModel):
    value: Optional[float] = Field(default=None, ge=0.05, le=2.0)


@router.put("/{league}/multiplier")
async def set_multiplier(league: str, body: MultIn):
    c = await active_career()
    if league not in {r["name"] for r in (await resolve(c))["leagues"]}:
        raise HTTPException(404, "League not in this save")
    await _edit(c, league, "multiplier", body.value, f"{league} multiplier set to {body.value}" if body.value is not None else f"{league} multiplier back to the formula")
    return {"ok": True}


async def _edit(c: dict, league: str, kind: str, value, note: str):
    rev = await next_revision("league_edits", {"career_id": c["id"], "league": league, "kind": kind})
    await db.league_edits.insert_one({"id": new_id(), "career_id": c["id"], "league": league, "kind": kind, "value": value, "revision": rev, "at": now_iso(), "note": note})
    await audit(c["id"], "league strength", "leagues", note)


@router.get("/{league}/history")
async def league_history(league: str):
    c = await active_career()
    return await db.league_edits.find({"career_id": c["id"], "league": league}, {"_id": 0}).sort("at", -1).to_list(100)


class RecalcIn(BaseModel):
    apply: bool = False
    reset_edits: bool = False


@router.post("/recalculate")
async def recalculate(body: RecalcIn):
    """Re-places every estimated league from the save's current reputations. Shows old and new values; saves only with apply."""
    c = await active_career()
    old, new = await resolve(c), await resolve(c, fresh_estimates=True)
    oldm = {r["name"]: r for r in old["leagues"]}
    diff = [{"league": r["name"], "old": oldm[r["name"]]["multiplier"], "new": r["auto_multiplier"] if (body.reset_edits or not r["edited"]) else r["multiplier"],
             "edited": r["edited"]} for r in new["leagues"] if r["status"] == "estimated" or (body.reset_edits and r["edited"])]
    if body.apply:
        values = {r["name"]: {"opta": r["opta"], "below": (r.get("between") or [None, None])[0], "above": (r.get("between") or [None, None])[1]}
                  for r in new["leagues"] if r["status"] == "estimated" and r["opta"]}
        rev = await next_revision("league_estimates", {"career_id": c["id"]})
        await db.league_estimates.insert_one({"career_id": c["id"], "revision": rev, "values": values, "at": now_iso(), "note": "Recalculated from reputations"})
        if body.reset_edits:
            for r in new["leagues"]:
                if r["edited"]:
                    await _edit(c, r["name"], "multiplier", None, f"{r['name']} multiplier reset by Recalculate")
        await audit(c["id"], "league strength", "leagues", f"Recalculated {len(values)} estimated leagues from reputations")
    return {"applied": body.apply, "changes": diff}


def _parse_list(name: str, raw: bytes) -> list:
    rows = []
    if name.lower().endswith(".xlsx"):
        import openpyxl
        wb = openpyxl.load_workbook(io.BytesIO(raw), data_only=True, read_only=True)
        for ws in wb.worksheets:
            it = ws.iter_rows(values_only=True)
            head = None
            for r in it:
                cells = [str(x or "").strip().lower() for x in r]
                if head is None and "competition" in cells and any("opta average" == x for x in cells):
                    head = {k: cells.index(k) for k in cells if k}
                    continue
                if head and isinstance(r[head.get("global rank", 0)], (int, float)):
                    rows.append({"rank": int(r[head["global rank"]]), "name": str(r[head["competition"]]), "country": str(r[head.get("country", 2)] or ""),
                                 "confed": str(r[head["confederation"]] or "") if "confederation" in head else "", "opta": float(r[head["opta average"]])})
            if rows:
                break
    else:
        for i, r in enumerate(csv.DictReader(io.StringIO(raw.decode("utf-8-sig")))):
            r = {k.strip().lower(): (v or "").strip() for k, v in r.items() if k}
            nm, op = r.get("competition") or r.get("league"), r.get("opta average") or r.get("opta") or r.get("rating")
            if nm and op:
                rows.append({"rank": int(float(r.get("global rank") or r.get("rank") or i + 1)), "name": nm, "country": r.get("country", ""), "confed": r.get("confederation", ""), "opta": float(op)})
    return rows


@router.post("/import")
async def import_list(file: UploadFile = File(...)):
    c = await active_career()
    raw = await file.read(5 * 1024 * 1024 + 1)
    if len(raw) > 5 * 1024 * 1024:
        raise HTTPException(413, "Keep the list under 5 MB")
    try:
        rows = _parse_list(file.filename or "", raw)
    except Exception:
        rows = []
    if len(rows) < 2:
        raise HTTPException(422, "No leagues found. Use the workbook's League Rankings sheet or a CSV with Competition, Country and Opta Average columns.")
    top = max(rows, key=lambda r: r["opta"])
    rev = await next_revision("league_lists", {"career_id": c["id"]})
    await db.league_lists.insert_one({"career_id": c["id"], "revision": rev, "source": (file.filename or "upload")[:120], "updated": None,
                                      "reference": top["opta"], "exponent": BUILTIN["exponent"], "leagues": rows, "at": now_iso()})
    await audit(c["id"], "league list imported", "leagues", f"{len(rows)} leagues from {file.filename}; reference {top['name']}")
    return {"ok": True, "count": len(rows), "reference": top["name"]}


@router.post("/use-builtin")
async def use_builtin():
    c = await active_career()
    rev = await next_revision("league_lists", {"career_id": c["id"]})
    await db.league_lists.insert_one({"career_id": c["id"], "revision": rev, "leagues": None, "source": "built-in", "at": now_iso()})
    await audit(c["id"], "league list", "leagues", "Back to the built-in list")
    return {"ok": True}
