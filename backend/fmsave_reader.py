"""Real save reader for the Windows program, built on fmsave (needs Python 3.12+). UNVERIFIED against real saves:
field access is defensive, and anything fmsave can't read stays None instead of being guessed."""
from datetime import date
from pathlib import Path

ATTR_MAP = {"handling": "handling", "reflexes": "reflexes", "one_on_ones": "one_on_ones", "kicking": "kicking", "command_of_area": "command_of_area",
            "aerial_reach": "aerial_reach", "passing": "passing", "first_touch": "first_touch", "technique": "technique", "dribbling": "dribbling",
            "crossing": "crossing", "finishing": "finishing", "heading": "heading", "tackling": "tackling", "marking": "marking", "vision": "vision",
            "flair": "flair", "off_the_ball": "off_the_ball", "work_rate": "work_rate", "strength": "strength", "jumping_reach": "jumping_reach",
            "stamina": "stamina", "positioning": "positioning", "decisions": "decisions", "composure": "composure", "anticipation": "anticipation",
            "pace": "pace", "acceleration": "acceleration"}
POS_FALLBACK = ["M (C)"]


def _get(obj, path, default=None):
    for part in path.split("."):
        obj = getattr(obj, part, None) if obj is not None else None
    return default if obj is None else obj


def latest_save(folder: str) -> Path | None:
    files = sorted(Path(folder).glob("*.fm"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def _positions(p) -> list:
    raw = _get(p, "positions") or []
    out = [str(getattr(x, "label", x)) for x in raw] if isinstance(raw, (list, tuple)) else [str(raw)]
    return [x for x in out if x] or POS_FALLBACK


def _player(p, club_name: str, club_lookup: dict) -> dict:
    birth = _get(p, "birth_date")
    contract_end = _get(p, "contract.end_date") or _get(p, "contract.expires")
    return {"unique_id": int(_get(p, "unique_id", _get(p, "uid", 0))), "name": _get(p, "name", "Unknown"),
            "birth_date": birth.isoformat() if hasattr(birth, "isoformat") else str(birth or ""), "age": int(_get(p, "age", 0)),
            "nationality": _get(p, "nationality.name") or str(_get(p, "nationality", "")), "positions": _positions(p),
            "ca": int(_get(p, "ability.current", 0)), "pa": int(_get(p, "ability.potential", 0)),
            "contract_end": contract_end.isoformat() if hasattr(contract_end, "isoformat") else str(contract_end or "2099-06-30"),
            "wage": _get(p, "contract.wage"), "value": int(_get(p, "transfer_value", 0) or 0),
            "club": club_lookup.get(_get(p, "club_uid"), club_name), "minutes": 0, "appearances": 0, "avg_rating": None,
            "goals": 0, "assists": 0, "training_rating": None, "homegrown": bool(_get(p, "home_grown", False)),
            "attributes": {k: int(_get(p, f"attributes.{v}", 0) or 0) for k, v in ATTR_MAP.items()}}


def read_save(path: Path, club_name_hint: str) -> dict:
    import fmsave  # only installed in the Windows build

    with fmsave.open(str(path)) as save:
        clubs = save.managed_clubs()
        if not clubs:
            raise ValueError("You aren't managing a club in this save")
        club = clubs[0]
        club_lookup = {c.club_uid: c.name for c in save.clubs()} if hasattr(save, "clubs") else {}
        club_rows = [{"uid": int(u), "name": n, "league": None} for u, n in club_lookup.items() if u is not None and n]
        club_name = club_lookup.get(club.club_uid) or _get(club, "name") or club_name_hint
        squad = [_player(p, club_name, club_lookup) for p in save.players().where(club_uid=club.club_uid)]
        stats = {}
        try:
            for s in save.player_season_stats():
                a = stats.setdefault(_get(s, "player_uid"), {"minutes": 0, "appearances": 0, "goals": 0, "assists": 0, "ratings": []})
                a["minutes"] += _get(s, "minutes", 0)
                a["appearances"] += _get(s, "appearances", 0)
                a["goals"] += _get(s, "goals", 0)
                a["assists"] += _get(s, "assists", 0)
                if _get(s, "average_rating"):
                    a["ratings"].append(_get(s, "average_rating"))
        except Exception:
            stats = {}
        game_date = _get(save, "game_date") or date.today()
    gd = game_date if isinstance(game_date, date) else date.fromisoformat(str(game_date)[:10])
    for p in squad:
        s = stats.get(p["unique_id"])
        if s:
            p.update(minutes=s["minutes"], appearances=s["appearances"], goals=s["goals"], assists=s["assists"],
                     avg_rating=round(sum(s["ratings"]) / len(s["ratings"]), 2) if s["ratings"] else None)
    season_year = gd.year if gd.month >= 7 else gd.year - 1
    return {"file_name": path.name, "club_name": club_name, "game_date": gd.isoformat(), "season": f"{season_year}/{str(season_year + 1)[2:]}",
            "players": squad, "next_fixture": None, "pool": [], "clubs": club_rows, "file_mtime": path.stat().st_mtime}
