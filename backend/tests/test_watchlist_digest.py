# Watchlist (GET/POST/DELETE /api/watch), watch alerts via digest/notify, and Home "What changed" digest
import os
import pytest
import requests
from pymongo import MongoClient


def _env(path, key):
    for line in open(path):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


BASE_URL = (os.environ.get("REACT_APP_BACKEND_URL") or _env("/app/frontend/.env", "REACT_APP_BACKEND_URL")).rstrip("/")
DB = MongoClient(_env("/app/backend/.env", "MONGO_URL"))[_env("/app/backend/.env", "DB_NAME")]
UID = 20481104  # Jonas Lindqvist (own squad, sample save)
UID2 = 20481107
UID3 = 20481103


def _career_id():
    return DB.settings.find_one({"_id": "app"})["active_career_id"]


def _no_ca_pa(obj, path="root"):
    if isinstance(obj, dict):
        for k, v in obj.items():
            assert k.lower() not in {"ca", "pa", "current_ability", "potential_ability"}, f"CA/PA key at {path}.{k}"
            _no_ca_pa(v, f"{path}.{k}")
    elif isinstance(obj, list):
        for i, v in enumerate(obj):
            _no_ca_pa(v, f"{path}[{i}]")


@pytest.fixture(scope="module")
def s():
    x = requests.Session()
    yield x
    for u in (UID, UID2, UID3):
        x.delete(f"{BASE_URL}/api/watch/{u}")


class TestWatchCrud:
    def test_get_shape(self, s):
        r = s.get(f"{BASE_URL}/api/watch")
        assert r.status_code == 200
        d = r.json()
        assert isinstance(d["rows"], list) and isinstance(d["ids"], list)

    def test_add_unknown_404(self, s):
        r = s.post(f"{BASE_URL}/api/watch", json={"unique_id": 1})
        assert r.status_code == 404

    def test_add_bad_body_422(self, s):
        assert s.post(f"{BASE_URL}/api/watch", json={"unique_id": "abc"}).status_code == 422
        assert s.post(f"{BASE_URL}/api/watch", json={}).status_code == 422

    def test_add_get_idempotent_delete(self, s):
        r = s.post(f"{BASE_URL}/api/watch", json={"unique_id": UID3})
        assert r.status_code == 200 and r.json()["ok"] is True and r.json()["name"]
        assert s.post(f"{BASE_URL}/api/watch", json={"unique_id": UID3}).status_code == 200
        d = s.get(f"{BASE_URL}/api/watch").json()
        assert d["ids"].count(UID3) == 1
        row = next(x for x in d["rows"] if x["unique_id"] == UID3)
        assert row["last"]["name"] == r.json()["name"]
        assert row["latest"] is None
        _no_ca_pa(d)
        assert s.delete(f"{BASE_URL}/api/watch/{UID3}").status_code == 200
        assert UID3 not in s.get(f"{BASE_URL}/api/watch").json()["ids"]
        assert s.delete(f"{BASE_URL}/api/watch/{UID3}").status_code == 404


class TestWatchAlerts:
    def test_alert_flow_digest_and_notify(self, s):
        cid = _career_id()
        car = DB.careers.find_one({"id": cid})
        orig_checked = car.get("watch_checked_save")
        try:
            assert s.post(f"{BASE_URL}/api/watch", json={"unique_id": UID}).status_code == 200
            assert s.post(f"{BASE_URL}/api/watch", json={"unique_id": UID2}).status_code == 200
            w = DB.watchlist.find_one({"career_id": cid, "unique_id": UID})
            last = w["last"]
            DB.watchlist.update_one({"_id": w["_id"]}, {"$set": {"last.grade": (last.get("grade") or 50) - 5,
                                                               "last.value": max(int((last.get("value") or 1e6) * 2), 1000000),
                                                               "last.club": "TEST_Other FC"}})
            DB.careers.update_one({"id": cid}, {"$unset": {"watch_checked_save": ""}})
            r = s.get(f"{BASE_URL}/api/watch/digest")
            assert r.status_code == 200
            d = r.json()
            _no_ca_pa(d)
            for k in ("since", "current_save", "sample", "ratings", "contracts", "applied", "watch", "total"):
                assert k in d
            mine = [x for x in d["watch"] if x["unique_id"] == UID]
            kinds = " ".join(x["text"] for x in mine)
            print("digest watch items:", mine)
            assert "Grade rose" in kinds
            assert "Value fell" in kinds
            assert "Transferred from TEST_Other FC" in kinds
            # UID2 unchanged -> no items
            assert not [x for x in d["watch"] if x["unique_id"] == UID2]
            notes = list(DB.notices.find({"career_id": cid, "type": "watch", "key": {"$regex": f"^watch:{UID}:"}}, {"_id": 0}))
            assert len(notes) == 3, notes
            assert all(n["link"].startswith(f"/scouting?tab=watchlist&player={UID}") for n in notes)
            # bell API returns them
            nr = s.get(f"{BASE_URL}/api/notify")
            assert nr.status_code == 200
            _no_ca_pa(nr.json())
            assert "watch:" in nr.text or "Watched player" in nr.text or any(n["title"] in nr.text for n in notes)
            # watchlist row latest + last refreshed
            row = next(x for x in s.get(f"{BASE_URL}/api/watch").json()["rows"] if x["unique_id"] == UID)
            assert row["latest"] and row["latest"]["kind"] in {"grade", "value", "contract"}
            assert row["last"]["club"] != "TEST_Other FC"
            # second check is a no-op (same save)
            s.get(f"{BASE_URL}/api/watch/digest")
            assert DB.notices.count_documents({"career_id": cid, "type": "watch", "key": {"$regex": f"^watch:{UID}:"}}) == 3
        finally:
            DB.notices.delete_many({"career_id": cid, "type": "watch", "key": {"$regex": f"^watch:({UID}|{UID2}):"}})
            for u in (UID, UID2):
                s.delete(f"{BASE_URL}/api/watch/{u}")
            if orig_checked is not None:
                DB.careers.update_one({"id": cid}, {"$set": {"watch_checked_save": orig_checked}})


class TestDigest:
    def test_digest_applied_groups(self, s):
        d = s.get(f"{BASE_URL}/api/watch/digest").json()
        assert d["sample"] is True
        for g in d["applied"]:
            assert g["link"].startswith("/") and g["count"] >= 1 and len(g["names"]) <= 4
        assert d["total"] == len(d["ratings"]) + len(d["contracts"]) + sum(g["count"] for g in d["applied"]) + len(d["watch"])
