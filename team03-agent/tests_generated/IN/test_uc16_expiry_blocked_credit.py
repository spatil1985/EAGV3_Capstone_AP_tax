"""LLM-generated, not graded. UC-16 expiry warning (spec §5 worked example)."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc16_expiry_blocked_credit import ExpiryBlockedCredit

ITEM = {"id": "vb", "name": "V-Block Pair 239mm", "shelf_life_days": 53, "batch_tracked": 1, "product_type": "goods"}
BILL = {"id": "b", "number": "BILL-X", "status": "open", "date": "2026-09-01", "total_tax": 1800,
        "taxes": [{"tax_type": "IGST", "amount": 1800}],
        "items": [{"item_id": "vb", "qty": 100, "taxable_amount": 10000}]}


def run(make_ctx, ds, items, bills, as_of=date(2026, 9, 28)):
    return ExpiryBlockedCredit().evaluate(ds(items=items, bills=bills), make_ctx(as_of=as_of))


def test_lot_expiring_in_26_days(make_ctx, ds):
    found = run(make_ctx, ds, [ITEM], [BILL])
    assert [f.rule for f in found] == ["expiry_warning"]
    f = found[0]
    assert f.details["expiry_estimate"] == "2026-10-24" and f.details["days_to_expiry"] == 26
    assert f.total_exposure == Decimal("1800.00") and f.details["per_unit_tax"] == "18.00"


def test_far_from_expiry_is_quiet(make_ctx, ds):
    assert run(make_ctx, ds, [ITEM], [BILL], as_of=date(2026, 9, 2)) == []


def test_unbatched_service_item_is_two_data_quality_rows(make_ctx, ds):
    item = {**ITEM, "batch_tracked": 0, "product_type": "services"}
    assert sorted(f.rule for f in run(make_ctx, ds, [item], [BILL])) == [
        "classification_conflict", "missing_required_field"]
