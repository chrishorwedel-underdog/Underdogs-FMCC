"""Checks fmsave_reader's world reading against a fake fmsave module shaped like fmsave's documented records."""
import sys
import types
from datetime import date
from pathlib import Path
from types import SimpleNamespace as NS

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import fmsave_reader  # noqa: E402


class Rows(list):
    def where(self, **kw):
        return Rows(x for x in self if all(getattr(x, k) == v for k, v in kw.items()))


def _player(uid, club, nation_id, nat):
    return NS(uid=uid, unique_id=uid, name=f"Player {uid}", birth_date=date(2000, 1, 1), age=25, nation_id=nation_id, nationality=NS(name=nat),
              positions=["ST"], ability=NS(current=120, potential=150), contract=NS(end_date=date(2029, 6, 30), wage=1000), transfer_value=2_000_000,
              club_uid=club, home_grown=False, attributes=NS())


class FakeSave:
    game_date = date(2027, 10, 1)

    def __enter__(self):
        return self

    def __exit__(self, *a):
        return False

    def managed_clubs(self):
        return [NS(club_uid=1, name="My FC")]

    def clubs(self):
        return [NS(club_uid=1, name="My FC", nation_id=10, gender="Male"), NS(club_uid=2, name="Rival", nation_id=10, gender="Male"),
                NS(club_uid=3, name="Far Away", nation_id=20, gender="Male"), NS(club_uid=4, name="Unloaded", nation_id=30, gender="Male")]

    def players(self):
        return Rows([_player(100, 1, 10, "England"), _player(200, 2, 10, "England"), _player(300, 3, 20, "Spain"), _player(400, 4, 30, "Peru")])

    def player_season_stats(self):
        base = dict(starts=5, substitute_appearances=1, minutes=480, goals=3, assists=2, average_rating=7.1, rated_appearances=6,
                    non_penalty_expected_goals=2.4, expected_assists=1.2, open_play_key_passes=8, clear_cut_chances_created=3, progressive_passes=20,
                    dribbles=9, tackles_completed=4, possession_won=12, expected_goals_prevented=0, blocks=1, clearances=2, pressures_attempted=40,
                    pressures_completed=12, saves_held=0, saves_parried=0, saves_tipped=0, shots_on_target_faced=0)
        return [NS(player_uid=u, **base) for u in (100, 200, 300, 400)]

    def league_tables(self):
        return [NS(competition_id=7, competition_name=None, rows=[NS(club_uid=2, position=1, played=6, won=5, drawn=1, lost=0, goals_for=12, goals_against=3, points=16),
                                                                 NS(club_uid=1, position=2, played=6, won=4, drawn=1, lost=1, goals_for=9, goals_against=5, points=13)]),
                NS(competition_id=8, competition_name="La Liga", rows=[NS(club_uid=3, position=1, played=6, won=3, drawn=3, lost=0, goals_for=8, goals_against=4, points=12)])]

    def transfers(self):
        return [NS(player_uid=300, from_club_name="Rival", transfer_fee=15_000_000, transfer_date=date(2027, 8, 20))]


def test_world_read(tmp_path):
    sys.modules["fmsave"] = types.SimpleNamespace(open=lambda p: FakeSave())
    f = tmp_path / "career.fm"
    f.write_text("x")
    out = fmsave_reader.read_save(f, "My FC")
    assert [p["unique_id"] for p in out["players"]] == [100]
    assert out["players"][0]["appearances"] == 6 and out["players"][0]["avg_rating"] == 7.1
    pool = {p["unique_id"]: p for p in out["pool"]}
    assert set(pool) == {200, 300}, "only players from clubs in a loaded league table"
    assert pool[200]["league"] == "Competition 7" and pool[200]["country"] == "England"
    assert pool[300]["league"] == "La Liga" and pool[300]["country"] == "Spain"
    assert pool[300]["last_move"]["fee"] == 15_000_000
    assert pool[200]["stats"]["npxg"] == 0.45 and pool[200]["stats"]["prr"] == 30.0
    t = {x["league"]: x for x in out["tables"]}
    assert t["Competition 7"]["rows"][0] == {"club": "Rival", "pos": 1, "p": 6, "w": 5, "d": 1, "l": 0, "gf": 12, "ga": 3, "pts": 16, "gd": 9}
    assert t["La Liga"]["country"] == "Spain"
