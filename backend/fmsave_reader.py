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


P90_MAP = {"npxg": "non_penalty_expected_goals", "xa": "expected_assists", "kp": "open_play_key_passes", "chc": "clear_cut_chances_created",
           "progp": "progressive_passes", "drb": "dribbles", "tkw": "tackles_completed", "pwon": "possession_won", "xgp": "expected_goals_prevented"}
SUM_KEYS = set(P90_MAP.values()) | {"minutes", "goals", "assists", "starts", "substitute_appearances", "blocks", "clearances", "pressures_attempted",
                                    "pressures_completed", "saves_held", "saves_parried", "saves_tipped", "shots_on_target_faced"}
WORLD_CAP = 4000  # busiest players from the loaded leagues, so the world snapshot stays a sensible size


def _first(obj, *names, default=None):
    for n in names:
        v = _get(obj, n)
        if v is not None:
            return v
    return default


def _season_stats(save) -> dict:
    stats = {}
    try:
        for s in save.player_season_stats():
            a = stats.setdefault(_get(s, "player_uid"), {"ratings": []} | {k: 0 for k in SUM_KEYS})
            for k in SUM_KEYS:
                a[k] += _get(s, k, 0) or 0
            r, n = _get(s, "average_rating"), _first(s, "rated_appearances", "appearances", default=0) or 0
            if r:
                a["ratings"].append((r, max(1, n)))
    except Exception:
        return {}
    return stats


def _p90(s: dict) -> dict:
    m = s.get("minutes") or 0
    if m < 90:
        return {}
    out = {k: round(s[f] / m * 90, 3) for k, f in P90_MAP.items() if s.get(f)}
    out["padbc"] = round((s["blocks"] + s["clearances"]) / m * 90, 3)
    if s["pressures_attempted"]:
        out["prr"] = round(s["pressures_completed"] / s["pressures_attempted"] * 100, 1)
    if s["shots_on_target_faced"]:
        out["savep"] = round((s["saves_held"] + s["saves_parried"] + s["saves_tipped"]) / s["shots_on_target_faced"] * 100, 1)
    return out


def _apply(p: dict, s: dict | None):
    if not s:
        return
    w = sum(n for _, n in s["ratings"])
    p.update(minutes=s["minutes"], appearances=s["starts"] + s["substitute_appearances"], goals=s["goals"], assists=s["assists"],
             avg_rating=round(sum(r * n for r, n in s["ratings"]) / w, 2) if w else None)


def _tables(save, clubs: dict, nations: dict) -> tuple[list, dict]:
    """League tables from the save, plus club name -> league. Competition names only exist if fmsave has a name map."""
    out, club_league = [], {}
    try:
        tables = list(save.league_tables())
    except Exception:
        return [], {}
    for t in tables:
        name = _get(t, "competition_name") or f"Competition {_get(t, 'competition_id', '?')}"
        rows, nat, reps, women = [], {}, [], 0
        for i, r in enumerate(_get(t, "rows") or []):
            uid = _first(r, "club_uid", "team_club_uid")
            club, nid, rep, gender = clubs.get(uid, (None, None, None, None))
            if rep is not None:
                reps.append(rep)
            women += str(gender or "").lower().startswith(("f", "w"))
            club = _first(r, "club_name", "team_name") or club or "Unknown club"
            row = {"club": club, "pos": int(_first(r, "position", "pos", default=i + 1)), "p": int(_first(r, "played", "played_matches", "matches_played", default=0)),
                   "w": int(_first(r, "won", "wins", default=0)), "d": int(_first(r, "drawn", "draws", default=0)), "l": int(_first(r, "lost", "losses", default=0)),
                   "gf": int(_first(r, "goals_for", "scored", default=0)), "ga": int(_first(r, "goals_against", "conceded", default=0)), "pts": int(_first(r, "points", default=0))}
            rows.append(row | {"gd": row["gf"] - row["ga"]})
            club_league.setdefault(club, name)
            if nid is not None:
                nat[nid] = nat.get(nid, 0) + 1
        nid = _get(t, "nation_id") or (max(nat, key=nat.get) if nat else None)
        if rows:
            out.append({"league": name, "country": nations.get(nid, "Other"), "rows": sorted(rows, key=lambda x: x["pos"]),
                        "reputation": round(sum(reps) / len(reps)) if reps else None, "women": women > len(rows) / 2})
    return out, club_league


def _transfers(save) -> dict:
    out = {}
    try:
        for t in save.transfers():
            when = _get(t, "transfer_date")
            row = {"from_club": _get(t, "from_club_name"), "fee": int(_get(t, "transfer_fee", 0) or 0) or None,
                   "date": when.isoformat() if hasattr(when, "isoformat") else str(when or "")}
            uid = _get(t, "player_uid")
            if uid is not None and row["date"] >= (out.get(uid) or {}).get("date", ""):
                out[uid] = row
    except Exception:
        return {}
    return out


def read_save(path: Path, club_name_hint: str) -> dict:
    import fmsave  # only installed in the Windows build

    with fmsave.open(str(path)) as save:
        mine = save.managed_clubs()
        if not mine:
            raise ValueError("You aren't managing a club in this save")
        club = mine[0]
        my_uid = _first(club, "club_uid", "uid")
        clubs = {_first(c, "club_uid", "uid"): (_first(c, "name", "club_name"), _get(c, "nation_id"), _get(c, "gender"), _get(c, "reputation")) for c in save.clubs()} if hasattr(save, "clubs") else {}
        club_lookup = {u: v[0] for u, v in clubs.items()}
        club_rows = [{"uid": int(u), "name": n, "league": None} for u, n in club_lookup.items() if u is not None and n]
        club_name = club_lookup.get(my_uid) or _get(club, "name") or club_name_hint
        stats = _season_stats(save)
        everyone = list(save.players())
        nations = {}
        for p in everyone:
            nid, nn = _get(p, "nation_id"), _get(p, "nationality.name")
            if nid is not None and nn and isinstance(nn, str):
                nations.setdefault(nid, nn)
        tables, club_league = _tables(save, {u: (v[0], v[1], v[3], v[2]) for u, v in clubs.items()}, nations)
        moves = _transfers(save)
        squad, pool = [], []
        for p in everyone:
            uid, cu = _first(p, "unique_id", "uid"), _get(p, "club_uid")
            if cu == my_uid:
                row = _player(p, club_name, club_lookup)
                _apply(row, stats.get(_first(p, "uid", "unique_id")) or stats.get(uid))
                squad.append(row)
                continue
            cname = club_lookup.get(cu)
            s = stats.get(_first(p, "uid", "unique_id")) or stats.get(uid)
            if cname not in club_league or not s or not s["minutes"]:
                continue
            row = _player(p, cname, club_lookup)
            _apply(row, s)
            league = club_league[cname]
            row.update(league=league, country=next((t["country"] for t in tables if t["league"] == league), "Other"), stats=_p90(s) or None,
                       last_move=moves.get(_first(p, "uid", "unique_id")), gender="F" if str(clubs.get(cu, (0, 0, ""))[2]).lower().startswith(("f", "w")) else "M")
            pool.append(row)
        game_date = _get(save, "game_date") or date.today()
    pool = sorted(pool, key=lambda r: -r["minutes"])[:WORLD_CAP]
    gd = game_date if isinstance(game_date, date) else date.fromisoformat(str(game_date)[:10])
    season_year = gd.year if gd.month >= 7 else gd.year - 1
    return {"file_name": path.name, "club_name": club_name, "game_date": gd.isoformat(), "season": f"{season_year}/{str(season_year + 1)[2:]}",
            "players": squad, "next_fixture": None, "pool": pool, "tables": tables, "clubs": club_rows, "file_mtime": path.stat().st_mtime}
