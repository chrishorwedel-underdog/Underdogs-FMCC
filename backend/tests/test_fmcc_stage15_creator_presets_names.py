# Stage 15: Player Creator saved presets (per install) + layered name-list updates (sample channel)
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
CREATED = []
BATCHES = []


def settings(**kw):
    s = {"name": "", "count": 10, "nations": [{"nation": "England", "weight": 1}], "age_lo": 16, "age_hi": 21}
    s.update(kw)
    return s


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    # make sure the name layer starts on built-in only
    st = S.get(f"{API}/creator/names").json()
    while st["can_rollback"]:
        S.post(f"{API}/creator/names/rollback")
        st = S.get(f"{API}/creator/names").json()
    yield
    for pid in CREATED:
        S.delete(f"{API}/creator/presets/{pid}")
    for bid in BATCHES:
        S.delete(f"{API}/creator/batches/{bid}")
    st = S.get(f"{API}/creator/names").json()
    while st["can_rollback"]:
        S.post(f"{API}/creator/names/rollback")
        st = S.get(f"{API}/creator/names").json()


def _create(name, **kw):
    r = S.post(f"{API}/creator/presets", json={"name": name, "settings": settings(**kw)})
    if r.status_code == 200:
        CREATED.append(r.json()["pid"])
    return r


# ---------- presets ----------
class TestPresets:
    def test_list(self):
        r = S.get(f"{API}/creator/presets")
        assert r.status_code == 200 and isinstance(r.json(), list)

    def test_create_and_list(self):
        r = _create("TEST_Preset A", count=33, seed=77)
        assert r.status_code == 200
        d = r.json()
        assert d["name"] == "TEST_Preset A" and "seed" not in d["settings"] and "_id" not in d
        rows = {p["pid"]: p for p in S.get(f"{API}/creator/presets").json()}
        p = rows[d["pid"]]
        assert p["settings"]["count"] == 33 and p["dropped"] == [] and p["note"] is None

    def test_duplicate_case_insensitive(self):
        _create("TEST_Dup")
        r = _create("test_dup")
        assert r.status_code == 409
        r = _create("  TEST_DUP  ")
        assert r.status_code == 409

    @pytest.mark.parametrize("bad", [dict(age_lo=25, age_hi=20), dict(nations=[]), dict(ca_lo=150, ca_hi=100), dict(positions=["XX"])])
    def test_invalid_settings(self, bad):
        r = _create("TEST_Bad", **bad)
        assert r.status_code == 422

    def test_empty_name(self):
        assert _create("").status_code == 422

    def test_whitespace_name_rejected(self):
        r = _create("   ")
        assert r.status_code == 422, f"whitespace-only name accepted: {r.status_code} {r.text[:200]}"

    def test_rename_overwrite_delete(self):
        pid = _create("TEST_Edit", count=5).json()["pid"]
        r = S.patch(f"{API}/creator/presets/{pid}", json={"name": "TEST_Edited"})
        assert r.status_code == 200 and r.json()["name"] == "TEST_Edited"
        r = S.patch(f"{API}/creator/presets/{pid}", json={"settings": settings(count=99, age_lo=30, age_hi=35)})
        assert r.status_code == 200
        p = [x for x in S.get(f"{API}/creator/presets").json() if x["pid"] == pid][0]
        assert p["name"] == "TEST_Edited" and p["settings"]["count"] == 99 and p["settings"]["age_lo"] == 30
        # case-only rename of itself allowed
        assert S.patch(f"{API}/creator/presets/{pid}", json={"name": "test_edited"}).status_code == 200
        # rename onto another preset's name -> 409
        _create("TEST_Other")
        assert S.patch(f"{API}/creator/presets/{pid}", json={"name": "TEST_OTHER"}).status_code == 409
        # invalid overwrite -> 422
        assert S.patch(f"{API}/creator/presets/{pid}", json={"settings": settings(age_lo=30, age_hi=20)}).status_code == 422
        assert S.delete(f"{API}/creator/presets/{pid}").status_code == 200
        assert pid not in [x["pid"] for x in S.get(f"{API}/creator/presets").json()]
        assert S.delete(f"{API}/creator/presets/{pid}").status_code == 404
        assert S.patch(f"{API}/creator/presets/{pid}", json={"name": "x"}).status_code == 404

    def test_unknown_pid(self):
        assert S.patch(f"{API}/creator/presets/nope", json={"name": "TEST_x"}).status_code == 404
        assert S.delete(f"{API}/creator/presets/nope").status_code == 404

    def test_unknown_nation_dropped(self):
        pid = _create("TEST_Atlantis", nations=[{"nation": "Atlantis"}, {"nation": "Spain"}]).json()["pid"]
        p = [x for x in S.get(f"{API}/creator/presets").json() if x["pid"] == pid][0]
        assert p["dropped"] == ["Atlantis"]
        assert [n["nation"] for n in p["settings"]["nations"]] == ["Spain"]
        assert "Atlantis" in p["note"] and "England" not in p["note"]

    def test_all_unknown_england(self):
        pid = _create("TEST_AllUnknown", nations=[{"nation": "Atlantis"}, {"nation": "Narnia"}]).json()["pid"]
        p = [x for x in S.get(f"{API}/creator/presets").json() if x["pid"] == pid][0]
        assert [n["nation"] for n in p["settings"]["nations"]] == ["England"]
        assert "England used instead" in p["note"]


# ---------- name lists ----------
class TestNames:
    def test_state_builtin(self):
        d = S.get(f"{API}/creator/names").json()
        assert d["installed"] is None and d["can_rollback"] is False
        rows = {r["nation"]: r for r in d["countries"]}
        assert rows["Senegal"]["builtin"] > 0 and rows["Senegal"]["update"] == 0
        assert d["total"]["update"] == 0

    def test_check_sample(self):
        d = S.get(f"{API}/creator/names/check").json()
        assert d["sample"] is True and d["version"] == "sample-2026.1" and d["available"] is True
        assert d["countries_added"] == ["Jamaica", "Peru", "Slovenia", "Venezuela"]
        assert "Senegal" in d["names_added"] and d["total_added"] > 0

    def test_install_wrong_version(self):
        r = S.post(f"{API}/creator/names/install", json={"version": "bogus"})
        assert r.status_code == 409

    def test_batch_before_install_then_flow(self):
        # batch before install
        b = S.post(f"{API}/creator/batches", json=settings(name="TEST_Before", count=12, faces=False, nations=[{"nation": "Senegal"}]))
        assert b.status_code == 200, b.text
        bid = b.json()["bid"]
        BATCHES.append(bid)
        names_before = [p["name"] for p in b.json()["players"]]
        assert all(p["name_source"] == "built-in" for p in b.json()["players"])

        r = S.post(f"{API}/creator/names/install", json={"version": "sample-2026.1"})
        assert r.status_code == 200 and r.json()["version"] == "sample-2026.1"
        assert S.post(f"{API}/creator/names/install", json={"version": "sample-2026.1"}).status_code == 409

        d = S.get(f"{API}/creator/names").json()
        assert d["installed"]["version"] == "sample-2026.1" and d["installed"]["sample"] is True and d["can_rollback"]
        rows = {r["nation"]: r for r in d["countries"]}
        assert rows["Senegal"]["update"] > 0 and rows["Jamaica"]["builtin"] == 0 and rows["Jamaica"]["update"] == 20
        print("Senegal counts:", rows["Senegal"], "England:", rows["England"])

        m = S.get(f"{API}/creator/meta").json()
        for n in ("Jamaica", "Peru", "Slovenia", "Venezuela"):
            assert n in m["name_lists"] and n in m["nations"]
        assert "Senegal" not in m["closest"]
        assert m["name_counts"]["Jamaica"]["update"] == 20

        c = S.get(f"{API}/creator/names/check").json()
        assert c["available"] is False and c["installed"] == "sample-2026.1"

        pv = S.post(f"{API}/creator/preview", json=settings(count=40, nations=[{"nation": "Senegal"}, {"nation": "Jamaica"}])).json()
        assert "Jamaica" not in pv["borrowed_names"]
        jam = [p for p in pv["players"] if p["nationality"] == "Jamaica"]
        sen = [p for p in pv["players"] if p["nationality"] == "Senegal"]
        assert jam and sen
        assert all(p["ethnicity"] == "African / Caribbean" and p["name_source"] == "update" for p in jam)
        assert any(p["name_source"] == "update" for p in sen)

        # old batch keeps its names
        rows = {x["bid"]: x for x in S.get(f"{API}/creator/batches").json()}
        assert [p["name"] for p in rows[bid]["sample"]] == names_before[:6]
        f = S.get(f"{API}/creator/batches/{bid}/file").text
        assert all(n.split(" ")[0] in f for n in names_before)

        # new batch after install works
        b2 = S.post(f"{API}/creator/batches", json=settings(name="TEST_After", count=10, faces=False, nations=[{"nation": "Peru"}]))
        assert b2.status_code == 200
        BATCHES.append(b2.json()["bid"])
        assert all(p["name_source"] == "update" and p["ethnicity"] == "Mixed race" for p in b2.json()["players"])

        # rollback
        r = S.post(f"{API}/creator/names/rollback")
        assert r.status_code == 200 and r.json()["now"] == "built-in names only"
        d = S.get(f"{API}/creator/names").json()
        assert d["installed"] is None and d["total"]["update"] == 0
        assert "Jamaica" not in S.get(f"{API}/creator/meta").json()["name_lists"]
        assert S.post(f"{API}/creator/names/rollback").status_code == 409
        assert S.get(f"{API}/creator/names/check").json()["available"] is True


# ---------- presets not career-scoped ----------
class TestCrossCareer:
    def test_visible_in_other_career(self):
        careers = S.get(f"{API}/careers").json()
        orig = [c for c in careers if c["active"]][0]["id"]
        pid = _create("TEST_Global").json()["pid"]
        r = S.post(f"{API}/careers", json={"name": "TEST_Career2", "club_name": "TEST Club 2", "edition": "FM27"})
        assert r.status_code == 200, r.text
        new = r.json().get("id") or r.json().get("career", {}).get("id")
        S.post(f"{API}/careers/{new}/activate")
        try:
            assert pid in [p["pid"] for p in S.get(f"{API}/creator/presets").json()]
        finally:
            S.post(f"{API}/careers/{orig}/activate")
