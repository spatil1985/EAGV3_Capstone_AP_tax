"""LLM-generated, not graded. US-21 escheat (spec §5 constructed example)."""

from datetime import date

from scripts.uc.US.us21_unclaimed_property import UnclaimedProperty

BANK = [{"id": "t", "type": "debit", "date": "2026-02-01", "amount": 1, "categorization_status": "matched"},
        {"id": "u", "type": "debit", "date": "2026-03-01", "amount": 2, "categorization_status": "matched"}]
CHEQUE = {"id": "p", "number": "CHK-1", "date": "2026-02-10", "amount": 4200, "status": "paid", "payment_mode": "cheque",
          "vendor_id": "mi"}


def run(make_ctx, ds, as_of):
    data = ds(payments=[CHEQUE], bank_transactions=BANK, parties=[{"id": "mi", "addresses": [{"state": "MI"}]}],
              org=[{"state": "OH"}], bills=[])
    return UnclaimedProperty().evaluate(data, make_ctx(tenant="us", as_of=as_of))


def test_uncleared_cheque_ages_into_due_diligence_then_reportable(make_ctx, ds):
    assert run(make_ctx, ds, date(2026, 10, 4)) == []
    assert [f.rule for f in run(make_ctx, ds, date(2028, 11, 1))] == ["escheat_due_diligence"]
    found = run(make_ctx, ds, date(2029, 3, 1))
    assert [f.rule for f in found] == ["escheat_reportable"] and found[0].details["dormant_on"] == "2029-02-10"
