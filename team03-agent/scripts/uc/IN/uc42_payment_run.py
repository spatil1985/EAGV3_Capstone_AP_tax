"""UC-42 — Payment-run prioritisation (India).

Spec: docs/usecases/IN/uc-42-payment-run-prioritisation.md.
Question: "We can't pay everything this week. Which bills should we pay first to avoid penalties and
lost credit, and which should we hold?"

Engine: scripts/uc/common/payment_run.py. India scorers (cost of one more week's delay):
  msme_45_day        past or within a week of the MSME deadline: 7 days of penal interest at 3 × bank
                     rate, plus the s.43B(h) flag (UC-04)
  rule_37_180_day    within 14 days of day 180: the bill's ITC would have to be reversed (UC-01)
  contractual_due    past or within a week of due date: nominal late rate (rulebook)
India holds: IMS-rejected (UC-24), plus the shared approval / duplicate holds. Cash-mode bills are
flagged to be paid by bank (UC-38).
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.msme import COVERED_TYPES, deadline, is_msme
from scripts.uc.common.payment_run import WEEK, contractual, plan, plan_context, plan_findings
from scripts.uc.common.tax import doc_tax


def msme_cost(bill, data, ctx):
    vendor = data.index("parties", "id").get(bill.get("vendor_id"))
    if not is_msme(vendor):
        return []
    due = deadline(bill, ctx)
    if not due or due > ctx.as_of + timedelta(days=WEEK):
        return []
    annual = Decimal(str(ctx.constant("msme_interest_multiple"))) * Decimal(str(ctx.rule("rbi_bank_rate_pct"))) / 100
    cost = (money(bill.get("balance_due")) * annual * WEEK / 365).quantize(CENTS)
    covered = (vendor.get("msme_type") or "").lower() in COVERED_TYPES
    return [("msme_45_day", cost, f"deadline {due}" + ("; s.43B(h) applies" if covered else ""))]


def rule37_cost(bill, data, ctx):
    start = day(bill.get("date"))
    window = int(ctx.constant("itc_payment_window_days"))
    if not start or bill.get("itc_eligibility") in (None, "ineligible"):
        return []
    crosses = start + timedelta(days=window + 1)
    if not (ctx.as_of <= crosses <= ctx.as_of + timedelta(days=14)):
        return []
    tax = doc_tax(bill)
    itc = tax["total"] if tax else money(bill.get("total_tax"))
    return [("rule_37_180_day", itc, f"crosses day {window} on {crosses}")] if itc > 0 else []


def cash_mode(bill, data, ctx):
    return [("pay_by_bank_not_cash", Decimal("0"), "")] if (bill.get("payment_gateway") or "").lower() == "cash" else []


def ims_rejected(bill, data, ctx):
    return "IMS-rejected invoice (UC-24)" if (bill.get("ims_status") or "").lower() in ("reject", "rejected") else None


class PaymentPlan(Rule):
    id = "payment_plan"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        rows, _ = plan(data, ctx, [msme_cost, rule37_cost, contractual, cash_mode], [ims_rejected])
        yield from plan_findings(rows, ctx)


class PaymentRunPrioritisation(Playbook):

    @property
    def rules(self):
        return [PaymentPlan()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"),
                       vendor_credits=fetcher.list("VendorCredit"))

    def context(self, data, findings, ctx):
        rows, quiet = plan(data, ctx, [msme_cost, rule37_cost, contractual, cash_mode], [ims_rejected])
        return plan_context(rows, quiet, data, ctx)

    def summary(self, outcome, ctx):
        c = outcome.context
        pay = [f for f in outcome.findings if f.rule == "pay_now"]
        avoided = sum((f.total_exposure for f in pay), Decimal("0"))
        top = pay[0].entity_ref if pay else None
        return (f"Pay {fmt(money(c['pay now']), ctx.currency)} across {len(pay)} bill(s) this week"
                + (f", starting with {top}" if top else "") + f": that avoids {fmt(avoided, ctx.currency)} of cost for "
                f"each week of delay. Hold {fmt(money(c['held']), ctx.currency)}; net off "
                f"{fmt(money(c['credit netted off']), ctx.currency)} of vendor credits first. "
                f"{c['no cost of delay this week (pay by due date)']} bill(s) can wait until their due date.")
