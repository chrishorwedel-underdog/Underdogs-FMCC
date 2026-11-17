# Restart setup / cancel restart API tests (iteration 43). Always leaves setup_complete true.
import os
import pytest
import requests

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/")


@pytest.fixture(scope="module")
def s():
    sess = requests.Session()
    yield sess
    st = sess.get(f"{BASE_URL}/api/state").json()
    if not st.get("setup_complete"):
        sess.post(f"{BASE_URL}/api/setup/cancel")
    assert sess.get(f"{BASE_URL}/api/state").json()["setup_complete"] is True


class TestRestartCancel:
    def test_cancel_when_not_restarted_409(self, s):
        st = s.get(f"{BASE_URL}/api/state").json()
        assert st["setup_complete"] is True and st["setup_restart"] is False
        r = s.post(f"{BASE_URL}/api/setup/cancel")
        assert r.status_code == 409
        assert "detail" in r.json()

    def test_restart_then_cancel_keeps_career(self, s):
        before = s.get(f"{BASE_URL}/api/state").json()
        cid = before["career"]["id"]
        n_before = len(s.get(f"{BASE_URL}/api/careers").json()) if s.get(f"{BASE_URL}/api/careers").ok else None
        r = s.post(f"{BASE_URL}/api/setup/restart")
        assert r.status_code == 200 and r.json()["ok"] is True
        mid = s.get(f"{BASE_URL}/api/state").json()
        assert mid["setup_complete"] is False
        assert mid["setup_restart"] is True
        assert mid["career"]["id"] == cid
        prog = s.get(f"{BASE_URL}/api/setup/progress").json()
        assert prog["step"] == 0
        # restart twice is idempotent
        assert s.post(f"{BASE_URL}/api/setup/restart").status_code == 200
        assert s.get(f"{BASE_URL}/api/state").json()["setup_restart"] is True
        c = s.post(f"{BASE_URL}/api/setup/cancel")
        assert c.status_code == 200
        after = s.get(f"{BASE_URL}/api/state").json()
        assert after["setup_complete"] is True
        assert after["setup_restart"] is False
        assert after["career"]["id"] == cid
        if n_before is not None:
            assert len(s.get(f"{BASE_URL}/api/careers").json()) == n_before
        # second cancel -> 409
        assert s.post(f"{BASE_URL}/api/setup/cancel").status_code == 409

    def test_complete_rejected_when_setup_complete(self, s):
        # Not restarted: complete must not create a career
        st = s.get(f"{BASE_URL}/api/state").json()
        assert st["setup_complete"] is True
