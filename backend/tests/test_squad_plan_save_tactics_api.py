"""Squad plan API: formations default to the tactics read from the save (iteration 19)."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in open("/app/frontend/.env"):
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

SAVE_TACTICS = {"4231": "4-2-3-1 Gegenpress", "352": "Counter-attack (3-5-2)", "442": "Direct 4-4-2"}


@pytest.fixture(scope="module")
def s():
    return requests.Session()


# Default plan picks the first save tactic
def test_default_plan_uses_first_save_tactic(s):
    r = s.get(f"{BASE_URL}/api/squad/plan")
    assert r.status_code == 200
    d = r.json()
    assert d["formation"]["key"] == "4231"
    assert d["from_save"] is True
    assert d["formations"] == SAVE_TACTICS
    assert len(d["best"]["slots"]) == 11 and len(d["dev"]["slots"]) == 11
    for k in SAVE_TACTICS:
        assert k in d["all_formations"]


# Each save tactic shape and an extra still work
@pytest.mark.parametrize("key", ["352", "442", "433", "4231"])
def test_plan_each_formation(s, key):
    r = s.get(f"{BASE_URL}/api/squad/plan", params={"formation": key})
    assert r.status_code == 200
    d = r.json()
    assert d["formation"]["key"] == key
    assert d["formations"] == SAVE_TACTICS
    for mode in ("best", "dev", "domestic", "cup", "uefa"):
        assert len(d[mode]["slots"]) == 11
        assert len(set(d[mode]["slots"].values())) == 11


def test_352_has_wingbacks_and_three_cbs(s):
    d = s.get(f"{BASE_URL}/api/squad/plan", params={"formation": "352"}).json()
    pos = [x["pos"] for x in d["formation"]["slots"]]
    assert sum(1 for p in pos if p in ("CB", "DC")) == 3, pos
    keys = [x["key"] for x in d["formation"]["slots"]]
    assert sum(1 for k in keys if k.startswith("WB")) == 2, keys


def test_442_has_two_strikers(s):
    d = s.get(f"{BASE_URL}/api/squad/plan", params={"formation": "442"}).json()
    pos = [x["pos"] for x in d["formation"]["slots"]]
    assert sum(1 for p in pos if p in ("ST", "STC", "STL", "STR")) == 2, pos


def test_invalid_formation_422(s):
    assert s.get(f"{BASE_URL}/api/squad/plan", params={"formation": "bogus"}).status_code == 422


# Regression: other squad endpoints
@pytest.mark.parametrize("path", ["/api/squad", "/api/squad/registration"])
def test_squad_endpoints(s, path):
    r = s.get(f"{BASE_URL}{path}")
    assert r.status_code == 200
    assert r.json()
