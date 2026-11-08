"""First-run setup helpers: what FMCC found, a DOF key check, the health checklist and resume-where-you-left-off."""
import asyncio
import os
import tempfile
from datetime import datetime
from pathlib import Path
from typing import Literal, Optional

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field

import sample_reader
from core import db, active_career, latest_two, new_id, logger

router = APIRouter(prefix="/api/setup")
LIVE = os.environ.get("FMCC_READER") == "fmsave"
ROOT = Path(__file__).parent


def _item(key: str, label: str, ok: Optional[bool], detail: str, fix: Optional[str] = None) -> dict:
    return {"key": key, "label": label, "status": "ok" if ok is True else "warn" if ok is None else "fail", "detail": detail, "fix": fix}


class InspectIn(BaseModel):
    edition: Literal["FM26", "FM27"] = "FM27"
    save_folder: Optional[str] = Field(default=None, max_length=300)


def _inspect(edition: str, folder: Optional[str]) -> dict:
    det = sample_reader.detect_install(edition)
    if not LIVE:
        sf = folder or det["save_folder"]
        first = sample_reader.read_save(0, "Sample Club FC", {})
        return {"save_folder": sf, "sample": True, "items": [
            _item("game", "Game folder", True, f"Sample {edition} install (browser preview)"),
            _item("saves", "Save folder", True, sf),
            _item("count", "Saves in it", True, f"Sample saves · newest: {first['file_name']}, game date {first['game_date']}")]}
    from fm_game import game_root
    root = game_root(edition)
    sf = Path(folder or det["save_folder"])
    saves = sorted(sf.glob("*.fm"), key=lambda p: p.stat().st_mtime, reverse=True) if sf.is_dir() else []
    newest = f"{len(saves)} save{'s' if len(saves) != 1 else ''} · newest: {saves[0].name}, saved {datetime.fromtimestamp(saves[0].stat().st_mtime):%d %b %Y %H:%M}" if saves else "No .fm saves in this folder yet"
    return {"save_folder": str(sf), "sample": False, "items": [
        _item("game", "Game folder", bool(root), str(root) if root else f"{edition} wasn't found in your Steam libraries",
              None if root else "Install it through Steam, or check Steam is on this PC. FMCC only looks in Steam folders."),
        _item("saves", "Save folder", sf.is_dir(), str(sf) if sf.is_dir() else f"{sf} doesn't exist",
              None if sf.is_dir() else "Press Choose folder and type the path to your FM 'games' folder."),
        _item("count", "Saves in it", bool(saves), newest, None if saves else "Start a career in FM, save once, then press Find again.")]}


@router.post("/inspect")
async def inspect(body: InspectIn):
    return await asyncio.to_thread(_inspect, body.edition, (body.save_folder or "").strip() or None)


class KeyCheckIn(BaseModel):
    key: Optional[str] = Field(default=None, max_length=300)


@router.post("/check-key")
async def check_key(body: KeyCheckIn):
    """Makes one tiny request with the key. In the Windows program a working key is then saved on this PC."""
    from emergentintegrations.llm.chat import LlmChat, UserMessage
    import dof_api
    key = (body.key or "").strip() if LIVE else dof_api.api_key()
    if LIVE and len(key) < 20:
        raise HTTPException(422, "Paste your whole OpenAI key (it starts with sk-)")
    try:
        chat = LlmChat(api_key=key, session_id=f"keycheck-{new_id()}", system_message="Reply with the single word OK.").with_model(*dof_api.MODEL)
        await asyncio.wait_for(chat.send_message(UserMessage(text="Are you there?")), 45)
    except Exception as exc:
        logger.warning("DOF key check failed: %s", type(exc).__name__)
        return {"ok": False, "error": "That key didn't work. Check it's copied in full and that your OpenAI account has credit."}
    if LIVE:
        await dof_api.set_key(dof_api.KeyIn(key=key))
    return {"ok": True, "detail": "Key works and is saved on this PC" if LIVE else "The preview key works"}


def _writable(folder: Path) -> bool:
    try:
        folder.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(dir=folder, prefix="fmcc-check-"):
            pass
        return True
    except OSError:
        return False


@router.get("/health")
async def health():
    c = await active_career()
    snaps = await latest_two(c["id"])
    s = snaps[0] if snaps else None
    items = [_item("save", "Save readable", bool(s), f"Read {s['file_name']}: {len(s['players'])} players, game date {s['game_date']}" if s else "No save read yet",
                   None if s else "Save your game in FM, then press the refresh button in the top bar.")]
    if LIVE:
        from fm_game import DATA, game_root, fm_running
        folder = DATA / "backups"
    else:
        folder = ROOT / "preview_fm" / "backups"
    ok = await asyncio.to_thread(_writable, folder)
    items.append(_item("backup", "Backup folder writable", ok, "FMCC can write its backups" if ok else "FMCC can't write to its backup folder",
                       None if ok else "Free some disk space, or run FMCC once as administrator."))
    if LIVE:
        root = await asyncio.to_thread(game_root, c["edition"])
        items.append(_item("version", "FM version detected", True if root else False, f"{c['edition']} found at {root}" if root else f"{c['edition']} not found in Steam",
                           None if root else "Check FM is installed through Steam."))
        running = await asyncio.to_thread(fm_running, root)
        items.append(_item("running", "FM running or closed", None if running else True, "FM is running" if running else "FM is closed",
                           "Close FM before installing add-ons or applying live changes." if running else None))
    else:
        items.append(_item("version", "FM version detected", None, f"Sample {c['edition']} (browser preview)", "The Windows program checks your real install."))
        items.append(_item("running", "FM running or closed", None, "Can't check in the browser preview", "The Windows program checks this on your PC."))
    return {"items": items}


_DL = {"at": 0.0, "data": None}


@router.get("/download")
async def download_info():
    """Latest FMCC-Setup.exe from the GitHub release set in FMCC_RELEASE_REPO (owner/repo). Hidden inside the Windows program."""
    import time
    import httpx
    repo = (os.environ.get("FMCC_RELEASE_REPO") or "").strip().removeprefix("https://").removeprefix("github.com/").strip("/")
    if LIVE:
        return {"show": False}
    if not repo:
        return {"show": True, "url": None, "version": None, "message": "The download link isn't set up yet"}
    if _DL["data"] and time.time() - _DL["at"] < 600:
        return _DL["data"]
    data = {"show": True, "url": f"https://github.com/{repo}/releases/latest/download/FMCC-Setup.exe", "version": None, "message": None}
    try:
        async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
            r = await client.get(f"https://api.github.com/repos/{repo}/releases/latest", headers={"Accept": "application/vnd.github+json"})
        if r.status_code == 200:
            rel = r.json()
            asset = next((a for a in rel.get("assets", []) if a["name"].lower().endswith(".exe")), None)
            data |= {"version": rel.get("tag_name"), "url": asset["browser_download_url"] if asset else data["url"],
                     "size_mb": round(asset["size"] / 1e6, 1) if asset else None, "published": (rel.get("published_at") or "")[:10]}
        elif r.status_code == 404:
            data |= {"url": None, "message": "No release has been published yet"}
    except httpx.HTTPError as exc:
        logger.warning("Release check failed: %s", type(exc).__name__)
    _DL.update(at=time.time(), data=data)
    return data


class ProgressIn(BaseModel):
    step: int = Field(ge=0, le=3)
    form: dict = Field(default_factory=dict)


@router.get("/progress")
async def get_progress():
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "setup_progress": 1}) or {}
    return s.get("setup_progress") or {"step": 0, "form": {}}


@router.put("/progress")
async def put_progress(body: ProgressIn):
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "setup_complete": 1}) or {}
    if s.get("setup_complete"):
        return {"ok": True, "ignored": True}
    allowed = {k: v for k, v in body.form.items() if k in ("edition", "save_folder", "club_name", "name", "analytics", "found") and isinstance(v, (str, bool))}
    await db.settings.update_one({"_id": "app"}, {"$set": {"setup_progress": {"step": body.step, "form": allowed}}}, upsert=True)
    return {"ok": True}
