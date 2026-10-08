"""LLM-generated, not graded. US-01 sales tax by jurisdiction against the report."""

from datetime import date

from scripts.uc.US.us01_period_sales_use_tax import PeriodSalesUseTax


def inv(n, rows, net=296):
    return {"id": n, "direction": "receivable", "status": "paid", "date": "2026-05-01", "net_total": net, "taxes": rows}


OH = {"jurisdiction_id": "oh", "jurisdiction_name": "Ohio State Sales Tax", "state_code": "OH", "rate": 5.75}
STARK = {"jurisdiction_id": "stark", "jurisdiction_name": "Stark County (OH)", "state_code": "OH", "rate": 0.75}


def run(make_ctx, ds, invoices, report):
    data = ds(invoices=invoices, bills=[], jurisdictions=[], report=report)
    return PeriodSalesUseTax().evaluate(data, make_ctx(tenant="us", as_of=date(2026, 9, 30)))


def test_matches_report_and_flags_count_gap(make_ctx, ds):
    invoices = [inv("a", [{**OH, "amount": 17.02}, {**STARK, "amount": 2.22}]),
                inv("b", [{**STARK, "amount": 0, "is_exempt": True}])]
    report = {"jurisdictions": [{"jurisdiction_id": "oh", "tax_billed": 17.02, "invoice_count": 1},
                                {"jurisdiction_id": "stark", "tax_billed": 2.22, "invoice_count": 2}]}
    found = run(make_ctx, ds, invoices, report)
    liab = {f.entity_id: f for f in found if f.rule == "tax_liability"}
    assert liab["oh"].details["reconciled"] and liab["stark"].details["reconciled"]
    gaps = [f for f in found if f.rule == "stored_value_mismatch"]
    assert len(gaps) == 1 and gaps[0].entity_ref == "Stark County (OH)"
