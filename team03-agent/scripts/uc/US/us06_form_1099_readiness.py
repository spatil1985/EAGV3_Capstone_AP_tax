"""US-06 — Form 1099 readiness and backup withholding.

Spec: docs/usecases/US/us-06-form-1099-readiness.md.
Question: "Which vendors will need a 1099 for this year, and do we have what we need to file it — or should
we be withholding?"

Statute: IRC 6041/6041A (1099-MISC / 1099-NEC to non-corporate payees at or above the threshold —
$2,000 from 2026 under OBBBA 2025, confirm); IRC 3406 (24% backup withholding when no TIN).

Oracle: GET /api/cpa/reports/1099-summary?year= (REST, allowlisted). `Party.tin` is redacted for our role,
so TIN presence comes from the report's `tin_on_file`.

Rules (calendar year; reportable = the report's meets_threshold):
  w9_missing                   reportable vendor with no W-9 on file
  tin_missing                  reportable vendor with no TIN
  backup_withholding_required  no TIN and payments made: 24% of the reportable amount
  box_unmapped                 reportable vendor with no 1099 box
  classification_missing       paid at or above the threshold with no US tax classification
  stored_value_mismatch        the report's total_paid ≠ PaymentMade for the year
Approaching vendors (≥ 80% of the threshold, non-corporate) are context.
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day

REPORT = "/api/cpa/reports/1099-summary"
CORPORATE = {"c_corporation", "s_corporation", "llc_c_corp", "llc_s_corp", "corporation"}


def paid_this_year(data, ctx) -> dict:
    start = date(ctx.as_of.year, 1, 1)
    out: dict = {}
    for p in data.get("payments", []):
        d = day(p.get("date"))
        if d and start <= d <= ctx.as_of and (p.get("status") or "").lower() not in ("void", "draft", "cancelled"):
            out[p.get("vendor_id")] = out.get(p.get("vendor_id"), Decimal("0")) + money(p.get("amount"))
    return out


class Form1099(Rule):
    id = "form_1099"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        report = data.get("report") or {}
        rate = Decimal(str(ctx.constant("backup_withholding_rate_pct"))) / 100
        threshold = money(ctx.rule("form_1099_threshold_usd"))
        paid = paid_this_year(data, ctx)
        for v in report.get("vendors") or []:
            if not v.get("meets_threshold"):
                continue
            vid, name = v.get("vendor_id"), v.get("vendor_name")
            amount = money(v.get("reportable_amount"))
            base = dict(entity_type="Party", entity_id=vid, entity_ref=name, currency=ctx.currency, counterparty_id=vid,
                        counterparty_name=name)
            det = {"tax_year": report.get("tax_year"), "reportable_amount": str(amount), "box": v.get("box"),
                   "form_type": v.get("form_type")}
            if v.get("needs_w9") or not v.get("w9_on_file"):
                yield Finding(finding_type="form_1099", rule="w9_missing", severity=60, **base, details=det,
                              summary=f"{name} ({fmt(amount, ctx.currency)} reportable on {v.get('form_type')}) has no W-9 "
                                      f"on file — request one before January.")
            if not v.get("tin_on_file"):
                bw = (amount * rate).quantize(CENTS)
                yield Finding(finding_type="form_1099", rule="backup_withholding_required", severity=85,
                              total_exposure=bw, **base, details={**det, "rule_also": "tin_missing"},
                              summary=f"{name} has been paid {fmt(amount, ctx.currency)} with no TIN on file: backup "
                                      f"withholding of 24% ({fmt(bw, ctx.currency)}) was required (IRC 3406).")
            if not v.get("box"):
                yield Finding(finding_type="form_1099", rule="box_unmapped", severity=45, **base, details=det,
                              summary=f"{name} is reportable but has no 1099 box mapped.")
            ours = paid.get(vid, Decimal("0"))
            if abs(ours - money(v.get("total_paid"))) > 1:
                yield Finding(finding_type=DATA_QUALITY, rule="stored_value_mismatch", status=DATA_QUALITY, severity=30,
                              **base, details={"report": str(money(v.get("total_paid"))), "payments": str(ours)},
                              summary=f"{name}: the 1099 report says {fmt(money(v.get('total_paid')), ctx.currency)} paid; "
                                      f"payments this year add up to {fmt(ours, ctx.currency)}.")
        parties = data.index("parties", "id")
        for vid, total in paid.items():
            party = parties.get(vid) or {}
            if total >= threshold and not party.get("us_tax_classification"):
                yield Finding(finding_type="form_1099", rule="classification_missing", severity=50, entity_type="Party",
                              entity_id=vid, entity_ref=party.get("name"), currency=ctx.currency,
                              counterparty_id=vid, counterparty_name=party.get("name"),
                              summary=f"{party.get('name')} was paid {fmt(total, ctx.currency)} this year with no US tax "
                                      f"classification, so whether a 1099 is due can't be decided.",
                              details={"paid": str(total)})


class Form1099Readiness(Playbook):

    @property
    def rules(self):
        return [Form1099()]

    def fetch(self, ctx, fetcher) -> Dataset:
        report = fetcher.rest_get(REPORT, {"year": ctx.as_of.year})
        return Dataset(report=report, parties=fetcher.list("Party"), payments=fetcher.list("PaymentMade"))

    def context(self, data, findings, ctx):
        rep = data.get("report") or {}
        threshold = money(ctx.rule("form_1099_threshold_usd"))
        parties = data.index("parties", "id")
        near = [(parties.get(v) or {}).get("name") for v, t in paid_this_year(data, ctx).items()
                if threshold * Decimal("0.8") <= t < threshold
                and (parties.get(v) or {}).get("us_tax_classification") not in CORPORATE]
        return {"tax year": rep.get("tax_year"), "threshold": str(threshold), "reportable vendors": rep.get("reportable_count"),
                "total reportable": str(money(rep.get("total_reportable"))),
                "excluded corporations": rep.get("excluded_corporation_count"), "approaching the threshold": near}

    def summary(self, outcome, ctx):
        c = outcome.context
        w9 = [f.entity_ref for f in outcome.findings if f.rule == "w9_missing"]
        bw = [f for f in outcome.findings if f.rule == "backup_withholding_required"]
        return (f"{c['reportable vendors']} vendor(s) will receive a {c['tax year']} Form 1099 "
                f"({fmt(money(c['total reportable']), ctx.currency)}). "
                + (f"No W-9 on file for {', '.join(w9)} — request one now. " if w9 else "All have a W-9. ")
                + (f"Backup withholding was required for {len(bw)} vendor(s)."
                   if bw else "No backup withholding is required: every reportable vendor has a TIN on file."))
