# Phase 3 stat lines: Monthly Awards picks, Breakout celebration card, Breakout notice helpers (iteration 53)
import os
import re
import sys

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

GK = ["games", "cs", "sv", "rating"]
DEF = {"games", "tkw", "int", "goals", "assists", "rating"}
MID = {"games", "goals", "assists", "kp", "rating"}
ATT = {"games", "goals", "assists", "rating"}
SING = {"games": "game", "goals": "goal", "assists": "assist", "cs": "clean sheet", "sv": "save", "tkw": "tackle won", "int": "interception", "kp": "key pass"}
PLUR = {"games": "games", "goals": "goals", "assists": "assists", "cs": "clean sheets", "sv": "saves", "tkw": "tackles won", "int": "interceptions", "kp": "key passes"}


def _check_line(line):
    assert isinstance(line, list) and line
    keys = [s["key"] for s in line]
    assert len(keys) == len(set(keys))
    for s in line:
        assert set(s) == {"key", "value", "label"}
        assert isinstance(s["value"], str)
        assert "ca" not in s["key"].lower() and "pa" != s["key"].lower()
        if s["key"] == "rating":
            assert re.fullmatch(r"\d+\.\d", s["value"]) and s["label"] == "avg rating"
        else:
            assert s["label"] == (SING[s["key"]] if s["value"] == "1" else PLUR[s["key"]]), s
    if "rating" in keys:
        assert keys[-1] == "rating"
    return keys


@pytest.fixture(scope="module")
def report():
    r = requests.get(f"{BASE_URL}/api/world/report", timeout=60)
    assert r.status_code == 200
    return r.json()


# Monthly Awards picks
class TestAwardsLine:
    def test_all_picks_have_line(self, report):
        assert report["awards"]
        for k, a in report["awards"].items():
            assert a["picks"], k
            for p in a["picks"]:
                _check_line(p["line"])

    def test_goalie_picks_gk_line(self, report):
        for p in report["awards"]["goalie"]["picks"]:
            keys = [s["key"] for s in p["line"]]
            assert set(keys) <= set(GK) and "goals" not in keys, keys

    def test_defender_picks_def_line(self, report):
        for p in report["awards"]["defender"]["picks"]:
            keys = [s["key"] for s in p["line"]]
            assert set(keys) <= DEF and "kp" not in keys, keys
            for s in p["line"]:
                if s["key"] in ("goals", "assists"):
                    assert s["value"] != "0", "defender goals/assists shown only if any"

    def test_attacker_picks_line(self, report):
        for p in report["awards"]["attacker"]["picks"]:
            keys = set(s["key"] for s in p["line"])
            assert keys <= MID or keys <= ATT, keys


# Breakout celebration card
class TestCelebrations:
    def test_breakout_line(self):
        r = requests.get(f"{BASE_URL}/api/celebrations", timeout=60)
        assert r.status_code == 200
        cards = [c for c in r.json()["cards"] if c["kind"] == "breakout"]
        if not cards:
            pytest.skip("no breakout card in this career")
        c = cards[0]
        keys = _check_line(c["line"])
        assert set(keys) <= DEF | MID | set(GK)
        txt = str(c).lower()
        assert "'ca'" not in txt and "'pa'" not in txt


# Pure helpers (stat_line, season_line, line_text)
class TestHelpers:
    def test_stat_line_groups(self):
        from world_api import stat_line
        gk = stat_line("GK", 5, 0, 0, 7.04, {"cs": 1, "sv": 12, "tkw": 3})
        assert [s["key"] for s in gk] == GK and gk[1]["label"] == "clean sheet" and gk[3]["value"] == "7.0"
        cb = stat_line("CB", 1, 0, 2, 6.95, {"tkw": 1, "int": 4})
        assert [s["key"] for s in cb] == ["games", "tkw", "int", "assists", "rating"]
        assert cb[0]["label"] == "game" and cb[1]["label"] == "tackle won"
        cm = stat_line("CM", 4, 1, 0, 6.6, {})
        assert [s["key"] for s in cm] == ["games", "goals", "assists", "rating"]  # kp missing -> left out
        st = stat_line("ST", 4, 3, 1, 7.25, {"kp": 9})
        assert [s["key"] for s in st] == ["games", "goals", "assists", "rating"]
        assert stat_line("GK", 0, None, None, None, {}) == []

    def test_season_line_and_text(self):
        from awards_api import season_line, line_text
        x = {"unique_id": 1, "positions": ["D (L)"], "appearances": 20, "goals": 0, "assists": 1, "avg_rating": 7.0}
        snap = {"players": [{"unique_id": 1, "totals": {"tkw": 30, "int": 22}}]}
        line = season_line(x, snap)
        assert line_text(line) == "20 games · 30 tackles won · 22 interceptions · 1 assist · 7.0 avg rating"
