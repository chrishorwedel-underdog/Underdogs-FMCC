# Iteration 24: Seed a Surname 4-step page backend contract + Dynamic Potential "all loaded players" scope.
# Run with -n 0. Restores DP scope to my_club=True, all_players=False and clears the seed draft it creates.
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
S = requests.Session()


def dp():
    r = S.get(f"{BASE_URL}/api/dp")
    assert r.status_code == 200
    return r.json()


def put_scope(scope):
    d = dp()
    r = S.put(f"{BASE_URL}/api/dp/scope", json={"scope": scope, "expected_version": d["version"]})
    return r


# ---- Dynamic Potential all_players ----
class TestDPAllPlayers:
    def test_all_players_on_covers_everyone(self):
        base = dp()
        assert "all_players" in base["scope"] or base["scope"].get("all_players") is None
        orig = base["scope"]
        try:
            # my-club-only covered count
            r = put_scope({"my_club": True, "all_players": False, "nations": [], "leagues": []})
            assert r.status_code == 200
            own = dp()["covered"]
            pool_total = sum(l["count"] for l in dp()["leagues"])
            r = put_scope({"my_club": False, "all_players": True, "nations": [], "leagues": []})
            assert r.status_code == 200, r.text
            d = dp()
            assert d["scope"]["all_players"] is True
            assert d["covered"] == own + pool_total, (d["covered"], own, pool_total)
            # review lists everyone
            rv = S.get(f"{BASE_URL}/api/dp/review").json()
            n = sum(len(c["players"]) for lg in rv for c in lg["clubs"])
            assert n == d["covered"]
            # off restores
            r = put_scope({"my_club": True, "all_players": False, "nations": [], "leagues": []})
            assert r.status_code == 200
            d2 = dp()
            assert d2["scope"]["all_players"] is False and d2["covered"] == own
        finally:
            put_scope({"my_club": True, "all_players": False, "nations": orig.get("nations", []), "leagues": orig.get("leagues", [])})

    def test_stale_version_409(self):
        r = S.put(f"{BASE_URL}/api/dp/scope", json={"scope": {"all_players": True}, "expected_version": -5})
        assert r.status_code == 409

    def test_bad_type_422(self):
        r = S.put(f"{BASE_URL}/api/dp/scope", json={"scope": {"all_players": "yes please"}, "expected_version": dp()["version"]})
        assert r.status_code == 422


# ---- Seed create: total = players + staff, payload as the 4-step UI builds it ----
POS = {"GK": 1, "DC": 2, "DL": 1, "DR": 1, "DM": 1, "MC": 1, "AML": 1, "AMR": 1, "ST": 1}  # 10
STAFF = {"First-Team Coach": 1, "Scout": 2}  # 3


def body(mode, nations):
    return {"surname": "Testseed", "mode": mode, "players": POS, "staff": STAFF, "nations": nations,
            "player_ages": {"young": 2, "prime": 2, "experienced": 1, "youth": 1, "veteran": 1},
            "staff_ages": {"early": 1, "established": 2, "senior": 2, "veteran": 1}, "seed": 4242,
            "ca_lo": 30, "ca_hi": 60, "pa_lo": 60, "pa_hi": 100}


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    d = S.get(f"{BASE_URL}/api/seed/draft").json()
    for p in (d or {}).get("people", []):
        S.delete(f"{BASE_URL}/api/seed/draft/{p['pid']}")


class TestSeedCreate:
    def test_new_mode_total_and_nation_counts(self):
        r = S.post(f"{BASE_URL}/api/seed/create", json=body("new", [{"nation": "England", "count": 8}, {"nation": "France", "count": 5}]))
        assert r.status_code == 200, r.text
        ppl = r.json()["people"]
        assert len(ppl) == 13
        assert sum(p["kind"] == "player" for p in ppl) == 10 and sum(p["kind"] == "staff" for p in ppl) == 3
        assert sum(p["nationality"] == "England" for p in ppl) == 8
        assert all(p["last_name"] == "Testseed" and p["ca"] <= 60 and p["pa"] <= 100 for p in ppl)

    def test_nation_mismatch_422(self):
        r = S.post(f"{BASE_URL}/api/seed/create", json=body("new", [{"nation": "England", "count": 12}]))
        assert r.status_code == 422

    def test_current_mode_at_most_total(self):
        r = S.post(f"{BASE_URL}/api/seed/create", json=body("current", [{"nation": "England", "count": 13}]))
        assert r.status_code == 200, r.text
        d = r.json()
        assert 1 <= len(d["people"]) <= 13
        if len(d["people"]) < 13:
            assert d["note"]
        assert all(p["club"] != "TEST FC" for p in d["people"])

    def test_large_100_players(self):
        b = body("new", [{"nation": "England", "count": 120}])
        b["players"] = {"GK": 9, "DC": 18, "DL": 9, "DR": 9, "DM": 9, "MC": 13, "AML": 9, "AMR": 9, "AMC": 9, "ST": 6}
        b["staff"] = {"Scout": 20}
        r = S.post(f"{BASE_URL}/api/seed/create", json=b)
        assert r.status_code == 200, r.text
        assert len(r.json()["people"]) == 120
