"""UC-05 — Duplicate vendor payment (India).

Spec: docs/usecases/IN/uc-05-duplicate-vendor-payment.md.
Question: "Is any vendor being paid twice?"

Three tiers, highest wins (scripts/uc/common/duplicates.py):
  duplicate_exact        same vendor GSTIN/id + normalised supplier bill_number + FY
  duplicate_over_billed  bill_match: the PO was billed beyond the ordered quantity
  duplicate_suspicious_* same vendor, same positive grand_total, ≤ 3 days apart, not one
                         recurring template (N6 is reported separately); strong when the
                         line items are identical

Negative grand_total (N7) is excluded from tier 3. The summary always states tier-1
coverage (how many bills carry a supplier bill number), so a clean tier 1 is never read
as "no duplicates".
"""

from decimal import Decimal

from aptax.agentswitch.fetch import FetchError
from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.money import fmt, money
from scripts.uc.common.duplicates import (candidates, exact_pairs, match_result, over_billed_finding,
                                          paid_bill_ids, pair_finding, suspicious_pairs)


class DuplicateTiers(Rule):
    id = "duplicate_payment"
    severity = 90

    def evaluate(self, data: Dataset, ctx):
        bills = candidates(data.get("bills", []))
        paid = paid_bill_ids(data.get("payments", []))
        seen: set = set()
        for a, b, tier, note in exact_pairs(bills, data, ctx):
            seen.add(frozenset((a["id"], b["id"])))
            yield pair_finding(a, b, tier, note, data, ctx, paid)
        for bill in bills:
            f = over_billed_finding(bill, data.get("matches", {}).get(bill["id"]), data, ctx)
            if f:
                yield f
        pairs, _ = suspicious_pairs(bills)
        for a, b, tier, note in pairs:
            if frozenset((a["id"], b["id"])) not in seen:
                yield pair_finding(a, b, tier, note, data, ctx, paid)


class DuplicateVendorPayment(Playbook):
    match_tool = "endpoint.accounting.bill_match"

    @property
    def rules(self):
        return [DuplicateTiers()]

    def fetch(self, ctx, fetcher) -> Dataset:
        bills = fetcher.list("Bill")
        matches, failed = {}, 0
        for bill in candidates(bills):
            if bill.get("purchase_order_id"):
                try:
                    matches[bill["id"]] = match_result(fetcher.call(self.match_tool, {"bill_id": bill["id"]}))
                except FetchError:
                    failed += 1
        return Dataset(bills=bills, parties=fetcher.list("Party"), payments=fetcher.list("PaymentMade"),
                       matches=matches, match_failures=[None] * failed)

    @staticmethod
    def sort_key(f):
        return (-f.severity, -f.total_exposure)

    def context(self, data, findings, ctx):
        bills = candidates(data["bills"])
        _, suppressed = suspicious_pairs(bills)
        return {"bills checked (not void)": len(bills),
                "tier-1 coverage (supplier bill_number present)": f"{sum(1 for b in bills if b.get('bill_number'))}/{len(bills)}",
                "bills checked with bill_match": len(data["matches"]),
                "bill_match failures": len(data["match_failures"]),
                "recurring-template pairs suppressed": suppressed,
                "negative grand_total excluded from tier 3": sum(1 for b in bills if money(b.get("grand_total")) < 0)}

    def summary(self, outcome, ctx):
        tiers: dict = {}
        for f in outcome.findings:
            tiers[f.details["tier"]] = tiers.get(f.details["tier"], 0) + 1
        bills = outcome.context.get("tier-1 coverage (supplier bill_number present)", "?")
        held = sum((f.total_exposure for f in outcome.findings if f.details.get("action") != "recover"), Decimal("0"))
        if not outcome.findings:
            return f"No candidate duplicates. Tier-1 coverage: {bills} bills carry a supplier bill number."
        parts = ", ".join(f"{n} {t.replace('_', ' ')}" for t, n in sorted(tiers.items()))
        return (f"{len(outcome.findings)} candidate duplicate(s) ({parts}); {fmt(held, ctx.currency)} could still be "
                f"stopped before payment. Tier-1 coverage: {bills} bills carry a supplier bill number; "
                f"{outcome.context.get('recurring-template pairs suppressed', 0)} recurring pairs suppressed.")
