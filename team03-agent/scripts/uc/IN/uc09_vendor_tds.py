"""UC-09 — Vendor TDS verification.

Spec: docs/usecases/IN/uc-09-vendor-tds-verification.md.
Question: "Are we deducting the right TDS on every vendor payment, under the right section?"

Statute: Income-tax Act 1961 ss.194C/194J/194I (contract, professional/technical, rent),
s.206AA (no PAN), CBDT Circular 23/2017 (base excludes GST). Renumbered by the 2025 Act from
1 April 2026 — confirm citations.

Rules (one finding per bill; the worst rule leads, the rest are listed in `also`):
  tds_exceeds_bill       stored TDS > base: the payable goes negative (blocks payment)
  tds_arithmetic_wrong   stored amount ≠ base × stored rate (> ₹1)
  tds_on_goods           TDS on a bill whose lines are all goods HSN (194Q is UC-13's)
  tds_section_missing    TDS deducted with no section
  tds_rate_wrong         stored rate ≠ the section's rate
  tds_not_deducted       a 194C/J/I bill above the threshold with no TDS
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day, fy_start
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tds import all_goods, base, expected, stored

ORDER = ["tds_exceeds_bill", "tds_arithmetic_wrong", "tds_on_goods", "tds_section_missing",
         "tds_rate_wrong", "tds_not_deducted"]
SEVERITY = {"tds_exceeds_bill": 90, "tds_arithmetic_wrong": 75, "tds_on_goods": 70,
            "tds_section_missing": 55, "tds_rate_wrong": 60, "tds_not_deducted": 65}


def posted(bills):
    """Open and draft bills: a draft with phantom TDS is the one to fix before it is approved.
    Void, cancelled and rejected bills will never be paid."""
    return [b for b in bills if (b.get("status") or "").lower() not in NOT_POSTED - {"draft"}]


def fy_totals(bills, ctx) -> dict:
    """Aggregate 194C base per vendor in the current FY (for the annual threshold)."""
    start = fy_start(ctx.as_of, ctx.tax_regime)
    out: dict = {}
    for b in posted(bills):
        d = day(b.get("date"))
        if d and d >= start:
            for section, _, value, _, _ in expected(b, None, ctx):
                if section == "194C":
                    out[b.get("vendor_id")] = out.get(b.get("vendor_id"), Decimal("0")) + value
    return out


def over_threshold(section: str, value: Decimal, vendor_fy: Decimal, ctx) -> bool:
    if section == "194C":
        return value > money(ctx.constant("tds_threshold_194c_single_inr")) or \
            vendor_fy > money(ctx.constant("tds_threshold_194c_annual_inr"))
    if section == "194J":
        return value > money(ctx.constant("tds_threshold_194j_inr"))
    return value > money(ctx.constant("tds_threshold_194i_monthly_inr"))


class TdsChecks(Rule):
    id = "tds_verification"
    severity = 75

    def evaluate(self, data: Dataset, ctx):
        parties = data.index("parties", "id")
        totals = fy_totals(data.get("bills", []), ctx)
        for bill in posted(data.get("bills", [])):
            party = parties.get(bill.get("vendor_id"))
            amount, pct, section = stored(bill)
            b = base(bill)
            exp = expected(bill, party, ctx)
            exp_amount = sum((e[4] for e in exp), Decimal("0"))
            hits = []
            if amount > 0:
                if amount > b:
                    hits.append("tds_exceeds_bill")
                if abs(amount - (b * pct / 100).quantize(CENTS)) > 1:
                    hits.append("tds_arithmetic_wrong")
                if all_goods(bill):
                    hits.append("tds_on_goods")
                if not section:
                    hits.append("tds_section_missing")
                if exp and pct and all(e[3] != pct for e in exp):
                    hits.append("tds_rate_wrong")
            elif exp and any(over_threshold(e[0], e[2], totals.get(bill.get("vendor_id"), Decimal("0")), ctx)
                             for e in exp) and exp_amount > 0:
                hits.append("tds_not_deducted")
            if not hits:
                continue
            hits.sort(key=ORDER.index)
            lead = hits[0]
            vid, vname = party_of(bill, data)
            number = ref(bill, "number", "bill_number")
            diff = abs(amount - exp_amount)
            sections = sorted({e[0] for e in exp})
            text = {
                "tds_exceeds_bill": f"{fmt(amount, ctx.currency)} TDS on a {fmt(b, ctx.currency)} base; the payable "
                                    f"has gone negative ({fmt(money(bill.get('grand_total')), ctx.currency)}). Do not pay; "
                                    f"correct the bill.",
                "tds_arithmetic_wrong": f"stored TDS {fmt(amount, ctx.currency)} doesn't match its own rate "
                                        f"({pct}% of {fmt(b, ctx.currency)}).",
                "tds_on_goods": f"{fmt(amount, ctx.currency)} TDS on a goods-only bill; no 194C/J/I section applies.",
                "tds_section_missing": f"{fmt(amount, ctx.currency)} TDS deducted with no section.",
                "tds_rate_wrong": f"stored rate {pct}% is not the {', '.join(sections)} rate.",
                "tds_not_deducted": f"{', '.join(sections)} applies ({fmt(exp_amount, ctx.currency)} expected) but no "
                                    f"TDS was deducted.",
            }[lead]
            yield Finding(
                finding_type="tds_verification", rule=lead, severity=SEVERITY[lead], entity_type="Bill",
                entity_id=bill["id"], entity_ref=number, total_exposure=diff, currency=ctx.currency,
                counterparty_id=vid, counterparty_name=vname, summary=f"{number} ({vname}) — {text}",
                details={"also": hits[1:], "base_amount": str(b), "stored_tds_percentage": str(pct),
                         "stored_tds_amount": str(amount), "stored_section": section,
                         "stored_section_code": bill.get("_suspect_tds_section_code"),
                         "expected_sections": sections, "expected_tds_amount": str(exp_amount),
                         "difference": str(diff), "recurring_bill_id": bill.get("recurring_bill_id"),
                         "pan_on_file": bool((party or {}).get("pan")),
                         "rate_if_no_pan_pct": ctx.constant("tds_rate_206aa_pct")},
            )


class VendorTdsVerification(Playbook):

    @property
    def rules(self):
        return [TdsChecks()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"))

    @staticmethod
    def sort_key(f):
        return (ORDER.index(f.rule), -f.total_exposure)

    def context(self, data, findings, ctx):
        bills = posted(data["bills"])
        with_tds = [b for b in bills if stored(b)[0] > 0]
        return {"open and draft bills": len(bills), "bills with TDS": len(with_tds),
                "sum of stored TDS": str(sum((stored(b)[0] for b in with_tds), Decimal("0"))),
                "bills with a negative payable": sum(1 for b in bills if money(b.get("grand_total")) < 0),
                "vendors with a PAN on file": sum(1 for p in data["parties"] if p.get("pan")),
                "void bills carrying TDS (not checked)": sum(
                    1 for b in data["bills"] if b not in bills and stored(b)[0] > 0)}

    def summary(self, outcome, ctx):
        wrong = [f for f in outcome.findings if f.rule != "tds_not_deducted"]
        missing = [f for f in outcome.findings if f.rule == "tds_not_deducted"]
        phantom = sum((money(f.details["stored_tds_amount"]) for f in wrong), Decimal("0"))
        neg = sum(1 for f in outcome.findings if f.rule == "tds_exceeds_bill")
        return (f"{outcome.context.get('bills with TDS', 0)} open or draft bill(s) carry TDS; {len(wrong)} wrong "
                f"({fmt(phantom, ctx.currency)} stored); {neg} with TDS above the bill; {len(missing)} possibly "
                f"missing TDS. {outcome.context.get('void bills carrying TDS (not checked)', 0)} void "
                f"bills also carry TDS and were not checked.")
