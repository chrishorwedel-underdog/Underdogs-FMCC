"""Dynamic Potential rulesheet engine (Underdog FM Dynamic Potential Rulesheet, 11 November 2026).
Pure functions: every number comes from the settings, whose defaults are the rulesheet. Real CA/PA are used here only;
nothing returned for display contains them."""
import copy
import math

POS = ["GK", "CB", "FB", "DM", "CM", "AM", "W", "ST"]
POS_LABEL = {"GK": "Goalkeeper", "CB": "Centre-back", "FB": "Full-back / wing-back", "DM": "Defensive midfielder", "CM": "Central midfielder",
             "AM": "Attacking midfielder", "W": "Winger / wide forward", "ST": "Striker"}
METRIC_LABEL = {"save_pct": "Save %", "goals_prevented90": "Goals prevented / 90", "claims90": "Cross claims / 90", "sweeps90": "Sweeping actions / 90",
                "pass_pct": "Pass completion %", "aerial_pct": "Aerial win %", "tackle_pct": "Tackle success %", "interceptions90": "Interceptions / 90",
                "tackles_won90": "Tackles won / 90", "prog_passes90": "Progressive passes / 90", "def_actions90": "Defensive actions / 90",
                "key_passes90": "Chances created / 90", "poss_won90": "Possession won / 90", "poss_lost90": "Possession lost / 90",
                "xa90": "Expected assists / 90", "carries90": "Progressive carries / 90", "npxg90": "Non-penalty xG / 90", "dribbles90": "Dribbles / 90",
                "np_goals_minus_xg90": "Non-penalty goals minus xG / 90", "xg90": "xG / 90", "pressures90": "Pressures / 90"}

DEFAULTS = {
    "score": {"rating_weight": 55, "role_weight": 45, "group_weights": {"A": 40, "B": 35, "C": 25}, "min_comparison": 25, "youth_weight": 75, "level_band": 15},
    "metrics": {
        "GK": {"A": ["save_pct", "goals_prevented90"], "B": ["claims90", "sweeps90"], "C": ["pass_pct"]},
        "CB": {"A": ["aerial_pct", "tackle_pct"], "B": ["interceptions90", "tackles_won90"], "C": ["prog_passes90"]},
        "FB": {"A": ["tackle_pct", "def_actions90"], "B": ["prog_passes90"], "C": ["key_passes90"]},
        "DM": {"A": ["poss_won90", "interceptions90"], "B": ["pass_pct", "poss_lost90"], "C": ["prog_passes90"]},
        "CM": {"A": ["prog_passes90"], "B": ["key_passes90"], "C": ["poss_won90", "interceptions90"]},
        "AM": {"A": ["xa90", "key_passes90"], "B": ["prog_passes90", "carries90"], "C": ["npxg90"]},
        "W": {"A": ["npxg90"], "B": ["xa90", "key_passes90"], "C": ["dribbles90", "carries90"]},
        "ST": {"A": ["npxg90"], "B": ["np_goals_minus_xg90"], "C": ["xa90", "key_passes90"]},
    },
    "standins": {"carries90": "prog_passes90", "npxg90": "xg90", "goals_prevented90": "save_pct", "interceptions90": "def_actions90",
                 "poss_won90": "def_actions90", "tackles_won90": "def_actions90", "dribbles90": "carries90"},
    "reverse": ["poss_lost90"],
    "bands": [[97, 12], [95, 11], [93, 10], [90, 9], [88, 8], [86, 7], [83, 6], [80, 5], [75, 4], [70, 3], [65, 2], [30, 0], [25, -1], [20, -2], [15, -3], [10, -4], [0, -5]],
    "tiers": {"above": {"min": 2, "max": 4, "minutes": 1100}, "excellent": {"min": 5, "max": 8, "minutes": 1400},
              "exceptional": {"min": 9, "max": 12, "senior_minutes": 1800, "half_senior_minutes": 400, "min_percentile": 85},
              "youth_max": 8, "ratings_only_auto_max": 4},
    "decline": {"ordinary": {"max": 3, "season_minutes": 1300, "half_minutes": 300, "score_below": 30, "half_rating_below": 35},
                "severe": {"max": 5, "season_minutes": 1800, "half_minutes": 600, "score_below": 15, "half_rating_below": 25},
                "season_percentiles_below": 35, "low_senior_share": 60, "low_senior_max": 2},
    "age": [[25, 0], [26, 1], [27, 2], [28, 3], [29, 4], [30, 5], [31, 6], [32, 7], [33, 8]],
    "growth_taper": [[165, 100], [174, 75], [184, 50], [199, 25], [200, 0]],
    "decline_taper": [[135, 100], [125, 80], [115, 60], [105, 40], [96, 20], [0, 0]],
    "winter": {"min_minutes": 550, "share": 50, "max": 4, "youth_max": 8},
    "limits": {"floor": 95, "max_pa": 200, "season_max_growth": 12, "season_max_loss": 5, "return_minutes": 1300, "return_half_minutes": 300},
    "batch_size": 500,
}
SECTIONS = list(DEFAULTS)


def defaults() -> dict:
    return copy.deepcopy(DEFAULTS)


def validate(s: dict) -> list:
    """Plain-words problems; empty when the settings can be saved."""
    errs = []
    missing = [k for k in DEFAULTS if k not in s]
    if missing:
        return [f"Missing section: {', '.join(missing)}"]
    sc = s["score"]
    if sc["rating_weight"] + sc["role_weight"] != 100:
        errs.append("Match rating and role output weights must add up to 100")
    if sum(sc["group_weights"].values()) != 100 or set(sc["group_weights"]) != {"A", "B", "C"}:
        errs.append("Role groups A, B and C must add up to 100")
    th = [b[0] for b in s["bands"]]
    if th != sorted(th, reverse=True) or len(set(th)) != len(th) or th[-1] != 0 or th[0] > 100:
        errs.append("Score bands must run from highest to lowest without overlapping, ending at 0")
    t = s["tiers"]
    if not (t["above"]["min"] <= t["above"]["max"] < t["excellent"]["min"] <= t["excellent"]["max"] < t["exceptional"]["min"] <= t["exceptional"]["max"]):
        errs.append("Growth tiers must not overlap: Above expectations, then Excellent, then Exceptional")
    ages = [a[0] for a in s["age"]]
    if ages != sorted(ages) or len(set(ages)) != len(ages):
        errs.append("Age table must go from youngest to oldest")
    gt = [x[0] for x in s["growth_taper"]]
    if gt != sorted(gt) or any(not 0 <= x[1] <= 100 for x in s["growth_taper"]):
        errs.append("Growth taper must go from lowest to highest PA, with shares between 0 and 100%")
    dt = [x[0] for x in s["decline_taper"]]
    if dt != sorted(dt, reverse=True) or any(not 0 <= x[1] <= 100 for x in s["decline_taper"]):
        errs.append("Decline taper must go from highest to lowest PA, with shares between 0 and 100%")
    if not 1 <= s["batch_size"] <= 5000:
        errs.append("Batch size must be between 1 and 5,000")
    for pos in POS:
        if set((s["metrics"].get(pos) or {})) != {"A", "B", "C"}:
            errs.append(f"{POS_LABEL[pos]} needs metric groups A, B and C")
    nums = [sc["min_comparison"], sc["youth_weight"], s["winter"]["min_minutes"], s["limits"]["floor"], s["limits"]["max_pa"]]
    if any(not isinstance(v, (int, float)) or v < 0 for v in nums):
        errs.append("Values can't be negative")
    return errs


def percentile(values: list, v: float, reverse: bool = False) -> float:
    vals = [x for x in values if x is not None]
    if not vals or v is None:
        return None
    below = sum(1 for x in vals if (x > v if reverse else x < v))
    equal = sum(1 for x in vals if x == v)
    return round(100 * (below + 0.5 * equal) / len(vals), 1)


def base_change(score: float, s: dict) -> int:
    return next(d for t, d in s["bands"] if score >= t)


def age_deduction(age: int, s: dict) -> int:
    out = 0
    for a, d in s["age"]:
        if age >= a:
            out = d
    return out


def growth_taper(pa: int, pts: int, s: dict) -> int:
    acc, cap = 0.0, s["limits"]["max_pa"]
    for _ in range(max(0, pts)):
        cur = pa + math.floor(acc)
        share = next((sh for top, sh in s["growth_taper"] if cur <= top), 0) / 100
        acc += share
    return max(0, min(math.floor(acc), cap - pa))


def decline_taper(pa: int, pts: int, s: dict) -> int:
    acc = 0.0
    for _ in range(max(0, pts)):
        cur = pa - math.floor(acc)
        share = next((sh for low, sh in s["decline_taper"] if cur >= low), 0) / 100
        acc += share
    return math.floor(acc)


def score_player(p: dict, group: list, s: dict) -> dict:
    """Performance Score: 55% match-rating percentile + 45% role-output percentile (weights from settings)."""
    sc = s["score"]
    rating_pct = percentile([g.get("avg_rating") for g in group], p.get("avg_rating"))
    role, used, standins, missing, player_gap = {}, [], [], [], False
    for gk, metrics in s["metrics"][p["position"]].items():
        vals = []
        for m in metrics:
            field = m
            if p.get(m) is None and s["standins"].get(m) and p.get(s["standins"][m]) is not None:
                field = s["standins"][m]
                standins.append(f"{METRIC_LABEL.get(m, m)} \u2192 {METRIC_LABEL.get(field, field)}")
            if p.get(field) is None:
                if any(g.get(field) is not None for g in group):
                    player_gap = True
                missing.append(METRIC_LABEL.get(m, m))
                continue
            vals.append(percentile([g.get(field) for g in group], p[field], field in s["reverse"]))
            used.append(METRIC_LABEL.get(field, field))
        if vals:
            role[gk] = sum(vals) / len(vals)
    usable = len(role)
    role_pct = sum(role[g] * sc["group_weights"][g] for g in role) / sum(sc["group_weights"][g] for g in role) if role else None
    if rating_pct is None:
        score, ratings_only = None, usable < 2
    elif usable >= 2:
        score, ratings_only = (sc["rating_weight"] * rating_pct + sc["role_weight"] * role_pct) / 100, False
    else:
        score, ratings_only = rating_pct, True
    return {"rating_pct": rating_pct, "role_pct": round(role_pct, 1) if role_pct is not None else None, "score": round(score, 2) if score is not None else None,
            "groups_used": sorted(role), "metrics_used": list(dict.fromkeys(used)), "standins": list(dict.fromkeys(standins)),
            "missing": list(dict.fromkeys(missing)), "ratings_only": ratings_only, "provisional": player_gap}


def _growth_tier(base: int, ev: dict, sc: dict, s: dict) -> tuple:
    t = s["tiers"]
    youth = ev["youth_minutes"] > 0
    eff = ev["senior_minutes"] + ev["youth_minutes"] * s["score"]["youth_weight"] / 100
    exc = (not youth and ev["senior_minutes"] >= t["exceptional"]["senior_minutes"] and ev["halves_known"]
           and min(ev["h1"], ev["h2"]) >= t["exceptional"]["half_senior_minutes"] and not sc["ratings_only"]
           and (sc["rating_pct"] or 0) >= t["exceptional"]["min_percentile"] and (sc["role_pct"] or 0) >= t["exceptional"]["min_percentile"])
    if base >= t["exceptional"]["min"] and exc:
        return base, "Exceptional", None
    if eff >= t["excellent"]["minutes"]:
        cap = min(base, t["excellent"]["max"], t["youth_max"] if youth else 99)
        return cap, "Excellent" if cap >= t["excellent"]["min"] else "Above expectations", "capped at Excellent" if cap < base else None
    if eff >= t["above"]["minutes"]:
        return min(base, t["above"]["max"]), "Above expectations", "capped at Above expectations" if base > t["above"]["max"] else None
    return 0, None, f"needs {t['above']['minutes']:,} competitive minutes to grow"


def _decline(base: int, ev: dict, sc: dict, s: dict) -> tuple:
    d = s["decline"]

    def meets(r):
        return (ev["minutes"] >= r["season_minutes"] and ev["halves_known"] and min(ev["h1"], ev["h2"]) >= r["half_minutes"]
                and sc["score"] < r["score_below"] and ev["h1_rating_pct"] is not None and ev["h2_rating_pct"] is not None
                and max(ev["h1_rating_pct"], ev["h2_rating_pct"]) < r["half_rating_below"]
                and (sc["rating_pct"] or 100) < d["season_percentiles_below"] and (sc["role_pct"] or 100) < d["season_percentiles_below"]
                and len(sc["groups_used"]) >= 2)
    if meets(d["severe"]):
        loss = min(-base, d["severe"]["max"])
    elif meets(d["ordinary"]):
        loss = min(-base, d["ordinary"]["max"])
    else:
        return 0, "doesn't meet every decline requirement, so no loss"
    if ev["senior_share"] < d["low_senior_share"]:
        loss = min(loss, d["low_senior_max"])
    return -loss, None


def assess(p: dict, sc: dict, ev: dict, s: dict, kind: str, winter_applied: int, dp_points: int, group_size: int) -> dict:
    """One player's review. `p` carries real pa/ca for the maths only; the returned record never does."""
    L = s["limits"]
    rec = {"kind": kind, "group_size": group_size, "winter_applied": winter_applied, "age": ev["age"], "age_deduction": 0,
           "base": None, "tier": None, "after_age": None, "taper_reduced": False, "capped": [], "change": 0, "status": "none", "flags": []}
    if sc["score"] is None:
        return rec | {"status": "held", "reason": "No match ratings in this period, so there's no evidence to judge"}
    if kind == "winter" and ev["minutes"] < s["winter"]["min_minutes"]:
        return rec | {"reason": f"Needs {s['winter']['min_minutes']} competitive minutes before the winter review"}
    base = base_change(sc["score"], s)
    rec["base"] = base
    ref = p["pa"] - dp_points
    if base > 0:
        if kind == "winter":
            t = s["tiers"]
            exc_ok = ev["youth_minutes"] == 0 and not sc["ratings_only"] and min(sc["rating_pct"] or 0, sc["role_pct"] or 0) >= t["exceptional"]["min_percentile"]
            g = min(base, s["winter"]["youth_max"] if ev["youth_minutes"] > 0 or not exc_ok else L["season_max_growth"])
            rec["tier"] = "Provisional"
        else:
            g, rec["tier"], why = _growth_tier(base, ev, sc, s)
            if why:
                rec["capped"].append(why)
        g = min(g, L["season_max_growth"])
        ded = age_deduction(ev["age"], s)
        rec["age_deduction"] = ded
        g = max(0, g - ded)
        rec["after_age"] = g
        tg = growth_taper(ref, g, s)
        rec["taper_reduced"] = tg < g
        if kind == "winter":
            change = min(math.floor(tg * s["winter"]["share"] / 100), s["winter"]["max"])
        else:
            change = tg - winter_applied
    elif base < 0:
        if kind == "winter":
            return rec | {"status": "flag", "flags": ["monitoring"], "reason": "Poor first half: being monitored. Losses are only decided at season-end"}
        if sc["ratings_only"]:
            return rec | {"status": "flag", "flags": ["concern"], "reason": "Ratings point to a decline, but without role statistics no loss is applied"}
        if sc["provisional"] or not ev["halves_known"]:
            return rec | {"status": "held", "reason": "A decline is held until the missing evidence is resolved"}
        loss, why = _decline(base, ev, sc, s)
        if why:
            rec["capped"].append(why)
        floor = max(L["floor"], p.get("ca") or 0)
        tl = min(decline_taper(ref, -loss, s), max(0, ref - floor), L["season_max_loss"])
        rec["taper_reduced"] = tl < -loss
        if ref < L["floor"]:
            tl = 0
        change = -tl - winter_applied
    else:
        change = -winter_applied
    if kind == "season_end" and change < 0 and winter_applied > 0:
        can_return = (ev["minutes"] >= L["return_minutes"] and ev["halves_known"] and min(ev["h1"], ev["h2"]) >= L["return_half_minutes"] and not sc["provisional"])
        if not can_return:
            change = min(0, change + winter_applied) if base < 0 else 0
            rec["capped"].append("winter points kept: not enough evidence to take them back")
    if ref < L["floor"] and change < 0:
        change = max(change, -winter_applied) if winter_applied else 0
    change = max(min(change, L["max_pa"] - p["pa"]), -L["season_max_loss"] - winter_applied)
    status = "auto" if change else "none"
    if group_size < s["score"]["min_comparison"]:
        status = "needs_review"
        rec["flags"].append(f"only {group_size} comparison players (needs {s['score']['min_comparison']})")
    if sc["ratings_only"] and change > s["tiers"]["ratings_only_auto_max"]:
        status = "needs_review"
        rec["flags"].append(f"ratings-only growth above +{s['tiers']['ratings_only_auto_max']}")
    if sc["provisional"] and change < 0:
        status = "held"
    rec |= {"change": change, "status": status if change or status == "needs_review" else "none"}
    rec["reason"] = reason(rec, ev, sc)
    return rec


def reason(rec: dict, ev: dict, sc: dict) -> str:
    sc_txt = sc["score"]
    word = "Exceptional" if sc_txt >= 90 else "Strong" if sc_txt >= 75 else "Good" if sc_txt >= 65 else "Steady" if sc_txt >= 30 else "Poor"
    bits = [f"{word} {'first half' if rec['kind'] == 'winter' else 'season'}", f"{ev['minutes']:,} minutes"]
    if rec["age_deduction"]:
        bits.append(f"age {ev['age']} (\u2212{rec['age_deduction']})")
    if rec["taper_reduced"]:
        bits.append("taper applied")
    bits += rec["capped"]
    if rec["winter_applied"]:
        bits.append(f"+{rec['winter_applied']} already given at winter")
    return ", ".join(bits)
