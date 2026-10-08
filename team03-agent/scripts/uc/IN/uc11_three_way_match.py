"""UC-11 — Three-way match (India).

Spec: docs/usecases/IN/uc-11-three-way-match.md.
Question: "Were the goods we're being billed for actually received?"

Statute: s.16(2)(b) CGST Act — no ITC until the goods are received. Paying for goods never
received is also the classic AP loss.

Rules (scripts/uc/common/three_way.py, engine = endpoint.accounting.bill_match):
  billed_not_received  receipt_problem, or a line billed with 0 received → hold payment and ITC
  over_billed          billed-to-date beyond the ordered quantity (also UC-05 tier 2)
  price_variance       bill rate off the PO rate beyond tolerance
Cross-check: a billed_not_received bill from an MSME vendor carries `uc04_msme_vendor`, so the
UC-04 "pay before day 45" advice is not applied to goods that never arrived.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.money import fmt
from scripts.uc.common.msme import is_msme
from scripts.uc.common.three_way import fetch_matches, finding, po_bills


class ThreeWay(Rule):
    id = "three_way_match"
    severity = 80

    def evaluate(self, data: Dataset, ctx):
        parties = data.index("parties", "id")
        for bill in po_bills(data.get("bills", [])):
            match = data.get("matches", {}).get(bill["id"])
            if not match:
                continue
            flags = ["uc04_msme_vendor"] if is_msme(parties.get(bill.get("vendor_id"))) else []
            f = finding(bill, match, data, ctx, cross_flags=flags)
            if f:
                yield f


class ThreeWayMatch(Playbook):

    @property
    def rules(self):
        return [ThreeWay()]

    def fetch(self, ctx, fetcher) -> Dataset:
        bills = fetcher.list("Bill")
        matches, failed = fetch_matches(fetcher, bills)
        return Dataset(bills=bills, parties=fetcher.list("Party"), matches=matches, match_failures=[None] * failed)

    def context(self, data, findings, ctx):
        statuses: dict = {}
        for m in data["matches"].values():
            s = (m.get("live") or {}).get("status")
            statuses[s] = statuses.get(s, 0) + 1
        return {"bills with a PO": len(po_bills(data["bills"])), "bill_match calls": len(data["matches"]),
                "bill_match failures": len(data["match_failures"]), "live.status": statuses,
                "stored match_status": "quarantined (N2); not read"}

    def summary(self, outcome, ctx):
        nr = [f for f in outcome.findings if f.rule == "billed_not_received"]
        amount = sum((f.total_exposure for f in nr), Decimal("0"))
        msme = sum(1 for f in nr if f.details["cross_flags"])
        other = len(outcome.findings) - len(nr)
        if not outcome.findings:
            return f"All {outcome.context['bill_match calls']} PO-linked bills match within tolerance."
        return (f"{len(nr)} bill(s) billed against POs with nothing received ({fmt(amount, ctx.currency)} open"
                + (f", {msme} from MSME vendors" if msme else "") + f"); {other} other mismatch(es).")
