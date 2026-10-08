"""Payment-run prioritisation shared by UC-42 (India) and US-18 (US).

For every open bill: take out holds (each with a reason), net off the vendor's open credits, then score
the **cost of one more week's delay** with jurisdiction scorers, and rank. Bills with no hold and no
cost of delay are counted in the context, not emitted, so the plan lists what needs a decision.

A scorer is `score(bill, data, ctx) -> list[(reason, cost Decimal, note)]`; a hold check is
`hold(bill, data, ctx) -> str | None`.
"""

from datetime import timedelta
from decimal import Decimal

from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.duplicates import candidates, suspicious_pairs
from scripts.uc.common.vendor_balance import open_bills, open_credits

WEEK = 7


def due_date(bill, ctx):
    explicit = day(bill.get("due_date"))
    if explicit:
        return explicit
    start = day(bill.get("date"))
    return start + timedelta(days=int(ctx.constant("default_payment_terms_days"))) if start else None


def contractual(bill, data, ctx):
    due = due_date(bill, ctx)
    if not due or due > ctx.as_of + timedelta(days=WEEK):
        return []
    rate = Decimal(str(ctx.constant("late_payment_nominal_rate_pct"))) / 100
    cost = (money(bill.get("balance_due")) * rate * WEEK / 365).quantize(CENTS)
    return [("contractual_due", cost, f"due {due}")]


def common_holds(bill, data, ctx):
    status = (bill.get("approval_status") or "").lower()
    if status in ("pending_approval", "rejected"):
        return f"approval {status}"
    if bill["id"] in data.get("_duplicate_ids", set()):
        return "possible duplicate (UC-05)"
    return None


def plan(data, ctx, scorers, holds, withhold=None):
    """withhold(bill, data, ctx) -> (amount, reason) | None reduces the amount to pay (US backup withholding)."""
    pairs, _ = suspicious_pairs(candidates(data.get("bills", [])))
    data["_duplicate_ids"] = {max((a, b), key=lambda x: x.get("created_at") or "")["id"] for a, b, *_ in pairs}
    credit_left: dict = {}
    for vc in open_credits(data):
        credit_left[vc.get("vendor_id")] = credit_left.get(vc.get("vendor_id"), Decimal("0")) + money(vc.get("balance"))
    rows, quiet = [], []
    for bill in sorted(open_bills(data), key=lambda b: (due_date(b, ctx) or ctx.as_of, b.get("id"))):
        reason = None
        for hold in [common_holds, *holds]:
            reason = reason or hold(bill, data, ctx)
        balance = money(bill.get("balance_due"))
        net = min(credit_left.get(bill.get("vendor_id"), Decimal("0")), balance)
        if net:
            credit_left[bill["vendor_id"]] -= net
        reasons = [r for scorer in scorers for r in scorer(bill, data, ctx)]
        cost = sum((r[1] for r in reasons), Decimal("0"))
        if reason:
            action = "hold"
        elif net and net == balance:
            action = "net_off"
        elif cost > 0:
            action = "pay_now"
        else:
            quiet.append(bill)
            continue
        withheld, why = (withhold(bill, data, ctx) if withhold else None) or (Decimal("0"), None)
        to_pay = Decimal("0") if action in ("hold", "net_off") else balance - net - withheld
        rows.append({"bill": bill, "action": action, "hold_reason": reason, "net_off": net, "withheld": withheld,
                     "withholding_reason": why, "amount_to_pay": to_pay,
                     "cost": cost, "reasons": reasons, "due": due_date(bill, ctx)})
    rows.sort(key=lambda r: ({"pay_now": 0, "net_off": 1, "hold": 2}[r["action"]], -r["cost"], r["due"] or ctx.as_of))
    return rows, quiet


def plan_findings(rows, ctx):
    for rank, r in enumerate(rows, 1):
        bill = r["bill"]
        number = bill.get("number") or bill["id"]
        name = bill.get("_vendor_id_display")
        why = "; ".join(f"{reason} ({fmt(cost, ctx.currency)}{', ' + note if note else ''})"
                        for reason, cost, note in r["reasons"] if cost)
        text = {"pay_now": f"pay {fmt(r['amount_to_pay'], ctx.currency)} now — a week's delay costs "
                           f"{fmt(r['cost'], ctx.currency)}: {why}",
                "net_off": f"set {fmt(r['net_off'], ctx.currency)} of the vendor's open credit against it; nothing to pay",
                "hold": f"hold: {r['hold_reason']}"}[r["action"]]
        yield Finding(
            finding_type="payment_plan", rule=r["action"], severity={"pay_now": 70, "net_off": 50, "hold": 60}[r["action"]],
            entity_type="Bill", entity_id=bill["id"], entity_ref=number, total_exposure=r["cost"], currency=ctx.currency,
            counterparty_id=bill.get("vendor_id"), counterparty_name=name,
            summary=f"#{rank} {number} ({name}, {fmt(money(bill.get('balance_due')), ctx.currency)} due {r['due']}): "
                    + text + (f"; {fmt(r['net_off'], ctx.currency)} of credit applied first" if r["net_off"] and
                              r["action"] == "pay_now" else "")
                    + (f"; withhold {fmt(r['withheld'], ctx.currency)} ({r['withholding_reason']})" if r.get("withheld") else "")
                    + ".",
            details={"action": r["action"], "rank": rank, "withheld": str(r.get("withheld", Decimal("0"))), "pay_by_date": str(r["due"]) if r["due"] else None,
                     "amount_to_pay": str(r["amount_to_pay"]), "credit_applied": str(r["net_off"]),
                     "cost_of_delay_7d": str(r["cost"]), "reasons": [x[0] for x in r["reasons"] if x[1]],
                     "hold_reason": r["hold_reason"]})


def plan_context(rows, quiet, data, ctx) -> dict:
    bills = open_bills(data)
    overdue = [b for b in bills if (due_date(b, ctx) or ctx.as_of) < ctx.as_of]
    return {"open bills": len(bills), "open balance": str(sum((money(b.get("balance_due")) for b in bills), Decimal("0"))),
            "overdue": f"{len(overdue)} bills, {sum((money(b.get('balance_due')) for b in overdue), Decimal('0'))}",
            "pay now": str(sum((r["amount_to_pay"] for r in rows if r["action"] == "pay_now"), Decimal("0"))),
            "held": str(sum((money(r["bill"].get("balance_due")) for r in rows if r["action"] == "hold"), Decimal("0"))),
            "credit netted off": str(sum((r["net_off"] for r in rows), Decimal("0"))),
            "no cost of delay this week (pay by due date)": len(quiet)}
