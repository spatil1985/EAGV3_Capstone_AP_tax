"""UC-41 — Unapplied vendor credits and advances (India).

Spec: docs/usecases/IN/uc-41-unapplied-vendor-credits.md.
Question: "Are we about to pay vendors in full while they owe us money from credit notes or advances?"

Rules (scripts/uc/common/vendor_balance.py): credit_applicable_now, stale_credit, advance_unadjusted.
The agent never applies a credit itself (VendorCredit.apply_to_bill exists but is a ledger write).
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.money import fmt, money
from scripts.uc.common.vendor_balance import balance_context, balance_findings


class VendorBalances(Rule):
    id = "vendor_balance"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        yield from balance_findings(data, ctx)


class UnappliedVendorCredits(Playbook):

    @property
    def rules(self):
        return [VendorBalances()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(vendor_credits=fetcher.list("VendorCredit"), bills=fetcher.list("Bill"),
                       payments=fetcher.list("PaymentMade"))

    def context(self, data, findings, ctx):
        return balance_context(data)

    def summary(self, outcome, ctx):
        now = [f for f in outcome.findings if f.rule == "credit_applicable_now"]
        apply = sum((f.total_exposure for f in now), Decimal("0"))
        top = max(now, key=lambda f: f.total_exposure, default=None)
        c = outcome.context
        idle = money(c["open credit balance"]) - sum((money(f.details["open_credit"]) for f in now), Decimal("0"))
        return ((f"Apply {fmt(apply, ctx.currency)} of open vendor credits before paying {len(now)} vendor(s)"
                 + (f" ({top.counterparty_name} {fmt(top.total_exposure, ctx.currency)})" if top else "") + ". "
                 if now else "No vendor we owe has an open credit. ")
                + f"Another {fmt(idle, ctx.currency)} of credits sits with vendors we don't currently owe.")
