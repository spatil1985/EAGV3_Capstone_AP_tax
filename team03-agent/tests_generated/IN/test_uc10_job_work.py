"""LLM-generated, not graded. UC-10 job-work deadline (spec §5 worked example)."""

from datetime import date

from scripts.uc.IN.uc10_job_work import JobWorkItc04


def challan(**extra):
    base = {"id": "dc", "number": "DC-2026-00084", "challan_type": "job_work", "status": "delivered",
            "date": "2025-08-04", "customer_id": "jw", "_customer_id_display": "Supriya Rathi",
            "net_total": 1000, "items": [{"item_id": "it"}]}
    return {**base, **extra}


ITEM = {"id": "it", "intra_state_tax_rate": 18}


def run(make_ctx, ds, challans, bills=(), as_of=date(2026, 9, 28)):
    return JobWorkItc04().evaluate(ds(challans=challans, bills=list(bills), items=[ITEM]), make_ctx(as_of=as_of))


def test_draft_challan_has_no_clock(make_ctx, ds):
    assert run(make_ctx, ds, [challan(status="draft")]) == []


def test_over_a_year_is_a_deemed_supply(make_ctx, ds):
    found = run(make_ctx, ds, [challan()])
    assert [f.rule for f in found] == ["s143_deemed_supply"]
    assert found[0].details["estimated_tax"] == "180.00"


def test_a_later_bill_for_the_same_item_counts_as_returned(make_ctx, ds):
    back = {"vendor_id": "jw", "date": "2025-10-01", "items": [{"item_id": "it"}]}
    assert run(make_ctx, ds, [challan()], [back]) == []


def test_due_soon_window(make_ctx, ds):
    found = run(make_ctx, ds, [challan(date="2025-10-15")])
    assert [f.rule for f in found] == ["s143_due_soon"]
