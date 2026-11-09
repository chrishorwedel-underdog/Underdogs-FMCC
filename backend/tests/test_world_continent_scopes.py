# World Monthly Reports: continent/country/league scope tests (iteration 20) + squad plan formation order
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def world(s):
    r = s.get(f"{BASE_URL}/api/world/report")
    assert r.status_code == 200, r.text
    return r.json()


class TestWorldScope:
    def test_world_shape(self, world):
        assert world["scope"] is None and world["continent"] is None
        conts = [c["continent"] for c in world["continents"]]
        assert "Europe" in conts
        assert all("continent" in c and "leagues" in c for c in world["countries"])
        assert len(world["news"]) <= 12

    def test_continent_europe(self, s, world):
        r = s.get(f"{BASE_URL}/api/world/report", params={"continent": "Europe"})
        assert r.status_code == 200
        d = r.json()
        assert d["scope"] == "Europe" and d["continent"] == "Europe"
        assert 0 < len(d["news"]) <= 8
        assert d["tables"] and all(t["continent"] == "Europe" for t in d["tables"])
        europe_countries = {c["country"] for c in world["countries"] if c["continent"] == "Europe"}
        assert all(t["country"] in europe_countries for t in d["tables"])
        for a in d["awards"].values():
            for p in a["picks"]:
                assert any(p["league"] in c["leagues"] for c in world["countries"] if c["continent"] == "Europe")

    def test_country_england(self, s, world):
        eng = next((c for c in world["countries"] if c["country"] == "England"), None)
        assert eng, "England not in countries"
        assert "Premier Division" in eng["leagues"]
        r = s.get(f"{BASE_URL}/api/world/report", params={"continent": "Europe", "country": "England"})
        assert r.status_code == 200
        d = r.json()
        assert d["scope"] == "England"
        assert len(d["news"]) <= 5
        assert all(t["country"] == "England" for t in d["tables"])

    def test_league_premier_division(self, s):
        r = s.get(f"{BASE_URL}/api/world/report", params={"continent": "Europe", "country": "England", "league": "Premier Division"})
        assert r.status_code == 200
        d = r.json()
        assert d["scope"] == "Premier Division"
        assert [t["league"] for t in d["tables"]] == ["Premier Division"]
        assert len(d["news"]) <= 5
        for a in d["awards"].values():
            assert all(p["league"] == "Premier Division" for p in a["picks"])
        for l in d["leaders"]:
            assert all(x["league"] == "Premier Division" for x in l["rows"] + l["u21"])

    def test_league_only_param(self, s):
        r = s.get(f"{BASE_URL}/api/world/report", params={"league": "Premier Division"})
        assert r.status_code == 200
        assert [t["league"] for t in r.json()["tables"]] == ["Premier Division"]

    def test_unknown_continent_404(self, s):
        r = s.get(f"{BASE_URL}/api/world/report", params={"continent": "Mars"})
        assert r.status_code == 404
        assert "continent" in r.json()["detail"]

    def test_unknown_league_404(self, s):
        r = s.get(f"{BASE_URL}/api/world/report", params={"league": "Unknown"})
        assert r.status_code == 404

    def test_unknown_country_404(self, s):
        r = s.get(f"{BASE_URL}/api/world/report", params={"country": "Atlantis"})
        assert r.status_code == 404

    def test_mismatched_continent_country(self, s):
        # England is in Europe; asking for it in a non-loaded continent should 404 on the continent
        r = s.get(f"{BASE_URL}/api/world/report", params={"continent": "Asia", "country": "England"})
        assert r.status_code == 404

    def test_award_history_scopes(self, s):
        for params in ({}, {"continent": "Europe"}, {"country": "England"}, {"league": "Premier Division"}):
            r = s.get(f"{BASE_URL}/api/world/award-history", params=params)
            assert r.status_code == 200, params
            d = r.json()
            assert d.get("continent") == params.get("continent")
            assert d["months"]
            if "league" in params:
                for m in d["months"]:
                    for w in m["winners"].values():
                        assert w is None or w["league"] == "Premier Division"


class TestSquadPlanOrder:
    def test_formations_are_ordered_lists(self, s):
        r = s.get(f"{BASE_URL}/api/squad/plan")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["formations"], list) and isinstance(d["all_formations"], list)
        assert [k for k, _ in d["formations"]] == ["4231", "352", "442"]
        assert all(len(x) == 2 for x in d["all_formations"])
