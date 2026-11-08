"""DOF chat: a Director of Football that streams answers and can draft actions you must accept."""
import json
import os
import re

from fastapi import APIRouter, HTTPException
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field
from emergentintegrations.llm.chat import LlmChat, UserMessage, TextDelta, StreamDone

import roles
from core import db, active_career, latest_two, month_minutes, now_iso, new_id, logger
from matches_api import season_per90
from rules_api import current as current_rules
from sample_reader import GROUP

router = APIRouter(prefix="/api/dof")
MODEL = ("openai", "gpt-5.6-terra")
MARK = "ACTION:"
SUGGESTED = ["Who should start the next game to give my U21s minutes?", "Which veteran should I sell this summer?",
             "Where am I weakest?", "Who is my most effective presser?", "Which striker is underperforming his xG?"]


def api_key():
    return os.environ.get("OPENAI_API_KEY") or os.environ.get("EMERGENT_LLM_KEY")


async def build_context(c: dict) -> str:
    snaps = await latest_two(c["id"])
    latest = snaps[0]
    mins = month_minutes(latest, snaps[1] if len(snaps) > 1 else None)
    form = roles.formation_meta("433")
    depth = roles.depth_chart(latest["players"], form)
    best = roles.best_xi(latest["players"], form, depth)
    rules = {k: int(v) for k, v in (await current_rules(c["id"], "squad"))["data"]["params"].items()}
    info = {p["unique_id"]: {"name": p["name"], "age": p["age"], "u21": p["age"] < 21, "month_minutes": mins[p["unique_id"]]} for p in latest["players"]}
    dev, _, _ = roles.development_xi(best, form, depth, info, rules)
    per90 = await season_per90(c["id"], latest["season"], "us")
    squad = "\n".join(
        f"- id {p['unique_id']} | {p['name']} | age {p['age']} | {'/'.join(p['positions'])} | CA {p['ca']} PA {p['pa']} | best role {roles.best_role(p)['name']} {roles.best_role(p)['rating']} | "
        f"season minutes {p['minutes']} (last month {mins[p['unique_id']]}) | avg rating {p.get('avg_rating')} | contract to {p['contract_end']}"
        + (f" | per90 xG {per90[p['unique_id']]['per90']['xg']} xA {per90[p['unique_id']]['per90']['xa']} pressures {per90[p['unique_id']]['per90']['pressures']} "
           f"goals {per90[p['unique_id']]['goals']}" if p["unique_id"] in per90 else "") for p in latest["players"])
    name = lambda u: info[u]["name"] if u else "-"  # noqa: E731
    matches = await db.matches.find({"career_id": c["id"]}, {"_id": 0, "date": 1, "opponent": 1, "score": 1, "xg": 1}).sort("date", -1).limit(5).to_list(5)
    seen = sorted((await season_per90(c["id"], latest["season"], "them")).values(), key=lambda a: -a["avg_rating"])[:8]
    sl_pipe = [{"$match": {"career_id": c["id"]}}, {"$sort": {"at": -1}}, {"$group": {"_id": "$unique_id", "status": {"$first": "$status"}}}, {"$match": {"status": "active"}}]
    sl_ids = [d["_id"] async for d in db.shortlist.aggregate(sl_pipe)]
    pool = await db.pools.find_one({"career_id": c["id"]}, {"_id": 0, "players": 1}) or {"players": []}
    pool_by = {p["unique_id"]: p for p in pool["players"]}
    groups = {}
    for p in sorted(pool["players"], key=lambda p: -(p["pa"] + p["ca"])):
        g = GROUP[p["positions"][0]]
        if len(groups.setdefault(g, [])) < 4:
            groups[g].append(p)
    pool_lines = "; ".join(f"id {p['unique_id']} {p['name']} {p['age']} {'/'.join(p['positions'])} {p['club']} CA {p['ca']} PA {p['pa']} value {p['value']}" for ps in groups.values() for p in ps)
    plans = await db.plans.find({"career_id": c["id"]}, {"_id": 0, "name": 1, "minutes_target": 1, "loan": 1, "revision": 1}).sort("revision", -1).to_list(30)
    pending = await db.changes.count_documents({"career_id": c["id"], "status": "queued"})
    return f"""Club: {c['club_name']} ({c['edition']}), game date {latest['game_date']}, season {latest['season']}.
SQUAD:
{squad}
BEST XI (4-3-3, strength {roles.strength(best, depth)}): {', '.join(f"{k} {name(u)}" for k, u in best.items())}
DEVELOPMENT XI (strength {roles.strength(dev, depth)}): {', '.join(f"{k} {name(u)}" for k, u in dev.items())}
DEVELOPMENT RULES: U21 monthly target {rules['target_minutes']} min, max {rules['max_youth']} U21 starters, max team drop {rules['max_team_drop']}.
RECENT MATCHES: {'; '.join(f"{m['date']} vs {m['opponent']} {m['score']['us']}-{m['score']['them']} (xG {m['xg']['us']}-{m['xg']['them']})" for m in matches) or 'none recorded'}
OPPONENTS SEEN VS US (scouting ids): {'; '.join(f"id {a['unique_id']} {a['name']} ({a['club']}) rating {a['avg_rating']}" for a in seen) or 'none'}
SHORTLIST: {', '.join(pool_by[i]['name'] + f" ({pool_by[i]['club']}, id {i})" for i in sl_ids if i in pool_by) or 'empty'}
SCOUTING POOL (best 4 per position group): {pool_lines}
DEVELOPMENT PLANS: {'; '.join(f"{p['name']} {p['minutes_target']} min, {p['loan']}" for p in plans[:12]) or 'none'}
GAME CHANGES WAITING FOR APPROVAL: {pending}"""


SYSTEM = """You are the Director of Football inside FMCC, a companion app for Football Manager. The manager has final authority.
Answer in plain, confident football language, short paragraphs or a few bullets, using player names and the numbers from the data below. Never invent players or numbers.
Never reveal, estimate or discuss Dynamic Potential values or whether a player's potential was changed by it.
You may draft ONE action when it clearly helps. Put it on the very last line, exactly in this form, with nothing after it:
ACTION: {"type": "lineup", "kind": "dev" or "best", "formation": "433" or "4231", "summary": "..."}
ACTION: {"type": "shortlist", "unique_id": <scouting id>, "summary": "..."}
ACTION: {"type": "nomination", "module": "elite" or "breakout", "unique_id": <squad id>, "summary": "..."}
ACTION: {"type": "plan", "unique_id": <squad id>, "minutes_target": <int>, "loan": "none" | "loan_lower" | "loan_same" | "loan_abroad", "summary": "..."}
The manager must click Accept before anything is saved, so describe the draft as a suggestion.

CURRENT DATA:
"""


def split_action(text: str):
    if MARK not in text:
        return text.strip(), None
    body, _, tail = text.rpartition(MARK)
    try:
        action = json.loads(re.search(r"\{.*\}", tail, re.S).group(0))
        if action.get("type") not in ("lineup", "shortlist", "nomination", "plan"):
            action = None
    except (json.JSONDecodeError, AttributeError):
        action = None
    return body.strip().rstrip("`").strip(), action


class NewConv(BaseModel):
    title: str = Field("", max_length=80)


class Ask(BaseModel):
    text: str = Field(min_length=1, max_length=2000)


@router.get("/status")
async def status():
    return {"ready": bool(api_key()), "model": MODEL[1], "suggested": SUGGESTED,
            "key_source": "Your OpenAI key" if os.environ.get("OPENAI_API_KEY") else "Emergent universal key (preview)"}


@router.get("/conversations")
async def conversations():
    c = await active_career()
    return await db.dof_conversations.find({"career_id": c["id"]}, {"_id": 0}).sort("updated_at", -1).to_list(100)


@router.post("/conversations")
async def new_conversation(body: NewConv):
    c = await active_career()
    doc = {"id": new_id(), "career_id": c["id"], "title": body.title or "New conversation", "created_at": now_iso(), "updated_at": now_iso()}
    await db.dof_conversations.insert_one(dict(doc))
    return doc


async def _conv(c, conv_id):
    conv = await db.dof_conversations.find_one({"id": conv_id, "career_id": c["id"]}, {"_id": 0})
    if not conv:
        raise HTTPException(404, "Conversation not found")
    return conv


@router.get("/conversations/{conv_id}/messages")
async def messages(conv_id: str):
    c = await active_career()
    await _conv(c, conv_id)
    return await db.dof_messages.find({"conversation_id": conv_id}, {"_id": 0}).sort("at", 1).to_list(500)


@router.post("/conversations/{conv_id}/stream")
async def stream(conv_id: str, body: Ask):
    c = await active_career()
    conv = await _conv(c, conv_id)
    key = api_key()
    if not key:
        raise HTTPException(503, "Add your OpenAI key in Settings to use the DOF chat")
    history = await db.dof_messages.find({"conversation_id": conv_id}, {"_id": 0, "role": 1, "content": 1}).sort("at", 1).to_list(500)
    context = await build_context(c)
    transcript = "\n".join(f"{'Manager' if m['role'] == 'user' else 'DOF'}: {m['content']}" for m in history[-12:])
    await db.dof_messages.insert_one({"id": new_id(), "conversation_id": conv_id, "role": "user", "content": body.text, "at": now_iso()})
    if conv["title"] == "New conversation":
        await db.dof_conversations.update_one({"id": conv_id}, {"$set": {"title": body.text[:60]}})
    system = SYSTEM + context + (f"\n\nEARLIER IN THIS CONVERSATION:\n{transcript}" if transcript else "")
    chat = LlmChat(api_key=key, session_id=f"dof-{conv_id}-{new_id()}", system_message=system).with_model(*MODEL)

    async def gen():
        full = ""
        try:
            async for ev in chat.stream_message(UserMessage(text=body.text)):
                if isinstance(ev, TextDelta):
                    full += ev.content
                    yield f"data: {json.dumps({'t': 'delta', 'c': ev.content})}\n\n"
                elif isinstance(ev, StreamDone):
                    break
        except Exception as exc:
            logger.error("dof stream failed: %s", exc)
            yield f"data: {json.dumps({'t': 'error', 'c': 'The DOF could not answer right now. Please try again.'})}\n\n"
            return
        text, action = split_action(full)
        msg = {"id": new_id(), "conversation_id": conv_id, "role": "assistant", "content": text, "at": now_iso(),
               "draft": {"action": action, "status": "pending"} if action else None}
        await db.dof_messages.insert_one(dict(msg))
        await db.dof_conversations.update_one({"id": conv_id}, {"$set": {"updated_at": now_iso()}})
        yield f"data: {json.dumps({'t': 'done', 'message': msg})}\n\n"

    return StreamingResponse(gen(), media_type="text/event-stream", headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"})


async def _draft_msg(c, msg_id):
    m = await db.dof_messages.find_one({"id": msg_id}, {"_id": 0})
    if not m or not m.get("draft"):
        raise HTTPException(404, "Draft not found")
    await _conv(c, m["conversation_id"])
    if m["draft"]["status"] != "pending":
        raise HTTPException(409, "This draft was already handled")
    return m


@router.post("/messages/{msg_id}/accept")
async def accept(msg_id: str):
    import awards_api
    import plans_api
    import scouting_api
    import squad_api
    c = await active_career()
    m = await _draft_msg(c, msg_id)
    a = m["draft"]["action"]
    claimed = await db.dof_messages.update_one({"id": msg_id, "draft.status": "pending"}, {"$set": {"draft.status": "accepting"}})
    if not claimed.modified_count:
        raise HTTPException(409, "This draft was already handled")
    try:
        if a["type"] == "lineup":
            plan = await squad_api.squad_plan(a.get("formation", "433"))
            saved = await db.lineups.find_one({"career_id": c["id"], "formation": plan["formation"]["key"]}, {"_id": 0, "revision": 1}, sort=[("revision", -1)])
            res = await squad_api.save_lineup(squad_api.LineupIn(formation=plan["formation"]["key"], kind=a.get("kind", "dev"), slots=plan[a.get("kind", "dev")]["slots"],
                                                                 based_on_save_no=plan["save_no"], expected_revision=saved["revision"] if saved else 0, name="Drafted by DOF"))
            done = f"Lineup saved (version {res['revision']})"
        elif a["type"] == "shortlist":
            await scouting_api.shortlist(scouting_api.ShortlistIn(unique_id=int(a["unique_id"]), action="add"))
            done = "Added to your shortlist"
        elif a["type"] == "nomination":
            mod = a.get("module", "elite")
            await awards_api._nominate(c, mod if mod in ("elite", "breakout") else "elite", int(a["unique_id"]), "active", "Suggested by DOF")
            done = "Nomination saved"
        else:
            prev = await db.plans.find_one({"career_id": c["id"], "unique_id": int(a["unique_id"])}, {"_id": 0, "revision": 1}, sort=[("revision", -1)])
            await plans_api.save_plan(plans_api.PlanIn(unique_id=int(a["unique_id"]), minutes_target=int(a.get("minutes_target", 270)), loan=a.get("loan", "none"),
                                                       note="Drafted by DOF", expected_revision=prev["revision"] if prev else 0))
            done = "Development plan saved"
    except HTTPException:
        await db.dof_messages.update_one({"id": msg_id}, {"$set": {"draft.status": "pending"}})
        raise
    except Exception:
        await db.dof_messages.update_one({"id": msg_id}, {"$set": {"draft.status": "pending"}})
        raise HTTPException(422, "This draft refers to something that no longer exists")
    await db.dof_messages.update_one({"id": msg_id}, {"$set": {"draft.status": "accepted", "draft.result": done}})
    return {"result": done}


@router.post("/messages/{msg_id}/dismiss")
async def dismiss(msg_id: str):
    c = await active_career()
    await _draft_msg(c, msg_id)
    await db.dof_messages.update_one({"id": msg_id}, {"$set": {"draft.status": "dismissed"}})
    return {"ok": True}
