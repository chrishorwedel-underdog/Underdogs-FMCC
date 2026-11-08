"""Finds the Steam FM install and whether FM is running. Windows program only (UNVERIFIED on a real PC here)."""
import ctypes
import os
import re
from pathlib import Path

DATA = Path(os.environ.get("APPDATA", Path.home())) / "FMCC"
FOLDERS = {"FM27": ["Football Manager 27", "Football Manager 2027"], "FM26": ["Football Manager 26", "Football Manager 2026"]}


def steam_libraries() -> list[Path]:
    roots = []
    try:
        import winreg
        with winreg.OpenKey(winreg.HKEY_CURRENT_USER, r"Software\Valve\Steam") as k:
            roots.append(Path(winreg.QueryValueEx(k, "SteamPath")[0]))
    except Exception:
        pass
    roots.append(Path(os.environ.get("ProgramFiles(x86)", r"C:\Program Files (x86)")) / "Steam")
    libs = []
    for r in roots:
        vdf = r / "steamapps" / "libraryfolders.vdf"
        if vdf.exists():
            libs += [Path(p.replace("\\\\", "\\")) for p in re.findall(r'"path"\s+"([^"]+)"', vdf.read_text(errors="ignore"))]
        libs.append(r)
    return list(dict.fromkeys(libs))


def game_root(edition: str) -> Path | None:
    for lib in steam_libraries():
        for name in FOLDERS[edition]:
            p = lib / "steamapps" / "common" / name
            if p.is_dir():
                return p
    return None


def fm_running(root: Path | None) -> bool:
    import psutil
    for proc in psutil.process_iter(["exe", "name"]):
        exe = proc.info.get("exe")
        if not exe:
            continue
        if root and Path(exe).parent.resolve().is_relative_to(root.resolve()) and not exe.lower().endswith(("unitycrashhandler64.exe",)):
            return True
        if not root and (proc.info.get("name") or "").lower() == "fm.exe":
            return True
    return False


def is_admin() -> bool:
    try:
        return bool(ctypes.windll.shell32.IsUserAnAdmin())
    except Exception:
        return False
