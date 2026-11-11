# Shortlist to FM (send-to-fm -> changes queue -> preview/apply/undo) and Tactic Fit / Tactic import APIs
import json
import os
import time
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
API = f"{BASE_URL}/api"
IDS = [30500011, 30500012]


def no_ca_pa(obj):
    s = json.dumps(obj)
    return '"ca"' not in s and '"pa"' not in s


def my_changes(ids):
    q = requests.get(f"{API}/changes", timeout=30).json()["queued"]
    return [c for c in q if c.get("entity") == "shortlist" and c["unique_id"] in ids]


# ---------- Shortlist to FM ----------
class TestShortlistToFM:
    state = {}

    def test_01_send_queues(self):
        r = requests.post(f"{API}/scouting/send-to-fm", json={"ids": IDS}, timeout=30)
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["queued"] == 2 and d["already"] == 0 and d["not_found"] == 0

    def test_02_resend_already(self):
        d = requests.post(f"{API}/scouting/send-to-fm", json={"ids": IDS}, timeout=30).json()
        assert d["queued"] == 0 and d["already"] == 2

    def test_03_partial_unknown(self):
        d = requests.post(f"{API}/scouting/send-to-fm", json={"ids": [IDS[0], 99999999]}, timeout=30).json()
        assert d["queued"] == 0 and d["already"] == 1 and d["not_found"] == 1

    def test_04_unknown_404_and_empty_422(self):
        assert requests.post(f"{API}/scouting/send-to-fm", json={"ids": [99999999]}, timeout=30).status_code == 404
        assert requests.post(f"{API}/scouting/send-to-fm", json={"ids": []}, timeout=30).status_code == 422

    def test_05_listed_in_changes(self):
        d = requests.get(f"{API}/changes", timeout=30).json()
        assert d["sources"]["shortlist"] == "Shortlist to FM"
        mine = my_changes(IDS)
        assert len(mine) == 2
        assert all(c["source"] == "shortlist" and c["label"] == "Add to FM shortlist" and c["status"] == "queued" for c in mine)
        TestShortlistToFM.state["ids"] = [c["id"] for c in mine]

    def test_06_preview_apply(self):
        ids = TestShortlistToFM.state["ids"]
        p = requests.post(f"{API}/changes/preview", json={"ids": ids}, timeout=30)
        assert p.status_code == 200, p.text
        pd = p.json()
        assert pd["ready"] is True, pd["checks"]
        assert len(pd["rows"]) == 2 and all(r["current"] == 0 and r["new"] == 1 for r in pd["rows"])
        a = requests.post(f"{API}/changes/apply", json={"preview_id": pd["preview_id"]}, timeout=30)
        assert a.status_code == 200, a.text
        bid = a.json()["batch_id"]
        TestShortlistToFM.state["batch"] = bid
        for _ in range(30):
            b = requests.get(f"{API}/changes/batches/{bid}", timeout=30).json()
            if b["status"] == "done":
                break
            time.sleep(0.5)
        assert b["status"] == "done" and b["done"] == 2
        assert all(c["status"] == "applied" and c["new_value"] == 1 for c in b["changes"])
        # reuse of preview rejected
        assert requests.post(f"{API}/changes/apply", json={"preview_id": pd["preview_id"]}, timeout=30).status_code == 409

    def test_07_resend_after_applied(self):
        d = requests.post(f"{API}/scouting/send-to-fm", json={"ids": IDS}, timeout=30).json()
        assert d["queued"] == 0 and d["already"] == 2

    def test_08_undo(self):
        bid = TestShortlistToFM.state["batch"]
        r = requests.post(f"{API}/changes/batches/{bid}/undo", timeout=30)
        assert r.status_code == 200 and r.json()["undone"] == 2
        b = requests.get(f"{API}/changes/batches/{bid}", timeout=30).json()
        assert b["status"] == "undone" and all(c["status"] == "undone" for c in b["changes"])


# ---------- Tactic fit ----------
class TestTacticFit:
    created = []

    def test_list_tactics(self):
        t = requests.get(f"{API}/squad/tactics", timeout=30).json()
        save = [x for x in t if x.get("from_save")]
        assert save and save[0]["id"] == "save-0"

    def _check(self, d):
        assert len(d["slots"]) >= 10
        for s in d["slots"]:
            assert {"role", "role_options", "ranked", "score"} <= set(s)
            assert any(o["key"] == s["role"] for o in s["role_options"])
            r = s["ranked"]
            keys = [(-x["natural"], -x["rating"]) for x in r]
            assert keys == sorted(keys)
        n = len(d["slots"][0]["ranked"])
        assert all(len(s["ranked"]) == n for s in d["slots"])
        assert len(d["gaps"]) == 3
        assert no_ca_pa(d)

    def test_fit_default(self):
        r = requests.get(f"{API}/squad/tactic-fit", timeout=30)
        assert r.status_code == 200
        self._check(r.json())

    def test_fit_save1(self):
        d = requests.get(f"{API}/squad/tactic-fit", params={"tactic": "save-1"}, timeout=30).json()
        assert d["tactic"]["id"] == "save-1" and d["formation_key"] == d["tactic"]["formation"]
        self._check(d)

    def test_fit_formation_picks(self):
        d = requests.get(f"{API}/squad/tactic-fit", params={"formation": "442", "picks": "STR:af"}, timeout=30).json()
        assert d["formation_key"] == "442" and d["tactic"] is None
        self._check(d)
        print("slots", [(s["slot"], s["role"]) for s in d["slots"]])
        strs = [s for s in d["slots"] if s["slot"] == "STR"]
        if strs:
            assert strs[0]["role"] == "af"

    def test_unknown_404(self):
        assert requests.get(f"{API}/squad/tactic-fit", params={"tactic": "nope"}, timeout=30).status_code == 404
        assert requests.get(f"{API}/squad/tactic-fit", params={"formation": "999"}, timeout=30).status_code == 404

    def test_build_save_delete(self):
        fit = requests.get(f"{API}/squad/tactic-fit", params={"formation": "442"}, timeout=30).json()
        roles = {s["slot"]: s["role"] for s in fit["slots"]}
        slot = fit["slots"][-1]
        alt = next((o["key"] for o in slot["role_options"] if o["key"] != slot["role"]), slot["role"])
        roles[slot["slot"]] = alt
        r = requests.post(f"{API}/squad/tactics", json={"formation": "442", "name": "TEST_built", "roles": roles}, timeout=30)
        assert r.status_code == 200, r.text
        t = r.json()
        self.created.append(t["id"])
        assert t["name"] == "TEST_built" and t["roles"][slot["slot"]] == alt
        lst = requests.get(f"{API}/squad/tactics", timeout=30).json()
        assert any(x["id"] == t["id"] for x in lst)
        d = requests.get(f"{API}/squad/tactic-fit", params={"tactic": t["id"]}, timeout=30).json()
        assert next(s for s in d["slots"] if s["slot"] == slot["slot"])["role"] == alt
        assert requests.delete(f"{API}/squad/tactics/{t['id']}", timeout=30).status_code == 200
        assert requests.delete(f"{API}/squad/tactics/{t['id']}", timeout=30).status_code == 404
        assert requests.get(f"{API}/squad/tactic-fit", params={"tactic": t["id"]}, timeout=30).status_code == 404

    def test_bad_formation_422(self):
        assert requests.post(f"{API}/squad/tactics", json={"formation": "999"}, timeout=30).status_code == 422

    def test_import(self):
        r = requests.post(f"{API}/squad/tactics/import", files={"file": ("TEST_imp.fmf", b"xx shape 4-2-3-1 yy", "application/octet-stream")}, timeout=30)
        assert r.status_code == 200, r.text
        t = r.json()
        self.created.append(t["id"])
        assert t["formation"] == "4231" and t["name"] == "TEST_imp"
        assert requests.delete(f"{API}/squad/tactics/{t['id']}", timeout=30).status_code == 200

    def test_import_bad(self):
        assert requests.post(f"{API}/squad/tactics/import", files={"file": ("x.fmf", b"nothing here", "application/octet-stream")}, timeout=30).status_code == 422
        assert requests.post(f"{API}/squad/tactics/import", files={"file": ("x.txt", b"4-4-2", "text/plain")}, timeout=30).status_code == 422
