"""LLM-generated, not graded. US-14 filing calendar (spec §5 worked example)."""

from datetime import date

from scripts.uc.US.us14_filing_calendar import SalesTaxFilingCalendar

NEXUS = [{"id": "oh", "state_code": "OH", "is_registered": 1, "registered_on": "2023-09-17",
          "filing_frequency": "monthly", "next_filing_due": None},
         {"id": "mi", "state_code": "MI", "is_registered": 1, "registered_on": "2023-09-17",
          "filing_frequency": "quarterly", "next_filing_due": None}]
JURIS = [{"state_code": "OH", "filing_frequency": "monthly"}, {"state_code": "MI", "filing_frequency": "quarterly"}]
INV = {"date": "2026-09-10", "status": "paid", "taxes": [{"state_code": "MI", "amount": 600}]}


def run(make_ctx, ds, as_of):
    data = ds(nexus=NEXUS, jurisdictions=JURIS, invoices=[INV, {**INV, "date": "2026-07-01"}])
    return SalesTaxFilingCalendar().evaluate(data, make_ctx(tenant="us", as_of=as_of))


def test_michigan_q3_due_on_the_20th(make_ctx, ds):
    due = [f for f in run(make_ctx, ds, date(2026, 10, 15)) if f.rule == "filing_due"]
    mi = next(f for f in due if f.entity_ref == "MI")
    assert mi.details["due_date"] == "2026-10-20" and mi.details["liability"] == "1200.00"


def test_missing_next_due_and_unverifiable_history(make_ctx, ds):
    rules = {f.rule for f in run(make_ctx, ds, date(2026, 10, 4))}
    assert {"next_filing_due_missing", "filing_unverifiable"} <= rules
