"""Unapplied vendor credits and advances, shared by UC-41 (India) and US-17 (US).

  credit_applicable_now  a vendor with open credits and open bills: apply min(credit, bills) before paying
  stale_credit           open credit older than 90 days with nothing to apply it against: ask for a refund
  advance_unadjusted     an advance / unused payment older than 90 days not set against a bill
Residues below one currency unit are rounding and only counted in the context.
"""

from decimal import Decimal

from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day

STALE_DAYS = 90
ROUNDING = Decimal("1.00")


def open_credits(data):
    return [v for v in data.get("vendor_credits", []) if (v.get("status") or "").lower() == "open"
            and money(v.get("balance")) >= ROUNDING]


def open_bills(data):
    return [b for b in data.get("bills", []) if (b.get("status") or "").lower() in ("open", "overdue", "partially_paid")
            and money(b.get("balance_due")) > 0]


def balance_findings(data, ctx):
    credits_by: dict = {}
    for vc in open_credits(data):
        credits_by.setdefault(vc.get("vendor_id"), []).append(vc)
    bills_by: dict = {}
    for b in open_bills(data):
        bills_by.setdefault(b.get("vendor_id"), []).append(b)
    for vendor, vcs in credits_by.items():
        credit = sum((money(v.get("balance")) for v in vcs), Decimal("0"))
        name = vcs[0].get("_vendor_id_display") or vendor
        oldest = max(((ctx.as_of - day(v["date"])).days for v in vcs if day(v.get("date"))), default=0)
        bills = bills_by.get(vendor, [])
        owed = sum((money(b.get("balance_due")) for b in bills), Decimal("0"))
        overdue = sum((money(b.get("balance_due")) for b in bills
                       if day(b.get("due_date")) and day(b["due_date"]) < ctx.as_of), Decimal("0"))
        refs = [v.get("number") or v.get("vendor_credit_number") for v in vcs]
        if bills:
            apply = min(credit, owed)
            yield Finding(
                finding_type="vendor_balance", rule="credit_applicable_now", severity=65, entity_type="Party",
                entity_id=vendor, entity_ref=name, total_exposure=apply, currency=ctx.currency,
                counterparty_id=vendor, counterparty_name=name,
                summary=f"{name} owes us {fmt(credit, ctx.currency)} in open credits ({', '.join(map(str, refs[:3]))}) while we "
                        f"owe it {fmt(owed, ctx.currency)}: apply {fmt(apply, ctx.currency)} before paying.",
                details={"vendor_id": vendor, "open_credit": str(credit), "open_bills": str(owed),
                         "overdue_bills": str(overdue), "applicable_amount": str(apply), "oldest_credit_days": oldest,
                         "credits": refs})
        elif oldest > STALE_DAYS:
            yield Finding(
                finding_type="vendor_balance", rule="stale_credit", severity=45, entity_type="Party", entity_id=vendor,
                entity_ref=name, total_exposure=credit, currency=ctx.currency, counterparty_id=vendor,
                counterparty_name=name,
                summary=f"{name} has held {fmt(credit, ctx.currency)} of our credit for up to {oldest} days and we owe it "
                        f"nothing to set it against: ask for a refund.",
                details={"vendor_id": vendor, "open_credit": str(credit), "oldest_credit_days": oldest, "credits": refs})
    for p in data.get("payments", []):
        unused = money(p.get("unused_amount"))
        if unused < ROUNDING and (p.get("payment_type") or "") != "advance":
            continue
        age = (ctx.as_of - day(p["date"])).days if day(p.get("date")) else 0
        if age > STALE_DAYS and unused >= ROUNDING:
            name = p.get("_vendor_id_display") or p.get("vendor_id")
            yield Finding(
                finding_type="vendor_balance", rule="advance_unadjusted", severity=50, entity_type="PaymentMade",
                entity_id=p["id"], entity_ref=p.get("number"), total_exposure=unused, currency=ctx.currency,
                counterparty_id=p.get("vendor_id"), counterparty_name=name,
                summary=f"{p.get('number')}: {fmt(unused, ctx.currency)} paid to {name} {age} days ago is still not set "
                        f"against a bill.", details={"age_days": age})


def balance_context(data) -> dict:
    credits = open_credits(data)
    with_bills = {b.get("vendor_id") for b in open_bills(data)}
    return {"open credits": len(credits),
            "open credit balance": str(sum((money(v.get("balance")) for v in credits), Decimal("0"))),
            "vendors with open credits": len({v.get("vendor_id") for v in credits}),
            "… of which we also owe": len({v.get("vendor_id") for v in credits} & with_bills),
            "unused payment residue (rounding)": str(sum((money(p.get("unused_amount")) for p in data.get("payments", [])
                                                          if 0 < money(p.get("unused_amount")) < ROUNDING), Decimal("0")))}
