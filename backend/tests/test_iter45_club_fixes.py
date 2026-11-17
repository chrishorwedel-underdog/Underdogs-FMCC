# Iteration 45: retest _likely whole-word matching and read_error NO_CLUB_LIST passthrough
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import fmsave_reader  # noqa: E402
from fmsave_reader import _likely, NO_CLUB_LIST, club_choices  # noqa: E402


# _likely whole words
def test_chester_not_likely_for_manchester():
    assert _likely("Chester", ["manchester"]) is False


def test_ham_not_likely_for_wrexham():
    assert _likely("Ham", ["wrexham"]) is False


def test_wrexham_afc_likely_for_wrexham():
    assert _likely("Wrexham AFC", ["wrexham"]) is True


def test_manchester_utd_likely_for_manchester():
    assert _likely("Manchester United", ["manchester"]) is True


def test_club_choices_manchester_save_does_not_tag_chester():
    rows = club_choices({1: "Chester", 2: "Manchester City", 3: "Arsenal"}, "Me - Manchester 27")
    tags = {r["name"]: r["likely"] for r in rows}
    assert tags["Chester"] is False and tags["Manchester City"] is True
    assert rows[0]["name"] == "Manchester City"


# read_error passthrough
def test_read_error_no_club_list_unchanged():
    os.environ.setdefault("MONGO_URL", "mongodb://localhost:27017")
    import server
    msg = server.read_error("Wrexham 27.fm", ValueError(NO_CLUB_LIST))
    assert msg == NO_CLUB_LIST
    assert msg.count("FMCC couldn't") == 1


def test_read_error_other_still_prefixed():
    import server
    msg = server.read_error("X.fm", ValueError("boom"))
    assert msg.startswith("FMCC couldn't read X.fm:")
