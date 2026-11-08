import os
import httpx

COMPONENTS = [  # key, name, role, GitHub repo (None = not published yet), bundled version
    ("fmcc", "FMCC", "The program itself", os.environ.get("FMCC_RELEASE_REPO") or None, "v0.1.0"),
    ("fmsave", "fmsave", "Built-in save reader", "rhiever/fmsave", "v0.10.0"),
    ("fmlibreeditor", "FMLibreEditor", "Built-in game editor", "tozmoz/FMLibreEditor", "v0.5.0"),
    ("fmmatchlens", "FMMatchLens", "Match analytics add-on", "osnsyc/FMMatchLens", "v0.7.1"),
    ("bepinex", "BepInEx", "Add-on loader for FM", "BepInEx/BepInEx", "v5.4.23.6"),
]


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
        r = await client.get(f"https://api.github.com/repos/{repo}/releases/latest",
                             headers={"Accept": "application/vnd.github+json"})
        r.raise_for_status()
        d = r.json()
        return {"tag": d.get("tag_name"), "published_at": d.get("published_at"), "url": d.get("html_url")}
