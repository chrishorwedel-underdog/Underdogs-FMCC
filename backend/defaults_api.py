"""Defaults for new games: settings saved once and offered to every career started with FMCC's setup. Existing careers never change."""
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel

from core import db, active_career, logger, now_iso
import rules_api

router = APIRouter(prefix="/api/defaults")
AREAS = {"punish": "Punish a Club penalties", "seed": "Seed a Surname setup", "features": "Features on or off",
         "appearance": "Appearance and text size", "rules": "Dynamic Potential, Elite Training and Breakout Player rules"}
RULE_MODULES = ("dp", "elite", "breakout")


class AppearanceIn(BaseModel):
    appearance: dict | None = None


async def _doc() -> dict:
    return await db.defaults.find_one({"_id": "defaults"}) or {"areas": {}}


@router.get("")
async def get_defaults():
    d = await _doc()
    return {"areas": [{"key": k, "label": lab, "saved": k in d["areas"], "saved_at": (d["areas"].get(k) or {}).get("at")} for k, lab in AREAS.items()],
            "appearance": (d["areas"].get("appearance") or {}).get("data")}


@router.post("/{area}/save")
async def save_default(area: str, body: AppearanceIn):
    if area not in AREAS:
        raise HTTPException(404, "Unknown area")
    c = await active_career()
    if area == "features":
        data = c.get("features") or {}
    elif area == "appearance":
        if not body.appearance:
            raise HTTPException(422, "Nothing to save")
        data = body.appearance
    elif area == "rules":
        data = {m: (await rules_api.current(c["id"], m)).get("data") for m in RULE_MODULES}
    elif area == "punish":
        pipe = [{"$match": {"career_id": c["id"]}}, {"$sort": {"revision": -1}}, {"$group": {"_id": "$pid", "doc": {"$first": "$$ROOT"}}}]
        data = [{"club": {k: d["doc"]["club"].get(k) for k in ("name", "nation", "country")}, "penalties": d["doc"]["penalties"], "name": d["doc"].get("name", "")}
                async for d in db.punishments.aggregate(pipe) if d["doc"].get("status") == "active"]
        if not data:
            raise HTTPException(409, "This career has no club penalties to save yet")
    else:
        d = await db.seed_drafts.find_one({"career_id": c["id"]}, {"_id": 0, "settings": 1})
        if not d or not d.get("settings"):
            raise HTTPException(409, "Make a Seed a Surname setup in this career first")
        data = d["settings"]
    await db.defaults.update_one({"_id": "defaults"}, {"$set": {f"areas.{area}": {"data": data, "at": now_iso()}}}, upsert=True)
    return {"ok": True}


@router.delete("/{area}")
async def clear_default(area: str):
    await db.defaults.update_one({"_id": "defaults"}, {"$unset": {f"areas.{area}": ""}})
    return {"ok": True}


async def _bell(cid: str, key: str, title: str, text: str):
    from notify_api import _add
    snap = await db.snapshots.find_one({"career_id": cid}, {"_id": 0, "game_date": 1}, sort=[("save_no", -1)]) or {}
    await _add(cid, "changes", f"defaults:{key}", title, text, snap.get("game_date"))


async def apply_defaults(c: dict, areas: list) -> None:
    """Right after a new career's first save read: features and rules now, then penalties and Seed a Surname on the new save."""
    saved = (await _doc())["areas"]
    use = [a for a in areas if a in saved]
    if "features" in use:
        await db.careers.update_one({"id": c["id"]}, {"$set": {"features": saved["features"]["data"]}})
    if "rules" in use:
        for m, data in (saved["rules"]["data"] or {}).items():
            if data:
                try:
                    cur = await rules_api.current(c["id"], m)
                    await rules_api.save_version(c["id"], m, data, cur.get("version", 0), "From your defaults for new games")
                except Exception as exc:  # noqa: BLE001
                    logger.warning("default rules %s skipped: %s", m, exc)
    if "punish" in use:
        await _apply_punish(c, saved["punish"]["data"])
    if "seed" in use:
        import seed_api
        try:
            await seed_api.create(seed_api.SeedIn(**saved["seed"]["data"]))
            await _bell(c["id"], "seed", "Seed a Surname is ready to review", "Your default Seed a Surname setup ran on this save. Open Seed a Surname to check and apply it.")
        except Exception as exc:  # noqa: BLE001
            await _bell(c["id"], "seed-failed", "Your Seed a Surname default couldn't run", str(getattr(exc, "detail", exc))[:300])


async def _apply_punish(c: dict, items: list):
    import editor_api
    import punish_api
    clubs = await editor_api.clubs(c)
    for it in items:
        want = it["club"]
        hits = [x for x in clubs if x["name"].lower() == (want.get("name") or "").lower()
                and (not (want.get("nation") or want.get("country")) or (x.get("nation") or x.get("country")) in (want.get("nation"), want.get("country"), None))]
        if len(hits) != 1:
            why = "isn't in this save" if not hits else f"matches {len(hits)} clubs in this save. Make this penalty yourself in Punish a Club to pick the right one"
            await _bell(c["id"], f"punish:{want.get('name')}", f"Default penalty for {want.get('name')} not applied", f"{want.get('name')} {why}.")
            continue
        try:
            await punish_api.create(punish_api.PunishIn(club_uid=hits[0]["uid"], penalties=it["penalties"], name=it.get("name", "")))
        except Exception as exc:  # noqa: BLE001
            await _bell(c["id"], f"punish:{want.get('name')}", f"Default penalty for {want.get('name')} not applied", str(getattr(exc, "detail", exc))[:300])
