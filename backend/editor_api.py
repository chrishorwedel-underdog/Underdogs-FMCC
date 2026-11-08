"""Player & Teams Editor: faces (built on a user-installed NG_Regens pack), club logos, club renames (.lnc) and club attributes.
Every face/logo/name decision is an append-only revision; FMCC's graphics folder and .lnc file are rebuilt from the latest ones.
Browser preview: works on a sandbox FM folder with a SAMPLE NG_Regens pack (made-up portraits), not on a real install."""
import asyncio
import hashlib
import io
import os
import re
import shutil
import zlib
from pathlib import Path
from xml.sax.saxutils import quoteattr

from fastapi import APIRouter, HTTPException, UploadFile, File
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

import sample_reader
from core import db, active_career, latest_two, now_iso, new_id, audit, next_revision, logger

router = APIRouter(prefix="/api/editor")
LIVE = os.environ.get("FMCC_READER") == "fmsave"
ROOT = Path(__file__).parent
MAX_UPLOAD = 5 * 1024 * 1024
GENERATING: set[str] = set()
SAMPLE_CLUB_FIELDS = [("reputation", "Reputation", 0, 10000), ("balance", "Cash balance (£)", -500_000_000, 2_000_000_000),
                      ("transfer_budget", "Transfer budget (£)", 0, 2_000_000_000), ("wage_budget", "Wage budget (£/week)", 0, 50_000_000),
                      ("training", "Training facilities", 1, 20), ("youth_facilities", "Youth facilities", 1, 20), ("youth_coaching", "Youth coaching", 1, 20),
                      ("youth_recruitment", "Youth recruitment", 1, 20), ("corporate", "Corporate facilities", 1, 20), ("season_tickets", "Season tickets", 0, 200_000),
                      ("founded", "Year founded", 1800, 2100)]
NOT_EDITABLE = ["Owner and board personality or type", "Separate world, continental and national reputation", "Club name (use Rename instead)", "Nickname (no FM name-file command and no FMLibreEditor support yet)"]


# ---------- folders ----------
def fm_dirs(career: dict) -> dict:
    """graphics: FM's graphics folder; store: FMCC's own copy of every picture ever used (kept for history)."""
    if LIVE:
        from fm_game import DATA, game_root
        docs = Path(career["save_folder"]).parent
        return {"graphics": docs / "graphics", "store": DATA / "branding-store", "game": game_root(career["edition"])}
    base = ROOT / "preview_fm"
    return {"graphics": base / "graphics", "store": base / "store", "game": base / "game"}


def _png(raw: bytes, size: int) -> bytes:
    from PIL import Image
    try:
        im = Image.open(io.BytesIO(raw))
        im.load()
    except Exception:
        raise HTTPException(422, "That file isn't a picture FMCC can read (use PNG or JPEG)")
    im = im.convert("RGBA")
    im.thumbnail((size, size))
    out = io.BytesIO()
    im.save(out, "PNG")
    return out.getvalue()


def _store(dirs: dict, data: bytes) -> str:
    dirs["store"].mkdir(parents=True, exist_ok=True)
    h = hashlib.sha256(data).hexdigest()[:24]
    p = dirs["store"] / f"{h}.png"
    if not p.exists():
        p.write_bytes(data)
    return p.name


# ---------- NG_Regens ----------
def _sample_pack(ng: Path, uids: list[int]):
    """Browser preview only: a tiny made-up stand-in for NG_Regens (3 drawn portraits per folder) and its config.xml."""
    from PIL import Image, ImageDraw
    folders = ["Italy", "Netherlands", "Portugal", "England", "Brazil", "Spain", "Nigeria"]
    tones = [(241, 205, 170), (224, 186, 150), (198, 150, 110), (150, 104, 70), (110, 74, 50)]
    files = []
    for fi, f in enumerate(folders):
        (ng / f).mkdir(parents=True, exist_ok=True)
        for i in range(3):
            im = Image.new("RGB", (180, 180), (24 + i * 18, 34, 52 + fi * 12))
            d = ImageDraw.Draw(im)
            tone = tones[(fi + i) % len(tones)]
            d.ellipse((55, 30, 125, 110), fill=tone)
            d.ellipse((25, 115, 155, 230), fill=(40 + fi * 25, 60 + i * 40, 120))
            im.save(ng / f / f"{f.lower()}_{i + 1}.png")
            files.append(f"{f}/{f.lower()}_{i + 1}")
    recs = "".join(f'<record from="{files[u % len(files)]}" to="graphics/pictures/person/r-{u}/portrait"/>' for u in uids if u % 2 == 0)
    (ng / "config.xml").write_text(f'<record><boolean id="preload" value="false"/><boolean id="amap" value="false"/><list id="maps">{recs}</list></record>')


async def ng_index(career: dict) -> dict:
    """uid -> {file, newgen} from every config.xml inside NG_Regens, plus the picture folders."""
    dirs = fm_dirs(career)
    ng = dirs["graphics"] / "NG_Regens"
    if not LIVE and not (ng / "config.xml").exists():
        pool = await db.pools.find_one({"career_id": career["id"]}, {"_id": 0, "players.unique_id": 1}) or {"players": []}
        await asyncio.to_thread(_sample_pack, ng, [p["unique_id"] for p in pool["players"]])
    return await asyncio.to_thread(_read_ng, ng)


def _read_ng(ng: Path) -> dict:
    if not ng.is_dir():
        return {"installed": False, "folder": str(ng), "faces": {}, "folders": {}}
    faces = {}
    for cfg in ng.rglob("config.xml"):
        for frm, r, uid in re.findall(r'<record\s+from="([^"]+)"\s+to="graphics/pictures/person/(r-)?(\d+)/portrait"', cfg.read_text(errors="ignore")):
            faces[int(uid)] = {"file": str((cfg.parent / frm).with_suffix(".png")), "newgen": bool(r)}
    folders = {d.name: sorted(str(p) for p in d.glob("*.png")) for d in ng.iterdir() if d.is_dir()}
    return {"installed": True, "folder": str(ng), "faces": faces, "folders": {k: v for k, v in folders.items() if v}}


# ---------- revisions and the FMCC graphics folder ----------
async def latest(career_id: str, kind: str) -> dict:
    pipeline = [{"$match": {"career_id": career_id, "kind": kind}}, {"$sort": {"revision": -1}},
                {"$group": {"_id": "$target_uid", "doc": {"$first": "$$ROOT"}}}]
    return {d["_id"]: {k: v for k, v in d["doc"].items() if k != "_id"} async for d in db.branding.aggregate(pipeline)}


async def add_revision(c: dict, kind: str, uid: int, name: str, value: dict | None, note: str):
    rev = await next_revision("branding", {"career_id": c["id"], "kind": kind, "target_uid": uid})
    await db.branding.insert_one({"id": new_id(), "career_id": c["id"], "kind": kind, "target_uid": uid, "target_name": name,
                                  "revision": rev, "value": value, "at": now_iso(), "note": note})
    await audit(c["id"], f"{kind} {'changed' if value else 'removed'}", "editor", note, uid, name)


KIT_SLOTS = ("home", "away", "third")


def _write_graphics(dirs: dict, faces: dict, logos: dict, kits: dict | None = None) -> dict:
    out = dirs["graphics"] / "FMCC"
    out.mkdir(parents=True, exist_ok=True)
    keep, recs = set(), []
    groups = [("p", faces, ["person/{u}/portrait", "person/r-{u}/portrait"]), ("c", logos, ["club/{u}/logo"])]
    groups += [(f"k{s}", (kits or {}).get(s, {}), [f"club/{{u}}/kits/{s}"]) for s in KIT_SLOTS]
    for prefix, rows, paths in groups:
        for uid, r in rows.items():
            if not r.get("value"):
                continue
            name = f"{prefix}{uid}_{r['value']['image'][:8]}"
            shutil.copyfile(dirs["store"] / r["value"]["image"], out / f"{name}.png")
            keep.add(f"{name}.png")
            recs += [f'<record from={quoteattr(name)} to={quoteattr("graphics/pictures/" + t.format(u=uid))}/>' for t in paths]
    for f in out.glob("*.png"):
        if f.name not in keep:
            f.unlink()
    (out / "config.xml").write_text('<record>\n<boolean id="preload" value="false"/>\n<boolean id="amap" value="false"/>\n<list id="maps">\n'
                                    + "\n".join(recs) + "\n</list>\n</record>\n")
    return {"folder": str(out), "pictures": len(keep)}


def _lnc_dir(game: Path | None) -> Path | None:
    if not game:
        return None
    if not LIVE:
        return game / "data" / "database" / "db" / "2700" / "lnc" / "all"
    dbs = sorted((p for p in (game / "data" / "database" / "db").glob("*") if p.name.isdigit()), key=lambda p: int(p.name))
    return dbs[-1] / "lnc" / "all" if dbs else None


def _q(s: str) -> str:
    return s.replace('"', "'")


def _write_lnc(dirs: dict, names: dict, comps: dict | None = None, stadiums: dict | None = None) -> dict:
    d = _lnc_dir(dirs["game"])
    if not d:
        return {"ok": False, "message": "FM's game folder wasn't found, so renames can't be written"}
    d.mkdir(parents=True, exist_ok=True)
    f = d / "fmcc_club_names.lnc"
    lines = []
    for uid, r in names.items():
        if r.get("value"):
            lines += [f'"CLUB_LONG_NAME_CHANGE" {uid} "{_q(r["value"]["long"])}" ""', f'"CLUB_SHORT_NAME_CHANGE" {uid} "{_q(r["value"]["short"])}" ""']
    renames = len(lines) // 2
    for uid, r in (comps or {}).items():
        if r.get("value"):
            lines += [f'"COMP_LONG_NAME_CHANGE" {uid} "{_q(r["value"]["long"])}" ""', f'"COMP_SHORT_NAME_CHANGE" {uid} "{_q(r["value"]["short"])}" ""']
    for uid, r in (stadiums or {}).items():
        if r.get("value"):
            lines.append(f'"STADIUM_NAME_CHANGE" {uid} "{_q(r["value"]["long"])}" ""')
    if lines:
        f.write_text("\n".join(lines) + "\n", encoding="utf-8")
    elif f.exists():
        f.unlink()
    return {"ok": True, "file": str(f), "renames": renames, "lines": len(lines)}


async def rebuild(c: dict) -> dict:
    dirs = fm_dirs(c)
    faces, logos, names = await latest(c["id"], "face"), await latest(c["id"], "logo"), await latest(c["id"], "name")
    try:
        kits = {s: await latest(c["id"], f"kit_{s}") for s in KIT_SLOTS}
        g = await asyncio.to_thread(_write_graphics, dirs, faces, logos, kits)
        lnc = await asyncio.to_thread(_write_lnc, dirs, names, await latest(c["id"], "comp"), await latest(c["id"], "stadium"))
    except PermissionError:
        raise HTTPException(403, "Windows blocked access to FM's folders. Restart FMCC as administrator.")
    await db.settings.update_one({"_id": "app"}, {"$set": {"branding_files": {"graphics": g, "lnc": lnc, "at": now_iso()}}}, upsert=True)
    return {"graphics": g, "lnc": lnc}


# ---------- people and clubs ----------
async def people(c: dict) -> list:
    snaps = await latest_two(c["id"])
    out = {p["unique_id"]: p | {"club": p.get("club") or c["club_name"]} for p in (snaps[0]["players"] if snaps else [])}
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}) or {"players": []}
    for p in pool["players"]:
        out.setdefault(p["unique_id"], p)
    return list(out.values())


async def clubs(c: dict) -> list:
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "clubs": 1}) or {}
    if pool.get("clubs"):
        return pool["clubs"]
    rows = [{"uid": 900000, "name": c["club_name"], "league": "Premier Division"}]
    for league, names in sample_reader.LEAGUES.items():
        rows += [{"uid": 900000 + zlib.crc32(n.encode()) % 99999 + 1, "name": n, "league": league} for n in names]
    return rows


async def club(c: dict, uid: int) -> dict:
    hit = next((x for x in await clubs(c) if x["uid"] == uid), None)
    if not hit:
        raise HTTPException(404, "Club not found in this save")
    return hit


# ---------- routes: faces ----------
@router.get("/status")
async def status():
    c = await active_career()
    ng = await ng_index(c)
    files = (await db.settings.find_one({"_id": "app"}, {"_id": 0, "branding_files": 1}) or {}).get("branding_files")
    lnc_ok = None
    if files and files["lnc"].get("file") and (files["lnc"].get("lines") or files["lnc"].get("renames")):
        lnc_ok = await asyncio.to_thread(Path(files["lnc"]["file"]).exists)
    mapping = (await db.settings.find_one({"_id": "app"}, {"_id": 0, "nation_folders": 1}) or {}).get("nation_folders") or {}
    return {"desktop": LIVE, "ngregens": {"installed": ng["installed"], "folder": ng["folder"], "faces": len(ng["faces"]), "folders": sorted(ng["folders"])},
            "files": files, "lnc_present": lnc_ok, "nation_folders": mapping, "edition": c["edition"], "not_editable": NOT_EDITABLE}


@router.get("/players")
async def players(q: str = "", missing: bool = False, limit: int = 60):
    c = await active_career()
    ng, mine = await ng_index(c), await latest(c["id"], "face")
    rows = []
    for p in await people(c):
        m = mine.get(p["unique_id"])
        src = (m["value"]["source"] if m and m.get("value") else None) or ("NG_Regens" if p["unique_id"] in ng["faces"] else None)
        if q and q.lower() not in p["name"].lower() and q.lower() not in (p.get("club") or "").lower():
            continue
        if missing and src:
            continue
        rows.append({"unique_id": p["unique_id"], "name": p["name"], "age": p.get("age"), "club": p.get("club"), "nationality": p.get("nationality"),
                     "face": src, "custom": bool(m and m.get("value")), "revisions": m["revision"] if m else 0,
                     "image_rev": m["value"]["image"][:8] if m and m.get("value") else None})
    rows.sort(key=lambda r: (r["face"] is not None, r["name"]))
    return {"total": len(rows), "players": rows[:min(limit, 300)]}


@router.get("/image/{kind}/{uid}")
async def image(kind: str, uid: int):
    c = await active_career()
    if kind in ("face", "logo"):
        r = (await latest(c["id"], kind)).get(uid)
        if r and r.get("value"):
            return FileResponse(fm_dirs(c)["store"] / r["value"]["image"], media_type="image/png")
    if kind == "face":
        hit = (await ng_index(c))["faces"].get(uid)
        if hit and Path(hit["file"]).exists():
            return FileResponse(hit["file"], media_type="image/png")
    raise HTTPException(404, "No picture")


async def _read_upload(file: UploadFile, size: int) -> bytes:
    raw = await file.read(MAX_UPLOAD + 1)
    if len(raw) > MAX_UPLOAD:
        raise HTTPException(413, "Pictures can be at most 5 MB")
    return await asyncio.to_thread(_png, raw, size)


@router.post("/faces/{uid}")
async def upload_face(uid: int, file: UploadFile = File(...)):
    c = await active_career()
    p = next((x for x in await people(c) if x["unique_id"] == uid), None)
    if not p:
        raise HTTPException(404, "Player not found in this save")
    img = _store(fm_dirs(c), await _read_upload(file, 250))
    await add_revision(c, "face", uid, p["name"], {"image": img, "source": "Your picture"}, f"New face from {file.filename}")
    return await rebuild(c)


@router.delete("/faces/{uid}")
async def remove_face(uid: int):
    c = await active_career()
    cur = (await latest(c["id"], "face")).get(uid)
    if not cur or not cur.get("value"):
        raise HTTPException(409, "This player has no FMCC face to remove")
    await add_revision(c, "face", uid, cur["target_name"], None, "FMCC face removed: the NG_Regens face (if any) shows again")
    return await rebuild(c)


class NationFoldersIn(BaseModel):
    mapping: dict[str, str]


@router.put("/nation-folders")
async def set_nation_folders(body: NationFoldersIn):
    await db.settings.update_one({"_id": "app"}, {"$set": {"nation_folders": {k[:60]: v[:80] for k, v in body.mapping.items() if v}}}, upsert=True)
    return {"ok": True}


def _pick(files: list, used: set, uid: int, skip: str | None = None) -> str | None:
    free = [f for f in files if f not in used and f != skip] or [f for f in files if f != skip]
    return free[uid % len(free)] if free else None


async def _ng_face(c: dict, p: dict, ng: dict, used: set, mapping: dict, skip: str | None = None) -> str | None:
    folder = mapping.get(p.get("nationality") or "") or next((k for k in ng["folders"] if k.casefold() == (p.get("nationality") or "").casefold()), None)
    pick = _pick(ng["folders"].get(folder, []), used, p["unique_id"], skip) if folder else None
    if not pick:
        return None
    used.add(pick)
    img = _store(fm_dirs(c), await asyncio.to_thread(Path(pick).read_bytes))
    await add_revision(c, "face", p["unique_id"], p["name"], {"image": img, "source": f"NG_Regens · {folder}", "ng_file": pick}, f"NG_Regens face from {folder}")
    return folder


@router.post("/fill-missing-faces")
async def fill_missing():
    """Gives every player without any face an unused NG_Regens picture from the folder that matches their nationality."""
    c = await active_career()
    ng, mine = await ng_index(c), await latest(c["id"], "face")
    if not ng["installed"]:
        raise HTTPException(409, "Install NG_Regens first: unzip its picture pack into FM's graphics folder")
    mapping = (await db.settings.find_one({"_id": "app"}, {"_id": 0, "nation_folders": 1}) or {}).get("nation_folders") or {}
    used = {f["file"] for f in ng["faces"].values()} | {r["value"].get("ng_file") for r in mine.values() if r.get("value")}
    done, unmatched = 0, {}
    for p in await people(c):
        if p["unique_id"] in ng["faces"] or (mine.get(p["unique_id"]) or {}).get("value"):
            continue
        if await _ng_face(c, p, ng, used, mapping):
            done += 1
        else:
            unmatched[p.get("nationality") or "Unknown"] = unmatched.get(p.get("nationality") or "Unknown", 0) + 1
    files = await rebuild(c) if done else None
    return {"filled": done, "unmatched": unmatched, "files": files}


@router.post("/faces/{uid}/another")
async def another_face(uid: int):
    c = await active_career()
    p = next((x for x in await people(c) if x["unique_id"] == uid), None)
    if not p:
        raise HTTPException(404, "Player not found in this save")
    ng, mine = await ng_index(c), await latest(c["id"], "face")
    mapping = (await db.settings.find_one({"_id": "app"}, {"_id": 0, "nation_folders": 1}) or {}).get("nation_folders") or {}
    cur = (mine.get(uid) or {}).get("value") or {}
    used = {f["file"] for f in ng["faces"].values()} | {r["value"].get("ng_file") for r in mine.values() if r.get("value")}
    if not await _ng_face(c, p, ng, used, mapping, skip=cur.get("ng_file") or (ng["faces"].get(uid) or {}).get("file")):
        raise HTTPException(409, f"No NG_Regens folder is set for {p.get('nationality') or 'this nationality'}")
    return await rebuild(c)


# ---------- routes: clubs ----------
def _ng_path(ng: dict, rel: str) -> Path:
    base = Path(ng["folder"]).resolve()
    p = (base / rel).resolve()
    if not p.is_relative_to(base) or p.suffix.lower() != ".png" or not p.is_file():
        raise HTTPException(404, "That NG_Regens picture wasn't found")
    return p


@router.get("/ng-folder/{folder}")
async def ng_folder(folder: str, offset: int = 0, limit: int = 60):
    """One NG_Regens nationality folder, page by page, with who already uses each picture."""
    c = await active_career()
    ng, mine = await ng_index(c), await latest(c["id"], "face")
    files = ng["folders"].get(folder)
    if files is None:
        raise HTTPException(404, "That NG_Regens folder wasn't found")
    names = {p["unique_id"]: p["name"] for p in await people(c)}
    used = {}
    for uid, f in ng["faces"].items():
        if not (mine.get(uid) or {}).get("value"):
            used[str(Path(f["file"]).resolve())] = names.get(uid, f"Player {uid}")
    for uid, r in mine.items():
        if r.get("value") and r["value"].get("ng_file"):
            used[str(Path(r["value"]["ng_file"]).resolve())] = r["target_name"]
    base = Path(ng["folder"]).resolve()
    page = files[max(0, offset):max(0, offset) + min(limit, 120)]
    return {"folder": folder, "total": len(files), "offset": offset,
            "pictures": [{"id": str(Path(f).resolve().relative_to(base)).replace("\\", "/"), "used_by": used.get(str(Path(f).resolve()))} for f in page]}


@router.get("/ng-picture")
async def ng_picture(path: str):
    c = await active_career()
    return FileResponse(_ng_path(await ng_index(c), path), media_type="image/png")


class PickIn(BaseModel):
    path: str = Field(min_length=3, max_length=300)


class GenerateIn(BaseModel):
    notes: str = Field(default="", max_length=300)


class DraftIn(BaseModel):
    image: str = Field(pattern=r"^[0-9a-f]{24}\.png$")


async def _draw(prompt: str, lock: str, what: str) -> bytes:
    """One picture from ChatGPT (GPT Image 1.5). One request at a time per player or club, so repeated clicks don't spend credits twice."""
    from emergentintegrations.llm.openai.image_generation import OpenAIImageGeneration
    from dof_api import api_key
    key = api_key()
    if not key:
        raise HTTPException(409, f"Add your OpenAI key in Settings to create {what}s with ChatGPT")
    if lock in GENERATING:
        raise HTTPException(409, f"A {what} is already being created here")
    GENERATING.add(lock)
    try:
        images = await OpenAIImageGeneration(api_key=key).generate_images(prompt=prompt, model="gpt-image-1.5", number_of_images=1)
    except Exception as exc:
        logger.warning("%s generation failed: %s", what, exc)
        raise HTTPException(502, f"ChatGPT couldn't create a {what} just now. Please try again.")
    finally:
        GENERATING.discard(lock)
    if not images:
        raise HTTPException(502, "ChatGPT didn't return a picture. Please try again.")
    return images[0]


@router.post("/faces/{uid}/generate")
async def generate_face(uid: int, body: GenerateIn):
    """ChatGPT draws a draft face for a made-up person; nothing changes until you press 'Use this face'."""
    c = await active_career()
    p = next((x for x in await people(c) if x["unique_id"] == uid), None)
    if not p:
        raise HTTPException(404, "Player not found in this save")
    prompt = (f"Photorealistic head-and-shoulders portrait of a fictional {p.get('age') or 22}-year-old professional footballer from {p.get('nationality') or 'Europe'}, "
              "facing the camera, plain dark training top, neutral light-grey studio background, soft even lighting, square crop, "
              "in the style of a Football Manager facepack. No text, no logos, no watermark, not a real person."
              + (f" Details: {body.notes.strip()}" if body.notes.strip() else ""))
    raw = await _draw(prompt, f"p{uid}", "face")
    img = _store(fm_dirs(c), await asyncio.to_thread(_png, raw, 250))
    await db.face_drafts.insert_one({"id": new_id(), "career_id": c["id"], "uid": uid, "kind": "face", "image": img, "notes": body.notes.strip(), "at": now_iso()})
    return {"draft": img}


STYLES = {"classic": "a classic heraldic football crest with a shield outline", "modern": "a modern minimal flat football badge with simple geometric shapes",
          "roundel": "a retro circular roundel football badge with a ring around the emblem", "animal": "a football crest built around a bold animal emblem"}


class LogoGenIn(BaseModel):
    colours: list[str] = Field(min_length=1, max_length=3)
    style: str = Field(pattern="^(classic|modern|roundel|animal)$")
    notes: str = Field(default="", max_length=300)
    with_name: bool = True


def _cut_background(raw: bytes) -> bytes:
    """Makes the plain background around the badge transparent (flood fill from the corners), so it sits cleanly in FM."""
    from PIL import Image, ImageDraw
    im = Image.open(io.BytesIO(raw)).convert("RGBA")
    w, h = im.size
    for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
        ImageDraw.floodfill(im, xy, (0, 0, 0, 0), thresh=40)
    out = io.BytesIO()
    im.save(out, "PNG")
    return out.getvalue()


@router.post("/clubs/{uid}/logo/generate")
async def generate_logo(uid: int, body: LogoGenIn):
    """ChatGPT designs a draft badge from the club's name and your colours; nothing changes until you press 'Use this logo'."""
    c = await active_career()
    cl = await club(c, uid)
    names = (await latest(c["id"], "name")).get(uid)
    name = ((names or {}).get("value") or {}).get("long") or cl["name"]
    cols = ", ".join(x.strip()[:30] for x in body.colours if x.strip())
    if not cols:
        raise HTTPException(422, "Pick at least one club colour")
    prompt = (f"Design {STYLES[body.style]} for a fictional football club called '{name}'. Club colours: {cols}. "
              + (f"Include the text '{name}' clearly and spelled exactly. " if body.with_name else "No text or letters. ")
              + "Centred, filling most of a square canvas, flat vector look with clean edges, on a plain solid white background, "
              "no mock-up, no shadow, no watermark, not a copy of any real club's badge."
              + (f" Details: {body.notes.strip()}" if body.notes.strip() else ""))
    raw = await _draw(prompt, f"c{uid}", "logo")
    png = await asyncio.to_thread(_png, await asyncio.to_thread(_cut_background, raw), 360)
    img = _store(fm_dirs(c), png)
    await db.face_drafts.insert_one({"id": new_id(), "career_id": c["id"], "uid": uid, "kind": "logo", "image": img,
                                     "notes": f"{body.style}, {cols}" + (f", {body.notes.strip()}" if body.notes.strip() else ""), "at": now_iso()})
    return {"draft": img}


@router.post("/clubs/{uid}/logo/use-draft")
async def use_logo_draft(uid: int, body: DraftIn):
    c = await active_career()
    cl = await club(c, uid)
    d = await db.face_drafts.find_one({"career_id": c["id"], "uid": uid, "kind": "logo", "image": body.image}, {"_id": 0})
    if not d:
        raise HTTPException(404, "That draft wasn't made for this club")
    await add_revision(c, "logo", uid, cl["name"], {"image": body.image, "source": "Created with ChatGPT"}, f"Logo created with ChatGPT: {d['notes']}")
    return await rebuild(c)


@router.get("/drafts/{image}")
async def draft_image(image: str):
    c = await active_career()
    if not re.fullmatch(r"[0-9a-f]{24}\.png", image) or not await db.face_drafts.find_one({"career_id": c["id"], "image": image}):
        raise HTTPException(404, "No such draft")
    return FileResponse(fm_dirs(c)["store"] / image, media_type="image/png")


@router.post("/faces/{uid}/use-draft")
async def use_draft(uid: int, body: DraftIn):
    c = await active_career()
    d = await db.face_drafts.find_one({"career_id": c["id"], "uid": uid, "kind": {"$nin": ["logo", "kit"]}, "image": body.image}, {"_id": 0})
    if not d:
        raise HTTPException(404, "That draft wasn't made for this player")
    p = next((x for x in await people(c) if x["unique_id"] == uid), None)
    await add_revision(c, "face", uid, p["name"] if p else str(uid), {"image": body.image, "source": "Created with ChatGPT"},
                       "Face created with ChatGPT" + (f": {d['notes']}" if d["notes"] else ""))
    return await rebuild(c)


@router.post("/faces/{uid}/pick")
async def pick_face(uid: int, body: PickIn):
    c = await active_career()
    p = next((x for x in await people(c) if x["unique_id"] == uid), None)
    if not p:
        raise HTTPException(404, "Player not found in this save")
    ng = await ng_index(c)
    src = _ng_path(ng, body.path)
    folder = src.relative_to(Path(ng["folder"]).resolve()).parts[0]
    img = _store(fm_dirs(c), await asyncio.to_thread(src.read_bytes))
    await add_revision(c, "face", uid, p["name"], {"image": img, "source": f"NG_Regens · {folder}", "ng_file": str(src)}, f"Face picked from NG_Regens: {body.path}")
    return await rebuild(c)


@router.get("/clubs")
async def list_clubs(q: str = ""):
    c = await active_career()
    logos, names = await latest(c["id"], "logo"), await latest(c["id"], "name")
    out = []
    for x in await clubs(c):
        if q and q.lower() not in x["name"].lower():
            continue
        n, lg = (names.get(x["uid"]) or {}).get("value"), (logos.get(x["uid"]) or {}).get("value")
        out.append(x | {"rename": n, "logo": bool(lg), "logo_rev": lg["image"][:8] if lg else None})
    return out[:200]


@router.post("/clubs/{uid}/logo")
async def upload_logo(uid: int, file: UploadFile = File(...)):
    c = await active_career()
    cl = await club(c, uid)
    img = _store(fm_dirs(c), await _read_upload(file, 360))
    await add_revision(c, "logo", uid, cl["name"], {"image": img, "source": "Your picture"}, f"New logo from {file.filename}")
    return await rebuild(c)


@router.delete("/clubs/{uid}/logo")
async def remove_logo(uid: int):
    c = await active_career()
    cl = await club(c, uid)
    await add_revision(c, "logo", uid, cl["name"], None, "FMCC logo removed")
    return await rebuild(c)


class NameIn(BaseModel):
    long: str = Field(min_length=2, max_length=60, pattern=r'^[^\x00-\x1f"]+$')
    short: str = Field(min_length=2, max_length=30, pattern=r'^[^\x00-\x1f"]+$')


@router.put("/clubs/{uid}/name")
async def rename(uid: int, body: NameIn):
    c = await active_career()
    cl = await club(c, uid)
    await add_revision(c, "name", uid, cl["name"], {"long": body.long.strip(), "short": body.short.strip()}, f"Renamed to {body.long.strip()} ({body.short.strip()})")
    return await rebuild(c)


@router.delete("/clubs/{uid}/name")
async def remove_rename(uid: int):
    c = await active_career()
    cl = await club(c, uid)
    await add_revision(c, "name", uid, cl["name"], None, "Rename removed: FM's own name shows again")
    return await rebuild(c)


@router.post("/rewrite")
async def rewrite():
    return await rebuild(await active_career())


@router.get("/history/{kind}/{uid}")
async def history(kind: str, uid: int):
    c = await active_career()
    return await db.branding.find({"career_id": c["id"], "kind": kind, "target_uid": uid}, {"_id": 0}).sort("revision", -1).to_list(50)


# ---------- routes: club attributes ----------
def sample_value(uid: int, key: str, lo: int, hi: int) -> int:
    if key == "founded":
        return 1870 + zlib.crc32(f"{uid}{key}".encode()) % 120
    span = min(hi, 20 if hi <= 20 else 9000 if key == "reputation" else 40_000 if key == "season_tickets" else 60_000_000) - max(lo, 0)
    return max(lo, 0) + 1 + zlib.crc32(f"{uid}{key}".encode()) % span


async def club_values(c: dict, uid: int) -> list:
    if LIVE:
        import live_editor
        try:
            vals = await asyncio.to_thread(live_editor.read_all, "club", uid)
        except live_editor.AdminNeeded as exc:
            raise HTTPException(403, str(exc))
        except Exception as exc:
            raise HTTPException(409, f"FMLibreEditor couldn't read this club. Start FM27 with this save loaded. ({exc})")
        return [{"key": k, "label": k.replace("_", " ").replace(".", " · ").capitalize(), "value": v, "min": None, "max": None} for k, v in vals.items()]
    edits = await db.club_edits.find_one({"career_id": c["id"], "uid": uid}, {"_id": 0}) or {}
    return [{"key": k, "label": lbl, "value": edits.get(k, sample_value(uid, k, lo, hi)), "min": lo, "max": hi} for k, lbl, lo, hi in SAMPLE_CLUB_FIELDS]


@router.get("/clubs/{uid}/attributes")
async def club_attributes(uid: int):
    c = await active_career()
    cl = await club(c, uid)
    if LIVE and c["edition"] != "FM27":
        return {"club": cl, "fields": [], "read_only": "FM26 saves stay read-only, because FMLibreEditor only supports FM27", "not_editable": NOT_EDITABLE}
    return {"club": cl, "fields": await club_values(c, uid), "read_only": None, "not_editable": NOT_EDITABLE}


class AttrIn(BaseModel):
    values: dict[str, int] = Field(min_length=1, max_length=40)


@router.post("/clubs/{uid}/attributes")
async def queue_attributes(uid: int, body: AttrIn):
    """Club edits go into Game changes, so they get the same preview, checks, backup, read-back and undo as player changes."""
    from changes_api import queue_club_edit
    c = await active_career()
    cl = await club(c, uid)
    fields = {f["key"]: f for f in await club_values(c, uid)}
    for k, v in body.values.items():
        f = fields.get(k)
        if not f:
            raise HTTPException(422, f"{k} can't be edited")
        if f["min"] is not None and not f["min"] <= v <= f["max"]:
            raise HTTPException(422, f"{f['label']} must be between {f['min']} and {f['max']}")
    n = 0
    for k, v in body.values.items():
        if v != fields[k]["value"]:
            await queue_club_edit(c, cl, k, fields[k]["label"], v)
            n += 1
    return {"queued": n}
