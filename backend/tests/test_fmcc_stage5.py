# FMCC Stage 5: setup (FM27), notices, updates (BepInEx 6), auto-read setting, Connections (simulated MatchLens install/check/remove/dashboard),
# matches after install, Check my save, DP + Breakout queueing, game-change batches (preview/apply/409/partial/undo/detail).
# Precondition: EMPTY DB (first-run). Run with `-n 0`.
import os
import time
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
CTX = {}


def wait_batch(bid, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        b = S.get(f"{API}/changes/batches/{bid}").json()
        if b["status"] != "running":
            return b
        time.sleep(0.5)
    return b


class TestStage5:
    def test_01_setup(self):
        if S.get(f"{API}/state").json()["setup_complete"]:
            pytest.skip("DB not fresh")
        r = S.post(f"{API}/setup/complete", json={"name": "Sample career", "club_name": "Sample Club FC", "edition": "FM27", "save_folder": "C:\\TEST_folder"})
        assert r.status_code == 200, r.text
        assert r.json()["career"]["edition"] == "FM27"
        st = S.get(f"{API}/state").json()
        assert st["setup_complete"] is True and st["auto_read_saves"] is True

    def test_02_notices_and_updates(self):
        assert S.get(f"{API}/notices").json() == []
        ups = S.get(f"{API}/updates").json()
        txt = str(ups)
        assert "BepInEx 6" in txt and "6.0.0-be" in txt
        assert "5.4" not in txt

    def test_03_auto_read_toggle(self):
        assert S.put(f"{API}/settings/auto-read", json={"auto_read": False}).status_code == 200
        assert S.get(f"{API}/state").json()["auto_read_saves"] is False
        assert S.put(f"{API}/settings/auto-read", json={"auto_read": True}).status_code == 200
        assert S.get(f"{API}/state").json()["auto_read_saves"] is True

    def test_04_connections_initial(self):
        d = S.get(f"{API}/connections").json()
        assert d["desktop"] is False and d["edition"] == "FM27" and d["target_version"] == "v0.7.1"
        assert d["bepinex"] is False and d["plugin"] is False and d["editor_supported"] is True
        assert S.post(f"{API}/connections/matchlens/check").status_code == 409
        assert S.post(f"{API}/connections/matchlens/remove").status_code == 409

    def test_05_install_check_dashboard(self):
        r = S.post(f"{API}/connections/matchlens/install")
        assert r.status_code == 200 and r.json()["simulated"] is True and r.json()["fmmatchlens"] == "v0.7.1"
        assert S.post(f"{API}/connections/matchlens/install").status_code == 409
        d = S.get(f"{API}/connections").json()
        assert d["bepinex"] and d["plugin"] and d["dashboard"]
        c = S.post(f"{API}/connections/matchlens/check")
        assert c.status_code == 200 and c.json()["working"] == "ok"
        assert S.get(f"{API}/connections").json()["matchlens"]["working"] == "ok"
        dash = S.post(f"{API}/connections/matchlens/dashboard")
        assert dash.status_code == 409 and "Windows" in dash.json()["detail"]

    def test_06_read_save_matches_check(self):
        r = S.post(f"{API}/saves/read")
        assert r.status_code == 200, r.text
        ms = S.get(f"{API}/matches").json()["matches"]
        assert len(ms) > 0
        saves = S.get(f"{API}/saves").json()
        nos = sorted(s["save_no"] for s in (saves if isinstance(saves, list) else saves.get("saves", [])))
        CTX["save_nos"] = nos
        ck = S.get(f"{API}/saves/{nos[-1]}/check").json()
        assert ck["players"] > 0 and ck["club_name"] and ck["game_date"] and ck["first"] is False
        assert isinstance(ck["new_players"], list) and isinstance(ck["left"], list)
        assert S.get(f"{API}/saves/9999/check").status_code == 404

    def test_07_dp_run_hidden(self):
        r = S.post(f"{API}/dp/run", json={})
        assert r.status_code == 200, r.text
        assert r.json()["queued"] > 0
        q = S.get(f"{API}/changes").json()
        assert q["live"] is False and q["auto_allowed"] is True and q["editor_ok"] is True
        dp = [x for x in q["queued"] if x["source"] == "dp"]
        assert dp and all(x["delta"] is None for x in dp)
        CTX["dp_ids"] = [x["id"] for x in dp]

    def test_08_breakout_flow(self):
        b = S.get(f"{API}/breakout").json()
        cand = next((c for c in b["candidates"] if c["category"]), None)
        if not cand:
            pytest.skip("No breakout candidate with category")
        r = S.post(f"{API}/breakout/review", json={"unique_id": cand["unique_id"], "decision": "provisional"})
        assert r.status_code == 200, r.text
        f = S.post(f"{API}/breakout/finalise")
        assert f.status_code == 200 and f.json()["official"] >= 1
        q = S.get(f"{API}/changes").json()
        assert any(x["source"] == "breakout" for x in q["queued"])

    def test_09_preview_and_409(self):
        ids = CTX["dp_ids"][:2]
        p = S.post(f"{API}/changes/preview", json={"ids": ids})
        assert p.status_code == 200, p.text
        d = p.json()
        assert d["preview_id"] and d["ready"] is True and len(d["rows"]) == 2
        assert all("current" in r and "new" in r for r in d["rows"])
        assert {c["key"] for c in d["checks"]} >= {"preview", "backup", "dupes"}
        assert S.post(f"{API}/changes/preview", json={"ids": ["nope"]}).status_code == 409
        a = S.post(f"{API}/changes/apply", json={"preview_id": d["preview_id"]})
        assert a.status_code == 200 and a.json()["total"] == 2
        CTX["bid"] = a.json()["batch_id"]
        assert S.post(f"{API}/changes/apply", json={"preview_id": d["preview_id"]}).status_code == 409
        # applied ids can't be previewed again
        assert S.post(f"{API}/changes/preview", json={"ids": ids}).status_code == 409

    def test_10_batch_done_detail_partial(self):
        b = wait_batch(CTX["bid"])
        assert b["status"] == "done" and b["done"] == 2
        assert b["approved_by"] == "Manager (browser preview)"
        assert len(b["changes"]) == 2 and all(c["status"] == "applied" for c in b["changes"])
        q = S.get(f"{API}/changes").json()
        qids = {x["id"] for x in q["queued"]}
        assert not (set(CTX["dp_ids"][:2]) & qids)
        assert set(CTX["dp_ids"][2:]) <= qids  # only ticked rows applied

    def test_11_undo(self):
        u = S.post(f"{API}/changes/batches/{CTX['bid']}/undo")
        assert u.status_code == 200 and u.json()["undone"] == 2
        b = S.get(f"{API}/changes/batches/{CTX['bid']}").json()
        assert b["status"] == "undone" and all(c["status"] == "undone" for c in b["changes"])
        assert S.post(f"{API}/changes/batches/{CTX['bid']}/undo").status_code == 409

    def test_12_audit_record(self):
        a = S.get(f"{API}/audit").json()
        actions = {x["action"] for x in a}
        assert {"batch approved", "applied", "batch undone", "installed"} <= actions

    def test_13_backups(self):
        bk = S.get(f"{API}/backups").json()
        assert len(bk) >= 1
