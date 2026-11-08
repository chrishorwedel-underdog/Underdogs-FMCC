# Stage 11: formulas, advanced filters, quadrant, replacement, price explained, tactic fit, apps, updates
import io
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
CREATED = []


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    yield
    for k in reversed(CREATED):
        S.delete(f"{API}/scout/formulas/{k}")


def _put(key, name, expr):
    r = S.put(f"{API}/scout/formulas/{key}", json={"name": name, "expr": expr})
    if r.status_code == 200:
        CREATED.append(key)
    return r


# ---------- formulas ----------
class TestFormulas:
    def test_list(self):
        d = S.get(f"{API}/scout/formulas").json()
        assert d["limit"] == 30 and "npg" in d["names"] and "minutes" in d["names"]
        for it in d["items"]:
            assert "_id" not in it

    def test_preview_ok(self):
        d = S.post(f"{API}/scout/formulas/preview", json={"name": "x", "expr": "npg - npxg"}).json()
        assert d["ok"] is True and len(d["rows"]) == 5

    @pytest.mark.parametrize("expr", ["foo + 1", "__import__(1)", "npg ** 2", "(npg", "'a'", "npg.real", "max(a=1)"])
    def test_preview_errors(self, expr):
        d = S.post(f"{API}/scout/formulas/preview", json={"name": "x", "expr": expr}).json()
        assert d["ok"] is False and d["error"]

    def test_save_chain_cycle_delete(self):
        assert _put("test_a", "TEST_A", "npg - npxg").status_code == 200
        assert _put("test_b", "TEST_B", "if(f_test_a > 0, f_test_a * 2, 0)").status_code == 200
        items = {i["key"]: i for i in S.get(f"{API}/scout/formulas").json()["items"]}
        assert items["test_b"]["expr"].startswith("if(")
        # cycle
        r = S.put(f"{API}/scout/formulas/test_a", json={"name": "TEST_A", "expr": "f_test_b + 1"})
        assert r.status_code == 422, r.text
        # self
        r = S.put(f"{API}/scout/formulas/test_c", json={"name": "TEST_C", "expr": "f_test_c + 1"})
        assert r.status_code == 422
        # delete blocked
        r = S.delete(f"{API}/scout/formulas/test_a")
        assert r.status_code == 409 and "TEST_B" in r.json()["detail"]
        # edit -> revision 2
        r = _put("test_a", "TEST_A2", "npg - npxg + 0")
        assert r.json()["revision"] == 2
        # values on players
        rows = S.post(f"{API}/scout/players", json={"min_minutes": 400, "sort": "f:test_b"}).json()["rows"]
        assert rows and "test_b" in (rows[0]["f"] or {})
        a = rows[0]["f"]["test_a"]
        b = rows[0]["f"]["test_b"]
        if a is not None:
            assert b == pytest.approx(a * 2 if a > 0 else 0, abs=0.01)

    def test_bad_key(self):
        assert S.put(f"{API}/scout/formulas/Bad-Key", json={"name": "x", "expr": "1"}).status_code == 422

    def test_delete_missing(self):
        assert S.delete(f"{API}/scout/formulas/nope_zzz").status_code == 404

    def test_import(self):
        r = S.post(f"{API}/scout/formulas/import", json={"formulas": [{"key": "test_imp", "name": "TEST_imp", "expr": "age * 2"}]})
        assert r.status_code == 200 and r.json()["imported"] == ["test_imp"]
        CREATED.append("test_imp")
        assert any(i["key"] == "test_imp" for i in S.get(f"{API}/scout/formulas").json()["items"])

    def test_import_bad(self):
        r = S.post(f"{API}/scout/formulas/import", json={"formulas": [{"key": "test_bad", "name": "x", "expr": "foo"}]})
        assert r.status_code == 422

    def test_meta_has_formulas(self):
        m = S.get(f"{API}/scout/meta").json()
        assert any(f["key"] == "test_a" for f in m["formulas"])


# ---------- advanced filter ----------
class TestAdv:
    def test_value_and_or(self):
        adv = {"op": "and", "items": [{"kind": "value", "field": "minutes", "cmp": ">=", "value": 900},
                                      {"op": "or", "items": [{"kind": "value", "field": "age", "cmp": "<", "value": 23}, {"kind": "value", "field": "age", "cmp": ">", "value": 30}]}]}
        rows = S.post(f"{API}/scout/players", json={"adv": adv, "limit": 500}).json()["rows"]
        assert rows and all(r["minutes"] >= 900 and (r["age"] < 23 or r["age"] > 30) for r in rows)

    def test_stat_vs_stat(self):
        adv = {"op": "and", "items": [{"kind": "stat", "a": "npg", "b": "npxg", "cmp": ">"}]}
        rows = S.post(f"{API}/scout/players", json={"adv": adv, "limit": 500}).json()["rows"]
        assert all(r["stats"]["npg"] > r["stats"]["npxg"] for r in rows)

    def test_pct(self):
        tot = S.post(f"{API}/scout/players", json={"min_minutes": 400}).json()["total"]
        adv = {"op": "and", "items": [{"kind": "pct", "field": "grade", "cmp": ">=", "value": 80, "pool": "save"}]}
        d = S.post(f"{API}/scout/players", json={"adv": adv}).json()
        assert 0 < d["total"] < tot

    def test_formula_field(self):
        adv = {"op": "and", "items": [{"kind": "value", "field": "f:test_imp", "cmp": ">=", "value": 60}]}
        rows = S.post(f"{API}/scout/players", json={"adv": adv, "limit": 500}).json()["rows"]
        assert all(r["age"] >= 30 for r in rows)

    def test_bad_value_no_500(self):
        adv = {"op": "and", "items": [{"kind": "value", "field": "age", "cmp": ">=", "value": "abc"}]}
        r = S.post(f"{API}/scout/players", json={"adv": adv})
        assert r.status_code != 500, "non-numeric value crashes"

    def test_fair_play_no_pa_leak(self):
        adv = {"op": "and", "items": [{"kind": "value", "field": "pa", "cmp": ">=", "value": 170}]}
        d = S.post(f"{API}/scout/players", json={"adv": adv, "view": "fair"}).json()
        full = S.post(f"{API}/scout/players", json={"view": "fair"}).json()["total"]
        assert d["total"] in (0, full), f"PA filter works in Fair play ({d['total']} of {full}) - hidden info leak"


# ---------- quadrant / replacement / price ----------
class TestScoutLab:
    def test_quadrant(self):
        d = S.get(f"{API}/scout/quadrant", params={"perf": "grade"}).json()
        assert d["points"] and {p["zone"] for p in d["points"]} <= {"Stars", "Hidden gems", "Overpriced", "Avoid"}

    def test_quadrant_formula(self):
        d = S.get(f"{API}/scout/quadrant", params={"perf": "f:test_imp"}).json()
        assert d["points"]

    def test_replacement(self):
        uid = S.post(f"{API}/scout/players", json={"min_minutes": 900}).json()["rows"][0]["unique_id"]
        d = S.get(f"{API}/scout/replacement/{uid}").json()
        assert d["target"]["name"] and isinstance(d["rows"], list)
        d2 = S.get(f"{API}/scout/replacement/{uid}", params={"max_value": 1000000, "max_age": 25}).json()
        assert all(r["age"] <= 25 for r in d2["rows"])

    def test_replacement_404(self):
        assert S.get(f"{API}/scout/replacement/1").status_code == 404

    def test_price_all_players(self):
        rows = S.post(f"{API}/scout/players", json={"limit": 500}).json()["rows"]
        bad = []
        for r in rows:
            for view in ("full", "fair"):
                x = S.get(f"{API}/scout/price/{r['unique_id']}", params={"view": view})
                if x.status_code != 200:
                    bad.append((r["unique_id"], view, x.status_code))
        assert not bad, f"price explained failed for {len(bad)}: {bad[:5]}"

    def test_price_fair_hides_potential(self):
        uid = S.post(f"{API}/scout/players", json={}).json()["rows"][0]["unique_id"]
        d = S.get(f"{API}/scout/price/{uid}", params={"view": "fair"}).json()
        assert not any(f["factor"] == "Potential" for f in d["factors"])
        d = S.get(f"{API}/scout/price/{uid}", params={"view": "moneyball"}).json()
        assert not any(f["factor"] == "Potential" for f in d["factors"])


# ---------- squad tactic fit ----------
class TestTactics:
    def test_fit(self):
        for f in ("433", "4231"):
            d = S.get(f"{API}/squad/tactic-fit", params={"formation": f}).json()
            assert len(d["slots"]) == 11 and len(d["gaps"]) == 3 and d["slots"][0]["starter"]

    def test_fit_404(self):
        assert S.get(f"{API}/squad/tactic-fit", params={"formation": "999"}).status_code == 404

    def test_shapes(self):
        d = S.get(f"{API}/squad/shapes").json()
        assert {s["key"] for s in d} == {"433", "4231"}

    def test_save_tactic(self):
        r = S.post(f"{API}/squad/tactics", json={"formation": "4231", "name": "TEST_tac"})
        assert r.status_code == 200 and "_id" not in r.json()
        assert any(t["name"] == "TEST_tac" for t in S.get(f"{API}/squad/tactics").json())
        assert S.post(f"{API}/squad/tactics", json={"formation": "442"}).status_code == 422

    def test_import_fmf(self):
        r = S.post(f"{API}/squad/tactics/import", files={"file": ("TEST_t.fmf", io.BytesIO(b"xx 4-2-3-1 yy"))})
        assert r.status_code == 200 and r.json()["formation"] == "4231"
        r = S.post(f"{API}/squad/tactics/import", files={"file": ("TEST_u.fmf", io.BytesIO(b"\x00\x01garbage"))})
        assert r.status_code == 422 and "formation" in r.json()["detail"]
        r = S.post(f"{API}/squad/tactics/import", files={"file": ("TEST_u.txt", io.BytesIO(b"4-3-3"))})
        assert r.status_code == 422


# ---------- apps + updates ----------
class TestApps:
    def test_apps(self):
        d = S.get(f"{API}/apps").json()
        a = {x["key"]: x for x in d["apps"]}
        assert a["fmdossier"]["url"] == "https://fmdossier.dev/" and a["fmos"]["kind"] == "windows"  # stage 12: fmOS is a Windows app

    def test_path(self):
        assert S.put(f"{API}/apps/fmdossier/path", json={"path": "C:\\x\\dossier.txt"}).status_code == 422
        assert S.put(f"{API}/apps/fmos/path", json={"path": "C:\\x\\a.exe"}).status_code == 200  # stage 12: fmos is a Windows app now
        assert S.put(f"{API}/apps/fmst26/path", json={"path": "C:\\TEST\\fmst.exe"}).status_code == 200
        assert {x["key"]: x for x in S.get(f"{API}/apps").json()["apps"]}["fmst26"]["path"] == "C:\\TEST\\fmst.exe"

    def test_open_409(self):
        assert S.post(f"{API}/apps/fmdossier/open").status_code == 409
