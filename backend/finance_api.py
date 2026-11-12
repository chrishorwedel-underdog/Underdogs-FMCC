"""Club money health for the finance strip. Reads only what the save provides; missing figures stay missing, never estimated."""
from fastapi import APIRouter

from core import db, active_career

router = APIRouter(prefix="/api")
FFP = {"comfortable": ("gold", "Comfortably within the rules"), "compliant": ("green", "Within the rules"),
       "at_risk": ("red", "At risk of breaking the rules"), "breach": ("red", "Breaking the rules")}


def _money(v: int) -> str:
    s = "-" if v < 0 else ""
    v = abs(v)
    return f"{s}£{v / 1_000_000:.1f}m" if v >= 1_000_000 else f"{s}£{round(v / 1000)}k"


def _item(key: str, label: str, value, tone=None, reason=None) -> dict:
    if value is None:
        return {"key": key, "label": label, "value": None, "text": "Not in save yet", "tone": "missing", "reason": "This save doesn't include this figure yet"}
    return {"key": key, "label": label, "value": value, "text": value if isinstance(value, str) else _money(value), "tone": tone, "reason": reason}


def assess(f: dict) -> list:
    out = []
    ffp = f.get("ffp_status")
    tone, why = FFP.get(ffp, (None, None))
    out.append(_item("ffp", "FFP", {"comfortable": "Comfortable", "compliant": "Compliant", "at_risk": "At risk", "breach": "Breaching"}.get(ffp), tone, why))
    wages, turnover = f.get("wage_bill"), f.get("turnover")
    if wages is not None and turnover:
        r = round(100 * wages / turnover)
        tone = "gold" if r < 50 else "green" if r <= 70 else "red"
        out.append(_item("wages", "Wages/Turnover", f"{r}%", tone, f"Wages are {r}% of turnover. Under 50% is excellent, 50–70% healthy, over 70% trouble."))
    else:
        out.append(_item("wages", "Wages/Turnover", None))
    spent, left = f.get("transfer_spent"), f.get("transfer_budget")
    total = (spent or 0) + (left or 0) if spent is not None and left is not None else None
    if spent is None:
        out.append(_item("spent", "Incoming Transfers", None))
    else:
        share = round(100 * spent / total) if total and total > 0 else None
        tone = "red" if left is not None and left < 0 else "gold" if share is not None and share <= 50 else "green"
        out.append(_item("spent", "Incoming Transfers", spent, tone, f"Spent on players bought this season · {share}% of this year's transfer budget used" if share is not None else "Spent on players bought this season"))
    sold = f.get("transfer_received")
    net = sold - spent if sold is not None and spent is not None else None
    net_txt = None if net is None else f"Net spend {'+' if net > 0 else ''}{_money(net)} (sales minus purchases)"
    if spent is not None and net_txt:
        out[-1]["reason"] = f"{out[-1]['reason']} · {net_txt}"
    out.append(_item("sold", "Outgoing Transfers", None) if sold is None else _item("sold", "Outgoing Transfers", sold, "green" if sold > 0 else None, ("Made selling players this season" if sold > 0 else "No players sold this season yet") + (f" · {net_txt}" if net_txt else "")))
    out.append(_item("net", "Net Spend", None) if net is None else _item("net", "Net Spend", f"{'+' if net > 0 else ''}{_money(net)}", "green" if net >= 0 else "gold", "Sales minus purchases this season. Positive means you've made more than you've spent.") | {"amount": net})
    if left is None:
        out.append(_item("budget", "Budget Left", None))
    else:
        share = round(100 * left / total) if total and total > 0 else None
        tone = "red" if left <= 0 else "gold" if share is not None and share >= 50 else "green"
        out.append(_item("budget", "Budget Left", left, tone, "No transfer money left" if left <= 0 else f"{share}% of this year's transfer budget still to spend" if share is not None else "Transfer budget remaining"))
    bank = f.get("bank_balance")
    if bank is None:
        out.append(_item("bank", "Bank", None))
    else:
        tone = "red" if bank < 0 else "gold" if turnover and bank >= turnover / 2 else "green"
        out.append(_item("bank", "Bank", bank, tone, "The club is in debt" if bank < 0 else "Cash worth half a year's turnover or more" if tone == "gold" else "In credit"))
    return out


@router.get("/finance")
async def finance():
    c = await active_career()
    snap = await db.snapshots.find_one({"career_id": c["id"]}, {"_id": 0, "finance": 1, "game_date": 1}, sort=[("save_no", -1)]) or {}
    return {"items": assess(snap.get("finance") or {}), "game_date": snap.get("game_date")}
