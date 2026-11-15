# FMCC Site Audit Phase 1: CA/PA sweep, /api/home/extras, squad progress, report compare, Hall of Fame tribute
import os
import re
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
SECRET = {"ca", "pa", "ca_change", "start_ca", "goal_ca", "goal_gain", "goal_so_far", "pa_change", "true_ca", "true_pa"}
EXEMPT = ("/api/editor", "/api/seed", "/api/creator")
NUM_RE = re.compile(r"(potential \+?-?\d+|\bCA [+-]\d+|CA gained)", re.I)


def find_secret(obj, path=""):
    hits = []
    if isinstance(obj, dict):
        for k, v in obj.items():
            if k in SECRET:
                hits.append(f"{path}.{k}")
            hits += find_secret(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj[:300]):
            hits += find_secret(v, f"{path}[{i}]")
    return hits


def find_text(obj):
    out = []
    if isinstance(obj, dict):
        for v in obj.values():
            out += find_text(v)
    elif isinstance(obj, list):
        for v in obj:
            out += find_text(v)
    elif isinstance(obj, str) and NUM_RE.search(obj):
        out.append(obj[:120])
    return out


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def get_routes(s):
    # route list only (openapi not exposed via ingress); requests still go through BASE_URL
    try:
        spec = s.get("http://localhost:8001/openapi.json", timeout=30)
    except Exception:
        pytest.skip("no openapi")
    if spec.status_code != 200:
        pytest.skip("no openapi")
    paths = spec.json()["paths"]
    return [p for p, ops in paths.items() if "get" in ops and "{" not in p and p.startswith("/api") and not p.startswith(EXEMPT)]


# CA/PA sweep across every parameterless GET endpoint
def test_no_secret_keys_any_get(s, get_routes):
    bad = {}
    for p in get_routes:
        if any(x in p for x in ("download", "export", "stream", "backup", "self-update", "file")):
            continue
        try:
            r = s.get(f"{BASE_URL}{p}", timeout=30)
        except Exception:
            continue
        if "application/json" not in r.headers.get("content-type", ""):
            continue
        hits = find_secret(r.json())
        if hits:
            bad[p] = hits[:3]
    print("checked", len(get_routes))
    assert not bad, bad


def test_no_numeric_ability_text(s):
    bad = {}
    for p in ("/api/notify", "/api/audit", "/api/changes", "/api/home", "/api/development", "/api/squad"):
        r = s.get(f"{BASE_URL}{p}", timeout=30)
        if r.status_code == 200:
            t = find_text(r.json())
            if t:
                bad[p] = t[:3]
    assert not bad, bad


def test_compare_report(s):
    r = s.get(f"{BASE_URL}/api/reports/compare?a=0&b=1", timeout=30)
    assert r.status_code in (200, 400, 404), r.text
    if r.status_code != 200:
        pytest.skip(f"compare {r.status_code}: {r.text[:100]}")
    d = r.json()
    assert not find_secret(d)
    assert "total_change" not in (d.get("summary") or {})
    rows = d.get("rows") or []
    if rows:
        assert "progress" in rows[0]


def test_scout_players_post(s):
    r = s.post(f"{BASE_URL}/api/scout/players", json={}, timeout=60)
    if r.status_code in (404, 405, 422):
        pytest.skip(f"scout players {r.status_code}")
    assert r.status_code == 200, r.text[:200]
    assert not find_secret(r.json())


def test_squad_progress(s):
    r = s.get(f"{BASE_URL}/api/squad", timeout=30)
    assert r.status_code == 200
    d = r.json()
    players = d.get("players", d if isinstance(d, list) else [])
    assert players
    withp = [p for p in players if p.get("progress")]
    assert withp, "no progress on any player"
    for p in withp:
        assert set(p["progress"]) == {"tone", "text"}
        assert p["progress"]["text"] in ("Big step forward", "Improving", "Holding steady", "Slipped back a little")


def test_home_report(s):
    r = s.get(f"{BASE_URL}/api/home", timeout=30)
    assert r.status_code == 200
    d = r.json()
    assert not find_secret(d)
    rep = d.get("report") or {}
    print("home report keys", list(rep.keys()), rep.get("riser"))
    if rep.get("riser"):
        assert set(rep["riser"].keys()) <= {"name", "unique_id"}, rep["riser"]


def test_home_extras(s):
    r = s.get(f"{BASE_URL}/api/home/extras", timeout=30)
    assert r.status_code == 200
    d = r.json()
    for k in ("celebrations", "record_watch", "digest", "countdowns"):
        assert k in d


# Hall of Fame tribute note
def test_hof_note_crud(s):
    pl = s.get(f"{BASE_URL}/api/history/players", timeout=30).json()
    lst = pl.get("players", pl) if isinstance(pl, dict) else pl
    existing = {m["unique_id"] for m in s.get(f"{BASE_URL}/api/history/hall-of-fame").json()["members"]}
    cand = next((p for p in lst if p["unique_id"] not in existing), None)
    if not cand:
        pytest.skip("no candidate")
    uid = cand["unique_id"]
    try:
        r = s.post(f"{BASE_URL}/api/history/hall-of-fame", json={"unique_id": uid, "note": "TEST_tribute one"})
        assert r.status_code == 200, r.text
        m = next(m for m in s.get(f"{BASE_URL}/api/history/hall-of-fame").json()["members"] if m["unique_id"] == uid)
        assert m["note"] == "TEST_tribute one"
        r = s.put(f"{BASE_URL}/api/history/hall-of-fame/{uid}", json={"unique_id": uid, "note": "TEST_tribute two"})
        assert r.status_code == 200
        m = next(m for m in s.get(f"{BASE_URL}/api/history/hall-of-fame").json()["members"] if m["unique_id"] == uid)
        assert m["note"] == "TEST_tribute two"
        assert s.put(f"{BASE_URL}/api/history/hall-of-fame/999999999", json={"unique_id": 1, "note": "x"}).status_code == 404
        assert s.post(f"{BASE_URL}/api/history/hall-of-fame", json={"unique_id": uid, "note": "x" * 301}).status_code == 422
    finally:
        assert s.delete(f"{BASE_URL}/api/history/hall-of-fame/{uid}").status_code == 200
    assert s.delete(f"{BASE_URL}/api/history/hall-of-fame/{uid}").status_code == 404
