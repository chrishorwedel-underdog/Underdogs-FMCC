"""Cleanup helper: removes TEST_ careers and every record tied to them, then resets setup so the preview opens on setup."""
import os
import sys
from pathlib import Path
from pymongo import MongoClient

for line in (Path(__file__).parent.parent / ".env").read_text().splitlines():
    if "=" in line:
        k, v = line.split("=", 1)
        os.environ.setdefault(k.strip(), v.strip().strip('"'))
db = MongoClient(os.environ["MONGO_URL"])[os.environ["DB_NAME"]]

ids = [c["id"] for c in db.careers.find({"name": {"$regex": "^TEST_"}}, {"id": 1})]
print("TEST careers:", ids)
conv_ids = [c["id"] for c in db.dof_conversations.find({"career_id": {"$in": ids}}, {"id": 1})]
if conv_ids:
    print("dof_messages", db.dof_messages.delete_many({"conversation_id": {"$in": conv_ids}}).deleted_count)
for name in db.list_collection_names():
    if name in ("settings", "careers"):
        continue
    n = db[name].delete_many({"career_id": {"$in": ids}}).deleted_count
    if n:
        print(name, n)
print("backups", db.backups.delete_many({"reason": {"$regex": "^TEST_[^:]*:"}}).deleted_count)
if "--test-results" in sys.argv:
    print("test_results", db.test_results.delete_many({}).deleted_count)
print("careers", db.careers.delete_many({"id": {"$in": ids}}).deleted_count)
s = db.settings.find_one({"_id": "app"}) or {}
unset = {"setup_progress": "", "notify_prefs": ""}
if s.get("active_career_id") in ids:
    unset["active_career_id"] = ""
db.settings.update_one({"_id": "app"}, {"$set": {"setup_complete": False}, "$unset": unset}, upsert=True)
ed = Path(__file__).parent.parent / "preview_fm" / "editor data"
for p in ed.glob("FMCC Punish - *.xml") if ed.is_dir() else []:
    p.unlink()
    print("deleted file", p.name)
print("settings", db.settings.find_one({"_id": "app"}))
