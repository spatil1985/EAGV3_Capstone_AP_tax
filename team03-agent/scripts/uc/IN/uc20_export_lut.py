"""UC-20 — Zero-rated supplies (export, SEZ) and LUT cover.

Spec: docs/usecases/IN/uc-20-export-lut-tracking.md.
Question: "Are our export invoices genuinely zero-rated, and is our LUT still valid?"

Statute: s.16 IGST Act (zero-rated: export, supply to SEZ; under LUT without IGST, or with IGST
and refund); Rule 96A (LUT per financial year); s.2(6) IGST Act (five conditions for export of
services); s.7(5)(b) (SEZ supplies are inter-state: never CGST/SGST).

Rules:
  sez_intra_state_tax_charged  SEZ invoice carrying CGST/SGST
  export_condition_failed      `overseas` invoice failing s.2(6): place of supply in India, or INR
  deemed_export_untaxed        deemed export with no tax (it is not zero-rated)
  lut_missing                  FY aggregate: zero-tax zero-rated invoices and no LUT record at all
  lut_validity_unknown         FY aggregate: an LUT record exists, but has no dates, FY or ARN
                               (N426 T4.4, GAP-5), so cover can't be confirmed
SEZ invoices in INR are correct and never flagged by the overseas currency test.
"""

import re
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day, fy_label
from scripts.uc.common.records import NOT_POSTED, party_of
from scripts.uc.common.tax import doc_tax

ZERO_RATED = {"sez", "overseas", "deemed_export"}
LUT = re.compile(r"\bLUT\b|letter of undertaking", re.I)
INDIAN_STATE_CODE = re.compile(r"^\d{2}$")


def zero_rated(data):
    for inv in data.get("invoices", []):
        t = (inv.get("gst_treatment") or "").lower()
        if (inv.get("direction", "receivable") == "receivable" and t in ZERO_RATED
                and (inv.get("status") or "").lower() not in NOT_POSTED):
            yield inv, t


def _row(rule, inv, data, ctx, severity, summary, **details):
    pid, pname = party_of(inv, data)
    return Finding(finding_type="zero_rated_supply", rule=rule, severity=severity, entity_type="Invoice",
                   entity_id=inv["id"], entity_ref=inv.get("number"), total_exposure=money(inv.get("grand_total")),
                   currency=ctx.currency, counterparty_id=pid, counterparty_name=pname, summary=summary,
                   details=details)


class ZeroRatingConditions(Rule):
    id = "zero_rated_supply"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        for inv, treatment in zero_rated(data):
            tax = doc_tax(inv) or {"cgst": Decimal("0"), "sgst": Decimal("0"), "igst": Decimal("0"),
                                   "total": money(inv.get("total_tax"))}
            number = inv.get("number")
            if treatment == "sez" and (tax["cgst"] > 0 or tax["sgst"] > 0):
                yield _row("sez_intra_state_tax_charged", inv, data, ctx, 75,
                           f"{number} to an SEZ carries CGST/SGST ({fmt(tax['cgst'] + tax['sgst'], ctx.currency)}); "
                           f"SEZ supplies are inter-state by law (IGST under LUT, or IGST with refund).")
            elif treatment == "overseas":
                failed = []
                pos = str(inv.get("place_of_supply") or "")
                if INDIAN_STATE_CODE.match(pos):
                    failed.append(f"place of supply {pos} is an Indian state")
                if (inv.get("currency_code") or "INR").upper() == "INR":
                    failed.append("invoiced in INR, not convertible foreign exchange")
                if failed:
                    yield _row("export_condition_failed", inv, data, ctx, 80,
                               f"{number} is treated as an export but fails s.2(6) IGST: {'; '.join(failed)}. "
                               f"Unless the conditions are met it is a domestic supply with tax due.",
                               conditions_failed=failed)
            elif treatment == "deemed_export" and tax["total"] <= 0:
                yield _row("deemed_export_untaxed", inv, data, ctx, 65,
                           f"{number} is a deemed export with no tax; deemed exports are taxed and refunded, "
                           f"not zero-rated.")


class LutCover(Rule):
    id = "lut"
    severity = 55

    def evaluate(self, data, ctx):
        luts = [e for e in data.get("exemptions", []) if LUT.search(str(e.get("exemption_reason") or ""))]
        by_fy: dict = {}
        for inv, treatment in zero_rated(data):
            tax = doc_tax(inv)
            if treatment != "deemed_export" and (tax["total"] if tax else money(inv.get("total_tax"))) == 0 \
                    and day(inv.get("date")):
                by_fy.setdefault(fy_label(day(inv["date"]), "gst"), []).append(inv)
        for label, invs in sorted(by_fy.items()):
            value = sum((money(i.get("grand_total")) for i in invs), Decimal("0"))
            names = sorted({party_of(i, data)[1] or "?" for i in invs})
            rule = "lut_validity_unknown" if luts else "lut_missing"
            yield Finding(
                finding_type="zero_rated_supply", rule=rule, severity=self.severity if luts else 85,
                entity_type="FiscalYear", entity_id=label, entity_ref=label, total_exposure=value,
                currency=ctx.currency,
                summary=(f"{len(invs)} {label} zero-rated invoice(s) ({', '.join(names)}, {fmt(value, ctx.currency)}) "
                         + ("rely on an LUT. An LUT record exists, but the platform stores no validity period, FY or "
                            "ARN, so cover can't be confirmed. Record the LUT ARN and FY."
                            if luts else "were issued without tax and no LUT record exists: IGST was payable.")),
                details={"fy": label, "invoices": [i.get("number") for i in invs],
                         "lut_records": [{"id": e.get("id"), "reason": e.get("exemption_reason")} for e in luts]})


class ExportLutTracking(Playbook):

    @property
    def rules(self):
        return [ZeroRatingConditions(), LutCover()]

    def fetch(self, ctx, fetcher) -> Dataset:
        invoices = []
        for treatment in sorted(ZERO_RATED):          # one enum value per call (README Rule 6)
            invoices += fetcher.list("Invoice", direction="receivable", gst_treatment=treatment)
        return Dataset(invoices=invoices, exemptions=fetcher.list("TaxExemption"))

    def context(self, data, findings, ctx):
        rows = list(zero_rated(data))
        return {"zero-rated invoices (posted)": {t: sum(1 for _, x in rows if x == t) for t in sorted(ZERO_RATED)},
                "LUT records (TaxExemption)": sum(1 for e in data["exemptions"]
                                                  if LUT.search(str(e.get("exemption_reason") or ""))),
                "LUT dates / ARN": "not stored on the platform (N426 T4.4)"}

    def summary(self, outcome, ctx):
        lut = [f.summary for f in outcome.findings if f.rule.startswith("lut_")]
        other = [f for f in outcome.findings if not f.rule.startswith("lut_")]
        return (" ".join(lut) or "No zero-tax zero-rated invoices need LUT cover.") + \
            f" {len(other)} invoice(s) fail a zero-rating condition."
