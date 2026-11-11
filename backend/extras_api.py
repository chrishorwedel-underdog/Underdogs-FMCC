"""Extras FMCC can't ship (third-party packs): what each is for, whether it's found, one-click install from Downloads, update checks."""
import asyncio
import logging
import os
import re
import shutil
import tempfile
import time
import zipfile
from datetime import datetime, timezone
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

import editor_api
from editor_api import LIVE, fm_dirs, ROOT
from core import db, active_career, now_iso, new_id, audit

router = APIRouter(prefix="/api/extras")
logger = logging.getLogger(__name__)
OURS_LNC = "fmcc_club_names.lnc"
RNF_PAGE = {"FM26": "https://sortitoutsi.net/content/74677/fm26-real-name-fix", "FM27": "https://sortitoutsi.net/search?q=FM27+real+name+fix"}
ITEMS = [
    {"key": "ng_regens", "name": "NG_Regens newgen faces", "by": "NG_Regens", "needed": True, "kind": "installer", "pattern": r"ng.?regens.*\.exe$",
     "for": "Faces for computer-generated players, used by Player faces and the Player Creator's face matching",
     "page": "https://ngregens.org/", "how": "Download the NG_Regens Manager. FMCC finds it in Downloads and starts its installer; the Manager then installs and updates the faces itself."},
    {"key": "real_name_fix", "name": "sortitoutsi Real Name Fix", "by": "sortitoutsi", "needed": True, "kind": "zip", "pattern": r"real.?names?.?fix.*\.zip$",
     "for": "Real club, competition, award and stadium names, used by the Licensing fix",
     "page": None, "how": "Download the zip for your FM version. FMCC backs up the game's dbc, edt and lnc folders, puts the fix's folders in their place and copies its .fmf files into editor data."},
    {"key": "logos", "name": "Logo pack", "by": "sortitoutsi (or any logo pack)", "needed": False, "kind": "zip", "pattern": r"logo.*\.zip$",
     "for": "Real club and competition logos in FM and in FMCC's Clubs tab", "page": "https://sortitoutsi.net/graphics",
     "how": "Download a logo pack zip. FMCC unpacks it into FM's graphics folder."},
    {"key": "kits", "name": "Kit pack", "by": "sortitoutsi (or any kit pack)", "needed": False, "kind": "zip", "pattern": r"kit.*\.zip$",
     "for": "Real kits in FM and in FMCC's Kits tab", "page": "https://sortitoutsi.net/graphics",
     "how": "Download a kit pack zip. FMCC unpacks it into FM's graphics folder."},
]
BUILT_IN = [("fmsave", "Reads your saves"), ("FMLibreEditor", "Makes FM27 game edits"), ("FMMatchLens + BepInEx", "Match analytics; FMCC installs it from Connections"),
            ("ScoutSheet", "Scouting engine inside Scout Players"), ("League strength workbook", "408 rated competitions"),
            ("Stats Table, Role Fit and Player Dossiers", "Inside Scout Players"), ("Transfer Market and Club Analysis", "Their own menu pages")]
_CHECK = {"data": {}, "at": {}}


def _paths(c: dict) -> dict:
    d = fm_dirs(c)
    if LIVE:
        from fm_game import DATA
        return d | {"downloads": Path.home() / "Downloads", "editor_data": Path(c["save_folder"]).parent / "editor data", "backups": DATA / "extras-backups"}
    base = ROOT / "preview_fm"
    return d | {"downloads": base / "Downloads", "editor_data": base / "editor data", "backups": base / "extras-backups"}


def _db_dirs(game: Path | None) -> list:
    if not game:
        return []
    roots = [game / "shared" / "data" / "database" / "db", game / "data" / "database" / "db"]
    return [p for r in roots if r.is_dir() for p in sorted(r.iterdir()) if p.is_dir() and p.name.isdigit()]


def _sample_downloads(p: dict):
    """Browser preview only: tiny SAMPLE downloads so the install buttons can be tried."""
    dl = p["downloads"]
    dl.mkdir(parents=True, exist_ok=True)
    exe = dl / "SAMPLE NG_Regens Manager Setup.exe"
    if not exe.exists():
        exe.write_text("SAMPLE - not a real installer")
    rnf = dl / "SAMPLE Real Name Fix FM27.zip"
    if not rnf.exists():
        with zipfile.ZipFile(rnf, "w") as z:
            z.writestr("Real Name Fix/dbc/permanent/sample_fix.dbc", "SAMPLE")
            z.writestr("Real Name Fix/edt/permanent/sample_fix.edt", "SAMPLE")
            z.writestr("Real Name Fix/lnc/all/sample_real_names_fix.lnc", '"CLUB_LONG_NAME_CHANGE" 1 "Sample Real Club"\n')
            z.writestr("Real Name Fix/editor data/sample_fix.fmf", "SAMPLE")
    kits = dl / "SAMPLE Kits Pack.zip"
    if not kits.exists():
        with zipfile.ZipFile(kits, "w") as z:
            z.writestr("Sample Kits/config.xml", "<record></record>")
    p["game"] and (p["game"] / "data" / "database" / "db" / "2700").mkdir(parents=True, exist_ok=True)


def _newest(folder: Path, pattern: str):
    if not pattern or not folder.is_dir():
        return None
    files = [f for f in folder.iterdir() if f.is_file() and re.search(pattern, f.name, re.I)]
    return max(files, key=lambda f: f.stat().st_mtime) if files else None


def _found(key: str, p: dict) -> tuple[bool, str]:
    g = p["graphics"]
    if key == "ng_regens":
        ok = (g / "NG_Regens" / "config.xml").exists()
        return ok, "Faces found in FM's graphics folder" if ok else "Not found in FM's graphics folder"
    if key == "real_name_fix":
        n = sum(1 for d in _db_dirs(p["game"]) for f in (d / "lnc" / "all").glob("*.lnc") if f.name != OURS_LNC)
        return bool(n), f"{n} real-name file(s) in the game's database folders" if n else "Not found in the game's database folders"
    if key in ("logos", "kits"):
        word = "logo" if key == "logos" else "kit"
        tops = [t.name for t in g.iterdir() if t.is_dir() and word in t.name.lower()] if g.is_dir() else []
        return bool(tops), f"Found: {', '.join(tops[:3])}" if tops else "Not found in FM's graphics folder"
    return False, "FMCC can't see separate apps; Connections opens them once installed"


@router.get("")
async def extras():
    c = await active_career()
    p = _paths(c)
    await editor_api.ng_index(c)
    if not LIVE:
        await asyncio.to_thread(_sample_downloads, p)
    last = {d["_id"]: d for d in await db.extras_installs.aggregate([{"$sort": {"at": -1}}, {"$group": {"_id": "$key", "at": {"$first": "$at"}, "file": {"$first": "$file"}}}]).to_list(20)}
    out = []
    for it in ITEMS:
        ok, detail = await asyncio.to_thread(_found, it["key"], p)
        f = await asyncio.to_thread(_newest, p["downloads"], it["pattern"])
        page = it["page"] or RNF_PAGE.get(c["edition"], RNF_PAGE["FM26"])
        out.append({k: v for k, v in it.items() if k != "pattern"} | {"page": page, "found": ok, "detail": detail,
                    "download": {"file": f.name, "mb": round(f.stat().st_size / 1e6, 1), "sample": f.name.startswith("SAMPLE")} if f else None,
                    "installed_at": (last.get(it["key"]) or {}).get("at")})
    return {"desktop": LIVE, "edition": c["edition"], "items": out, "built_in": [{"name": n, "role": r} for n, r in BUILT_IN],
            "needed_missing": [i["name"] for i in out if i["needed"] and not i["found"]]}


def _extract(zpath: Path, tmp: Path) -> Path:
    with zipfile.ZipFile(zpath) as z:
        for m in z.infolist():
            target = (tmp / m.filename).resolve()
            if not str(target).startswith(str(tmp.resolve())):
                raise HTTPException(422, "This zip has unsafe paths, so FMCC won't unpack it")
        z.extractall(tmp)
    return tmp


def _install_rnf(zpath: Path, p: dict, stamp: str) -> dict:
    dbs = _db_dirs(p["game"])
    if not dbs:
        raise HTTPException(409, "FMCC couldn't find the game's database folders. Check FM is installed and found in Setup.")
    with tempfile.TemporaryDirectory() as t:
        tmp = _extract(zpath, Path(t))
        src = next((d for d in sorted(tmp.rglob("*"), key=lambda x: len(x.parts)) if d.is_dir() and all((d / s).is_dir() for s in ("dbc", "edt", "lnc"))), None)
        if not src:
            raise HTTPException(422, "This zip doesn't look like the Real Name Fix (no dbc, edt and lnc folders)")
        backup = p["backups"] / f"real_name_fix-{stamp}"
        for d in dbs:
            ours = d / "lnc" / "all" / OURS_LNC
            keep = ours.read_bytes() if ours.exists() else None
            for s in ("dbc", "edt", "lnc"):
                staged = d / f"{s}.fmcc-new"
                if staged.exists():
                    (backup / d.name).mkdir(parents=True, exist_ok=True)
                    shutil.move(str(staged), str(backup / d.name / f"{s}.stale"))
                shutil.copytree(src / s, staged)
            for s in ("dbc", "edt", "lnc"):
                if (d / s).exists():
                    (backup / d.name).mkdir(parents=True, exist_ok=True)
                    shutil.move(str(d / s), str(backup / d.name / s))
                (d / f"{s}.fmcc-new").rename(d / s)
            if keep is not None:
                ours.parent.mkdir(parents=True, exist_ok=True)
                ours.write_bytes(keep)
        fmf = list(tmp.rglob("*.fmf"))
        p["editor_data"].mkdir(parents=True, exist_ok=True)
        for f in fmf:
            if (p["editor_data"] / f.name).exists():
                (backup / "editor data").mkdir(parents=True, exist_ok=True)
                shutil.copy2(p["editor_data"] / f.name, backup / "editor data" / f.name)
            shutil.copy2(f, p["editor_data"] / f.name)
    return {"message": f"Real Name Fix installed into {len(dbs)} database folder(s) and {len(fmf)} .fmf file(s) copied. The old folders are backed up.", "backup": backup.name}


def _install_graphics(zpath: Path, p: dict, word: str, stamp: str) -> dict:
    g = p["graphics"]
    backup = p["backups"] / f"{word}s-{stamp}"
    replaced = 0
    with tempfile.TemporaryDirectory() as t:
        tmp = _extract(zpath, Path(t))
        tops = [x for x in tmp.iterdir()]
        src, name = (tops[0], tops[0].name) if len(tops) == 1 and tops[0].is_dir() else (tmp, zpath.stem)
        if word not in name.lower():
            name = f"{name} {word}s"
        dest = g / name
        n = 0
        for f in src.rglob("*"):
            if f.is_file():
                rel = f.relative_to(src)
                if (dest / rel).exists():
                    (backup / name / rel).parent.mkdir(parents=True, exist_ok=True)
                    shutil.copy2(dest / rel, backup / name / rel)
                    replaced += 1
                (dest / rel).parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(f, dest / rel)
                n += 1
    return {"message": f"{n} file(s) unpacked into FM's graphics folder as \"{name}\"{f' ({replaced} replaced file(s) backed up)' if replaced else ''}. Restart FM (or reload skin) to see them.",
            "backup": backup.name if replaced else None}


@router.post("/ng_regens/fetch")
async def ng_fetch():
    """Download the NG_Regens Manager installer from the official site into Downloads (Windows file preferred), then start it."""
    if not LIVE:
        raise HTTPException(409, "FMCC fetches NG_Regens itself only in the Windows program")
    c = await active_career()
    p = _paths(c)
    async with httpx.AsyncClient(timeout=httpx.Timeout(30, read=180), follow_redirects=True) as client:
        page = await client.get("https://ngregens.org/")
        links = re.findall(r'href="([^"]+\.(?:exe|msi|zip))"', page.text) if page.status_code == 200 else []
        links = sorted(set(links), key=lambda u: (not re.search(r"(?i)win|setup|\.exe$", u), u))
        if not links:
            raise HTTPException(502, "Couldn't find the NG_Regens Manager download on ngregens.org. Use the official page instead.")
        url = links[0] if links[0].startswith("http") else httpx.URL("https://ngregens.org/").join(links[0]).__str__()
        dest = p["downloads"] / ("NG_Regens_Manager_" + url.rsplit("/", 1)[-1])
        async with client.stream("GET", url) as r:
            r.raise_for_status()
            with dest.open("wb") as f:
                async for chunk in r.aiter_bytes(1 << 20):
                    f.write(chunk)
    return await install("ng_regens")


@router.post("/{key}/install")
async def install(key: str):
    it = next((i for i in ITEMS if i["key"] == key), None)
    if not it or it["kind"] == "app":
        raise HTTPException(404, "FMCC can't install this one; use its own installer")
    c = await active_career()
    p = _paths(c)
    f = await asyncio.to_thread(_newest, p["downloads"], it["pattern"])
    if not f:
        raise HTTPException(409, f"No {it['name']} download found in your Downloads folder yet. Use \"Get it\" first.")
    sample = f.name.startswith("SAMPLE")
    stamp = datetime.now(timezone.utc).strftime("%Y%m%d-%H%M%S") + "-" + new_id()[:6]
    try:
        res = await _run(it, key, f, p, sample, stamp)
    except zipfile.BadZipFile:
        raise HTTPException(422, f"{f.name} isn't a complete zip. Download it again.")
    except PermissionError:
        raise HTTPException(409, "Windows wouldn't let FMCC change those files. Close FM and try again.")
    except OSError as exc:
        logger.warning("Extra install failed: %s", type(exc).__name__)
        raise HTTPException(409, f"The install stopped: {exc.strerror or type(exc).__name__}. Nothing already in place was removed without a backup.")
    seen = None if sample else (_CHECK["data"].get(c["edition"]) or {}).get(key, {}).get("latest")
    await db.extras_installs.insert_one({"id": new_id(), "key": key, "career_id": c["id"], "edition": c["edition"], "at": now_iso(), "file": f.name, "sample": sample,
                                         "backup": res["backup"], "version_seen": seen})
    await audit(c["id"], "extra installed", "extras", f"{it['name']} from {f.name}{' (sample)' if sample else ''}")
    return res | {"sample": sample, "file": f.name}


async def _run(it: dict, key: str, f: Path, p: dict, sample: bool, stamp: str) -> dict:
    if it["kind"] == "installer":
        if LIVE and not sample:
            os.startfile(str(f))  # noqa: S606 (Windows only)
            return {"message": "The NG_Regens Manager installer has started. Follow its steps; FMCC reads the faces once they're in FM's graphics folder.", "backup": None}
        return {"message": "Browser preview: this is a SAMPLE file, so nothing was started. In the Windows program this opens the NG_Regens Manager installer.", "backup": None}
    if key == "real_name_fix":
        return await asyncio.to_thread(_install_rnf, f, p, stamp)
    return await asyncio.to_thread(_install_graphics, f, p, key[:-1], stamp)


async def _ng_latest(client: httpx.AsyncClient) -> dict:
    r = await client.get("https://ngregens.org/")
    m = re.search(r"NG_Regens Manager\s+([0-9]+v[0-9.]+)", r.text) if r.status_code == 200 else None
    return {"latest": m.group(1), "how": "auto"} if m else {"latest": None, "how": "manual", "message": "Couldn't read the latest version from ngregens.org"}


async def _page_check(client: httpx.AsyncClient, url: str) -> dict:
    try:
        r = await client.get(url)
    except httpx.HTTPError:
        return {"latest": None, "how": "manual", "message": "Couldn't reach the site"}
    if r.status_code in (401, 403, 429):
        return {"latest": None, "how": "manual", "message": "This site doesn't allow automatic checks. Open its page to see if there's a newer version."}
    return {"latest": None, "how": "manual", "message": "Open its page to see if there's a newer version"}


@router.get("/updates")
async def updates():
    c = await active_career()
    ed = c["edition"]
    if ed not in _CHECK["data"] or time.time() - _CHECK["at"][ed] > 6 * 3600:
        data = {}
        async with httpx.AsyncClient(timeout=8, follow_redirects=True, headers={"User-Agent": "FMCC update check"}) as client:
            try:
                data["ng_regens"] = await _ng_latest(client)
            except httpx.HTTPError as exc:
                logger.warning("NG_Regens check failed: %s", type(exc).__name__)
                data["ng_regens"] = {"latest": None, "how": "manual", "message": "Couldn't reach ngregens.org"}
            data["real_name_fix"] = await _page_check(client, RNF_PAGE.get(c["edition"], RNF_PAGE["FM26"]))
        _CHECK["data"][ed] = data
        _CHECK["at"][ed] = time.time()
    out = {}
    for key, v in _CHECK["data"][ed].items():
        last = await db.extras_installs.find_one({"key": key, "sample": {"$ne": True}}, {"_id": 0}, sort=[("at", -1)])
        seen = (last or {}).get("version_seen")
        out[key] = v | {"installed_at": (last or {}).get("at"), "update": bool(v["latest"] and last and seen and seen != v["latest"]),
                        "unknown_installed": bool(v["latest"] and (not last or not seen))}
    return {"checked_at": datetime.fromtimestamp(_CHECK["at"][ed], timezone.utc).isoformat(), "items": out}
