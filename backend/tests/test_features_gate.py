# Per-career feature switches: GET/PUT /api/features, /seen, notify filtering, 409 gates on run endpoints, read-page
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
KEYS = ["dp", "breakout", "scouting", "market", "club", "reports", "moneyball", "squad", "development", "elite", "matches", "editor", "punish", "dof"]


@pytest.fixture(scope="module")
def s():
    ses = requests.Session()
    yield ses
    # restore: all ON
    ses.put(f"{API}/features", json={"features": {k: True for k in KEYS}})


def put(s, **kw):
    r = s.put(f"{API}/features", json={"features": kw})
    assert r.status_code == 200, r.text
    return r.json()["features"]


# Features GET shape
def test_get_features_shape(s):
    d = s.get(f"{API}/features").json()
    assert set(d["features"]) == set(KEYS)
    assert isinstance(d["ask"], bool) and isinstance(d["seen"], bool)


# PUT unknown key -> 422
def test_put_unknown_key(s):
    r = s.put(f"{API}/features", json={"features": {"bogus": False}})
    assert r.status_code == 422


# PUT partial merges and persists
def test_put_partial_persists(s):
    f = put(s, reports=False)
    assert f["reports"] is False and f["dp"] is True
    assert s.get(f"{API}/features").json()["features"]["reports"] is False
    put(s, reports=True)


# reports off hides Monthly report countdown + missed; notify excludes /reports notices
def test_reports_off_hides_countdowns_and_notices(s):
    put(s, reports=False)
    cd = s.get(f"{API}/notify/countdowns").json()
    assert not any(x["page"] == "reports" for x in cd["items"])
    assert cd["missed"] == []
    n = s.get(f"{API}/notify").json()
    assert not any(r["link"].split("?")[0] == "/reports" for r in n["items"])
    put(s, reports=True)
    cd2 = s.get(f"{API}/notify/countdowns").json()
    assert any(x["page"] == "reports" for x in cd2["items"])


# scouting off hides window countdowns; squad off hides contract countdowns
def test_scouting_squad_off_countdowns(s):
    put(s, scouting=False, squad=False)
    cd = s.get(f"{API}/notify/countdowns").json()
    assert not any(x["page"] in ("window", "squad") for x in cd["items"])
    put(s, scouting=True, squad=True)
    cd = s.get(f"{API}/notify/countdowns").json()
    assert any(x["page"] == "window" for x in cd["items"])


# 409 gates when off; when on the same invalid-body call gets past the gate (422 / not 409)
@pytest.mark.parametrize("key,path,body", [
    ("dp", "/dp/run", {"__bad": 1}),
    ("elite", "/elite/queue", None),
    ("breakout", "/breakout/finalise", None),
    ("dof", "/dof/conversations/TEST_nonexistent/stream", {"__bad": 1}),
])
def test_run_endpoints_409_when_off(s, key, path, body):
    put(s, **{key: False})
    r = s.post(f"{API}{path}", json=body)
    put(s, **{key: True})
    assert r.status_code == 409, r.text
    assert "turned off" in r.json()["detail"].lower()


def test_dp_run_not_blocked_when_on(s):
    put(s, dp=True)
    r = s.post(f"{API}/dp/run", json="not-an-object")
    assert r.status_code != 409


# notify badge_items shape
def test_notify_badge_items(s):
    n = s.get(f"{API}/notify").json()
    assert set(n["badge_items"]) == set(n["badges"])
    for b, titles in n["badge_items"].items():
        assert isinstance(titles, list) and len(titles) >= 1


# read-page on a path with no notices marks 0
def test_read_page_unknown(s):
    r = s.post(f"{API}/notify/read-page", json={"path": "/TEST_nowhere"})
    assert r.status_code == 200 and r.json()["marked"] == 0
