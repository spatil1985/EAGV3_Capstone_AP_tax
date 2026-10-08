"""UC-01 — Rule 37: 180-day non-payment ITC reversal.

Spec: docs/usecases/IN/uc-01-rule-37-itc-reversal.md.
Question: "Which unpaid bills are about to cost me my input credit, and how much?"

Statute: s.16(2) second proviso CGST Act + Rule 37 — ITC on a bill not paid within 180
days of the invoice date is added back to output tax, with s.50(1) interest at 18% p.a.

Rule (spec §5, with the 2026-09-30 tax-source correction):
  rule_37_180_day   ITC-eligible, posted (not draft/void), balance_due > 0, age > 180 days.
                    Reversal = the bill's ITC from its trusted tax source (taxes[] or valid
                    item lines); interest = ITC × 18% × (age − 180) / 365.
  data_quality      an in-scope bill whose tax can't be sourced; excluded from totals.

Partial payment (spec §10, open): the full ITC is reversed — the conservative reading the
spec chose. The pro-rata figure (ITC × balance_due / grand_total) is kept in `details`.
Bills crossing day 180 within the warning window are reported as context, not findings.
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tax import doc_tax, untrusted_tax

FINDING_TYPE = "itc_reversal"
ELIGIBLE = {"input", "input_services", "capital_goods"}


def in_scope(bill: dict) -> bool:
    return (bill.get("itc_eligibility") in ELIGIBLE
            and (bill.get("status") or "").lower() not in NOT_POSTED
            and money(bill.get("balance_due")) > 0
            and day(bill.get("date")) is not None)


def age_days(bill: dict, ctx) -> int:
    return (ctx.as_of - day(bill["date"])).days


class Rule37Breach(Rule):
    id = "rule_37_180_day"
    severity = 85

    def evaluate(self, data: Dataset, ctx):
        window = int(ctx.constant("itc_payment_window_days"))
        rate = Decimal(str(ctx.constant("gst_interest_rate_pct"))) / 100
        for bill in data.get("bills", []):
            if not in_scope(bill) or age_days(bill, ctx) <= window:
                continue
            tax = doc_tax(bill)
            if tax is None:
                yield untrusted_tax(bill, "Bill", blocks="UC-01 reversal amount", currency=ctx.currency)
                continue
            itc = tax["total"]
            if itc <= 0:
                continue          # aged, but no credit was claimed on it: nothing to reverse
            age = age_days(bill, ctx)
            interest = (itc * rate * (age - window) / 365).quantize(CENTS)
            balance, grand = money(bill.get("balance_due")), money(bill.get("grand_total"))
            pro_rata = (itc * balance / grand).quantize(CENTS) if grand > 0 else itc
            vid, vname = party_of(bill, data)
            number = ref(bill, "bill_number", "number")
            yield Finding(
                finding_type=FINDING_TYPE, rule=self.id, severity=self.severity,
                entity_type="Bill", entity_id=bill["id"], entity_ref=number,
                reversal_base_amount=itc, interest_amount=interest, total_exposure=itc + interest,
                currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                summary=f"{number} ({vname}) — {age} days unpaid, {fmt(itc, ctx.currency)} ITC must be "
                        f"reversed, {fmt(interest, ctx.currency)} interest, "
                        f"{fmt(itc + interest, ctx.currency)} total.",
                details={"trigger_date": bill.get("date"), "age_days": age,
                         "balance_due": str(balance), "grand_total": str(grand),
                         "tax_source": tax["source"], "itc_heads": {h: str(tax[h]) for h in ("cgst", "sgst", "igst", "cess")},
                         "pro_rata_reversal_if_partial": str(pro_rata),
                         "partially_paid": money(bill.get("amount_paid")) > 0},
            )


class Rule37Reversal(Playbook):

    @property
    def rules(self):
        return [Rule37Breach()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"))

    def approaching(self, data, ctx) -> list[dict]:
        window = int(ctx.constant("itc_payment_window_days"))
        warn = int(ctx.constant("itc_reversal_warning_days"))
        out = []
        for bill in data.get("bills", []):
            if in_scope(bill) and window - warn < age_days(bill, ctx) <= window:
                tax = doc_tax(bill)
                out.append({"bill": ref(bill, "bill_number", "number"),
                            "crosses_on": str(day(bill["date"]) + timedelta(days=window + 1)),
                            "itc": str(tax["total"]) if tax else "unsourced"})
        return sorted(out, key=lambda r: r["crosses_on"])

    def context(self, data, findings, ctx):
        bills = data["bills"]
        scope = [b for b in bills if in_scope(b)]
        oldest = max((age_days(b, ctx) for b in scope), default=None)
        soon = self.approaching(data, ctx)
        return {"bills": len(bills), "in scope (ITC-eligible, posted, unpaid)": len(scope),
                "oldest in-scope bill (days)": oldest,
                f"crossing day {ctx.constant('itc_payment_window_days')} within "
                f"{ctx.constant('itc_reversal_warning_days')} days": len(soon),
                "next to cross": soon[:5]}

    def summary(self, outcome, ctx):
        rows = [f for f in outcome.findings if f.finding_type == FINDING_TYPE]
        dq = len(outcome.findings) - len(rows)
        if not rows:
            return (f"No unpaid ITC-eligible bill has crossed {ctx.constant('itc_payment_window_days')} days."
                    + (f" {dq} bill(s) excluded: tax could not be sourced." if dq else ""))
        itc = sum((f.reversal_base_amount for f in rows), Decimal("0"))
        interest = sum((f.interest_amount for f in rows), Decimal("0"))
        return (f"{len(rows)} unpaid bill(s) have crossed {ctx.constant('itc_payment_window_days')} days; "
                f"total ITC exposure {fmt(itc, ctx.currency)}, total interest {fmt(interest, ctx.currency)}."
                + (f" {dq} bill(s) excluded: tax could not be sourced." if dq else ""))
