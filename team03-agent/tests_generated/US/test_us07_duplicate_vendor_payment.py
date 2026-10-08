"""LLM-generated, not graded. US-07: standing orders are not duplicates (spec §6, §9)."""

from scripts.uc.US.us07_duplicate_vendor_payment import DuplicateVendorPaymentUS

LINES = [{"_item_id_display": "Hot-Rolled Steel Sheet", "qty": 1, "rate": 16739.38}]


def bill(bid, when, po):
    return {"id": bid, "number": bid, "vendor_id": "apex", "status": "paid", "date": when, "grand_total": 16739.38,
            "balance_due": 0, "amount_paid": 16739.38, "items": LINES, "purchase_order_id": po,
            "created_at": f"{when}T10:00:00"}


def run(make_ctx, ds, bills):
    return DuplicateVendorPaymentUS().evaluate(ds(bills=bills, parties=[], payments=[], matches={}, match_failures=[]),
                                               make_ctx(tenant="us"))


def test_fortnightly_standing_orders_are_not_flagged(make_ctx, ds):
    bills = [bill("a", "2026-01-26", "p1"), bill("b", "2026-02-11", "p2"), bill("c", "2026-02-27", "p3")]
    assert run(make_ctx, ds, bills) == []


def test_two_paid_identical_bills_two_days_apart_are_a_recovery(make_ctx, ds):
    found = run(make_ctx, ds, [bill("a", "2026-03-01", "p1"), bill("b", "2026-03-03", "p1")])
    assert found[0].details["action"] == "recover"
