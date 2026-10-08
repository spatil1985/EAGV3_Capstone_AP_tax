"""UC-22 — GST on advances received for services.

Spec: docs/usecases/IN/uc-22-advance-receipt-gst.md.
Question: "Have we paid GST on client advances we're still holding?"

Statute: s.13(2) CGST Act — for services, GST is due on the earlier of invoice or receipt of
payment, so an advance triggers tax on receipt (Rule 50 receipt voucher). Advances for goods
are exempt (Notification 66/2017-CT). SEZ under LUT: 0%, but the voucher is still required.

The platform's advance construct, RetainerInvoice, has no items and no tax fields (N426 T4.6),
so "was GST paid?" can only be computed, never verified:
  advance_gst_unverifiable  advance held (payment_made − amount_applied > 0); tax if services at
                            18%, tax-inclusive: held × 18 / 118
  advance_gst_zero_rated    the same for an SEZ customer: 0% under a valid LUT (UC-20 can't
                            confirm one), receipt voucher still required
On-account PaymentReceived (unused_amount > 0) are included the same way.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.records import party_of

SERVICE_RATE = Decimal("18")


def supply_type(customer_id, data) -> tuple[str, str]:
    """Dominant product_type on the customer's invoices, else 'services' (conservative)."""
    items = data.index("items", "id")
    counts = {"goods": 0, "services": 0}
    for inv in data.get("invoices", []):
        if inv.get("party_id") != customer_id:
            continue
        for line in inv.get("items") or []:
            kind = (items.get(line.get("item_id")) or {}).get("product_type")
            if kind in counts:
                counts[kind] += 1
    if counts["goods"] > counts["services"]:
        return "goods", "customer's invoices are mostly goods"
    if counts["services"]:
        return "services", "customer's invoices are mostly services"
    return "services", "supply_type_assumed (no invoice evidence)"


def held_advances(data):
    for ret in data.get("retainers", []):
        held = money(ret.get("payment_made")) - money(ret.get("amount_applied"))
        if held > 0:
            yield "RetainerInvoice", ret, ret.get("customer_id"), held
    for rec in data.get("receipts", []):
        if money(rec.get("unused_amount")) > 0:
            yield "PaymentReceived", rec, rec.get("customer_id"), money(rec.get("unused_amount"))


class AdvanceGst(Rule):
    id = "advance_gst"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        parties = data.index("parties", "id")
        for entity, doc, customer, held in held_advances(data):
            kind, basis = supply_type(customer, data)
            tax_if_services = (held * SERVICE_RATE / (100 + SERVICE_RATE)).quantize(CENTS)
            sez = ((parties.get(customer) or {}).get("gst_treatment") or "").lower() == "sez"
            pid, pname = party_of(doc, data)
            pname = pname or (parties.get(customer) or {}).get("name")
            rule = "advance_gst_zero_rated" if sez else "advance_gst_unverifiable"
            exposure = Decimal("0.00") if kind == "goods" else tax_if_services
            text = (f"{doc.get('number')} — {fmt(held, ctx.currency)} advance from {pname} received "
                    f"{doc.get('date')}, not yet adjusted. ")
            if sez:
                text += (f"SEZ customer: 0% under a valid LUT (unconfirmed — UC-20), but a receipt voucher is "
                         f"required; {fmt(tax_if_services, ctx.currency)} IGST if there is no LUT.")
            elif kind == "goods":
                text += "Looks like goods (no GST on goods advances, Notif. 66/2017); confirm."
            else:
                text += (f"If for services, {fmt(tax_if_services, ctx.currency)} GST was due in the month of "
                         f"receipt. The platform can't record GST on an advance, so this can't be verified.")
            yield Finding(
                finding_type="rcm_undeclared_liability", rule=rule, severity=self.severity if not sez else 45,
                entity_type=entity, entity_id=doc["id"], entity_ref=doc.get("number"), total_exposure=exposure,
                currency=ctx.currency, counterparty_id=customer, counterparty_name=pname, summary=text,
                details={"held_amount": str(held), "received_date": doc.get("date"), "supply_type": kind,
                         "supply_type_basis": basis, "assumed_rate": str(SERVICE_RATE),
                         "tax_if_services": str(tax_if_services), "tax_if_goods": "0.00", "sez_customer": sez})


class AdvanceReceiptGst(Playbook):

    @property
    def rules(self):
        return [AdvanceGst()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(retainers=fetcher.list("RetainerInvoice"), receipts=fetcher.list("PaymentReceived"),
                       parties=fetcher.list("Party"), invoices=fetcher.list("Invoice", direction="receivable"),
                       items=fetcher.list("Item"))

    def context(self, data, findings, ctx):
        statuses: dict = {}
        for r in data["retainers"]:
            statuses[r.get("status")] = statuses.get(r.get("status"), 0) + 1
        return {"retainers": statuses,
                "on-account receipts (unused_amount > 0)": sum(1 for r in data["receipts"]
                                                              if money(r.get("unused_amount")) > 0),
                "tax on advances": "RetainerInvoice has no tax fields (N426 T4.6): computed, never verified"}

    def summary(self, outcome, ctx):
        if not outcome.findings:
            return "No advance is being held unadjusted."
        held = sum((money(f.details["held_amount"]) for f in outcome.findings), Decimal("0"))
        likely = sum((f.total_exposure for f in outcome.findings), Decimal("0"))
        ceiling = sum((money(f.details["tax_if_services"]) for f in outcome.findings), Decimal("0"))
        goods = sum(1 for f in outcome.findings if f.details["supply_type"] == "goods")
        return (f"{len(outcome.findings)} advance(s) held unadjusted ({fmt(held, ctx.currency)}). GST exposure: "
                f"{fmt(likely, ctx.currency)} on the supply types the invoices suggest ({goods} look like goods, "
                f"which carry no GST on advances), up to {fmt(ceiling, ctx.currency)} if all are for services. "
                f"The platform records neither the supply type nor the tax on advances, so confirm both.")
