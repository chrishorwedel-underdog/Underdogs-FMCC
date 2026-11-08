from datetime import date

SLOTS = [  # 4-3-3: slot key, label, accepted positions
    ("GK", "Goalkeeper", ["GK"]), ("DL", "Left Back", ["D (L)", "WB (L)"]),
    ("DC1", "Centre Back", ["D (C)"]), ("DC2", "Centre Back", ["D (C)"]),
    ("DR", "Right Back", ["D (R)", "WB (R)"]), ("DM", "Defensive Midfield", ["DM"]),
    ("MC1", "Central Midfield", ["M (C)"]), ("MC2", "Central Midfield", ["M (C)", "AM (C)"]),
    ("AML", "Left Wing", ["AM (L)"]), ("AMR", "Right Wing", ["AM (R)"]), ("ST", "Striker", ["ST"]),
]
MONTHLY_TARGET = 270


def best_xi(players: list) -> list:
    used, xi = set(), []
    for key, label, pos in sorted(SLOTS, key=lambda s: sum(1 for p in players if set(p["positions"]) & set(s[2]))):
        options = [p for p in players if p["unique_id"] not in used and set(p["positions"]) & set(pos)]
        pick = max(options, key=lambda p: p["ca"], default=None)
        if pick:
            used.add(pick["unique_id"])
        xi.append({"slot": key, "label": label, "player": pick})
    return xi


def _by_id(snap):
    return {p["unique_id"]: p for p in snap["players"]} if snap else {}


def compute(latest: dict, prev: dict | None, last_backup: str | None) -> dict:
    players = latest["players"]
    gd = date.fromisoformat(latest["game_date"])
    before = _by_id(prev)
    xi = best_xi(players)
    filled = [s for s in xi if s["player"]]
    xi_avg = round(sum(s["player"]["ca"] for s in filled) / max(1, len(filled)))
    weak = min(filled, key=lambda s: s["player"]["ca"]) if filled else None

    youth = []
    for p in players:
        if p["age"] >= 21:
            continue
        last_month = p["minutes"] - before[p["unique_id"]]["minutes"] if p["unique_id"] in before and before[p["unique_id"]]["minutes"] <= p["minutes"] else p["minutes"]
        youth.append({"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "minutes": last_month})
    needy = sorted([y for y in youth if y["minutes"] < MONTHLY_TARGET], key=lambda y: y["minutes"])

    deltas = [(p, p["ca"] - before[p["unique_id"]]["ca"]) for p in players if p["unique_id"] in before]
    total = sum(d for _, d in deltas)
    riser = max(deltas, key=lambda x: x[1], default=None)

    expiring = [p for p in players if (date.fromisoformat(p["contract_end"]) - gd).days <= 183]
    season_end = date(gd.year if gd.month < 7 else gd.year + 1, 5, 31)
    weeks_left = max(0, (season_end - gd).days // 7)

    attention = []
    for y in needy[:2]:
        attention.append({"kind": "minutes", "tone": "amb", "unique_id": y["unique_id"],
                          "text": f"{y['name']}, {y['age']}, played {y['minutes']} of {MONTHLY_TARGET} target minutes last month.",
                          "sub": "Under-21s need regular minutes to develop."})
    for p in expiring[:2]:
        attention.append({"kind": "contract", "tone": "blu", "unique_id": p["unique_id"],
                          "text": f"{p['name']}'s contract ends on {p['contract_end']}.",
                          "sub": "Decide whether to renew or sell before it runs out."})
    if weak:
        attention.append({"kind": "weak", "tone": "acc", "unique_id": weak["player"]["unique_id"],
                          "text": f"{weak['label']} is your weakest position in the Best XI.",
                          "sub": f"{weak['player']['name']} is the best option there (ability {weak['player']['ca']})."})

    return {
        "game_date": latest["game_date"], "season": latest["season"], "club_name": latest["club_name"],
        "squad_size": len(players), "next_fixture": latest.get("next_fixture"), "last_backup": last_backup,
        "has_previous": prev is not None,
        "squad": {"xi_average": xi_avg, "weak_spot": weak["label"] if weak else None},
        "development": {"count": len(needy), "target": MONTHLY_TARGET, "players": needy[:3]},
        "report": {"total_change": total, "riser": {"name": riser[0]["name"], "change": riser[1]} if riser else None},
        "awards": {"weeks_left": weeks_left, "season_end": season_end.isoformat()},
        "attention": attention,
    }
