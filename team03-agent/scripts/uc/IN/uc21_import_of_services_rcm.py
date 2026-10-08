"""UC-21 — Import of services under reverse charge.

Spec: docs/usecases/IN/uc-21-import-of-services-rcm.md.
Question: "Which foreign supplier bills create a GST liability we have to pay ourselves?"

Statute: s.5(3) IGST Act with Notification 10/2017-IT(R) entry 1 — IGST on services imported
from a supplier outside India is paid by the recipient under reverse charge. Goods imports are
customs IGST at the border, not RCM.

Step 1 needs two agreeing "overseas" signals (Bill.gst_treatment, Party.gst_treatment, non-INR
currency, no Indian GSTIN) and no contrary one (a vendor registered as business_gst etc.), because
the bill-level tag is unreliable on this tenant (all 12 `overseas` bills are Indian vendors in INR —
spec §6) and GSTINs are blank on every vendor, so "no GSTIN" alone proves nothing.

Rules:
  rcm_import_of_services   genuine overseas service bill, is_reverse_charge off → liability =
                           line rate (or 18%) × taxable value, derived (UC-03 row shape)
  rcm_double_tax           genuine overseas service bill with RCM on, but carrying supplier GST
  classification_conflict  (data_quality) tagged overseas on one signal only
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.lines import line_value
from scripts.uc.common.rcm import is_service_bill
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tax import doc_tax


def signals(bill, party) -> list[str]:
    out = []
    if (bill.get("gst_treatment") or "").lower() == "overseas":
        out.append("bill tagged overseas")
    if ((party or {}).get("gst_treatment") or "").lower() == "overseas":
        out.append("vendor tagged overseas")
    if (bill.get("currency_code") or "INR").upper() != "INR":
        out.append(f"currency {bill.get('currency_code')}")
    if party is not None and not party.get("gst_no"):
        out.append("vendor has no Indian GSTIN")
    return out


def is_service(bill, items) -> bool:
    if is_service_bill(bill):
        return True
    lines = bill.get("items") or []
    return bool(lines) and all((items.get(l.get("item_id")) or {}).get("product_type") == "services"
                               or str(l.get("hsn_or_sac") or "").startswith("99") for l in lines)


class ImportOfServices(Rule):
    id = "rcm_import_of_services"
    severity = 80

    def evaluate(self, data: Dataset, ctx):
        parties, items = data.index("parties", "id"), data.index("items", "id")
        for bill in data.get("bills", []):
            if (bill.get("status") or "").lower() in NOT_POSTED:
                continue
            party = parties.get(bill.get("vendor_id"))
            found = signals(bill, party)
            tagged = (bill.get("gst_treatment") or "").lower() == "overseas"
            if not found or (len(found) == 1 and not tagged):
                continue
            number = ref(bill, "number", "bill_number")
            vid, vname = party_of(bill, data)
            vendor_says = ((party or {}).get("gst_treatment") or "").lower()
            contradicted = vendor_says not in ("", "overseas")   # e.g. business_gst: an Indian registrant
            if len(found) < 2 or contradicted:
                yield Finding(
                    finding_type=DATA_QUALITY, rule="classification_conflict", entity_type="Bill",
                    entity_id=bill["id"], entity_ref=number, status=DATA_QUALITY, severity=15,
                    currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                    summary=f"{number} is tagged overseas, but nothing else agrees (vendor "
                            f"{(party or {}).get('gst_treatment') or 'untagged'}, {bill.get('currency_code') or 'INR'}); "
                            f"no import-of-services liability is assumed. Fix the tag.",
                    details={"signals": found, "contradicted_by": f"vendor gst_treatment {vendor_says}" if contradicted else None,
                             "is_reverse_charge": bill.get("is_reverse_charge"),
                             "service": is_service(bill, items)})
                continue
            if not is_service(bill, items):
                continue      # imported goods: customs IGST, not RCM
            tax = doc_tax(bill)
            charged = tax["total"] if tax else money(bill.get("total_tax"))
            if bill.get("is_reverse_charge"):
                if charged > 0:
                    yield Finding(
                        finding_type="rcm_undeclared_liability", rule="rcm_double_tax", severity=60,
                        entity_type="Bill", entity_id=bill["id"], entity_ref=number, total_exposure=charged,
                        currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                        summary=f"{number} ({vname}) is an import of services under reverse charge, yet carries "
                                f"{fmt(charged, ctx.currency)} supplier GST; a foreign supplier can't charge Indian GST.",
                        details={"signals": found})
                continue
            liability = Decimal("0")
            for line in bill.get("items") or []:
                rate = money(line.get("tax_percentage")) or Decimal(str(ctx.constant("rcm_rate_services_pct")))
                liability += line_value(line) * rate / 100
            liability = liability.quantize(CENTS)
            yield Finding(
                finding_type="rcm_undeclared_liability", rule=self.id, severity=self.severity, entity_type="Bill",
                entity_id=bill["id"], entity_ref=number, total_exposure=liability, currency=ctx.currency,
                counterparty_id=vid, counterparty_name=vname,
                summary=f"{number} ({vname}) is an import of services ({', '.join(found)}) with reverse charge not "
                        f"declared: ~{fmt(liability, ctx.currency)} IGST to self-assess (derived).",
                details={"signals": found, "rcm_expected": True, "is_reverse_charge_actual": False,
                         "derivation_method": "line rate, else 18%, on taxable value",
                         "notification": "10/2017-IT(R) entry 1"})


class ImportOfServicesRcm(Playbook):

    @property
    def rules(self):
        return [ImportOfServices()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"), items=fetcher.list("Item"))

    def context(self, data, findings, ctx):
        tagged = [b for b in data["bills"] if (b.get("gst_treatment") or "").lower() == "overseas"]
        return {"bills tagged overseas": len(tagged),
                "vendors tagged overseas": sum(1 for p in data["parties"]
                                               if (p.get("gst_treatment") or "").lower() == "overseas"),
                "rule": "two agreeing overseas signals required (spec §5 step 1)"}

    def summary(self, outcome, ctx):
        rcm = [f for f in outcome.findings if f.rule == "rcm_import_of_services"]
        rejected = sum(1 for f in outcome.findings if f.rule == "classification_conflict")
        total = sum((f.total_exposure for f in rcm), Decimal("0"))
        return ((f"{len(rcm)} import-of-services bill(s) owe ~{fmt(total, ctx.currency)} IGST under reverse charge."
                 if rcm else "No genuine import of services found.")
                + f" {rejected} bill(s) tagged overseas were rejected: only the tag says so "
                  f"(of {outcome.context['bills tagged overseas']} tagged).")
