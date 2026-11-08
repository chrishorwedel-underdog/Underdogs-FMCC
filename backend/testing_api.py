"""Test checklist for trying the Windows program on your PC, with an exportable report (personal paths hidden)."""
import json
import logging
import os
import re
from collections import deque
from typing import Literal

from fastapi import APIRouter, HTTPException
from fastapi.responses import Response
from pydantic import BaseModel, Field

from core import db, now_iso, new_id

router = APIRouter(prefix="/api/testing")
LIVE = os.environ.get("FMCC_READER") == "fmsave"
ITEMS = [
    ("setup", "Setup finds FM", "Run setup, pick your edition and press Find. The game folder, save folder and newest save all get a green tick."),
    ("read", "A real save is read", "After setup, Home shows the right in-game date and your squad has the right number of players."),
    ("backup", "A backup is created and restored", "Settings > Backups: make a backup, change something small, then restore it and check it's back."),
    ("auto_read", "Automatic save reading", "With FMCC open, save in FM. Within a minute FMCC shows the new in-game date without pressing refresh."),
    ("fm27_change", "FM27 change: preview, apply, verify, undo", "Queue one small FM27 change, preview it, apply it with FM open, check it in FM, then undo it."),
    ("matchlens", "FMMatchLens installs and is removed cleanly", "Connections: install FMMatchLens with FM closed, start FM and play a match, then remove it."),
    ("graphics", "Faces and logos appear in-game", "Give a player a face and a club a logo, then reload skins in FM and check they show."),
    ("punish", "Punish a Club file works", "Make a punishment, start a new career in FM, pick the FMCC file from the database list, and check the penalties took effect."),
    ("creator", "Created players appear in a new career", "Make a batch in Player Creator, start a new career with the FMCC file, and search for a few of the players: free agents with the right nationality, age and face."),
]
KEYS = {k for k, _, _ in ITEMS}


class _Ring(logging.Handler):
    def __init__(self):
        super().__init__(logging.INFO)
        self.lines = deque(maxlen=400)

    def emit(self, record):
        self.lines.append(f"{record.levelname} {record.name}: {record.getMessage()}"[:600])


RING = _Ring()
logging.getLogger().addHandler(RING)
logging.getLogger("fmcc").addHandler(RING)


def scrub(text: str) -> str:
    text = re.sub(r"(?i)([a-z]:[\\/]+users[\\/]+)[^\\/\s\"']+", r"\1[you]", text)
    return re.sub(r"(/(?:home|Users)/)[^/\s\"']+", r"\1[you]", text)


class ResultIn(BaseModel):
    status: Literal["pass", "fail", "untested"]
    note: str = Field(default="", max_length=500)


async def _latest() -> dict:
    pipe = [{"$sort": {"at": -1}}, {"$group": {"_id": "$key", "doc": {"$first": "$$ROOT"}}}]
    return {d["_id"]: {k: d["doc"][k] for k in ("status", "note", "at")} async for d in db.test_results.aggregate(pipe)}


@router.get("")
async def checklist():
    res = await _latest()
    return {"desktop": LIVE, "items": [{"key": k, "label": l, "how": h, **res.get(k, {"status": "untested", "note": "", "at": None})} for k, l, h in ITEMS]}


@router.put("/{key}")
async def set_result(key: str, body: ResultIn):
    if key not in KEYS:
        raise HTTPException(404, "Unknown test")
    await db.test_results.insert_one({"id": new_id(), "key": key, "status": body.status, "note": body.note.strip(), "at": now_iso()})
    return {"ok": True}


@router.get("/report")
async def report():
    s = await db.settings.find_one({"_id": "app"}, {"_id": 0, "active_career_id": 1}) or {}
    career = await db.careers.find_one({"id": s.get("active_career_id")}, {"_id": 0, "edition": 1}) if s.get("active_career_id") else None
    data = {"app": "FMCC", "version": os.environ.get("FMCC_VERSION", "dev"), "mode": "Windows program" if LIVE else "Browser preview",
            "edition": (career or {}).get("edition"), "generated_at": now_iso(), "results": (await checklist())["items"], "log": list(RING.lines)}
    body = scrub(json.dumps(data, indent=2, ensure_ascii=False))
    return Response(body, media_type="application/json", headers={"Content-Disposition": 'attachment; filename="fmcc-test-report.json"'})
