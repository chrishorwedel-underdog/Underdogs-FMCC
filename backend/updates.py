import os
import re
from urllib.parse import unquote

import httpx

COMPONENTS = [  # key, name, role, GitHub repo (None = not published yet), bundled version
    ("fmcc", "FMCC", "The program itself", os.environ.get("FMCC_RELEASE_REPO") or None, "v0.1.0"),
    ("fmsave", "fmsave", "Built-in save reader", "rhiever/fmsave", "v0.10.0"),
    ("fmlibreeditor", "FMLibreEditor", "Built-in game editor", "tozmoz/FMLibreEditor", "v0.5.0"),
    ("fmmatchlens", "FMMatchLens", "Match analytics add-on", "osnsyc/FMMatchLens", "v0.7.1"),
    ("bepinex", "BepInEx 6", "Add-on loader for FM (IL2CPP bleeding edge)", "bepinex_be", "6.0.0-be.793"),
    ("scoutsheet", "ScoutSheet", "Scouting engine inside Scout Players (MIT licence)", os.environ.get("SCOUTSHEET_REPO") or None, "v1.0.0"),
    ("fmdossier", "FM Dossier", "Squad and recruitment app (launched from Connections)", "page:https://fmdossier.dev/download", "not tracked"),
    ("fmst26", "FMST26", "Scouting stats app (launched from Connections)", ("page:" + os.environ["FMST26_URL"]) if os.environ.get("FMST26_URL") else None, "not tracked"),
    ("fmos", "fmOS", "Career website (opens in your browser)", ("page:" + os.environ["FMOS_URL"]) if os.environ.get("FMOS_URL") else None, "not tracked"),
]


async def fetch_page_version(url: str):
    async with httpx.AsyncClient(timeout=8, follow_redirects=True) as client:
        r = await client.get(url)
        r.raise_for_status()
    m = re.search(r"\bv?(\d+\.\d+\.\d+)\b", re.sub(r"<[^>]+>", " ", r.text))
    return f"v{m.group(1)}" if m else None
BEPINEX_BUILDS = "https://builds.bepinex.dev"


def bepinex_link(html: str) -> tuple[str, str]:
    m = re.search(r'href="(/projects/bepinex_be/\d+/BepInEx-Unity\.IL2CPP-win-x64-([^"]+?)\.zip)"', html)
    if not m:
        raise ValueError("No BepInEx 6 IL2CPP x64 build found")
    return BEPINEX_BUILDS + m.group(1), unquote(m.group(2)).split("+")[0]


def bepinex_latest_sync(client: httpx.Client) -> tuple[str, str]:
    r = client.get(f"{BEPINEX_BUILDS}/projects/bepinex_be")
    r.raise_for_status()
    return bepinex_link(r.text)


def _ver(v: str) -> tuple:
    parts = []
    for x in v.lstrip("vV").split("."):
        digits = "".join(c for c in x if c.isdigit())
        parts.append(int(digits) if digits else 0)
    return tuple(parts)


def is_newer(latest: str, installed: str) -> bool:
    return _ver(latest) > _ver(installed)


async def fetch_latest(repo: str) -> dict:
    async with httpx.AsyncClient(timeout=8) as client:
        if repo == "bepinex_be":
            r = await client.get(f"{BEPINEX_BUILDS}/projects/bepinex_be")
            r.raise_for_status()
            return {"tag": bepinex_link(r.text)[1], "published_at": None, "url": f"{BEPINEX_BUILDS}/projects/bepinex_be"}
        r = await client.get(f"https://api.github.com/repos/{repo}/releases/latest",
                             headers={"Accept": "application/vnd.github+json"})
        r.raise_for_status()
        d = r.json()
        return {"tag": d.get("tag_name"), "published_at": d.get("published_at"), "url": d.get("html_url")}
