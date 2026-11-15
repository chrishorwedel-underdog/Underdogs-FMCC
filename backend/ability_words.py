"""True CA/PA never leave the backend: plain-words ability notes plus a response guard that strips raw values."""
import json
import re

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response

PROGRESS = [(3, "big", "Big step forward"), (1, "up", "Improving"), (0, "flat", "Holding steady"), (None, "down", "Slipped back a little")]
# Raw ability keys that must never reach the app (the editor/seed/creator tools are the user's own inputs and stay untouched).
SECRET_KEYS = {"ca", "pa", "ca_change", "pa_change", "start_ca", "goal_ca", "true_ca", "true_pa", "ca_gain_month", "ca_gain_season", "goal_so_far", "goal_gain"}
OPEN_PREFIXES = ("/api/editor", "/api/seed", "/api/creator")


def progress(delta: int | None) -> dict | None:
    if delta is None:
        return None
    for floor, tone, text in PROGRESS:
        if floor is None or delta >= floor:
            return {"tone": tone, "text": text}


def potential_words(delta: int) -> str:
    size = "small" if abs(delta) <= 3 else "solid" if abs(delta) <= 7 else "big"
    return f"a {size} {'boost to' if delta > 0 else 'drop in'} his potential"


def _words(m) -> str:
    d = int(m.group(2))
    return potential_words(d).removeprefix("a ") if m.group(1) == "potential" else ("current ability improved" if d > 0 else "current ability lowered")


NUM_TEXT = re.compile(r"\b(potential|current ability) ([+-]?\d+)\b")


def _scrub(v):
    if isinstance(v, dict):
        return {k: _scrub(x) for k, x in v.items() if k not in SECRET_KEYS}
    if isinstance(v, list):
        return [_scrub(x) for x in v]
    if isinstance(v, str) and ("potential" in v or "current ability" in v):
        return NUM_TEXT.sub(_words, v)
    return v


class AbilityGuard(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        resp = await call_next(request)
        path = request.url.path
        if not path.startswith("/api") or path.startswith(OPEN_PREFIXES) or "application/json" not in resp.headers.get("content-type", ""):
            return resp
        body = b"".join([c async for c in resp.body_iterator])
        try:
            data = _scrub(json.loads(body))
        except ValueError:
            return Response(body, status_code=resp.status_code, headers=dict(resp.headers))
        headers = {k: v for k, v in resp.headers.items() if k.lower() != "content-length"}
        return Response(json.dumps(data), status_code=resp.status_code, headers=headers, media_type="application/json")
