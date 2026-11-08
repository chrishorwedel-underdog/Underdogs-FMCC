# FMCC Stage 8: Logo Creator (ChatGPT club badge drafts: validation, generation, transparency, use-draft isolation)
import io
import os
from pathlib import Path

import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")
API = f"{BASE_URL}/api"
S = requests.Session()
CTX = {}
RUN_AI = os.environ.get("FMCC_RUN_AI") == "1"
GOOD = {"colours": ["#C8102E", "#FFFFFF"], "style": "classic", "notes": "TEST_ a lighthouse", "with_name": True}


def _mongo():
    from pymongo import MongoClient
    env = dict(l.split("=", 1) for l in Path("/app/backend/.env").read_text().splitlines() if "=" in l)
    return MongoClient(env["MONGO_URL"].strip('"'))[env["DB_NAME"].strip('"')]


class TestLogoCreator:
    # setup + pick a club
    def test_00_setup(self):
        st = S.get(f"{API}/state").json()
        if not st["setup_complete"]:
            r = S.post(f"{API}/setup/complete", json={"name": "TEST_career", "club_name": "Sample Club FC", "edition": "FM27", "save_folder": "C:\\TEST_folder"})
            assert r.status_code == 200, r.text
        cl = S.get(f"{API}/editor/clubs").json()
        assert len(cl) > 3
        CTX["club"] = cl[2]["uid"]
        CTX["club2"] = cl[3]["uid"]
        ps = S.get(f"{API}/editor/players", params={"limit": 300}).json()["players"]
        CTX["player"] = ps[0]["unique_id"]

    # validation
    @pytest.mark.parametrize("body", [
        {**GOOD, "colours": []},
        {**GOOD, "colours": ["#111111", "#222222", "#333333", "#444444"]},
        {**GOOD, "style": "graffiti"},
        {**GOOD, "notes": "x" * 301},
        {"style": "classic"},
    ])
    def test_01_validation_422(self, body):
        r = S.post(f"{API}/editor/clubs/{CTX['club']}/logo/generate", json=body)
        assert r.status_code == 422, r.text

    def test_02_unknown_club_404(self):
        r = S.post(f"{API}/editor/clubs/1/logo/generate", json=GOOD)
        assert r.status_code == 404, r.text

    def test_03_use_draft_bad_inputs(self):
        assert S.post(f"{API}/editor/clubs/{CTX['club']}/logo/use-draft", json={"image": "../x.png"}).status_code == 422
        r = S.post(f"{API}/editor/clubs/{CTX['club']}/logo/use-draft", json={"image": "0" * 24 + ".png"})
        assert r.status_code == 404
        r = S.post(f"{API}/editor/clubs/1/logo/use-draft", json={"image": "0" * 24 + ".png"})
        assert r.status_code == 404

    # real generation (costs credits)
    @pytest.mark.skipif(not RUN_AI, reason="set FMCC_RUN_AI=1")
    def test_10_generate(self):
        r = S.post(f"{API}/editor/clubs/{CTX['club']}/logo/generate", json=GOOD, timeout=180)
        assert r.status_code == 200, r.text
        d = r.json()["draft"]
        assert d.endswith(".png") and len(d) == 28
        CTX["draft"] = d
        img = S.get(f"{API}/editor/drafts/{d}")
        assert img.status_code == 200 and img.headers["content-type"] == "image/png"
        from PIL import Image
        im = Image.open(io.BytesIO(img.content))
        assert im.mode == "RGBA", im.mode
        assert max(im.size) == 360, im.size
        w, h = im.size
        for xy in ((0, 0), (w - 1, 0), (0, h - 1), (w - 1, h - 1)):
            assert im.getpixel(xy)[3] == 0, f"corner {xy} alpha {im.getpixel(xy)}"
        alpha = im.getchannel("A")
        assert alpha.getextrema()[1] == 255  # badge itself stays opaque
        CTX["opaque_ratio"] = sum(1 for a in alpha.getdata() if a > 0) / (w * h)
        print("opaque ratio", CTX["opaque_ratio"])
        assert CTX["opaque_ratio"] > 0.15
        # nothing applied yet
        c = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == CTX["club"])
        CTX["logo_before"] = c["logo_rev"]

    @pytest.mark.skipif(not RUN_AI, reason="set FMCC_RUN_AI=1")
    def test_11_logo_draft_not_usable_as_face_or_other_club(self):
        d = CTX["draft"]
        assert S.post(f"{API}/editor/faces/{CTX['player']}/use-draft", json={"image": d}).status_code == 404
        assert S.post(f"{API}/editor/faces/{CTX['club']}/use-draft", json={"image": d}).status_code == 404
        assert S.post(f"{API}/editor/clubs/{CTX['club2']}/logo/use-draft", json={"image": d}).status_code == 404

    @pytest.mark.skipif(not RUN_AI, reason="set FMCC_RUN_AI=1")
    def test_12_face_draft_not_usable_as_logo(self):
        db = _mongo()
        doc = {"id": "TEST_fake_face_draft", "career_id": db.face_drafts.find_one({"image": CTX["draft"]})["career_id"],
               "uid": CTX["club2"], "kind": "face", "image": CTX["draft"], "notes": "TEST_", "at": "2026-01-01"}
        db.face_drafts.insert_one(doc)
        try:
            r = S.post(f"{API}/editor/clubs/{CTX['club2']}/logo/use-draft", json={"image": CTX["draft"]})
            assert r.status_code == 404, r.text
        finally:
            db.face_drafts.delete_one({"id": "TEST_fake_face_draft"})

    @pytest.mark.skipif(not RUN_AI, reason="set FMCC_RUN_AI=1")
    def test_13_use_draft(self):
        uid = CTX["club"]
        before = S.get(f"{API}/editor/history/logo/{uid}").json()
        r = S.post(f"{API}/editor/clubs/{uid}/logo/use-draft", json={"image": CTX["draft"]})
        assert r.status_code == 200, r.text
        assert r.json()["graphics"]["pictures"] >= 1
        h = S.get(f"{API}/editor/history/logo/{uid}").json()
        assert len(h) == len(before) + 1
        assert h[0]["note"].startswith("Logo created with ChatGPT: classic, #C8102E, #FFFFFF"), h[0]["note"]
        assert h[0]["value"] == {"image": CTX["draft"], "source": "Created with ChatGPT"}
        c = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == uid)
        assert c["logo"] is True and c["logo_rev"] == CTX["draft"][:8]
        img = S.get(f"{API}/editor/image/logo/{uid}")
        assert img.status_code == 200 and img.content[:4] == b"\x89PNG"
        cfg = Path("/app/backend/preview_fm/graphics/FMCC/config.xml").read_text()
        assert f"graphics/pictures/club/{uid}/logo" in cfg

    @pytest.mark.skipif(not RUN_AI, reason="set FMCC_RUN_AI=1")
    def test_14_remove_logo_cleanup(self):
        r = S.delete(f"{API}/editor/clubs/{CTX['club']}/logo")
        assert r.status_code == 200
        c = next(x for x in S.get(f"{API}/editor/clubs").json() if x["uid"] == CTX["club"])
        assert c["logo"] is False
