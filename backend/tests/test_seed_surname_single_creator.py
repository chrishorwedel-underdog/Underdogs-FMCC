# Seed a Surname (/api/seed/*) and single Player Creator (/api/creator/single/*) regression tests
import os
import xml.etree.ElementTree as ET
from collections import Counter

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")
S = requests.Session()


def body(**kw):
    b = {"surname": "Testseed", "mode": "new", "players": {"GK": 1, "DC": 2, "MC": 2, "ST": 1},
         "staff": {"Scout": 1, "Physio": 1, "General Manager": 1},
         "nations": [{"nation": "England", "count": 5}, {"nation": "France", "count": 4}],
         "ca_lo": 30, "ca_hi": 60, "pa_lo": 60, "pa_hi": 100, "faces": False, "seed": 7}
    b.update(kw)
    return b


def unique_ids_ok(xml_text):
    root = ET.fromstring(xml_text.encode())  # well-formed or raises
    for el in root.iter():
        assert len(el.attrib) == len(set(el.attrib))
    return root


# Seed meta + validation
class TestSeedValidation:
    def test_meta(self):
        r = S.get(f"{BASE_URL}/api/seed/meta")
        assert r.status_code == 200
        d = r.json()
        assert d["caps"] == {"ca": 60, "pa": 100}
        assert "GK" in d["positions"] and "Scout" in d["staff"]["Scouts"]
        assert len(d["player_ages"]) == 5 and len(d["staff_ages"]) == 5
        assert "England" in d["nations"]

    @pytest.mark.parametrize("kw", [
        {"nations": [{"nation": "England", "count": 3}]},
        {"ca_hi": 61},
        {"pa_hi": 101},
        {"surname": "Test_1"},
        {"surname": "TEST_seed"},
        {"players": {"XX": 1}},
        {"ca_lo": 50, "ca_hi": 40},
        {"player_ages": {"young": 0}},
    ])
    def test_rejects(self, kw):
        r = S.post(f"{BASE_URL}/api/seed/create", json=body(**kw))
        assert r.status_code == 422, r.text


# New-save seed flow: create -> edit -> drop -> apply -> history -> file -> remove
class TestSeedNewFlow:
    sid = None

    def test_create_new(self):
        r = S.post(f"{BASE_URL}/api/seed/create", json=body())
        assert r.status_code == 200, r.text
        d = r.json()
        ppl = d["people"]
        assert len(ppl) == 9 and d["mode"] == "new"
        assert all(p["last_name"] == "Testseed" for p in ppl)
        assert Counter(p["nationality"] for p in ppl) == {"England": 5, "France": 4}
        assert all(p["ca"] <= 60 and p["pa"] <= 100 and p["pa"] >= p["ca"] for p in ppl)
        assert sum(p["kind"] == "staff" for p in ppl) == 3
        assert Counter(p["position"] for p in ppl if p["kind"] == "player") == {"GK": 1, "DC": 2, "MC": 2, "ST": 1}
        staff = [p for p in ppl if p["kind"] == "staff"]
        assert all(25 <= p["age"] <= 72 for p in staff)
        assert all(18 <= p["age"] <= 27 for p in ppl if p["kind"] == "player")

    def test_patch_and_caps(self):
        r = S.patch(f"{BASE_URL}/api/seed/draft/s0", json={"first_name": "Bobby", "ca": 55, "age": 20})
        assert r.status_code == 200, r.text
        assert r.json()["first_name"] == "Bobby" and r.json()["pa"] >= 55
        assert r.json()["dob"].startswith(str(int(r.json()["dob"][:4])))
        assert S.patch(f"{BASE_URL}/api/seed/draft/s0", json={"ca": 61}).status_code == 422
        assert S.patch(f"{BASE_URL}/api/seed/draft/s0", json={"pa": 101}).status_code == 422
        assert S.patch(f"{BASE_URL}/api/seed/draft/s0", json={"first_name": "B0b"}).status_code == 422
        assert S.patch(f"{BASE_URL}/api/seed/draft/s99", json={"first_name": "Bob"}).status_code == 404
        g = S.get(f"{BASE_URL}/api/seed/draft").json()
        assert next(p for p in g["people"] if p["pid"] == "s0")["first_name"] == "Bobby"

    def test_drop(self):
        assert S.delete(f"{BASE_URL}/api/seed/draft/s8").status_code == 200
        g = S.get(f"{BASE_URL}/api/seed/draft").json()
        assert len(g["people"]) == 8
        assert S.delete(f"{BASE_URL}/api/seed/draft/s8").status_code == 404

    def test_apply_and_history(self):
        r = S.post(f"{BASE_URL}/api/seed/apply")
        assert r.status_code == 200, r.text
        d = r.json()
        TestSeedNewFlow.sid = d["id"]
        assert len(d["people"]) == 8 and d["file_name"].startswith("FMCC Seed - Testseed")
        assert len({p["id"] for p in d["people"]}) == 8
        assert S.get(f"{BASE_URL}/api/seed/draft").json() is None
        assert S.post(f"{BASE_URL}/api/seed/apply").status_code == 409
        h = S.get(f"{BASE_URL}/api/seed/history").json()
        row = next(x for x in h if x["id"] == d["id"])
        assert row["count"] == 8 and row["surname"] == "Testseed"

    def test_file_wellformed(self):
        r = S.get(f"{BASE_URL}/api/seed/history/{self.sid}/file")
        assert r.status_code == 200
        root = unique_ids_ok(r.text)
        recs = root.findall(".//list/record")
        assert len(recs) == 8 and all(x.get("last_name") == "Testseed" for x in recs)

    def test_remove(self):
        assert S.delete(f"{BASE_URL}/api/seed/history/{self.sid}").status_code == 200
        assert S.get(f"{BASE_URL}/api/seed/history/{self.sid}/file").status_code == 404
        assert all(x["id"] != self.sid for x in S.get(f"{BASE_URL}/api/seed/history").json())


# Current-save mode: picks existing low-profile players, never exposes CA/PA
class TestSeedCurrent:
    def test_create_current(self):
        meta = S.get(f"{BASE_URL}/api/seed/meta").json()
        r = S.post(f"{BASE_URL}/api/seed/create", json=body(mode="current"))
        assert r.status_code == 200, r.text
        d = r.json()
        assert d["mode"] == "current" and len(d["people"]) == 9
        staff = [p for p in d["people"] if p["kind"] == "staff"]
        assert len(staff) == 3 and all(p["role"] not in ("Manager", "Chairperson") for p in staff)
        for p in d["people"]:
            assert p["club"] != meta["club"]
            assert "ca" not in p and "pa" not in p
            assert p["current_name"] and p["last_name"] == "Testseed"
        assert len({p["id"] for p in d["people"]}) == 9
        # current-mode patch only changes names
        r2 = S.patch(f"{BASE_URL}/api/seed/draft/{d['people'][0]['pid']}", json={"first_name": "Rolf", "age": 40})
        assert r2.status_code == 200 and r2.json()["first_name"] == "Rolf" and r2.json()["age"] == d["people"][0]["age"]
        # clear the draft (don't apply from backend suite)
        for p in d["people"]:
            S.delete(f"{BASE_URL}/api/seed/draft/{p['pid']}")


def single(**kw):
    meta = S.get(f"{BASE_URL}/api/creator/single/meta").json()
    attrs = {a: 12 for g in meta["groups"].values() for a in g}
    b = {"first_name": "Testchris", "last_name": "Horwedel", "common_name": "", "nationality": "England", "second_nationality": "",
         "dob": "2007-05-05", "ethnicity": "Northern European", "skin_tone": 3, "height": 182, "weight": 76, "left_foot": 9, "right_foot": 20,
         "positions": {"M (C)": 20, "DM": 15}, "ca": 185, "pa": 200, "attributes": attrs, "personality": {p: 14 for p in meta["personality"]},
         "club": "Free agent", "faces": False}
    b.update(kw)
    return b


# Single Player Creator CRUD + validation
class TestSingleCreator:
    sid = None

    def test_auto_attributes(self):
        r = S.post(f"{BASE_URL}/api/creator/single/auto-attributes", json={"positions": {"ST": 20}, "ca": 170, "variation": 2})
        assert r.status_code == 200
        assert all(1 <= v <= 20 for v in r.json().values()) and "finishing" in r.json()

    @pytest.mark.parametrize("kw", [{"ca": 201}, {"pa": 50, "ca": 100}, {"positions": {"ST": 15}}, {"first_name": "TEST_x"}, {"ethnicity": "Nope"}])
    def test_rejects(self, kw):
        assert S.post(f"{BASE_URL}/api/creator/single", json=single(**kw)).status_code == 422

    def test_create_edit_file_delete(self):
        r = S.post(f"{BASE_URL}/api/creator/single", json=single())
        assert r.status_code == 200, r.text
        d = r.json()
        sid = d["id"]
        assert d["player"]["ca"] == 185 and d["player"]["pa"] == 200
        try:
            u = S.put(f"{BASE_URL}/api/creator/single/{sid}", json=single(common_name="Chrissy", ca=150))
            assert u.status_code == 200 and u.json()["player"]["name"] == "Chrissy"
            # player game id must stay the same int after edit (regression: was replaced by doc uuid)
            assert u.json()["player"]["id"] == d["player"]["id"] and isinstance(u.json()["player"]["id"], int)
            lst = S.get(f"{BASE_URL}/api/creator/single").json()
            row = next(x for x in lst if x["id"] == sid)
            assert row["player"]["ca"] == 150
            f = S.get(f"{BASE_URL}/api/creator/single/{sid}/file")
            assert f.status_code == 200
            root = unique_ids_ok(f.text)
            rec = root.find(".//record[@id='new_person']")
            assert rec.get("common_name") == "Chrissy" and rec.get("ca") == "150"
            assert rec.get("unique_id") == str(d["player"]["id"])
        finally:
            assert S.delete(f"{BASE_URL}/api/creator/single/{sid}").status_code == 200
        assert S.get(f"{BASE_URL}/api/creator/single/{sid}/file").status_code == 404
