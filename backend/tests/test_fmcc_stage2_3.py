# FMCC Stage 2 (planning modules + rules) and Stage 3 (game change queue, batches, audit, undo) backend regression.
# Sequential shared state in ONE class. Precondition: EMPTY DB (fresh setup). Run with `-n 0`.
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


def wait_batches(timeout=40):
    end = time.time() + timeout
    while time.time() < end:
        bs = S.get(f"{API}/changes").json()["batches"]
        if all(b["status"] not in ("running",) for b in bs):
            return bs
        time.sleep(0.5)
    return S.get(f"{API}/changes").json()["batches"]


def squad_player(uid):
    return next((p for p in S.get(f"{API}/squad").json()["players"] if p["unique_id"] == uid), None)


class TestStage23:
    # --- setup ---
    def test_01_setup_and_read_saves(self):
        st = S.get(f"{API}/state").json()
        if st["setup_complete"]:
            pytest.skip("DB not fresh")
        r = S.post(f"{API}/setup/complete", json={"name": "TEST_S23", "club_name": "TEST Club", "edition": "FM27", "save_folder": "C:\\FM27"})
        assert r.status_code == 200
        for _ in range(3):
            assert S.post(f"{API}/saves/read").status_code == 200
        assert len(S.get(f"{API}/saves").json()) == 4

    # --- squad planning ---
    def test_02_squad_plan_433_4231(self):
        for f in ("433", "4231"):
            d = S.get(f"{API}/squad/plan", params={"formation": f}).json()
            slots = [s["key"] for s in d["formation"]["slots"]]
            assert len(slots) == 11 and len(d["best"]["slots"]) == 11 and len(d["dev"]["slots"]) == 11
            assert len(set(d["best"]["slots"].values())) == 11
            CTX[f] = d
        assert set(CTX["433"]["best"]["slots"]) != set(CTX["4231"]["best"]["slots"])
        d = CTX["433"]
        u21 = [u for u in d["dev"]["slots"].values() if d["players"][str(u)]["u21"]]
        assert len(u21) <= d["rules"]["max_youth"]
        assert d["dev"]["youth"], "Dev XI picked no youth"
        assert d["dev"]["slots"] != d["best"]["slots"]
        assert all(0 <= r["rating"] <= 100 for v in d["depth"].values() for r in v)
        assert len(d["weak"]) == 11

    def test_03_lineup_save_and_conflicts(self):
        d = CTX["433"]
        body = {"formation": "433", "kind": "best", "slots": d["best"]["slots"], "based_on_save_no": d["save_no"], "expected_revision": 0}
        r = S.post(f"{API}/lineups", json=body)
        assert r.status_code == 200 and r.json()["revision"] == 1
        assert S.post(f"{API}/lineups", json=body).status_code == 409  # wrong expected_revision
        assert S.post(f"{API}/lineups", json=body | {"based_on_save_no": 0, "expected_revision": 1}).status_code == 409
        slots = dict(d["best"]["slots"])
        keys = list(slots)
        slots[keys[1]] = slots[keys[0]]
        assert S.post(f"{API}/lineups", json=body | {"slots": slots, "expected_revision": 1}).status_code == 422
        gk = [k for k in keys if k.startswith("GK")][0]
        st = [k for k in keys if k.startswith("ST")][0]
        bad = dict(d["best"]["slots"])
        bad[gk], bad[st] = bad[st], bad[gk]
        r = S.post(f"{API}/lineups", json=body | {"slots": bad, "expected_revision": 1})
        assert r.status_code == 422 and "can't play" in r.json()["detail"]
        assert S.get(f"{API}/squad/plan").json()["saved"]["revision"] == 1

    def test_04_registration_and_squad_roles(self):
        d = S.get(f"{API}/squad/registration").json()
        assert {c["key"] for c in d["checks"]} == {"senior", "homegrown", "u21"}
        p = S.get(f"{API}/squad").json()["players"][0]
        assert "best_role" in p and "rating" in p["best_role"]
        pd = S.get(f"{API}/players/{p['unique_id']}").json()
        assert len(pd["role_ratings"]) >= 1

    # --- rules ---
    def test_05_rules_params_affect_dev_xi(self):
        g = S.get(f"{API}/rules/squad").json()
        assert g["kind"] == "params" and g["version"] == 0
        params = dict(g["data"]["params"], max_youth=0)
        r = S.put(f"{API}/rules/squad", json={"data": {"params": params}, "expected_version": 0})
        assert r.status_code == 200 and r.json()["version"] == 1
        assert S.put(f"{API}/rules/squad", json={"data": {"params": params}, "expected_version": 0}).status_code == 409
        d = S.get(f"{API}/squad/plan").json()
        assert d["dev"]["youth"] == []
        bad = dict(params, max_senior=99)
        assert S.put(f"{API}/rules/squad", json={"data": {"params": bad}, "expected_version": 1}).status_code == 422
        r = S.post(f"{API}/rules/squad/reset", json={"expected_version": 1})
        assert r.status_code == 200 and r.json()["version"] == 2
        g = S.get(f"{API}/rules/squad").json()
        assert g["data"]["params"]["max_youth"] == 3 and len(g["history"]) == 2

    def test_06_rules_cards_import_test(self):
        g = S.get(f"{API}/rules/elite").json()
        assert g["kind"] == "rules"
        r = S.post(f"{API}/rules/elite/import", json={"data": g["data"], "expected_version": 0, "note": "TEST import"})
        assert r.status_code == 200 and r.json()["version"] == 1
        t = S.post(f"{API}/rules/elite/test", json={"rule": g["data"]["rules"][0]})
        assert t.status_code == 200
        td = t.json()
        assert set(td) == {"count", "population", "names"} and td["count"] == len(td["names"]) or td["count"] > 40
        dup = {"rules": [g["data"]["rules"][0], g["data"]["rules"][0]]}
        assert S.put(f"{API}/rules/elite", json={"data": dup, "expected_version": 1}).status_code == 422

    # --- scouting ---
    def test_07_scouting(self):
        m = S.get(f"{API}/scouting/meta").json()
        assert 100 <= m["count"] <= 160
        r = S.get(f"{API}/scouting/rankings").json()
        assert r["total"] == m["count"] and len(r["rows"]) <= 80
        lg = m["leagues"][0]
        rl = S.get(f"{API}/scouting/rankings", params={"league": lg, "max_age": 23}).json()["rows"]
        assert rl and all(x["league"] == lg and x["age"] <= 23 for x in rl)
        assert S.get(f"{API}/scouting/rankings", params={"role": "nope"}).status_code == 422
        uid = r["rows"][0]["unique_id"]
        CTX["scout_uid"] = uid
        assert S.post(f"{API}/scouting/shortlist", json={"unique_id": uid, "action": "add"}).status_code == 200
        sl = S.get(f"{API}/scouting/rankings", params={"shortlist_only": True}).json()["rows"]
        assert [x["unique_id"] for x in sl] == [uid]
        assert S.post(f"{API}/scouting/shortlist", json={"unique_id": 1, "action": "add"}).status_code == 404
        ids = ",".join(str(x["unique_id"]) for x in r["rows"][:4])
        c = S.get(f"{API}/scouting/compare", params={"ids": ids}).json()
        assert len(c) == 4

    # --- development plans ---
    def test_08_plans_append_only(self):
        body = {"unique_id": 20481123, "minutes_target": 300, "loan": "none", "note": "TEST", "expected_revision": 0}
        assert S.post(f"{API}/development/plans", json=body).json()["revision"] == 1
        assert S.post(f"{API}/development/plans", json=body).status_code == 409
        assert S.post(f"{API}/development/plans", json=body | {"loan": "loan_lower", "expected_revision": 1}).json()["revision"] == 2
        h = S.get(f"{API}/development/plans/20481123/history").json()
        assert [x["revision"] for x in h] == [2, 1]
        rows = S.get(f"{API}/development").json()["rows"]
        row = next(x for x in rows if x["unique_id"] == 20481123)
        assert row["plan"]["loan"] == "loan_lower" and row["target"] == 300

    # --- reports ---
    def test_09_reports(self):
        months = S.get(f"{API}/reports/months").json()
        assert len(months) == 4
        d = S.get(f"{API}/reports/compare", params={"a": 0, "b": 3}).json()
        assert "Mateus Costa" in d["summary"]["joined"] and "Pablo Navarro" in d["summary"]["left"]
        assert all(r["trend"] in ("rising", "falling", "steady") for r in d["rows"])
        assert S.get(f"{API}/reports/compare", params={"a": 0, "b": 99}).status_code == 404

    # --- elite training ---
    def test_10_elite_nominate_queue_dedupe(self):
        assert S.post(f"{API}/elite/nominations", json={"unique_id": 20481111}).status_code == 200
        e = S.get(f"{API}/elite").json()
        n = next(x for x in e["nominees"] if x["unique_id"] == 20481111)
        assert n["rule"] and n["preview"].startswith("Raise PA")
        q1 = S.post(f"{API}/elite/queue").json()
        assert q1["queued"] == 1
        q2 = S.post(f"{API}/elite/queue").json()
        assert q2["queued"] == 0 and q2["skipped_duplicates"] == 1
        assert S.post(f"{API}/elite/nominations/20481111/withdraw").status_code == 200
        assert not any(x["unique_id"] == 20481111 for x in S.get(f"{API}/elite").json()["nominees"])

    # --- breakout ---
    def test_11_breakout_review_finalise(self):
        assert S.post(f"{API}/breakout/nominations", json={"unique_id": 20481109}).status_code == 200
        assert S.post(f"{API}/breakout/review", json={"unique_id": 20481109, "rule_id": "bo-2", "decision": "provisional"}).json()["revision"] == 1
        assert S.post(f"{API}/breakout/review", json={"unique_id": 20481109, "rule_id": "bo-1", "decision": "provisional"}).json()["revision"] == 2
        c = next(x for x in S.get(f"{API}/breakout").json()["candidates"] if x["unique_id"] == 20481109)
        assert c["review"]["status"] == "provisional" and c["review"]["revisions"] == 2
        assert S.post(f"{API}/breakout/finalise").json()["official"] == 1
        r = S.post(f"{API}/breakout/review", json={"unique_id": 20481109, "rule_id": "bo-1", "decision": "provisional"})
        assert r.status_code == 409
        assert S.post(f"{API}/breakout/finalise").json()["official"] == 0

    # --- dynamic potential (hidden) ---
    def test_12_dp_scope_review_run_hidden(self):
        d = S.get(f"{API}/dp").json()
        lg = d["leagues"][0]["name"]
        nat = d["nations"][0]["name"]
        r = S.put(f"{API}/dp/scope", json={"scope": {"my_club": True, "leagues": [lg], "nations": [nat]}, "expected_version": d["version"]})
        assert r.status_code == 200
        d2 = S.get(f"{API}/dp").json()
        assert d2["covered"] >= d["covered"]
        groups = S.get(f"{API}/dp/review").json()
        flat = [p for g in groups for c in g["clubs"] for p in c["players"]]
        assert len(flat) == d2["covered"] and len({p["unique_id"] for p in flat}) == len(flat)
        assert all(set(p) == {"unique_id", "name"} for p in flat)
        run = S.post(f"{API}/dp/run", json={"exclude_ids": [20481109, 20481111]}).json()
        assert run["queued"] > 0
        assert S.post(f"{API}/dp/run", json={}).json()["queued"] <= 2  # only previously excluded may be new
        ch = S.get(f"{API}/changes").json()
        dp_rows = [x for x in ch["queued"] if x["source"] == "dp"]
        assert dp_rows and all(x["delta"] is None for x in dp_rows)
        assert all("key" not in x for x in ch["queued"])
        S.put(f"{API}/changes/reveal", json={"reveal": True})
        assert all(x["delta"] is not None for x in S.get(f"{API}/changes").json()["queued"] if x["source"] == "dp")
        S.put(f"{API}/changes/reveal", json={"reveal": False})

    # --- change queue / batches ---
    def test_13_apply_breakout_twice_409_and_persist_to_save(self):
        ch = S.get(f"{API}/changes").json()["queued"]
        bo = next(x for x in ch if x["source"] == "breakout" and x["unique_id"] == 20481109)
        others = [x for x in ch if x["unique_id"] == 20481109 and x["id"] != bo["id"]]
        assert not others
        before = squad_player(20481109)["pa"]
        r = S.post(f"{API}/changes/apply", json={"ids": [bo["id"]]})
        assert r.status_code == 200 and r.json()["total"] == 1
        assert S.post(f"{API}/changes/apply", json={"ids": [bo["id"]]}).status_code == 409
        wait_batches()
        backups = S.get(f"{API}/backups").json()
        assert any("before game change batch" in b["reason"] for b in backups)
        S.post(f"{API}/saves/read")
        after = squad_player(20481109)["pa"]
        assert after == min(200, before + bo["delta"]), (before, after, bo["delta"])
        CTX["bo_delta"] = bo["delta"]

    def test_14_pause_resume_undo_dp_batch(self):
        ch = S.get(f"{API}/changes").json()["queued"]
        ids = [x["id"] for x in ch if x["source"] == "dp"]
        assert len(ids) >= 5
        b = S.post(f"{API}/changes/apply", json={"ids": ids}).json()
        assert S.post(f"{API}/changes/batches/{b['batch_id']}/pause").status_code == 200
        time.sleep(0.5)
        bb = next(x for x in S.get(f"{API}/changes").json()["batches"] if x["id"] == b["batch_id"])
        assert bb["status"] == "paused" and bb["done"] < bb["total"]
        assert S.post(f"{API}/changes/batches/{b['batch_id']}/pause").status_code == 409
        assert S.post(f"{API}/changes/batches/{b['batch_id']}/resume").status_code == 200
        bs = wait_batches(60)
        bb = next(x for x in bs if x["id"] == b["batch_id"])
        assert bb["status"] == "done" and bb["done"] == bb["total"]
        u = S.post(f"{API}/changes/batches/{b['batch_id']}/undo")
        assert u.status_code == 200 and u.json()["undone"] == bb["total"]
        aud = S.get(f"{API}/audit").json()
        dp_applied = [a for a in aud if a["action"] == "applied" and a["source"] == "dp"]
        assert dp_applied and all(a["detail"] == "included" for a in dp_applied)
        assert any(a["action"] == "batch undone" for a in aud)

    def test_15_auto_mode(self):
        assert S.put(f"{API}/changes/modes", json={"source": "elite", "mode": "auto"}).status_code == 200
        assert S.get(f"{API}/changes").json()["modes"]["elite"] == "auto"
        S.post(f"{API}/elite/nominations", json={"unique_id": 20481115})
        q = S.post(f"{API}/elite/queue").json()
        assert q["queued"] >= 1
        wait_batches()
        assert not [x for x in S.get(f"{API}/changes").json()["queued"] if x["source"] == "elite" and x["unique_id"] == 20481115]
        S.put(f"{API}/changes/modes", json={"source": "elite", "mode": "ask"})

    def test_16_reject(self):
        ch = [x for x in S.get(f"{API}/changes").json()["queued"]]
        if not ch:
            pytest.skip("nothing queued")
        assert S.post(f"{API}/changes/reject", json={"ids": [ch[0]["id"]]}).json()["rejected"] == 1
        assert S.post(f"{API}/changes/apply", json={"ids": [ch[0]["id"]]}).status_code == 409

    def test_17_restore_batch_backup_leaves_queue_consistent(self):
        """Restoring the 'before game change batch' backup should give back an applyable queue."""
        b = next(x for x in S.get(f"{API}/backups").json() if "before game change batch" in x["reason"])
        assert S.post(f"{API}/backups/{b['id']}/restore").status_code == 200
        ch = S.get(f"{API}/changes").json()
        assert S.get(f"{API}/lineups").json(), "lineups lost after restore"
        stuck = S.get(f"{API}/home").json()["pending_changes"] - len(ch["queued"])
        assert stuck == 0, f"{stuck} change(s) restored in 'approved' state with no batch - not visible/applyable"
