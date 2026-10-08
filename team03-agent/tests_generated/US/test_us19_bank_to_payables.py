"""LLM-generated, not graded. US-19: voucher links and unidentified debits (spec §9)."""

from datetime import date

from scripts.uc.US.us19_bank_to_payables import BankToPayablesUS


def test_voucher_match_unidentified_debit_and_missing_payment(make_ctx, ds):
    txns = [{"id": "t1", "type": "debit", "date": "2026-08-08", "amount": 1950, "matched_voucher_type": "PaymentMade",
             "matched_voucher_id": "p1", "categorization_status": "matched"},
            {"id": "t2", "type": "debit", "date": "2026-08-06", "amount": 3000, "categorization_status": "uncategorized"}]
    pays = [{"id": "p1", "number": "POUT-1", "date": "2026-08-08", "amount": 1950, "status": "paid"},
            {"id": "p2", "number": "POUT-66", "date": "2026-08-07", "amount": 8250, "status": "paid"}]
    found = BankToPayablesUS().evaluate(ds(bank_transactions=txns, payments=pays, parties=[], bills=[]),
                                        make_ctx(tenant="us", as_of=date(2026, 10, 4)))
    assert sorted(f.rule for f in found) == ["payment_not_in_bank", "unidentified_debit"]
