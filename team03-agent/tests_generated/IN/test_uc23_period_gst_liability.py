"""LLM-generated, not graded. UC-23 period liability: utilisation order, Rule 86B, oracle."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc23_period_gst_liability import PeriodGstLiability, utilise

D = Decimal


def test_utilisation_order_igst_first_and_no_cgst_sgst_cross():
    out = {"igst": D("100"), "cgst": D("50"), "sgst": D("50"), "cess": D("0")}
    credit = {"igst": D("120"), "cgst": D("0"), "sgst": D("80"), "cess": D("0")}
    cash, used, carried = utilise(out, credit)
    assert cash == {"igst": D("0"), "cgst": D("30"), "sgst": D("0"), "cess": D("0")}   # IGST 20 spills to CGST
    assert carried["sgst"] == D("30")                                                    # SGST never pays CGST


def sale(n, when, cgst, taxable, **extra):
    return {"id": n, "number": n, "direction": "receivable", "status": "sent", "date": when, "total_tax": 2 * cgst,
            "taxable_value": taxable, "taxes": [{"tax_type": "CGST", "amount": cgst}, {"tax_type": "SGST", "amount": cgst}],
            "items": [], **extra}


def run(make_ctx, ds, invoices, bills=(), returns=()):
    data = ds(invoices=invoices, credit_notes=[], bills=list(bills), vendor_credits=[], parties=[], items=[],
              returns=list(returns))
    return PeriodGstLiability().evaluate(data, make_ctx(as_of=date(2026, 9, 15)))


def test_august_cash_by_head_and_oracle_mismatch(make_ctx, ds):
    bill = {"id": "b", "number": "B", "status": "open", "date": "2026-08-10", "itc_eligibility": "input",
            "total_tax": 200, "taxes": [{"tax_type": "CGST", "amount": 100}, {"tax_type": "SGST", "amount": 100}],
            "items": [{"taxable_amount": 1000}]}
    ret = {"id": "r", "return_type": "GSTR-3B", "return_period": "08-2026", "taxable_amount": 999999,
           "cgst_amount": 0, "sgst_amount": 0, "igst_amount": 0, "cess_amount": 0, "filing_status": "unfiled"}
    found = run(make_ctx, ds, [sale("I1", "2026-08-05", 900, 10000)], [bill], [ret])
    heads = {f.details["head"]: f for f in found if f.rule == "head_payable"}
    assert heads["CGST"].details["cash_payable"] == "800.00"
    assert any(f.rule == "stored_value_mismatch" for f in found)


def test_rule_86b_floor(make_ctx, ds):
    bill = {"id": "b", "number": "B", "status": "open", "date": "2026-08-10", "itc_eligibility": "input",
            "total_tax": 1800000, "taxes": [{"tax_type": "IGST", "amount": 1800000}], "items": [{"taxable_amount": 1}]}
    found = run(make_ctx, ds, [sale("I1", "2026-08-05", 450000, 6000000)], [bill])
    assert any(f.rule == "rule_86b_cash_floor" for f in found)
