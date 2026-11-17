# Iteration 49 helper: hit every parameter-free GET route with and without odd rows; report ones that are 200 clean but fail with odd rows
import os, sys, requests
sys.path.insert(0, "/app/backend/tests")
os.environ.setdefault("REACT_APP_BACKEND_URL", open("/app/frontend/.env").read().split("REACT_APP_BACKEND_URL=")[1].split()[0])
import test_iter51_odd_rows_nokeys as t

U = os.environ["REACT_APP_BACKEND_URL"].rstrip("/")
SKIP = ("update", "download", "export", "backup", "restart", "stream", "logs", "zip", "open")
spec = requests.get("http://localhost:8001/openapi.json").json()  # route list only
paths = [p for p, m in spec["paths"].items() if "get" in m and "{" not in p and not any(s in p for s in SKIP)]


def sweep():
    out = {}
    for p in paths:
        try:
            out[p] = requests.get(f"{U}{p}", timeout=40).status_code
        except Exception as e:
            out[p] = str(e)[:40]
    return out


clean = sweep()
snap = t.mdb.snapshots.find_one({"career_id": t.CID}, {"_id": 1}, sort=[("save_no", -1)])
t.mdb.snapshots.update_one({"_id": snap["_id"]}, {"$push": {"players": {"$each": t.SNAP_ODD}}})
t.mdb.pools.update_one({"career_id": t.CID}, {"$push": {"players": {"$each": t.POOL_ODD}}})
try:
    odd = sweep()
finally:
    t.mdb.snapshots.update_one({"_id": snap["_id"]}, {"$pull": {"players": {"unique_id": {"$in": t.SNAP_IDS}}}})
    t.mdb.pools.update_one({"career_id": t.CID}, {"$pull": {"players": {"unique_id": {"$in": t.POOL_IDS}}}})
print("routes", len(paths))
for p in paths:
    if clean[p] != odd[p]:
        print("REGRESSION", p, clean[p], "->", odd[p])
print("clean non-200:", {p: c for p, c in clean.items() if c != 200})
