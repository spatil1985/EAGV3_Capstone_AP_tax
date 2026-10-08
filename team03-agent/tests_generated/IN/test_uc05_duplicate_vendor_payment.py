"""LLM-generated, not graded. UC-05 duplicate tiers (spec §5 worked example)."""

from decimal import Decimal

from scripts.uc.IN.uc05_duplicate_vendor_payment import DuplicateVendorPayment

LINES = [{"_item_id_display": "EN19 Round Bar 40mm", "qty": 10, "rate": 100}]


def bill(bid, **extra):
    base = {"id": bid, "number": f"BILL-{bid}", "vendor_id": "sandvik", "_vendor_id_display": "Sandvik Tooling",
            "status": "open", "date": "2026-09-12", "grand_total": 353554, "balance_due": 353554,
            "amount_paid": 0, "items": LINES, "created_at": f"2026-09-12T17:19:{40 if bid == 'b' else 39}"}
    return {**base, **extra}


def run(make_ctx, ds, bills, matches=None):
    return DuplicateVendorPayment().evaluate(
        ds(bills=bills, parties=[], payments=[], matches=matches or {}, match_failures=[]), make_ctx())


def test_same_amount_same_items_is_strong_and_holds_later_bill(make_ctx, ds):
    found = run(make_ctx, ds, [bill("a"), bill("b")])
    assert [f.details["tier"] for f in found] == ["suspicious_strong"]
    assert found[0].entity_id == "b" and found[0].details["action"] == "hold_one"
    assert found[0].details["possible_double_submit"] is True


def test_recurring_template_pairs_are_suppressed(make_ctx, ds):
    assert run(make_ctx, ds, [bill("a", recurring_bill_id="r1"), bill("b", recurring_bill_id="r1")]) == []


def test_exact_supplier_number_regardless_of_amount(make_ctx, ds):
    found = run(make_ctx, ds, [bill("a", bill_number="INV/0042"), bill("b", bill_number="inv-42",
                                                                       grand_total=1, date="2026-09-30")])
    assert [f.details["tier"] for f in found] == ["exact"]


def test_over_billed_from_bill_match(make_ctx, ds):
    match = {"live": {"lines": [{"ordered_qty": 2, "billed_to_date_qty": 4, "bill_rate": 1284.272}]}}
    found = run(make_ctx, ds, [bill("a", purchase_order_id="po1")], matches={"a": match})
    assert found[0].rule == "duplicate_over_billed"
    assert found[0].total_exposure == Decimal("2568.54")


def test_negative_totals_never_pair(make_ctx, ds):
    assert run(make_ctx, ds, [bill("a", grand_total=-5, items=[]), bill("b", grand_total=-5, items=[])]) == []
