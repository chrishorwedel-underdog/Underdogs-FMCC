"""Licensing fix: finds unlicensed clubs and competitions by reading community real-names fix files (.lnc), finds real logos in
the logo packs already in FM's graphics folder, and applies real names through FMCC's own name file. Manual fixes too.
Browser preview: a SAMPLE fix file and SAMPLE logo pack are generated in the sandbox FM folder."""
import asyncio
import re
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File
from pydantic import BaseModel, Field

from core import db, active_career, logger
from editor_api import LIVE, fm_dirs, clubs, latest, add_revision, rebuild, _lnc_dir

router = APIRouter(prefix="/api/editor/licensing")
LINE = re.compile(r'^\s*"(\w+)"\s+(\d+)\s+"([^"]*)"', re.M)
CLUB_LONG, CLUB_SHORT = {"CLUB_LONG_NAME_CHANGE", "LONG_NAME_CHANGE"}, {"CLUB_SHORT_NAME_CHANGE", "SHORT_NAME_CHANGE"}
OURS = "fmcc_club_names.lnc"
SAFE_NAME = r'^[^\x00-\x1f"]+$'


def _fix_dirs(c: dict) -> tuple[Path | None, Path]:
    dirs = fm_dirs(c)
    if LIVE:
        from fm_game import DATA
        return _lnc_dir(dirs["game"]), DATA / "fixes"
    return _lnc_dir(dirs["game"]), dirs["store"].parent / "fixes"


def _sample(c_lnc: Path, graphics: Path, club_rows: list):
    """Browser preview only: a made-up 'real names fix' and logo pack for a few sample clubs."""
    from PIL import Image, ImageDraw
    picks = club_rows[1:4]
    c_lnc.mkdir(parents=True, exist_ok=True)
    lines = ["# SAMPLE real-names fix (browser preview)"]
    for x in picks:
        lines += [f'"CLUB_LONG_NAME_CHANGE" {x["uid"]} "{x["name"]} Football Club" ""', f'"CLUB_SHORT_NAME_CHANGE" {x["uid"]} "{x["name"].split()[0]}" ""']
    lines += ['"COMP_LONG_NAME_CHANGE" 950001 "Sample Premier Division (real name)" ""', '"COMP_SHORT_NAME_CHANGE" 950001 "Premier Div" ""']
    (c_lnc / "sample_real_names_fix.lnc").write_text("\n".join(lines) + "\n")
    pack = graphics / "Sample Logo Pack"
    pack.mkdir(parents=True, exist_ok=True)
    recs = []
    for i, x in enumerate(picks[:2]):
        im = Image.new("RGBA", (200, 200), (0, 0, 0, 0))
        ImageDraw.Draw(im).polygon([(100, 10), (185, 45), (170, 150), (100, 192), (30, 150), (15, 45)], fill=(200 - i * 120, 40 + i * 60, 60 + i * 120, 255))
        im.save(pack / f"logo{x['uid']}.png")
        recs.append(f'<record from="logo{x["uid"]}" to="graphics/pictures/club/{x["uid"]}/logo"/>')
    (pack / "config.xml").write_text(f'<record><list id="maps">{"".join(recs)}</list></record>')


def _parse(path: Path) -> dict:
    out = {"clubs": {}, "comps": {}, "stadiums": {}}
    for cmd, uid, name in LINE.findall(path.read_text(encoding="utf-8", errors="ignore")):
        uid = int(uid)
        if cmd in CLUB_LONG or cmd == "NAME_CHANGE":
            out["clubs"].setdefault(uid, {})["long" if cmd != "NAME_CHANGE" else "name"] = name
        elif cmd in CLUB_SHORT:
            out["clubs"].setdefault(uid, {})["short"] = name
        elif cmd.startswith("COMP_") and "NAME_CHANGE" in cmd:
            out["comps"].setdefault(uid, {})["long" if "LONG" in cmd else "short"] = name
        elif cmd == "STADIUM_NAME_CHANGE":
            out["stadiums"][uid] = {"long": name}
    return out


def _logo_packs(graphics: Path) -> tuple[dict, list]:
    found, packs = {}, []
    if not graphics.is_dir():
        return found, packs
    for top in graphics.iterdir():
        if not top.is_dir() or top.name in ("FMCC", "NG_Regens"):
            continue
        n = 0
        for cfg in top.rglob("config.xml"):
            for uid in re.findall(r'to="graphics/pictures/club/(\d+)/logo"', cfg.read_text(errors="ignore")):
                found.setdefault(int(uid), top.name)
                n += 1
        if n:
            packs.append({"name": top.name, "logos": n})
    return found, packs


def _scan_files(lnc: Path | None, imported: Path) -> list:
    files = []
    for folder, active in ((lnc, True), (imported, False)):
        if folder and folder.is_dir():
            files += [{"name": f.name, "path": str(f), "active": active, **_parse(f)} for f in sorted(folder.glob("*.lnc")) if f.name != OURS]
    return files


@router.get("/scan")
async def scan():
    c = await active_career()
    lnc, imported = _fix_dirs(c)
    graphics = fm_dirs(c)["graphics"]
    rows = await clubs(c)
    if not LIVE and lnc and not (lnc / "sample_real_names_fix.lnc").exists():
        await asyncio.to_thread(_sample, lnc, graphics, rows)
    try:
        files = await asyncio.to_thread(_scan_files, lnc, imported)
        logos, packs = await asyncio.to_thread(_logo_packs, graphics)
    except PermissionError:
        raise HTTPException(403, "Windows blocked access to FM's folders. Restart FMCC as administrator.")
    names, comps_done, mine_logos = await latest(c["id"], "name"), await latest(c["id"], "comp"), await latest(c["id"], "logo")
    by_uid = {x["uid"]: x for x in rows}
    club_out, comp_out, seen = [], [], set()
    for f in files:
        for uid, n in f["clubs"].items():
            real = n.get("long") or n.get("name")
            if uid in seen or not real:
                continue
            seen.add(uid)
            cur = by_uid.get(uid)
            mine = ((names.get(uid) or {}).get("value") or {}).get("long")
            applied = mine == real[:60]
            club_out.append({"uid": uid, "current": cur["name"] if cur else None, "in_save": bool(cur), "real_long": real, "real_short": n.get("short") or real,
                             "source": f["name"], "active_in_fm": f["active"], "applied": applied, "unlicensed": bool(cur) and cur["name"] != real,
                             "conflict": mine if mine and not applied else None,
                             "logo_pack": logos.get(uid), "fmcc_logo": bool((mine_logos.get(uid) or {}).get("value"))})
        for uid, n in f["comps"].items():
            if uid in {x["uid"] for x in comp_out}:
                continue
            comp_out.append({"uid": uid, "real_long": n.get("long") or n.get("short"), "real_short": n.get("short") or n.get("long"), "source": f["name"],
                             "active_in_fm": f["active"], "applied": ((comps_done.get(uid) or {}).get("value") or {}).get("long") == (n.get("long") or n.get("short"))})
    club_out.sort(key=lambda x: (not x["unlicensed"], x["current"] or x["real_long"]))
    listed = {x["uid"] for x in comp_out}
    stadiums = await latest(c["id"], "stadium")
    my_fixes = [{"kind": "comp", "uid": u, "name": r["value"]["long"], "short": r["value"]["short"]} for u, r in comps_done.items() if r.get("value") and u not in listed]
    my_fixes += [{"kind": "stadium", "uid": u, "name": r["value"]["long"], "short": None} for u, r in stadiums.items() if r.get("value")]
    return {"desktop": LIVE, "lnc_folder": str(lnc) if lnc else None, "import_folder": str(imported),
            "files": [{"name": f["name"], "active": f["active"], "clubs": len(f["clubs"]), "comps": len(f["comps"]), "stadiums": len(f["stadiums"])} for f in files],
            "clubs": club_out, "comps": comp_out, "logo_packs": packs, "my_fixes": my_fixes,
            "to_fix": sum(1 for x in club_out if x["unlicensed"] and not x["applied"] and not x["active_in_fm"])}


@router.post("/import")
async def import_fix(file: UploadFile = File(...)):
    """Keeps a copy of a real-names fix file in FMCC's own folder; nothing is applied until you press Apply."""
    c = await active_career()
    if not (file.filename or "").lower().endswith(".lnc"):
        raise HTTPException(422, "Choose a .lnc file from the real-names fix")
    raw = await file.read(2 * 1024 * 1024 + 1)
    if len(raw) > 2 * 1024 * 1024:
        raise HTTPException(413, "Fix files can be at most 2 MB")
    text = raw.decode("utf-8", errors="ignore")
    if not LINE.search(text):
        raise HTTPException(422, "That file has no name changes FMCC understands")
    _, imported = _fix_dirs(c)
    imported.mkdir(parents=True, exist_ok=True)
    name = re.sub(r"[^\w.\- ]", "_", Path(file.filename).name)[:80]
    if name == OURS:
        raise HTTPException(422, "Rename the file first")
    (imported / name).write_text(text, encoding="utf-8")
    return {"name": name}


@router.delete("/import/{name}")
async def remove_import(name: str):
    c = await active_career()
    _, imported = _fix_dirs(c)
    p = (imported / name).resolve()
    if not p.is_relative_to(imported.resolve()) or not p.is_file():
        raise HTTPException(404, "That imported fix file wasn't found")
    p.unlink()
    return {"ok": True}


class ApplyIn(BaseModel):
    clubs: list[int] = Field(default_factory=list, max_length=5000)
    comps: list[int] = Field(default_factory=list, max_length=2000)


@router.post("/apply")
async def apply(body: ApplyIn):
    c = await active_career()
    s = await scan()
    want_c, want_k = set(body.clubs), set(body.comps)
    n = 0
    for x in s["clubs"]:
        if x["uid"] in want_c and x["in_save"] and x["unlicensed"] and not x["applied"] and not x["active_in_fm"]:
            await add_revision(c, "name", x["uid"], x["current"], {"long": x["real_long"][:60], "short": x["real_short"][:30], "fix": x["source"]},
                               f"Real name from {x['source']}: {x['real_long']}")
            n += 1
    for x in s["comps"]:
        if x["uid"] in want_k and not x["applied"] and not x["active_in_fm"]:
            await add_revision(c, "comp", x["uid"], x["real_long"], {"long": x["real_long"][:60], "short": x["real_short"][:30], "fix": x["source"]},
                               f"Real competition name from {x['source']}: {x['real_long']}")
            n += 1
    if not n:
        raise HTTPException(409, "Nothing new to apply")
    files = await rebuild(c)
    logger.info("licensing fix applied: %s", n)
    return {"applied": n, "files": files}


class ManualIn(BaseModel):
    long: str = Field(min_length=2, max_length=60, pattern=SAFE_NAME)
    short: str = Field(min_length=2, max_length=30, pattern=SAFE_NAME)
    founded: int | None = Field(default=None, ge=1800, le=2100)
    stadium_id: int | None = Field(default=None, ge=1)
    stadium_name: str | None = Field(default=None, min_length=2, max_length=60, pattern=SAFE_NAME)


@router.post("/manual/club/{uid}")
async def manual_club(uid: int, body: ManualIn):
    """Your own fix for one club: real name and short name (name file), stadium (name file, needs FM's stadium ID) and year founded (Game changes)."""
    from editor_api import club, club_values
    from changes_api import queue_club_edit
    c = await active_career()
    cl = await club(c, uid)
    if bool(body.stadium_id) != bool(body.stadium_name):
        raise HTTPException(422, "Give both the stadium's ID and its real name")
    await add_revision(c, "name", uid, cl["name"], {"long": body.long.strip(), "short": body.short.strip(), "fix": "manual"}, f"Real name set by you: {body.long.strip()}")
    if body.stadium_id:
        await add_revision(c, "stadium", body.stadium_id, body.stadium_name.strip(), {"long": body.stadium_name.strip(), "club_uid": uid}, f"Real stadium name for {cl['name']}: {body.stadium_name.strip()}")
    queued = False
    if body.founded is not None:
        fields = {f["key"]: f for f in await club_values(c, uid)}
        if "founded" not in fields:
            raise HTTPException(409, "FMLibreEditor can't change the year founded for this club. The name was saved.")
        if fields["founded"]["value"] != body.founded:
            await queue_club_edit(c, cl, "founded", "Year founded", body.founded)
            queued = True
    return {"files": await rebuild(c), "founded_queued": queued}


class CompIn(BaseModel):
    long: str = Field(min_length=2, max_length=60, pattern=SAFE_NAME)
    short: str = Field(min_length=2, max_length=30, pattern=SAFE_NAME)


@router.post("/manual/comp/{uid}")
async def manual_comp(uid: int, body: CompIn):
    c = await active_career()
    await add_revision(c, "comp", uid, body.long.strip(), {"long": body.long.strip(), "short": body.short.strip(), "fix": "manual"}, f"Real competition name set by you: {body.long.strip()}")
    return {"files": await rebuild(c)}


@router.delete("/{kind}/{uid}")
async def undo_fix(kind: str, uid: int):
    if kind not in ("name", "comp", "stadium"):
        raise HTTPException(404, "Unknown fix")
    c = await active_career()
    cur = (await latest(c["id"], kind)).get(uid)
    if not cur or not cur.get("value"):
        raise HTTPException(409, "Nothing to undo")
    await add_revision(c, kind, uid, cur["target_name"], None, "Fix removed: FM's own name shows again")
    return {"files": await rebuild(c)}
