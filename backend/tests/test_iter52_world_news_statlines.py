# World report "12 biggest stories": per-position monthly stat lines (iteration 52)
import os
import re
import sys

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

GROUP_KEYS = {"GK": {"games", "cs", "sv", "rating"}, "CB": {"games", "tkw", "int", "goals", "assists", "rating"},
              "DM": {"games", "goals", "assists", "kp", "rating"}, "ATT": {"games", "goals", "assists", "rating"}}
SING = {"games": "game", "goals": "goal", "assists": "assist", "cs": "clean sheet", "sv": "save", "tkw": "tackle won", "int": "interception", "kp": "key pass"}
PLUR = {"games": "games", "goals": "goals", "assists": "assists", "cs": "clean sheets", "sv": "saves", "tkw": "tackles won", "int": "interceptions", "kp": "key passes"}


def _get(params=None):
    r = requests.get(f"{BASE_URL}/api/world/report", params=params or {}, timeout=60)
    assert r.status_code == 200, r.text[:300]
    return r.json()


def _check_item(n, league_scope=False):
    assert isinstance(n["tag"], str) and n["tag"]
    assert "country" in n
    assert n["league"] is None or (isinstance(n["league"], str) and n["league"] != "Other" and n["league"].strip())
    if "player" in n:
        assert set(n) == {"tag", "country", "player", "club", "stats", "league"}, n
        assert n["stats"], n
        keys = [s["key"] for s in n["stats"]]
        assert len(keys) == len(set(keys))
        assert any(set(keys) <= v for v in GROUP_KEYS.values()), keys
        for s in n["stats"]:
            assert set(s) == {"key", "value", "label"}
            assert isinstance(s["value"], str)
            if s["key"] == "rating":
                assert re.fullmatch(r"\d+\.\d", s["value"]), s
                assert s["label"] == "avg rating"
            else:
                assert s["value"].isdigit()
                assert s["label"] == (SING if s["value"] == "1" else PLUR)[s["key"]], s
        if "tkw" in keys or "int" in keys:
            # defender: goals/assists only when > 0
            for s in n["stats"]:
                if s["key"] in ("goals", "assists"):
                    assert s["value"] != "0", n
    else:
        assert set(n) == {"tag", "country", "text", "league"}, n
        assert "scores " not in n["text"] and "averages " not in n["text"]


class TestWorldReportNews:
    def test_world_news_shape(self):
        d = _get()
        assert 0 < len(d["news"]) <= 12
        for n in d["news"]:
            _check_item(n)
        assert any("player" in n for n in d["news"])

    def test_latest_month_has_def_gk_totals(self):
        d = _get()
        players = [n for n in d["news"] if "player" in n]
        keys = {s["key"] for n in players for s in n["stats"]}
        # after two reads with totals, defender + GK lines include their month totals
        assert {"tkw", "int"} <= keys, keys
        assert {"cs", "sv"} <= keys, keys

    def test_old_month_without_prev_totals_leaves_keys_out(self):
        d = _get({"month": "2028-04"})
        assert d["month"] == "2028-04"
        for n in d["news"]:
            _check_item(n)
            if "player" in n:
                assert not {s["key"] for s in n["stats"]} & {"tkw", "int", "cs", "sv", "kp"}, n

    def test_all_months_valid(self):
        for m in _get()["months"]:
            for n in _get({"month": m})["news"]:
                _check_item(n)

    def test_continent_country_league_scopes(self):
        d = _get()
        cont = d["continents"][0]["continent"]
        dc = _get({"continent": cont})
        assert dc["scope"] == cont and len(dc["news"]) <= 8
        for n in dc["news"]:
            _check_item(n)
        ctry = d["countries"][0]
        dn = _get({"country": ctry["country"]})
        assert len(dn["news"]) <= 5
        for n in dn["news"]:
            _check_item(n)
        dl = _get({"league": ctry["leagues"][0]})
        assert dl["league"] == ctry["leagues"][0] and len(dl["news"]) <= 5
        for n in dl["news"]:
            _check_item(n)

    def test_bad_scope_404(self):
        r = requests.get(f"{BASE_URL}/api/world/report", params={"league": "TEST_nope"}, timeout=30)
        assert r.status_code == 404


# Unit tests for _stat_line/_story
def _row(group, **kw):
    base = {"name": "TEST_P", "club": "TEST_C", "league": "TEST_L", "group": group, "has_apps": True, "m_apps": 3, "m_goals": 0,
            "m_assists": 0, "m_rating": 7.04, "m_tot": {}}
    return base | kw


@pytest.fixture(scope="module")
def wa():
    import world_api
    return world_api


class TestStatLineUnit:
    def test_gk(self, wa):
        line = wa._stat_line(_row("GK", m_tot={"cs": 1, "sv": 9, "tkw": 2}))
        assert [s["key"] for s in line] == ["games", "cs", "sv", "rating"]
        assert line[1]["label"] == "clean sheet" and line[3]["value"] == "7.0"

    def test_cb_goals_only_if_any(self, wa):
        assert [s["key"] for s in wa._stat_line(_row("CB", m_tot={"tkw": 4, "int": 1}))] == ["games", "tkw", "int", "rating"]
        line = wa._stat_line(_row("FB", m_goals=1, m_tot={"tkw": 4}))
        assert [s["key"] for s in line] == ["games", "tkw", "goals", "rating"]
        assert line[2]["label"] == "goal"

    def test_dm_cm(self, wa):
        assert [s["key"] for s in wa._stat_line(_row("CM", m_tot={"kp": 5}))] == ["games", "goals", "assists", "kp", "rating"]

    def test_attackers(self, wa):
        for g in ("AM", "W", "ST"):
            assert [s["key"] for s in wa._stat_line(_row(g, m_assists=1, m_tot={"kp": 5}))] == ["games", "goals", "assists", "rating"]

    def test_wb_maps_to_fb(self):
        from sample_reader import GROUP
        assert GROUP["WB (L)"] == "FB" and GROUP["WB (R)"] == "FB"

    def test_dropped_when_unreadable(self, wa):
        assert wa._story(_row("GK", has_apps=False, m_rating=None)) is None
        assert wa._story(_row("CB", has_apps=False, m_rating=None)) is None

    def test_league_null_when_blank(self, wa):
        assert wa._story(_row("ST", league=""))["league"] is None
        assert wa._story(_row("ST", league=None))["league"] is None
