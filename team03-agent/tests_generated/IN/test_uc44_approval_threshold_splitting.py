"""LLM-generated, not graded. UC-44 threshold splitting (spec §5 worked example, Suvarna Electricals)."""

from scripts.uc.IN.uc44_approval_threshold_splitting import ApprovalThresholdSplitting


def bill(n, amount, **extra):
    return {"id": n, "number": n, "vendor_id": "s", "_vendor_id_display": "Suvarna Electricals", "status": "open",
            "date": "2026-09-12", "grand_total": amount, "approval_status": "not_required", "created_by": "u1",
            "created_at": f"2026-09-12T17:19:{n[-1]}0", **extra}


def run(make_ctx, ds, bills):
    found = ApprovalThresholdSplitting().evaluate(ds(bills=bills, purchase_orders=[]), make_ctx())
    return [f for f in found if f.rule == "split_candidate"]


def test_four_bills_under_the_limit_together_over_it(make_ctx, ds):
    found = run(make_ctx, ds, [bill("b1", 40120), bill("b2", 36108), bill("b3", 40120), bill("b4", 36108)])
    assert len(found) == 1 and found[0].details["sum"] == "152456.00"
    assert found[0].details["strength"] == "high"


def test_approved_or_large_or_recurring_groups_are_not_splits(make_ctx, ds):
    assert run(make_ctx, ds, [bill("b1", 60000), bill("b2", 60000, approval_status="approved")]) == []
    assert run(make_ctx, ds, [bill("b1", 160000), bill("b2", 60000)]) == []
    assert run(make_ctx, ds, [bill("b1", 60000, recurring_bill_id="r"), bill("b2", 60000, recurring_bill_id="r")]) == []
