"""QoL Phase 2: Scout Players extras (Moneyball, Similar, Youth intake), Loan Manager, depth reorder, weakest-position agreement."""
import os
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"


def _env(key):
    for line in open("/app/backend/.env"):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


@pytest.fixture(scope="module")
def mdb():
    return MongoClient(_env("MONGO_URL"))[_env("DB_NAME")]


@pytest.fixture(scope="module")
def cid(mdb):
    return mdb.settings.find_one({"_id": "app"})["active_career_id"]


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def plan(s):
    r = s.get(f"{API}/squad/plan")
    assert r.status_code == 200
    return r.json()


# --- Moneyball
class TestMoneyball:
    def test_lists(self, s):
        r = s.get(f"{API}/scout/moneyball")
        assert r.status_code == 200
        d = r.json()
        for k in ("bargains", "vfm", "undervalued"):
            assert isinstance(d[k], list) and d[k], k
            for x in d[k]:
                assert "ca" not in x and "pa" not in x and x["own"] is False
                assert x["why"]
        for x in d["bargains"]:
            assert x["fair_price"] >= 1.3 * x["value"]

    def test_no_ca_pa_text(self, s):
        t = s.get(f"{API}/scout/moneyball").text.lower()
        assert '"ca"' not in t and '"pa"' not in t


# --- Similar players
class TestSimilar:
    def test_by_player(self, s):
        r = s.get(f"{API}/scout/moneyball").json()
        uid = r["vfm"][0]["unique_id"]
        r = s.post(f"{API}/scout/similar", json={"unique_id": uid})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["base"]["unique_id"] == uid
        assert d["rows"] and all(row["unique_id"] != uid for row in d["rows"])
        assert all(0 <= row["similarity"] <= 100 for row in d["rows"])

    def test_by_numbers_p90(self, s):
        r = s.post(f"{API}/scout/similar", json={"targets": {"npxg": 0.4, "xa": 0.2}, "mode": "p90"})
        assert r.status_code == 200, r.text
        rows = r.json()["rows"]
        assert rows and set(rows[0]["values"]) == {"npxg", "xa"}
        sims = [x["similarity"] for x in rows]
        assert sims == sorted(sims, reverse=True)

    def test_by_numbers_total_group(self, s):
        r = s.post(f"{API}/scout/similar", json={"targets": {"npxg": 8, "xa": 4}, "mode": "total", "group": "ST"})
        assert r.status_code == 200, r.text
        assert all(x["group"] == "ST" for x in r.json()["rows"])

    def test_no_targets_422(self, s):
        assert s.post(f"{API}/scout/similar", json={"targets": {}}).status_code == 422
        assert s.post(f"{API}/scout/similar", json={"targets": {"bogus": 1}}).status_code == 422

    def test_bad_mode_and_unknown_player(self, s):
        assert s.post(f"{API}/scout/similar", json={"targets": {"npxg": 1}, "mode": "x"}).status_code == 422
        assert s.post(f"{API}/scout/similar", json={"unique_id": 1}).status_code == 404


# --- Youth intake
class TestYouth:
    def test_get_defaults(self, s, mdb, cid):
        c = mdb.careers.find_one({"id": cid}) or {}
        d = s.get(f"{API}/youth-intake").json()
        assert d["rows"]
        if not c.get("youth_intake"):
            on = {r["league"] for r in d["rows"] if r["on"]}
            assert on == {r["league"] for r in d["rows"] if r["league"] in ("Premier League", "LaLiga", "La Liga", "Bundesliga", "Serie A", "Ligue 1")}

    def test_put_toggle_and_date_then_restore(self, s, mdb, cid):
        car = mdb.careers.find_one({"id": cid}) if cid else None
        before = (car or {}).get("youth_intake", "__unset__")
        try:
            r = s.put(f"{API}/youth-intake", json={"league": "Eredivisie", "on": True})
            assert r.status_code == 200
            rows = {x["league"]: x for x in s.get(f"{API}/youth-intake").json()["rows"]}
            assert rows["Eredivisie"]["on"] is True and rows["Serie A"]["on"] is True
            r = s.put(f"{API}/youth-intake", json={"league": "Eredivisie", "mmdd": "04-02"})
            assert r.status_code == 200
            e = {x["league"]: x for x in s.get(f"{API}/youth-intake").json()["rows"]}["Eredivisie"]
            assert e["mmdd"] == "04-02" and e["estimated"] is False and e["date"].endswith("-04-02")
            assert s.put(f"{API}/youth-intake", json={"league": "Eredivisie", "mmdd": "13-01"}).status_code == 422
            assert s.put(f"{API}/youth-intake", json={"league": "Nope League", "on": True}).status_code == 404
        finally:
            if cid:
                if before == "__unset__":
                    mdb.careers.update_one({"id": cid}, {"$unset": {"youth_intake": ""}})
                else:
                    mdb.careers.update_one({"id": cid}, {"$set": {"youth_intake": before}})

    def test_invalid_day_for_month(self, s, mdb, cid):
        """04-31 passes the regex; should be 422, not 500."""
        before = (mdb.careers.find_one({"id": cid}) or {}).get("youth_intake", "__unset__")
        try:
            r = s.put(f"{API}/youth-intake", json={"league": "Eredivisie", "mmdd": "04-31"})
            after = s.get(f"{API}/youth-intake")
            assert after.status_code == 200, f"GET youth-intake broke after saving 04-31: {after.status_code}"
            assert r.status_code == 422, r.status_code
        finally:
            if before == "__unset__":
                mdb.careers.update_one({"id": cid}, {"$unset": {"youth_intake": ""}})
            else:
                mdb.careers.update_one({"id": cid}, {"$set": {"youth_intake": before}})


# --- Loans
class TestLoans:
    def test_clubs(self, s):
        r = s.get(f"{API}/loans/clubs")
        assert r.status_code == 200 and isinstance(r.json(), list) and r.json()

    def test_try_track_untrack(self, s, plan, mdb, cid):
        uid = next(int(u) for u, p in plan["players"].items() if p["age"] < 21)
        club = s.get(f"{API}/loans/clubs").json()[0]
        r = s.post(f"{API}/loans/try", json={"unique_id": uid, "club": club})
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["grade"] in ["A+", "A", "A-", "B+", "B", "B-", "C+", "C", "C-", "D+", "D", "D-", "F"]
        assert d["reason"] and d["rank"] >= 1 and isinstance(d["depth"], list)
        assert d["facilities"] is None
        try:
            assert s.post(f"{API}/loans/track", json={"unique_id": uid, "club": club}).status_code == 200
            rows = s.get(f"{API}/loans").json()["rows"]
            row = next(x for x in rows if x["unique_id"] == uid)
            assert row["club"] == club and row["arrow"] in ("up", "down") and row["tone"] in ("red", "green", "gold")
            assert s.delete(f"{API}/loans/track/{uid}").status_code == 200
            assert all(x["unique_id"] != uid for x in s.get(f"{API}/loans").json()["rows"])
        finally:
            mdb.loans.delete_one({"career_id": cid, "unique_id": uid, "club": club})

    def test_try_errors(self, s, plan):
        club = s.get(f"{API}/loans/clubs").json()[0]
        assert s.post(f"{API}/loans/try", json={"unique_id": 1, "club": club}).status_code == 404
        uid = int(next(iter(plan["players"])))
        assert s.post(f"{API}/loans/try", json={"unique_id": uid, "club": "No Such FC"}).status_code == 404


# --- Depth chart reorder
class TestDepth:
    def test_reorder_and_restore(self, s, plan, mdb, cid):
        f = plan["formation"]["key"]
        slot = next(k for k, v in plan["depth"].items() if len(v) >= 2)
        orig = [r["unique_id"] for r in plan["depth"][slot]]
        new = [orig[1], orig[0]] + orig[2:]
        existed = mdb.depth_orders.find_one({"career_id": cid, "formation": f})
        try:
            r = s.put(f"{API}/squad/depth", json={"formation": f, "slot": slot, "order": new})
            assert r.status_code == 200
            p = s.get(f"{API}/squad/plan", params={"formation": f}).json()
            assert [r["unique_id"] for r in p["depth"][slot]] == new
            assert slot in p["depth_custom"]
            assert s.put(f"{API}/squad/depth", json={"formation": f, "slot": slot, "order": new[:1]}).status_code == 422
            assert s.put(f"{API}/squad/depth", json={"formation": f, "slot": "ZZ", "order": new}).status_code == 422
            # weakest position must not change because of a custom order
            assert p["weak_spot"][0] == plan["weak_spot"][0]
            assert s.get(f"{API}/home").json()["squad"]["weak_spot"] == plan["weak_spot"][0]
        finally:
            if existed:
                mdb.depth_orders.replace_one({"_id": existed["_id"]}, existed)
            else:
                mdb.depth_orders.delete_one({"career_id": cid, "formation": f})


# --- Weakest position agreement
class TestWeakest:
    def test_agree(self, s, plan):
        w = plan["weak_spot"][0]
        home = s.get(f"{API}/home").json()
        assert home["squad"]["weak_spot"] == w
        att = [a for a in home.get("attention", []) if a.get("kind") == "weak"]
        assert att and att[0]["text"].startswith(f"{w} is your weakest position")
        todo = s.get(f"{API}/analysis/club").json()["todo"]
        first = next(t for t in todo if t["title"].startswith("Weakest area"))
        assert w in first["evidence"]
