# Stage 12: starter pack respects the 30-formula limit
import os
import requests

API = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/") + "/api"
S = requests.Session()


def test_starter_limit():
    have = len(S.get(f"{API}/scout/formulas").json()["items"])
    mine = [f"test_lim_{i}" for i in range(28 - have)]
    try:
        for k in mine:
            assert S.put(f"{API}/scout/formulas/{k}", json={"name": "TEST_" + k, "expr": "age + 1"}).status_code == 200
        r = S.post(f"{API}/scout/formulas/starter", json={"keys": ["finishing", "goal_threat", "creator", "carrier"]})
        n = len(S.get(f"{API}/scout/formulas").json()["items"])
        print("status", r.status_code, r.text, "count", n)
        assert n <= 30
        assert r.status_code in (200, 409)
    finally:
        for k in mine + ["finishing", "goal_threat", "creator", "carrier"]:
            S.delete(f"{API}/scout/formulas/{k}")
