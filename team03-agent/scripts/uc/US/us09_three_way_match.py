"""US-09 — Three-way match (US instance of UC-11).

Spec: docs/usecases/US/us-09-three-way-match.md (algorithm as UC-11).
Question: "Were the goods we're being billed for actually received?"

Same classification as UC-11 (scripts/uc/common/three_way.py); the basis here is SOX §404 (paying for
goods not received is a cash loss — there is no input credit). N2 appears fixed on this tenant
(`recorded_status` now populated), so one rule is added as its regression guard:
  stored_value_mismatch  bill_match's recorded_status ≠ its live status
A null received_qty means no receipt basis (two-way match), never "0 received".
"""

from aptax.playbooks.base import Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.uc.IN.uc11_three_way_match import ThreeWay, ThreeWayMatch
from scripts.uc.common.three_way import po_bills


class RecordedStatus(Rule):
    id = "stored_value_mismatch"
    severity = 20

    def evaluate(self, data, ctx):
        for bill in po_bills(data.get("bills", [])):
            m = data.get("matches", {}).get(bill["id"]) or {}
            live = (m.get("live") or {}).get("status")
            recorded = m.get("recorded_status")
            if live and recorded != live:
                yield Finding(finding_type=DATA_QUALITY, rule=self.id, status=DATA_QUALITY, severity=self.severity,
                              entity_type="Bill", entity_id=bill["id"], entity_ref=bill.get("number"),
                              currency=ctx.currency,
                              summary=f"{bill.get('number')}: bill_match's recorded status is {recorded!r} but the live "
                                      f"match says {live!r} (the N2 defect, regression guard).",
                              details={"recorded_status": recorded, "live_status": live})


class ThreeWayMatchUS(ThreeWayMatch):

    @property
    def rules(self):
        return [ThreeWay(), RecordedStatus()]

    def summary(self, outcome, ctx):
        base = super().summary(outcome, ctx)
        stale = sum(1 for f in outcome.findings if f.rule == "stored_value_mismatch")
        return base + (f" {stale} bill(s) have a stale recorded match status." if stale
                       else " Recorded match status agrees with the live match on every bill (N2 looks fixed).")
