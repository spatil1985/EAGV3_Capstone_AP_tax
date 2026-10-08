"""LLM-generated, not graded. US-18 payment plan (spec §9 withholding fixture)."""

from datetime import date

from scripts.uc.US.us18_payment_run import PaymentRunPrioritisationUS


def run(make_ctx, ds, bills, parties):
    return PaymentRunPrioritisationUS().evaluate(ds(bills=bills, parties=parties, vendor_credits=[]),
                                                 make_ctx(tenant="us", as_of=date(2026, 10, 4)))


def test_canton_paid_net_of_backup_withholding(make_ctx, ds):
    bill = {"id": "b", "number": "BILL-C", "vendor_id": "can", "status": "open", "date": "2026-08-01",
            "due_date": "2026-08-31", "balance_due": 7800, "grand_total": 7800, "approval_status": "approved"}
    found = run(make_ctx, ds, [bill], [{"id": "can", "is_1099_vendor": 1, "w9_on_file": 0}])
    assert found[0].rule == "pay_now"
    assert found[0].details["withheld"] == "1872.00" and found[0].details["amount_to_pay"] == "5928.00"


def test_discount_closing_this_week(make_ctx, ds):
    bill = {"id": "d", "number": "BILL-D", "vendor_id": "v", "status": "open", "date": "2026-09-28",
            "due_date": "2026-10-28", "balance_due": 10000, "payment_terms": "2/10 net 30", "approval_status": "approved"}
    found = run(make_ctx, ds, [bill], [])
    assert found[0].details["reasons"] == ["discount_lost"] and str(found[0].total_exposure) == "200.00"
