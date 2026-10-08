"""LLM-generated, not graded. US-09: N2 regression guard."""

from scripts.uc.US.us09_three_way_match import ThreeWayMatchUS

BILL = {"id": "b81", "number": "BILL-2026-00081", "status": "paid", "purchase_order_id": "po", "grand_total": 6750}
LIVE = {"status": "within_tolerance", "price_tolerance_pct": 2,
        "lines": [{"ordered_qty": 1, "received_qty": None, "billed_qty": 1, "billed_to_date_qty": 1}]}


def run(make_ctx, ds, recorded):
    match = {"live": LIVE, "recorded_status": recorded}
    return ThreeWayMatchUS().evaluate(ds(bills=[BILL], parties=[], matches={"b81": match}, match_failures=[]),
                                      make_ctx(tenant="us"))


def test_recorded_status_agrees(make_ctx, ds):
    assert run(make_ctx, ds, "within_tolerance") == []


def test_stale_recorded_status_is_flagged(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, None)] == ["stored_value_mismatch"]
