# Iteration 49: worst-mode odd player rows (snapshot + pool) must not break Breakout/Elite/DP/Scout/Home/Squad
import os
import sys
import asyncio
import pytest
import requests
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
CID = "72f82391-d58c-41f7-bc47-6a46cfd10a55"
mdb = MongoClient(os.environ.get("MONGO_URL"))[os.environ.get("DB_NAME")]

# Mixed worst mode: missing keys, spec odd values, league null, no league key, nationality null
BASE = {"ca": 100, "pa": 130, "appearances": 5, "goals": 0, "assists": 0, "gender": "M", "league": "Premier Division", "value": 1000, "wage": 100}
SNAP_ODD = [
    {"unique_id": 99990001, "name": "TEST_Odd One", "positions": "D/WB (R)", "nationality": None, "age": "x", "club": None, "minutes": None, "attributes": None, "ca": 100, "pa": 130},
    {"unique_id": 99990002, "name": "TEST_Odd Two", "positions": ["AM (RLC)"], "age": 20, "ca": None, "pa": None, "minutes": 500},
    {"unique_id": 99990003, "name": None, "positions": [], "nationality": "Spain", "age": 22, "ca": 90, "pa": 120, "minutes": 900, "attributes": {"pace": "x"}},
    {"unique_id": 99990004, "name": "TEST_Odd Four", "positions": None, "nationality": "England", "age": 19, "ca": 80, "pa": 140, "minutes": 1200, "attributes": {}},
    BASE | {"unique_id": 99990005, "name": "TEST_Odd Five", "positions": ["D/WB (R)"], "nationality": None, "age": 20, "club": "TEST FC", "minutes": 900, "attributes": {"pace": 10}},
    BASE | {"unique_id": 99990006, "name": "TEST_Odd Six", "positions": ["AM (RLC)"], "nationality": "Spain", "age": "x", "club": None, "minutes": None, "attributes": None, "league": None},
    BASE | {"unique_id": 99990007, "name": "TEST_Odd Seven", "positions": [], "nationality": "Spain", "age": None, "club": "TEST FC", "minutes": 600, "attributes": {}},
]
POOL_ODD = [
    {"unique_id": 99991001, "name": "TEST_Pool One", "positions": "D/WB (R)", "nationality": None, "age": "x", "club": None, "league": None, "minutes": None, "attributes": None, "ca": 100, "pa": 130, "gender": "M"},
    {"unique_id": 99991002, "name": "TEST_Pool Two", "positions": ["AM (RLC)"], "age": 24, "club": "Northbridge Athletic", "league": "Premier Division", "ca": None, "minutes": 2000, "gender": "M"},
    {"unique_id": 99991003, "name": "TEST_Pool Three", "positions": [], "nationality": "Spain", "age": 22, "club": "Northbridge Athletic", "league": "Premier Division", "ca": 90, "pa": 120, "minutes": 1500, "attributes": {"pace": "x"}},
    {"unique_id": 99991004, "name": "TEST_Pool Four", "positions": None, "nationality": "Italy", "age": 30, "ca": 120, "pa": 125, "minutes": 3000, "gender": "M"},
    BASE | {"unique_id": 99991005, "name": "TEST_Pool Five", "positions": ["D/WB (R)"], "nationality": None, "age": 20, "club": "Northbridge Athletic", "minutes": 900, "attributes": {"pace": 10}},
    BASE | {"unique_id": 99991006, "name": "TEST_Pool Six", "positions": ["AM (RLC)"], "nationality": "Spain", "age": "x", "club": None, "minutes": None, "attributes": None, "league": None},
    {"unique_id": 99991007, "name": "TEST_Pool Seven", "positions": None, "nationality": None, "age": None, "club": None, "minutes": None, "attributes": None},
    {"unique_id": 99991008, "name": "TEST_Pool Eight", "positions": "M (C)", "nationality": "France", "age": 18, "club": "Elsewhere FC", "league": None, "ca": 70, "pa": 150, "minutes": 100, "gender": "M"},
]
SNAP_IDS = [p["unique_id"] for p in SNAP_ODD]
POOL_IDS = [p["unique_id"] for p in POOL_ODD]


@pytest.fixture(scope="module")
def api():
    s = requests.Session()
    s.headers.update({"Content-Type": "application/json"})
    return s


@pytest.fixture(scope="module")
def odd_rows():
    snap = mdb.snapshots.find_one({"career_id": CID}, {"_id": 1, "save_no": 1}, sort=[("save_no", -1)])
    mdb.snapshots.update_one({"_id": snap["_id"]}, {"$push": {"players": {"$each": SNAP_ODD}}})
    mdb.pools.update_one({"career_id": CID}, {"$push": {"players": {"$each": POOL_ODD}}})
    yield snap
    mdb.snapshots.update_one({"_id": snap["_id"]}, {"$pull": {"players": {"unique_id": {"$in": SNAP_IDS}}}})
    mdb.pools.update_one({"career_id": CID}, {"$pull": {"players": {"unique_id": {"$in": POOL_IDS}}}})


class TestClean:
    def test_clean_league(self):
        from player_clean import clean_player
        q = clean_player(POOL_ODD[6])
        assert q["league"] == "" and q["nationality"] == "" and q["age"] is None and q["positions"] == []


class TestOddWorst:
    @pytest.mark.parametrize("path", ["/api/breakout", "/api/elite", "/api/dp", "/api/dp/preview", "/api/dp/scope",
                                      "/api/dp/review", "/api/dp/records", "/api/scout/meta", "/api/home", "/api/home/extras",
                                      "/api/squad", "/api/development", "/api/players"])
    def test_get_200(self, api, odd_rows, path):
        r = api.get(f"{BASE_URL}{path}", timeout=60)
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:300]}"

    def test_breakout_content(self, api, odd_rows):
        d = api.get(f"{BASE_URL}/api/breakout", timeout=60).json()
        assert d.get("check_note") is None

    def test_scout_players(self, api, odd_rows):
        r = api.post(f"{BASE_URL}/api/scout/players", json={}, timeout=60)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["total"] > 0 and "left_out" in d

    def test_scout_players_max_age(self, api, odd_rows):
        r = api.post(f"{BASE_URL}/api/scout/players", json={"max_age": 21, "min_age": 16}, timeout=60)
        assert r.status_code in (200, 422), r.text[:300]
        assert r.status_code == 200, r.text[:300]

    def test_scout_similar(self, api, odd_rows):
        rows = api.post(f"{BASE_URL}/api/scout/players", json={}, timeout=60).json()["rows"]
        r = api.post(f"{BASE_URL}/api/scout/similar", json={"unique_id": rows[0]["unique_id"]}, timeout=60)
        assert r.status_code == 200, r.text[:300]
        for uid in (99991001, 99991006, 99991007):
            r2 = api.post(f"{BASE_URL}/api/scout/similar", json={"unique_id": uid, "max_age": 25}, timeout=60)
            assert r2.status_code in (200, 404), f"{uid}: {r2.status_code} {r2.text[:300]}"

    def test_population_contexts(self, odd_rows):
        import core
        import population
        from motor.motor_asyncio import AsyncIOMotorClient

        async def run():
            core.db = AsyncIOMotorClient(os.environ.get("MONGO_URL"))[os.environ.get("DB_NAME")]
            population.db = core.db
            c = await core.db.careers.find_one({"id": CID}, {"_id": 0})
            return await population.contexts(c, {"my_club": True, "all_players": True, "nations": ["Spain"], "leagues": ["Premier Division"]})
        out = asyncio.run(run())
        assert len(out) > 0

