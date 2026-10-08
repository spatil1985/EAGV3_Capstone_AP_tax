"""UC-43 — Bank-to-payables reconciliation (India).

Spec: docs/usecases/IN/uc-43-bank-to-payables-reconciliation.md.
Question: "Does every vendor payment in the bank match a payment in our books, and the other way round?"

Engine: scripts/uc/common/bank_recon.py — bank_debit_unrecorded, payment_not_in_bank,
match_without_voucher, unidentified_debit. The bank feed may be partial, so the summary states the
window and counts rather than a verdict on the business.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.money import fmt, money
from scripts.uc.common.bank_recon import recon_context, recon_findings


class BankRecon(Rule):
    id = "bank_reconciliation"
    severity = 65

    def evaluate(self, data: Dataset, ctx):
        yield from recon_findings(data, ctx)


class BankToPayables(Playbook):

    @property
    def rules(self):
        return [BankRecon()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bank_transactions=fetcher.list("BankTransaction"), payments=fetcher.list("PaymentMade"),
                       parties=fetcher.list("Party"), bills=fetcher.list("Bill"))

    def context(self, data, findings, ctx):
        return recon_context(data, ctx)

    def summary(self, outcome, ctx):
        unrec = [f for f in outcome.findings if f.rule == "bank_debit_unrecorded"]
        out = sum((f.total_exposure for f in unrec), Decimal("0"))
        missing = next((f for f in outcome.findings if f.rule == "payment_not_in_bank"), None)
        nv = next((f for f in outcome.findings if f.rule == "match_without_voucher"), None)
        c = outcome.context
        if not unrec and not missing:
            return f"Bank and payables reconcile over {c['bank window']}."
        parts = []
        if unrec:
            parts.append(f"{fmt(out, ctx.currency)} left the bank to {len(unrec)} vendor payee(s) with no payment in AP "
                         f"(those bills may be paid again)")
        if missing:
            parts.append(f"{fmt(missing.total_exposure, ctx.currency)} of AP payments ({missing.details['count']}) never "
                         f"appear in the bank")
        return (f"Over {c['bank window']}: " + ", and ".join(parts)
                + (f". {nv.details['count']} debit(s) are 'matched' to no voucher." if nv else "."))
