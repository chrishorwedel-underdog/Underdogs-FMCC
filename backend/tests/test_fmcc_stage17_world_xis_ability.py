"""Stage 17: hidden CA/PA, competition XIs, extra formations, development columns, World Monthly Reports."""
import os

import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
CREATED_LINEUPS = []  # (formation, revision)
CREATED_PLANS = []  # (unique_id, revision)


def _env():
    out = {}
    for line in open(os.path.join(os.path.dirname(__file__), "..", ".env")):
        if "=" in line:
            k, v = line.strip().split("=", 1)
            out[k] = v.strip('"')
    return out


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    e = _env()
    db = MongoClient(e["MONGO_URL"])[e["DB_NAME"]]
    cid = S.get(f"{API}/state").json().get("career", {}).get("id") if S.get(f"{API}/state").ok else None
    if not cid:
        car = db.careers.find_one({"name": "TEST_Shot"}) or {}
        cid = car.get("id")
    for f, rev in CREATED_LINEUPS:
        db.lineups.delete_one({"career_id": cid, "formation": f, "revision": rev})
    for uid, rev in CREATED_PLANS:
        db.plans.delete_one({"career_id": cid, "unique_id": uid, "revision": rev})


# ---- scout: CA/PA always null ----
class TestScoutMask:
    @pytest.mark.parametrize("view", ["full", "fair", "moneyball"])
    def test_players_ca_pa_null(self, view):
        r = S.post(f"{API}/scout/players", json={"view": view})
        assert r.status_code == 200
        rows = r.json()["rows"]
        assert rows
        assert all(x["ca"] is None and x["pa"] is None for x in rows)

    def test_profile_ca_pa_null(self):
        uid = S.post(f"{API}/scout/players", json={"view": "full"}).json()["rows"][0]["unique_id"]
        r = S.get(f"{API}/scout/player/{uid}", params={"view": "full"})
        assert r.status_code == 200
        txt = r.text
        d = r.json()
        p = d.get("player", d)
        assert p.get("ca") is None and p.get("pa") is None, txt[:300]

    def test_csv_no_ca_pa(self):
        r = S.post(f"{API}/scout/export", json={"view": "full"})
        assert r.status_code == 200, r.text[:300]
        header = r.text.splitlines()[0].lower().split(",")
        assert "ca" not in header and "pa" not in header, header


# ---- squad: competition XIs + extra formations ----
class TestSquad:
    def test_plan_has_competition_xis(self):
        d = S.get(f"{API}/squad/plan").json()
        assert len(d["all_formations"]) == 22
        for k in ("best", "dev", "domestic", "cup", "uefa"):
            assert len(d[k]["slots"]) == 11, k
            assert all(v for v in d[k]["slots"].values())
        assert d["cup"]["rested"]

    def test_plan_no_ca_leak(self):
        d = S.get(f"{API}/squad/plan").json()
        leaks = [y for y in d.get("youth_minutes", []) if "ca" in y]
        assert not leaks, f"youth_minutes exposes real CA: {leaks[:1]}"

    @pytest.mark.parametrize("f", ["352", "442", "532"])
    def test_extra_formation_plan(self, f):
        r = S.get(f"{API}/squad/plan", params={"formation": f})
        assert r.status_code == 200, r.text[:200]
        d = r.json()
        assert d["formation"]["key"] == f
        assert len(d["formation"]["slots"]) == 11
        assert len(d["best"]["slots"]) == 11

    def test_bad_formation_422(self):
        assert S.get(f"{API}/squad/plan", params={"formation": "999"}).status_code == 422

    @pytest.mark.parametrize("kind", ["domestic", "cup", "uefa"])
    def test_save_lineup_kinds(self, kind):
        d = S.get(f"{API}/squad/plan").json()
        hist = S.get(f"{API}/lineups", params={"formation": "433"}).json()
        rev = hist[0]["revision"] if hist else 0
        r = S.post(f"{API}/lineups", json={"formation": "433", "kind": kind, "slots": {k: v for k, v in d[kind]["slots"].items()},
                                             "based_on_save_no": d["save_no"], "expected_revision": rev})
        assert r.status_code == 200, r.text[:300]
        CREATED_LINEUPS.append(("433", r.json()["revision"]))
        top = S.get(f"{API}/lineups", params={"formation": "433"}).json()[0]
        assert top["kind"] == kind
        assert top["name"] == {"domestic": "Domestic XI", "cup": "Cup XI", "uefa": "UEFA XI"}[kind]


# ---- development ----
class TestDevelopment:
    def test_rows_no_ca_pa(self):
        d = S.get(f"{API}/development").json()
        for r in d["rows"]:
            assert "ca" not in r and "pa" not in r
            for k in ("ca_gain_month", "ca_gain_season", "goals", "assists", "minutes_per_game", "avg_rating"):
                assert k in r

    def test_save_plan_goal_gain(self):
        d = S.get(f"{API}/development").json()
        row = d["rows"][0]
        uid = row["unique_id"]
        hist = S.get(f"{API}/development/plans/{uid}/history").json()
        rev = hist[0]["revision"] if hist else 0
        r = S.post(f"{API}/development/plans", json={"unique_id": uid, "minutes_target": 300, "goal_gain": 5, "note": "TEST_plan", "expected_revision": rev})
        assert r.status_code == 200, r.text
        CREATED_PLANS.append((uid, r.json()["revision"]))
        row = next(x for x in S.get(f"{API}/development").json()["rows"] if x["unique_id"] == uid)
        assert row["plan"]["goal_gain"] == 5
        assert "goal_ca" not in row["plan"] and "start_ca" not in row["plan"]
        h = S.get(f"{API}/development/plans/{uid}/history").json()[0]
        assert h["goal_gain"] == 5 and "goal_ca" not in h and "start_ca" not in h


# ---- world monthly reports ----
class TestWorld:
    def test_world_report(self):
        r = S.get(f"{API}/world/report")
        assert r.status_code == 200
        d = r.json()
        assert d["sample"] is True
        assert 0 < len(d["news"]) <= 12
        assert set(d["awards"]) == {"attacker", "defender", "goalie", "u21"}
        for a in d["awards"].values():
            assert len(a["picks"]) <= 3
        for l in d["leaders"]:
            assert len(l["rows"]) <= 10 and len(l["u21"]) <= 5
        assert d["countries"]
        assert "ca" not in r.text.lower().replace("cap", "").split('"ca"')[0] or '"ca":' not in r.text

    def test_world_news_count_12(self):
        d = S.get(f"{API}/world/report").json()
        assert len(d["news"]) == 12, f"only {len(d['news'])} world stories"

    def test_country_report(self):
        d = S.get(f"{API}/world/report").json()
        c = d["countries"][0]["country"]
        r = S.get(f"{API}/world/report", params={"country": c})
        assert r.status_code == 200
        x = r.json()
        assert x["country"] == c
        assert len(x["news"]) <= 5
        assert all(t["country"] == c for t in x["tables"])

    def test_unknown_country_404(self):
        assert S.get(f"{API}/world/report", params={"country": "Atlantis"}).status_code == 404

    def test_month_param(self):
        d = S.get(f"{API}/world/report").json()
        m = d["months"][0]
        r = S.get(f"{API}/world/report", params={"month": m})
        assert r.status_code == 200 and r.json()["month"] == m
        assert S.get(f"{API}/world/report", params={"month": "bad"}).status_code == 422
