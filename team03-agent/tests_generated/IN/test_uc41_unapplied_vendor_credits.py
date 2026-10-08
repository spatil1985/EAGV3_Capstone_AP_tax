"""LLM-generated, not graded. UC-41 unapplied vendor credits."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc41_unapplied_vendor_credits import UnappliedVendorCredits

AS_OF = date(2026, 10, 4)


def run(make_ctx, ds, credits, bills=(), payments=()):
    return UnappliedVendorCredits().evaluate(ds(vendor_credits=credits, bills=list(bills), payments=list(payments)),
                                             make_ctx(as_of=AS_OF))


def test_jindal_credit_applicable_now(make_ctx, ds):
    credits = [{"vendor_id": "j", "_vendor_id_display": "Jindal", "status": "open", "balance": 112548, "date": "2026-08-01",
                "number": "VC-1"}, {"vendor_id": "j", "status": "open", "balance": 204589.59, "date": "2026-09-01",
                                    "number": "VC-99"}]
    bills = [{"vendor_id": "j", "status": "open", "balance_due": 3435771, "due_date": "2026-07-22"}]
    found = run(make_ctx, ds, credits, bills)
    assert [f.rule for f in found] == ["credit_applicable_now"]
    assert found[0].total_exposure == Decimal("317137.59")


def test_stale_credit_and_rounding(make_ctx, ds):
    credits = [{"vendor_id": "x", "status": "open", "balance": 5000, "date": "2026-05-01", "number": "VC-5"},
               {"vendor_id": "y", "status": "open", "balance": 0.4, "date": "2026-05-01", "number": "VC-6"}]
    assert [f.rule for f in run(make_ctx, ds, credits)] == ["stale_credit"]
