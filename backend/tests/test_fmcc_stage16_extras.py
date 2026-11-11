"""Stage 16: 'Downloads you need' extras (NG_Regens, Real Name Fix, logos/kits, apps) + preset validation retest."""
import os
import shutil
import time
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
PF = Path(__file__).resolve().parents[1] / "preview_fm"
DB = PF / "game" / "data" / "database" / "db" / "2700"
OURS = DB / "lnc" / "all" / "fmcc_club_names.lnc"
CREATED = []


def _items():
    r = S.get(f"{API}/extras")
    assert r.status_code == 200
    return r.json(), {i["key"]: i for i in r.json()["items"]}


@pytest.fixture(scope="module", autouse=True)
def cleanup():
    had_ours = OURS.exists()
    backups_before = set(os.listdir(PF / "extras-backups")) if (PF / "extras-backups").exists() else set()
    yield
    for pid in CREATED:
        S.delete(f"{API}/creator/presets/{pid}")
    if not had_ours and OURS.exists():
        OURS.unlink()
    # remove backups this run created
    if (PF / "extras-backups").exists():
        for b in set(os.listdir(PF / "extras-backups")) - backups_before:
            shutil.rmtree(PF / "extras-backups" / b, ignore_errors=True)


# ---------- retest: preset validation ----------
class TestPresetValidation:
    def _settings(self):
        return {"count": 5, "age_lo": 16, "age_hi": 19, "nations": [{"nation": "England", "weight": 1}]}

    def test_whitespace_post_422(self):
        r = S.post(f"{API}/creator/presets", json={"name": "   ", "settings": self._settings()})
        if r.status_code == 200:
            CREATED.append(r.json()["pid"])
        assert r.status_code == 422

    def test_patch_blank_and_empty_422(self):
        r = S.post(f"{API}/creator/presets", json={"name": f"TEST_S16_{int(time.time())}", "settings": self._settings()})
        assert r.status_code == 200, r.text
        pid = r.json()["pid"]
        CREATED.append(pid)
        assert S.patch(f"{API}/creator/presets/{pid}", json={}).status_code == 422
        assert S.patch(f"{API}/creator/presets/{pid}", json={"name": "   "}).status_code == 422
        assert S.patch(f"{API}/creator/presets/{pid}", json={"name": "  TEST_S16_trim  "}).json()["name"] == "TEST_S16_trim"


# ---------- extras list ----------
class TestExtrasList:
    def test_list_shape(self):
        d, it = _items()
        assert [i["key"] for i in d["items"]] == ["ng_regens", "real_name_fix", "logos", "kits"]
        assert it["ng_regens"]["needed"] and it["real_name_fix"]["needed"]
        assert not any(it[k]["needed"] for k in ("logos", "kits"))
        assert d["desktop"] is False
        assert len(d["built_in"]) >= 5 and all("name" in b and "role" in b for b in d["built_in"])
        assert isinstance(d["needed_missing"], list)
        assert "pattern" not in it["ng_regens"]

    def test_sample_downloads(self):
        _, it = _items()
        assert it["ng_regens"]["download"]["sample"] and it["ng_regens"]["download"]["file"].startswith("SAMPLE")
        assert it["real_name_fix"]["download"]["file"] == "SAMPLE Real Name Fix FM27.zip"
        assert it["kits"]["download"]["sample"]
        assert it["logos"]["download"] is None

    def test_pages(self):
        _, it = _items()
        assert "ngregens.org" in it["ng_regens"]["page"]
        assert "sortitoutsi.net" in it["real_name_fix"]["page"]


# ---------- installs ----------
class TestInstalls:
    def test_rnf_install_twice_preserves_ours(self):
        OURS.parent.mkdir(parents=True, exist_ok=True)
        OURS.write_text('"CLUB_LONG_NAME_CHANGE" 1 "TEST_ours"\n')
        r = S.post(f"{API}/extras/real_name_fix/install")
        assert r.status_code == 200, r.text
        j = r.json()
        assert j["sample"] is True and j["backup"].startswith("real_name_fix-") and "Real Name Fix installed" in j["message"]
        assert (PF / "extras-backups" / j["backup"]).is_dir()
        assert OURS.exists() and "TEST_ours" in OURS.read_text()
        assert (DB / "dbc" / "permanent" / "sample_fix.dbc").exists()
        assert (DB / "edt" / "permanent" / "sample_fix.edt").exists()
        assert (PF / "editor data" / "sample_fix.fmf").exists()
        d, it = _items()
        assert it["real_name_fix"]["found"] is True and it["real_name_fix"]["installed_at"]
        assert d["needed_missing"] == []
        time.sleep(1.1)
        r2 = S.post(f"{API}/extras/real_name_fix/install")
        assert r2.status_code == 200, r2.text
        assert r2.json()["backup"] != j["backup"]
        assert (PF / "extras-backups" / r2.json()["backup"] / "2700" / "lnc" / "all" / "fmcc_club_names.lnc").exists()
        assert OURS.exists()

    def test_rnf_install_same_second(self):
        # two quick installs in the same second must not 500
        codes = [S.post(f"{API}/extras/real_name_fix/install").status_code for _ in range(2)]
        assert all(c == 200 for c in codes), codes

    def test_kits_install(self):
        r = S.post(f"{API}/extras/kits/install")
        assert r.status_code == 200, r.text
        assert "unpacked" in r.json()["message"]  # backup present on reinstall
        _, it = _items()
        assert it["kits"]["found"] is True
        assert (PF / "graphics" / "Sample Kits" / "config.xml").exists()

    def test_logos_409(self):
        r = S.post(f"{API}/extras/logos/install")
        assert r.status_code == 409
        assert "Downloads" in r.json()["detail"]

    @pytest.mark.parametrize("k", ["fmos", "fmst26", "fmdossier", "nope"])
    def test_apps_404(self, k):
        assert S.post(f"{API}/extras/{k}/install").status_code == 404

    def test_ng_regens_sample(self):
        r = S.post(f"{API}/extras/ng_regens/install")
        assert r.status_code == 200
        assert "SAMPLE" in r.json()["message"] and "nothing was started" in r.json()["message"]

    def test_audit_entries(self):
        r = S.get(f"{API}/audit")
        if r.status_code != 200:
            pytest.skip("no audit endpoint")
        rows = r.json() if isinstance(r.json(), list) else r.json().get("items", [])
        assert any(x.get("source") == "extras" for x in rows)


# ---------- updates ----------
class TestUpdates:
    def test_updates(self):
        r = S.get(f"{API}/extras/updates", timeout=40)
        assert r.status_code == 200
        d = r.json()
        assert d["checked_at"]
        ng = d["items"]["ng_regens"]
        print("ng_regens:", ng)
        print("rnf:", d["items"]["real_name_fix"])
        assert ng["how"] in ("auto", "manual")
        if ng["how"] == "auto":
            assert ng["latest"] and "v" in ng["latest"]
        rnf = d["items"]["real_name_fix"]
        assert rnf["how"] == "manual" and rnf["latest"] is None and rnf["message"]
