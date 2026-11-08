# FMCC Stage 4: FMMatchLens install, match generation on save reads, match detail, season per90, scouting seen-vs-us,
# per-90 rule fields, DOF chat (conversations, SSE stream with REAL LLM, drafts accept/dismiss/409, career isolation).
# Precondition: EMPTY DB. Run with `-n 0`. Makes 2 real LLM calls.
import json
import os
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


def ask(conv, text):
    r = S.post(f"{API}/dof/conversations/{conv}/stream", json={"text": text}, stream=True, timeout=180)
    assert r.status_code == 200, r.text
    deltas, done, err = 0, None, None
    buf = ""
    for chunk in r.iter_content(chunk_size=None, decode_unicode=True):
        buf += chunk
        while "\n\n" in buf:
            part, buf = buf.split("\n\n", 1)
            if not part.startswith("data: "):
                continue
            ev = json.loads(part[6:])
            if ev["t"] == "delta":
                deltas += 1
            elif ev["t"] == "done":
                done = ev["message"]
            elif ev["t"] == "error":
                err = ev["c"]
    return deltas, done, err


class TestStage4:
    def test_01_setup(self):
        if S.get(f"{API}/state").json()["setup_complete"]:
            pytest.skip("DB not fresh")
        r = S.post(f"{API}/setup/complete", json={"name": "TEST_S4", "club_name": "TEST Club", "edition": "FM26", "save_folder": "C:\\FM26"})
        assert r.status_code == 200
        d = S.get(f"{API}/matches").json()
        assert d["matches"] == [] and d["matchlens"]["installed"] is False

    def test_02_no_matches_before_install(self):
        assert S.post(f"{API}/saves/read").status_code == 200
        assert S.get(f"{API}/matches").json()["matches"] == []
        assert S.get(f"{API}/matches/season").json() == {"season": None, "players": []}

    def test_03_install_and_generate(self):
        r = S.post(f"{API}/matchlens/install")
        assert r.status_code == 200 and r.json()["installed"] is True and r.json()["fmmatchlens"]
        assert S.get(f"{API}/matches").json()["matchlens"]["installed"] is True
        assert S.post(f"{API}/saves/read").status_code == 200
        ms = S.get(f"{API}/matches").json()["matches"]
        assert len(ms) == 4
        assert S.post(f"{API}/saves/read").status_code == 200
        ms = S.get(f"{API}/matches").json()["matches"]
        assert len(ms) == 8
        assert ms == sorted(ms, key=lambda m: m["date"], reverse=True)
        assert len({m["id"] for m in ms}) == 8
        CTX["mid"] = ms[0]["id"]

    def test_04_match_detail(self):
        m = S.get(f"{API}/matches/{CTX['mid']}").json()
        assert "_id" not in m
        us_goals = sum(s["team"] == "us" and s["outcome"] == "goal" for s in m["shots"])
        assert m["score"]["us"] == us_goals
        assert abs(m["xg"]["us"] - sum(s["xg"] for s in m["shots"] if s["team"] == "us")) < 0.05
        assert len(m["momentum"]) == 19
        assert all(0 <= s["x"] <= 100 and 0 <= s["y"] <= 100 and 0 < s["xg"] <= 0.75 for s in m["shots"])
        ours = [p for p in m["players"] if p["team"] == "us"]
        assert len(ours) == 11 and all(4.8 <= p["rating"] <= 10 for p in ours)
        assert any(p["key"] for p in m["passes"]) and any(p["progressive"] for p in m["passes"])
        assert {d["type"] for d in m["defensive"]} <= {"tackle", "interception", "pressure", "clearance"}
        squad_ids = {p["unique_id"] for p in S.get(f"{API}/squad").json()["players"]}
        assert {p["unique_id"] for p in ours} <= squad_ids
        CTX["us_ids"] = {p["unique_id"] for p in ours}
        CTX["them_ids"] = {p["unique_id"] for p in m["players"] if p["team"] == "them"}
        assert S.get(f"{API}/matches/nope").status_code == 404

    def test_05_season_per90(self):
        d = S.get(f"{API}/matches/season").json()
        assert d["season"] and d["players"]
        p = d["players"][0]
        assert p["team"] == "us" and len(p["trend"]) <= 8 and len(p["trend"]) >= 1
        assert abs(p["per90"]["xg"] - round(p["xg"] * 90 / p["minutes"], 2)) < 0.02
        assert [x["avg_rating"] for x in d["players"]] == sorted([x["avg_rating"] for x in d["players"]], reverse=True)

    def test_06_scouting_seen_vs_us(self):
        rows = S.get(f"{API}/scouting/rankings", params={"league": "Premier Division"}).json()["rows"]
        seen = [r for r in rows if r["seen_vs_us"] > 0]
        assert seen, "No 'seen vs us' players in rankings"
        assert all(r["per90"] is not None and r["match_rating"] is not None for r in seen)
        assert all(r["unique_id"] not in CTX["us_ids"] for r in seen)

    def test_07_rules_per90(self):
        d = S.get(f"{API}/rules/breakout").json()
        for k in ("xg90", "xa90", "key_passes90", "pressures90", "def_actions90"):
            assert k in d["fields"]
        assert d["fields"]["xg90"][0] == "xG per 90"
        rule = {"id": "t1", "name": "TEST_p90", "conditions": [{"field": "pressures90", "op": ">=", "value": 0}], "action": {"target": "pa", "min": 1, "max": 2}}
        r = S.post(f"{API}/rules/breakout/test", json={"rule": rule})
        assert r.status_code == 200
        res = r.json()
        # only players who played recorded matches have a pressures90 value
        assert 0 < res["count"] < res["population"], res

    def test_08_dof_status_conversations(self):
        st = S.get(f"{API}/dof/status").json()
        assert st["ready"] is True and st["model"] == "gpt-5.6-terra" and "Emergent" in st["key_source"] and len(st["suggested"]) >= 3
        c = S.post(f"{API}/dof/conversations", json={}).json()
        assert c["title"] == "New conversation" and "_id" not in c
        CTX["conv"] = c["id"]
        assert any(x["id"] == c["id"] for x in S.get(f"{API}/dof/conversations").json())
        assert S.get(f"{API}/dof/conversations/{c['id']}/messages").json() == []
        assert S.post(f"{API}/dof/conversations/nope/stream", json={"text": "hi"}).status_code == 404
        assert S.post(f"{API}/dof/conversations/{c['id']}/stream", json={"text": ""}).status_code == 422

    def test_09_dof_lineup_draft_accept(self):
        deltas, done, err = ask(CTX["conv"], "Who should start the next game to give my U21s minutes? Draft the lineup.")
        assert err is None, err
        assert deltas > 3 and done and done["content"]
        assert "ACTION:" not in done["content"]
        squad_names = [p["name"] for p in S.get(f"{API}/squad").json()["players"]]
        assert any(n.split()[-1] in done["content"] for n in squad_names), "Answer uses no squad names"
        msgs = S.get(f"{API}/dof/conversations/{CTX['conv']}/messages").json()
        assert [m["role"] for m in msgs] == ["user", "assistant"]
        conv = next(x for x in S.get(f"{API}/dof/conversations").json() if x["id"] == CTX["conv"])
        assert conv["title"].startswith("Who should start")
        if not done.get("draft"):
            pytest.fail(f"No lineup draft produced. Content: {done['content'][:300]}")
        assert done["draft"]["action"]["type"] == "lineup" and done["draft"]["status"] == "pending"
        mid = done["id"]
        r = S.post(f"{API}/dof/messages/{mid}/accept")
        assert r.status_code == 200 and r.json()["result"].startswith("Lineup saved (version")
        assert S.post(f"{API}/dof/messages/{mid}/accept").status_code == 409
        assert S.post(f"{API}/dof/messages/{mid}/dismiss").status_code == 409
        lus = S.get(f"{API}/lineups").json()
        assert "Drafted by DOF" in json.dumps(lus)
        m = next(x for x in S.get(f"{API}/dof/conversations/{CTX['conv']}/messages").json() if x["id"] == mid)
        assert m["draft"]["status"] == "accepted"

    def test_10_dof_shortlist_draft_dismiss(self):
        deltas, done, err = ask(CTX["conv"], "Pick the single best young prospect from the scouting pool sample and draft adding him to my shortlist.")
        assert err is None and done
        if not done.get("draft"):
            pytest.fail(f"No shortlist draft produced. Content: {done['content'][:300]}")
        assert done["draft"]["action"]["type"] == "shortlist"
        CTX["sl_msg"] = done["id"]
        r = S.post(f"{API}/dof/messages/{done['id']}/dismiss")
        assert r.status_code == 200
        assert S.post(f"{API}/dof/messages/{done['id']}/accept").status_code == 409
        msgs = S.get(f"{API}/dof/conversations/{CTX['conv']}/messages").json()
        assert len(msgs) == 4

    def test_11_career_isolation(self):
        r = S.post(f"{API}/careers", json={"name": "TEST_S4b", "club_name": "TEST Other", "edition": "FM26"})
        assert r.status_code == 200, r.text
        cid = r.json()["id"]
        assert S.get(f"{API}/dof/conversations").json() == []
        assert S.get(f"{API}/dof/conversations/{CTX['conv']}/messages").status_code == 404
        if "sl_msg" in CTX:
            assert S.post(f"{API}/dof/messages/{CTX['sl_msg']}/accept").status_code in (404, 409)
        # add-on install is app-wide, so the new career's first save read generates its own 4 matches
        new_ms = S.get(f"{API}/matches").json()["matches"]
        assert len(new_ms) == 4 and CTX["mid"] not in {m["id"] for m in new_ms}
        first = next(c for c in S.get(f"{API}/careers").json() if c["id"] != cid)
        assert S.post(f"{API}/careers/{first['id']}/activate").status_code == 200
        assert len(S.get(f"{API}/dof/conversations").json()) == 1

    def test_12_uninstall_stops_generation(self):
        assert S.post(f"{API}/matchlens/uninstall").json()["installed"] is False
        n = len(S.get(f"{API}/matches").json()["matches"])
        S.post(f"{API}/saves/read")
        assert len(S.get(f"{API}/matches").json()["matches"]) == n
        S.post(f"{API}/matchlens/install")
