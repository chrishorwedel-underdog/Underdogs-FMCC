"""Graphics tools: kits (upload or ChatGPT, with templates and bulk creation), the pack browser, staged bulk import and the graphics pack check.
The pack check only reports; FMCC never edits another pack's files."""
import asyncio
import io
import re
import zipfile
from pathlib import Path

from fastapi import APIRouter, HTTPException, UploadFile, File, Form, BackgroundTasks
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field

from core import db, active_career, now_iso, new_id, logger
from editor_api import (fm_dirs, _png, _store, _draw, _cut_background, latest, add_revision, rebuild, people, clubs, club, KIT_SLOTS, DraftIn,
                        _read_upload)

router = APIRouter(prefix="/api/editor")
MAX_ITEMS, MAX_TOTAL, MAX_ONE = 5000, 500 * 1024 * 1024, 5 * 1024 * 1024
TEMPLATES = {"plain": "a plain shirt in the main colour with contrasting collar and cuffs", "stripes": "vertical stripes", "hoops": "horizontal hoops",
             "sash": "a diagonal sash across the chest", "halves": "a halves design split down the middle", "quarters": "a quartered design",
             "pinstripes": "thin pinstripes", "chevron": "a chevron across the chest"}
SIZES = {"faces": 250, "logos": 360, "kits": 400}
BULK_JOBS: dict = {}


# ---------- kits ----------
@router.get("/kits")
async def list_kits(q: str = ""):
    c = await active_career()
    kits = {s: await latest(c["id"], f"kit_{s}") for s in KIT_SLOTS}
    ql = q.lower().strip()
    out = []
    for cl in await clubs(c):
        if ql and ql not in cl["name"].lower():
            continue
        out.append(cl | {"kits": {s: ((kits[s].get(cl["uid"]) or {}).get("value") or None) for s in KIT_SLOTS}})
    return out[:80]


@router.get("/kit-image/{uid}/{slot}")
async def kit_image(uid: int, slot: str):
    c = await active_career()
    if slot not in KIT_SLOTS:
        raise HTTPException(404, "Unknown kit")
    r = (await latest(c["id"], f"kit_{slot}")).get(uid)
    if not r or not r.get("value"):
        raise HTTPException(404, "No kit")
    return FileResponse(fm_dirs(c)["store"] / r["value"]["image"], media_type="image/png")


def _slot(slot: str):
    if slot not in KIT_SLOTS:
        raise HTTPException(404, "Kits are home, away or third")


@router.post("/kits/{uid}/{slot}")
async def upload_kit(uid: int, slot: str, file: UploadFile = File(...)):
    _slot(slot)
    c = await active_career()
    cl = await club(c, uid)
    img = _store(fm_dirs(c), await _read_upload(file, SIZES["kits"]))
    await add_revision(c, f"kit_{slot}", uid, cl["name"], {"image": img, "source": "Uploaded"}, f"{slot.title()} kit uploaded for {cl['name']}")
    return await rebuild(c)


@router.delete("/kits/{uid}/{slot}")
async def remove_kit(uid: int, slot: str):
    _slot(slot)
    c = await active_career()
    cl = await club(c, uid)
    await add_revision(c, f"kit_{slot}", uid, cl["name"], None, f"{slot.title()} kit removed for {cl['name']}")
    return await rebuild(c)


class KitGenIn(BaseModel):
    colours: list[str] = Field(min_length=1, max_length=3)
    template: str = Field(default="plain", pattern="^(" + "|".join(TEMPLATES) + ")$")
    notes: str = Field(default="", max_length=300)


async def _kit_draft(c: dict, uid: int, slot: str, body: KitGenIn) -> str:
    cl = await club(c, uid)
    name = ((((await latest(c["id"], "name")).get(uid) or {}).get("value")) or {}).get("long") or cl["name"]
    cols = ", ".join(x.strip()[:30] for x in body.colours if x.strip())
    if not cols:
        raise HTTPException(422, "Pick at least one kit colour")
    prompt = (f"A flat front view of a football shirt for the {slot} kit of a fictional club called '{name}'. Design: {TEMPLATES[body.template]}. Colours: {cols}. "
              "Short sleeves, centred, filling most of a square canvas, clean flat illustration, plain solid white background, "
              "no club badge, no sponsor, no real brand logos, no text, no mannequin, no shadow." + (f" Details: {body.notes.strip()}" if body.notes.strip() else ""))
    raw = await _draw(prompt, f"k{uid}{slot}", "kit")
    img = _store(fm_dirs(c), await asyncio.to_thread(_png, await asyncio.to_thread(_cut_background, raw), SIZES["kits"]))
    await db.face_drafts.insert_one({"id": new_id(), "career_id": c["id"], "uid": uid, "kind": "kit", "slot": slot, "image": img,
                                     "notes": f"{body.template}, {cols}" + (f", {body.notes.strip()}" if body.notes.strip() else ""), "at": now_iso()})
    return img


@router.post("/kits/{uid}/{slot}/generate")
async def generate_kit(uid: int, slot: str, body: KitGenIn):
    _slot(slot)
    c = await active_career()
    return {"draft": await _kit_draft(c, uid, slot, body)}


@router.post("/kits/{uid}/{slot}/use-draft")
async def use_kit_draft(uid: int, slot: str, body: DraftIn):
    _slot(slot)
    c = await active_career()
    cl = await club(c, uid)
    d = await db.face_drafts.find_one({"career_id": c["id"], "uid": uid, "kind": "kit", "slot": slot, "image": body.image}, {"_id": 0})
    if not d:
        raise HTTPException(404, "That draft wasn't made for this kit")
    await add_revision(c, f"kit_{slot}", uid, cl["name"], {"image": body.image, "source": "Created with ChatGPT"}, f"{slot.title()} kit created with ChatGPT: {d['notes']}")
    return await rebuild(c)


class BulkKitIn(BaseModel):
    uids: list[int] = Field(min_length=1, max_length=10)
    slot: str = Field(pattern="^(home|away|third)$")
    template: str = Field(default="plain", pattern="^(" + "|".join(TEMPLATES) + ")$")
    colours: list[str] = Field(min_length=1, max_length=3)


async def _run_bulk(job_id: str, c: dict, body: BulkKitIn):
    job = BULK_JOBS[job_id]
    for uid in body.uids:
        item = next(i for i in job["items"] if i["uid"] == uid)
        item["status"] = "creating"
        try:
            item["draft"] = await _kit_draft(c, uid, body.slot, KitGenIn(colours=body.colours, template=body.template))
            item["status"] = "ready"
        except HTTPException as e:
            item |= {"status": "failed", "error": e.detail}
        except Exception as exc:
            logger.warning("bulk kit failed: %s", exc)
            item |= {"status": "failed", "error": "ChatGPT couldn't create this one"}
    job["done"] = True


@router.post("/kits/bulk")
async def bulk_kits(body: BulkKitIn, tasks: BackgroundTasks):
    """Creates draft kits for up to 10 clubs one after another. Each draft waits for you to press 'Use'."""
    c = await active_career()
    if any(j for j in BULK_JOBS.values() if not j["done"]):
        raise HTTPException(409, "A bulk kit run is already going")
    names = {x["uid"]: x["name"] for x in await clubs(c)}
    if any(u not in names for u in body.uids):
        raise HTTPException(404, "A club isn't in this save")
    job_id = new_id()
    BULK_JOBS[job_id] = {"id": job_id, "slot": body.slot, "template": body.template, "done": False,
                         "items": [{"uid": u, "name": names[u], "status": "waiting", "draft": None} for u in body.uids]}
    tasks.add_task(_run_bulk, job_id, c, body)
    return BULK_JOBS[job_id]


@router.get("/kits/bulk/{job_id}")
async def bulk_status(job_id: str):
    if job_id not in BULK_JOBS:
        raise HTTPException(404, "Bulk run not found")
    return BULK_JOBS[job_id]


# ---------- packs ----------
REC = re.compile(r'<record\s+from="([^"]+)"\s+to="graphics/pictures/([^"]+)"')


def _target(to: str):
    m = re.match(r"(person|club)/(r-)?(\d+)/(portrait|logo|kits/(home|away|third))", to)
    return (m.group(1), int(m.group(3)), m.group(4)) if m else (None, None, None)


def _scan_packs(graphics: Path) -> dict:
    packs = {}
    if not graphics.is_dir():
        return packs
    for d in sorted(p for p in graphics.iterdir() if p.is_dir()):
        recs = []
        for cfg in d.rglob("config.xml"):
            for frm, to in REC.findall(cfg.read_text(errors="ignore")):
                base = cfg.parent / frm
                f = next((base.with_suffix(s) for s in (".png", ".jpg", ".jpeg") if base.with_suffix(s).exists()), base.with_suffix(".png"))
                kind, uid, what = _target(to)
                recs.append({"file": str(f), "rel": str(f.relative_to(d)) if f.is_relative_to(d) else f.name, "to": to, "kind": kind, "uid": uid, "what": what})
        loose = [p for p in d.rglob("*.png")][:1] if not recs else []
        packs[d.name] = {"name": d.name, "records": recs, "has_config": bool(recs) or any(d.rglob("config.xml")), "loose": bool(loose)}
    return packs


async def _names(c: dict) -> dict:
    return {"person": {p["unique_id"]: p["name"] for p in await people(c)}, "club": {x["uid"]: x["name"] for x in await clubs(c)}}


@router.get("/packs")
async def packs():
    c = await active_career()
    from editor_api import ng_index
    await ng_index(c)
    ps = await asyncio.to_thread(_scan_packs, fm_dirs(c)["graphics"])
    return [{"name": p["name"], "pictures": len(p["records"]), "faces": sum(1 for r in p["records"] if r["kind"] == "person"),
             "logos": sum(1 for r in p["records"] if r["what"] == "logo"), "kits": sum(1 for r in p["records"] if (r["what"] or "").startswith("kits"))} for p in ps.values()]


@router.get("/packs/{name}")
async def pack(name: str, offset: int = 0, limit: int = 60, q: str = ""):
    c = await active_career()
    ps = await asyncio.to_thread(_scan_packs, fm_dirs(c)["graphics"])
    if name not in ps:
        raise HTTPException(404, "Pack not found")
    names = await _names(c)
    rows = [r | {"owner": names.get(r["kind"] or "", {}).get(r["uid"]), "index": i} for i, r in enumerate(ps[name]["records"])]
    ql = q.lower().strip()
    if ql:
        rows = [r for r in rows if ql in (r["owner"] or "").lower() or ql in str(r["uid"])]
    return {"total": len(rows), "rows": [{k: v for k, v in r.items() if k != "file"} for r in rows[offset:offset + min(limit, 120)]]}


@router.get("/packs/{name}/picture/{index}")
async def pack_picture(name: str, index: int):
    c = await active_career()
    ps = await asyncio.to_thread(_scan_packs, fm_dirs(c)["graphics"])
    if name not in ps or not 0 <= index < len(ps[name]["records"]):
        raise HTTPException(404, "Picture not found")
    f = Path(ps[name]["records"][index]["file"])
    if not f.exists():
        raise HTTPException(404, "Picture missing")
    return FileResponse(f)


def _check(graphics: Path, people_ids: set, club_ids: set) -> dict:
    from PIL import Image
    ps = _scan_packs(graphics)
    missing, broken, not_in_save, by_target, checked = [], [], [], {}, 0
    for p in ps.values():
        for r in p["records"]:
            f = Path(r["file"])
            row = {"pack": p["name"], "to": r["to"], "uid": r["uid"], "file": r["rel"]}
            if not f.exists():
                missing.append(row)
                continue
            if checked < 3000:
                checked += 1
                try:
                    with Image.open(f) as im:
                        im.verify()
                except Exception:
                    broken.append(row)
            if r["uid"] is not None and r["uid"] not in (people_ids if r["kind"] == "person" else club_ids):
                not_in_save.append(row)
            by_target.setdefault(re.sub(r"/r-(\d+)/", r"/\1/", r["to"]), []).append(p["name"])
    conflicts = [{"to": t, "packs": sorted(set(v)), "likely_shown": sorted(set(v))[-1]} for t, v in by_target.items() if len(set(v)) > 1]
    return {"packs": [{"name": p["name"], "pictures": len(p["records"])} for p in ps.values()], "missing": missing[:500], "broken": broken[:500],
            "conflicts": conflicts[:500], "not_in_save": not_in_save[:500],
            "counts": {"missing": len(missing), "broken": len(broken), "conflicts": len(conflicts), "not_in_save": len(not_in_save)}, "checked_files": checked}


@router.get("/pack-check")
async def pack_check():
    c = await active_career()
    names = await _names(c)
    out = await asyncio.to_thread(_check, fm_dirs(c)["graphics"], set(names["person"]), set(names["club"]))
    return out | {"at": now_iso(), "note": "FM's load order between packs isn't documented, so 'likely shown' is FMCC's best guess (the pack that sorts last)."}


# ---------- staged bulk import ----------
def _parse_name(name: str, kind: str):
    stem = Path(name).stem.lower()
    m = re.search(r"(r-)?(\d{3,})", stem)
    if not m:
        return None, None, "No ID in the file name"
    slot = None
    if kind == "kits":
        slot = next((s for s in KIT_SLOTS if s in stem), None)
        if not slot:
            return int(m.group(2)), None, "Kit files need home, away or third in the name"
    return int(m.group(2)), slot, None


def _collect(uploads: list) -> list:
    """(name, bytes) for every picture in the uploads, opening zips. Enforces the import limits."""
    out, total = [], 0
    for name, blob in uploads:
        if name.lower().endswith(".zip"):
            with zipfile.ZipFile(io.BytesIO(blob)) as z:
                for info in z.infolist():
                    if info.is_dir() or not info.filename.lower().endswith((".png", ".jpg", ".jpeg")):
                        continue
                    if info.file_size > MAX_ONE:
                        out.append((info.filename, None))
                        continue
                    total += info.file_size
                    if total > MAX_TOTAL or len(out) >= MAX_ITEMS:
                        raise HTTPException(413, "An import holds up to 5,000 pictures and 500 MB")
                    out.append((info.filename, z.read(info)))
        else:
            data = blob
            total += len(data)
            if total > MAX_TOTAL or len(out) >= MAX_ITEMS:
                raise HTTPException(413, "An import holds up to 5,000 pictures and 500 MB")
            out.append((name, data if len(data) <= MAX_ONE else None))
    return out


@router.post("/bulk/stage")
async def bulk_stage(kind: str = Form(..., pattern="^(faces|logos|kits)$"), files: list[UploadFile] = File(...)):
    """Stages a folder or zip of pictures. Nothing is written until you press 'Write to FM'."""
    c = await active_career()
    dirs = fm_dirs(c)
    uploads, total = [], 0
    for i, f in enumerate(files[:MAX_ITEMS]):
        blob = await f.read(MAX_TOTAL + 1 - total)
        total += len(blob)
        if total > MAX_TOTAL:
            raise HTTPException(413, "An import holds up to 5,000 pictures and 500 MB")
        uploads.append((f.filename or f"file{i}", blob))
    items = await asyncio.to_thread(_collect, uploads)
    names = await _names(c)
    ids = names["person"] if kind == "faces" else names["club"]
    lk = {"faces": "face", "logos": "logo"}
    current = {s: await latest(c["id"], f"kit_{s}") for s in KIT_SLOTS} if kind == "kits" else {None: await latest(c["id"], lk[kind])}
    staged = []
    for n, (fname, data) in enumerate(items):
        uid, slot, problem = _parse_name(fname, kind)
        row = {"n": n, "file": Path(fname).name, "uid": uid, "slot": slot, "owner": ids.get(uid) if uid else None, "image": None}
        if data is None:
            problem = "Over 5 MB"
        if not problem:
            try:
                row["image"] = _store(dirs, await asyncio.to_thread(_png, data, SIZES[kind]))
            except HTTPException:
                problem = "Not a picture FMCC can read"
        if problem:
            row["status"] = "skipped"
            row["problem"] = problem
        elif uid not in ids:
            row["status"] = "not_in_save"
        else:
            row["status"] = "replace" if ((current.get(slot) or {}).get(uid) or {}).get("value") else "add"
        staged.append(row)
    doc = {"id": new_id(), "career_id": c["id"], "kind": kind, "items": staged, "state": "staged", "at": now_iso()}
    await db.bulk_imports.insert_one(dict(doc))
    return _summary(doc)


def _summary(doc: dict) -> dict:
    counts = {}
    for i in doc["items"]:
        counts[i["status"]] = counts.get(i["status"], 0) + 1
    return {k: v for k, v in doc.items() if k not in ("_id", "career_id")} | {"counts": counts}


@router.get("/bulk/{bid}")
async def bulk_get(bid: str):
    c = await active_career()
    doc = await db.bulk_imports.find_one({"id": bid, "career_id": c["id"]}, {"_id": 0})
    if not doc:
        raise HTTPException(404, "Import not found")
    return _summary(doc)


def _kind(doc: dict, item: dict) -> str:
    return {"faces": "face", "logos": "logo"}.get(doc["kind"]) or f"kit_{item['slot']}"


@router.post("/bulk/{bid}/write")
async def bulk_write(bid: str):
    c = await active_career()
    doc = await db.bulk_imports.find_one({"id": bid, "career_id": c["id"]}, {"_id": 0})
    if not doc or doc["state"] != "staged":
        raise HTTPException(409, "This import was already written or isn't staged")
    cache = {}
    for it in doc["items"]:
        if it["status"] not in ("add", "replace"):
            continue
        k = _kind(doc, it)
        cache.setdefault(k, await latest(c["id"], k))
        it["previous"] = (cache[k].get(it["uid"]) or {}).get("value")
        await add_revision(c, k, it["uid"], it["owner"] or str(it["uid"]), {"image": it["image"], "source": f"Bulk import {bid[:8]}"}, f"Bulk import: {it['file']}")
        it["written"] = True
    await db.bulk_imports.update_one({"id": bid}, {"$set": {"items": doc["items"], "state": "written", "written_at": now_iso()}})
    files = await rebuild(c)
    return _summary(doc | {"state": "written"}) | {"files": files}


@router.post("/bulk/{bid}/undo/{n}")
async def bulk_undo(bid: str, n: int):
    c = await active_career()
    doc = await db.bulk_imports.find_one({"id": bid, "career_id": c["id"]}, {"_id": 0})
    it = next((i for i in (doc or {}).get("items", []) if i["n"] == n), None)
    if not it or not it.get("written") or it.get("undone"):
        raise HTTPException(409, "Nothing to undo for this picture")
    await add_revision(c, _kind(doc, it), it["uid"], it["owner"] or str(it["uid"]), it.get("previous"), f"Bulk import undone: {it['file']}")
    it["undone"] = True
    await db.bulk_imports.update_one({"id": bid}, {"$set": {"items": doc["items"]}})
    return await rebuild(c)


@router.get("/bulk-image/{image}")
async def bulk_image(image: str):
    c = await active_career()
    if not re.fullmatch(r"[0-9a-f]{24}\.png", image) or not await db.bulk_imports.find_one({"career_id": c["id"], "items.image": image}):
        raise HTTPException(404, "No such picture")
    return FileResponse(fm_dirs(c)["store"] / image, media_type="image/png")


def zip_bytes(files: dict) -> bytes:
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w") as z:
        for n, d in files.items():
            z.writestr(n, d)
    return buf.getvalue()
