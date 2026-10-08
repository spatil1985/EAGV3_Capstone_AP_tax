"""MSME late-payment arithmetic shared by UC-04 (exposure) and UC-42 (payment-run priority).

MSMED Act s.15: pay a micro/small supplier within the agreed period, never more than 45 days
from acceptance (Bill.date is the acceptance proxy). s.16: compound interest at 3 × the RBI
bank rate, with monthly rests, from the day after the deadline.
"""

from datetime import date, timedelta
from decimal import Decimal

from scripts.money import CENTS, money
from scripts.uc.common.dates import day

COVERED_TYPES = {"micro", "small"}      # s.43B(h) and s.15 cover MSEs, not medium enterprises


def is_msme(party: dict | None) -> bool:
    return bool(party) and bool(party.get("is_msme"))


def deadline(bill: dict, ctx) -> date | None:
    start = day(bill.get("date"))
    if not start:
        return None
    cap = start + timedelta(days=int(ctx.constant("msme_payment_days")))
    agreed = day(bill.get("due_date"))
    return min(cap, agreed) if agreed else cap


def penal_interest(principal: Decimal, overdue_days: int, ctx, on: date | None = None) -> Decimal:
    """Compound monthly at multiple × bank rate; whole months elapsed (floor), spec UC-04 §5.7."""
    if overdue_days <= 0 or principal <= 0:
        return Decimal("0.00")
    annual = (Decimal(str(ctx.constant("msme_interest_multiple")))
              * Decimal(str(ctx.rule("rbi_bank_rate_pct", on))) / 100)
    months = overdue_days // 30
    return (money(principal) * ((1 + annual / 12) ** months - 1)).quantize(CENTS)
