"""Connections: the FMMatchLens match add-on (BepInEx 6 + plugin + dashboard) and the live game editor status.
In the browser preview the install is MOCKED (recorded only); the Windows program downloads and copies real files."""
import asyncio
import hashlib
import os
import shutil
import zipfile
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

import updates
from core import db, active_career, audit, now_iso

router = APIRouter(prefix="/api/connections")
LIVE = os.environ.get("FMCC_READER") == "fmsave"
MATCHLENS = {"FM27": "v0.7.1", "FM26": "v0.6.1"}
ML_REPO = "https://github.com/osnsyc/FMMatchLens/releases/download"
PLUGIN_DLL = Path("BepInEx/plugins/FMMatchLens/FMMatchLens.Plugin.dll")
restart_hook = None  # set by the Windows launcher


async def ml_state() -> dict:
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "matchlens": 1}) or {}
    return s.get("matchlens") or {"installed": False}


async def save_state(state: dict):
    await db.settings.update_one({"_id": "app"}, {"$set": {"matchlens": state}}, upsert=True)


def _dash_dir() -> Path:
    from fm_game import DATA
    return DATA / "matchlens-dashboard"


def _download(client: httpx.Client, url: str, dest: Path) -> Path:
    with client.stream("GET", url, follow_redirects=True) as r:
        r.raise_for_status()
        with dest.open("wb") as f:
            for chunk in r.iter_bytes():
                f.write(chunk)
    return dest


def _sha(p: Path) -> str:
    return hashlib.sha256(p.read_bytes()).hexdigest()


def _extract_new(zpath: Path, root: Path) -> list[str]:
    """Extract only files that don't exist yet, so nothing of yours is overwritten. Returns what was added."""
    added, base = [], root.resolve()
    try:
        with zipfile.ZipFile(zpath) as z:
            for m in z.infolist():
                if m.is_dir():
                    continue
                target = (root / m.filename).resolve()
                if not target.is_relative_to(base):
                    raise ValueError(f"Unsafe path in {zpath.name}: {m.filename}")
                if target.exists():
                    continue
                target.parent.mkdir(parents=True, exist_ok=True)
                with z.open(m) as src, target.open("wb") as out:
                    shutil.copyfileobj(src, out)
                added.append(str(target.relative_to(base)))
    except Exception:
        _remove_files(root, added)
        raise
    return added


def _remove_files(root: Path, files: list[str]) -> int:
    removed = 0
    for rel in sorted(files, key=lambda x: -x.count(os.sep)):
        p = root / rel
        if p.is_file():
            p.unlink()
            removed += 1
        parent = p.parent
        while parent != root and parent.is_dir() and not any(parent.iterdir()):
            parent.rmdir()
            parent = parent.parent
    return removed


def _install(root: Path, edition: str, have_bepinex: bool) -> dict:
    from fm_game import DATA
    tmp = DATA / "downloads"
    tmp.mkdir(parents=True, exist_ok=True)
    ml_ver = MATCHLENS[edition]
    added, bep_ver = [], None
    with httpx.Client(timeout=60) as client:
        try:
            if not have_bepinex:
                url, bep_ver = updates.bepinex_latest_sync(client)
                added += _extract_new(_download(client, url, tmp / "bepinex.zip"), root)
            sums = client.get(f"{ML_REPO}/{ml_ver}/SHA256SUMS.txt", follow_redirects=True).text
            files = {}
            for kind in ("plugin", "dashboard"):
                name = f"FMMatchLens-{kind}-{ml_ver}.zip"
                z = _download(client, f"{ML_REPO}/{ml_ver}/{name}", tmp / name)
                if f"{_sha(z)}" not in sums:
                    raise ValueError(f"{name} didn't match its published checksum")
                files[kind] = z
            added += _extract_new(files["plugin"], root)
            dash = _dash_dir()
            shutil.rmtree(dash, ignore_errors=True)
            dash.mkdir(parents=True)
            with zipfile.ZipFile(files["dashboard"]) as zf:
                zf.extractall(dash)
        except Exception:
            _remove_files(root, added)
            raise
    return {"files": added, "bepinex": bep_ver, "fmmatchlens": ml_ver}


def _check_log(root: Path, since: str) -> dict:
    from datetime import datetime
    log = root / "BepInEx" / "LogOutput.log"
    if not log.exists() or datetime.fromtimestamp(log.stat().st_mtime).astimezone() < datetime.fromisoformat(since):
        return {"working": "waiting", "message": "Start FM once and wait for the main menu, then check again."}
    text = log.read_text(errors="ignore")
    lines = [ln for ln in text.splitlines() if "FMMatchLens" in ln]
    if any("loaded" in ln.lower() for ln in lines):
        return {"working": "ok", "message": "BepInEx's log shows FMMatchLens loaded."}
    bad = [ln for ln in lines if any(w in ln.lower() for w in ("error", "exception", "fail"))]
    return {"working": "fail", "message": bad[-1].strip()[:300] if bad else "BepInEx ran, but FMMatchLens didn't load. Check that this FM version is supported."}


def _paths(edition: str):
    import fm_game
    root = fm_game.game_root(edition)
    return root, fm_game.fm_running(root) if root else fm_game.fm_running(None), fm_game.is_admin()


@router.get("")
async def connections():
    c = await active_career()
    ml = await ml_state()
    if not LIVE:
        root = f"C:\\Program Files (x86)\\Steam\\steamapps\\common\\Football Manager {c['edition'][2:]}"
        return {"desktop": False, "edition": c["edition"], "game_root": root, "game_running": False, "is_admin": False,
                "bepinex": ml.get("installed", False), "plugin": ml.get("installed", False), "dashboard": ml.get("installed", False),
                "matchlens": ml, "target_version": MATCHLENS[c["edition"]], "editor_supported": c["edition"] == "FM27"}
    root, running, admin = await asyncio.to_thread(_paths, c["edition"])
    have = lambda rel: bool(root) and (root / rel).exists()  # noqa: E731
    return {"desktop": True, "edition": c["edition"], "game_root": str(root) if root else None, "game_running": running, "is_admin": admin,
            "bepinex": have("winhttp.dll") and have("BepInEx/core"), "plugin": have(PLUGIN_DLL), "dashboard": (_dash_dir() / "index.html").exists(),
            "matchlens": ml, "target_version": MATCHLENS[c["edition"]], "editor_supported": c["edition"] == "FM27",
            "probe_present": bool(os.environ.get("FMCC_PROBE")) and Path(os.environ["FMCC_PROBE"]).exists()}


@router.post("/matchlens/install")
async def install():
    c = await active_career()
    if (await ml_state()).get("installed"):
        raise HTTPException(409, "The match add-on is already installed")
    if not LIVE:
        state = {"installed": True, "at": now_iso(), "bepinex": "6.0.0-be (simulated)", "fmmatchlens": MATCHLENS[c["edition"]],
                 "files": ["winhttp.dll", "doorstop_config.ini", "BepInEx/core/…", str(PLUGIN_DLL)], "working": "waiting", "simulated": True,
                 "message": "Start FM once and wait for the main menu, then check again."}
        await save_state(state)
        await audit(c["id"], "installed", "matchlens", f"Match add-on install simulated: FMMatchLens {state['fmmatchlens']} (preview)")
        return state
    root, running, _ = await asyncio.to_thread(_paths, c["edition"])
    if not root:
        raise HTTPException(404, f"FMCC couldn't find {c['edition']} in your Steam library")
    if running:
        raise HTTPException(409, "Close Football Manager first. The add-on can only be installed while FM is closed.")
    have_bep = (root / "winhttp.dll").exists() and (root / "BepInEx" / "core").is_dir()
    try:
        res = await asyncio.to_thread(_install, root, c["edition"], have_bep)
    except PermissionError:
        raise HTTPException(403, "Windows blocked access to the game folder. Restart FMCC as administrator and try again.")
    except Exception as exc:
        raise HTTPException(502, f"The install didn't finish and was rolled back: {exc}")
    state = {"installed": True, "at": now_iso(), "game_root": str(root), "edition": c["edition"], "working": "waiting",
             "message": "Start FM once and wait for the main menu, then check again.", **res,
             "bepinex": res["bepinex"] or "already installed"}
    await save_state(state)
    await audit(c["id"], "installed", "matchlens", f"BepInEx {state['bepinex']}, FMMatchLens {res['fmmatchlens']} and the dashboard installed ({len(res['files'])} files added)")
    return state


@router.post("/matchlens/remove")
async def remove():
    c = await active_career()
    ml = await ml_state()
    if not ml.get("installed"):
        raise HTTPException(409, "The match add-on isn't installed by FMCC")
    removed = 0 if LIVE else len(ml.get("files", []))
    if LIVE:
        root = Path(ml["game_root"])
        if await asyncio.to_thread(lambda: _paths(c["edition"])[1]):
            raise HTTPException(409, "Close Football Manager first.")
        try:
            removed = await asyncio.to_thread(_remove_files, root, ml.get("files", []))
        except PermissionError:
            raise HTTPException(403, "Windows blocked access to the game folder. Restart FMCC as administrator and try again.")
        shutil.rmtree(_dash_dir(), ignore_errors=True)
    await save_state({"installed": False})
    await audit(c["id"], "removed", "matchlens", f"Match add-on removed: {removed} file(s) FMCC added were taken out" + ("" if LIVE else " (preview)"))
    return {"installed": False, "removed": removed}


@router.post("/matchlens/check")
async def check():
    ml = await ml_state()
    if not ml.get("installed"):
        raise HTTPException(409, "Install the match add-on first")
    res = {"working": "ok", "message": "Simulated in the browser preview."} if not LIVE else await asyncio.to_thread(_check_log, Path(ml["game_root"]), ml["at"])
    await save_state(ml | res | {"checked_at": now_iso()})
    return res


@router.post("/matchlens/dashboard")
async def open_dashboard():
    if not LIVE:
        raise HTTPException(409, "The FMMatchLens dashboard opens in the Windows program")
    index = _dash_dir() / "index.html"
    if not index.exists():
        raise HTTPException(404, "The dashboard isn't installed. Install the match add-on first.")
    os.startfile(str(index))  # type: ignore[attr-defined]
    return {"ok": True}


@router.post("/restart-admin")
async def restart_admin():
    if not LIVE or not restart_hook:
        raise HTTPException(409, "Only the Windows program can restart as administrator")
    asyncio.get_running_loop().call_later(0.5, restart_hook)
    return {"ok": True}
