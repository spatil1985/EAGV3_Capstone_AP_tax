"""US-11 — Sales tax paid to vendors on purchases that should have been tax-free.

Spec: docs/usecases/US/us-11-sales-tax-on-exempt-purchases.md.
Question: "Have we paid sales tax to vendors on purchases that should have been tax-free, and can we still
get it back?"

Statute (Ohio shown): resale (R.C. 5739.01(E)), manufacturing direct use (R.C. 5739.02(B)(42)(g)),
nonprofit/government buyers (R.C. 5739.02(B)(12), (B)(1)); refund within 4 years (R.C. 5739.07).

Rules (lines classified by scripts/uc/common/us_purchase_tax.py — the mirror of US-02):
  tax_paid_on_exempt_purchase        a vendor-taxed bill line or expense in an exempt class; exposure = the tax
  exemption_certificate_not_issued   that vendor has no certificate from us on file (overrides) — the root cause
  refund_window_closing              purchase date + the state's window is within 180 days
Certificates we issue are not in the data model: config/overrides/exemption_certificates_issued.yaml.
"""

from datetime import timedelta
from decimal import Decimal

import yaml

from aptax.config import CONFIG_DIR
from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import add_months, day
from scripts.uc.common.us_purchase_tax import classify, line_amount

OVERRIDES = CONFIG_DIR / "overrides" / "exemption_certificates_issued.yaml"
EXEMPT = {"exempt_manufacturing", "exempt_resale"}
WARN_DAYS = 180


def issued() -> set:
    try:
        raw = yaml.safe_load(OVERRIDES.read_text(encoding="utf-8")) or {}
    except OSError:
        return set()
    return {c.get("vendor_id") for c in raw.get("certificates") or [] if c.get("vendor_id")}


def taxed_lines(data):
    for b in data.get("bills", []):
        tax = money(b.get("total_tax")) or sum((money(r.get("amount")) for r in b.get("taxes") or []), Decimal("0"))
        if tax <= 0 or (b.get("status") or "").lower() in ("draft", "void"):
            continue
        lines = b.get("items") or []
        base = sum((line_amount(l) for l in lines), Decimal("0")) or Decimal("1")
        for l in lines:
            yield "Bill", b, l, (tax * line_amount(l) / base).quantize(Decimal("0.01"))
    for e in data.get("expenses", []):
        if money(e.get("tax_amount")) > 0 and (e.get("status") or "").lower() not in ("draft", "void"):
            yield "Expense", e, {"description": f"{e.get('_account_id_display') or ''} {e.get('description') or ''}"}, \
                money(e.get("tax_amount"))


class ExemptPurchases(Rule):
    id = "purchase_taxability"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        certs = data.get("issued", set())
        years = int(ctx.constant("sales_tax_refund_window_years_oh"))
        uncovered: dict = {}
        for entity, doc, line, tax in taxed_lines(data):
            cls, note = classify(line)
            if cls not in EXEMPT:
                continue
            vendor = doc.get("vendor_id")
            name = doc.get("_vendor_id_display") or vendor
            d = day(doc.get("date"))
            closes = add_months(d, 12 * years) if d else None
            yield Finding(
                finding_type="purchase_taxability", rule="tax_paid_on_exempt_purchase", severity=self.severity,
                entity_type=entity, entity_id=doc["id"], entity_ref=doc.get("number"), total_exposure=tax,
                currency=ctx.currency, counterparty_id=vendor, counterparty_name=name,
                summary=f"{doc.get('number')} ({name}): {fmt(tax, ctx.currency)} sales tax paid on "
                        f"'{(line.get('description') or '').strip()[:60]}', which is {note}. Recoverable from the vendor "
                        f"or the state until {closes}.",
                details={"exemption_class": cls, "refund_window_closes": str(closes) if closes else None})
            if closes and closes <= ctx.as_of + timedelta(days=WARN_DAYS):
                yield Finding(finding_type="purchase_taxability", rule="refund_window_closing", severity=70,
                              entity_type=entity, entity_id=f"{doc['id']}:window", entity_ref=doc.get("number"),
                              total_exposure=tax, currency=ctx.currency,
                              summary=f"The refund window for {doc.get('number')} closes on {closes}.",
                              details={"refund_window_closes": str(closes)})
            if vendor not in certs:
                uncovered.setdefault(vendor, [name, Decimal("0")])
                uncovered[vendor][1] += tax
        for vendor, (name, total) in uncovered.items():
            yield Finding(finding_type="purchase_taxability", rule="exemption_certificate_not_issued", severity=50,
                          entity_type="Party", entity_id=vendor, entity_ref=name, total_exposure=total,
                          currency=ctx.currency, counterparty_id=vendor, counterparty_name=name,
                          summary=f"No exemption certificate from us is on file for {name}; issuing one prevents the "
                                  f"next overcharge ({fmt(total, ctx.currency)} so far).", details={})


class TaxOnExemptPurchases(Playbook):

    @property
    def rules(self):
        return [ExemptPurchases()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), expenses=fetcher.list("Expense"), issued=issued())

    def context(self, data, findings, ctx):
        return {"vendor-taxed purchase lines": sum(1 for _ in taxed_lines(data)),
                "certificates we issued (overrides)": len(data["issued"]),
                "opposite direction (untaxed but taxable)": "US-02"}

    def summary(self, outcome, ctx):
        paid = [f for f in outcome.findings if f.rule == "tax_paid_on_exempt_purchase"]
        if not paid:
            return (f"No vendor charged sales tax on an exempt purchase ({outcome.context['vendor-taxed purchase lines']} "
                    f"vendor-taxed line(s) in total). The opposite problem — untaxed purchases that are taxable — is US-02.")
        total = sum((f.total_exposure for f in paid), Decimal("0"))
        return f"{fmt(total, ctx.currency)} of sales tax was paid on {len(paid)} exempt purchase line(s); recover it."
