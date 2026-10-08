"""US-18 — Payment-run prioritisation (US).

Spec: docs/usecases/US/us-18-payment-run-prioritisation.md.
Question: "Which bills should we pay first this week, and which should we hold or withhold on?"

Engine: scripts/uc/common/payment_run.py. The US plan is driven by terms, discounts and withholding,
not statutory penalties (there is no private-sector prompt-payment statute and no input credit):
  contractual_due     past or within a week of due date (shared scorer)
  discount_lost       an early-payment discount (e.g. "2/10 net 30") whose window closes this week
  backup withholding  a 1099 vendor with no W-9: pay 76% and withhold 24% (IRC §3406, US-06)
Holds: approval pending/rejected, possible duplicate (US-07). Credits are netted off first (US-17).
"""

import re
from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.payment_run import WEEK, contractual, plan, plan_context, plan_findings

DISCOUNT = re.compile(r"(\d+(?:\.\d+)?)\s*/\s*(\d+)\s*,?\s*net\s*(\d+)", re.I)


def discount_cost(bill, data, ctx):
    m = DISCOUNT.search(str(bill.get("payment_terms") or ""))
    start = day(bill.get("date"))
    if not m or not start:
        return []
    pct, days = Decimal(m.group(1)), int(m.group(2))
    closes = start + timedelta(days=days)
    if not (ctx.as_of <= closes <= ctx.as_of + timedelta(days=WEEK)):
        return []
    return [("discount_lost", (money(bill.get("balance_due")) * pct / 100).quantize(CENTS), f"{pct}% if paid by {closes}")]


def backup_withholding(bill, data, ctx):
    vendor = data.index("parties", "id").get(bill.get("vendor_id")) or {}
    if vendor.get("is_1099_vendor") and (not vendor.get("w9_on_file") or vendor.get("backup_withholding")):
        rate = Decimal(str(ctx.constant("backup_withholding_rate_pct"))) / 100
        return (money(bill.get("balance_due")) * rate).quantize(CENTS), "backup withholding 24%, no W-9 (IRC 3406)"
    return None


class PaymentPlanUS(Rule):
    id = "payment_plan"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        rows, _ = plan(data, ctx, [contractual, discount_cost], [], withhold=backup_withholding)
        yield from plan_findings(rows, ctx)


class PaymentRunPrioritisationUS(Playbook):

    @property
    def rules(self):
        return [PaymentPlanUS()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"),
                       vendor_credits=fetcher.list("VendorCredit"))

    def context(self, data, findings, ctx):
        rows, quiet = plan(data, ctx, [contractual, discount_cost], [], withhold=backup_withholding)
        out = plan_context(rows, quiet, data, ctx)
        out["backup withholding"] = str(sum((r["withheld"] for r in rows), Decimal("0")))
        return out

    def summary(self, outcome, ctx):
        c = outcome.context
        pay = [f for f in outcome.findings if f.rule == "pay_now"]
        top = pay[0].entity_ref if pay else None
        return (f"Pay {fmt(money(c['pay now']), ctx.currency)} across {len(pay)} bill(s) this week"
                + (f", starting with {top}" if top else "") + f"; open {c['open bills']} bills, overdue {c['overdue']}. "
                f"Hold {fmt(money(c['held']), ctx.currency)}; withhold {fmt(money(c['backup withholding']), ctx.currency)} "
                f"(backup withholding). Many overdue bills may be disputed — there is no dispute flag, so confirm before "
                f"ranking them as urgent.")
