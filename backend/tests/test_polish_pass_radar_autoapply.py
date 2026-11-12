# FMCC Polish Pass: radar compare, auto-apply of Editor/Punish club edits, exact rules impact counts
import os
import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/") + "/api"
S = requests.Session()
CTX = {}


def _players():
    if "rows" not in CTX:
        CTX["rows"] = S.post(f"{BASE}/scout/players", json={"limit": 300}).json()["rows"]
    return CTX["rows"]


def _wait_done(bid):
    import time
    for _ in range(20):
        b = S.get(f"{BASE}/changes/batches/{bid}").json()
        if b["status"] not in ("running", "approved", "applying"):
            return b
        time.sleep(0.5)
    return b


# ---------- Radar compare ----------
class TestRadarCompare:
    def test_two_players_shape(self):
        rows = [r for r in _players() if (r.get("minutes") or 0) > 900]
        ids = [rows[0]["unique_id"], rows[1]["unique_id"]]
        r = S.post(f"{BASE}/scout/radar-compare", json={"ids": ids, "view": "full"})
        assert r.status_code == 200, r.text
        d = r.json()
        for k in ("role", "roles", "keys", "labels", "players", "verdict"):
            assert k in d
        assert d["role"] in d["roles"] and 1 <= len(d["keys"]) <= 6
        assert set(d["labels"]) == set(d["keys"])
        assert [p["unique_id"] for p in d["players"]] == ids
        for p in d["players"]:
            assert set(p["role"]) == set(d["keys"])
            assert isinstance(p["phases"], dict)
            assert "ca" not in p and "pa" not in p
        assert '"ca"' not in r.text and '"pa"' not in r.text
        v = d["verdict"]
        assert v and v["leader"] in ids and isinstance(v["text"], str) and len(v["gaps"]) <= 2
        for g in v["gaps"]:
            assert {"key", "label", "a", "b"} <= set(g)

    def test_role_param_and_four(self):
        rows = [r for r in _players() if (r.get("minutes") or 0) > 900][:4]
        ids = [x["unique_id"] for x in rows]
        roles = S.post(f"{BASE}/scout/radar-compare", json={"ids": ids[:2]}).json()["roles"]
        role = roles[-1]
        d = S.post(f"{BASE}/scout/radar-compare", json={"ids": ids, "role": role, "view": "fair"}).json()
        assert d["role"] == role and len(d["players"]) == 4

    def test_bad_counts_422(self):
        ids = [x["unique_id"] for x in _players()[:5]]
        assert S.post(f"{BASE}/scout/radar-compare", json={"ids": ids[:1]}).status_code == 422
        assert S.post(f"{BASE}/scout/radar-compare", json={"ids": ids}).status_code == 422
        assert S.post(f"{BASE}/scout/radar-compare", json={"ids": ids[:2], "view": "bogus"}).status_code == 422

    def test_unknown_uid(self):
        ids = [_players()[0]["unique_id"], 999999999]
        r = S.post(f"{BASE}/scout/radar-compare", json={"ids": ids})
        print("unknown uid ->", r.status_code, r.text[:150])
        assert r.status_code in (404, 422)

    def test_zero_minute_player(self):
        low = sorted(_players(), key=lambda x: x.get("minutes") or 0)[0]
        hi = [r for r in _players() if (r.get("minutes") or 0) > 900][0]
        r = S.post(f"{BASE}/scout/radar-compare", json={"ids": [hi["unique_id"], low["unique_id"]]})
        assert r.status_code == 200, r.text
        print("low-min player role:", r.json()["players"][1]["role"], "verdict:", r.json()["verdict"])


# ---------- Auto-apply: Editor clubs + Punish ----------
class TestAutoApply:
    def _club(self):
        cl = S.get(f"{BASE}/editor/clubs").json()
        cl = cl.get("clubs", cl) if isinstance(cl, dict) else cl
        return cl[0]

    def test_editor_club_autoapply_and_undo(self):
        assert S.get(f"{BASE}/features").json()["review_changes"] is False
        uid = self._club()["uid"]
        f = {x["key"]: x for x in S.get(f"{BASE}/editor/clubs/{uid}/attributes").json()["fields"]}
        old = f["training"]["value"]
        new = 5 if old != 5 else 6
        before = {b["id"] for b in S.get(f"{BASE}/changes").json()["batches"]}
        q = S.post(f"{BASE}/editor/clubs/{uid}/attributes", json={"values": {"training": new}})
        assert q.status_code == 200, q.text
        d = q.json()
        assert d["queued"] == 1 and d["auto_applied"] is True and d["batch_id"]
        ch = S.get(f"{BASE}/changes").json()
        assert d["batch_id"] in {b["id"] for b in ch["batches"]} - before
        assert not [x for x in ch["queued"] if x.get("entity") == "club" and x["unique_id"] == uid]
        b = _wait_done(d["batch_id"])
        f2 = {x["key"]: x["value"] for x in S.get(f"{BASE}/editor/clubs/{uid}/attributes").json()["fields"]}
        assert f2["training"] == new
        olds = [c.get("old_value") for c in b["changes"]]
        if None in olds:
            # BUG: auto-applied club edits store old_value None, and undo would write None into the club. Restore by re-queueing the old value instead.
            S.post(f"{BASE}/editor/clubs/{uid}/attributes", json={"values": {"training": old}})
            pytest.fail(f"auto-applied club change has old_value None -> undo would blank the value: {olds}")
        u = S.post(f"{BASE}/changes/batches/{d['batch_id']}/undo")
        assert u.status_code == 200 and u.json()["undone"] == 1
        f3 = {x["key"]: x["value"] for x in S.get(f"{BASE}/editor/clubs/{uid}/attributes").json()["fields"]}
        assert f3["training"] == old

    def test_editor_review_on_waits(self):
        uid = self._club()["uid"]
        f = {x["key"]: x for x in S.get(f"{BASE}/editor/clubs/{uid}/attributes").json()["fields"]}
        old = f["training"]["value"]
        new = 5 if old != 5 else 6
        try:
            assert S.put(f"{BASE}/features/review", json={"on": True}).status_code == 200
            d = S.post(f"{BASE}/editor/clubs/{uid}/attributes", json={"values": {"training": new}}).json()
            assert d["queued"] == 1 and d.get("auto_applied") is False
            mine = [x for x in S.get(f"{BASE}/changes").json()["queued"] if x.get("entity") == "club" and x["unique_id"] == uid]
            assert mine
            CTX["reject"] = [x["id"] for x in mine]
        finally:
            if CTX.get("reject"):
                S.post(f"{BASE}/changes/reject", json={"ids": CTX["reject"]})
            S.put(f"{BASE}/features/review", json={"on": False})
        assert S.get(f"{BASE}/features").json()["review_changes"] is False

    def test_punish_autoapply_and_undo(self):
        clubs = S.get(f"{BASE}/punish/clubs", params={"q": "AC Valdora"}).json()
        c = clubs[0]
        rep0 = {x["key"]: x["value"] for x in S.get(f"{BASE}/editor/clubs/{c['uid']}/attributes").json()["fields"]}["reputation"]
        r = S.post(f"{BASE}/punish", json={"club_uid": c["uid"], "penalties": {"reputation": {"amount": 500}}, "name": "TEST_punish"})
        assert r.status_code == 200, r.text
        pid = r.json()["pid"]
        try:
            q = S.post(f"{BASE}/punish/{pid}/queue")
            assert q.status_code == 200, q.text
            d = q.json()
            print("punish queue ->", d)
            assert d["queued"] and d["auto_applied"] is True and d["batch_id"]
            b = _wait_done(d["batch_id"])
            olds = [c.get("old_value") for c in b["changes"]]
            if None in olds:
                S.post(f"{BASE}/editor/clubs/{c['uid']}/attributes", json={"values": {"reputation": rep0}})
                pytest.fail(f"punish auto-applied change has old_value None -> undo blanks reputation: {olds} (restored via editor)")
            u = S.post(f"{BASE}/changes/batches/{d['batch_id']}/undo")
            assert u.status_code == 200 and u.json()["undone"] >= 1
        finally:
            S.delete(f"{BASE}/punish/{pid}")


# ---------- Rules impact exact counts ----------
class TestRulesImpact:
    @pytest.mark.parametrize("module,key,val", [("squad", "target_minutes", 0), ("squad", "max_senior", 11), ("development", "needs_pct", 100), ("development", "default_target", 1000)])
    def test_impact(self, module, key, val):
        cur = S.get(f"{BASE}/rules/{module}").json()["data"]
        z = S.post(f"{BASE}/rules/{module}/impact", json={"data": cur})
        assert z.status_code == 200, z.text
        assert z.json()["affected"] == 0
        draft = {"params": dict(cur["params"]) | {key: val}}
        r = S.post(f"{BASE}/rules/{module}/impact", json={"data": draft})
        assert r.status_code == 200, r.text
        d = r.json()
        print(module, key, val, d)
        assert isinstance(d["affected"], int) and d["population"] >= d["affected"]
        assert d["affected"] > 0
        assert "ca" not in d and "pa" not in d

    def test_impact_invalid(self):
        cur = S.get(f"{BASE}/rules/squad").json()["data"]
        r = S.post(f"{BASE}/rules/squad/impact", json={"data": {"params": dict(cur["params"]) | {"max_youth": 99}}})
        assert r.status_code in (400, 422)
