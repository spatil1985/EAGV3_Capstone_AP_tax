"""LLM-generated, not graded. US-17 unapplied credits."""

from datetime import date

from scripts.uc.US.us17_unapplied_vendor_credits import UnappliedVendorCreditsUS


def test_no_credits_is_quiet_and_open_credit_applies(make_ctx, ds):
    ctx = make_ctx(tenant="us", as_of=date(2026, 10, 4))
    assert UnappliedVendorCreditsUS().evaluate(ds(vendor_credits=[], bills=[], payments=[]), ctx) == []
    credits = [{"vendor_id": "apex", "status": "open", "balance": 500, "date": "2026-09-01", "number": "VC-1"}]
    bills = [{"vendor_id": "apex", "status": "open", "balance_due": 16739.38}]
    found = UnappliedVendorCreditsUS().evaluate(ds(vendor_credits=credits, bills=bills, payments=[]), ctx)
    assert [f.rule for f in found] == ["credit_applicable_now"]
