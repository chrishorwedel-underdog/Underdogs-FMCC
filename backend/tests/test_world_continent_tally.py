# World Monthly Reports: continent award tally + award-history refactor regression (iteration 21)
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
FORBIDDEN = {"ca", "pa", "current_ability", "potential_ability"}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def world(s):
    r = s.get(f"{BASE_URL}/api/world/report")
    assert r.status_code == 200, r.text
    return r.json()


@pytest.fixture(scope="module")
def tally(s, world):
    r = s.get(f"{BASE_URL}/api/world/continent-tally")
    assert r.status_code == 200, r.text
    return r.json()


def _keys(o):
    if isinstance(o, dict):
        for k, v in o.items():
            yield k
            yield from _keys(v)
    elif isinstance(o, list):
        for v in o:
            yield from _keys(v)


class TestContinentTally:
    def test_shape(self, tally):
        assert isinstance(tally["seasons"], list) and tally["seasons"]
        for s in tally["seasons"]:
            assert {"season", "months", "rows"} <= set(s)
            assert isinstance(s["months"], int) and s["months"] >= 1
            for r in s["rows"]:
                assert {"continent", "points", "wins", "seconds", "thirds", "winners"} <= set(r)
                assert isinstance(r["winners"], list) and len(r["winners"]) <= 3

    def test_newest_first(self, tally):
        seasons = [s["season"] for s in tally["seasons"]]
        assert seasons == sorted(seasons, reverse=True)

    def test_points_formula_and_sort(self, tally):
        for s in tally["seasons"]:
            for r in s["rows"]:
                assert r["points"] == 3 * r["wins"] + 2 * r["seconds"] + r["thirds"]
            pts = [r["points"] for r in s["rows"]]
            assert pts == sorted(pts, reverse=True)

    def test_europe_present(self, tally):
        assert any(r["continent"] == "Europe" for s in tally["seasons"] for r in s["rows"])

    def test_matches_award_history(self, s, tally):
        h = s.get(f"{BASE_URL}/api/world/award-history").json()
        for season in tally["seasons"]:
            months = [m for m in h["months"] if m["season"] == season["season"]]
            assert len(months) == season["months"]
            wins = sum(1 for m in months for w in m["winners"].values() if w)
            assert sum(r["wins"] for r in season["rows"]) == wins

    def test_no_ca_pa(self, tally):
        assert not (set(_keys(tally)) & FORBIDDEN)


class TestAwardHistory:
    def _check(self, s, params):
        r = s.get(f"{BASE_URL}/api/world/award-history", params=params)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["labels"] and d["months"]
        ms = [m["month"] for m in d["months"]]
        assert ms == sorted(ms, reverse=True)
        assert any(w for m in d["months"] for w in m["winners"].values())
        assert not (set(_keys(d)) & FORBIDDEN)
        return d

    def test_world(self, s):
        self._check(s, {})

    def test_continent(self, s):
        d = self._check(s, {"continent": "Europe"})
        assert d["continent"] == "Europe"

    def test_country(self, s, world):
        country = "England" if any(c["country"] == "England" for c in world["countries"]) else world["countries"][0]["country"]
        d = self._check(s, {"country": country})
        for m in d["months"]:
            for w in m["winners"].values():
                if w:
                    assert w["country"] == country

    def test_league(self, s, world):
        lg = world["countries"][0]["leagues"][0]
        d = self._check(s, {"league": lg})
        for m in d["months"]:
            for w in m["winners"].values():
                if w:
                    assert w["league"] == lg


class TestReportLevels:
    def test_levels(self, s, world):
        c = world["countries"][0]
        for p in ({}, {"continent": "Europe"}, {"country": c["country"]}, {"league": c["leagues"][0]}):
            r = s.get(f"{BASE_URL}/api/world/report", params=p)
            assert r.status_code == 200, (p, r.text)
            assert r.json()["awards"]

    def test_bad_continent_404(self, s):
        assert s.get(f"{BASE_URL}/api/world/report", params={"continent": "Atlantis"}).status_code == 404
