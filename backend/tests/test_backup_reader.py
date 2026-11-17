# Iteration 47: backup save reader (fm-open-scout fm_save_parser) with a fake parser, combine(), read_save fallback, check-save API
import json
import os
import stat
import sys
from pathlib import Path

import pytest
import requests

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")

import backup_reader  # noqa: E402
import fmsave_reader  # noqa: E402

BASE_URL = os.environ.get("REACT_APP_BACKEND_URL", "").rstrip("/")
if not BASE_URL:
    for line in Path("/app/frontend/.env").read_text().splitlines():
        if line.startswith("REACT_APP_BACKEND_URL="):
            BASE_URL = line.split("=", 1)[1].strip().rstrip("/")

KEYS = list(fmsave_reader.ATTR_MAP.keys())

RAW = {"version": {"game_version": "27.1.0", "major": 27, "current_date": "2026-10-15"}, "warnings": ["w1"],
       "players": [
           {"uid": 101, "name": "TEST_Striker", "date_of_birth": "2000-10-20", "nation_name": "Wales", "current_ability": 120, "potential_ability": -5,
            "club": {"uid": 900, "name": "Wrexham", "team_slot": 0}, "contract": {"ends": "2028-06-30", "weekly_wage": 5000},
            "positions": {"ST": 20, "AMC": 16, "DC": 14, "MC": 3}, "best_position": "ST", "attributes": {"pace": 15, "finishing": 14}},
           {"uid": 102, "name": "TEST_Defender", "date_of_birth": "1995-01-01", "nation_name": "England", "current_ability": 110, "potential_ability": 130,
            "club": {"uid": 900, "name": "Wrexham", "team_slot": 0}, "contract": {"ends": "2027-06-30", "weekly_wage": 3000},
            "positions": {"DC": 20, "DM": 15}, "best_position": "DC", "attributes": {"tackling": 16}},
           {"uid": 201, "name": "TEST_Other", "date_of_birth": "1998-03-03", "nation_name": "Spain", "current_ability": 100, "potential_ability": 100,
            "club": {"uid": 901, "name": "Wrexham Ladies", "team_slot": 0}, "contract": {}, "positions": {}, "best_position": "GK", "attributes": {}},
           {"uid": 301, "name": "TEST_Away", "date_of_birth": None, "nation_name": "", "current_ability": 90, "potential_ability": 95,
            "club": {"uid": 902, "name": "Chester", "team_slot": 0}, "contract": {}, "positions": {"MC": 18}, "best_position": "MC", "attributes": {}},
       ]}


@pytest.fixture
def fake_parser(tmp_path, monkeypatch):
    data = tmp_path / "players.json"
    data.write_text(json.dumps(RAW))
    exe = tmp_path / "fm_save_parser"
    exe.write_text(f"#!/bin/sh\n[ \"$1\" = players ] && [ \"$3\" = --json ] || exit 3\ncp '{data}' \"$4\"\n")
    exe.chmod(exe.stat().st_mode | stat.S_IEXEC)
    monkeypatch.setenv("FMCC_BACKUP_PARSER", str(exe))
    return data


@pytest.fixture
def save_file(tmp_path):
    p = tmp_path / "Chris Horwedel - Wrexham 27.fm"
    p.write_bytes(b"fake")
    return p


# backup_reader.read normalisation
class TestBackupRead:
    def test_normalized(self, fake_parser, save_file):
        d, err = backup_reader.read(save_file, KEYS)
        assert err is None
        assert d["fm_version"] == "27.1.0" and d["game_date"] == "2026-10-15"
        assert d["clubs"] == {900: "Wrexham", 901: "Wrexham Ladies", 902: "Chester"}
        assert set(d["players"]) == {101, 102, 201, 301}
        s = d["players"][101]
        assert s["positions"] == ["ST", "AM (C)"]
        assert s["age"] == 25  # birthday 20 Oct, current 15 Oct
        assert s["pa"] == 0 and s["ca"] == 120
        assert s["contract_end"] == "2028-06-30" and s["wage"] == 5000
        assert s["nationality"] == "Wales" and s["birth_date"] == "2000-10-20"
        assert set(s["attributes"]) == set(KEYS) and s["attributes"]["pace"] == 15
        assert d["players"][102]["positions"] == ["D (C)", "DM"]
        assert d["players"][201]["positions"] == ["GK"]  # best_position fallback
        assert d["players"][201]["contract_end"] == "2099-06-30" and d["players"][201]["wage"] is None
        assert d["players"][301]["age"] == 0

    def test_missing_parser(self, monkeypatch, save_file):
        monkeypatch.delenv("FMCC_BACKUP_PARSER", raising=False)
        assert backup_reader.read(save_file, KEYS) == (None, "it isn't installed")
        monkeypatch.setenv("FMCC_BACKUP_PARSER", "/nonexistent/parser.exe")
        assert backup_reader.read(save_file, KEYS) == (None, "it isn't installed")

    def test_failing_parser(self, tmp_path, monkeypatch, save_file):
        exe = tmp_path / "bad"
        exe.write_text("#!/bin/sh\necho 'unsupported save version 27.3' >&2\nexit 2\n")
        exe.chmod(0o755)
        monkeypatch.setenv("FMCC_BACKUP_PARSER", str(exe))
        d, err = backup_reader.read(save_file, KEYS)
        assert d is None and err == "unsupported save version 27.3"

    def test_bad_json(self, tmp_path, monkeypatch, save_file):
        exe = tmp_path / "badjson"
        exe.write_text("#!/bin/sh\necho 'not json' > \"$4\"\n")
        exe.chmod(0o755)
        monkeypatch.setenv("FMCC_BACKUP_PARSER", str(exe))
        d, err = backup_reader.read(save_file, KEYS)
        assert d is None and err


# read_save when fmsave is missing (main fails)
class TestReadSaveFallback:
    def test_backup_only(self, fake_parser, save_file):
        d = fmsave_reader.read_save(save_file, "", None)
        assert d["club_name"] == "Wrexham" and d["club_uid"] == 900
        assert {p["unique_id"] for p in d["players"]} == {101, 102}
        assert all(p["club"] == "Wrexham" and "club_uid" not in p for p in d["players"])
        assert d["readers"]["main"] == "failed" and d["readers"]["backup"] == "ok" and d["readers"]["backup_added"] == 2
        assert d["season"] == "2026/27" and d["game_date"] == "2026-10-15"
        assert d["skipped"] == fmsave_reader.MAIN_ONLY
        note = fmsave_reader.reader_note(d)
        assert note and "FM 27.1.0" in note and "fmsave" in note and "fm-open-scout" in note

    def test_no_backup_main_fails(self, monkeypatch, save_file):
        monkeypatch.delenv("FMCC_BACKUP_PARSER", raising=False)
        with pytest.raises(ValueError) as e:
            fmsave_reader.read_save(save_file, "", None)
        msg = str(e.value)
        assert "fmsave" in msg and "fm-open-scout" in msg and "isn't installed" in msg and "up to date" in msg
        import server
        assert server.read_error(save_file.name, e.value) == msg

    def test_ambiguous_backup_only(self, fake_parser, tmp_path):
        p = tmp_path / "Me - Career 27.fm"
        p.write_bytes(b"x")
        with pytest.raises(fmsave_reader.ClubNotFound) as e:
            fmsave_reader.read_save(p, "", None)
        assert {c["name"] for c in e.value.choices} == {"Wrexham", "Wrexham Ladies", "Chester"}


def _main_partial():
    return {"file_name": "x.fm", "club_name": "Wrexham", "club_uid": 900, "game_date": "2026-10-15", "season": "2026/27", "pool": [], "tables": [],
            "clubs": [{"uid": 900, "name": "Wrexham AFC", "league": "League One"}], "staff": [], "skipped": ["tactics"],
            "players": [
                {"unique_id": 101, "name": "Main Name", "positions": ["M (C)"], "contract_end": "2099-06-30", "wage": None, "nationality": "", "birth_date": "", "ca": 125, "pa": 140},
                {"unique_id": 102, "name": "Main Def", "positions": ["D (L)"], "contract_end": "2030-06-30", "wage": 9999, "nationality": "Scotland", "birth_date": "1995-01-02", "ca": 111, "pa": 131},
            ]}


# combine(): main wins conflicts, backup fills gaps
class TestCombine:
    def test_combine(self, fake_parser, save_file):
        backup, _ = backup_reader.read(save_file, KEYS)
        d = fmsave_reader.combine(_main_partial(), backup, None, save_file, "", None)
        by = {p["unique_id"]: p for p in d["players"]}
        assert by[101]["name"] == "Main Name" and by[101]["ca"] == 125
        assert by[101]["positions"] == ["ST", "AM (C)"] and by[101]["contract_end"] == "2028-06-30" and by[101]["wage"] == 5000
        assert by[101]["nationality"] == "Wales" and by[101]["birth_date"] == "2000-10-20"
        assert by[102]["positions"] == ["D (L)"] and by[102]["wage"] == 9999 and by[102]["nationality"] == "Scotland"
        assert by[102]["contract_end"] == "2030-06-30"
        assert set(by) == {101, 102}
        names = {c["uid"]: c["name"] for c in d["clubs"]}
        assert names[900] == "Wrexham AFC" and names[901] == "Wrexham Ladies" and names[902] == "Chester" and len(d["clubs"]) == 3
        r = d["readers"]
        assert r["main"] == "partial" and r["backup"] == "ok" and r["backup_added"] == 0 and r["backup_filled"] == 1
        assert "filled the gaps for 1" in fmsave_reader.reader_note(d)

    def test_combine_adds_missing(self, fake_parser, save_file):
        backup, _ = backup_reader.read(save_file, KEYS)
        m = _main_partial()
        m["players"] = m["players"][:1]
        m["skipped"] = []
        d = fmsave_reader.combine(m, backup, None, save_file, "", None)
        assert {p["unique_id"] for p in d["players"]} == {101, 102}
        assert d["readers"]["main"] == "ok" and d["readers"]["backup_added"] == 1 and d["readers"]["backup_filled"] == 1
        assert fmsave_reader.reader_note(d) is None  # quiet when the main read works

    def test_combine_backup_failed_and_missing(self, save_file):
        d = fmsave_reader.combine(_main_partial(), None, "boom", save_file, "", None)
        assert d["readers"]["backup"] == "failed" and "couldn't help either (boom)" in fmsave_reader.reader_note(d)
        d = fmsave_reader.combine(_main_partial(), None, "it isn't installed", save_file, "", None)
        assert d["readers"]["backup"] == "missing"

    def test_find_club_ambiguous_includes_backup(self):
        with pytest.raises(fmsave_reader.ClubNotFound) as e:
            fmsave_reader._find_club(None, {900: "Wrexham", 901: "Wrexham Ladies", 5: "Arsenal"}, "Me - Wrex 27", "", None, [])
        assert {c["name"] for c in e.value.choices} == {"Wrexham", "Wrexham Ladies", "Arsenal"}


# API: check-save in sample mode
class TestCheckSaveAPI:
    def test_sample_ok(self):
        r = requests.post(f"{BASE_URL}/api/setup/check-save", json={"path": "C:/games/Sample Club FC.fm", "club_name": "Sample Club FC"}, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is True and d["note"] is None and d["players"] > 0
        assert d["readers"]["main"] == "ok" and d["readers"]["backup"] == "sample"
        txt = r.text.lower()
        assert '"ca"' not in txt and '"pa"' not in txt

    def test_old_career_need_club(self):
        r = requests.post(f"{BASE_URL}/api/setup/check-save", json={"path": "C:/games/Old career.fm", "club_name": ""}, timeout=60)
        assert r.status_code == 200
        d = r.json()
        assert d["ok"] is False and d["need_club"] is True and len(d["clubs"]) > 1

    def test_updates_components(self):
        r = requests.post(f"{BASE_URL}/api/updates/check", timeout=90)
        assert r.status_code == 200
        row = next(c for c in r.json()["components"] if c["key"] == "fmopenscout")
        assert row["name"] == "fm-open-scout" and row["repo"] == "YanivGabay/fm-open-scout" and row["installed_version"] == "v0.2.0"
