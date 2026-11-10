"""Per-career feature switches: which left-menu features are on in this career. Off features keep their data but do no automatic work."""
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel

from core import db, active_career, audit

router = APIRouter(prefix="/api/features")
KEYS = ["dp", "breakout", "scouting", "reports", "moneyball", "squad", "development", "elite", "matches", "editor", "punish", "dof"]
PATHS = {"/dynamic-potential": "dp", "/breakout": "breakout", "/scouting": "scouting", "/reports": "reports", "/moneyball": "moneyball", "/squad": "squad",
         "/development": "development", "/elite-training": "elite", "/matches": "matches", "/editor": "editor", "/punish": "punish", "/dof": "dof"}
COUNTDOWN = {"reports": "reports", "development": "development", "dp": "dp", "elite": "elite", "breakout": "breakout", "window": "scouting", "squad": "squad"}


def state(c: dict) -> dict:
    return {k: True for k in KEYS} | {k: bool(v) for k, v in (c.get("features") or {}).items() if k in KEYS}


def off(c: dict) -> set:
    return {k for k, v in state(c).items() if not v}


def path_off(link: str | None, offs: set) -> bool:
    return PATHS.get((link or "").split("?")[0]) in offs


async def require(key: str):
    c = await active_career()
    if key in off(c):
        raise HTTPException(409, "This feature is turned off for this career. Turn it on in Features.")


def need(key: str):
    async def dep():
        await require(key)
    return [Depends(dep)]


@router.get("")
async def get_features():
    c = await active_career()
    return {"features": state(c), "seen": bool(c.get("features_seen")), "ask": not c.get("features_seen") and (c.get("next_save_no") or 0) > 0}


class FeaturesIn(BaseModel):
    features: dict[str, bool]


@router.put("")
async def put_features(body: FeaturesIn):
    c = await active_career()
    bad = [k for k in body.features if k not in KEYS]
    if bad:
        raise HTTPException(422, f"Unknown feature: {bad[0]}")
    new = state(c) | body.features
    await db.careers.update_one({"id": c["id"]}, {"$set": {"features": new}})
    changed = [k for k in KEYS if new[k] != state(c)[k]]
    if changed:
        await audit(c["id"], "features changed", "features", ", ".join(f"{k} {'on' if new[k] else 'off'}" for k in changed))
    return {"features": new}


@router.post("/seen")
async def seen():
    c = await active_career()
    await db.careers.update_one({"id": c["id"]}, {"$set": {"features_seen": True}})
    return {"ok": True}
