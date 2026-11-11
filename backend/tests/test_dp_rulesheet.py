# Dynamic Potential rulesheet: engine unit checks + /api/dp API (settings, season, reviews, records, decide, scope)
import os
import sys
import json
import pytest
import requests

sys.path.insert(0, "/app/backend")
import dp_engine as E  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api/dp"
S = requests.Session()
STATE = {}


def _no_secret_keys(obj, path="$"):
    bad = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in ("ca", "pa", "ca_growth"):
                bad.append(f"{path}.{k}")
            bad += _no_secret_keys(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            bad += _no_secret_keys(v, f"{path}[{i}]")
    return bad


# Engine pure-function checks
class TestEngine:
    def test_tapers(self):
        s = E.defaults()
        assert E.growth_taper(174, 12, s) == 6
        assert [E.decline_taper(p, 5, s) for p in (140, 130, 120, 110, 100, 95)] == [5, 4, 3, 2, 1, 0]

    def test_bands_age(self):
        s = E.defaults()
        assert E.base_change(97, s) == 12 and E.base_change(64.9, s) == 0 and E.base_change(29.9, s) == -1 and E.base_change(0, s) == -5
        assert [E.age_deduction(a, s) for a in (24, 25, 26, 30, 33, 36)] == [0, 0, 1, 5, 8, 8]
        assert E.validate(E.defaults()) == []

    def test_assess_examples(self):
        s = E.defaults()
        sc = {"score": 91, "rating_pct": 91, "role_pct": 91, "ratings_only": False, "provisional": False, "groups_used": ["A", "B"]}
        ev = dict(minutes=1500, senior_minutes=1500, youth_minutes=0, senior_share=100, halves_known=True, h1=750, h2=750, h1_rating_pct=90, h2_rating_pct=90, age=22)
        r = E.assess({"pa": 150, "ca": 120}, sc, ev, s, "season_end", 0, 0, 30)
        assert r["change"] == 8 and r["tier"] == "Excellent"
        w = E.assess({"pa": 150, "ca": 120}, sc, dict(ev, minutes=800, senior_minutes=800), s, "winter", 0, 0, 30)
        assert w["change"] == 4
        st = E.assess({"pa": 152, "ca": 120}, dict(sc, score=83, rating_pct=83, role_pct=83), ev, s, "season_end", 2, 2, 30)
        assert st["change"] == 4


# API flow (sequential, shared state)
class TestDPApi:
    def test_01_overview(self):
        r = S.get(API)
        assert r.status_code == 200
        o = r.json()
        for k in ("season", "winter_date", "stage", "counts", "next_review"):
            assert k in o
        STATE["season"] = o["season"]
        STATE["orig_winter"] = o["winter_date"]
        assert set(o["counts"]) == {"rising", "falling", "steady", "held", "review"}

    def test_02_settings_get_and_validation(self):
        r = S.get(f"{API}/settings")
        assert r.status_code == 200
        d = r.json()
        assert d["data"]["score"]["rating_weight"] == 55 and "history" in d and "defaults" in d
        STATE["v0"] = d["version"]
        bad = json.loads(json.dumps(d["data"]))
        bad["score"]["rating_weight"] = 60
        r = S.put(f"{API}/settings", json={"data": bad})
        assert r.status_code == 422, r.text

    def test_03_settings_malformed_is_422_not_500(self):
        bad = E.defaults()
        bad["bands"] = []
        r = S.put(f"{API}/settings", json={"data": bad})
        assert r.status_code == 422, f"got {r.status_code}: {r.text[:200]}"

    def test_04_settings_save_reset_restore(self):
        d = E.defaults()
        d["bands"][0][1] = 11
        d["winter"]["max"] = 3
        r = S.put(f"{API}/settings", json={"data": d, "note": "TEST_edit"})
        assert r.status_code == 200, r.text
        v_edit = r.json()["version"]
        assert set(r.json()["changed"]) == {"bands", "winter"}
        r = S.post(f"{API}/settings/reset", params={"section": "bands"})
        assert r.status_code == 200 and r.json()["changed"] == ["winter"]
        r = S.post(f"{API}/settings/reset", params={"section": "nope"})
        assert r.status_code == 404
        r = S.post(f"{API}/settings/restore/{v_edit}")
        assert r.status_code == 200 and set(r.json()["changed"]) == {"bands", "winter"}
        g = S.get(f"{API}/settings").json()
        assert g["data"]["bands"][0][1] == 11
        r = S.post(f"{API}/settings/restore/99999")
        assert r.status_code == 404
        r = S.post(f"{API}/settings/reset")
        assert r.status_code == 200 and r.json()["changed"] == []
        assert S.get(f"{API}/settings").json()["changed"] == []

    def test_05_season_put_before_review(self):
        r = S.put(f"{API}/season", json={"winter_date": "2028-01-02"})
        assert r.status_code == 200
        assert S.get(API).json()["winter_date"] == "2028-01-02"
        # the sample save is dated 2028-01-01; a winter date before it lets the season-end review run in this test
        r = S.put(f"{API}/season", json={"winter_date": "2027-12-01"})
        assert r.status_code == 200

    def test_06_winter_review(self):
        r = S.post(f"{API}/review/winter", json={})
        assert r.status_code == 200, r.text
        d = r.json()
        STATE["winter_reviewed"] = d["reviewed"]
        assert d["reviewed"] > 0
        o = S.get(API).json()
        assert o["stage"] == "winter_done" and o["next_review"] == "season_end"
        assert o["reviewed"]["winter"] == d["reviewed"]

    def test_07_winter_rerun_no_duplicate(self):
        r = S.post(f"{API}/review/winter", json={})
        assert r.status_code == 200 and r.json()["reviewed"] == 0
        assert S.get(API).json()["reviewed"]["winter"] == STATE["winter_reviewed"]

    def test_08_season_put_409_after_review(self):
        r = S.put(f"{API}/season", json={"winter_date": "2028-01-03"})
        assert r.status_code == 409

    def test_09_records_no_ca_pa(self):
        r = S.get(f"{API}/records")
        assert r.status_code == 200
        recs = r.json()
        assert recs
        assert _no_secret_keys(recs) == []
        STATE["records"] = recs
        uid = recs[0]["unique_id"]
        r = S.get(f"{API}/records/{uid}")
        assert r.status_code == 200 and _no_secret_keys(r.json()) == []
        assert S.get(f"{API}/records/1").status_code == 404
        print("statuses", {x["status"] for x in recs})

    def test_10_again_revision(self):
        before = {r["unique_id"]: r for r in S.get(f"{API}/records", params={"kind": "winter"}).json()}
        r = S.post(f"{API}/review/winter", json={"again": True})
        assert r.status_code == 200
        assert r.json()["applied"]["queued"] == 0, "again must not re-apply already applied changes"
        after = {r["unique_id"]: r for r in S.get(f"{API}/records", params={"kind": "winter"}).json()}
        for uid, b in before.items():
            assert after[uid]["revision"] == b["revision"] + 1
            if b["status"] in ("auto", "approved") and b["change"]:
                assert after[uid]["change"] == b["change"] and after[uid]["status"] == b["status"]

    def test_11_decide(self):
        recs = S.get(f"{API}/records", params={"kind": "winter"}).json()
        nr = [r for r in recs if r["status"] == "needs_review"]
        if not nr:
            pytest.skip("no needs_review records")
        with_change = [r for r in nr if r["change"]]
        rej = nr[0] if not with_change or len(nr) > 1 and nr[0] is not with_change[0] else nr[-1]
        r = S.post(f"{API}/records/{rej['id']}/decide", json={"approve": False})
        assert r.status_code == 200 and r.json()["status"] == "rejected"
        STATE["rejected_uid"] = rej["unique_id"]
        if with_change and with_change[0]["id"] != rej["id"]:
            ap = with_change[0]
            r = S.post(f"{API}/records/{ap['id']}/decide", json={"approve": True})
            assert r.status_code == 200 and r.json()["status"] == "approved"
            STATE["approved_id"] = ap["id"]
            STATE["approve_resp"] = r.json()
            rec = S.get(f"{API}/records/{ap['unique_id']}").json()
            assert rec[0]["status"] == "approved"

    def test_12_decide_twice_blocked(self):
        rid = STATE.get("approved_id")
        if not rid:
            pytest.skip("no approved record")
        r = S.post(f"{API}/records/{rid}/decide", json={"approve": True})
        assert r.status_code == 409, f"Same (superseded) record decided twice -> {r.status_code} {r.text[:200]}"

    def test_13_season_end(self):
        r = S.post(f"{API}/review/season_end", json={})
        assert r.status_code == 200, r.text
        n = r.json()["reviewed"]
        assert n > 0
        r2 = S.post(f"{API}/review/season_end", json={})
        assert r2.json()["reviewed"] == 0
        o = S.get(API).json()
        assert o["stage"] == "season_done" and o["next_review"] is None
        recs = S.get(f"{API}/records", params={"kind": "season_end"}).json()
        assert _no_secret_keys(recs) == []
        r3 = S.post(f"{API}/review/season_end", json={"again": True})
        assert r3.status_code == 200 and r3.json()["applied"]["queued"] == 0

    def test_14_scope(self):
        r = requests.get(f"{BASE_URL}/api/dp/scope")
        assert r.status_code == 200
        d = r.json()
        assert "scope" in d and "covered" in d and "version" in d
        STATE["scope"] = d
        new = dict(d["scope"], all_players=True)
        r = requests.put(f"{BASE_URL}/api/dp/scope", json={"scope": new, "expected_version": d["version"]})
        assert r.status_code == 200, r.text
        d2 = requests.get(f"{BASE_URL}/api/dp/scope").json()
        assert d2["scope"].get("all_players") is True and d2["covered"] >= d["covered"]
        r = requests.put(f"{BASE_URL}/api/dp/scope", json={"scope": d["scope"], "expected_version": d2["version"]})
        assert r.status_code == 200
        assert requests.get(f"{BASE_URL}/api/dp/scope").json()["covered"] == d["covered"]
