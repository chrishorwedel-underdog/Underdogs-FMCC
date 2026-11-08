# FMCC Stage 9: Licensing fix (scan .lnc fix files + logo packs, import, apply, undo, manual club/comp fixes, founded via Game changes)
import os
from pathlib import Path

import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
L = f"{API}/editor/licensing"
S = requests.Session()
CTX = {}
LNC = Path("/app/backend/preview_fm/game/data/database/db/2700/lnc/all/fmcc_club_names.lnc")
FIX_NAME = "TEST_real_fix.lnc"
FIX = ('"CLUB_LONG_NAME_CHANGE" 900000 "TEST Real Sample Club" ""\n"CLUB_SHORT_NAME_CHANGE" 900000 "TEST Real" ""\n'
       '"COMP_LONG_NAME_CHANGE" 950555 "TEST Real Cup" ""\n"COMP_SHORT_NAME_CHANGE" 950555 "TEST Cup" ""\n')


def scan():
    r = S.get(f"{L}/scan")
    assert r.status_code == 200, r.text
    return r.json()


def lnc_text():
    return LNC.read_text() if LNC.exists() else ""


class TestLicensing:
    def test_00_setup(self):
        st = S.get(f"{API}/state").json()
        if not st["setup_complete"]:
            r = S.post(f"{API}/setup/complete", json={"name": "TEST_career", "club_name": "Sample Club FC", "edition": "FM27", "save_folder": "C:\\TEST_folder"})
            assert r.status_code == 200, r.text
        assert S.get(f"{API}/state").json()["career"]["edition"] == "FM27"

    # scan: sample fix file (active), sample logo pack, 3 clubs + comp 950001
    def test_01_scan_sample(self):
        d = scan()
        assert d["desktop"] is False
        f = next(x for x in d["files"] if x["name"] == "sample_real_names_fix.lnc")
        assert f["active"] is True and f["clubs"] == 3 and f["comps"] == 1
        assert {"name": "Sample Logo Pack", "logos": 2} in d["logo_packs"]
        active = [c for c in d["clubs"] if c["source"] == "sample_real_names_fix.lnc"]
        assert len(active) == 3 and all(c["active_in_fm"] and c["in_save"] for c in active)
        assert sum(1 for c in active if c["logo_pack"] == "Sample Logo Pack") == 2
        comp = next(c for c in d["comps"] if c["uid"] == 950001)
        assert comp["active_in_fm"] is True

    # import validation
    def test_02_import_bad(self):
        r = S.post(f"{L}/import", files={"file": ("TEST_fix.txt", b'"CLUB_LONG_NAME_CHANGE" 1 "x" ""', "text/plain")})
        assert r.status_code == 422
        r = S.post(f"{L}/import", files={"file": ("TEST_empty.lnc", b"# nothing here\nhello\n", "application/octet-stream")})
        assert r.status_code == 422
        r = S.post(f"{L}/import", files={"file": ("fmcc_club_names.lnc", FIX.encode(), "application/octet-stream")})
        assert r.status_code == 422

    def test_03_import_ok(self):
        r = S.post(f"{L}/import", files={"file": (FIX_NAME, FIX.encode(), "application/octet-stream")})
        assert r.status_code == 200, r.text
        assert r.json()["name"] == FIX_NAME
        d = scan()
        f = next(x for x in d["files"] if x["name"] == FIX_NAME)
        assert f["active"] is False and f["clubs"] == 1 and f["comps"] == 1
        c = next(x for x in d["clubs"] if x["uid"] == 900000)
        assert c["source"] == FIX_NAME and c["current"] == "Sample Club FC" and c["real_long"] == "TEST Real Sample Club"
        assert c["unlicensed"] is True and c["applied"] is False and c["active_in_fm"] is False
        k = next(x for x in d["comps"] if x["uid"] == 950555)
        assert k["active_in_fm"] is False and k["applied"] is False

    # apply + persistence + 409 on re-apply
    def test_04_apply_club(self):
        r = S.post(f"{L}/apply", json={"clubs": [900000], "comps": []})
        assert r.status_code == 200, r.text
        assert r.json()["applied"] == 1
        c = next(x for x in scan()["clubs"] if x["uid"] == 900000)
        assert c["applied"] is True
        row = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == 900000)
        assert row["rename"]["long"] == "TEST Real Sample Club" and row["rename"]["short"] == "TEST Real"
        assert '"CLUB_LONG_NAME_CHANGE" 900000 "TEST Real Sample Club" ""' in lnc_text()
        assert S.post(f"{L}/apply", json={"clubs": [900000], "comps": []}).status_code == 409

    def test_05_apply_active_is_noop(self):
        d = scan()
        act = [c["uid"] for c in d["clubs"] if c["active_in_fm"]]
        r = S.post(f"{L}/apply", json={"clubs": act, "comps": [950001]})
        assert r.status_code == 409 and "Nothing new to apply" in r.text

    def test_06_apply_comp_and_undo(self):
        before = S.get(f"{API}/editor/status").json()["files"]["lnc"]["lines"]
        r = S.post(f"{L}/apply", json={"clubs": [], "comps": [950555]})
        assert r.status_code == 200 and r.json()["applied"] == 1
        assert '"COMP_LONG_NAME_CHANGE" 950555 "TEST Real Cup" ""' in lnc_text()
        assert S.get(f"{API}/editor/status").json()["files"]["lnc"]["lines"] == before + 2
        assert next(x for x in scan()["comps"] if x["uid"] == 950555)["applied"] is True
        assert S.delete(f"{L}/comp/950555").status_code == 200
        assert " 950555 " not in lnc_text()

    def test_07_undo_club(self):
        assert S.delete(f"{L}/name/900000").status_code == 200
        c = next(x for x in scan()["clubs"] if x["uid"] == 900000)
        assert c["applied"] is False
        row = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == 900000)
        assert not row["rename"]
        assert '900000 "TEST Real Sample Club"' not in lnc_text()
        assert S.delete(f"{L}/name/900000").status_code == 409
        assert S.delete(f"{L}/bogus/900000").status_code == 404

    def test_08_remove_import(self):
        assert S.delete(f"{L}/import/{FIX_NAME}").status_code == 200
        assert not any(x["name"] == FIX_NAME for x in scan()["files"])
        assert S.delete(f"{L}/import/{FIX_NAME}").status_code == 404
        assert S.delete(f"{L}/import/..%2F..%2Fgame%2Fx.lnc").status_code in (404, 405)

    # manual club fix: validation
    def test_09_manual_validation(self):
        cl = S.get(f"{API}/editor/clubs").json()
        c = next(x for x in cl if not x["rename"] and x["uid"] not in (900000, 978596, 999023, 964833))
        CTX["club"] = c
        u = f"{L}/manual/club/{c['uid']}"
        assert S.post(u, json={"long": "TEST Real", "short": "TEST", "stadium_id": 12399}).status_code == 422
        assert S.post(u, json={"long": 'TEST "Real"', "short": "TEST"}).status_code == 422
        assert S.post(u, json={"long": "TEST Real", "short": "TEST", "founded": 1700}).status_code == 422
        assert S.post(f"{L}/manual/club/123", json={"long": "TEST Real", "short": "TEST"}).status_code == 404
        # nothing should have been saved by the failed calls
        assert not next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == c["uid"])["rename"]

    def test_10_manual_save(self):
        c = CTX["club"]
        f = {x["key"]: x for x in S.get(f"{API}/editor/clubs/{c['uid']}/attributes").json()["fields"]}
        assert "founded" in f and f["founded"]["label"] == "Year founded"
        year = 1901 if f["founded"]["value"] != 1901 else 1902
        r = S.post(f"{L}/manual/club/{c['uid']}", json={"long": "TEST Manual Real FC", "short": "TEST Manual", "founded": year,
                                                         "stadium_id": 12399, "stadium_name": "TEST Real Park"})
        assert r.status_code == 200, r.text
        assert r.json()["founded_queued"] is True
        t = lnc_text()
        assert f'"CLUB_LONG_NAME_CHANGE" {c["uid"]} "TEST Manual Real FC" ""' in t
        assert '"STADIUM_NAME_CHANGE" 12399 "TEST Real Park" ""' in t
        q = [x for x in S.get(f"{API}/changes").json()["queued"] if x.get("entity") == "club" and x["unique_id"] == c["uid"] and x["field"] == "founded"]
        assert len(q) == 1 and q[0]["target"] == year
        CTX["queued"] = q[0]["id"]
        row = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == c["uid"])
        assert row["rename"]["long"] == "TEST Manual Real FC"

    def test_11_manual_cleanup(self):
        c = CTX["club"]
        assert S.post(f"{API}/changes/reject", json={"ids": [CTX["queued"]]}).json()["rejected"] == 1
        assert S.delete(f"{L}/name/{c['uid']}").status_code == 200
        assert S.delete(f"{L}/stadium/12399").status_code == 200
        t = lnc_text()
        assert "TEST Manual Real FC" not in t and "12399" not in t

    def test_12_manual_comp(self):
        before = S.get(f"{API}/editor/status").json()["files"]["lnc"]["lines"]
        r = S.post(f"{L}/manual/comp/950777", json={"long": "TEST Manual League", "short": "TEST ML"})
        assert r.status_code == 200, r.text
        after = S.get(f"{API}/editor/status").json()["files"]["lnc"]["lines"]
        assert after == before + 2
        assert '"COMP_SHORT_NAME_CHANGE" 950777 "TEST ML" ""' in lnc_text()
        assert S.post(f"{L}/manual/comp/950777", json={"long": 'TEST "x"', "short": "TEST"}).status_code == 422
        assert S.delete(f"{L}/comp/950777").status_code == 200
        assert S.get(f"{API}/editor/status").json()["files"]["lnc"]["lines"] == before
