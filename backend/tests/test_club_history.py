# Club History API (/api/history/*): seasons, cabinet, season page, records, leaders, compare, milestones, pins, hall of fame
import os
import json
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
H = f"{BASE_URL}/api/history"


def _no_ca_pa(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert str(k).lower() not in ("ca", "pa", "true_ca", "true_pa"), f"CA/PA key at {path}.{k}"
            _no_ca_pa(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_ca_pa(v, f"{path}[{i}]")


@pytest.fixture(scope="module")
def s():
    return requests.Session()


class TestReads:
    def test_seasons(self, s):
        r = s.get(f"{H}/seasons")
        assert r.status_code == 200
        d = r.json()
        assert any(x["season"] == "2027/28" for x in d["seasons"])
        x = next(x for x in d["seasons"] if x["season"] == "2027/28")
        assert x["status"] in ("In Progress", "Completed")
        _no_ca_pa(d)

    @pytest.mark.parametrize("scope", ["save", "full"])
    def test_cabinet(self, s, scope):
        r = s.get(f"{H}/cabinet", params={"scope": scope})
        assert r.status_code == 200
        d = r.json()
        assert d["scope"] == scope
        for k in ("latest", "last_three", "trophies", "promotions", "runner_up", "totals", "individual", "fmcc_awards", "timeline"):
            assert k in d
        assert set(d["totals"]) == {"trophies", "promotions", "runner_up"}
        _no_ca_pa(d)

    def test_season_page(self, s):
        r = s.get(f"{H}/seasons/2027/28")
        assert r.status_code == 200
        d = r.json()
        assert d["season"] == "2027/28"
        assert isinstance(d["squad"], list) and d["squad"]
        for k in ("league", "cups", "recruitment", "academy", "growth", "sources"):
            assert k in d
        assert "_id" not in d
        _no_ca_pa(d)

    def test_season_missing_404(self, s):
        assert s.get(f"{H}/seasons/1999/00").status_code == 404

    @pytest.mark.parametrize("scope", ["league", "all"])
    def test_records(self, s, scope):
        r = s.get(f"{H}/records", params={"scope": scope})
        assert r.status_code == 200
        d = r.json()
        assert d["min_minutes"] == 900
        for part in ("team", "players", "matches", "transfers"):
            assert isinstance(d[part], list) and d[part]
            for rec in d[part]:
                assert "holder" in rec and "previous" in rec and "available" in rec
        _no_ca_pa(d)

    def test_leaders(self, s):
        r = s.get(f"{H}/leaders")
        assert r.status_code == 200
        d = r.json()
        assert {l["key"] for l in d["leaders"]} == {"npxg", "xa", "xgxa", "progp", "prgc", "xgp"}
        r2 = s.get(f"{H}/leaders", params={"season": "2027/28"})
        assert r2.status_code == 200 and r2.json()["season"] == "2027/28"
        _no_ca_pa(d)

    def test_compare(self, s):
        r = s.get(f"{H}/compare", params={"a": "2027/28", "b": "2027/28"})
        assert r.status_code == 200
        d = r.json()
        assert d["a"]["season"] == "2027/28" and d["b"]["season"] == "2027/28"
        assert s.get(f"{H}/compare", params={"a": "1999/00", "b": "2027/28"}).status_code == 404

    def test_milestones_players_hof(self, s):
        for p in ("milestones", "players", "hall-of-fame"):
            r = s.get(f"{H}/{p}")
            assert r.status_code == 200, p
            _no_ca_pa(r.json())
        assert isinstance(s.get(f"{H}/players").json()["players"], list)


class TestHallOfFame:
    def test_induct_and_remove(self, s):
        players = s.get(f"{H}/players").json()["players"]
        if not players:
            pytest.skip("no club players with appearances")
        existing = {m["unique_id"] for m in s.get(f"{H}/hall-of-fame").json()["members"]}
        p = next((p for p in players if p["unique_id"] not in existing), None)
        if not p:
            pytest.skip("all players inducted already")
        r = s.post(f"{H}/hall-of-fame", json={"unique_id": p["unique_id"], "note": "TEST_"})
        try:
            assert r.status_code == 200 and r.json()["name"] == p["name"]
            mem = s.get(f"{H}/hall-of-fame").json()["members"]
            m = next(m for m in mem if m["unique_id"] == p["unique_id"])
            assert m["totals"]["appearances"] >= 0
            _no_ca_pa(mem)
        finally:
            d = s.delete(f"{H}/hall-of-fame/{p['unique_id']}")
        assert d.status_code == 200
        assert all(m["unique_id"] != p["unique_id"] for m in s.get(f"{H}/hall-of-fame").json()["members"])
        assert s.delete(f"{H}/hall-of-fame/{p['unique_id']}").status_code == 404

    def test_induct_non_club_player_404(self, s):
        assert s.post(f"{H}/hall-of-fame", json={"unique_id": 999999999}).status_code == 404

    def test_induct_bad_body_422(self, s):
        assert s.post(f"{H}/hall-of-fame", json={"unique_id": "abc"}).status_code == 422


class TestPins:
    def test_custom_pin_validation(self, s):
        assert s.post(f"{H}/pins", json={"title": "", "season": "2027/28"}).status_code == 422
        assert s.post(f"{H}/pins", json={"title": "TEST_x"}).status_code == 422
        assert s.post(f"{H}/pins", json={"title": "   ", "season": "2027/28"}).status_code == 422

    def test_custom_pin_lifecycle(self, s):
        r = s.post(f"{H}/pins", json={"title": "TEST_moment", "season": "2027/28", "note": "n"})
        assert r.status_code == 200
        pid = r.json()["id"]
        try:
            ms = s.get(f"{H}/milestones").json()["milestones"]
            m = next(m for m in ms if m["id"] == pid)
            assert m["pinned"] is True and m["title"] == "TEST_moment" and m["kind"] == "pinned"
        finally:
            assert s.delete(f"{H}/pins/{pid}").status_code == 200
        assert all(m["id"] != pid for m in s.get(f"{H}/milestones").json()["milestones"])
        assert s.delete(f"{H}/pins/{pid}").status_code == 404

    def test_pin_auto_milestone(self, s):
        ms = s.get(f"{H}/milestones").json()["milestones"]
        auto = next((m for m in ms if not m.get("pinned") and m["kind"] != "pinned"), None)
        if not auto:
            pytest.skip("no unpinned auto milestone")
        assert s.post(f"{H}/pins", json={"id": auto["id"]}).status_code == 200
        try:
            m = next(m for m in s.get(f"{H}/milestones").json()["milestones"] if m["id"] == auto["id"])
            assert m["pinned"] is True
        finally:
            assert s.delete(f"{H}/pins/{auto['id']}").status_code == 200
        m = next(m for m in s.get(f"{H}/milestones").json()["milestones"] if m["id"] == auto["id"])
        assert m["pinned"] is False
