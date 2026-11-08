"""Writes approved changes into the running FM27 through FMLibreEditor's command-line probe.
Windows program only; UNVERIFIED against a real game from this build environment."""
import hashlib
import os
import re
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

FIELDS = {"pa": "potential_ability", "ca": "current_ability"}
LIMITS = (1, 200)


class EditorError(Exception):
    pass


class AdminNeeded(EditorError):
    pass


def run(*args, timeout: int = 120) -> str:
    exe = os.environ.get("FMCC_PROBE")
    if not exe or not Path(exe).exists():
        raise EditorError("FMLibreEditor's command-line tool is missing from this install")
    r = subprocess.run([exe, *map(str, args)], capture_output=True, text=True, timeout=timeout,
                       creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0))
    out = (r.stdout or "") + "\n" + (r.stderr or "")
    if re.search(r"access is denied|os error 5\b|run .*as an? administrator", out, re.I):
        raise AdminNeeded("Windows blocked access to the game. Restart FMCC as administrator.")
    if r.returncode != 0:
        last = [ln for ln in out.splitlines() if ln.strip()]
        raise EditorError(last[-1].strip()[:300] if last else "FMLibreEditor stopped with an error")
    return r.stdout


def health() -> dict:
    out = run("health")
    profile = re.search(r"^Build profile: (.+)$", out, re.M)
    build = re.search(r"build: (.+)$", out, re.M)
    date = re.search(r"In-game date: (\d{4}-\d{2}-\d{2})", out)
    return {"known_build": bool(profile) and not profile.group(1).startswith("none"), "profile": profile.group(1) if profile else None,
            "build": build.group(1).strip() if build else None, "game_date": date.group(1) if date else None,
            "failed_checks": [ln.strip() for ln in out.splitlines() if ln.strip().startswith("FAIL")]}


def read(uid: int, field: str, entity: str = "player") -> tuple[int, str]:
    key = FIELDS.get(field, field) if entity == "player" else field
    out = run("get", entity, uid, key)
    head = re.match(rf"^(.*) \({entity} \d+\)", out.strip())
    m = re.search(rf"^\s*{key}\s+(-?\d+)\s*$", out, re.M)
    if not m:
        raise EditorError(f"{key} of player {uid} can't be read or isn't writable")
    return int(m.group(1)), head.group(1).strip() if head else ""


def write(uid: int, field: str, value: int, entity: str = "player") -> int:
    out = run("set", entity, uid, FIELDS.get(field, field) if entity == "player" else field, value)
    m = re.search(r"reads back (-?\d+)", out)
    if not m or int(m.group(1)) != value:
        raise EditorError(f"The new value didn't read back as {value}")
    return value


def read_all(entity: str, uid: int) -> dict:
    """Every editable whole-number field FMLibreEditor can read for this club (or player)."""
    out = run("get", entity, uid)
    return {m.group(1): int(m.group(2)) for m in re.finditer(r"^\s{2}(\S+)\s+(-?\d+)\s*$", out, re.M)}


def clamp(v: int) -> int:
    return max(LIMITS[0], min(LIMITS[1], v))


def backup_save(folder: str) -> dict:
    import fmsave_reader
    from fm_game import DATA
    src = fmsave_reader.latest_save(folder)
    if not src:
        raise EditorError("There's no save file to back up in your save folder")
    dest_dir = DATA / "save-backups"
    dest_dir.mkdir(parents=True, exist_ok=True)
    dest = dest_dir / f"{src.stem}.{datetime.now().strftime('%Y%m%d-%H%M%S')}{src.suffix}"
    shutil.copy2(src, dest)
    a, b = (hashlib.sha256(p.read_bytes()).hexdigest() for p in (src, dest))
    if a != b:
        dest.unlink(missing_ok=True)
        raise EditorError("The save backup didn't verify, so nothing was applied")
    return {"file": str(dest), "source": src.name, "sha256": a}
