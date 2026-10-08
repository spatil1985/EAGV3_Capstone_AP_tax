"""LLM-generated, not graded. US-15 late entries."""

from scripts.uc.US.us15_late_entered_documents import LateEnteredDocumentsUS


def doc(n, when, created, **extra):
    return {"id": n, "number": n, "status": "paid", "date": when, "created_at": created, "net_total": 1000,
            "total_tax": 65, **extra}


def run(make_ctx, ds, invoices=(), bills=()):
    data = ds(locks=[], periods=[], org=[{"state": "OH"}], Invoice=list(invoices), Bill=list(bills), CreditNote=[],
              VendorCredit=[], PaymentMade=[], Expense=[])
    return LateEnteredDocumentsUS().evaluate(data, make_ctx(tenant="us"))


def test_bulk_back_entry_is_one_row_per_month(make_ctx, ds):
    invoices = [doc(f"i{k}", "2026-03-10", "2026-09-16T10:00:00") for k in range(3)] + \
               [doc("j", "2026-07-02", "2026-09-16T10:00:00")]
    found = run(make_ctx, ds, invoices)
    assert sorted((f.rule, f.details["period"], f.details["count"]) for f in found) == [
        ("entered_into_reported_period", "2026-03", 3), ("entered_into_reported_period", "2026-07", 1)]


def test_backdated_bill_and_timely_invoice(make_ctx, ds):
    found = run(make_ctx, ds, [doc("ok", "2026-09-01", "2026-09-02T09:00:00")],
                [doc("b", "2026-06-01", "2026-09-16T10:00:00")])
    assert [(f.rule, f.entity_type) for f in found] == [("backdated_document", "Bill")]
