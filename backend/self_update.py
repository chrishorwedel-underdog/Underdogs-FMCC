import os
import re
import subprocess
from pathlib import Path

import httpx
from fastapi import APIRouter, HTTPException

import updates
from core import db, logger, io_lock, now_iso

router = APIRouter(prefix="/api/fmcc")
DATA = Path(os.environ.get("APPDATA", Path.home())) / "FMCC"
install_hook = None  # set by the Windows launcher: closes FMCC, then runs the installer


def notes_items(body: str, limit: int = 8) -> list:
    """Bullet lines from a release's notes, minus housekeeping lines."""
    out = []
    for line in (body or "").splitlines():
        m = re.match(r"^\s*[-*]\s+(.+)$", line)
        if m and not re.search(r"(?i)auto-commit|checkpoint|merge branch", m.group(1)):
            t = m.group(1).replace("**", "").split(" - ")[0].strip()
            out.append(t if len(t) <= 90 else t[:90].rsplit(" ", 1)[0] + "…")
    return list(dict.fromkeys(out))[:limit]


def _version() -> str:
    return os.environ.get("FMCC_VERSION") or "dev"


async def _release(path: str) -> dict:
    repo = updates.release_repo()
    if not repo:
        raise HTTPException(409, "FMCC's release page isn't set")
    async with httpx.AsyncClient(timeout=10) as client:
        r = await client.get(f"https://api.github.com/repos/{repo}/releases/{path}", headers={"Accept": "application/vnd.github+json"})
    if r.status_code == 404:
        raise HTTPException(404, "That release isn't on the release page")
    r.raise_for_status()
    return r.json()


@router.get("/latest")
async def latest():
    d = await _release("latest")
    return {"installed": _version(), "version": d.get("tag_name"), "url": d.get("html_url"), "items": notes_items(d.get("body")),
            "newer": _version() != "dev" and updates.is_newer(d.get("tag_name") or "", _version()), "can_install": install_hook is not None}


@router.get("/update-card")
async def update_card():
    """Corner card in the installed Windows program: shown once per start when a newer installer is out, unless snoozed for that version."""
    if install_hook is None or _version() == "dev":
        return {"show": False}
    try:
        d = await _release("latest")
    except Exception:  # noqa: BLE001 - offline or release page unreachable: stay quiet
        return {"show": False}
    tag = d.get("tag_name") or ""
    if not updates.is_newer(tag, _version()):
        return {"show": False}
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "update_snooze": 1}) or {}
    sn = s.get("update_snooze") or {}
    if sn.get("version") == tag and sn.get("until", "") > now_iso():
        return {"show": False}
    return {"show": True, "version": tag, "installed": _version(), "items": notes_items(d.get("body"), 3)}


@router.post("/update-card/snooze")
async def snooze_update_card(version: str):
    from datetime import datetime, timedelta, timezone
    until = (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat()
    await db.settings.update_one({"_id": "app"}, {"$set": {"update_snooze": {"version": version[:40], "until": until}}}, upsert=True)
    return {"ok": True, "until": until}


@router.post("/install")
async def install():
    if install_hook is None:
        raise HTTPException(409, "One-click update works in the FMCC Windows program. Download the installer from the Downloads page instead.")
    async with io_lock:
        d = await _release("latest")
        if not updates.is_newer(d.get("tag_name") or "", _version()):
            raise HTTPException(409, "You already have the newest FMCC")
        asset = next((a for a in d.get("assets", []) if a.get("name") == "FMCC-Setup.exe"), None)
        if not asset:
            raise HTTPException(404, "This release has no FMCC-Setup.exe")
        dest = DATA / "updates" / f"FMCC-Setup-{d['tag_name']}.exe"
        dest.parent.mkdir(parents=True, exist_ok=True)
        part = dest.with_suffix(".part")
        try:
            async with httpx.AsyncClient(timeout=httpx.Timeout(30, read=120), follow_redirects=True) as client:
                async with client.stream("GET", asset["browser_download_url"]) as r:
                    r.raise_for_status()
                    with part.open("wb") as f:
                        async for chunk in r.aiter_bytes(1 << 20):
                            f.write(chunk)
            if asset.get("size") and part.stat().st_size != asset["size"]:
                raise ValueError("download incomplete")
            part.replace(dest)
        except Exception as exc:
            logger.warning("FMCC update download failed: %s", exc)
            part.unlink(missing_ok=True)
            raise HTTPException(502, "Couldn't download the update. Check your internet connection and try again.")
        await db.settings.update_one({"_id": "app"}, {"$set": {"update_started": {"to": d["tag_name"], "at": now_iso()}}}, upsert=True)
    install_hook(str(dest))
    return {"ok": True, "version": d["tag_name"]}


def run_installer(path: str):
    """Silent install; the installer closes FMCC and opens it again when done."""
    subprocess.Popen([path, "/SILENT", "/CLOSEAPPLICATIONS", "/NORESTART"], close_fds=True,
                     creationflags=getattr(subprocess, "DETACHED_PROCESS", 0))


@router.get("/whats-new")
async def whats_new():
    ver = _version()
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "last_seen_version": 1}) or {}
    if ver == "dev":
        return {"show": False}
    if not s.get("last_seen_version"):
        await db.settings.update_one({"_id": "app"}, {"$set": {"last_seen_version": ver}}, upsert=True)
        return {"show": False}
    if s["last_seen_version"] == ver:
        return {"show": False}
    tag = "v" + ver.lstrip("vV")
    try:
        d = await _release(f"tags/{tag}")
        return {"show": True, "version": tag, "items": notes_items(d.get("body")), "url": d.get("html_url")}
    except Exception:
        return {"show": True, "version": tag, "items": [], "url": None}


@router.post("/whats-new/seen")
async def whats_new_seen():
    await db.settings.update_one({"_id": "app"}, {"$set": {"last_seen_version": _version()}}, upsert=True)
    return {"ok": True}
