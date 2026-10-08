"""LLM-generated, not graded. US-20 (spec §9 fixture) and threshold inference."""

from decimal import Decimal

from scripts.uc.US.us20_approval_threshold_splitting import ApprovalThresholdSplittingUS
from scripts.uc.common.threshold_split import infer_threshold


def bill(n, amount, **extra):
    return {"id": n, "number": n, "vendor_id": "v", "status": "open", "date": "2026-06-01", "grand_total": amount,
            "approval_status": "not_required", **extra}


def test_three_4000_bills_split_at_the_inferred_edge(make_ctx, ds):
    found = [f for f in ApprovalThresholdSplittingUS().evaluate(
        ds(bills=[bill("a", 4000), bill("b", 4000), bill("c", 4000)], purchase_orders=[], requests=[]),
        make_ctx(tenant="us")) if f.rule == "split_candidate"]
    assert len(found) == 1 and found[0].details["threshold"] == "10000.00"


def test_apex_standing_orders_are_not_splits(make_ctx, ds):
    bills = [bill(n, a) for n, a in (("1", 3288.20), ("2", 3437.94), ("3", 10626.36), ("4", 16739.38))]
    found = ApprovalThresholdSplittingUS().evaluate(ds(bills=bills, purchase_orders=[], requests=[]),
                                                    make_ctx(tenant="us"))
    assert [f.rule for f in found] == ["policy_unreadable"]


def test_edge_inferred_from_two_bands():
    reqs = [{"document_type": "Bill", "policy_id": "low", "document_amount": a} for a in (3075, 10000)] + \
           [{"document_type": "Bill", "policy_id": "high", "document_amount": a} for a in (10626, 16739)]
    edge, _ = infer_threshold(reqs, "Bill")
    assert edge == Decimal("10000.00")
