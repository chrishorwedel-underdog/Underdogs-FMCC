# Iteration 54: Squad picks by natural position + squad-relative stars (no ability numbers anywhere)
import os
import re
import sys

import pymongo
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
import roles  # noqa: E402

STARS = {x / 2 for x in range(1, 11)}
BANNED_KEYS = {"ca", "pa", "rating", "current_ability", "potential_ability"}


def _keys(o, path="", out=None):
    out = [] if out is None else out
    if isinstance(o, dict):
        for k, v in o.items():
            if k in BANNED_KEYS:
                out.append(f"{path}.{k}")
            _keys(v, f"{path}.{k}", out)
    elif isinstance(o, list):
        for i, v in enumerate(o):
            _keys(v, f"{path}[{i}]", out)
    return out


@pytest.fixture(scope="module")
def s():
    return requests.Session()


@pytest.fixture(scope="module")
def mdb():
    return pymongo.MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]


@pytest.fixture(scope="module")
def snap(mdb):
    st = mdb.settings.find_one({"_id": "app"})
    c = mdb.careers.find_one({"id": st["active_career_id"]})
    return mdb.snapshots.find_one({"career_id": c["id"]}, sort=[("save_no", -1)]) | {"_cid": c["id"]}


@pytest.fixture(scope="module")
def plan(s):
    r = s.get(f"{BASE_URL}/api/squad/plan")
    assert r.status_code == 200, r.text
    return r.json()


# ---- /api/squad/plan ----
class TestPlan:
    def test_no_banned_keys_except_saved(self, plan):
        leaks = [k for k in _keys({k: v for k, v in plan.items() if k != "saved"})]
        assert not leaks, leaks

    def test_saved_lineup_strength_is_stars(self, plan):
        sv = plan.get("saved")
        if not sv:
            pytest.skip("no saved lineup")
        assert sv["strength"] in STARS, f"saved lineup strength is a 0-100 number: {sv['strength']}"

    def test_depth_rows_shape_and_order(self, plan):
        for slot, rows in plan["depth"].items():
            for r in rows:
                assert set(r) == {"unique_id", "stars", "oop"}, (slot, r)
                assert r["stars"] in STARS
            nat = [r for r in rows if not r["oop"]]
            oop = [r for r in rows if r["oop"]]
            assert rows[:len(nat)] == nat, f"{slot}: oop before natural"
            st = [r["stars"] for r in nat]
            assert st == sorted(st, reverse=True), (slot, st)
            if oop:
                assert len(nat) < 2, slot
                assert len(rows) <= 3, slot
            if slot == "GK":
                assert not oop

    def test_eligibility_against_snapshot(self, plan, snap):
        by = {p["unique_id"]: p for p in snap["players"]}
        slots = {sl["key"]: sl for sl in plan["formation"]["slots"]}
        for k, rows in plan["depth"].items():
            for r in rows:
                nat = set(roles.natural_positions(by[r["unique_id"]]))
                if not r["oop"]:
                    assert nat & set(slots[k]["positions"]), (k, by[r["unique_id"]]["name"])
                else:
                    assert not (nat & set(slots[k]["positions"])), (k, r)
                    assert nat & set(roles.COVER[slots[k]["pos"]]), (k, r)
        # every natural player is listed
        for k, sl in slots.items():
            exp = {u for u, p in by.items() if set(roles.natural_positions(p)) & set(sl["positions"])}
            got = {r["unique_id"] for r in plan["depth"][k] if not r["oop"]}
            assert exp == got, k

    def test_weak(self, plan):
        labels = [w["label"] for w in plan["weak"]]
        assert len(labels) == len(set(labels)), labels
        for w in plan["weak"]:
            assert set(w) == {"slot", "label", "stars", "options"}
            nat = [r for r in plan["depth"][w["slot"]] if not r["oop"]]
            assert w["options"] == len(nat)
            assert w["stars"] == (nat[0]["stars"] if nat else 0)
        st = [w["stars"] for w in plan["weak"]]
        assert st == sorted(st)

    def test_strengths_are_stars(self, plan):
        for k in ("best", "dev", "domestic", "cup", "uefa"):
            assert plan[k]["strength"] in STARS, (k, plan[k]["strength"])

    def test_why_texts(self, plan):
        texts = [t for k in ("best", "dev", "domestic", "cup", "uefa") for _, t in plan[k]["why"]]
        for t in texts:
            assert "point" not in t.lower(), t
            assert "%" not in t, t
            assert not re.search(r"\brating\b|\bCA\b|\bPA\b|ability \d", t), t

    def test_players_info_no_ca(self, plan):
        for u, i in plan["players"].items():
            assert "ca" not in i and "pa" not in i


# ---- eligibility with sample 'natural' (pure unit; sample reader, no DB writes) ----
class TestSampleNatural:
    def test_uid_mod3_rule_and_depth(self):
        import sample_reader
        data = sample_reader.read_save(9, "TEST club")
        players = data["players"]
        for p in players:
            exp = p["positions"][:1] if p["unique_id"] % 3 == 0 else p["positions"]
            assert roles.natural_positions(p) == exp, p["name"]
        for key in ("433", "4231", "352", "442"):
            form = roles.formation_meta(key)
            depth = roles.depth_chart(players, form)
            by = {p["unique_id"]: p for p in players}
            for sl in form["slots"]:
                for r in depth[sl["key"]]:
                    ok = set(roles.natural_positions(by[r["unique_id"]])) & set(sl["positions"])
                    assert bool(ok) == (not r["oop"]), (key, sl["key"], by[r["unique_id"]]["name"])
            xi = roles.best_xi(players, form, depth)
            assert len({u for u in xi.values() if u}) == len([u for u in xi.values() if u])


# ---- PUT /api/squad/depth keeps a custom order ----
class TestDepthOrder:
    def test_custom_order_kept(self, s, plan, mdb, snap):
        f = plan["formation"]["key"]
        slot = next(k for k, v in plan["depth"].items() if len(v) >= 2 and k not in plan["depth_custom"])
        orig = [r["unique_id"] for r in plan["depth"][slot]]
        before = mdb.depth_orders.find_one({"career_id": snap["_cid"], "formation": f})
        new = list(reversed(orig))
        try:
            r = s.put(f"{BASE_URL}/api/squad/depth", json={"formation": f, "slot": slot, "order": new})
            assert r.status_code == 200, r.text
            p2 = s.get(f"{BASE_URL}/api/squad/plan", params={"formation": f}).json()
            assert [x["unique_id"] for x in p2["depth"][slot]] == new
            assert slot in p2["depth_custom"]
            bad = s.put(f"{BASE_URL}/api/squad/depth", json={"formation": f, "slot": slot, "order": new[:1]})
            assert bad.status_code == 422
        finally:
            if before is None:
                mdb.depth_orders.delete_one({"career_id": snap["_cid"], "formation": f})
            else:
                mdb.depth_orders.update_one({"_id": before["_id"]}, {"$unset": {f"slots.{slot}": ""}})
        p3 = s.get(f"{BASE_URL}/api/squad/plan", params={"formation": f}).json()
        assert [x["unique_id"] for x in p3["depth"][slot]] == orig


# ---- Tactic fit & shapes ----
class TestLab:
    def test_tactic_fit(self, s):
        r = s.get(f"{BASE_URL}/api/squad/tactic-fit")
        assert r.status_code == 200, r.text
        d = r.json()
        assert not [k for k in _keys(d["slots"]) if not k.endswith(".role_options")], _keys(d["slots"])[:5]
        for sl in d["slots"]:
            assert sl["score"] == 0 or sl["score"] in STARS, sl["score"]
            for row in sl["ranked"]:
                assert "stars" in row and "natural" in row and "rating" not in row
            nat = [x for x in sl["ranked"] if x["natural"]]
            assert sl["ranked"][:len(nat)] == nat
        assert [g["score"] for g in d["gaps"]] == sorted(sl["score"] for sl in d["slots"])[:3]

    def test_tactic_fit_formations(self, s):
        for f in ("433", "352", "41212", "523"):
            r = s.get(f"{BASE_URL}/api/squad/tactic-fit", params={"formation": f})
            assert r.status_code == 200, (f, r.text)

    def test_shapes(self, s):
        d = s.get(f"{BASE_URL}/api/squad/shapes").json()
        for x in d:
            assert x["strength"] in STARS and (x["depth"] == 0 or x["depth"] in STARS), x


# ---- Home, analysis, registration, try-xi ----
class TestOthers:
    def test_home(self, s):
        r = s.get(f"{BASE_URL}/api/home")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["squad"]["xi_average"] in STARS, d["squad"]
        weak = [a for a in d["attention"] if a["kind"] == "weak"]
        assert weak
        assert re.fullmatch(r".+ is the best option there \(\d(\.5)? stars?\)\.", weak[0]["sub"]), weak[0]["sub"]
        assert not [k for k in _keys(d) if k.split(".")[-1] in ("ca", "pa")]

    def test_home_weak_label_matches_squad_card(self, s):
        d = s.get(f"{BASE_URL}/api/home").json()
        weak = [a for a in d["attention"] if a["kind"] == "weak"][0]
        assert weak["text"].startswith(str(d["squad"]["weak_spot"])), (weak["text"], d["squad"]["weak_spot"])

    def test_analysis_club(self, s):
        r = s.get(f"{BASE_URL}/api/analysis/club")
        assert r.status_code == 200, r.text
        txt = r.text
        ev = [t for t in re.findall(r'"evidence":\s*"([^"]*)"', txt) if "weakest" in t.lower()]
        print(ev)
        for e in ev:
            assert "star" in e, e

    def test_registration(self, s):
        r = s.get(f"{BASE_URL}/api/squad/registration")
        assert r.status_code == 200, r.text
        for t in r.json()["suggestions"]:
            assert "rating" not in t.lower() or "lowest-rated" in t.lower(), t
            assert not re.search(r"\(\d{2,3}\b", t), t

    def test_try_xi(self, s, mdb, snap):
        pool = (mdb.pools.find_one({"career_id": snap["_cid"]}) or {}).get("players") or []
        if not pool:
            pytest.skip("no pool")
        ids = ",".join(str(p["unique_id"]) for p in sorted(pool, key=lambda p: -(p.get("ca") or 0))[:3])
        r = s.get(f"{BASE_URL}/api/squad/try-xi", params={"add": ids})
        assert r.status_code == 200, r.text
        d = r.json()
        for sl in d["slots"]:
            for k in ("before_rating", "after_rating"):
                assert sl[k] is None or sl[k] in STARS, (sl, k)
        assert d["strength_before"] in STARS and d["strength_after"] in STARS
        assert not [k for k in _keys(d) if k.split(".")[-1] in ("ca", "pa")]
