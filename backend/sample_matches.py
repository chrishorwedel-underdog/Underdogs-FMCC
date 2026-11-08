"""SAMPLE match data shaped like FMMatchLens output (events with pitch coordinates). Coordinates: x 0-100 along the pitch towards the
opponent's goal for the team that made the event, y 0-100 across the pitch."""
import math
import random
from datetime import date, timedelta

import roles

OUR_XY = {}


def _slot_xy(form: dict) -> dict:
    return {s["key"]: (100 - s["y"], s["x"]) for s in form["slots"]}


def _xg(x: float, y: float) -> float:
    dist = math.hypot((100 - x) * 1.05, (y - 50) * 0.68)
    return round(max(0.02, min(0.75, 0.9 * math.exp(-dist / 9.5))), 2)


def _team_events(rng, team, lineup, strength, opp_strength):
    shots, passes, defs, stats = [], [], [], {}
    attackers = [p for p in lineup if p["x"] > 55] or lineup
    for p in lineup:
        stats[p["unique_id"]] = {"unique_id": p["unique_id"], "name": p["name"], "pos": p["pos"], "team": team, "minutes": 90, "goals": 0, "assists": 0,
                                 "xg": 0.0, "xa": 0.0, "shots": 0, "key_passes": 0, "passes": 0, "passes_completed": 0, "prog_passes": 0,
                                 "duels_won": rng.randint(1, 9), "pressures": 0, "def_actions": 0}
    n_shots = max(3, int(rng.gauss(11 + (strength - opp_strength) / 3, 3)))
    for _ in range(n_shots):
        shooter = rng.choice(attackers + attackers + lineup)
        x, y = rng.uniform(72, 98), max(10, min(90, rng.gauss(50, 14)))
        xg = _xg(x, y)
        r = rng.random()
        outcome = "goal" if r < xg else "saved" if r < xg + 0.3 else "blocked" if r < xg + 0.5 else "missed"
        assister = rng.choice([p for p in lineup if p is not shooter]) if rng.random() < 0.7 else None
        shots.append({"team": team, "minute": rng.randint(1, 94), "unique_id": shooter["unique_id"], "player": shooter["name"], "x": round(x, 1), "y": round(y, 1),
                      "xg": xg, "outcome": outcome, "assist_id": assister["unique_id"] if assister else None})
        s = stats[shooter["unique_id"]]
        s["shots"] += 1
        s["xg"] = round(s["xg"] + xg, 2)
        s["goals"] += outcome == "goal"
        if assister:
            a = stats[assister["unique_id"]]
            a["key_passes"] += 1
            a["xa"] = round(a["xa"] + xg, 2)
            a["assists"] += outcome == "goal"
            passes.append({"team": team, "minute": shots[-1]["minute"], "unique_id": assister["unique_id"], "player": assister["name"],
                           "x1": round(max(30, x - rng.uniform(8, 30)), 1), "y1": round(rng.uniform(10, 90), 1), "x2": round(x, 1), "y2": round(y, 1),
                           "completed": True, "progressive": True, "key": True})
    for _ in range(70):
        p = rng.choice(lineup)
        x1, y1 = max(2, min(95, rng.gauss(p["x"], 10))), max(3, min(97, rng.gauss(p["y"], 12)))
        dx = rng.gauss(6, 14)
        x2, y2 = max(1, min(99, x1 + dx)), max(1, min(99, y1 + rng.gauss(0, 18)))
        done = rng.random() < 0.82
        prog = done and x2 - x1 >= 15
        passes.append({"team": team, "minute": rng.randint(1, 94), "unique_id": p["unique_id"], "player": p["name"], "x1": round(x1, 1), "y1": round(y1, 1),
                       "x2": round(x2, 1), "y2": round(y2, 1), "completed": done, "progressive": prog, "key": False})
        s = stats[p["unique_id"]]
        s["passes"] += 1
        s["passes_completed"] += done
        s["prog_passes"] += prog
    for _ in range(40):
        p = rng.choice([q for q in lineup if q["x"] < 75] or lineup)
        kind = rng.choice(["tackle", "interception", "pressure", "pressure", "clearance"])
        defs.append({"team": team, "minute": rng.randint(1, 94), "unique_id": p["unique_id"], "player": p["name"], "type": kind,
                     "x": round(max(2, min(98, rng.gauss(p["x"] - 8, 12))), 1), "y": round(max(2, min(98, rng.gauss(p["y"], 14))), 1)})
        s = stats[p["unique_id"]]
        s["def_actions"] += 1
        s["pressures"] += kind == "pressure"
    for s in stats.values():
        s["rating"] = round(max(4.8, min(10, 6.3 + s["goals"] * 0.9 + s["assists"] * 0.6 + s["xg"] * 0.5 + s["key_passes"] * 0.15
                                          + s["def_actions"] * 0.04 + s["prog_passes"] * 0.05 + rng.uniform(-0.35, 0.35))), 1)
    return shots, passes, defs, list(stats.values())


def _lineup(players, form):
    depth = roles.depth_chart(players, form)
    xi = roles.best_xi(players, form, depth)
    xy = _slot_xy(form)
    by = {p["unique_id"]: p for p in players}
    return [{"unique_id": u, "name": by[u]["name"], "pos": next(s["pos"] for s in form["slots"] if s["key"] == k), "x": xy[k][0], "y": xy[k][1]}
            for k, u in xi.items() if u], roles.strength(xi, depth)


def play_month(save_no: int, game_date: str, club_name: str, players: list, pool: list, opponents: list) -> list:
    form = roles.formation_meta("433")
    ours, our_str = _lineup(players, form)
    gd = date.fromisoformat(game_date)
    out = []
    for m in range(4):
        rng = random.Random(save_no * 100 + m)
        opp = opponents[(save_no * 4 + m) % len(opponents)]
        opp_players = [p for p in pool if p["club"] == opp]
        theirs, their_str = _lineup(opp_players, form) if opp_players else ([], 60)
        s1, p1, d1, st1 = _team_events(rng, "us", ours, our_str, their_str)
        s2, p2, d2, st2 = _team_events(rng, "them", theirs, their_str, our_str)
        shots = sorted(s1 + s2, key=lambda s: s["minute"])
        mom = []
        for b in range(0, 95, 5):
            us = sum(s["xg"] for s in s1 if b <= s["minute"] < b + 5) + sum(0.01 for p in p1 if p["progressive"] and b <= p["minute"] < b + 5)
            them = sum(s["xg"] for s in s2 if b <= s["minute"] < b + 5) + sum(0.01 for p in p2 if p["progressive"] and b <= p["minute"] < b + 5)
            mom.append({"minute": b, "value": round(us - them, 3)})
        out.append({"save_no": save_no, "match_no": m, "date": (gd - timedelta(days=28 - m * 7)).isoformat(), "opponent": opp, "home": m % 2 == 0,
                    "competition": "League", "club_name": club_name,
                    "score": {"us": sum(s["outcome"] == "goal" for s in s1), "them": sum(s["outcome"] == "goal" for s in s2)},
                    "xg": {"us": round(sum(s["xg"] for s in s1), 2), "them": round(sum(s["xg"] for s in s2), 2)},
                    "shots": shots, "passes": p1 + p2, "defensive": d1 + d2, "players": st1 + st2, "momentum": mom,
                    "source": "Sample FMMatchLens data"})
    return out
