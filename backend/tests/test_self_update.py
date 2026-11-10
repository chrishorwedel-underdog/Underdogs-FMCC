import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from dotenv import load_dotenv  # noqa: E402

load_dotenv(Path(__file__).resolve().parents[1] / ".env")
import self_update as su  # noqa: E402


def test_notes_items_keeps_bullets_and_drops_housekeeping():
    body = "FMCC v0.2.3 for Windows 10/11.\n\nChanges:\n- Footer version tag\n- auto-commit for abc\n* Continent award tally\n- Footer version tag\n\nWindows may warn."
    assert su.notes_items(body) == ["Footer version tag", "Continent award tally"]


def test_notes_items_limit_and_empty():
    assert su.notes_items(None) == []
    assert len(su.notes_items("\n".join(f"- item {i}" for i in range(20)))) == 8


def test_notes_items_shortens_long_commit_lines():
    t = su.notes_items("- Award tally added **Bold** text " + "word " * 40 + "- second part")[0]
    assert len(t) <= 91 and t.endswith("…") and "**" not in t
