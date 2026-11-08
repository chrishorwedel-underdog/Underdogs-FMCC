"""Plain-sentence rule presets and evaluation. Rules, not AI."""
import random

FIELDS = {
    "age": ("age", "number"), "minutes": ("minutes this season", "number"), "appearances": ("appearances", "number"),
    "avg_rating": ("average rating", "number"), "goals": ("goals", "number"), "assists": ("assists", "number"),
    "ca": ("current ability", "number"), "pa": ("potential ability", "number"), "ca_growth": ("ability growth this season", "number"),
    "training_rating": ("training rating", "number"), "position": ("position group", "text"), "nationality": ("nationality", "text"),
    "league": ("league", "text"), "club": ("club", "text"),
    "xg90": ("xG per 90", "number"), "xa90": ("xA per 90", "number"), "key_passes90": ("key passes per 90", "number"),
    "pressures90": ("pressures per 90", "number"), "def_actions90": ("defensive actions per 90", "number"),
}
REWARD_MODULES = {"elite", "breakout", "dp"}
PARAM_MODULES = {"squad", "scouting", "reports", "development"}


def _rule(rid, name, conds, target, lo, hi, timing="season_end", join="and", max_value=200):
    return {"id": rid, "name": name, "enabled": True, "join": join, "timing": timing, "max_value": max_value,
            "conditions": [{"field": f, "op": o, "value": v} for f, o, v in conds], "action": {"target": target, "min": lo, "max": hi}}


PRESETS = {
    "elite": {"rules": [
        _rule("elite-1", "Standout trainee", [("age", "<=", 20), ("training_rating", ">=", 7.5)], "pa", 2, 5, "monthly", max_value=190),
        _rule("elite-2", "Exceptional trainee", [("age", "<=", 18), ("training_rating", ">=", 8.0), ("ca_growth", ">=", 5)], "pa", 4, 8, "monthly", max_value=195),
    ]},
    "breakout": {"rules": [
        _rule("bo-1", "Breakout of the Season", [("age", "<=", 22), ("minutes", ">=", 1500), ("avg_rating", ">=", 7.0)], "pa", 3, 8),
        _rule("bo-2", "Young Player of the Season", [("age", "<=", 20), ("minutes", ">=", 900), ("ca_growth", ">=", 6)], "pa", 2, 6),
        _rule("bo-3", "Late Bloomer", [("age", ">=", 24), ("ca_growth", ">=", 5)], "ca", 2, 4),
    ]},
    "dp": {"rules": [
        _rule("dp-1", "Growth", [("age", "<=", 23), ("minutes", ">=", 1200), ("avg_rating", ">=", 7.0)], "pa", 2, 6),
        _rule("dp-2", "Stalled", [("age", "<=", 23), ("minutes", "<=", 300)], "pa", -4, -1),
        _rule("dp-3", "Decline", [("age", ">=", 30), ("avg_rating", "<=", 6.5)], "pa", -3, -1),
    ], "scope": {"my_club": True, "nations": [], "leagues": []}, "caps": {"max_players": 500, "max_pa_change": 8}},
    "squad": {"params": {"target_minutes": 270, "max_youth": 3, "max_team_drop": 5, "max_slot_drop": 15, "max_senior": 25, "min_homegrown": 8}},
    "scouting": {"params": {"w_role": 40, "w_potential": 30, "w_age": 15, "w_value": 15, "over_threshold": 0.3}},
    "reports": {"params": {"rising": 3, "falling": -3}},
    "development": {"params": {"default_target": 270, "needs_pct": 60}},
}
PARAM_LIMITS = {"target_minutes": (0, 1000), "max_youth": (0, 11), "max_team_drop": (0, 50), "max_slot_drop": (0, 100), "max_senior": (11, 40),
                "min_homegrown": (0, 25), "w_role": (0, 100), "w_potential": (0, 100), "w_age": (0, 100), "w_value": (0, 100),
                "over_threshold": (0, 3), "rising": (0, 50), "falling": (-50, 0), "default_target": (0, 1000), "needs_pct": (0, 100)}


def check(cond: dict, ctx: dict) -> bool:
    v, target = ctx.get(cond["field"]), cond["value"]
    if v is None:
        return False
    if FIELDS[cond["field"]][1] == "text":
        same = str(v).lower() == str(target).lower()
        return same if cond["op"] in ("=", ">=", "<=") else not same
    target = float(target)
    return {">=": v >= target, "<=": v <= target, "=": v == target, "!=": v != target}[cond["op"]]


def matches(rule: dict, ctx: dict) -> bool:
    res = [check(c, ctx) for c in rule["conditions"]]
    return bool(res) and (all(res) if rule["join"] == "and" else any(res))


def first_match(rules: list, ctx: dict):
    return next((r for r in rules if r["enabled"] and matches(r, ctx)), None)


def roll(rule: dict, seed: str) -> int:
    lo, hi = sorted((rule["action"]["min"], rule["action"]["max"]))
    return random.Random(seed).randint(lo, hi)


def capped(current: int, delta: int, max_value: int) -> int:
    return max(1 - current, min(delta, max_value - current)) if delta > 0 else max(delta, 1 - current)
