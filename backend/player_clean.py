"""Make a save's player rows safe for every page: any FM position style, missing details left blank (never guessed)."""
import re

SIDES = {"L": "L", "R": "R", "C": "C"}
FALLBACK_POS = "M (C)"


def norm_positions(raw) -> list:
    """'D/WB (R)', 'AM (RLC)', 'M/AM (C)', 'ST (C)', 'GK' or a list of them -> FMCC's positions, e.g. ['D (R)', 'WB (R)']."""
    items = raw if isinstance(raw, (list, tuple)) else [raw] if raw else []
    out = []
    for item in items:
        s = str(item or "").upper().replace("STRIKER", "ST").strip()
        for part in re.split(r",\s*", s):
            m = re.match(r"^([A-Z/ ]+?)\s*(?:\(([LRC]+)\))?$", part.strip())
            if not m:
                continue
            roles, sides = [r.strip() for r in m.group(1).split("/") if r.strip()], m.group(2) or ""
            for role in roles:
                if role in ("GK", "DM", "SW"):
                    out.append("D (C)" if role == "SW" else role)
                elif role in ("ST", "S", "F"):
                    out.append("ST")
                elif role in ("D", "WB", "M", "AM"):
                    for side in sides or "C":
                        pos = "M (C)" if role == "M" and side == "C" else ("AM (L)" if role == "M" and side == "L" else "AM (R)" if role == "M" else f"{role} ({side})")
                        out.append("WB (L)" if pos == "WB (C)" else pos)
                elif role in ("DL", "DC", "DR", "ML", "MC", "MR", "AML", "AMC", "AMR", "WBL", "WBR"):
                    base, side = role[:-1], role[-1]
                    out.append(f"{'AM' if base == 'M' and side != 'C' else base} ({side})" if base != "M" or side != "C" else "M (C)")
    return list(dict.fromkeys(out))


def first_pos(p: dict) -> str:
    pos = p.get("positions") or []
    return pos[0] if pos else FALLBACK_POS


UNKNOWN_AGE = 99  # an unreadable age never counts as young, so no youth rule or reward can pick him by mistake


def _int(v, default=0):
    try:
        return int(v) if v is not None else default
    except (TypeError, ValueError):
        return default


def _iso(s: str) -> bool:
    from datetime import date
    try:
        date.fromisoformat(s)
        return True
    except ValueError:
        return False


def clean_player(p: dict) -> dict:
    """Same row with odd fields made safe: numbers that can't be read become 0/None, text becomes ''."""
    q = dict(p)
    q["positions"] = norm_positions(p.get("positions"))
    for k in ("minutes", "appearances", "goals", "assists", "ca", "pa", "value", "wage"):
        q[k] = _int(p.get(k))
    q["age"] = _int(p.get("age"), UNKNOWN_AGE)
    q["age_unknown"] = q["age"] == UNKNOWN_AGE and p.get("age") != UNKNOWN_AGE
    for k in ("name", "nationality", "club", "league"):
        q[k] = p.get(k) if isinstance(p.get(k), str) else ("Unknown" if k == "name" else "")
    try:
        q["avg_rating"] = float(p.get("avg_rating") or 0)
    except (TypeError, ValueError):
        q["avg_rating"] = 0.0
    ce = p.get("contract_end")
    q["contract_end"] = ce[:10] if isinstance(ce, str) and _iso(ce[:10]) else None
    q["attributes"] = {k: _int(v) for k, v in (p.get("attributes") or {}).items()} if isinstance(p.get("attributes"), dict) else {}
    return q


def clean_all(rows) -> list:
    out = []
    for p in rows or []:
        if isinstance(p, dict) and p.get("unique_id") is not None:
            out.append(clean_player(p))
    return out
