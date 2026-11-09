"""Tactics read from a save map to the closest FMCC formation."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import roles  # noqa: E402


def test_codes_pick_the_shape():
    assert roles.match_tactic({"name": "Gegenpress", "positions": ["GK", "DR", "DCR", "DCL", "DL", "DMCR", "DMCL", "AMR", "AMC", "AML", "STC"]}) in ("4231", "4231n")
    assert roles.match_tactic({"name": "x", "positions": ["GK", "DCR", "DC", "DCL", "WBR", "WBL", "DMC", "MCR", "MCL", "STCR", "STCL"]}) == "352"
    assert roles.match_tactic({"name": "x", "positions": ["GK", "DR", "DCR", "DCL", "DL", "MR", "MCR", "MCL", "ML", "STCR", "STCL"]}) == "442"


def test_name_fallback_and_unknown():
    assert roles.match_tactic({"name": "My 5-3-2 wingbacks", "positions": [1, 2, 3]}) == "532"
    assert roles.match_tactic({"name": "Mystery", "positions": []}) is None
