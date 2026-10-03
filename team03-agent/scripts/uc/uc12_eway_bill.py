"""UC-12 — E-way bill coverage and expiry audit.

Spec: docs/usecases/IN/uc-12-eway-bill-coverage.md.
Question: "Is anything moving on the road right now without valid documentation?"

Statute: s.68 CGST Act + Rule 138 CGST Rules — an e-way bill is required before moving
goods worth more than the Rule 138 threshold; validity is 1 day per 200 km (20 km for
over-dimensional cargo). Goods moving without a valid EWB are liable to detention
under s.129. Penalty rate is deliberately NOT computed here (spec §2 flags it for
confirmation), so exposure is the consignment value at risk of detention.

Five rules (Strategy), in the severity order the spec's §7 asks for:

  Part B — coverage       ewb_missing             outward goods > threshold, not draft, no EWB
  Part A — validity       ewb_not_real            "active"/"generated" but no EWB number
                          ewb_part_b_missing      "active" with no vehicle (Part-B)
                          ewb_expired_in_transit  "active"/"generated" past expiry_date
                          ewb_validity_wrong      expiry ≠ generation + ceil(km / 200)

Everything below `fetch()` is pure: hand-written tests can build a Dataset from a few
dicts and call `EWayBillAudit().evaluate(dataset, ctx)`.
"""

import math
from datetime import date

from harness.core.playbook import Dataset, Playbook, PlaybookOutcome, RecordRule, Rule
from scripts.findings import Finding
from scripts.money import fmt, money

LIVE_STATUSES = {"active", "generated"}
NOT_MOVED = {"draft", "void", "cancelled"}
FINDING_TYPE = "eway_bill"


def _day(value) -> date | None:
    return date.fromisoformat(str(value)[:10]) if value else None


def _is_goods_line(line: dict) -> bool:
    """SAC codes start 99 (services). An empty HSN cannot be proven a service, so it
    counts as goods — the conservative reading for a detention risk."""
    return not str(line.get("hsn_or_sac") or "").startswith("99")


def _linked_document(ewb: dict, data: Dataset) -> dict | None:
    txn = ewb.get("transaction_id")
    return data.index("invoices", "id").get(txn) or data.index("challans", "id").get(txn)


def _counterparty(doc: dict | None) -> tuple[str | None, str | None]:
    if not doc:
        return None, None
    return (doc.get("party_id") or doc.get("customer_id"),
            doc.get("_party_id_display") or doc.get("_customer_id_display"))


class _EwbRule(RecordRule):
    """Shared finding builder for the four Part-A rules over the `ewb` record set."""

    source = "ewb"

    def describe(self, ewb: dict, ctx) -> str:
        raise NotImplementedError

    def extra(self, ewb: dict, ctx) -> dict:
        return {}

    def finding(self, ewb, data, ctx):
        doc = _linked_document(ewb, data)
        cp_id, cp_name = _counterparty(doc)
        doc_ref = ewb.get("_transaction_id_display") or ewb.get("transaction_id")
        return Finding(
            finding_type=FINDING_TYPE, rule=self.id, severity=self.severity,
            entity_type="EWayBill", entity_id=ewb["id"], entity_ref=ewb.get("number"),
            total_exposure=money(ewb.get("total")), currency=ctx.currency,
            counterparty_id=cp_id, counterparty_name=cp_name,
            summary=f"{ewb.get('number')} for {ewb.get('transaction_type')} {doc_ref}: "
                    f"{self.describe(ewb, ctx)}",
            details={"status": ewb.get("status"), "eway_bill_number": ewb.get("eway_bill_number"),
                     "transaction_type": ewb.get("transaction_type"),
                     "transaction_id": ewb.get("transaction_id"), "document_ref": doc_ref,
                     "direction": "inward" if ewb.get("transaction_type") == "bill" else "outward",
                     "generation_date": ewb.get("generation_date"),
                     "expiry_date": ewb.get("expiry_date"), "distance_km": ewb.get("distance_km"),
                     **self.extra(ewb, ctx)},
        )


class EwbNotReal(_EwbRule):
    id = "ewb_not_real"
    severity = 80
    platform_contradiction = True   # status claims issuance the data doesn't show

    def applies(self, ewb, data, ctx):
        return ewb.get("status") in LIVE_STATUSES and not ewb.get("eway_bill_number")

    def describe(self, ewb, ctx):
        return (f"marked '{ewb.get('status')}' but has no EWB number, so it was never issued "
                f"and is not valid documentation ({fmt(money(ewb.get('total')), ctx.currency)})")


class EwbPartBMissing(_EwbRule):
    id = "ewb_part_b_missing"
    severity = 60

    def applies(self, ewb, data, ctx):
        return ewb.get("status") == "active" and not ewb.get("vehicle_number")

    def describe(self, ewb, ctx):
        return "active with no vehicle number (Part-B), not valid for movement"


class EwbExpiredInTransit(_EwbRule):
    id = "ewb_expired_in_transit"
    severity = 70
    platform_contradiction = True   # platform never moves status to expired

    def applies(self, ewb, data, ctx):
        expiry = _day(ewb.get("expiry_date"))
        return ewb.get("status") in LIVE_STATUSES and expiry is not None and expiry < ctx.as_of

    def extra(self, ewb, ctx):
        return {"days_past_expiry": (ctx.as_of - _day(ewb["expiry_date"])).days}

    def describe(self, ewb, ctx):
        return (f"still '{ewb.get('status')}' {self.extra(ewb, ctx)['days_past_expiry']} days "
                f"after it expired on {str(ewb.get('expiry_date'))[:10]}")


class EwbValidityWrong(_EwbRule):
    id = "ewb_validity_wrong"
    severity = 40
    platform_contradiction = True

    @staticmethod
    def expected_days(ewb, ctx) -> int:
        per_day = ctx.constant("eway_bill_km_per_day_odc" if ewb.get("is_over_dimensional")
                               else "eway_bill_km_per_day")
        return max(1, math.ceil(float(ewb["distance_km"]) / per_day))

    def applies(self, ewb, data, ctx):
        gen, exp = _day(ewb.get("generation_date")), _day(ewb.get("expiry_date"))
        if not (gen and exp and ewb.get("distance_km")):
            return False
        return (exp - gen).days != self.expected_days(ewb, ctx)

    def extra(self, ewb, ctx):
        gen, exp = _day(ewb["generation_date"]), _day(ewb["expiry_date"])
        return {"expected_days": self.expected_days(ewb, ctx), "actual_days": (exp - gen).days}

    def describe(self, ewb, ctx):
        x = self.extra(ewb, ctx)
        return (f"validity is {x['actual_days']} day(s) for {ewb.get('distance_km')} km; "
                f"Rule 138(10) gives {x['expected_days']}")


class EwbMissing(Rule):
    """Part B: outward goods documents above the threshold with no e-way bill at all."""

    id = "ewb_missing"
    severity = 90

    @staticmethod
    def candidates(data: Dataset, ctx):
        """(entity_type, doc, value) for outward goods movements above the threshold."""
        threshold = money(ctx.constant("eway_bill_threshold_inr"))
        for inv in data.get("invoices", []):
            value = money(inv.get("grand_total"))
            if value > threshold and any(_is_goods_line(l) for l in inv.get("items") or []):
                yield "Invoice", inv, value
        for dc in data.get("challans", []):   # a delivery challan moves goods by definition
            value = money(dc.get("grand_total"))
            if value > threshold:
                yield "DeliveryChallan", dc, value

    def evaluate(self, data, ctx):
        covered = {e.get("transaction_id") for e in data.get("ewb", [])}
        for entity_type, doc, value in self.candidates(data, ctx):
            if doc.get("status") in NOT_MOVED or doc["id"] in covered:
                continue
            cp_id, cp_name = _counterparty(doc)
            doc_day = _day(doc.get("date"))
            age = (ctx.as_of - doc_day).days if doc_day else None
            yield Finding(
                finding_type=FINDING_TYPE, rule=self.id, severity=self.severity,
                entity_type=entity_type, entity_id=doc["id"], entity_ref=doc.get("number"),
                total_exposure=value, currency=ctx.currency,
                counterparty_id=cp_id, counterparty_name=cp_name,
                summary=f"{doc.get('number')} dated {doc.get('date')} ({doc.get('status')}, "
                        f"{fmt(value, ctx.currency)}) shows goods above the e-way bill "
                        f"threshold moved with no e-way bill linked",
                details={"status": doc.get("status"), "date": doc.get("date"),
                         "days_since_document": age},
            )


class EWayBillAudit(Playbook):
    """Template Method hooks for UC-12. The run skeleton is inherited unchanged."""

    @property
    def rules(self):
        return [EwbMissing(), EwbNotReal(), EwbExpiredInTransit(), EwbPartBMissing(),
                EwbValidityWrong()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(
            ewb=fetcher.list("EWayBill"),
            invoices=fetcher.list("Invoice", direction="receivable"),
            challans=fetcher.list("DeliveryChallan"),
        )

    def context(self, data, findings, ctx):
        ewb = data["ewb"]
        awaiting = [doc for _, doc, _ in EwbMissing.candidates(data, ctx)
                    if doc.get("status") in NOT_MOVED]
        statuses = sorted({e.get("status") for e in ewb})
        return {
            "e-way bills": len(ewb),
            **{f"… status {s}": sum(1 for e in ewb if e.get("status") == s) for s in statuses},
            "… inward (transaction_type bill)": sum(1 for e in ewb if e.get("transaction_type") == "bill"),
            "outward docs above threshold": sum(1 for _ in EwbMissing.candidates(data, ctx)),
            "drafts that will need an EWB before despatch": len(awaiting),
        }

    def summary(self, outcome: PlaybookOutcome, ctx) -> str:
        if not outcome.findings:
            return "No e-way bill gaps: every outward goods movement above the threshold is covered and valid."
        per_entity = {(f.entity_type, f.entity_id): f.total_exposure for f in outcome.findings}
        missing = sum(1 for f in outcome.findings if f.rule == "ewb_missing")
        invalid = len({f.entity_id for f in outcome.findings if f.entity_type == "EWayBill"})
        return (f"{missing} goods movement(s) above the threshold have no e-way bill, and "
                f"{invalid} e-way bill(s) are not valid documentation; "
                f"{fmt(sum(per_entity.values()), ctx.currency)} of consignments affected "
                f"(each document counted once).")
