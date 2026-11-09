"""Unnamed save competitions get names from the league strength workbook."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")  # world_api imports core; nothing here touches the database
import world_api  # noqa: E402

WB = [{"name": "Premier League", "country": "England", "tier": 1, "teams": 20, "rank": 1}, {"name": "EFL Championship", "country": "England", "tier": 2, "teams": 24, "rank": 20},
      {"name": "EFL League One", "country": "England", "tier": 3, "teams": 24, "rank": 60}, {"name": "La Liga", "country": "Spain", "tier": 1, "teams": 20, "rank": 2}]


def _t(name, country, rep, n):
    return {"league": name, "country": country, "reputation": rep, "rows": [{"club": f"c{i}"} for i in range(n)], "women": False}


def test_names_by_country_and_level():
    tables = [_t("Competition 7", "England", 5000, 24), _t("Competition 3", "England", 9000, 20), _t("Competition 9", "Spain", 8500, 20), _t("Competition 11", "Peru", 3000, 18)]
    pool = [{"league": "Competition 7"}, {"league": "Competition 11"}]
    renames = world_api.name_unnamed(tables, pool, WB)
    assert renames == {"Competition 3": "Premier League", "Competition 7": "EFL Championship", "Competition 9": "La Liga"}
    assert pool[0]["league"] == "EFL Championship" and pool[1]["league"] == "Competition 11"
    assert all(t.get("named_from_workbook") for t in tables[:3])


def test_named_tables_keep_their_names_and_tier():
    tables = [_t("Premier League", "England", 9000, 20), _t("Competition 7", "England", 5000, 24)]
    assert world_api.name_unnamed(tables, [], WB) == {"Competition 7": "EFL Championship"}
