"""LLM-generated, not graded. US-06 Form 1099 (spec §5 worked example)."""

from datetime import date
from decimal import Decimal

from scripts.uc.US.us06_form_1099_readiness import Form1099Readiness

REPORT = {"tax_year": 2026, "vendors": [
    {"vendor_id": "tus", "vendor_name": "Tuscarawas Machining", "meets_threshold": True, "w9_on_file": True,
     "tin_on_file": True, "box": "NEC-1", "form_type": "1099-NEC", "reportable_amount": 18450, "total_paid": 18450},
    {"vendor_id": "can", "vendor_name": "Canton Industrial Consulting", "meets_threshold": True, "w9_on_file": False,
     "needs_w9": True, "tin_on_file": False, "box": "NEC-1", "form_type": "1099-NEC", "reportable_amount": 7800,
     "total_paid": 7800}]}


def run(make_ctx, ds):
    payments = [{"vendor_id": "tus", "date": "2026-03-01", "amount": 18450, "status": "paid"},
                {"vendor_id": "can", "date": "2026-03-01", "amount": 7800, "status": "paid"}]
    parties = [{"id": "tus", "us_tax_classification": "llc_partnership"},
               {"id": "can", "us_tax_classification": "individual_sole_proprietor"}]
    return Form1099Readiness().evaluate(ds(report=REPORT, parties=parties, payments=payments),
                                        make_ctx(tenant="us", as_of=date(2026, 10, 3)))


def test_canton_needs_w9_and_backup_withholding(make_ctx, ds):
    found = {(f.entity_id, f.rule): f for f in run(make_ctx, ds)}
    assert set(found) == {("can", "w9_missing"), ("can", "backup_withholding_required")}
    assert found[("can", "backup_withholding_required")].total_exposure == Decimal("1872.00")
