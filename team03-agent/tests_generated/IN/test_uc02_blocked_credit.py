"""LLM-generated, not graded. UC-02 blocked credit (spec §5 worked example)."""

from decimal import Decimal

from scripts.uc.IN.uc02_blocked_credit import BlockedCreditAudit


def bill(**extra):
    base = {"id": "b1", "bill_number": "BILL-2026-00087", "_vendor_id_display": "Metro Hospitality",
            "status": "open", "itc_eligibility": "input", "total_tax": 1800, "taxes": [],
            "items": [{"description": "Business Lunch - Client Meeting", "hsn_or_sac": "996331",
                       "taxable_amount": 10000, "tax_percentage": 18, "cgst_amount": 900, "sgst_amount": 900},
                      {"description": "Conference room hire", "hsn_or_sac": "997212",
                       "taxable_amount": 0, "cgst_amount": 0, "sgst_amount": 0}]}
    return {**base, **extra}


def test_catering_line_is_flagged_with_its_own_tax(make_ctx, ds):
    found = BlockedCreditAudit().evaluate(ds(bills=[bill()], items=[]), make_ctx())
    blocked = [f for f in found if f.rule == "section_17_5"]
    assert len(blocked) == 1   # venue hire (SAC 9972, renting) is not a blocked category
    lunch = next(f for f in blocked if f.details["line_index"] == 0)
    assert lunch.details["blocked_category"] == "food_beverage_catering"
    assert lunch.total_exposure == Decimal("1800.00")


def test_ineligible_bill_of_ordinary_inputs_is_under_claimed(make_ctx, ds):
    b = bill(itc_eligibility="ineligible", total_tax=180,
             taxes=[{"tax_type": "IGST", "amount": 180}],
             items=[{"description": "Pump bracket", "hsn_or_sac": "82055900", "taxable_amount": 1000}])
    found = BlockedCreditAudit().evaluate(ds(bills=[b], items=[]), make_ctx())
    assert [f.rule for f in found] == ["itc_possibly_under_claimed"]
    assert found[0].total_exposure == Decimal("180.00")


def test_blank_hsn_is_data_quality(make_ctx, ds):
    b = bill(items=[{"description": "Spares", "hsn_or_sac": "", "taxable_amount": 100}], total_tax=0)
    found = BlockedCreditAudit().evaluate(ds(bills=[b], items=[]), make_ctx())
    assert [f.rule for f in found] == ["missing_required_field"]
