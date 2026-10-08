"""LLM-generated, not graded. UC-43 bank reconciliation."""

from scripts.uc.IN.uc43_bank_to_payables import BankToPayables

PARTIES = [{"id": "j", "name": "Jindal Steel Depot"}]


def run(make_ctx, ds, txns, payments=(), bills=()):
    return BankToPayables().evaluate(ds(bank_transactions=txns, payments=list(payments), parties=PARTIES,
                                        bills=list(bills)), make_ctx())


def test_debit_without_payment_and_same_amount_bill(make_ctx, ds):
    txn = {"id": "t", "type": "debit", "date": "2026-08-09", "amount": 385000, "payee": "Jindal Steel Depot",
           "categorization_status": "uncategorized"}
    bill = {"number": "BILL-9", "vendor_id": "j", "status": "open", "balance_due": 385000}
    found = run(make_ctx, ds, [txn], bills=[bill])
    assert [f.rule for f in found] == ["bank_debit_unrecorded"]
    assert found[0].details["open_bills_same_amount"] == ["BILL-9"]


def test_matched_by_payee_amount_date_and_missing_payment(make_ctx, ds):
    txn = {"id": "t", "type": "debit", "date": "2026-08-09", "amount": 385000, "payee": "Jindal Steel Depot Pvt Ltd",
           "categorization_status": "matched"}
    paid = {"id": "p", "number": "PAY-1", "vendor_id": "j", "date": "2026-08-07", "amount": 385000.5, "status": "paid"}
    other = {"id": "q", "number": "PAY-2", "vendor_id": "j", "date": "2026-08-09", "amount": 10, "status": "paid"}
    rules = sorted(f.rule for f in run(make_ctx, ds, [txn], [paid, other]))
    assert rules == ["match_without_voucher", "payment_not_in_bank"]
