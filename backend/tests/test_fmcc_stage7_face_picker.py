# FMCC Stage 7: Face Picker (NG_Regens folder browse, pick exact face, path security) + ChatGPT face drafts (generate, draft image, use-draft)
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


def players(**kw):
    return S.get(f"{API}/editor/players", params={"limit": 300, **kw}).json()


class TestFacePicker:
    def test_00_setup(self):
        st = S.get(f"{API}/state").json()
        if not st["setup_complete"]:
            r = S.post(f"{API}/setup/complete", json={"name": "TEST_career", "club_name": "Sample Club FC", "edition": "FM27", "save_folder": "C:\\TEST_folder"})
            assert r.status_code == 200, r.text
        s = S.get(f"{API}/editor/status").json()
        assert s["ngregens"]["installed"] and "Italy" in s["ngregens"]["folders"]
        CTX["folders"] = s["ngregens"]["folders"]
        ps = players()["players"]
        CTX["p"] = next(p for p in ps if p["nationality"] in CTX["folders"])
        CTX["p2"] = next(p for p in ps if p["unique_id"] != CTX["p"]["unique_id"])

    # folder listing + used_by labels
    def test_01_ng_folder(self):
        r = S.get(f"{API}/editor/ng-folder/Italy")
        assert r.status_code == 200
        d = r.json()
        assert d["folder"] == "Italy" and d["total"] == 3 and len(d["pictures"]) == 3
        assert all(p["id"].startswith("Italy/") and p["id"].endswith(".png") for p in d["pictures"])
        # paging
        d2 = S.get(f"{API}/editor/ng-folder/Italy", params={"offset": 2, "limit": 60}).json()
        assert len(d2["pictures"]) == 1
        # some folder should have a used picture (config.xml maps even uids)
        used = [p for f in CTX["folders"] for p in S.get(f"{API}/editor/ng-folder/{f}").json()["pictures"] if p["used_by"]]
        assert used, "No picture labelled as used in any folder"

    def test_02_ng_folder_404(self):
        r = S.get(f"{API}/editor/ng-folder/Nope")
        assert r.status_code == 404

    def test_03_ng_picture(self):
        r = S.get(f"{API}/editor/ng-picture", params={"path": "Italy/italy_1.png"})
        assert r.status_code == 200 and r.headers["content-type"] == "image/png" and r.content[:4] == b"\x89PNG"

    @pytest.mark.parametrize("path", ["../../server.py", "../../../backend/.env", "Italy/../../../server.py", "/etc/passwd", "config.xml", "Italy/nope.png"])
    def test_04_ng_picture_traversal(self, path):
        r = S.get(f"{API}/editor/ng-picture", params={"path": path})
        assert r.status_code == 404, f"{path}: {r.status_code}"

    def test_05_pick_face(self):
        uid = CTX["p"]["unique_id"]
        before = S.get(f"{API}/editor/history/face/{uid}").json()
        r = S.post(f"{API}/editor/faces/{uid}/pick", json={"path": "Spain/spain_2.png"})
        assert r.status_code == 200, r.text
        assert r.json()["graphics"]["pictures"] >= 1
        after = S.get(f"{API}/editor/history/face/{uid}").json()
        assert len(after) == len(before) + 1
        assert after[0]["value"]["source"] == "NG_Regens · Spain"
        row = next(p for p in players() if False) if False else next(p for p in players()["players"] if p["unique_id"] == uid)
        assert row["face"] == "NG_Regens · Spain" and row["custom"] is True
        img = S.get(f"{API}/editor/image/face/{uid}")
        src = S.get(f"{API}/editor/ng-picture", params={"path": "Spain/spain_2.png"})
        assert img.status_code == 200
        # used_by now labels the player
        d = S.get(f"{API}/editor/ng-folder/Spain").json()
        assert any(p["id"] == "Spain/spain_2.png" and p["used_by"] == CTX["p"]["name"] for p in d["pictures"])
        CTX["picked"] = uid

    @pytest.mark.parametrize("path", ["Italy/nope.png", "../../server.py", "Italy/../../../server.py"])
    def test_06_pick_bad_path(self, path):
        uid = CTX["p"]["unique_id"]
        r = S.post(f"{API}/editor/faces/{uid}/pick", json={"path": path})
        assert r.status_code == 404, f"{path}: {r.status_code} {r.text}"

    def test_07_pick_unknown_player(self):
        r = S.post(f"{API}/editor/faces/1/pick", json={"path": "Italy/italy_1.png"})
        assert r.status_code == 404

    # drafts
    def test_08_draft_unknown(self):
        assert S.get(f"{API}/editor/drafts/{'a' * 24}.png").status_code == 404
        assert S.get(f"{API}/editor/drafts/..%2F..%2Fserver.py").status_code == 404

    def test_09_use_draft_bad_name(self):
        uid = CTX["p"]["unique_id"]
        assert S.post(f"{API}/editor/faces/{uid}/use-draft", json={"image": "../server.py"}).status_code == 422
        assert S.post(f"{API}/editor/faces/{uid}/use-draft", json={"image": "ABC.png"}).status_code == 422

    def test_10_use_draft_not_made(self):
        uid = CTX["p"]["unique_id"]
        r = S.post(f"{API}/editor/faces/{uid}/use-draft", json={"image": f"{'b' * 24}.png"})
        assert r.status_code == 404

    def test_11_generate_unknown_player(self):
        r = S.post(f"{API}/editor/faces/1/generate", json={"notes": ""})
        assert r.status_code == 404

    def test_12_generate_notes_too_long(self):
        r = S.post(f"{API}/editor/faces/{CTX['p']['unique_id']}/generate", json={"notes": "x" * 301})
        assert r.status_code == 422

    @pytest.mark.skipif(not RUN_AI, reason="set FMCC_RUN_AI=1 to spend credits on one generation")
    def test_13_generate_and_use(self):
        uid = CTX["p"]["unique_id"]
        r = S.post(f"{API}/editor/faces/{uid}/generate", json={"notes": "TEST_ short black hair"}, timeout=180)
        assert r.status_code == 200, r.text
        draft = r.json()["draft"]
        assert draft.endswith(".png") and len(draft) == 28
        img = S.get(f"{API}/editor/drafts/{draft}")
        assert img.status_code == 200 and img.content[:4] == b"\x89PNG"
        # another player can't use it
        assert S.post(f"{API}/editor/faces/{CTX['p2']['unique_id']}/use-draft", json={"image": draft}).status_code == 404
        r = S.post(f"{API}/editor/faces/{uid}/use-draft", json={"image": draft})
        assert r.status_code == 200, r.text
        h = S.get(f"{API}/editor/history/face/{uid}").json()
        assert h[0]["value"]["source"] == "Created with ChatGPT" and h[0]["value"]["image"] == draft
        row = next(p for p in players()["players"] if p["unique_id"] == uid)
        assert row["face"] == "Created with ChatGPT"

    def test_99_cleanup(self):
        uid = CTX.get("picked")
        if uid:
            r = S.delete(f"{API}/editor/faces/{uid}")
            assert r.status_code in (200, 409)
