"""LLM-generated, not graded. UC-11 three-way match (spec §5 worked example BILL-2026-00018)."""

from scripts.uc.IN.uc11_three_way_match import ThreeWayMatch

BILL = {"id": "b18", "number": "BILL-2026-00018", "vendor_id": "v", "_vendor_id_display": "Pune Industrial",
        "status": "open", "purchase_order_id": "po", "grand_total": 64664, "balance_due": 64664}
NOT_RECEIVED = {"live": {"status": "exceeds_tolerance", "receipt_problem": "receipt_not_for_purchase_order",
                         "lines": [{"ordered_qty": 40000, "received_qty": 0, "billed_qty": 40000,
                                    "billed_to_date_qty": 40000}]}}


def run(make_ctx, ds, match, parties=()):
    return ThreeWayMatch().evaluate(ds(bills=[BILL], parties=list(parties), matches={"b18": match},
                                       match_failures=[]), make_ctx())


def test_billed_not_received_from_msme_vendor(make_ctx, ds):
    found = run(make_ctx, ds, NOT_RECEIVED, [{"id": "v", "is_msme": 1}])
    assert [f.rule for f in found] == ["billed_not_received"]
    assert found[0].details["cross_flags"] == ["uc04_msme_vendor"]
    assert found[0].details["action"] == "hold_payment"


def test_within_tolerance_is_quiet(make_ctx, ds):
    ok = {"live": {"status": "within_tolerance", "price_tolerance_pct": 2,
                   "lines": [{"ordered_qty": 2, "received_qty": 2, "billed_qty": 2, "billed_to_date_qty": 2,
                              "price_variance_pct": 0.5}]}}
    assert run(make_ctx, ds, ok) == []


def test_price_variance_beyond_tolerance(make_ctx, ds):
    priced = {"live": {"price_tolerance_pct": 2, "lines": [{"ordered_qty": 2, "received_qty": 2, "billed_qty": 2,
                                                            "billed_to_date_qty": 2, "price_variance_pct": 7}]}}
    assert [f.rule for f in run(make_ctx, ds, priced)] == ["price_variance"]


def test_no_receipt_basis_is_not_billed_not_received(make_ctx, ds):
    two_way = {"live": {"status": "within_tolerance", "price_tolerance_pct": 2,
                        "lines": [{"ordered_qty": 2, "received_qty": None, "billed_qty": 2,
                                   "billed_to_date_qty": 2, "price_variance_pct": 0}]}}
    assert run(make_ctx, ds, two_way) == []
