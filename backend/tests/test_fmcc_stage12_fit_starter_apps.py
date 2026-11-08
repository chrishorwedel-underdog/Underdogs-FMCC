# Stage 12: one-player-per-position Tactic fit, Formula starter pack, official app pages, update checks
import os
import sys
import pytest
import requests
from pymongo import MongoClient

sys.path.insert(0, "/app/backend")
import roles  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
STARTER_KEYS = ["finishing", "goal_threat", "creator", "carrier", "defender", "duels", "shot_stopper", "cost_per_grade", "wage_value", "young_talent"]


def _env(k):
    for line in open("/app/backend/.env"):
        if line.startswith(k + "="):
            return line.split("=", 1)[1].strip().strip('"')


def _players():
    db = MongoClient(_env("MONGO_URL"))[_env("DB_NAME")]
    car = db.careers.find_one({"name": "TEST_Career"}) or db.careers.find_one({})
    snap = db.snapshots.find({"career_id": car["id"]}).sort([("save_no", -1)]).limit(1)[0]
    return snap["players"]


def _best_sum(players, slots):
    """Exhaustive max sum of natural ratings, each player once, slots may be empty."""
    elig = [[(p["unique_id"], roles.role_rating(p, s["role"])) for p in players if roles.eligible(p, s)] for s in slots]
    memo = {}

    def go(i, used):
        if i == len(slots):
            return 0
        k = (i, used)
        if k in memo:
            return memo[k]
        best = go(i + 1, used)
        for uid, r in elig[i]:
            if uid not in used:
                best = max(best, r + go(i + 1, used | frozenset([uid])))
        memo[k] = best
        return best
    return go(0, frozenset())


# ---------- tactic fit ----------
class TestTacticFit:
    @pytest.mark.parametrize("f", ["433", "4231"])
    def test_no_duplicates(self, f):
        d = S.get(f"{API}/squad/tactic-fit", params={"formation": f}).json()
        uids = [s[k]["unique_id"] for s in d["slots"] for k in ("starter", "backup", "depth") if s[k]]
        assert len(uids) == len(set(uids)), f"duplicates in {f}"
        assert len(d["slots"]) == 11 and len(d["gaps"]) == 3
        assert all(s[k]["natural"] for s in d["slots"] for k in ("starter", "backup", "depth") if s[k])

    @pytest.mark.parametrize("f", ["433", "4231"])
    def test_starters_optimal(self, f):
        d = S.get(f"{API}/squad/tactic-fit", params={"formation": f}).json()
        got = sum(s["starter"]["rating"] for s in d["slots"] if s["starter"])
        slots = roles.formation_meta(f)["slots"]
        assert got == _best_sum(_players(), slots)

    def test_shapes(self):
        r = S.get(f"{API}/squad/shapes")
        assert r.status_code == 200
        d = r.json()
        assert {x["key"] for x in d} >= {"433", "4231"} and all("strength" in x and "depth" in x for x in d)

    def test_404(self):
        assert S.get(f"{API}/squad/tactic-fit", params={"formation": "999"}).status_code == 404


# ---------- starter pack ----------
class TestStarterPack:
    def test_list(self):
        d = S.get(f"{API}/scout/formulas/starter").json()
        assert [x["key"] for x in d] == STARTER_KEYS
        assert all(set(x) >= {"key", "name", "expr", "about", "added"} for x in d)

    def test_all_preview_ok(self):
        for x in S.get(f"{API}/scout/formulas/starter").json():
            p = S.post(f"{API}/scout/formulas/preview", json={"name": x["name"], "expr": x["expr"]}).json()
            assert p["ok"], (x["key"], p)

    def test_add_edit_delete_cycle(self):
        r = S.post(f"{API}/scout/formulas/starter", json={"keys": ["finishing", "creator"]})
        assert r.status_code == 200 and sorted(r.json()["added"]) == ["creator", "finishing"]
        r2 = S.post(f"{API}/scout/formulas/starter", json={"keys": ["finishing", "goal_threat"]})
        assert r2.json()["added"] == ["goal_threat"]
        st = {x["key"]: x["added"] for x in S.get(f"{API}/scout/formulas/starter").json()}
        assert st["finishing"] and st["creator"] and st["goal_threat"] and not st["carrier"]
        items = {x["key"]: x for x in S.get(f"{API}/scout/formulas").json()["items"]}
        assert {"finishing", "creator", "goal_threat"} <= set(items)
        meta = S.get(f"{API}/scout/meta").json()
        assert {"finishing", "creator"} <= {f["key"] for f in meta["formulas"]}
        rows = S.post(f"{API}/scout/players", json={}).json()
        row = (rows.get("rows") or rows.get("items") or [])[0]
        assert "finishing" in (row.get("f") or {}), row.keys()
        rev = items["finishing"]["revision"]
        e = S.put(f"{API}/scout/formulas/finishing", json={"name": "Finishing vs xG", "expr": "npg - npxg * 1.1"})
        assert e.status_code == 200 and e.json()["revision"] == rev + 1
        for k in ("finishing", "creator", "goal_threat"):
            assert S.delete(f"{API}/scout/formulas/{k}").status_code == 200
        st = {x["key"]: x["added"] for x in S.get(f"{API}/scout/formulas/starter").json()}
        assert not any(st.values())

    def test_empty_keys_422(self):
        assert S.post(f"{API}/scout/formulas/starter", json={"keys": []}).status_code == 422

    def test_unknown_key_ignored(self):
        r = S.post(f"{API}/scout/formulas/starter", json={"keys": ["nope"]})
        assert r.status_code == 200 and r.json()["added"] == []


# ---------- apps and updates ----------
class TestApps:
    def test_apps(self):
        a = {x["key"]: x for x in S.get(f"{API}/apps").json()["apps"]}
        assert a["fmst26"]["url"] == "https://www.fmscout.com/a-fmst-26.html"
        assert a["fmos"]["url"] == "https://fmos.it/"
        assert a["fmdossier"]["url"] == "https://fmdossier.dev/"
        assert all(x["kind"] == "windows" for x in a.values()) and len(a) == 3

    def test_fmos_path_now_allowed(self):
        assert S.put(f"{API}/apps/fmos/path", json={"path": "C:\\x\\a.txt"}).status_code == 422

    def test_updates_manual(self):
        S.post(f"{API}/updates/check")
        rows = {x["key"]: x for x in S.get(f"{API}/updates").json()} if isinstance(S.get(f"{API}/updates").json(), list) else {x["key"]: x for x in S.get(f"{API}/updates").json()["components"]}
        exp = {"fmst26": "v2.1.0", "fmos": "v1.5", "fmdossier": "v1.15.3"}
        for k, v in exp.items():
            assert rows[k]["status"] == "manual" and rows[k]["manual"] is True, rows[k]
            assert rows[k]["latest_version"] == v, (k, rows[k]["latest_version"])
            assert rows[k]["release_url"]
