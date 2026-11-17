"""Role ratings, formations, Best XI, Development XI and depth charts (rules-based, no AI)."""
GK_ATTRS = ["handling", "reflexes", "one_on_ones", "kicking", "command_of_area", "aerial_reach"]
OUTFIELD_ATTRS = ["passing", "first_touch", "technique", "dribbling", "crossing", "finishing", "heading", "tackling", "marking",
                  "vision", "flair", "off_the_ball", "work_rate", "strength", "jumping_reach", "stamina"]
SHARED_ATTRS = ["positioning", "decisions", "composure", "anticipation", "pace", "acceleration"]

# role key: name, duty, key attributes (double weight), other attributes
ROLES = {
    "sk": ("Sweeper Keeper", "Defend", ["reflexes", "one_on_ones", "handling", "command_of_area"], ["kicking", "composure", "decisions", "anticipation", "acceleration"]),
    "gk": ("Goalkeeper", "Defend", ["handling", "reflexes", "aerial_reach", "command_of_area"], ["positioning", "decisions", "composure"]),
    "bpd": ("Ball-Playing Defender", "Defend", ["tackling", "marking", "positioning", "heading", "passing", "composure"], ["vision", "first_touch", "technique", "strength", "jumping_reach", "anticipation", "decisions"]),
    "cd": ("Central Defender", "Defend", ["tackling", "marking", "heading", "positioning", "strength", "jumping_reach"], ["anticipation", "decisions", "composure", "pace"]),
    "fb": ("Full Back", "Support", ["tackling", "marking", "positioning", "anticipation", "work_rate"], ["crossing", "passing", "stamina", "pace", "decisions"]),
    "wb": ("Wing Back", "Support", ["crossing", "stamina", "work_rate", "tackling", "pace", "off_the_ball"], ["dribbling", "first_touch", "passing", "technique", "acceleration", "decisions"]),
    "dlp": ("Deep-Lying Playmaker", "Defend", ["passing", "first_touch", "technique", "vision", "composure", "decisions"], ["tackling", "positioning", "anticipation", "work_rate"]),
    "dm": ("Defensive Midfielder", "Defend", ["tackling", "positioning", "anticipation", "work_rate", "decisions"], ["marking", "passing", "stamina", "strength", "composure"]),
    "bbm": ("Box-to-Box Midfielder", "Support", ["passing", "stamina", "work_rate", "tackling", "off_the_ball", "decisions"], ["first_touch", "finishing", "technique", "anticipation", "strength", "pace"]),
    "ap": ("Advanced Playmaker", "Attack", ["passing", "first_touch", "technique", "vision", "composure", "decisions", "flair"], ["dribbling", "off_the_ball", "anticipation"]),
    "if": ("Inside Forward", "Attack", ["finishing", "dribbling", "first_touch", "technique", "off_the_ball", "acceleration"], ["pace", "composure", "flair", "anticipation", "passing"]),
    "w": ("Winger", "Attack", ["crossing", "dribbling", "technique", "pace", "acceleration"], ["first_touch", "passing", "off_the_ball", "flair", "work_rate", "stamina"]),
    "af": ("Advanced Forward", "Attack", ["finishing", "first_touch", "technique", "off_the_ball", "composure", "acceleration"], ["dribbling", "pace", "anticipation", "decisions", "passing"]),
    "tf": ("Target Forward", "Support", ["heading", "strength", "jumping_reach", "finishing", "composure"], ["first_touch", "off_the_ball", "anticipation", "work_rate"]),
}
ROLE_POSITIONS = {"sk": ["GK"], "gk": ["GK"], "bpd": ["D (C)"], "cd": ["D (C)"], "fb": ["D (L)", "D (R)", "WB (L)", "WB (R)"],
                  "wb": ["D (L)", "D (R)", "WB (L)", "WB (R)"], "dlp": ["DM", "M (C)"], "dm": ["DM"], "bbm": ["M (C)", "DM"],
                  "ap": ["AM (C)", "M (C)"], "if": ["AM (L)", "AM (R)"], "w": ["AM (L)", "AM (R)"], "af": ["ST"], "tf": ["ST"]}
LABELS = {"GK": "Goalkeeper", "LB": "Left Back", "CB": "Centre Back", "RB": "Right Back", "DM": "Defensive Midfield",
          "CM": "Central Midfield", "AM": "Attacking Midfield", "LW": "Left Wing", "RW": "Right Wing", "ST": "Striker"}
_BACK = [("GK", "GK", "sk", ["GK"], 50, 91), ("DL", "LB", "fb", ["D (L)", "WB (L)"], 14, 72), ("DCL", "CB", "bpd", ["D (C)"], 37, 77),
         ("DCR", "CB", "cd", ["D (C)"], 63, 77), ("DR", "RB", "wb", ["D (R)", "WB (R)"], 86, 72)]
FORMATIONS = {
    "433": ("4-3-3", _BACK + [("DM", "DM", "dlp", ["DM"], 50, 58), ("MCL", "CM", "bbm", ["M (C)"], 29, 46),
                              ("MCR", "CM", "ap", ["M (C)", "AM (C)"], 71, 46), ("AML", "LW", "if", ["AM (L)"], 17, 24),
                              ("AMR", "RW", "w", ["AM (R)"], 83, 24), ("ST", "ST", "af", ["ST"], 50, 13)]),
    "4231": ("4-2-3-1", _BACK + [("DMCL", "DM", "dlp", ["DM", "M (C)"], 37, 58), ("DMCR", "DM", "bbm", ["DM", "M (C)"], 63, 58),
                                 ("AMC", "AM", "ap", ["AM (C)"], 50, 38), ("AML", "LW", "if", ["AM (L)"], 17, 27),
                                 ("AMR", "RW", "w", ["AM (R)"], 83, 27), ("ST", "ST", "af", ["ST"], 50, 13)]),
}
_S = {"GK": ("GK", "GK", "sk", ["GK"], 50, 91), "DL": ("DL", "LB", "fb", ["D (L)", "WB (L)"], 14, 72), "DR": ("DR", "RB", "wb", ["D (R)", "WB (R)"], 86, 72),
      "DCL": ("DCL", "CB", "bpd", ["D (C)"], 37, 77), "DCR": ("DCR", "CB", "cd", ["D (C)"], 63, 77), "DC": ("DC", "CB", "cd", ["D (C)"], 50, 79),
      "DCL3": ("DCL", "CB", "bpd", ["D (C)"], 28, 76), "DCR3": ("DCR", "CB", "cd", ["D (C)"], 72, 76),
      "WBL": ("WBL", "LB", "wb", ["WB (L)", "D (L)"], 10, 56), "WBR": ("WBR", "RB", "wb", ["WB (R)", "D (R)"], 90, 56),
      "DM": ("DM", "DM", "dm", ["DM"], 50, 60), "DMCL": ("DMCL", "DM", "dlp", ["DM", "M (C)"], 37, 58), "DMCR": ("DMCR", "DM", "bbm", ["DM", "M (C)"], 63, 58),
      "MCL": ("MCL", "CM", "bbm", ["M (C)"], 32, 45), "MC": ("MC", "CM", "dlp", ["M (C)", "DM"], 50, 48), "MCR": ("MCR", "CM", "ap", ["M (C)", "AM (C)"], 68, 45),
      "ML": ("ML", "LW", "w", ["M (L)", "AM (L)", "WB (L)"], 13, 42), "MR": ("MR", "RW", "w", ["M (R)", "AM (R)", "WB (R)"], 87, 42),
      "AMC": ("AMC", "AM", "ap", ["AM (C)", "M (C)"], 50, 31), "AMCL": ("AMCL", "AM", "ap", ["AM (C)", "AM (L)"], 36, 29), "AMCR": ("AMCR", "AM", "ap", ["AM (C)", "AM (R)"], 64, 29),
      "AML": ("AML", "LW", "if", ["AM (L)"], 17, 25), "AMR": ("AMR", "RW", "w", ["AM (R)"], 83, 25),
      "ST": ("ST", "ST", "af", ["ST"], 50, 13), "STL": ("STL", "ST", "af", ["ST"], 38, 14), "STR": ("STR", "ST", "tf", ["ST"], 62, 14)}
_B4 = ["GK", "DL", "DCL", "DCR", "DR"]
_B3 = ["GK", "DCL3", "DC", "DCR3"]
_B5 = ["GK", "WBL", "DCL3", "DC", "DCR3", "WBR"]
# Every other formation, for experimenting with lineups on the Squad page.
EXTRA_FORMATIONS = {k: (n, [_S[s] for s in slots]) for k, n, slots in [
    ("442", "4-4-2", _B4 + ["ML", "MCL", "MCR", "MR", "STL", "STR"]), ("4411", "4-4-1-1", _B4 + ["ML", "MCL", "MCR", "MR", "AMC", "ST"]),
    ("4141", "4-1-4-1", _B4 + ["DM", "ML", "MCL", "MCR", "MR", "ST"]), ("451", "4-5-1", _B4 + ["ML", "MCL", "MC", "MCR", "MR", "ST"]),
    ("41212", "4-1-2-1-2 (diamond)", _B4 + ["DM", "MCL", "MCR", "AMC", "STL", "STR"]), ("4312", "4-3-1-2", _B4 + ["MCL", "MC", "MCR", "AMC", "STL", "STR"]),
    ("4321", "4-3-2-1", _B4 + ["MCL", "MC", "MCR", "AMCL", "AMCR", "ST"]), ("4222", "4-2-2-2", _B4 + ["DMCL", "DMCR", "AMCL", "AMCR", "STL", "STR"]),
    ("424", "4-2-4", _B4 + ["MCL", "MCR", "AML", "AMR", "STL", "STR"]), ("4231n", "4-2-3-1 narrow", _B4 + ["DMCL", "DMCR", "AMCL", "AMC", "AMCR", "ST"]),
    ("433dm", "4-3-3 two holding", _B4 + ["DMCL", "DMCR", "MC", "AML", "AMR", "ST"]),
    ("352", "3-5-2", _B3 + ["WBL", "WBR", "DM", "MCL", "MCR", "STL", "STR"]), ("343", "3-4-3", _B3 + ["WBL", "MCL", "MCR", "WBR", "AML", "AMR", "ST"]),
    ("3412", "3-4-1-2", _B3 + ["WBL", "MCL", "MCR", "WBR", "AMC", "STL", "STR"]), ("3421", "3-4-2-1", _B3 + ["WBL", "MCL", "MCR", "WBR", "AMCL", "AMCR", "ST"]),
    ("3511", "3-5-1-1", _B3 + ["WBL", "MCL", "MC", "MCR", "WBR", "AMC", "ST"]),
    ("532", "5-3-2", _B5 + ["MCL", "MC", "MCR", "STL", "STR"]), ("541", "5-4-1", _B5 + ["ML", "MCL", "MCR", "MR", "ST"]),
    ("5212", "5-2-1-2", _B5 + ["MCL", "MCR", "AMC", "STL", "STR"]), ("523", "5-2-3", _B5 + ["MCL", "MCR", "AML", "AMR", "ST"])]}
ALL_FORMATIONS = FORMATIONS | EXTRA_FORMATIONS
FM_CODE = {"DMC": "DM", "DML": "DMCL", "DMR": "DMCR", "STC": "ST", "STCL": "STL", "STCR": "STR", "SC": "ST", "SCL": "STL", "SCR": "STR"}


def match_tactic(t: dict) -> str | None:
    """Closest FMCC formation for a tactic read from the save: by its 11 position codes, else a shape like 4-2-3-1 in its name."""
    import re
    from collections import Counter
    codes = Counter(FM_CODE.get(c, c) for c in (str(x).upper().replace(" ", "") for x in t.get("positions") or []))
    if sum(codes.values()) >= 10:
        score = {k: sum((codes & Counter(s[0] for s in v[1])).values()) for k, v in ALL_FORMATIONS.items()}
        best = max(score, key=lambda k: (score[k], k in FORMATIONS))
        if score[best] >= 8:
            return best
    m = re.search(r"\d(?:-\d){2,4}", t.get("name") or "")
    return next((k for k, v in ALL_FORMATIONS.items() if m and v[0].startswith(m.group(0))), None)
DEFAULT_RULES = {"target_minutes": 270, "max_youth": 3, "max_team_drop": 5, "max_slot_drop": 15}


def role_rating(player: dict, role: str) -> int:
    a = player.get("attributes") or {}
    _, _, key, other = ROLES[role]
    total = 2 * sum(a.get(k, 0) for k in key) + sum(a.get(k, 0) for k in other)
    return round(total / (2 * len(key) + len(other)) * 5)


def role_ratings(player: dict) -> list:
    rows = [{"role": k, "name": v[0], "duty": v[1], "rating": role_rating(player, k),
             "natural": bool(set(player["positions"]) & set(ROLE_POSITIONS[k]))} for k, v in ROLES.items()]
    return sorted(rows, key=lambda r: (not r["natural"], -r["rating"]))


def best_role(player: dict) -> dict:
    return role_ratings(player)[0]



def fit_words(player: dict, role: str) -> dict | None:
    """How well he suits a role, in words plus a short reason from the role's key attributes."""
    a = player.get("attributes") or {}
    if not a:
        return None
    r = role_rating(player, role)
    word = "Excellent fit" if r >= 75 else "Good fit" if r >= 62 else "Fair fit" if r >= 50 else "Poor fit"
    vals = sorted(((a.get(k, 0), k) for k in ROLES[role][2]), reverse=True)
    name = lambda k: k.replace("_", " ")  # noqa: E731
    strong = [name(k) for v, k in vals if v >= 14][:2]
    weak = [name(k) for v, k in reversed(vals) if v <= 10][:1]
    parts = ([f"strong {' and '.join(strong)}"] if strong else []) + ([f"weaker {weak[0]}"] if weak else [])
    return {"word": word, "tone": {"Excellent fit": "ok", "Good fit": "g", "Fair fit": "a", "Poor fit": "r"}[word],
            "reason": ", ".join(parts) if parts else "no standout strengths or weaknesses for this role"}


def formation_meta(key: str) -> dict:
    name, slots = ALL_FORMATIONS[key]
    return {"key": key, "name": name, "slots": [{"key": s, "pos": p, "label": LABELS[p], "role": r, "role_name": f"{ROLES[r][0]} ({ROLES[r][1]})",
                                                 "positions": acc, "x": x, "y": y} for s, p, r, acc, x, y in slots]}


def natural_positions(player: dict) -> list:
    """His first-listed position plus every position FM rates him Natural (just the first when the save gives no ratings)."""
    pos = player.get("positions") or []
    return list(dict.fromkeys(pos[:1] + [x for x in (player.get("natural") or []) if isinstance(x, str)]))


def eligible(player: dict, slot: dict) -> bool:
    return bool(set(natural_positions(player)) & set(slot["positions"]))


# Nearby positions that may cover a slot when too few players play there naturally (goalkeepers: none).
COVER = {"GK": [], "CB": ["DM"], "LB": ["WB (L)", "D (L)", "D (C)"], "RB": ["WB (R)", "D (R)", "D (C)"], "DM": ["M (C)", "D (C)"],
         "CM": ["DM", "AM (C)"], "AM": ["M (C)", "AM (L)", "AM (R)", "M (L)", "M (R)"],
         "LW": ["AM (L)", "M (L)", "AM (C)", "WB (L)", "ST"], "RW": ["AM (R)", "M (R)", "AM (C)", "WB (R)", "ST"], "ST": ["AM (C)", "AM (L)", "AM (R)"]}
MIN_NATURAL, FILL_TO, OOP_COST = 2, 3, 500
STAR_CA = 15  # one star = this much in-FM ability below the squad's best (internal only, never shown)


def stars(score: float) -> float:
    return max(.5, min(5.0, round(score / 10) / 2))


def _score(p: dict, top: int) -> float:
    """Squad-relative 0-100 score from in-FM ability; internal only. 20 points = one star."""
    return max(0.0, 100 - (top - (p.get("ca") or 0)) * 20 / STAR_CA)


def depth_chart(players: list, form: dict) -> dict:
    top = max([p.get("ca") or 0 for p in players] or [0])
    row = lambda p, oop: {"unique_id": p["unique_id"], "rating": _score(p, top), "stars": stars(_score(p, top)), "oop": oop}  # noqa: E731
    out = {}
    for s in form["slots"]:
        nat = sorted([p for p in players if eligible(p, s)], key=lambda p: -(p.get("ca") or 0))
        rows = [row(p, False) for p in nat]
        if len(nat) < MIN_NATURAL:
            ids = {p["unique_id"] for p in nat}
            cover = sorted([p for p in players if p["unique_id"] not in ids and set(natural_positions(p)) & set(COVER.get(s["pos"], []))], key=lambda p: -(p.get("ca") or 0))
            rows += [row(p, True) for p in cover[:FILL_TO - len(nat)]]
        out[s["key"]] = rows
    return out


def public_depth(depth: dict) -> dict:
    """Depth chart for the browser: order, stars and the out-of-position tag only."""
    return {k: [{"unique_id": r["unique_id"], "stars": r["stars"], "oop": r["oop"]} for r in v] for k, v in depth.items()}


def score(assign: dict, depth: dict) -> float:
    """Average internal score of a lineup (for FMCC's own rules; never shown)."""
    vals = [next((r["rating"] for r in depth[k] if r["unique_id"] == uid), 0) for k, uid in assign.items() if uid]
    return sum(vals) / max(1, len(vals))


def strength(assign: dict, depth: dict) -> float:
    """Lineup strength in stars."""
    return stars(score(assign, depth))


def star_words(points: float) -> str:
    s = round(points / 10) / 2
    return "less than half a star" if s < .5 else f"{s:g} star{'' if s == 1 else 's'}"


def _hungarian(cost: list) -> list:
    """Minimum-cost assignment of n rows to m >= n columns (exact, same result as trying every lineup)."""
    n, m = len(cost), len(cost[0])
    inf = float("inf")
    u, v, p, way = [0] * (n + 1), [0] * (m + 1), [0] * (m + 1), [0] * (m + 1)
    for i in range(1, n + 1):
        p[0], j0 = i, 0
        minv, used = [inf] * (m + 1), [False] * (m + 1)
        while True:
            used[j0] = True
            i0, delta, j1 = p[j0], inf, 0
            for j in range(1, m + 1):
                if not used[j]:
                    cur = cost[i0 - 1][j - 1] - u[i0] - v[j]
                    if cur < minv[j]:
                        minv[j], way[j] = cur, j0
                    if minv[j] < delta:
                        delta, j1 = minv[j], j
            for j in range(m + 1):
                if used[j]:
                    u[p[j]] += delta
                    v[j] -= delta
                else:
                    minv[j] -= delta
            j0 = j1
            if p[j0] == 0:
                break
        while j0:
            j1 = way[j0]
            p[j0] = p[j1]
            j0 = j1
    res = [None] * n
    for j in range(1, m + 1):
        if p[j]:
            res[p[j] - 1] = j - 1
    return res


def best_xi(players: list, form: dict, depth: dict) -> dict:
    """The strongest lineup: natural players first, then out-of-position cover, by in-FM ability (optimal assignment)."""
    rate = {k: {r["unique_id"]: r["rating"] - (OOP_COST if r.get("oop") else 0) for r in v} for k, v in depth.items()}
    slots = [s["key"] for s in form["slots"]]
    uids = sorted({u for r in rate.values() for u in r})
    if not uids:
        return {k: None for k in slots}
    cols = uids + [None] * len(slots)
    cost = [[-rate[k][u] if u is not None and u in rate[k] else (0 if u is None else 10_000) for u in cols] for k in slots]
    pick = _hungarian(cost)
    return {k: (cols[j] if cols[j] is not None and cols[j] in rate[k] else None) for k, j in zip(slots, pick)}


def development_xi(best: dict, form: dict, depth: dict, info: dict, rules: dict) -> tuple:
    """Start from the Best XI and give starts to under-21s who are short of minutes, within the rule limits."""
    rate = {k: {r["unique_id"]: r["rating"] for r in v} for k, v in depth.items()}
    labels = {s["key"]: s["label"] for s in form["slots"]}
    assign = dict(best)
    best_avg = score(best, depth)
    youth = [uid for uid in assign.values() if uid and info[uid]["u21"]]
    picked, skipped = [], []
    needy = sorted([u for u, i in info.items() if i["u21"] and u not in assign.values() and i["month_minutes"] < rules["target_minutes"]],
                   key=lambda u: (info[u]["month_minutes"], -max([rate[k].get(u, 0) for k in rate] or [0])))
    for uid in needy:
        if len(youth) >= rules["max_youth"]:
            skipped.append((uid, "limit", None, None))
            continue
        options = [(rate[k][assign[k]] - rate[k][uid], k) for k in assign if uid in rate[k] and assign[k] and not info[assign[k]]["u21"]]
        if not options:
            skipped.append((uid, "position", None, None))
            continue
        drop, slot = min(options)
        trial = dict(assign, **{slot: uid})
        if drop > rules["max_slot_drop"] or best_avg - score(trial, depth) > rules["max_team_drop"]:
            skipped.append((uid, "drop", slot, drop))
            continue
        assign = trial
        youth.append(uid)
        picked.append(uid)
    why = []
    dev_avg = score(assign, depth)
    if picked:
        names = ", ".join(info[u]["name"] for u in picked)
        why.append(("acc", f"Gives {len(picked)} under-21 {'player' if len(picked) == 1 else 'players'} a start: {names}."))
    else:
        why.append(("blu", "No under-21 player fits your rules this time, so it matches the Best XI."))
    why.append(("acc", f"Team strength {stars(dev_avg):g} stars, {star_words(best_avg - dev_avg)} below your Best XI."))
    for uid, reason, slot, drop in skipped[:2]:
        short = rules["target_minutes"] - info[uid]["month_minutes"]
        text = {"limit": f"{info[uid]['name']} is {short} minutes short, but you already have {rules['max_youth']} under-21 starters (your limit).",
                "position": f"{info[uid]['name']} is {short} minutes short, but has no natural position in this shape.",
                "drop": f"{info[uid]['name']} is {short} minutes short, but would weaken {labels.get(slot, '')} by {star_words(drop)}, more than your rules allow."}[reason]
        why.append(("amb", text))
    return assign, picked, why


def best_why(best: dict, form: dict, depth: dict, info: dict, rules: dict) -> list:
    rate = {k: {r["unique_id"]: r["rating"] for r in v} for k, v in depth.items()}
    labels = {s["key"]: s["label"] for s in form["slots"]}
    why = [("acc", f"Your strongest eleven for this {form['name']}: players in positions they play naturally, ranked by their in-FM ability.")]
    youth = [info[u]["name"] for u in best.values() if u and info[u]["u21"]]
    why.append(("blu", f"Under-21 starters: {', '.join(youth)}." if youth else "No under-21 starters in this lineup."))
    needy = sorted([u for u, i in info.items() if i["u21"] and u not in best.values() and i["month_minutes"] < rules["target_minutes"]], key=lambda u: info[u]["month_minutes"])
    if needy:
        u = needy[0]
        why.append(("amb", f"{info[u]['name']} stays {rules['target_minutes'] - info[u]['month_minutes']} minutes short of his monthly target."))
    weak = weak_spot(best, depth, labels, rate)
    if weak:
        why.append(("amb", f"{weak[0]} is the weakest position in the team ({weak[1]:g} stars)."))
    return why


def weak_spot(assign: dict, depth: dict, labels: dict, rate: dict | None = None):
    rate = rate or {k: {r["unique_id"]: r["rating"] for r in v} for k, v in depth.items()}
    filled = [(rate[k][u], k) for k, u in assign.items() if u]
    if not filled:
        return None
    r, k = min(filled)
    return LABELS_FULL(labels[k]), stars(r)


def LABELS_FULL(pos: str) -> str:  # noqa: N802
    return LABELS.get(pos, pos)
