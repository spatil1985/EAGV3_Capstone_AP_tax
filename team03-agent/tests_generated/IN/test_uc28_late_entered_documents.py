"""LLM-generated, not graded. UC-28 late-entered documents."""

from scripts.uc.IN.uc28_late_entered_documents import LateEnteredDocuments

RETURNS = [{"id": "r", "return_type": "GSTR-3B", "return_period": "07-2026", "filing_status": "filed",
            "filed_date": "2026-08-08"}]
LOCKS = [{"id": "l", "module": "sales", "lock_date": "2026-07-31", "created_at": "2026-09-12T17:20:00"}]


def run(make_ctx, ds, invoices):
    data = ds(returns=RETURNS, locks=LOCKS, periods=[], Invoice=invoices, CreditNote=[], Bill=[], VendorCredit=[],
              PaymentMade=[], Expense=[])
    return LateEnteredDocuments().evaluate(data, make_ctx())


def test_july_invoice_entered_after_filing(make_ctx, ds):
    inv = {"id": "i", "number": "INV-X", "status": "sent", "date": "2026-07-20", "created_at": "2026-08-20T10:00:00",
           "total_tax": 900}
    found = run(make_ctx, ds, [inv])
    assert [f.rule for f in found] == ["entered_after_filing"]
    assert found[0].details["days_after_close"] == 12


def test_backdated_but_open_period(make_ctx, ds):
    inv = {"id": "b", "number": "INV-B", "status": "sent", "date": "2026-08-01", "created_at": "2026-09-20T10:00:00"}
    assert [f.rule for f in run(make_ctx, ds, [inv])] == ["backdated_document"]


def test_entered_on_time_is_quiet(make_ctx, ds):
    inv = {"id": "ok", "number": "INV-OK", "status": "sent", "date": "2026-07-20", "created_at": "2026-07-21T10:00:00"}
    assert run(make_ctx, ds, [inv]) == []
