"""LLM-generated, not graded. UC-01 Rule 37 reversal (spec §5 worked example and §9 boundaries)."""

from datetime import date, timedelta
from decimal import Decimal

from scripts.uc.IN.uc01_rule37_itc_reversal import Rule37Reversal

AS_OF = date(2026, 9, 25)


def bill(days_old, **extra):
    base = {"id": f"b{days_old}", "bill_number": f"BILL-{days_old}", "vendor_id": "v1",
            "_vendor_id_display": "Bosch Rexroth India", "status": "open", "itc_eligibility": "input",
            "date": str(AS_OF - timedelta(days=days_old)), "balance_due": 50000, "grand_total": 59000,
            "amount_paid": 0, "total_tax": 9000,
            "taxes": [{"tax_type": "CGST", "amount": 4500}, {"tax_type": "SGST", "amount": 4500}]}
    return {**base, **extra}


def test_worked_example_253_days(make_ctx, ds):
    found = Rule37Reversal().evaluate(ds(bills=[bill(253)]), make_ctx(as_of=AS_OF))
    assert len(found) == 1
    f = found[0]
    assert f.reversal_base_amount == Decimal("9000.00")
    assert f.interest_amount == Decimal("324.00")
    assert f.total_exposure == Decimal("9324.00")


def test_boundary_180_is_compliant_181_is_not(make_ctx, ds):
    found = Rule37Reversal().evaluate(ds(bills=[bill(179), bill(180), bill(181)]), make_ctx(as_of=AS_OF))
    assert [f.entity_id for f in found] == ["b181"]


def test_paid_draft_and_ineligible_are_out_of_scope(make_ctx, ds):
    bills = [bill(200, id="paid", balance_due=0), bill(200, id="draft", status="draft"),
             bill(200, id="inel", itc_eligibility="ineligible")]
    assert Rule37Reversal().evaluate(ds(bills=bills), make_ctx(as_of=AS_OF)) == []


def test_unsourced_tax_becomes_data_quality(make_ctx, ds):
    bad = bill(200, taxes=[], total_tax=900, items=[{"cgst_amount": 10, "sgst_amount": 10}])
    found = Rule37Reversal().evaluate(ds(bills=[bad]), make_ctx(as_of=AS_OF))
    assert [f.finding_type for f in found] == ["data_quality"]
