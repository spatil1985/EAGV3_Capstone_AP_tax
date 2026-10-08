"""LLM-generated, not graded. UC-27 filing timeliness (spec §5 worked example, 2026-10-04)."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc27_return_filing_timeliness import ReturnFilingTimeliness

ROWS = [
    {"id": "g1", "return_type": "GSTR-1", "return_period": "08-2026", "filing_status": "unfiled", "due_date": "2026-09-11"},
    {"id": "g3", "return_type": "GSTR-3B", "return_period": "08-2026", "filing_status": "unfiled",
     "due_date": "2026-09-20", "net_tax_payable": 572073.68},
    {"id": "g2b", "return_type": "GSTR-2B", "return_period": "08-2026", "filing_status": "unfiled", "due_date": "2026-09-14"},
    {"id": "j1", "return_type": "GSTR-1", "return_period": "07-2026", "filing_status": "filed",
     "due_date": "2026-08-11", "filed_date": "2026-08-08"},
]


def run(make_ctx, ds, rows=ROWS):
    data = ds(returns=rows, invoices=[{"date": "2026-07-05"}], credit_notes=[], bills=[], vendor_credits=[],
              parties=[], items=[])
    return ReturnFilingTimeliness().evaluate(data, make_ctx(as_of=date(2026, 10, 4)))


def test_august_overdue_fees_and_interest(make_ctx, ds):
    found = {f.entity_ref: f for f in run(make_ctx, ds) if f.rule == "return_overdue"}
    assert found["GSTR-1 08-2026"].details["late_fee"] == "1150.00"
    three_b = found["GSTR-3B 08-2026"]
    assert three_b.details["late_fee"] == "700.00" and three_b.interest_amount == Decimal("3949.66")


def test_knock_ons_and_meaningless_2b(make_ctx, ds):
    rules = {f.rule for f in run(make_ctx, ds)}
    assert {"eway_block_risk", "return_status_meaningless", "return_not_generated"} <= rules
