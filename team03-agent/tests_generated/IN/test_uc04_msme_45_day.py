"""LLM-generated, not graded. UC-04 MSME 45-day exposure (spec §5 worked example)."""

from datetime import date
from decimal import Decimal

from aptax.domain.rules import RuleVersion
from scripts.uc.IN.uc04_msme_45_day import Msme45DayExposure

AS_OF = date(2026, 9, 25)
VENDOR = {"id": "v1", "name": "Sharma Precision Components", "is_msme": 1, "msme_type": "small",
          "msme_no": "UDYAM-MH-01-0000001"}


def bill(**extra):
    base = {"id": "b1", "bill_number": "BILL-2026-00077", "vendor_id": "v1", "status": "open",
            "date": "2026-06-01", "due_date": None, "balance_due": 300000, "grand_total": 300000}
    return {**base, **extra}


def ctx_at_6_5(make_ctx):
    ctx = make_ctx(as_of=AS_OF)
    ctx.rulebook.entries["rbi_bank_rate_pct"] = [RuleVersion(6.5, None, None, "test", None)]
    return ctx


def test_worked_example_small_enterprise(make_ctx, ds):
    found = Msme45DayExposure().evaluate(ds(bills=[bill()], parties=[VENDOR]), ctx_at_6_5(make_ctx))
    assert len(found) == 1
    f = found[0]
    assert f.details["deadline"] == "2026-07-16" and f.details["overdue_days"] == 71
    # 300000 × ((1 + 0.195/12)^2 − 1); the spec's "≈ 9,810.35" rounded the factor early
    assert f.interest_amount == Decimal("9829.22")
    assert f.details["s43b_h_disallowance_amount"] == "300000.00"


def test_medium_enterprise_has_interest_but_no_43bh(make_ctx, ds):
    found = Msme45DayExposure().evaluate(ds(bills=[bill()], parties=[{**VENDOR, "msme_type": "medium"}]),
                                         ctx_at_6_5(make_ctx))
    assert found[0].details["s43b_h_applicable"] is False


def test_negative_grand_total_is_data_quality_and_blank_udyam_flagged(make_ctx, ds):
    found = Msme45DayExposure().evaluate(
        ds(bills=[bill(grand_total=-5)], parties=[{**VENDOR, "msme_no": ""}]), ctx_at_6_5(make_ctx))
    assert sorted(f.rule for f in found) == ["missing_required_field", "stored_value_mismatch"]


def test_due_within_a_week_is_a_warning(make_ctx, ds):
    found = Msme45DayExposure().evaluate(ds(bills=[bill(date="2026-08-15")], parties=[VENDOR]),
                                         ctx_at_6_5(make_ctx))
    assert [f.rule for f in found] == ["msme_45_day_due_soon"]
