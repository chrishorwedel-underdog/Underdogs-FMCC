"""Backup save reader: fm-open-scout's fm_save_parser (MIT), bundled in the Windows build. Results are UNVERIFIED, like other unconfirmed fields."""
import json
import logging
import os
import subprocess
import tempfile
from datetime import date
from pathlib import Path

logger = logging.getLogger("fmcc")
TIMEOUT = 300
POS = {"GK": "GK", "SW": "D (C)", "DL": "D (L)", "DC": "D (C)", "DR": "D (R)", "DM": "DM", "ML": "M (L)", "MC": "M (C)", "MR": "M (R)",
       "AML": "AM (L)", "AMC": "AM (C)", "AMR": "AM (R)", "ST": "ST", "WBL": "WB (L)", "WBR": "WB (R)"}


def parser() -> Path | None:
    p = os.environ.get("FMCC_BACKUP_PARSER")
    return Path(p) if p and Path(p).is_file() else None


def _run(path: Path) -> dict:
    exe = parser()
    if not exe:
        raise FileNotFoundError("it isn't installed")
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "players.json"
        r = subprocess.run([str(exe), "players", str(path), "--json", str(out)], capture_output=True, text=True, timeout=TIMEOUT,
                           creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0), check=False)
        if r.returncode != 0 or not out.exists():
            lines = (r.stderr or "").strip().splitlines()
            raise RuntimeError(lines[-1][:200] if lines else f"exit code {r.returncode}")
        return json.loads(out.read_text(encoding="utf-8"))


def _iso(v) -> str | None:
    try:
        return date.fromisoformat(str(v)[:10]).isoformat()
    except (TypeError, ValueError):
        return None


def _age(birth: str | None, today: str | None) -> int:
    if not birth or not today:
        return 0
    b, t = date.fromisoformat(birth), date.fromisoformat(today)
    return t.year - b.year - ((t.month, t.day) < (b.month, b.day))


def _positions(p: dict) -> list:
    rated = sorted(((v, k) for k, v in (p.get("positions") or {}).items() if isinstance(v, int) and v >= 15), reverse=True)
    out = list(dict.fromkeys(POS[k] for _, k in rated if k in POS))
    return out or ([POS[p["best_position"]]] if p.get("best_position") in POS else [])


def _natural(p: dict) -> list | None:
    """Positions FM rates Natural (20 on its 1-20 scale); None when the save gives no ratings."""
    rated = p.get("positions")
    if not isinstance(rated, dict) or not rated:
        return None
    return list(dict.fromkeys(POS[k] for k, v in rated.items() if isinstance(v, int) and v >= 20 and k in POS))


def normalize(raw: dict, attr_keys) -> dict:
    """fm_save_parser JSON -> FMCC's player rows, keyed by unique ID. CA/PA stay internal like everywhere else."""
    v = raw.get("version") or {}
    today = _iso(v.get("current_date"))
    clubs, players = {}, {}
    for p in raw.get("players") or []:
        if p.get("uid") is None:
            continue
        p["uid"] = int(p["uid"])
        c = p.get("club") or {}
        if c.get("uid") is not None and (c.get("name") or c.get("short_name")):
            clubs.setdefault(c["uid"], c.get("name") or c.get("short_name"))
        birth, contract = _iso(p.get("date_of_birth")), p.get("contract") or {}
        attrs = p.get("attributes") or {}
        players[p["uid"]] = {"unique_id": int(p["uid"]), "name": p.get("name") or p.get("full_name") or "Unknown", "birth_date": birth or "",
                             "age": _age(birth, today), "nationality": p.get("nation_name") or "", "positions": _positions(p), "natural": _natural(p),
                             "ca": int(p.get("current_ability") or 0), "pa": max(int(p.get("potential_ability") or 0), 0),
                             "contract_end": _iso(contract.get("ends")) or "2099-06-30", "wage": contract.get("weekly_wage") or None,
                             "value": int(p.get("valuation_unverified") or 0), "club_uid": c.get("uid"), "club": c.get("name") or c.get("short_name"),
                             "minutes": 0, "appearances": 0, "avg_rating": None, "goals": 0, "assists": 0, "training_rating": None, "homegrown": False,
                             "attributes": {k: int(attrs.get(k) or 0) for k in attr_keys}}
    return {"fm_version": v.get("game_version") or (f"FM{v['major']}" if v.get("major") else None), "game_date": today,
            "clubs": clubs, "players": players, "warnings": raw.get("warnings") or []}


def read(path: Path, attr_keys) -> tuple[dict | None, str | None]:
    """(result, None) or (None, why it failed). Never raises: FMCC carries on with the main reader alone."""
    try:
        return normalize(_run(path), attr_keys), None
    except Exception as exc:  # noqa: BLE001 - a backup that fails must never stop a read
        logger.warning("backup save reader: %s", exc)
        return None, str(exc)[:200]
