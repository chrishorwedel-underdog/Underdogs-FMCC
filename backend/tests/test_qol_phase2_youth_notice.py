"""Youth intake bell notice: a save read crossing a tracked league's intake date adds a 'youth' notice (cleaned up afterwards)."""
import os
import requests
from pymongo import MongoClient

API = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/") + "/api"


def _env(key):
    for line in open("/app/backend/.env"):
        if line.startswith(key + "="):
            return line.split("=", 1)[1].strip().strip('"')


def test_youth_notice_on_crossing():
    db = MongoClient(_env("MONGO_URL"))[_env("DB_NAME")]
    cid = db.settings.find_one({"_id": "app"})["active_career_id"]
    before = (db.careers.find_one({"id": cid}) or {}).get("youth_intake", "__unset__")
    st = requests.get(f"{API}/youth-intake").json()
    year = st["game_date"][:4]
    key = f"youth:Serie A:{year}"
    pre = db.notices.find_one({"career_id": cid, "key": key})
    try:
        # prev save 2028-02-01, latest 2028-03-01: an intake on 02-15 was crossed
        assert requests.put(f"{API}/youth-intake", json={"league": "Serie A", "mmdd": "02-15"}).status_code == 200
        # untracked league with crossed date must not notify
        assert requests.put(f"{API}/youth-intake", json={"league": "Eredivisie", "mmdd": "02-16", "on": False}).status_code == 200
        d = requests.get(f"{API}/notify").json()
        youth = [n for n in d["items"] if n["type"] == "youth"]
        assert any(n["key"] == key and n["link"] == "/scouting?tab=youth" for n in youth), youth
        assert not any("Eredivisie" in n["key"] for n in youth)
    finally:
        if before == "__unset__":
            db.careers.update_one({"id": cid}, {"$unset": {"youth_intake": ""}})
        else:
            db.careers.update_one({"id": cid}, {"$set": {"youth_intake": before}})
        if not pre:
            db.notices.delete_one({"career_id": cid, "key": key})
