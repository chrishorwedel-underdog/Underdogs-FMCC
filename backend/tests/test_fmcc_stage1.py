# FMCC Stage 1 backend regression: setup, saves, identity matching, squad, careers, updates, backups.
# All tests share sequential state and live in ONE class (xdist loadscope keeps it on one worker).
# Precondition: DB collections settings/careers/identities/snapshots/backups/components are empty.
import os
import pytest
import requests
from pymongo import MongoClient

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    with open("/app/frontend/.env") as f:
        for line in f:
            if line.startswith("REACT_APP_BACKEND_URL="):
                BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"


def _mongo():
    env = {}
    with open("/app/backend/.env") as f:
        for line in f:
            if "=" in line:
                k, v = line.strip().split("=", 1)
                env[k] = v.strip('"')
    return MongoClient(env["MONGO_URL"])[env["DB_NAME"]]


S = requests.Session()
CTX = {}


class TestFMCCFlow:
    # --- setup ---
    def test_01_state_fresh(self):
        r = S.get(f"{API}/state")
        assert r.status_code == 200
        d = r.json()
        if d["setup_complete"]:
            pytest.skip("DB not fresh")
        assert d["career"] is None and d["sample_mode"] is True

    def test_02_detect(self):
        r = S.post(f"{API}/setup/detect", json={"edition": "FM27"})
        assert r.status_code == 200
        d = r.json()
        assert d["found"] is True and "Football Manager 2027" in d["save_folder"]
        r2 = S.post(f"{API}/setup/detect", json={"edition": "FM26"})
        assert "2026" in r2.json()["save_folder"]
        assert S.post(f"{API}/setup/detect", json={"edition": "FM99"}).status_code == 422

    def test_03_no_career_endpoints_409(self):
        assert S.get(f"{API}/home").status_code == 409
        assert S.post(f"{API}/saves/read").status_code == 409

    def test_04_setup_validation(self):
        r = S.post(f"{API}/setup/complete", json={"name": "", "club_name": "X", "edition": "FM27", "save_folder": "C:\\x"})
        assert r.status_code == 422

    def test_05_setup_complete_and_409(self):
        body = {"name": "TEST_Career A", "club_name": "TEST Club A", "edition": "FM27", "save_folder": "C:\\Games\\FM27"}
        r = S.post(f"{API}/setup/complete", json=body)
        assert r.status_code == 200, r.text
        d = r.json()
        CTX["career_a"] = d["career"]["id"]
        keys = [h["key"] for h in d["health"]]
        assert keys == ["link", "analytics", "dof"]
        assert d["health"][0]["ok"] is True and d["health"][1]["ok"] is False
        r2 = S.post(f"{API}/setup/complete", json=body)
        assert r2.status_code == 409
        st = S.get(f"{API}/state").json()
        assert st["setup_complete"] is True and st["career"]["id"] == CTX["career_a"]
        assert st["career"]["next_save_no"] == 1

    # --- home after first save ---
    def test_06_home_first_save(self):
        r = S.get(f"{API}/home")
        assert r.status_code == 200
        d = r.json()
        assert d["game_date"] == "2027-08-01"
        assert d["has_previous"] is False
        assert d["squad_size"] == 23
        assert isinstance(d["squad"]["xi_average"], int)
        assert d["next_fixture"]["opponent"]
        assert d["last_backup"]
        assert len(d["attention"]) >= 1
        assert "_id" not in d

    # --- identity: same name ---
    def test_07_squad_same_name(self):
        d = S.get(f"{API}/squad").json()
        lucas = [p for p in d["players"] if p["name"] == "Luca Romano"]
        assert sorted(p["unique_id"] for p in lucas) == [20481105, 20481106]
        assert all(p["shared_name"] for p in lucas)
        assert all(p["ca_change"] is None for p in d["players"])
        assert sum(1 for p in d["players"] if p["in_best_xi"]) == 11
        a = S.get(f"{API}/players/20481105").json()
        b = S.get(f"{API}/players/20481106").json()
        assert a["latest"]["birth_date"] != b["latest"]["birth_date"]
        assert a["identity"]["unique_id"] == 20481105
        assert S.get(f"{API}/players/99999999").status_code == 404

    def test_08_read_saves_identity_changes(self):
        backups_before = len(S.get(f"{API}/backups").json())
        for expected in ["2027-09-01", "2027-10-01", "2027-11-01"]:
            r = S.post(f"{API}/saves/read")
            assert r.status_code == 200, r.text
            assert r.json()["game_date"] == expected
        bk = S.get(f"{API}/backups").json()
        assert len(bk) == backups_before + 3
        assert bk[0]["reason"] == "Before reading save #4" and bk[0]["verified"] is True
        # save_no now 3 -> Navarro left, Costa joined
        sq = S.get(f"{API}/squad").json()
        assert sq["save_no"] == 3
        uids = {p["unique_id"]: p for p in sq["players"]}
        assert 20481122 not in uids
        assert 20481124 in uids and uids[20481124]["is_new"] is True
        assert any(d["unique_id"] == 20481122 for d in sq["departed"])
        assert any(p["ca_change"] is not None for p in sq["players"])
        assert sum(1 for p in sq["players"] if p["is_new"]) == 1
        # next save -> Costa no longer new
        S.post(f"{API}/saves/read")
        sq = S.get(f"{API}/squad").json()
        costa = [p for p in sq["players"] if p["unique_id"] == 20481124][0]
        assert costa["is_new"] is False
        hist = S.get(f"{API}/players/20481106").json()["history"]
        assert [h["save_no"] for h in hist] == [0, 1, 2, 3, 4]

    def test_09_home_has_previous(self):
        d = S.get(f"{API}/home").json()
        assert d["has_previous"] is True
        assert isinstance(d["report"]["total_change"], int)
        assert d["report"]["riser"]["name"]
        saves = S.get(f"{API}/saves").json()
        assert len(saves) == 5 and saves[0]["save_no"] == 4 and "players" not in saves[0]

    def test_10_search(self):
        r = S.get(f"{API}/players/search", params={"q": "luca"})
        assert r.status_code == 200
        assert len(r.json()) == 2
        assert len(S.get(f"{API}/players/search", params={"q": ""}).json()) == 8

    # --- careers ---
    def test_11_careers_create_switch(self):
        r = S.post(f"{API}/careers", json={"name": "TEST_Career B", "club_name": "TEST Club B", "edition": "FM26"})
        assert r.status_code == 200, r.text
        CTX["career_b"] = r.json()["id"]
        st = S.get(f"{API}/state").json()
        assert st["career"]["id"] == CTX["career_b"] and st["career"]["club_name"] == "TEST Club B"
        home = S.get(f"{API}/home").json()
        assert home["club_name"] == "TEST Club B" and home["game_date"] == "2027-08-01"
        cs = S.get(f"{API}/careers").json()
        assert len(cs) == 2 and sum(c["active"] for c in cs) == 1
        assert S.post(f"{API}/careers/{CTX['career_a']}/activate").status_code == 200
        assert S.get(f"{API}/home").json()["club_name"] == "TEST Club A"
        assert S.post(f"{API}/careers/nope/activate").status_code == 404

    def test_12_folder(self):
        r = S.put(f"{API}/careers/active/folder", json={"save_folder": "D:\\FM\\saves", "expected_career_id": CTX["career_a"]})
        assert r.status_code == 200
        assert S.get(f"{API}/state").json()["career"]["save_folder"] == "D:\\FM\\saves"
        r = S.put(f"{API}/careers/active/folder", json={"save_folder": "D:\\FM", "expected_career_id": CTX["career_b"]})
        assert r.status_code == 409

    # --- updates ---
    def test_13_updates_list(self):
        r = S.get(f"{API}/updates")
        assert r.status_code == 200
        d = r.json()
        keys = [c["key"] for c in d["components"]]
        assert keys == ["fmcc", "fmsave", "fmlibreeditor", "fmmatchlens", "bepinex"]
        by = {c["key"]: c for c in d["components"]}
        assert by["fmcc"]["status"] == "no_source"
        CTX["statuses"] = {k: v["status"] for k, v in by.items()}
        print("statuses", CTX["statuses"], {k: v.get("latest_version") for k, v in by.items()})
        assert d["last_check"]

    def test_14_update_apply_rollback(self):
        db = _mongo()
        db.components.update_one({"key": "fmmatchlens"}, {"$set": {"installed_version": "v0.7.0"}})
        d = S.post(f"{API}/updates/check").json()
        fm = [c for c in d["components"] if c["key"] == "fmmatchlens"][0]
        if fm["status"] == "check_failed":
            pytest.skip("GitHub unreachable / rate limited")
        assert fm["status"] == "update_available", fm
        latest = fm["latest_version"]
        r = S.post(f"{API}/updates/fmmatchlens/apply")
        assert r.status_code == 200 and r.json()["installed_version"] == latest
        assert S.post(f"{API}/updates/fmmatchlens/apply").status_code == 409
        comps = {c["key"]: c for c in S.get(f"{API}/updates").json()["components"]}
        assert comps["fmmatchlens"]["previous_version"] == "v0.7.0"
        assert S.post(f"{API}/updates/fmmatchlens/rollback").status_code == 200
        comps = {c["key"]: c for c in S.get(f"{API}/updates").json()["components"]}
        assert comps["fmmatchlens"]["installed_version"] == "v0.7.0"
        assert comps["fmmatchlens"]["status"] == "update_available"
        assert S.post(f"{API}/updates/fmmatchlens/rollback").status_code == 409
        # restore to bundled
        db.components.update_one({"key": "fmmatchlens"}, {"$set": {"installed_version": "v0.7.1"}, "$unset": {"previous_version": ""}})
        S.post(f"{API}/updates/check")

    def test_15_auto_install(self):
        assert S.put(f"{API}/settings/auto-install", json={"auto_install": True}).status_code == 200
        assert S.get(f"{API}/state").json()["auto_install_updates"] is True
        S.put(f"{API}/settings/auto-install", json={"auto_install": False})
        assert S.get(f"{API}/state").json()["auto_install_updates"] is False

    # --- backups ---
    def test_16_backup_and_restore(self):
        r = S.post(f"{API}/backups")
        assert r.status_code == 200 and r.json()["verified"] is True and "data" not in r.json()
        bk = S.get(f"{API}/backups").json()
        assert bk[0]["reason"] == "Manual backup"
        target = [b for b in bk if b["reason"] == "Before reading save #3"][0]
        r = S.post(f"{API}/backups/{target['id']}/restore")
        assert r.status_code == 200, r.text
        st = S.get(f"{API}/state").json()
        # before reading save #3 the career A had read 2 saves -> last date 2027-09-01
        assert st["career"]["id"] == CTX["career_a"]
        assert st["career"]["last_game_date"] == "2027-09-01"
        assert S.get(f"{API}/backups").json()[0]["reason"] == "Before restoring a backup"
        assert len(S.get(f"{API}/careers").json()) == 1  # career B created later is gone
        assert S.post(f"{API}/backups/nope/restore").status_code == 404
        # reading continues from the restored point
        r = S.post(f"{API}/saves/read")
        assert r.status_code == 200 and r.json()["game_date"] == "2027-10-01"
