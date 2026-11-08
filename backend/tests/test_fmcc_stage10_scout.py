# Stage 10: ScoutSheet views, FMDataLab analytics, league strength, graphics tools (kits/packs/bulk/pack check), Best XI
import io
import os
import zipfile

import pytest
import requests
from PIL import Image

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()


def players(**f):
    r = S.post(f"{API}/scout/players", json={"limit": 500} | f)
    assert r.status_code == 200, r.text
    return r.json()


def png(color=(200, 0, 0)):
    b = io.BytesIO()
    Image.new("RGB", (64, 64), color).save(b, "PNG")
    return b.getvalue()


@pytest.fixture(scope="module")
def pool():
    return players()["rows"]


# ---- views / masking ----
class TestViews:
    def test_full_view_shows_ca(self, pool):
        assert any(x["ca"] for x in pool) and any(x["best_role"] for x in pool)

    def test_fair_masks_ca_pa(self):
        rows = players(view="fair")["rows"]
        assert all(x["ca"] is None and x["pa"] is None for x in rows)

    def test_moneyball_masks_role(self):
        rows = players(view="moneyball")["rows"]
        assert all(x["best_role"] is None and x["ca"] is None for x in rows)

    def test_profile_views(self, pool):
        uid = next(x["unique_id"] for x in pool if x["minutes"] >= 900)
        full = S.get(f"{API}/scout/player/{uid}?view=full").json()
        assert full["hidden"] and full["report"] and isinstance(full["attributes"], dict)
        fair = S.get(f"{API}/scout/player/{uid}?view=fair").json()
        assert fair["hidden"] is None and fair["personality"] is None and fair["report"] is None and fair["ca"] is None
        assert all(isinstance(v, list) and len(v) == 2 for v in fair["attributes"].values())
        mb = S.get(f"{API}/scout/player/{uid}?view=moneyball").json()
        assert mb["attributes"] is None and mb["best_role"] is None and mb["role_ratings"] == []
        assert S.get(f"{API}/scout/player/999999999").status_code == 404

    def test_profile_similar_and_seasons(self, pool):
        uid = next(x["unique_id"] for x in pool if x["minutes"] >= 900)
        p = S.get(f"{API}/scout/player/{uid}").json()
        assert len(p["similar"]) > 0 and "similarity" in p["similar"][0]
        assert isinstance(p["seasons"], list) and len(p["seasons"]) >= 1
        assert p["profile_keys"]


# ---- minutes rules ----
class TestMinutes:
    def test_pct_needs_400(self, pool):
        assert all(not x["pct"] for x in pool if x["minutes"] < 400)

    def test_fair_price_needs_900(self, pool):
        assert all(x["fair_price"] is None for x in pool if x["minutes"] < 900)
        assert any(x["fair_price"] for x in pool if x["minutes"] >= 900)

    def test_grade_needs_400(self, pool):
        bad = [(x["name"], x["minutes"], x["grade_global"]) for x in pool if x["minutes"] < 400 and x["grade_global"] is not None]
        assert not bad, f"grades shown under 400 minutes: {bad[:5]}"


# ---- filters, presets, sorting, export ----
class TestFilters:
    def test_group_league_gender(self):
        assert all(x["group"] == "ST" for x in players(group="ST")["rows"])
        assert all(x["league"] == "Serie A" for x in players(league="Serie A")["rows"])
        f = players(gender="F")["rows"]
        assert f and all(x["league"] == "Women's Super Division" for x in f)

    def test_value_age_minutes(self):
        assert all(x["value"] <= 5_000_000 for x in players(max_value=5_000_000)["rows"])
        assert all(x["age"] <= 21 for x in players(max_age=21)["rows"])
        assert all(x["minutes"] >= 900 for x in players(min_minutes=900)["rows"])

    @pytest.mark.parametrize("p", ["wonderkids", "expiring", "bargains", "top_grade", "young_regulars"])
    def test_presets(self, p):
        rows = players(preset=p)["rows"]
        if p == "expiring":
            assert all(x["months_left"] <= 12 for x in rows)
        if p == "young_regulars":
            assert all(x["age"] <= 23 and x["minutes"] >= 900 for x in rows)

    def test_sort_and_modes(self):
        r = players(sort="age", dir="asc")["rows"]
        assert [x["age"] for x in r] == sorted(x["age"] for x in r)
        uid = r[0]["unique_id"]
        t = players(mode="total", sort="minutes")["rows"]
        p9 = players(mode="p90", sort="minutes")["rows"]
        k = next(iter(t[0]["stats"]))
        assert t[0]["unique_id"] == p9[0]["unique_id"] and (t[0]["stats"][k] != p9[0]["stats"][k] or t[0]["minutes"] == 90)
        assert uid

    def test_export_csv(self):
        r = S.post(f"{API}/scout/export", json={"view": "fair", "group": "ST"})
        assert r.status_code == 200 and "text/csv" in r.headers["content-type"]
        assert ",CA," not in r.text.splitlines()[0]
        r = S.post(f"{API}/scout/export", json={"view": "full"})
        assert "CA" in r.text.splitlines()[0]

    def test_bad_filter_422(self):
        assert S.post(f"{API}/scout/players", json={"group": "XX"}).status_code == 422


# ---- saved searches and prefs ----
class TestSearchesPrefs:
    def test_saved_search_crud(self):
        r = S.post(f"{API}/scout/searches", json={"name": "TEST_search", "filters": {"group": "ST", "max_age": 23}})
        key = r.json()["key"]
        lst = S.get(f"{API}/scout/searches").json()
        assert any(s["key"] == key and s["filters"]["group"] == "ST" for s in lst)
        assert S.delete(f"{API}/scout/searches/{key}").status_code == 200
        assert S.delete(f"{API}/scout/searches/{key}").status_code == 404

    def test_prefs(self):
        old = S.get(f"{API}/scout/prefs").json()
        S.put(f"{API}/scout/prefs", json={"currency": "EUR", "wages": "year"})
        assert S.get(f"{API}/scout/prefs").json() == {"currency": "EUR", "wages": "year"}
        S.put(f"{API}/scout/prefs", json=old)
        assert S.put(f"{API}/scout/prefs", json={"currency": "XXX"}).status_code == 422


# ---- my club, deals, offers ----
class TestClubDeals:
    def test_myclub_weakest_first(self):
        r = S.get(f"{API}/scout/myclub").json()
        assert len(r) == 8 and [x["rating"] for x in r] == sorted(x["rating"] for x in r)
        g = r[0]["group"]
        imp = S.get(f"{API}/scout/myclub/{g}").json()
        assert all(x["gain"] > 0 and not x["own"] for x in imp["rows"])
        assert S.get(f"{API}/scout/myclub/ZZ").status_code == 404

    def test_deals_under_80pct(self):
        d = S.get(f"{API}/scout/deals").json()
        assert all(x["value"] < .8 * x["fair_price"] for x in d)

    def test_offer_verdicts(self, pool):
        x = next(p for p in pool if p["fair_price"] and not p["own"])
        lo = S.post(f"{API}/scout/offer", json={"unique_id": x["unique_id"], "amount": int(x["fair_price"] * .5), "direction": "buy"}).json()
        hi = S.post(f"{API}/scout/offer", json={"unique_id": x["unique_id"], "amount": int(x["fair_price"] * 2), "direction": "buy"}).json()
        assert lo["verdict"] == "Good deal" and hi["verdict"] == "Well over fair price"
        sell = S.post(f"{API}/scout/offer", json={"unique_id": x["unique_id"], "amount": int(x["fair_price"] * 1.5), "direction": "sell"}).json()
        assert sell["verdict"] == "Great sale"
        y = next(p for p in pool if p["minutes"] < 900)
        assert S.post(f"{API}/scout/offer", json={"unique_id": y["unique_id"], "amount": 1000000}).json()["verdict"] == "Not enough minutes"


# ---- computed, tactical, scatter, breakdown, roles, possession ----
class TestAnalytics:
    def test_builtin_edit_and_reset(self):
        c = S.get(f"{API}/scout/computed").json()
        assert sum(1 for a in c["items"] if a["builtin"]) == 8
        a = next(a for a in c["items"] if a["builtin"])
        m = dict(a["metrics"])
        k0 = next(iter(m))
        m[k0] = 0 if m[k0] != 0 else 10
        assert S.put(f"{API}/scout/computed/{a['key']}", json={"name": a["name"], "metrics": m}).status_code == 200
        a2 = next(x for x in S.get(f"{API}/scout/computed").json()["items"] if x["key"] == a["key"])
        assert a2["metrics"][k0] == m[k0] and a2["metrics"] != a2["defaults"]
        assert S.delete(f"{API}/scout/computed/{a['key']}").status_code == 200
        a3 = next(x for x in S.get(f"{API}/scout/computed").json()["items"] if x["key"] == a["key"])
        assert a3["metrics"] == a3["defaults"]
        assert S.put(f"{API}/scout/computed/{a['key']}", json={"name": "x", "metrics": {"gls": 5}}).status_code == 422

    def test_custom_computed(self):
        assert S.put(f"{API}/scout/computed/test_c", json={"name": "TEST_c", "metrics": {"gls": 5, "xa": 5}}).status_code == 422
        assert S.put(f"{API}/scout/computed/test_c", json={"name": "TEST_c", "metrics": {"gls": 11, "xa": 5, "kp": 3}}).status_code == 422
        assert S.put(f"{API}/scout/computed/test_c", json={"name": "TEST_c", "metrics": {"gls": 5, "xa": 5, "kp": 3}}).status_code == 200
        assert "test_c" in players()["rows"][0]["computed"]
        assert S.delete(f"{API}/scout/computed/test_c").status_code == 200
        assert "test_c" not in [a["key"] for a in S.get(f"{API}/scout/computed").json()["items"]]

    def test_custom_limit_6(self):
        keys = []
        try:
            for i in range(7):
                r = S.put(f"{API}/scout/computed/test_l{i}", json={"name": f"TEST_l{i}", "metrics": {"gls": 5, "xa": 5, "kp": 3}})
                if r.status_code == 200:
                    keys.append(f"test_l{i}")
                else:
                    assert r.status_code == 409
            assert len(keys) == 6
        finally:
            for k in keys:
                S.delete(f"{API}/scout/computed/{k}")

    def test_tactical(self):
        r = S.get(f"{API}/scout/tactical", params={"key": "ball_winner", "in_w": 0, "out_w": 10})
        assert r.status_code == 200 and r.json()
        rows = r.json()
        assert [x["score"] for x in rows] == sorted((x["score"] for x in rows), reverse=True)
        assert S.get(f"{API}/scout/tactical", params={"key": "nope"}).status_code == 404

    def test_scatter_breakdown(self, pool):
        s = S.get(f"{API}/scout/scatter", params={"x": "gls", "y": "c:dlp"}).json()
        assert s["points"] and s["avg_x"] is not None
        ids = ",".join(str(x["unique_id"]) for x in pool if x["pct"])[:40].rsplit(",", 1)[0]
        b = S.get(f"{API}/scout/breakdown", params={"ids": ids, "key": "dlp"}).json()
        assert 1 <= len(b["players"]) <= 4 and b["players"][0]["parts"]

    def test_roles(self):
        meta = S.get(f"{API}/scout/meta").json()
        role = meta["roles"][0]["key"]
        r = S.get(f"{API}/scout/roles", params={"role": role}).json()
        assert [x["rating"] for x in r] == sorted((x["rating"] for x in r), reverse=True)
        assert S.get(f"{API}/scout/roles", params={"role": "bogus"}).status_code == 404

    def test_possession_and_adjusted(self):
        p = S.get(f"{API}/scout/possession").json()
        assert p["rows"][0]["own"] and "FMMatchLens" in p["matchlens"]
        club = p["rows"][0]["club"]
        assert S.put(f"{API}/scout/possession/{club}", json={"value": 90}).status_code == 422
        assert S.put(f"{API}/scout/possession/{club}", json={"value": 60}).status_code == 200
        p2 = S.get(f"{API}/scout/possession").json()
        row = next(r for r in p2["rows"] if r["club"] == club)
        assert row["value"] == 60 and row["revision"] >= 1
        S.put(f"{API}/scout/possession/{club}", json={"value": None})


# ---- HTML import ----
HTML = b"""<html><body><table><tr><th>UID</th><th>Name</th><th>Club</th><th>Age</th><th>Position</th><th>Mins</th><th>Gls</th><th>Transfer Value</th></tr>
<tr><td>30500004</td><td>TEST_Caio</td><td>Northbridge Athletic</td><td>32</td><td>D (L)</td><td>1200</td><td>3</td><td>&pound;13.5M</td></tr>
<tr><td></td><td>TEST_Unlinked</td><td>Nowhere FC</td><td>22</td><td>ST</td><td>900</td><td>10</td><td>&pound;2M</td></tr></table></body></html>"""


class TestHtmlImport:
    def test_import_and_remove(self):
        r = S.post(f"{API}/scout/import-html", files=[("files", ("TEST_export.html", HTML, "text/html"))])
        assert r.status_code == 200, r.text
        d = r.json()
        try:
            assert d["players"] == 2 and d["linked"] == 1
            rows = players(source="html")["rows"]
            names = {x["name"]: x for x in rows}
            assert "TEST_Unlinked" in names and "TEST_Caio" in names
            assert names["TEST_Caio"]["linked"] is True, "linked flag not passed through to rows"
            assert names["TEST_Unlinked"]["linked"] is False
        finally:
            assert S.delete(f"{API}/scout/imports/{d['id']}").status_code == 200

    def test_import_does_not_hijack_save_profile(self):
        d = S.post(f"{API}/scout/import-html", files=[("files", ("TEST_export.html", HTML, "text/html"))]).json()
        try:
            prof = S.get(f"{API}/scout/player/30500004").json()
            assert prof["source"] == "save", "linked HTML row replaced the save player's profile (by_uid overwrite)"
        finally:
            S.delete(f"{API}/scout/imports/{d['id']}")

    def test_removed_import_disappears(self):
        d = S.post(f"{API}/scout/import-html", files=[("files", ("TEST_export.html", HTML, "text/html"))]).json()
        players(source="html")
        S.delete(f"{API}/scout/imports/{d['id']}")
        left = [x for x in players(source="html")["rows"] if x["name"].startswith("TEST_")]
        assert not left, "removed HTML import still listed (stats cache not invalidated on remove)"

    def test_bad_html_422(self):
        assert S.post(f"{API}/scout/import-html", files=[("files", ("x.html", b"<p>no</p>", "text/html"))]).status_code == 422


# ---- leagues ----
class TestLeagues:
    def test_matching(self):
        d = S.get(f"{API}/leagues").json()
        L = {r["name"]: r for r in d["leagues"]}
        assert d["list"]["count"] == 408
        assert L["Serie A"]["opta_name"] == "Serie A"
        assert L["Highland Football League"]["opta_name"] == "Highland / Lowland Leagues"
        assert L["Women's Super Division"]["status"] == "womens"
        ref = d["list"]["reference"]
        assert abs(L["Serie A"]["multiplier"] - (L["Serie A"]["opta"] / ref) ** 1.5) < .002

    def test_match_and_multiplier(self):
        assert S.put(f"{API}/leagues/Serie A/match", json={"opta_name": "Serie B"}).status_code == 200
        L = {r["name"]: r for r in S.get(f"{API}/leagues").json()["leagues"]}
        assert L["Serie A"]["opta_name"] == "Serie B"
        S.put(f"{API}/leagues/Serie A/match", json={"opta_name": "Serie A"})
        assert S.put(f"{API}/leagues/Serie A/match", json={"opta_name": "Nope"}).status_code == 422
        assert S.put(f"{API}/leagues/Nope/match", json={"opta_name": None}).status_code == 404
        assert S.put(f"{API}/leagues/Eredivisie/multiplier", json={"value": 0.5}).status_code == 200
        L = {r["name"]: r for r in S.get(f"{API}/leagues").json()["leagues"]}
        assert L["Eredivisie"]["multiplier"] == 0.5 and L["Eredivisie"]["edited"]
        ere = [x for x in players(league="Eredivisie")["rows"] if x["grade_local"] is not None][0]
        assert abs(ere["grade_global"] - round(20 + (ere["grade_local"] - 20) * 0.5, 1)) <= 0.15
        S.put(f"{API}/leagues/Eredivisie/multiplier", json={"value": None})
        assert S.put(f"{API}/leagues/Eredivisie/multiplier", json={"value": 5}).status_code == 422
        assert len(S.get(f"{API}/leagues/Eredivisie/history").json()) >= 2

    def test_recalculate_preview(self):
        r = S.post(f"{API}/leagues/recalculate", json={"apply": False}).json()
        assert r["applied"] is False and isinstance(r["changes"], list)

    def test_import_list_and_builtin(self):
        csv = b"Competition,Country,Opta Average\nTEST League A,Testland,90\nTEST League B,Testland,60\n"
        r = S.post(f"{API}/leagues/import", files={"file": ("TEST_list.csv", csv, "text/csv")})
        assert r.status_code == 200 and r.json()["count"] == 2
        assert S.get(f"{API}/leagues").json()["list"]["count"] == 2
        assert S.post(f"{API}/leagues/import", files={"file": ("bad.csv", b"a,b\n1,2\n", "text/csv")}).status_code == 422
        S.post(f"{API}/leagues/use-builtin")
        assert S.get(f"{API}/leagues").json()["list"]["count"] == 408


# ---- squad best XI ----
def test_squad_plan():
    r = S.get(f"{API}/squad/plan")
    assert r.status_code == 200, r.text


# ---- editor graphics ----
class TestGraphics:
    def test_kits_upload_remove(self):
        clubs = S.get(f"{API}/editor/kits").json()
        assert clubs
        uid = clubs[0]["uid"]
        r = S.post(f"{API}/editor/kits/{uid}/home", files={"file": ("k.png", png(), "image/png")})
        assert r.status_code == 200, r.text
        assert next(c for c in S.get(f"{API}/editor/kits").json() if c["uid"] == uid)["kits"]["home"]
        assert S.get(f"{API}/editor/kit-image/{uid}/home").status_code == 200
        assert S.delete(f"{API}/editor/kits/{uid}/home").status_code == 200
        assert not next(c for c in S.get(f"{API}/editor/kits").json() if c["uid"] == uid)["kits"]["home"]
        assert S.post(f"{API}/editor/kits/{uid}/fourth", files={"file": ("k.png", png(), "image/png")}).status_code in (404, 422)

    def test_packs(self):
        p = S.get(f"{API}/editor/packs").json()
        assert p
        name = p[0]["name"]
        g = S.get(f"{API}/editor/packs/{name}", params={"limit": 2}).json()
        assert g
        assert S.get(f"{API}/editor/packs/nopack").status_code == 404

    def test_pack_check(self):
        r = S.get(f"{API}/editor/pack-check")
        assert r.status_code == 200, r.text

    def test_bulk_stage_write_undo(self, pool):
        uid = pool[0]["unique_id"]
        z = io.BytesIO()
        with zipfile.ZipFile(z, "w") as f:
            f.writestr(f"{uid}.png", png())
            f.writestr("99999998.png", png())
            f.writestr("noid.png", png())
        r = S.post(f"{API}/editor/bulk/stage", data={"kind": "faces"}, files=[("files", ("TEST.zip", z.getvalue(), "application/zip"))])
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["counts"].get("add", 0) + d["counts"].get("replace", 0) == 1
        assert d["counts"].get("not_in_save") == 1 and d["counts"].get("skipped") == 1
        w = S.post(f"{API}/editor/bulk/{d['id']}/write")
        assert w.status_code == 200, w.text
        assert S.post(f"{API}/editor/bulk/{d['id']}/write").status_code == 409
        n = next(i["n"] for i in d["items"] if i["status"] in ("add", "replace"))
        assert S.post(f"{API}/editor/bulk/{d['id']}/undo/{n}").status_code == 200
        assert S.post(f"{API}/editor/bulk/{d['id']}/undo/{n}").status_code == 409
