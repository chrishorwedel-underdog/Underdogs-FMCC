import os, re, requests, pytest

BASE = os.environ.get("REACT_APP_BACKEND_URL").rstrip("/") + "/api"
WORDS = {"Excellent fit": "g", "Good fit": "ok", "Fair fit": "a", "Poor fit": "r"}


# Elite Training: teams lists
class TestEliteTeams:
    def test_shape(self):
        d = requests.get(f"{BASE}/elite").json()
        assert set(d["teams"]) == {"U21", "U18"}
        assert isinstance(d["teams_from_save"], bool)
        for t, rows in d["teams"].items():
            for r in rows:
                assert set(r) == {"unique_id", "name", "age"}
                if not d["teams_from_save"]:
                    assert (r["age"] < 18) if t == "U18" else (18 <= r["age"] <= 20), r
            assert [r["name"] for r in rows] == sorted(r["name"] for r in rows)
        assert "suggestions" in d and "nominees" in d
        print("U21", len(d["teams"]["U21"]), "U18", len(d["teams"]["U18"]), "from_save", d["teams_from_save"], "nominees", len(d["nominees"]))

    def test_nominate_drops_from_list_then_withdraw(self):
        d = requests.get(f"{BASE}/elite").json()
        assert not d["nominees"], "expected 0 nominees at start"
        uid = d["teams"]["U21"][0]["unique_id"]
        r = requests.post(f"{BASE}/elite/nominations", json={"unique_id": uid, "note": ""})
        assert r.status_code == 200, r.text
        try:
            d2 = requests.get(f"{BASE}/elite").json()
            assert uid in [n["unique_id"] for n in d2["nominees"]]
            assert uid not in [x["unique_id"] for x in d2["teams"]["U21"] + d2["teams"]["U18"]]
            assert uid not in [x["unique_id"] for x in d2["suggestions"]]
        finally:
            w = requests.post(f"{BASE}/elite/nominations/{uid}/withdraw")
            assert w.status_code == 200
        d3 = requests.get(f"{BASE}/elite").json()
        assert not d3["nominees"]
        assert uid in [x["unique_id"] for x in d3["teams"]["U21"]]

    def test_no_ca_pa(self):
        txt = requests.get(f"{BASE}/elite").text
        assert '"ca"' not in txt and '"pa"' not in txt


# Tactic fit: role_fit words
class TestRoleFit:
    def _check(self, d):
        n = 0
        for s in d["slots"]:
            for r in s["ranked"]:
                rf = r["role_fit"]
                if rf is None:
                    continue
                n += 1
                assert set(rf) == {"word", "tone", "reason"}
                assert rf["word"] in WORDS and WORDS[rf["word"]] == rf["tone"]
                assert rf["reason"] and not re.search(r"\d", rf["reason"]), rf
        return n

    def test_default(self):
        d = requests.get(f"{BASE}/squad/tactic-fit").json()
        n = self._check(d)
        assert n > 0
        txt = str(d)
        assert "'ca'" not in txt and "'pa'" not in txt

    def test_role_change_changes_fit_not_order(self):
        d = requests.get(f"{BASE}/squad/tactic-fit", params={"formation": "433"}).json()
        base = {s["slot"]: s for s in d["slots"]}
        changed_any = False
        for s in d["slots"]:
            others = [o["key"] for o in s["role_options"] if o["key"] != s["role"]]
            if not others or len(s["ranked"]) < 1:
                continue
            for alt in others:
                d2 = requests.get(f"{BASE}/squad/tactic-fit", params={"formation": "433", "picks": f"{s['slot']}:{alt}"}).json()
                s2 = next(x for x in d2["slots"] if x["slot"] == s["slot"])
                assert s2["role"] == alt
                assert [r["unique_id"] for r in s2["ranked"]] == [r["unique_id"] for r in base[s["slot"]]["ranked"]]
                self._check(d2)
                if [r["role_fit"] for r in s2["ranked"]] != [r["role_fit"] for r in base[s["slot"]]["ranked"]]:
                    changed_any = True
        assert changed_any, "no role change altered role_fit"

    def test_all_formations(self):
        fs = requests.get(f"{BASE}/squad/tactic-fit").json()["formations"]
        for k, _ in fs:
            r = requests.get(f"{BASE}/squad/tactic-fit", params={"formation": k})
            assert r.status_code == 200, k
            self._check(r.json())
