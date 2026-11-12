# FMCC QoL phase 1: finance strip, review switch, auto-apply, PA/CA hiding, rules screen impact/reset, DP settings impact.
# Run serially: pytest tests/test_qol_phase1.py -n 0 -o addopts=''
import os
import re
import time

import pytest
import requests

BASE = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/") + "/api"
S = requests.Session()


def j(r):
    assert r.status_code < 500, f"{r.status_code} {r.text[:300]}"
    return r.json()


def set_review(on):
    r = S.put(f"{BASE}/features/review", json={"on": on})
    assert r.status_code == 200 and r.json()["review_changes"] is on


def wait_batch(bid, t=20):
    for _ in range(t * 4):
        b = j(S.get(f"{BASE}/changes/batches/{bid}"))
        if b["status"] != "running":
            return b
        time.sleep(0.25)
    return b


# ---------- Finance ----------
class TestFinance:
    def test_finance_items(self):
        d = j(S.get(f"{BASE}/finance"))
        it = {x["key"]: x for x in d["items"]}
        assert list(it) == ["ffp", "wages", "spent", "budget", "bank"]
        assert it["ffp"]["text"] == "Compliant" and it["ffp"]["tone"] == "green"
        assert it["wages"]["text"] == "60%" and it["wages"]["tone"] == "green"
        assert it["spent"]["text"] == "£6.3m"
        assert it["budget"]["text"] == "£6.2m"
        assert it["bank"]["text"] == "£15.9m"
        assert all(x["tone"] and x["reason"] for x in d["items"])


# ---------- Features review switch ----------
class TestReviewSwitch:
    def test_toggle(self):
        assert j(S.get(f"{BASE}/features"))["review_changes"] is False
        set_review(True)
        assert j(S.get(f"{BASE}/features"))["review_changes"] is True
        assert j(S.get(f"{BASE}/changes"))["review_changes"] is True
        set_review(False)
        assert j(S.get(f"{BASE}/features"))["review_changes"] is False

    def test_bad_body(self):
        assert S.put(f"{BASE}/features/review", json={}).status_code == 422


# ---------- Auto-apply vs review via Elite Training ----------
class TestAutoApply:
    def _nominee(self, idx):
        e = j(S.get(f"{BASE}/elite"))
        return e["suggestions"][idx]["unique_id"]

    def test_review_on_stays_queued_then_off_auto_applies(self):
        before = {x["id"] for x in j(S.get(f"{BASE}/changes"))["queued"]}
        uid = self._nominee(0)
        try:
            set_review(True)
            assert S.post(f"{BASE}/elite/nominations", json={"unique_id": uid, "note": "TEST_"}).status_code == 200
            res = j(S.post(f"{BASE}/elite/queue"))
            print("review on queue:", res)
            ch = j(S.get(f"{BASE}/changes"))
            new = [x for x in ch["queued"] if x["id"] not in before]
            if res["queued"] == 0:
                pytest.skip(f"nominee did not qualify: {res}")
            assert res.get("auto_applied") is False
            assert len(new) == res["queued"]
            for x in new:
                if x["field"] in ("pa", "ca"):
                    assert x.get("current") is None and x.get("new") is None
            pv = j(S.post(f"{BASE}/changes/preview", json={"ids": [x["id"] for x in new]}))
            for r in pv["rows"]:
                assert r["current"] is None and r["new"] is None, r
            # reject the queued test change (cleanup)
            assert j(S.post(f"{BASE}/changes/reject", json={"ids": [x["id"] for x in new]}))["rejected"] == len(new)
        finally:
            S.post(f"{BASE}/elite/nominations/{uid}/withdraw")
            set_review(False)

    def test_review_off_auto_applies_and_notifies(self):
        uid = self._nominee(1)
        bid = None
        try:
            set_review(False)
            assert S.post(f"{BASE}/elite/nominations", json={"unique_id": uid, "note": "TEST_"}).status_code == 200
            res = j(S.post(f"{BASE}/elite/queue"))
            print("review off queue:", res)
            if res["queued"] == 0:
                pytest.skip(f"nominee did not qualify: {res}")
            assert res["auto_applied"] is True
            b = j(S.get(f"{BASE}/changes"))["batches"][0]
            bid = b["id"]
            b = wait_batch(bid)
            assert b["status"] == "done", b
            for r in b["changes"]:
                if r["field"] in ("pa", "ca"):
                    assert r["old_value"] is None and r["new_value"] is None
            n = j(S.get(f"{BASE}/notify"))["items"]
            assert any(x["type"] == "changes" and re.match(r"\d+ change\(s\) applied to your save", x["title"]) for x in n), [x["title"] for x in n[:5]]
            audit = j(S.get(f"{BASE}/audit"))
            assert not any(re.search(r"\b(PA|CA)\b[^;,]*\d+\s*→\s*\d+", a.get("detail") or "") for a in audit)
        finally:
            if bid:
                print("undo:", S.post(f"{BASE}/changes/batches/{bid}/undo").json())
            S.post(f"{BASE}/elite/nominations/{uid}/withdraw")


# ---------- PA/CA never exposed ----------
class TestHidden:
    def test_rankings_no_ca_pa(self):
        d = j(S.get(f"{BASE}/scouting/rankings"))
        assert d["rows"] and not any(k in r for r in d["rows"] for k in ("ca", "pa"))

    def test_rules_fields(self):
        for m in ("elite", "breakout", "squad", "scouting", "reports", "development"):
            d = j(S.get(f"{BASE}/rules/{m}"))
            assert "ca" not in d["fields"] and "pa" not in d["fields"]
            assert "defaults" in d and "changed_at" in d

    def test_changes_queue_hidden(self):
        for x in j(S.get(f"{BASE}/changes"))["queued"]:
            if x.get("field") in ("pa", "ca"):
                assert x.get("current") is None and x.get("new") is None

    def test_audit_rewritten(self):
        for a in j(S.get(f"{BASE}/audit?limit=500")):
            assert not re.search(r"\b(PA|CA)\b[^;,]*?\d+\s*→\s*\d+", a.get("detail") or ""), a["detail"]
            assert not re.search(r"\b(PA|CA)\b put back to \d+", a.get("detail") or ""), a["detail"]


# ---------- Rules screen impact / save / reset ----------
class TestRules:
    @pytest.mark.parametrize("module,key,val", [("squad", "max_senior", 24), ("scouting", None, None), ("reports", None, None), ("development", None, None)])
    def test_params_impact_save_reset(self, module, key, val):
        d = j(S.get(f"{BASE}/rules/{module}"))
        params = dict(d["data"]["params"])
        if key is None:
            key = list(params)[0]
            val = params[key] + 1
        params[key] = val
        imp = S.post(f"{BASE}/rules/{module}/impact", json={"data": {"params": params}})
        assert imp.status_code == 200, imp.text
        imp = imp.json()
        print(module, key, imp)
        assert isinstance(imp["affected"], int) and isinstance(imp["population"], int) and imp["note"]
        assert imp["affected"] <= imp["population"]
        v = d["version"]
        r = j(S.put(f"{BASE}/rules/{module}", json={"data": {"params": params}, "expected_version": v}))
        assert r["version"] == v + 1
        d2 = j(S.get(f"{BASE}/rules/{module}"))
        assert d2["data"]["params"][key] == val and key in d2["changed_at"]
        r = j(S.post(f"{BASE}/rules/{module}/reset", json={"expected_version": v + 1}))
        d3 = j(S.get(f"{BASE}/rules/{module}"))
        assert d3["data"] == d3["defaults"]

    def test_impact_bad_param(self):
        r = S.post(f"{BASE}/rules/squad/impact", json={"data": {"params": {"x": 1}}})
        assert r.status_code == 422

    def test_elite_rules_impact(self):
        d = j(S.get(f"{BASE}/rules/elite"))
        rules = [dict(x) for x in d["data"]["rules"]]
        rules[0] = rules[0] | {"conditions": [{"field": "age", "op": "<=", "value": 30}]}
        imp = S.post(f"{BASE}/rules/elite/impact", json={"data": {"rules": rules}})
        assert imp.status_code == 200, imp.text
        print("elite impact", imp.json())
        assert imp.json()["population"] > 0 and imp.json()["affected"] > 0


# ---------- DP settings ----------
class TestDPSettings:
    def test_settings_shape(self):
        d = j(S.get(f"{BASE}/dp/settings"))
        assert "changed_at" in d and "defaults" in d

    def test_impact_ok(self):
        d = j(S.get(f"{BASE}/dp/settings"))
        data = d["data"]
        data["score"]["rating_weight"], data["score"]["role_weight"] = 80, 20
        r = S.post(f"{BASE}/dp/settings/impact", json={"data": data})
        assert r.status_code == 200, r.text
        print("dp impact", r.json())
        assert r.json()["population"] > 0

    def test_impact_malformed_422(self):
        r = S.post(f"{BASE}/dp/settings/impact", json={"data": {"score": 1}})
        assert r.status_code == 422, f"{r.status_code} {r.text[:200]}"
