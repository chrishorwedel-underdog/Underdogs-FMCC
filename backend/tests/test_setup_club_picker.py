# Setup "pick your club" fix: fmsave_reader club detection unit tests (fake saves) + /api/setup/check-save + setup/complete club_uid
import os
import sys
from pathlib import Path

import pytest
import requests
from pymongo import MongoClient

sys.path.insert(0, str(Path(__file__).parent.parent))
import fmsave_reader as fr

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL")
if not BASE_URL:
    for line in (Path(__file__).parent.parent.parent / "frontend" / ".env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip()
BASE_URL = BASE_URL.rstrip("/")
OLD = "C:\\Users\\[You]\\Documents\\Sports Interactive\\Football Manager 2027\\games\\Old career.fm"
SAMPLE = "C:\\Users\\[You]\\Documents\\Sports Interactive\\Football Manager 2027\\games\\Sample Club FC.fm"
KEEP_ID = "72f82391-d58c-41f7-bc47-6a46cfd10a55"


class Obj:
    def __init__(self, **kw):
        self.__dict__.update(kw)


class FakeSave:
    def __init__(self, managed=None, staff=None, managed_raises=False):
        self._m, self._s, self._r = managed, staff, managed_raises

    def managed_clubs(self):
        if self._r:
            raise RuntimeError("layout")
        return self._m or []

    def staff(self):
        return self._s or []


NAMES = {1: "Wrexham", 2: "Chester", 3: "Wrexham Women", 4: "Manchester United", 5: "Manchester City", 6: "Tranmere Rovers"}


# ---- unit: club_from_file / club_choices / _find_club ----
class TestReaderUnit:
    def test_club_from_file(self):
        assert fr.club_from_file("Chris Horwedel - Wrexham 27") == "Wrexham"
        assert fr.club_from_file("Wrexham 27") == "Wrexham"
        assert fr.club_from_file("Chris - Wrexham 27 backup") == "Wrexham"

    def test_filename_exact_beats_substring(self):
        sk = []
        assert fr._find_club(FakeSave(managed_raises=True), NAMES, "Chris Horwedel - Wrexham 27", "", None, sk) == (1, None)
        assert "your club" in sk

    def test_picked_uid_first(self):
        assert fr._find_club(FakeSave(managed=[Obj(club_uid=1)]), NAMES, "x", "", 6, []) == (6, None)

    def test_managed_then_human(self):
        m = Obj(club_uid=2)
        assert fr._find_club(FakeSave(managed=[m]), NAMES, "x", "", None, []) == (2, m)
        st = [Obj(is_human_manager=False, club_uid=4), Obj(is_human_manager=True, club_uid=6)]
        assert fr._find_club(FakeSave(staff=st), NAMES, "x", "", None, []) == (6, None)

    def test_unique_substring_and_hint(self):
        assert fr._find_club(FakeSave(), NAMES, "Me - Tranmere 27", "", None, []) == (6, None)
        assert fr._find_club(FakeSave(), NAMES, "Me - Unknown 27", "chester", None, []) == (2, None)

    def test_ambiguous_raises_with_choices(self):
        with pytest.raises(fr.ClubNotFound) as e:
            fr._find_club(FakeSave(), NAMES, "Me - Manchester 27", "", None, [])
        ch = e.value.choices
        assert len(ch) == len(NAMES)
        likely = [c["name"] for c in ch if c["likely"]]
        assert "Manchester City" in likely and "Manchester United" in likely
        assert [c["likely"] for c in ch] == sorted([c["likely"] for c in ch], reverse=True)
        rest = [c["name"] for c in ch if not c["likely"]]
        assert rest == sorted(rest, key=str.lower)
        assert all(set(c) == {"uid", "name", "likely"} and isinstance(c["uid"], int) for c in ch)

    def test_likely_no_fragment_false_positive(self):
        # KNOWN BUG: _likely uses `n in h`, so 'Chester' is flagged likely for a 'Manchester' save
        ch = fr.club_choices(NAMES, "Me - Manchester 27")
        assert not next(c for c in ch if c["name"] == "Chester")["likely"]

    def test_empty_club_list_plain_error(self):
        with pytest.raises(ValueError) as e:
            fr._find_club(FakeSave(), {}, "Me - Wrexham 27", "", None, [])
        assert not isinstance(e.value, fr.ClubNotFound)
        assert str(e.value) == fr.NO_CLUB_LIST


# ---- API: check-save ----
@pytest.fixture(scope="module")
def s():
    return requests.Session()


class TestCheckSave:
    def test_old_career_needs_club(self, s):
        r = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": OLD})
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False and d["need_club"] is True and "Pick your club" in d["error"]
        clubs = d["clubs"]
        assert len(clubs) > 5 and all(set(c) == {"uid", "name", "likely"} for c in clubs)
        flags = [c["likely"] for c in clubs]
        assert flags == sorted(flags, reverse=True)
        for grp in (True, False):
            names = [c["name"] for c in clubs if c["likely"] is grp]
            assert names == sorted(names, key=str.lower)

    def test_old_career_typed_hint_likely_first(self, s):
        d = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": OLD, "club_name": "Sample"}).json()
        assert d["need_club"] and d["clubs"][0]["name"] == "Sample Club FC" and d["clubs"][0]["likely"]

    def test_old_career_with_uid_ok(self, s):
        clubs = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": OLD}).json()["clubs"]
        pick = clubs[3]
        d = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": OLD, "club_uid": pick["uid"]}).json()
        assert d["ok"] is True and d["club_name"] == pick["name"] and d["club_uid"] == pick["uid"] and d["players"] > 0

    def test_old_career_bad_uid_still_needs_club(self, s):
        d = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": OLD, "club_uid": 999999}).json()
        assert d["ok"] is False and d["need_club"] is True

    def test_sample_save_auto(self, s):
        for p in (SAMPLE, SAMPLE.replace("Sample Club FC.fm", "Sample Club FC - backup.fm")):
            d = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": p}).json()
            assert d["ok"] is True and d["club_name"] == "Sample Club FC" and d["club_uid"] is None

    def test_validation(self, s):
        assert s.post(f"{BASE_URL}/api/setup/check-save", json={"path": "x"}).status_code == 422


# ---- setup/complete stores club_uid (creates a TEST_ career and removes it by id) ----
def _db():
    env = {}
    for line in (Path(__file__).parent.parent / ".env").read_text().splitlines():
        if "=" in line:
            k, v = line.split("=", 1)
            env[k.strip()] = v.strip().strip('"')
    return MongoClient(env["MONGO_URL"])[env["DB_NAME"]]


def test_complete_stores_club_uid(s):
    db = _db()
    new_id = None
    try:
        assert s.post(f"{BASE_URL}/api/setup/restart").status_code == 200
        clubs = s.post(f"{BASE_URL}/api/setup/check-save", json={"path": OLD}).json()["clubs"]
        pick = clubs[2]
        r = s.post(f"{BASE_URL}/api/setup/complete", json={"edition": "FM27", "save_folder": "C:\\Saves", "save_file": OLD, "club_uid": pick["uid"],
                                                          "club_name": pick["name"], "name": "TEST_PickClub 27", "address": "Boss"})
        assert r.status_code == 200, r.text
        new_id = r.json()["career"]["id"]
        assert r.json()["career"]["club_uid"] == pick["uid"]
        st = s.get(f"{BASE_URL}/api/state").json()
        assert st["setup_complete"] is True and st["career"]["id"] == new_id
        assert st["career"].get("club_uid") == pick["uid"], f"state career missing club_uid: {st['career'].get('club_uid')}"
        row = next(c for c in s.get(f"{BASE_URL}/api/careers").json() if c["id"] == new_id)
        assert row["club_uid"] == pick["uid"] and row["club_name"] == pick["name"]
    finally:
        if new_id:
            for name in db.list_collection_names():
                if name not in ("settings", "careers"):
                    db[name].delete_many({"career_id": new_id})
            db.careers.delete_one({"id": new_id})
        db.settings.update_one({"_id": "app"}, {"$set": {"active_career_id": KEEP_ID, "setup_complete": True}, "$unset": {"setup_restart": "", "setup_progress": ""}})
