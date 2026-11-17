"""Real save reader for the Windows program, built on fmsave (needs Python 3.12+). UNVERIFIED against real saves:
field access is defensive, and anything fmsave can't read stays None instead of being guessed."""
from datetime import date
from pathlib import Path
import logging
import re

logger = logging.getLogger("fmcc")

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


def latest_save(folder: str, pick: str | None = None) -> Path | None:
    """The save you chose in setup if it's still there, otherwise the newest .fm in the folder."""
    if pick and Path(pick).is_file():
        return Path(pick)
    files = sorted(Path(folder).glob("*.fm"), key=lambda p: p.stat().st_mtime, reverse=True)
    return files[0] if files else None


def candidate_folders(edition: str, extra: str | None = None) -> list[Path]:
    """Every place FM usually keeps saves on Windows, including OneDrive-moved Documents folders."""
    import os
    home = Path(os.environ.get("USERPROFILE") or Path.home())
    docs = [home / "Documents", *sorted(home.glob("OneDrive*/Documents")), *sorted(home.glob("OneDrive*/Dokumente")), *sorted(home.glob("OneDrive*/Documenten"))]
    years = ["27", "26"] if edition == "FM27" else ["26", "27"]
    names = [n for y in years for n in (f"Football Manager 20{y}", f"Football Manager {y}")]
    out = ([Path(extra)] if extra else []) + [d / "Sports Interactive" / n / "games" for d in docs for n in names]
    seen, uniq = set(), []
    for p in out:
        if str(p).lower() not in seen:
            seen.add(str(p).lower())
            uniq.append(p)
    return uniq


def find_saves(edition: str, extra: str | None = None, limit: int = 40) -> list[dict]:
    """Scan the usual save folders (and one level of sub-folders) for .fm saves, newest first."""
    found = {}
    for folder in candidate_folders(edition, extra):
        if not folder.is_dir():
            continue
        for f in [*folder.glob("*.fm"), *folder.glob("*/*.fm")]:
            try:
                st = f.stat()
            except OSError:
                continue
            found[str(f)] = {"path": str(f), "name": f.stem, "folder": str(f.parent), "modified": st.st_mtime, "size_mb": round(st.st_size / 1e6, 1)}
    return sorted(found.values(), key=lambda s: -s["modified"])[:limit]


def _safe(fn, default, label: str, skipped: list):
    """Optional parts of the save: if the reader can't handle one, FMCC carries on without it."""
    try:
        return fn()
    except Exception as exc:  # noqa: BLE001 - fmsave raises many layout-specific errors
        logger.warning("fmsave skipped %s: %s", label, exc)
        skipped.append(label)
        return default


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
TOT_ALIASES = {"tkw": ("tackles_completed", "tackles_won"), "int": ("interceptions", "interceptions_made"), "cs": ("clean_sheets",),
               "kp": ("key_passes", "open_play_key_passes"), "sv": ("saves_held", "saves_parried", "saves_tipped")}
WORLD_CAP = 4000  # busiest players from the loaded leagues, so the world snapshot stays a sensible size
STAFF_CAP = 8000


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
            tot = a.setdefault("tot", {})
            for k, names in TOT_ALIASES.items():
                vals = [v for v in (_get(s, n) for n in names) if v is not None] if k == "sv" else [_first(s, *names)]
                if vals and vals[0] is not None:
                    tot[k] = tot.get(k, 0) + sum(vals)
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
    p.update(minutes=s["minutes"], appearances=s["starts"] + s["substitute_appearances"], starts=s["starts"], sub_apps=s["substitute_appearances"], goals=s["goals"], assists=s["assists"],
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


def _tactics(save, my_uid) -> list:
    """Your club's saved tactics with each slot's position code (out of possession first, as that is the shape FM shows)."""
    out = []
    try:
        mine = [t for t in save.tactics() if _get(t, "club_uid") == my_uid]
    except Exception:
        return []
    for i, t in enumerate(sorted(mine, key=lambda t: (_get(t, "team_slot", 0) or 0, _get(t, "index", 0) or 0))):
        pos = []
        for s in _get(t, "slots") or []:
            p = _first(s, "position", "out_of_possession_positions", "in_possession_positions")
            p = p[0] if isinstance(p, (list, tuple)) and p else p
            if p is not None:
                pos.append(str(getattr(p, "name", p)))
        out.append({"name": _get(t, "name") or f"Tactic {i + 1}", "positions": pos[:11]})
    return out


def _staff(save, club_lookup: dict, club_league: dict, nations: dict) -> list:
    """Non-player staff at every club, for Seed a Surname. fmsave's staff() reader; job titles on FM27 only. UNVERIFIED."""
    if not hasattr(save, "staff"):
        return []
    out = []
    try:
        rows = list(save.staff())
    except Exception:
        return []
    for s in rows:
        if _get(s, "is_human_manager"):
            continue
        uid = _first(s, "unique_id", "uid")
        club = _get(s, "club_name") or club_lookup.get(_get(s, "club_uid"))
        job = _get(s, "job")
        label = getattr(getattr(job, "value", job), "name", None) or getattr(job, "name", None)
        out.append({"unique_id": int(uid) if uid is not None else None, "name": _get(s, "name") or _get(s, "full_name") or "Unknown", "age": _get(s, "age"),
                    "nationality": nations.get(_get(s, "nation_id")), "club": club, "league": club_league.get(club),
                    "job": label.replace("_", " ").title().replace(" Of ", " of ") if label and label != "UNKNOWN" else None,
                    "ca": _get(s, "ability.current"), "has_contract": bool(_get(s, "has_contract", True))})
    return [r for r in out if r["unique_id"] is not None][:STAFF_CAP]


def _hex(v) -> str | None:
    """'#RRGGBB' from a hex string, an (r, g, b) tuple or an object with r/g/b, else None."""
    if isinstance(v, str) and len(v.lstrip("#")) == 6:
        try:
            int(v.lstrip("#"), 16)
            return "#" + v.lstrip("#").upper()
        except ValueError:
            return None
    rgb = v if isinstance(v, (tuple, list)) else tuple(_get(v, k) for k in ("r", "g", "b")) if v is not None else None
    if rgb and len(rgb) >= 3 and all(isinstance(x, int) and 0 <= x <= 255 for x in rgb[:3]):
        return "#%02X%02X%02X" % tuple(rgb[:3])
    return None


def _colours(club) -> dict | None:
    """Your club's colours, if this fmsave version exposes them (its documented Club record doesn't yet). UNVERIFIED."""
    primary = _hex(_first(club, "background_colour", "primary_colour", "home_kit_colour", "colour", "colours.background"))
    secondary = _hex(_first(club, "foreground_colour", "secondary_colour", "colours.foreground"))
    return {"primary": primary, "secondary": secondary} if primary else None


def _finance(club) -> dict:
    """Club money figures, if this fmsave version exposes them. Anything missing stays None. UNVERIFIED."""
    def num(*keys):
        v = _first(club, *keys)
        return int(v) if isinstance(v, (int, float)) else None
    ffp = _first(club, "ffp_status", "finances.ffp_status")
    return {"bank_balance": num("balance", "bank_balance", "finances.balance"), "transfer_budget": num("transfer_budget", "finances.transfer_budget"),
            "transfer_spent": num("transfer_spent", "finances.transfer_spent"), "transfer_received": num("transfer_received", "transfer_income", "finances.transfer_received", "finances.transfer_income"), "wage_bill": num("wage_bill", "finances.wage_bill"),
            "turnover": num("turnover", "revenue", "finances.turnover"), "ffp_status": ffp if ffp in ("comfortable", "compliant", "at_risk", "breach") else None}


def _club_history(club) -> dict:
    """Honours, cup runs, awards and ground figures, if this fmsave version exposes them. Missing stays None/empty. UNVERIFIED."""
    def lst(*keys):
        v = _first(club, *keys)
        return [dict(x) if isinstance(x, dict) else {k: _get(x, k) for k in ("competition", "season", "kind", "stage", "manager", "opponent", "score", "venue", "scorers", "player_uid", "player", "award", "title", "date")} for x in v] if isinstance(v, (list, tuple)) else []
    def num(*keys):
        v = _first(club, *keys)
        return int(v) if isinstance(v, (int, float)) else None
    return {"honours": lst("honours", "trophies", "history.honours"), "cups": lst("cup_runs", "competitions", "history.cups"), "awards": lst("awards", "player_awards", "history.awards"),
            "milestones": lst("milestones", "history.milestones"), "attendance": num("average_attendance", "attendance", "stadium.average_attendance"),
            "capacity": num("stadium_capacity", "stadium.capacity"), "stadium": _first(club, "stadium_name", "stadium.name"), "facilities": _first(club, "training_facilities", "facilities"),
            "academy": _first(club, "youth_academy", "academy_level", "youth_facilities"), "manager": _first(club, "manager_name", "manager.name")}


NO_CLUB_LIST = ("FMCC couldn't read the list of clubs from this save, so it can't tell which club you manage. This usually means the save comes from an FM update "
                "the save reader doesn't fully support yet. Make sure FM and FMCC are both up to date, or pick a different save.")


class ClubNotFound(ValueError):
    """No clue in the save says which club is yours; carries the club list so you can pick."""
    def __init__(self, choices: list):
        super().__init__("FMCC couldn't work out which club you manage in this save")
        self.choices = choices


def club_from_file(stem: str) -> str:
    """'Chris Horwedel - Wrexham 27' -> 'Wrexham'."""
    part = stem.split(" - ")[-1]
    return re.sub(r"\b(backup|auto ?save|copy|\d+)\b", "", part, flags=re.I).strip(" -_()")


def _likely(name: str, hints: list) -> bool:
    n = (name or "").lower()
    word = lambda a, b: re.search(rf"\b{re.escape(a)}\b", b) is not None  # noqa: E731
    return bool(n) and any(h and len(h) >= 3 and (word(h, n) or word(n, h)) for h in hints)


def club_choices(names: dict, stem: str, hint: str = "") -> list:
    """Every club, likely matches (named in the save file or typed) first, then A-Z."""
    hints = [club_from_file(stem).lower(), (hint or "").strip().lower()]
    rows = [{"uid": int(u), "name": n, "likely": _likely(n, hints)} for u, n in names.items() if u is not None and n]
    return sorted(rows, key=lambda r: (not r["likely"], r["name"].lower()))


def _human_club(save):
    for s in save.staff() if hasattr(save, "staff") else []:
        if _get(s, "is_human_manager") and _get(s, "club_uid") is not None:
            return _get(s, "club_uid")
    return None


def _find_club(save, names: dict, stem: str, hint: str, club_uid, skipped: list):
    """Your club: the one you picked, the one you manage, your manager's employer, the save file's name, then the typed name."""
    if club_uid is not None and club_uid in names:
        return club_uid, None
    mine = _safe(save.managed_clubs, [], "your club", skipped) if save is not None and hasattr(save, "managed_clubs") else []
    if mine:
        return _first(mine[0], "club_uid", "uid"), mine[0]
    human = _safe(lambda: _human_club(save), None, "your manager", skipped) if save is not None else None
    if human is not None and (not names or human in names):
        return human, None
    for want in (club_from_file(stem), hint):
        want = (want or "").strip().lower()
        if not want:
            continue
        exact = [u for u, n in names.items() if n and n.lower() == want]
        close = exact or [u for u, n in names.items() if n and len(want) >= 3 and want in n.lower()]
        if len(close) == 1:
            return close[0], None
    if not names:
        raise ValueError(NO_CLUB_LIST)
    raise ClubNotFound(club_choices(names, stem, hint))


def _open(fmsave, path: Path):
    try:
        return fmsave.open(str(path), strict=False)
    except TypeError:
        return fmsave.open(str(path))


MAIN_ONLY = ["season stats", "league tables", "transfers", "tactics", "staff", "finances", "club history"]
LOW_CAP = 50000


def low_row(uid, name, age, nat, positions, club, minutes, ca, gender="M") -> dict | None:
    """Seed a Surname candidates: free agents, 18 and under, under 90 minutes this season, or low ability. Ability stays internal."""
    if not (not club or (age or 99) <= 18 or (minutes or 0) < 90 or (ca or 999) <= 90):
        return None
    return {"unique_id": int(uid), "name": name or "Unknown", "age": age, "nationality": nat or "", "positions": positions or [],
            "club": club or "Free agent", "minutes": minutes or 0, "ca": ca or 0, "gender": gender}


def _safe_low(p, club_lookup: dict, stats: dict, low: list):
    try:
        s = stats.get(_first(p, "uid", "unique_id")) or {}
        r = low_row(_first(p, "unique_id", "uid"), _get(p, "name"), _get(p, "age"), _get(p, "nationality.name"), _positions(p),
                    club_lookup.get(_get(p, "club_uid")), s.get("minutes"), _get(p, "ability.current"))
        if r:
            low.append(r)
    except Exception:  # noqa: BLE001 - one odd player is simply not a candidate
        pass


def failure_message(name: str, exc: Exception, backup: dict | None, backup_err: str | None) -> str:
    ver = (backup or {}).get("fm_version")
    why = "isn't installed" if backup_err == "it isn't installed" else f"also had trouble ({backup_err})" if backup_err else "found no players"
    return (f"FMCC couldn't read {name}{f' (saved with FM {ver})' if ver else ''}. The main save reader (fmsave) stopped: {str(exc)[:140]}. "
            f"The backup reader (fm-open-scout) {why}. Make sure FM and FMCC are both up to date, save again in FM, or pick a different save.")


def combine(main: dict | None, backup: dict | None, backup_err: str | None, path: Path, hint: str, club_uid) -> dict:
    """One result from both readers: the main reader wins every conflict, the backup only fills gaps."""
    if main is None:
        skipped = list(MAIN_ONLY)
        my_uid, _ = _find_club(None, backup["clubs"], path.stem, hint, club_uid, skipped)
        main = {"file_name": path.name, "club_name": backup["clubs"].get(my_uid) or hint, "club_uid": my_uid,
                "game_date": backup["game_date"] or date.fromtimestamp(path.stat().st_mtime).isoformat(), "players": [], "next_fixture": None,
                "tactics": [], "pool": [], "tables": [], "clubs": [], "staff": [], "club_colours": None, "finance": {}, "history": {},
                "file_mtime": path.stat().st_mtime, "skipped": skipped}
        gd = date.fromisoformat(main["game_date"])
        sy = gd.year if gd.month >= 7 else gd.year - 1
        main["season"] = f"{sy}/{str(sy + 1)[2:]}"
        status = "failed"
    else:
        status = "partial" if main["skipped"] else "ok"
    added = filled = 0
    if backup:
        bp = backup["players"]
        have = set()
        for row in main["players"]:
            have.add(row["unique_id"])
            b = bp.get(row["unique_id"])
            if not b:
                continue
            gaps = {k: b[k] for k, empty in (("positions", POS_FALLBACK), ("contract_end", "2099-06-30"), ("wage", None), ("nationality", ""), ("birth_date", ""))
                    if row.get(k) in (empty, None, "") and b.get(k) not in (empty, None, "", [])}
            filled += bool(gaps)
            row.update(gaps)
        for uid, b in bp.items():
            if uid not in have and b["club_uid"] == main["club_uid"]:
                main["players"].append({k: v for k, v in b.items() if k != "club_uid"} | {"club": main["club_name"]})
                added += 1
        known = {c["uid"] for c in main["clubs"]}
        main["clubs"] += [{"uid": int(u), "name": n, "league": None} for u, n in backup["clubs"].items() if u not in known]
        low = main.setdefault("low_profile", [])
        seen = {r["unique_id"] for r in low}
        for uid, b in bp.items():
            if len(low) >= LOW_CAP:
                break
            if uid not in seen and b["club_uid"] != main["club_uid"]:
                r = low_row(uid, b["name"], b["age"] or None, b["nationality"], b["positions"], b["club"], None, b["ca"])
                if r:
                    low.append(r)
    main["readers"] = {"fm_version": (backup or {}).get("fm_version"), "main": status, "backup": "ok" if backup else "missing" if backup_err == "it isn't installed" else "failed",
                       "backup_error": backup_err, "backup_added": added, "backup_filled": filled}
    return main


def reader_note(d: dict) -> str | None:
    """Plain words when a read had trouble; None when it simply worked."""
    r, skipped = d.get("readers") or {}, d.get("skipped") or []
    if r.get("main") == "ok" and not skipped:
        return None
    ver = f"Saved with FM {r['fm_version']}. " if r.get("fm_version") else ""
    if r.get("main") == "failed":
        text = ("The main save reader (fmsave) couldn't read this save, so FMCC used the backup reader (fm-open-scout) for your club and squad. "
                "Stats, league tables, finances and history stay empty until the main reader supports this FM update.")
    else:
        text = f"The main save reader (fmsave) skipped: {', '.join(skipped)}."
        if r.get("backup") == "ok" and (r.get("backup_added") or r.get("backup_filled")):
            text += f" The backup reader (fm-open-scout) filled the gaps for {r['backup_added'] + r['backup_filled']} of your players."
        elif r.get("backup") == "failed":
            text += f" The backup reader (fm-open-scout) couldn't help either ({r.get('backup_error')})."
    return f"{ver}{text} If something looks missing, update FM and FMCC, or save again in FM."


def read_save(path: Path, club_name_hint: str, club_uid: int | None = None) -> dict:
    """Both readers on the same save, one after the other, combined."""
    import backup_reader
    backup, backup_err = backup_reader.read(path, ATTR_MAP.keys())
    try:
        main = _read_main(path, club_name_hint, club_uid, (backup or {}).get("clubs", {}))
    except ClubNotFound:
        raise
    except Exception as exc:  # noqa: BLE001 - the backup reader may still have the squad
        if not backup or not backup["players"] or not backup["clubs"]:
            raise ValueError(failure_message(path.name, exc, backup, backup_err)) from exc
        logger.warning("fmsave failed, using the backup reader: %s", exc)
        main = None
    return combine(main, backup, backup_err, path, club_name_hint, club_uid)


def _read_main(path: Path, club_name_hint: str, club_uid, extra_names: dict) -> dict:
    import fmsave  # only installed in the Windows build

    skipped = []
    with _open(fmsave, path) as save:
        objs = _safe(lambda: list(save.clubs()) if hasattr(save, "clubs") else [], [], "club list", skipped)
        clubs = {_first(c, "club_uid", "uid"): (_first(c, "name", "club_name"), _get(c, "nation_id"), _get(c, "gender"), _get(c, "reputation")) for c in objs}
        my_uid, club = _find_club(save, {**extra_names, **{u: v[0] for u, v in clubs.items()}}, path.stem, club_name_hint, club_uid, skipped)
        club = club or next((c for c in objs if _first(c, "club_uid", "uid") == my_uid), None)
        club_lookup = {u: v[0] for u, v in clubs.items()}
        club_rows = [{"uid": int(u), "name": n, "league": None} for u, n in club_lookup.items() if u is not None and n]
        club_name = club_lookup.get(my_uid) or _get(club, "name") or extra_names.get(my_uid) or club_name_hint
        club_colours = _safe(lambda: _colours(club), None, "club colours", skipped)
        stats = _safe(lambda: _season_stats(save), {}, "season stats", skipped)
        everyone = list(save.players())
        nations = {}
        for p in everyone:
            nid, nn = _get(p, "nation_id"), _get(p, "nationality.name")
            if nid is not None and nn and isinstance(nn, str):
                nations.setdefault(nid, nn)
        tables, club_league = _safe(lambda: _tables(save, {u: (v[0], v[1], v[3], v[2]) for u, v in clubs.items()}, nations), ([], {}), "league tables", skipped)
        moves = _safe(lambda: _transfers(save), {}, "transfers", skipped)
        tactics = _safe(lambda: _tactics(save, my_uid), [], "tactics", skipped)
        squad, pool, low = [], [], []
        for p in everyone:
            uid, cu = _first(p, "unique_id", "uid"), _get(p, "club_uid")
            if cu != my_uid and len(low) < LOW_CAP:
                _safe_low(p, club_lookup, stats, low)
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
            row.update(league=league, country=next((t["country"] for t in tables if t["league"] == league), "Other"), stats=_p90(s) or None, totals=s.get("tot") or None,
                       last_move=moves.get(_first(p, "uid", "unique_id")), gender="F" if str(clubs.get(cu, (0, 0, ""))[2]).lower().startswith(("f", "w")) else "M")
            pool.append(row)
        game_date = _get(save, "game_date") or date.today()
        staff = _safe(lambda: _staff(save, club_lookup, club_league, nations), [], "staff", skipped)
        finance = _safe(lambda: _finance(club), {}, "finances", skipped)
        history = _safe(lambda: _club_history(club), {}, "club history", skipped)
    pool = sorted(pool, key=lambda r: -r["minutes"])[:WORLD_CAP]
    gd = game_date if isinstance(game_date, date) else date.fromisoformat(str(game_date)[:10])
    season_year = gd.year if gd.month >= 7 else gd.year - 1
    return {"file_name": path.name, "club_name": club_name, "club_uid": my_uid, "game_date": gd.isoformat(), "season": f"{season_year}/{str(season_year + 1)[2:]}",
            "players": squad, "low_profile": low, "next_fixture": None, "tactics": tactics, "pool": pool, "tables": tables, "clubs": club_rows, "staff": staff, "club_colours": club_colours, "finance": finance, "history": history, "file_mtime": path.stat().st_mtime, "skipped": skipped}
