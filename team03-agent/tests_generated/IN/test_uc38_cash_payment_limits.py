"""LLM-generated, not graded. UC-38 cash limits."""

from scripts.uc.IN.uc38_cash_payment_limits import CashPaymentLimits


def exp(eid, amount, account="Advertising", through="Cash", vendor="v1", when="2026-09-07"):
    return {"id": eid, "number": eid, "date": when, "amount": amount, "paid_through_account": through,
            "_account_id_display": account, "vendor_id": vendor, "_vendor_id_display": "Anil", "status": "unbilled"}


def run(make_ctx, ds, expenses, bills=()):
    return CashPaymentLimits().evaluate(ds(payments=[], expenses=expenses, bills=list(bills),
                                           bank_accounts=[{"name": "Petty Cash — Plant", "account_type": "cash"}]),
                                        make_ctx())


def test_split_payments_same_day_are_added_up(make_ctx, ds):
    found = run(make_ctx, ds, [exp("a", 6000), exp("b", 6000)])
    assert [f.rule for f in found] == ["cash_payment_disallowed"]
    assert found[0].details["daily_total"] == "12000.00"


def test_goods_carriage_limit_and_bank_payment(make_ctx, ds):
    found = run(make_ctx, ds, [exp("t", 30000, account="Freight Inward"), exp("k", 50000, through="HDFC Current")])
    assert found == []


def test_cash_bill_and_wages(make_ctx, ds):
    bill = {"id": "b", "number": "BILL-44", "payment_gateway": "cash", "balance_due": 139617.92, "status": "open"}
    rules = sorted(f.rule for f in run(make_ctx, ds, [exp("w", 20000, account="Direct Wages")], [bill]))
    assert rules == ["cash_payment_planned", "cash_payment_wages"]
