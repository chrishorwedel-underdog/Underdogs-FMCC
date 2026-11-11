# Try in XI (shadow signings) - GET /api/squad/try-xi
import json
import os
import requests
import pytest

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
URL = f"{BASE_URL}/api/squad/try-xi"
OWN = 20481101
POOL = [30500001, 30500002, 30500006, 30500008]


def get(**params):
    return requests.get(URL, params=params, timeout=30)


def no_ca_pa(obj):
    s = json.dumps(obj)
    return '"ca"' not in s and '"pa"' not in s


class TestTryXI:
    def test_zero_ids(self):
        r = get()
        assert r.status_code == 200
        d = r.json()
        assert d["trial"] == [] and d["skipped"] == [] and d["dropped"] == []
        assert d["strength_before"] == d["strength_after"]
        assert len(d["slots"]) == 11
        assert all(not s["trial"] and s["before"] == s["after"] for s in d["slots"])
        assert isinstance(d["label"], str) and d["formation"]
        assert no_ca_pa(d)

    def test_one_id(self):
        d = get(add=str(POOL[2]), formation="4231").json()
        assert d["formation"] == "4231" and d["label"]
        assert [t["unique_id"] for t in d["trial"]] == [POOL[2]]
        t = d["trial"][0]
        assert {"name", "club", "positions", "in_xi"} <= set(t)
        if t["in_xi"]:
            assert any(s["trial"] for s in d["slots"])
            assert d["strength_after"] >= d["strength_before"]
            assert len(d["dropped"]) >= 1
        assert no_ca_pa(d)

    def test_three_ids(self):
        d = get(add=",".join(map(str, POOL[:3]))).json()
        assert sorted(t["unique_id"] for t in d["trial"]) == sorted(POOL[:3])
        assert d["strength_after"] >= d["strength_before"]
        assert sum(s["trial"] for s in d["slots"]) == sum(t["in_xi"] for t in d["trial"])

    def test_more_than_three_uses_first_three(self):
        d = get(add=",".join(map(str, POOL))).json()
        ids = [t["unique_id"] for t in d["trial"]]
        assert POOL[3] not in ids and len(ids) == 3

    def test_own_player_skipped(self):
        d = get(add=f"{OWN},{POOL[0]}").json()
        assert OWN in d["skipped"]
        assert [t["unique_id"] for t in d["trial"]] == [POOL[0]]

    def test_unknown_id_skipped(self):
        d = get(add="99999999").json()
        assert d["skipped"] == [99999999] and d["trial"] == []

    def test_garbage_ids_ignored(self):
        r = get(add="abc,,-5, ")
        assert r.status_code == 200
        assert r.json()["trial"] == []

    def test_invalid_formation_422(self):
        assert get(add=str(POOL[0]), formation="999").status_code == 422

    @pytest.mark.parametrize("f", ["433", "442", "4231"])
    def test_formations(self, f):
        d = get(add=str(POOL[2]), formation=f).json()
        assert d["formation"] == f and len(d["slots"]) == 11

    def test_long_add_422(self):
        assert get(add="1," * 150).status_code == 422
