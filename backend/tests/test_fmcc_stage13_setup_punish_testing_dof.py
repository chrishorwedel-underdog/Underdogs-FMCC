"""Stage 13: setup helpers (inspect, key check, health, progress), Punish a Club, Test checklist + report, DOF suggestions."""
import json
import os
from pathlib import Path

import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/") + "/api"
EDITOR_DATA = Path(__file__).parent.parent / "preview_fm" / "editor data"
S = requests.Session()


def _club(name):
    r = S.get(f"{BASE}/punish/clubs", params={"q": name})
    assert r.status_code == 200
    return next(c for c in r.json() if c["name"] == name)


# ---------- Setup helpers ----------
class TestSetup:
    @pytest.mark.parametrize("ed", ["FM26", "FM27"])
    def test_inspect(self, ed):
        r = S.post(f"{BASE}/setup/inspect", json={"edition": ed})
        assert r.status_code == 200
        d = r.json()
        assert [i["key"] for i in d["items"]] == ["game", "saves", "count"]
        assert all(i["status"] == "ok" for i in d["items"])
        assert ed in d["items"][0]["detail"] and "newest" in d["items"][2]["detail"]
        assert d["sample"] is True and d["save_folder"]

    def test_inspect_bad_edition(self):
        assert S.post(f"{BASE}/setup/inspect", json={"edition": "FM99"}).status_code == 422

    def test_check_key(self):
        r = S.post(f"{BASE}/setup/check-key", json={}, timeout=90)
        assert r.status_code == 200
        assert r.json()["ok"] is True, r.json()

    def test_health(self):
        r = S.get(f"{BASE}/setup/health")
        assert r.status_code == 200
        st = {i["key"]: i for i in r.json()["items"]}
        assert list(st) == ["save", "backup", "version", "running"]
        assert st["save"]["status"] == "ok" and st["backup"]["status"] == "ok"
        assert st["version"]["status"] == "warn" and st["version"]["fix"]
        assert st["running"]["status"] == "warn" and st["running"]["fix"]

    def test_progress_roundtrip_and_filtering(self):
        form = {"edition": "FM26", "club_name": "TEST Club", "name": "TEST_Career", "analytics": True, "found": True, "evil": "x", "save_folder": 5}
        r = S.put(f"{BASE}/setup/progress", json={"step": 2, "form": form})
        assert r.status_code == 200
        if r.json().get("ignored"):
            pytest.skip("setup already complete: progress is ignored by design")
        d = S.get(f"{BASE}/setup/progress").json()
        assert d["step"] == 2
        assert d["form"] == {"edition": "FM26", "club_name": "TEST Club", "name": "TEST_Career", "analytics": True, "found": True}

    @pytest.mark.parametrize("step", [-1, 4])
    def test_progress_bad_step(self, step):
        assert S.put(f"{BASE}/setup/progress", json={"step": step, "form": {}}).status_code == 422


# ---------- Punish a Club ----------
class TestPunish:
    def test_meta(self):
        d = S.get(f"{BASE}/punish/meta").json()
        assert len(d["penalties"]) == 12
        assert {p["key"] for p in d["presets"]} == {"light", "heavy", "full115"}
        full = next(p for p in d["presets"] if p["key"] == "full115")
        assert len(full["penalties"]) == 12

    def test_club_search(self):
        r = S.get(f"{BASE}/punish/clubs", params={"q": "VALD"})
        assert r.status_code == 200 and [c["name"] for c in r.json()] == ["AC Valdora"]
        assert S.get(f"{BASE}/punish/clubs", params={"q": "zzzqqq"}).json() == []

    def test_preview_summary_text(self):
        c = _club("AC Valdora")
        r = S.post(f"{BASE}/punish/preview", json={"club_uid": c["uid"], "penalties": {"points": {"points": 15}, "embargo": {"years": 2, "age_limit": 21}, "wipe_bank": {}}})
        assert r.status_code == 200
        d = r.json()
        assert d["summary"] == "AC Valdora: −15 points, two-year transfer ban for over-21s, bank balance set to 0"
        rows = {x["key"]: x for x in d["rows"]}
        assert rows["wipe_bank"]["current_save"] is True and rows["points"]["current_save"] is False and rows["points"]["why_not"]

    @pytest.mark.parametrize("pens", [{"points": {"points": 0}}, {"points": {"points": 121}}, {"embargo": {"years": 6}}, {"stadium": {"percent": 90}}, {"nope": {}}])
    def test_preview_out_of_range(self, pens):
        c = _club("AC Valdora")
        r = S.post(f"{BASE}/punish/preview", json={"club_uid": c["uid"], "penalties": pens})
        assert r.status_code == 422
        assert isinstance(r.json()["detail"], str)

    def test_preview_empty_and_bad_club(self):
        c = _club("AC Valdora")
        assert S.post(f"{BASE}/punish/preview", json={"club_uid": c["uid"], "penalties": {}}).status_code == 422
        assert S.post(f"{BASE}/punish/preview", json={"club_uid": 1, "penalties": {"wipe_bank": {}}}).status_code == 404

    def test_full_lifecycle(self):
        c = _club("AC Valdora")
        pens = {"points": {"points": 10}, "wipe_bank": {}, "reputation": {"amount": 1000}, "facilities": {"levels": 3}}
        r = S.post(f"{BASE}/punish", json={"club_uid": c["uid"], "penalties": pens})
        assert r.status_code == 200, r.text
        d = r.json()
        pid = d["pid"]
        assert d["file_name"].startswith("FMCC Punish - AC Valdora") and d["placed"] is False
        assert (EDITOR_DATA / d["file_name"]).exists()
        lst = S.get(f"{BASE}/punish").json()
        assert pid in [x["pid"] for x in lst]
        f = S.get(f"{BASE}/punish/{pid}/file")
        assert f.status_code == 200 and "attachment" in f.headers["content-disposition"]
        assert '<large id="club_unique_id" value="%d"/>' % c["uid"] in f.text and 'type="wipe_bank"' in f.text
        q = S.post(f"{BASE}/punish/{pid}/queue")
        assert q.status_code == 200
        qd = q.json()
        assert len(qd["queued"]) == 4, qd
        assert qd["new_career_only"] == ["Points deduction"]
        ch = S.get(f"{BASE}/changes").text
        assert "(Punish a Club)" in ch
        # Queue twice: older queued ones are replaced, not duplicated
        S.post(f"{BASE}/punish/{pid}/queue")
        from pymongo import MongoClient
        env = dict(l.split("=", 1) for l in (Path(__file__).parent.parent / ".env").read_text().splitlines() if "=" in l)
        db = MongoClient(env["MONGO_URL"].strip('"'))[env["DB_NAME"].strip('"')]
        assert db.changes.count_documents({"label": {"$regex": "Punish a Club"}, "status": "queued", "unique_id": c["uid"]}) == 4
        assert next(x for x in S.get(f"{BASE}/punish").json() if x["pid"] == pid)["queued"] is True
        rm = S.delete(f"{BASE}/punish/{pid}")
        assert rm.status_code == 200
        assert not (EDITOR_DATA / d["file_name"]).exists()
        assert pid not in [x["pid"] for x in S.get(f"{BASE}/punish").json()]
        assert S.get(f"{BASE}/punish/{pid}/file").status_code == 404
        assert S.delete(f"{BASE}/punish/{pid}").status_code == 404
        # reject queued Punish changes we made
        ids = [x["id"] for x in db.changes.find({"label": {"$regex": "Punish a Club"}, "status": "queued", "unique_id": c["uid"]})]
        rj = S.post(f"{BASE}/changes/reject", json={"ids": ids})
        print("reject", rj.status_code, rj.text[:200])


# ---------- Test checklist ----------
class TestChecklist:
    def test_list(self):
        d = S.get(f"{BASE}/testing").json()
        assert len(d["items"]) == 8 and d["desktop"] is False
        assert {"setup", "punish"} <= {i["key"] for i in d["items"]}

    def test_set_and_report_scrubbed(self):
        r = S.put(f"{BASE}/testing/setup", json={"status": "pass", "note": r"TEST_ saw C:\Users\alice\Documents ok and /home/bob/x"})
        assert r.status_code == 200
        it = next(i for i in S.get(f"{BASE}/testing").json()["items"] if i["key"] == "setup")
        assert it["status"] == "pass" and "alice" in it["note"]
        rep = S.get(f"{BASE}/testing/report")
        assert rep.status_code == 200 and "fmcc-test-report.json" in rep.headers["content-disposition"]
        assert "alice" not in rep.text and "bob" not in rep.text and "[you]" in rep.text
        data = json.loads(rep.text)
        assert len(data["results"]) == 8 and isinstance(data["log"], list) and data["mode"] == "Browser preview"

    def test_bad_inputs(self):
        assert S.put(f"{BASE}/testing/nope", json={"status": "pass"}).status_code == 404
        assert S.put(f"{BASE}/testing/setup", json={"status": "maybe"}).status_code == 422
        assert S.put(f"{BASE}/testing/setup", json={"status": "pass", "note": "x" * 501}).status_code == 422


# ---------- DOF suggestions ----------
class TestDof:
    def test_status_prompts(self):
        d = S.get(f"{BASE}/dof/status").json()
        assert d["suggested"][:3] == ["Fill my biggest gap", "Cheapest upgrade for my XI", "Young player to develop"]

    def test_suggestions_stream(self):
        conv = S.post(f"{BASE}/dof/conversations", json={"title": ""}).json()
        msg = None
        for text in ["Fill my biggest gap", "Who should I sign at right back? Suggest 3 players"]:
            r = S.post(f"{BASE}/dof/conversations/{conv['id']}/stream", json={"text": text}, stream=True, timeout=180)
            assert r.status_code == 200
            for line in r.iter_lines(decode_unicode=True):
                if line and line.startswith("data: "):
                    ev = json.loads(line[6:])
                    assert ev["t"] != "error", ev
                    if ev["t"] == "done":
                        msg = ev["message"]
            a = (msg.get("draft") or {}).get("action") if msg else None
            if a and a["type"] == "suggestions":
                break
        a = msg["draft"]["action"]
        assert a["type"] == "suggestions", msg
        items = a["items"]
        assert 1 <= len(items) <= 5
        for it in items:
            for k in ("unique_id", "name", "club", "gap", "reason", "numbers", "grade", "value", "wage", "over_budget"):
                assert k in it
            assert it["club"] != "TEST Club"
        uid = items[0]["unique_id"]
        r = S.post(f"{BASE}/dof/messages/{msg['id']}/shortlist/{uid}")
        assert r.status_code == 200 and items[0]["name"] in r.json()["result"]
        m = next(x for x in S.get(f"{BASE}/dof/conversations/{conv['id']}/messages").json() if x["id"] == msg["id"])
        assert m["draft"]["action"]["items"][0]["shortlisted"] is True
        assert S.post(f"{BASE}/dof/messages/{msg['id']}/shortlist/1").status_code == 404
        print("SUGGESTIONS", json.dumps(items, indent=1)[:1500])
