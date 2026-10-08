"""UC-25 — Inward credit notes (vendor credits) and the input credit they reduce.

Spec: docs/usecases/IN/uc-25-vendor-credit-debit-notes-itc.md.
Question: "Our suppliers have given us credit notes. Have we reduced our input credit for them, and
are any of them wrong?"

Statute: s.34 CGST Act — a supplier's credit note reduces its output tax and, by the matching rule,
the recipient's input credit in the same period (s.16, Rule 36); it must reference the original
invoice. A supplier that can't charge GST (unregistered, composition, overseas) can't give GST back.

Rules (population: vendor credits not draft):
  itc_reduction_due        registered supplier (business_gst, sez, deemed_export), not RCM, tax > 0:
                           credit must be reduced in the note's month (feeds UC-23)
  rcm_liability_reduction  reverse-charge credit: reduces the RCM liability and matching credit
  credit_tax_impossible    tax > 0 from unregistered / composition / consumer / overseas suppliers
  credit_unlinked          no reference_number, or one that resolves to no bill
  misfiled_vendor_credit   an outward CreditNote linked to a payable invoice (a vendor credit in the
                           wrong entity — UC-19 §6)
  data_quality             taxes[] rows named after products (quarantined at fetch, N128 pattern)
Tax: the quarantined clean heads, else valid item lines, else the stored total_tax (labelled).
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.records import party_of, ref
from scripts.uc.common.tax import clean_heads

REGISTERED = {"business_gst", "sez", "deemed_export"}
CANT_CHARGE = {"unregistered_business", "business_composition", "consumer", "overseas"}


def vc_tax(vc) -> tuple[Decimal, str]:
    heads = clean_heads(vc)
    if heads and heads["total"] > 0:
        return heads["total"], "clean taxes[] heads or valid items"
    return money(vc.get("total_tax")), "stored total_tax (no clean head rows)"


def credits(data):
    return [v for v in data.get("vendor_credits", []) if (v.get("status") or "").lower() not in ("draft", "void")]


class VendorNotes(Rule):
    id = "itc_adjustment"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        bills = data.get("bills", [])
        refs = {str(b.get(k)).strip().upper() for b in bills for k in ("bill_number", "number", "reference_number")
                if b.get(k)}
        unlinked = []
        for vc in credits(data):
            tax, source = vc_tax(vc)
            treatment = (vc.get("gst_treatment") or "").lower()
            number = ref(vc, "number", "vendor_credit_number")
            vid, vname = party_of(vc, data)
            base = dict(entity_type="VendorCredit", entity_id=vc["id"], entity_ref=number, currency=ctx.currency,
                        counterparty_id=vid, counterparty_name=vname)
            period = str(vc.get("date") or "")[:7]
            if tax > 0 and vc.get("is_reverse_charge"):
                yield Finding(finding_type="itc_adjustment", rule="rcm_liability_reduction", severity=45,
                              total_exposure=tax, reversal_base_amount=tax, **base,
                              summary=f"{number} ({vname}) is a reverse-charge credit: it reduces the {period} RCM "
                                      f"liability and the matching credit by {fmt(tax, ctx.currency)}.",
                              details={"period": period, "tax_source": source})
            elif tax > 0 and treatment in REGISTERED:
                yield Finding(finding_type="itc_adjustment", rule="itc_reduction_due", severity=55,
                              total_exposure=tax, reversal_base_amount=tax, **base,
                              summary=f"{number} ({vname}, {treatment}) — {fmt(tax, ctx.currency)} of input credit "
                                      f"must be reduced in {period}.",
                              details={"period": period, "tax_source": source, "gst_treatment": treatment})
            elif tax > 0 and treatment in CANT_CHARGE:
                yield Finding(finding_type="itc_adjustment", rule="credit_tax_impossible", severity=50,
                              total_exposure=tax, **base,
                              summary=f"{number} ({vname}) carries {fmt(tax, ctx.currency)} GST, but a {treatment} "
                                      f"supplier can't charge GST, so it can't give any back. Check the document.",
                              details={"gst_treatment": treatment, "tax_source": source})
            reference = str(vc.get("reference_number") or "").strip().upper()
            if not reference or reference not in refs:
                unlinked.append(vc)
            if vc.get("_suspect_taxes"):
                bad = [r.get("tax_type") or r.get("tax_name") for r in vc["_suspect_taxes"]]
                yield Finding(finding_type=DATA_QUALITY, rule="stored_value_mismatch", status=DATA_QUALITY,
                              severity=10, **base,
                              summary=f"{number}: taxes[] rows named after products ({', '.join(map(str, bad[:3]))}) "
                                      f"were set aside; only real GST heads are used.",
                              details={"field": "taxes[].tax_type", "observed": bad, "pattern": "N127/N128 seeder"})
        if unlinked:
            blank = sum(1 for v in unlinked if not v.get("reference_number"))
            yield Finding(finding_type="itc_adjustment", rule="credit_unlinked", severity=30, entity_type="VendorCredits",
                          entity_id="unlinked", entity_ref=f"{len(unlinked)} vendor credits", currency=ctx.currency,
                          summary=f"{len(unlinked)} vendor credit(s) can't be tied to an original bill ({blank} have no "
                                  f"reference; the rest reference codes that match no bill). s.34 requires the link, or "
                                  f"they are unlinked discounts (s.15(3)(b)).",
                          details={"count": len(unlinked), "vendor_credits": [ref(v, "number") for v in unlinked][:50],
                                   "sample_references": [v.get("reference_number") for v in unlinked[:5]]})
        invoices = data.index("invoices", "id")
        for cn in data.get("credit_notes", []):
            original = invoices.get(cn.get("invoice_id")) or {}
            if original.get("direction") == "payable" and (cn.get("status") or "").lower() not in ("draft", "void"):
                yield Finding(finding_type="itc_adjustment", rule="misfiled_vendor_credit", severity=40,
                              entity_type="CreditNote", entity_id=cn["id"], entity_ref=cn.get("number"),
                              total_exposure=money(cn.get("total_tax")), currency=ctx.currency,
                              summary=f"{cn.get('number')} is an outward credit note linked to purchase invoice "
                                      f"{original.get('number')}: probably a vendor credit recorded in the wrong place.",
                              details={"original": original.get("number")})


class VendorNotesItc(Playbook):

    @property
    def rules(self):
        return [VendorNotes()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(vendor_credits=fetcher.list("VendorCredit"), bills=fetcher.list("Bill"),
                       credit_notes=fetcher.list("CreditNote"), invoices=fetcher.list("Invoice", direction="payable"))

    def context(self, data, findings, ctx):
        live = credits(data)
        return {"vendor credits (not draft)": len(live),
                "tax on them": str(sum((vc_tax(v)[0] for v in live), Decimal("0"))),
                "with reference_number": sum(1 for v in data["vendor_credits"] if v.get("reference_number")),
                "inward debit notes": "no entity on the platform (open question)"}

    def summary(self, outcome, ctx):
        def agg(rule):
            rows = [f for f in outcome.findings if f.rule == rule]
            return len(rows), sum((f.total_exposure for f in rows), Decimal("0"))
        n, due = agg("itc_reduction_due")
        r, rcm = agg("rcm_liability_reduction")
        i, imp = agg("credit_tax_impossible")
        u = next((f.details["count"] for f in outcome.findings if f.rule == "credit_unlinked"), 0)
        m, _ = agg("misfiled_vendor_credit")
        return (f"{fmt(due, ctx.currency)} of input credit must be reduced for {n} supplier credit note(s); "
                f"{r} reverse-charge credit(s) reduce RCM by {fmt(rcm, ctx.currency)}. {i} credit note(s) carry GST "
                f"({fmt(imp, ctx.currency)}) from suppliers who can't charge it. {u} are unlinked to a bill; {m} outward "
                f"credit note(s) look like misfiled vendor credits.")
