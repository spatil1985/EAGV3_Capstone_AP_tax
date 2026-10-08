"""LLM-generated, not graded. UC-42 payment plan."""

from datetime import date

from scripts.uc.IN.uc42_payment_run import PaymentRunPrioritisation

AS_OF = date(2026, 10, 4)


def bill(bid, **extra):
    base = {"id": bid, "number": bid, "status": "open", "vendor_id": "v", "date": "2026-09-20", "due_date": "2026-11-30",
            "balance_due": 100000, "grand_total": 100000, "itc_eligibility": "input", "approval_status": "not_required",
            "created_at": f"2026-09-20T10:00:{bid[-1]}0"}
    return {**base, **extra}


def run(make_ctx, ds, bills, parties=(), credits=()):
    return PaymentRunPrioritisation().evaluate(ds(bills=bills, parties=list(parties), vendor_credits=list(credits)),
                                               make_ctx(as_of=AS_OF))


def test_msme_breach_is_paid_first_and_rejected_is_held(make_ctx, ds):
    msme = bill("b1", vendor_id="m", date="2026-06-07", due_date="2026-07-22")
    rejected = bill("b2", ims_status="reject", grand_total=5, balance_due=5)
    found = run(make_ctx, ds, [msme, rejected], parties=[{"id": "m", "is_msme": 1, "msme_type": "small"}])
    assert [(f.entity_id, f.rule) for f in found] == [("b1", "pay_now"), ("b2", "hold")]
    assert "msme_45_day" in found[0].details["reasons"]


def test_credit_covering_the_bill_is_net_off(make_ctx, ds):
    found = run(make_ctx, ds, [bill("b3")], credits=[{"vendor_id": "v", "status": "open", "balance": 150000,
                                                      "date": "2026-09-01"}])
    assert [f.rule for f in found] == ["net_off"]


def test_bill_not_due_is_quiet(make_ctx, ds):
    assert run(make_ctx, ds, [bill("b4")]) == []
