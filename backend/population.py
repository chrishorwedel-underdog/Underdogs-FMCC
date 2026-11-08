"""Builds the evidence each rule can look at, for your squad and (for Dynamic Potential) players at other clubs."""
from core import db, latest_snapshot, season_start_ca
from sample_reader import GROUP


def _ctx(p: dict, club: str, league: str, start_ca) -> dict:
    return {"unique_id": p["unique_id"], "name": p["name"], "age": p["age"], "minutes": p.get("minutes", 0), "appearances": p.get("appearances", 0),
            "avg_rating": p.get("avg_rating"), "goals": p.get("goals", 0), "assists": p.get("assists", 0), "ca": p["ca"], "pa": p["pa"],
            "ca_growth": p["ca"] - start_ca if start_ca is not None else 0, "training_rating": p.get("training_rating"),
            "position": GROUP[p["positions"][0]], "nationality": p["nationality"], "club": club, "league": league}


async def own_contexts(career: dict) -> list:
    snap = await latest_snapshot(career["id"])
    start = await season_start_ca(career["id"], snap["season"])
    return [_ctx(p, career["club_name"], "My league", start.get(p["unique_id"])) for p in snap["players"]]


async def contexts(career: dict, scope: dict) -> list:
    """Every covered player once, even when several toggles cover him."""
    out = {}
    if scope.get("my_club", True):
        for x in await own_contexts(career):
            out[x["unique_id"]] = x
    nations, leagues = set(scope.get("nations") or []), set(scope.get("leagues") or [])
    if nations or leagues:
        pool = await db.pools.find_one({"career_id": career["id"]}, {"_id": 0}) or {"players": [], "season_start_ca": {}}
        for p in pool["players"]:
            if p["league"] in leagues or p["nationality"] in nations:
                out.setdefault(p["unique_id"], _ctx(p, p["club"], p["league"], pool["season_start_ca"].get(str(p["unique_id"]))))
    return list(out.values())
