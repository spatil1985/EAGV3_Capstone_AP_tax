"""UC-03 — Reverse charge (RCM) self-invoicing on notified domestic services.

Spec: docs/usecases/IN/uc-03-rcm-self-invoicing.md.
Question: "Which supplier bills make us liable to pay the tax ourselves, and have we?"

Statute: s.9(3) CGST Act with Notification 13/2017-CT(R) — GTA, legal, sponsorship and
director services are taxed in the recipient's hands; the recipient self-invoices (s.31(3)(f))
and pays the tax in cash.

Rules:
  rcm_undeclared_liability  a notified service bill with is_reverse_charge off and no GST
                            charged by the supplier → liability = rate × taxable value
                            (derived, labelled as such). A GTA that charged GST itself has
                            opted for forward charge (spec §11 correction) → not a finding.
  rcm_flag_spurious         is_reverse_charge on, but the bill is no notified service and not
                            an import of services (UC-21's case) — 8 live cases in §11.
  rcm_unregistered_review   a bill from an unregistered supplier: s.9(4) applies only to
                            notified classes, so this is a review candidate (spec §5a).
  data_quality              a notified-service bill whose tax can't be sourced.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt
from scripts.uc.common.rcm import derived_liability, is_service_bill, notified_type, taxable_base, treatment
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tax import doc_tax, untrusted_tax


def _posted(bill):
    return (bill.get("status") or "").lower() not in NOT_POSTED


def _party(bill, data):
    return data.index("parties", "id").get(bill.get("vendor_id"))


def _row(rule, bill, data, ctx, *, severity, amount, summary, **details):
    vid, vname = party_of(bill, data)
    return Finding(finding_type="rcm_undeclared_liability" if rule == "rcm_undeclared_liability" else "rcm_review",
                   rule=rule, severity=severity, entity_type="Bill", entity_id=bill["id"],
                   entity_ref=ref(bill, "bill_number", "number"), total_exposure=amount, currency=ctx.currency,
                   counterparty_id=vid, counterparty_name=vname, summary=summary, details=details)


class UndeclaredRcm(Rule):
    id = "rcm_undeclared_liability"
    severity = 80

    def evaluate(self, data: Dataset, ctx):
        for bill in data.get("bills", []):
            if not _posted(bill) or bill.get("is_reverse_charge"):
                continue
            party = _party(bill, data)
            kind = notified_type(bill, party)
            if not kind:
                continue
            supplier_type, basis, rate_name, notif = kind
            tax = doc_tax(bill)
            if tax is None:
                yield untrusted_tax(bill, "Bill", blocks="UC-03 recorded tax", currency=ctx.currency)
                continue
            if tax["total"] > 0:
                continue      # supplier charged GST itself: forward charge (GTA option), no RCM due
            rate = ctx.constant(rate_name)
            liability = derived_liability(bill, rate)
            number = ref(bill, "bill_number", "number")
            _, vname = party_of(bill, data)
            yield _row(self.id, bill, data, ctx, severity=self.severity, amount=liability,
                       summary=f"{number} ({vname}, {supplier_type.upper()}) — reverse charge expected but "
                               f"not flagged and no GST charged; ~{fmt(liability, ctx.currency)} undeclared "
                               f"({rate}% on {fmt(taxable_base(bill), ctx.currency)}, derived, not on the bill).",
                       vendor_gst_treatment=treatment(bill, party), supplier_type_inferred=supplier_type,
                       supplier_type_basis=basis, notification=notif, rcm_expected=True,
                       is_reverse_charge_actual=False, recorded_tax_amount="0.00",
                       derivation_method=f"playbook_rate_{rate}pct_on_taxable_value",
                       caveat="GTA status (consignment note) and any forward-charge option are not in the data")


class SpuriousRcmFlag(Rule):
    id = "rcm_flag_spurious"
    severity = 40

    def evaluate(self, data, ctx):
        for bill in data.get("bills", []):
            if not _posted(bill) or not bill.get("is_reverse_charge"):
                continue
            party = _party(bill, data)
            if notified_type(bill, party):
                continue
            if treatment(bill, party) == "overseas" and is_service_bill(bill):
                continue      # import of services: RCM is right, and UC-21 audits it
            codes = sorted({str(l.get("hsn_or_sac") or "blank") for l in bill.get("items") or []})
            number = ref(bill, "bill_number", "number")
            tax = doc_tax(bill)
            yield _row(self.id, bill, data, ctx, severity=self.severity,
                       amount=tax["total"] if tax else Decimal("0"),
                       summary=f"{number} is flagged reverse charge, but its lines ({', '.join(codes)}) are "
                               f"no notified RCM service and not an import of services "
                               f"(treatment {treatment(bill, party) or 'blank'}). Check the classification.",
                       hsn_codes=codes, vendor_gst_treatment=treatment(bill, party))


class UnregisteredReview(Rule):
    id = "rcm_unregistered_review"
    severity = 20

    def evaluate(self, data, ctx):
        for bill in data.get("bills", []):
            party = _party(bill, data)
            if (not _posted(bill) or bill.get("is_reverse_charge") or notified_type(bill, party)
                    or treatment(bill, party) != "unregistered_business"):
                continue
            number = ref(bill, "bill_number", "number")
            yield _row(self.id, bill, data, ctx, severity=self.severity, amount=Decimal("0"),
                       summary=f"{number} is from an unregistered supplier. s.9(4) reverse charge applies "
                               f"only to notified classes; confirm this purchase is not one of them.",
                       vendor_gst_treatment="unregistered_business")


class RcmSelfInvoicing(Playbook):

    @property
    def rules(self):
        return [UndeclaredRcm(), SpuriousRcmFlag(), UnregisteredReview()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"))

    def context(self, data, findings, ctx):
        posted = [b for b in data["bills"] if _posted(b)]
        notified = [b for b in posted if notified_type(b, _party(b, data))]
        forward = [b for b in notified if (doc_tax(b) or {}).get("total", 0) > 0 and not b.get("is_reverse_charge")]
        return {"posted bills": len(posted), "notified-service bills": len(notified),
                "flagged reverse charge": sum(1 for b in posted if b.get("is_reverse_charge")),
                "GTA/notified bills where the supplier charged GST (forward charge)": len(forward)}

    def summary(self, outcome, ctx):
        und = [f for f in outcome.findings if f.rule == "rcm_undeclared_liability"]
        spur = sum(1 for f in outcome.findings if f.rule == "rcm_flag_spurious")
        unreg = sum(1 for f in outcome.findings if f.rule == "rcm_unregistered_review")
        total = sum((f.total_exposure for f in und), Decimal("0"))
        head = (f"{len(und)} bill(s) carry an undeclared reverse-charge liability, ~{fmt(total, ctx.currency)} "
                f"(derived at notified rates)." if und else "No undeclared reverse-charge liability on notified services.")
        return (head + (f" {spur} bill(s) are flagged reverse charge where it can't apply." if spur else "")
                + (f" {unreg} bill(s) from unregistered suppliers need a s.9(4) check." if unreg else ""))
