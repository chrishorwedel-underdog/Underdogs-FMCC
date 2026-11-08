# FMCC Stage 6: Player & Teams Editor (faces, NG_Regens fill/another, club logos, renames .lnc, club attributes via Game changes) + PA change regression
import io
import os
import time
from pathlib import Path

import pytest
import requests
from PIL import Image

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
CTX = {}
LNC = Path("/app/backend/preview_fm/game/data/database/db/2700/lnc/all/fmcc_club_names.lnc")
FMCC_CFG = Path("/app/backend/preview_fm/graphics/FMCC/config.xml")


def png(color=(200, 30, 30), fmt="PNG"):
    b = io.BytesIO()
    Image.new("RGB", (300, 300), color).save(b, fmt)
    return b.getvalue()


def wait_batch(bid, timeout=30):
    end = time.time() + timeout
    while time.time() < end:
        b = S.get(f"{API}/changes/batches/{bid}").json()
        if b["status"] != "running":
            return b
        time.sleep(0.5)
    return b


def players(**kw):
    return S.get(f"{API}/editor/players", params={"limit": 300, **kw}).json()


class TestEditor:
    def test_00_setup(self):
        st = S.get(f"{API}/state").json()
        if not st["setup_complete"]:
            r = S.post(f"{API}/setup/complete", json={"name": "TEST_career", "club_name": "Sample Club FC", "edition": "FM27", "save_folder": "C:\\TEST_folder"})
            assert r.status_code == 200, r.text
        assert S.get(f"{API}/state").json()["career"]["edition"] == "FM27"

    # status / NG_Regens
    def test_01_status(self):
        s = S.get(f"{API}/editor/status").json()
        assert s["ngregens"]["installed"] is True and s["ngregens"]["faces"] > 0
        assert "Italy" in s["ngregens"]["folders"] and s["desktop"] is False
        assert len(s["not_editable"]) == 3

    # players list: search + missing filter
    def test_02_players_filters(self):
        allp = players()
        assert allp["total"] > 0
        q = players(q="Sample Club")
        assert q["total"] > 0 and all("sample club" in (p["club"] or "").lower() or "sample club" in p["name"].lower() for p in q["players"])
        m = players(missing=True)
        assert all(p["face"] is None for p in m["players"])
        withface = next(p for p in allp["players"] if p["face"] and not p["custom"]) if any(p["face"] and not p["custom"] for p in allp["players"]) else None
        target = next(p for p in allp["players"] if p["face"] is None) if m["total"] else allp["players"][0]
        CTX["target"] = target
        CTX["ngp"] = withface

    # face image served for NG or 404 for none
    def test_03_image_endpoint(self):
        t = CTX["target"]
        r = S.get(f"{API}/editor/image/face/{t['unique_id']}")
        assert r.status_code == (404 if t["face"] is None else 200)

    # upload face -> Your picture, revision++, then remove (new revision)
    def test_04_upload_and_remove_face(self):
        uid = CTX["target"]["unique_id"]
        before = CTX["target"]["revisions"]
        r = S.post(f"{API}/editor/faces/{uid}", files={"file": ("TEST_face.png", png(), "image/png")})
        assert r.status_code == 200, r.text
        assert r.json()["graphics"]["pictures"] >= 1
        p = next(x for x in players() ["players"] if x["unique_id"] == uid)
        assert p["face"] == "Your picture" and p["custom"] is True and p["revisions"] == before + 1 and p["image_rev"]
        img = S.get(f"{API}/editor/image/face/{uid}")
        assert img.status_code == 200 and img.headers["content-type"] == "image/png"
        assert f"person/{uid}/portrait" in FMCC_CFG.read_text()
        # JPEG upload too
        r = S.post(f"{API}/editor/faces/{uid}", files={"file": ("TEST_face.jpg", png((10, 200, 10), "JPEG"), "image/jpeg")})
        assert r.status_code == 200
        d = S.delete(f"{API}/editor/faces/{uid}")
        assert d.status_code == 200
        p = next(x for x in players()["players"] if x["unique_id"] == uid)
        assert p["custom"] is False and p["revisions"] == before + 3
        assert S.delete(f"{API}/editor/faces/{uid}").status_code == 409

    def test_05_upload_non_image_and_unknown(self):
        uid = CTX["target"]["unique_id"]
        r = S.post(f"{API}/editor/faces/{uid}", files={"file": ("TEST.txt", b"hello world", "text/plain")})
        assert r.status_code == 422 and "picture" in r.json()["detail"]
        assert S.post(f"{API}/editor/faces/1", files={"file": ("a.png", png(), "image/png")}).status_code == 404

    # history newest first
    def test_06_history(self):
        h = S.get(f"{API}/editor/history/face/{CTX['target']['unique_id']}").json()
        revs = [x["revision"] for x in h]
        assert len(revs) >= 3 and revs == sorted(revs, reverse=True)
        assert h[0]["value"] is None

    # fill missing + nation folder mapping
    def test_07_fill_and_nation_folders(self):
        r = S.post(f"{API}/editor/fill-missing-faces")
        assert r.status_code == 200
        d = r.json()
        miss = players(missing=True)
        nats = {p["nationality"] for p in miss["players"]}
        assert set(d["unmatched"]) == nats or miss["total"] == 0
        if not nats:
            pytest.skip("no unmatched nationality")
        nat = sorted(nats)[0]
        CTX["mapped_nat"] = nat
        assert S.put(f"{API}/editor/nation-folders", json={"mapping": {nat: "Italy"}}).status_code == 200
        assert S.get(f"{API}/editor/status").json()["nation_folders"].get(nat) == "Italy"
        r2 = S.post(f"{API}/editor/fill-missing-faces").json()
        assert r2["filled"] >= 1 and nat not in r2["unmatched"]
        assert not any(p["nationality"] == nat for p in players(missing=True)["players"])

    # another NG face
    def test_08_another(self):
        allp = players()["players"]
        p = next((x for x in allp if x["face"] and x["face"].startswith("NG_Regens")), None)
        assert p
        old = p["image_rev"]
        r = S.post(f"{API}/editor/faces/{p['unique_id']}/another")
        assert r.status_code == 200, r.text
        np_ = next(x for x in players()["players"] if x["unique_id"] == p["unique_id"])
        assert np_["image_rev"] and np_["image_rev"] != old and np_["revisions"] == p["revisions"] + 1
        CTX["another_uid"] = p["unique_id"]

    # clubs: search, logo, rename, revert
    def test_09_clubs_logo_rename(self):
        cl = S.get(f"{API}/editor/clubs").json()
        assert len(cl) > 5
        c = next(x for x in cl if not x["rename"] and not x["logo"] and x["uid"] != 900000)
        CTX["club"] = c
        s = S.get(f"{API}/editor/clubs", params={"q": c["name"][:5]}).json()
        assert any(x["uid"] == c["uid"] for x in s)
        assert S.post(f"{API}/editor/clubs/{c['uid']}/logo", files={"file": ("TEST_logo.png", png((0, 0, 200)), "image/png")}).status_code == 200
        x = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == c["uid"])
        assert x["logo"] is True and x["logo_rev"]
        assert S.get(f"{API}/editor/image/logo/{c['uid']}").status_code == 200
        assert f"club/{c['uid']}/logo" in FMCC_CFG.read_text()
        assert S.delete(f"{API}/editor/clubs/{c['uid']}/logo").status_code == 200
        x = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == c["uid"])
        assert x["logo"] is False
        r = S.put(f"{API}/editor/clubs/{c['uid']}/name", json={"long": "TEST_Long Name", "short": "TEST_Short"})
        assert r.status_code == 200 and r.json()["lnc"]["ok"]
        txt = LNC.read_text()
        assert f'"CLUB_LONG_NAME_CHANGE" {c["uid"]} "TEST_Long Name" ""' in txt and f'"CLUB_SHORT_NAME_CHANGE" {c["uid"]} "TEST_Short" ""' in txt
        x = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == c["uid"])
        assert x["rename"]["long"] == "TEST_Long Name"
        assert S.put(f"{API}/editor/clubs/{c['uid']}/name", json={"long": "X", "short": "TEST"}).status_code == 422
        assert S.delete(f"{API}/editor/clubs/{c['uid']}/name").status_code == 200
        assert f" {c['uid']} " not in (LNC.read_text() if LNC.exists() else "")
        assert S.get(f"{API}/editor/clubs/123/attributes").status_code == 404

    # attributes: range validation and queue -> preview -> apply -> values -> undo
    def test_10_attributes_flow(self):
        uid = CTX["club"]["uid"]
        a = S.get(f"{API}/editor/clubs/{uid}/attributes").json()
        f = {x["key"]: x for x in a["fields"]}
        assert f["reputation"]["min"] == 0 and f["reputation"]["max"] == 10000
        assert S.post(f"{API}/editor/clubs/{uid}/attributes", json={"values": {"reputation": 20000}}).status_code == 422
        assert S.post(f"{API}/editor/clubs/{uid}/attributes", json={"values": {"nope": 1}}).status_code == 422
        assert S.post(f"{API}/editor/clubs/{uid}/attributes", json={"values": {}}).status_code == 422
        rep_old, tr_old = f["reputation"]["value"], f["training"]["value"]
        new_tr = 5 if tr_old != 5 else 6
        q = S.post(f"{API}/editor/clubs/{uid}/attributes", json={"values": {"reputation": 8000, "training": new_tr}})
        assert q.status_code == 200 and q.json()["queued"] == (2 if rep_old != 8000 else 1)
        mine = [x for x in S.get(f"{API}/changes").json()["queued"] if x.get("entity") == "club" and x["unique_id"] == uid]
        assert {x["field"] for x in mine} >= {"training"}
        p = S.post(f"{API}/changes/preview", json={"ids": [x["id"] for x in mine]}).json()
        assert p["ready"] is True
        rows = {r["field"]: r for r in p["rows"]}
        assert rows["training"]["current"] == tr_old and rows["training"]["new"] == new_tr
        if "reputation" in rows:
            assert rows["reputation"]["current"] == rep_old and rows["reputation"]["new"] == 8000
        ap = S.post(f"{API}/changes/apply", json={"preview_id": p["preview_id"]})
        assert ap.status_code == 200
        b = wait_batch(ap.json()["batch_id"])
        assert b["status"] == "done", b
        f2 = {x["key"]: x["value"] for x in S.get(f"{API}/editor/clubs/{uid}/attributes").json()["fields"]}
        assert f2["reputation"] == 8000 and f2["training"] == new_tr
        u = S.post(f"{API}/changes/batches/{b['id']}/undo")
        assert u.status_code == 200 and u.json()["undone"] == len(mine)
        f3 = {x["key"]: x["value"] for x in S.get(f"{API}/editor/clubs/{uid}/attributes").json()["fields"]}
        assert f3["reputation"] == rep_old and f3["training"] == tr_old

    def test_11_requeue_replaces(self):
        uid = CTX["club"]["uid"]
        S.post(f"{API}/editor/clubs/{uid}/attributes", json={"values": {"training": 3}})
        S.post(f"{API}/editor/clubs/{uid}/attributes", json={"values": {"training": 4}})
        mine = [x for x in S.get(f"{API}/changes").json()["queued"] if x.get("entity") == "club" and x["unique_id"] == uid and x["field"] == "training"]
        assert len(mine) == 1 and mine[0]["target"] == 4
        assert S.post(f"{API}/changes/reject", json={"ids": [mine[0]["id"]]}).json()["rejected"] == 1

    def test_12_rewrite(self):
        r = S.post(f"{API}/editor/rewrite")
        assert r.status_code == 200 and r.json()["graphics"]["pictures"] >= 1

    # regression: DP player changes preview+apply+undo
    def test_13_regression_dp(self):
        q = [x for x in S.get(f"{API}/changes").json()["queued"] if x["source"] in ("dp", "breakout")]
        if not q:
            r = S.post(f"{API}/dp/run", json={})
            assert r.status_code == 200, r.text
            q = [x for x in S.get(f"{API}/changes").json()["queued"] if x["source"] in ("dp", "breakout")]
        if not q:
            pytest.skip("no player changes available")
        ids = [q[0]["id"]]
        p = S.post(f"{API}/changes/preview", json={"ids": ids}).json()
        assert p["ready"] is True and p["rows"][0]["current"] is not None or p["rows"][0]["hidden"]
        ap = S.post(f"{API}/changes/apply", json={"preview_id": p["preview_id"]})
        assert ap.status_code == 200
        b = wait_batch(ap.json()["batch_id"])
        assert b["status"] == "done"
        assert S.post(f"{API}/changes/batches/{b['id']}/undo").json()["undone"] == 1
