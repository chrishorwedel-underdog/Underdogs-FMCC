# Iteration 48: odd player rows must not break Breakout/Elite/DP/Scout; NG_Regens find/choose; Seed note; Defaults; DOF key; club-logo
import os
import sys
import asyncio
import pytest
import requests
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")
BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
CID = "72f82391-d58c-41f7-bc47-6a46cfd10a55"
mdb = MongoClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "test_database")]

SNAP_ODD = [
    {"unique_id": 99990001, "name": "TEST_Odd One", "positions": "D/WB (R)", "nationality": None, "age": "x", "club": None, "minutes": None, "attributes": None, "ca": 100, "pa": 130},
    {"unique_id": 99990002, "name": "TEST_Odd Two", "positions": ["AM (RLC)"], "age": 20, "ca": None, "pa": None, "minutes": 500},
    {"unique_id": 99990003, "name": None, "positions": [], "nationality": "Spain", "age": 22, "ca": 90, "pa": 120, "minutes": 900, "attributes": {"pace": "x"}},
    {"unique_id": 99990004, "name": "TEST_Odd Four", "positions": None, "nationality": "England", "age": 19, "ca": 80, "pa": 140, "minutes": 1200, "attributes": {}},
]
POOL_ODD = [
    {"unique_id": 99991001, "name": "TEST_Pool One", "positions": "D/WB (R)", "nationality": None, "age": "x", "club": None, "league": None, "minutes": None, "attributes": None, "ca": 100, "pa": 130, "gender": "M"},
    {"unique_id": 99991002, "name": "TEST_Pool Two", "positions": ["AM (RLC)"], "age": 24, "club": "Northbridge Athletic", "league": "Premier Division", "ca": None, "minutes": 2000, "gender": "M"},
    {"unique_id": 99991003, "name": "TEST_Pool Three", "positions": [], "nationality": "Spain", "age": 22, "club": "Northbridge Athletic", "league": "Premier Division", "ca": 90, "pa": 120, "minutes": 1500, "attributes": {"pace": "x"}},
    {"unique_id": 99991004, "name": "TEST_Pool Four", "positions": None, "nationality": "Italy", "age": 30, "ca": 120, "pa": 125, "minutes": 3000, "gender": "M"},
]
if os.environ.get("ODD_MODE") == "spec":
    # exactly the review spec: every key present, odd values only
    base = {"ca": 100, "pa": 130, "appearances": 5, "goals": 0, "assists": 0, "gender": "M", "league": "Premier Division", "value": 1000, "wage": 100}
    SNAP_ODD = [base | {"unique_id": 99990001, "name": "TEST_Odd One", "positions": ["D/WB (R)"], "nationality": None, "age": 20, "club": "TEST FC", "minutes": 900, "attributes": {"pace": 10}},
                base | {"unique_id": 99990002, "name": "TEST_Odd Two", "positions": ["AM (RLC)"], "nationality": "Spain", "age": "x", "club": None, "minutes": None, "attributes": None},
                base | {"unique_id": 99990003, "name": "TEST_Odd Three", "positions": [], "nationality": "Spain", "age": 21, "club": "TEST FC", "minutes": 600, "attributes": {}},
                base | {"unique_id": 99990004, "name": "TEST_Odd Four", "positions": None, "nationality": "England", "age": 19, "club": "TEST FC", "minutes": 1200, "attributes": None}]
    POOL_ODD = [dict(p, unique_id=p["unique_id"] + 1000, club=p["club"] and "Northbridge Athletic") for p in SNAP_ODD]
    if os.environ.get("ODD_LEAGUE_NULL"):
        POOL_ODD[1]["league"] = None
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


# ---------- player_clean unit ----------
class TestNormPositions:
    def test_cases(self):
        from player_clean import norm_positions, clean_player
        assert norm_positions("D/WB (R)") == ["D (R)", "WB (R)"]
        assert set(norm_positions("AM (RLC)")) == {"AM (R)", "AM (L)", "AM (C)"}
        assert norm_positions("M/AM (C)") == ["M (C)", "AM (C)"]
        assert norm_positions("ST (C)") == ["ST"]
        assert norm_positions("") == [] and norm_positions(None) == []
        q = clean_player(SNAP_ODD[0])
        assert q["age"] is None and q["nationality"] == "" and q["club"] == "" and q["minutes"] == 0 and q["attributes"] == {}


# ---------- odd rows: pages must still answer ----------
class TestOddPlayers:
    @pytest.mark.parametrize("path", ["/api/breakout", "/api/elite", "/api/dp", "/api/dp/preview", "/api/dp/scope", "/api/dp/review", "/api/dp/records", "/api/scout/meta"])
    def test_get_200(self, api, odd_rows, path):
        r = api.get(f"{BASE_URL}{path}")
        assert r.status_code == 200, f"{path} -> {r.status_code} {r.text[:300]}"

    def test_breakout_check_note(self, api, odd_rows):
        d = api.get(f"{BASE_URL}/api/breakout").json()
        assert "check_note" in d and d["check_note"] is None

    def test_scout_players(self, api, odd_rows):
        r = api.post(f"{BASE_URL}/api/scout/players", json={})
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["total"] > 0 and "left_out" in d

    def test_scout_similar(self, api, odd_rows):
        rows = api.post(f"{BASE_URL}/api/scout/players", json={}).json()["rows"]
        r = api.post(f"{BASE_URL}/api/scout/similar", json={"unique_id": rows[0]["unique_id"]})
        assert r.status_code == 200, r.text[:300]
        r2 = api.post(f"{BASE_URL}/api/scout/similar", json={"unique_id": 99991001})
        assert r2.status_code in (200, 404), r2.text[:300]

    def test_population_all_players_scope(self, odd_rows):
        """DP scope 'all players / nations / leagues' reads the raw pool."""
        import importlib
        import core
        importlib.reload(core) if False else None
        import population
        from motor.motor_asyncio import AsyncIOMotorClient

        async def run():
            core.db = AsyncIOMotorClient(os.environ.get("MONGO_URL", "mongodb://localhost:27017"))[os.environ.get("DB_NAME", "test_database")]
            population.db = core.db
            c = await core.db.careers.find_one({"id": CID}, {"_id": 0})
            return await population.contexts(c, {"my_club": True, "all_players": True, "nations": [], "leagues": []})
        out = asyncio.run(run())
        assert len(out) > 0


# ---------- NG_Regens ----------
class TestNg:
    def test_find_and_choose(self, api):
        before = mdb.careers.find_one({"id": CID}, {"_id": 0, "ng_folder": 1})
        try:
            r = api.post(f"{BASE_URL}/api/editor/ng/find")
            assert r.status_code == 200
            d = r.json()
            assert d["found"] is True and d["folder"]
            assert mdb.careers.find_one({"id": CID})["ng_folder"] == d["folder"]
            r = api.post(f"{BASE_URL}/api/editor/ng/choose", json={"folder": "/nope/TEST_missing"})
            assert r.status_code == 404 and "isn't there" in r.json()["detail"]
            os.makedirs("/tmp/TEST_empty_ng", exist_ok=True)
            r = api.post(f"{BASE_URL}/api/editor/ng/choose", json={"folder": "/tmp/TEST_empty_ng"})
            assert r.status_code == 422 and "NG_Regens" in r.json()["detail"]
        finally:
            if not (before or {}).get("ng_folder"):
                mdb.careers.update_one({"id": CID}, {"$unset": {"ng_folder": ""}})


# ---------- Seed a Surname current mode ----------
class TestSeed:
    def test_create_current_note(self, api):
        old = mdb.seed_drafts.find_one({"career_id": CID})
        try:
            body = {"surname": "Testzorvak", "mode": "current", "players": {"ST": 1, "GK": 1}, "staff": {}, "nations": [{"nation": "Spain", "count": 2}]}
            r = api.post(f"{BASE_URL}/api/seed/create", json=body)
            if r.status_code == 422:
                pytest.fail(f"Body invalid: {r.text[:400]}")
            assert r.status_code in (200, 409), r.text[:300]
            note = r.json().get("note") if r.status_code == 200 else r.json().get("detail")
            print("SEED NOTE:", note)
            assert note and note.startswith("Chose from ") and "low-profile players and" in note
        finally:
            if old:
                mdb.seed_drafts.replace_one({"_id": old["_id"]}, old, upsert=True)
            else:
                mdb.seed_drafts.delete_one({"career_id": CID})


# ---------- Defaults for new games ----------
class TestDefaults:
    def test_flow(self, api):
        d = api.get(f"{BASE_URL}/api/defaults").json()
        assert [a["key"] for a in d["areas"]] == ["punish", "seed", "features", "appearance", "rules"]
        pre = next(a for a in d["areas"] if a["key"] == "features")["saved"]
        assert api.post(f"{BASE_URL}/api/defaults/features/save", json={}).status_code == 200
        d = api.get(f"{BASE_URL}/api/defaults").json()
        assert next(a for a in d["areas"] if a["key"] == "features")["saved"] is True
        assert api.post(f"{BASE_URL}/api/defaults/nope/save", json={}).status_code == 404
        if not pre:
            assert api.delete(f"{BASE_URL}/api/defaults/features").status_code == 200
            d = api.get(f"{BASE_URL}/api/defaults").json()
            assert next(a for a in d["areas"] if a["key"] == "features")["saved"] is False


# ---------- DOF key + club logo ----------
class TestDofLogo:
    def test_dof_status(self, api):
        d = api.get(f"{BASE_URL}/api/dof/status").json()
        assert d.get("model_label") and d.get("ready") is True

    def test_check_key(self, api):
        r = api.post(f"{BASE_URL}/api/setup/check-key", json={}, timeout=120)
        assert r.status_code == 200, r.text[:300]
        d = r.json()
        assert d["ok"] is True and d["model_label"]

    def test_club_logo_404(self, api):
        r = api.get(f"{BASE_URL}/api/club-logo", params={"career": CID})
        assert r.status_code == 404
