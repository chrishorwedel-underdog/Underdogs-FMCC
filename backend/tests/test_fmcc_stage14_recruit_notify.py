"""Stage 14: Recruitment Lab (profile, philosophy, pipeline, compare, explore, board, picks) and notification centre (countdowns, missed, notices, prefs).
Needs an active TEST_ career with saves read. Run with -n 0."""
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
S = requests.Session()
LEAK_KEYS = ("ca", "pa", "hidden", "personality", "best_role")


@pytest.fixture(scope="module")
def pool():
    r = S.post(f"{BASE_URL}/api/scout/players", json={})
    if r.status_code != 200:
        pytest.skip("No active career / scouting data")
    rows = r.json()["rows"]
    rows = [x for x in rows if (x.get("minutes") or 0) >= 600]
    return {"own": [x for x in rows if x["own"]], "other": [x for x in rows if not x["own"]], "all": rows}


@pytest.fixture(scope="module", autouse=True)
def restore_phil_and_prefs():
    ph = S.get(f"{BASE_URL}/api/recruit/philosophy").json() if S.get(f"{BASE_URL}/api/recruit/philosophy").status_code == 200 else None
    pr = S.get(f"{BASE_URL}/api/notify/prefs").json()["prefs"]
    yield
    S.put(f"{BASE_URL}/api/notify/prefs", json=pr)
    if ph:
        S.put(f"{BASE_URL}/api/recruit/philosophy", json={"weights": ph["weights"]})


# ---------- Recruit: profile ----------
class TestProfile:
    def test_profile_full(self, pool):
        uid = pool["other"][0]["unique_id"]
        r = S.get(f"{BASE_URL}/api/recruit/player/{uid}?role=af&view=full")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["role"] == "af" and isinstance(d["role_name"], str)
        for k in ("role_score", "philosophy", "character", "needs", "benchmarks", "indices", "fit", "extra", "summary", "similar", "pipeline", "weights"):
            assert k in d
        assert len(d["fit"]) == 5
        assert len(d["indices"]) == 12 and "luck" in d["indices"]["finishing"]
        assert d["player"]["league_word"] in ("Much stronger", "Slightly stronger", "Similar", "Slightly weaker", "Much weaker")

    def test_profile_bad_role_falls_back(self, pool):
        uid = pool["other"][0]["unique_id"]
        r = S.get(f"{BASE_URL}/api/recruit/player/{uid}?role=zzz")
        assert r.status_code == 200 and r.json()["role"] in r.json()["role_labels"]

    def test_profile_404(self):
        assert S.get(f"{BASE_URL}/api/recruit/player/1").status_code == 404

    @pytest.mark.parametrize("view", ["fair", "moneyball"])
    def test_profile_no_leak(self, pool, view):
        uid = pool["other"][0]["unique_id"]
        d = S.get(f"{BASE_URL}/api/recruit/player/{uid}?view={view}").json()
        p = d["player"]
        for k in LEAK_KEYS:
            assert p.get(k) is None, f"{k} leaked in {view}"
        assert d["character"]["result"] == "unknown"
        assert p["height"] is None and p["foot"] is None
        txt = str(d)
        assert "'ca':" not in txt and "'pa':" not in txt and "'hidden':" not in txt

    def test_bad_view_422(self, pool):
        uid = pool["other"][0]["unique_id"]
        assert S.get(f"{BASE_URL}/api/recruit/player/{uid}?view=god").status_code == 422


# ---------- Recruit: philosophy ----------
class TestPhilosophy:
    def test_save_revision(self, pool):
        before = S.get(f"{BASE_URL}/api/recruit/philosophy").json()
        w = {k: 3 for k in before["weights"]} | {"keep_ball": 5, "intensity": 0}
        r = S.put(f"{BASE_URL}/api/recruit/philosophy", json={"weights": w})
        assert r.status_code == 200 and r.json()["revision"] == before["revision"] + 1
        after = S.get(f"{BASE_URL}/api/recruit/philosophy").json()
        assert after["weights"]["keep_ball"] == 5 and after["weights"]["intensity"] == 0
        uid = pool["other"][0]["unique_id"]
        assert S.get(f"{BASE_URL}/api/recruit/player/{uid}").json()["weights"]["keep_ball"] == 5

    @pytest.mark.parametrize("w", [{"keep_ball": 6}, {"keep_ball": -1}, {"nope": 2}, {}])
    def test_invalid_422(self, w):
        assert S.put(f"{BASE_URL}/api/recruit/philosophy", json={"weights": w}).status_code == 422


# ---------- Recruit: pipeline ----------
class TestPipeline:
    def test_stage_history(self, pool):
        uid = pool["other"][1]["unique_id"]
        assert S.put(f"{BASE_URL}/api/recruit/pipeline/{uid}", json={"stage": "Watching", "note": "TEST_first"}).status_code == 200
        assert S.put(f"{BASE_URL}/api/recruit/pipeline/{uid}", json={"stage": "Scouted", "note": "TEST_second"}).status_code == 200
        pipe = S.get(f"{BASE_URL}/api/recruit/player/{uid}").json()["pipeline"]
        notes = [p["note"] for p in pipe]
        assert "TEST_first" in notes and "TEST_second" in notes
        assert pipe[0]["stage"] == "Scouted"

    def test_bad_stage_422(self, pool):
        uid = pool["other"][1]["unique_id"]
        assert S.put(f"{BASE_URL}/api/recruit/pipeline/{uid}", json={"stage": "Loaned"}).status_code == 422

    def test_unknown_player_404(self):
        assert S.put(f"{BASE_URL}/api/recruit/pipeline/1", json={"stage": "Watching"}).status_code == 404


# ---------- Recruit: compare ----------
class TestCompare:
    def test_compare_max4(self, pool):
        ids = [x["unique_id"] for x in pool["all"][:5]]
        r = S.get(f"{BASE_URL}/api/recruit/compare?ids={','.join(map(str, ids))}")
        assert r.status_code == 200, r.text
        d = r.json()
        assert len(d["players"]) == 4
        assert {g["group"] for g in d["groups"]} >= {"Shooting", "Creating"}
        row = d["groups"][0]["rows"][0]
        assert "median" in row and len(row["cells"]) == 4 and "best" in row
        assert d["radar"] and "p3" in d["radar"][0]
        assert isinstance(d["sit"], list) and any(s["sel"] for s in d["sit"])

    def test_compare_bad_ids(self):
        assert S.get(f"{BASE_URL}/api/recruit/compare?ids=a,b").status_code == 422

    def test_compare_empty_ids(self):
        r = S.get(f"{BASE_URL}/api/recruit/compare?ids=,")
        assert r.status_code in (404, 422), f"empty list returned {r.status_code}"

    def test_compare_fair_no_leak(self, pool):
        ids = ",".join(str(x["unique_id"]) for x in pool["all"][:2])
        assert "'ca'" not in str(S.get(f"{BASE_URL}/api/recruit/compare?ids={ids}&view=fair").json())


# ---------- Recruit: explore ----------
class TestExplore:
    def test_explore(self):
        r = S.get(f"{BASE_URL}/api/recruit/explore?x=npxg&y=xa&role=af")
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["count"] == len(d["points"]) > 0
        assert d["target"] == sum(p["kind"] == "target" for p in d["points"])
        assert {p["kind"] for p in d["points"]} <= {"own", "target", "pool", "shortlist"}
        assert d["ranked"] and all(not r_["own"] for r_ in d["ranked"])
        sc = [r_["score"] or 0 for r_ in d["ranked"]]
        assert sc == sorted(sc, reverse=True)

    def test_explore_bad_stat(self):
        assert S.get(f"{BASE_URL}/api/recruit/explore?x=bogus&y=xa").status_code == 422


# ---------- Recruit: board ----------
class TestBoard:
    def test_board_and_move(self, pool):
        uid = pool["other"][2]["unique_id"]
        S.post(f"{BASE_URL}/api/scouting/shortlist", json={"unique_id": uid, "action": "add"})
        b = S.get(f"{BASE_URL}/api/recruit/board").json()
        cols = b["columns"]
        assert len(cols) == 11
        slot_of = next(c["slot"] for c in cols if any(p["unique_id"] == uid for p in c["players"]))
        target = next(c["slot"] for c in cols if c["slot"] != slot_of)
        assert S.put(f"{BASE_URL}/api/recruit/board/{uid}", json={"slot": target}).status_code == 200
        b2 = S.get(f"{BASE_URL}/api/recruit/board").json()
        col = next(c for c in b2["columns"] if c["slot"] == target)
        p = next(p for p in col["players"] if p["unique_id"] == uid)
        assert "gain" in p and "stage" in p and "philosophy" in p
        S.post(f"{BASE_URL}/api/scouting/shortlist", json={"unique_id": uid, "action": "remove"})

    def test_move_bad_slot(self, pool):
        assert S.put(f"{BASE_URL}/api/recruit/board/{pool['other'][2]['unique_id']}", json={"slot": "zz"}).status_code == 422

    def test_board_bad_formation(self):
        assert S.get(f"{BASE_URL}/api/recruit/board?formation=999").status_code == 404


# ---------- Recruit: picks ----------
class TestPicks:
    def test_picks(self):
        r = S.post(f"{BASE_URL}/api/recruit/picks", json={"role": "af", "budget": 50_000_000, "max_wage": 200_000})
        assert r.status_code == 200, r.text
        d = r.json()
        assert set(d["columns"]) == {"Dream", "Upgrade", "Value", "Squad player", "Prospect"}
        assert all(len(v) <= 2 for v in d["columns"].values())
        ids = [p["unique_id"] for v in d["columns"].values() for p in v]
        assert len(ids) == len(set(ids)), "same player in two columns"
        assert any(d["columns"].values())
        for v in d["columns"].values():
            for p in v:
                assert (p["value"] or 0) <= 50_000_000 and isinstance(p["tags"], list) and p["reason"]

    def test_picks_tiny_budget_left_out(self):
        d = S.post(f"{BASE_URL}/api/recruit/picks", json={"role": "af", "budget": 1, "max_wage": 1}).json()
        assert not any(d["columns"].values())
        assert d["left_out"] and d["left_out"][0]["why"] in ("over budget", "wage too high")

    def test_picks_fair_no_leak(self):
        d = S.post(f"{BASE_URL}/api/recruit/picks", json={"role": "af", "budget": 50_000_000, "max_wage": 200_000, "view": "fair"}).json()
        for v in d["columns"].values():
            for p in v:
                assert p.get("personality") is None

    @pytest.mark.parametrize("body", [{"role": "zz", "budget": 1, "max_wage": 1}, {"role": "af", "budget": -1, "max_wage": 1}])
    def test_picks_invalid(self, body):
        assert S.post(f"{BASE_URL}/api/recruit/picks", json=body).status_code == 422


# ---------- Notify ----------
class TestNotify:
    def test_countdowns(self):
        d = S.get(f"{BASE_URL}/api/notify/countdowns").json()
        assert d["game_date"] and d["items"]
        for i in d["items"]:
            assert {"text", "days", "progress", "estimated", "link"} <= set(i)
            assert 0 <= i["progress"] <= 100
        assert isinstance(d["missed"], list)

    def test_missed_unknown_404(self):
        assert S.post(f"{BASE_URL}/api/notify/missed/missed:1999-01", json={"action": "late"}).status_code == 404

    def test_missed_bad_action(self):
        assert S.post(f"{BASE_URL}/api/notify/missed/missed:1999-01", json={"action": "x"}).status_code == 422

    def test_no_duplicates(self):
        a = S.get(f"{BASE_URL}/api/notify").json()
        b = S.get(f"{BASE_URL}/api/notify").json()
        assert len(a["items"]) == len(b["items"])
        keys = [i["key"] for i in b["items"]]
        assert len(keys) == len(set(keys))
        assert "unread" in b and "badges" in b

    def test_read_one(self):
        d = S.get(f"{BASE_URL}/api/notify").json()
        unread = [i for i in d["items"] if not i["read"]]
        if not unread:
            pytest.skip("nothing unread")
        assert S.post(f"{BASE_URL}/api/notify/{unread[0]['id']}/read").status_code == 200
        d2 = S.get(f"{BASE_URL}/api/notify").json()
        assert d2["unread"] == d["unread"] - 1
        assert next(i for i in d2["items"] if i["id"] == unread[0]["id"])["read"] is True

    def test_prefs(self):
        p = S.get(f"{BASE_URL}/api/notify/prefs").json()
        assert "save" in p["prefs"] and "save" in p["labels"]
        assert S.put(f"{BASE_URL}/api/notify/prefs", json={"bogus": True}).status_code == 422
        assert S.put(f"{BASE_URL}/api/notify/prefs", json={"save": False}).status_code == 200
        items = S.get(f"{BASE_URL}/api/notify").json()["items"]
        assert not any(i["type"] == "save" for i in items)
        assert S.put(f"{BASE_URL}/api/notify/prefs", json={"save": True}).status_code == 200
