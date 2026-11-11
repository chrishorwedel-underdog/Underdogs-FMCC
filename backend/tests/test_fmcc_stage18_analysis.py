# Stage 18: Stats Table / Role Fit / Dossier / Transfer Market / Club Analysis APIs + feature gates + extras list
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
HIDDEN = {"ca", "pa", "ability", "potential", "current_ability", "potential_ability"}


@pytest.fixture(scope="module")
def s():
    ses = requests.Session()
    ses.put(f"{API}/features", json={"features": {"market": True, "club": True, "scouting": True}})
    yield ses
    ses.delete(f"{API}/analysis/roles/cd")
    ses.put(f"{API}/features", json={"features": {"market": True, "club": True, "scouting": True}})


def bad_keys(o, path=""):
    out = []
    if isinstance(o, dict):
        for k, v in o.items():
            if k.lower() in HIDDEN:
                out.append(f"{path}.{k}")
            out += bad_keys(v, f"{path}.{k}")
    elif isinstance(o, list):
        for i, v in enumerate(o):
            out += bad_keys(v, f"{path}[{i}]")
    return out


@pytest.fixture(scope="module")
def table(s):
    r = s.get(f"{API}/analysis/table")
    assert r.status_code == 200, r.text
    return r.json()


# meta: groups and ~40 roles, 100+ columns
def test_meta(s):
    d = s.get(f"{API}/analysis/meta").json()
    for g in ["General", "Attacking", "Passing", "Defending", "Goalkeeping", "Physical", "Attributes"]:
        assert g in d["groups"], g
    ncols = sum(len(v) for v in d["groups"].values())
    print("columns", ncols, "roles", len(d["roles"]))
    assert ncols >= 100
    assert len(d["roles"]) >= 38
    assert bad_keys(d) == []


# table: rows, no CA/PA anywhere
def test_table_rows_no_ca_pa(table):
    rows = table["rows"]
    assert len(rows) > 50
    r = rows[0]
    for k in ["unique_id", "name", "club", "league", "group", "est_value", "role_fit", "top_roles", "p90", "attributes", "value_factors"]:
        assert k in r, k
    assert bad_keys(table) == []
    assert any(x["own"] for x in rows) and any(not x["own"] for x in rows)


# player dossier
def test_player(s, table):
    uid = table["rows"][0]["unique_id"]
    d = s.get(f"{API}/analysis/player/{uid}").json()
    assert d["unique_id"] == uid
    assert [f["name"] for f in d["value_factors"]] == ["Age", "Position", "Club", "Reputation", "Contract", "Form"]
    assert len(d["roles"]) >= 38 and "with_ball" in d["roles"][0]
    assert isinstance(d["value_history"], list)
    assert bad_keys(d) == []


def test_player_404(s):
    assert s.get(f"{API}/analysis/player/999999999").status_code == 404


# similar / cheaper / younger
@pytest.mark.parametrize("kind", ["similar", "cheaper", "younger"])
def test_similar(s, table, kind):
    r0 = max([x for x in table["rows"] if not x["own"]], key=lambda x: x["est_value"])
    r = s.get(f"{API}/analysis/similar/{r0['unique_id']}", params={"kind": kind})
    assert r.status_code == 200
    d = r.json()
    assert bad_keys(d) == []
    for x in d:
        assert x["group"] == r0["group"] and x["unique_id"] != r0["unique_id"]
        if kind == "cheaper":
            assert x["est_value"] <= 0.6 * r0["est_value"]
        if kind == "younger":
            assert x["age"] < r0["age"]
    print(kind, len(d))


def test_similar_bad_kind(s, table):
    assert s.get(f"{API}/analysis/similar/{table['rows'][0]['unique_id']}", params={"kind": "bogus"}).status_code == 422


# role weights put/get/delete + validation
def test_role_weights(s, table):
    assert s.put(f"{API}/analysis/roles/cd", json={"weights": {"bogus_attr": 2}}).status_code == 422
    assert s.put(f"{API}/analysis/roles/cd", json={"weights": {"tackling": 9}}).status_code == 422
    assert s.put(f"{API}/analysis/roles/cd", json={"weights": {"tackling": -1}}).status_code == 422
    assert s.put(f"{API}/analysis/roles/nope", json={"weights": {"tackling": 1}}).status_code == 404
    r = s.put(f"{API}/analysis/roles/cd", json={"weights": {"tackling": 5, "passing": 0}})
    assert r.status_code == 200
    assert s.get(f"{API}/analysis/roles").json()["cd"] == {"tackling": 5, "passing": 0}
    assert s.delete(f"{API}/analysis/roles/cd").status_code == 200
    assert "cd" not in s.get(f"{API}/analysis/roles").json()


# market
def test_market(s):
    r = s.get(f"{API}/analysis/market")
    assert r.status_code == 200
    d = r.json()
    assert set(d["lists"]) == {"expiring", "free", "clauses", "u21", "loans"}
    assert "changes" in d and "rankings" in d and "notes" in d
    assert bad_keys(d) == []
    for x in d["lists"]["expiring"]:
        assert x["years_left"] <= 1 and not x["own"]
    for x in d["lists"]["u21"]:
        assert x["age"] <= 21
    print({k: len(v) for k, v in d["lists"].items()}, "changes", len(d["changes"]), "notes", d["notes"])


# club
def test_club(s):
    r = s.get(f"{API}/analysis/club")
    assert r.status_code == 200
    d = r.json()
    assert len(d["positions"]) == 8
    assert isinstance(d["todo"], list) and len(d["todo"]) >= 1
    for t in d["todo"]:
        assert t["title"] and t["evidence"] and t["link"].startswith("/")
    assert {"upgrade", "affordable", "successor"} <= set(d["ideas"])
    assert bad_keys(d) == []


# feature gates
@pytest.mark.parametrize("key,path", [("market", "/analysis/market"), ("club", "/analysis/club")])
def test_gate(s, key, path):
    s.put(f"{API}/features", json={"features": {key: False}})
    r = s.get(f"{API}{path}")
    s.put(f"{API}/features", json={"features": {key: True}})
    assert r.status_code == 409
    assert s.get(f"{API}{path}").status_code == 200


def test_features_has_market_club(s):
    f = s.get(f"{API}/features").json()["features"]
    assert "market" in f and "club" in f


# extras list only four packs
def test_extras_items(s):
    d = s.get(f"{API}/extras").json()
    keys = [i["key"] for i in d["items"]]
    print(keys)
    assert set(keys) == {"ng_regens", "real_name_fix", "logos", "kits"}
