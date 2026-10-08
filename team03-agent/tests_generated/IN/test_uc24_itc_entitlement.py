"""LLM-generated, not graded. UC-24 ITC entitlement."""

from datetime import date

from scripts.uc.IN.uc24_itc_entitlement import ItcEntitlementAudit


def bill(bid, ims, when="2026-09-12", **extra):
    return {"id": bid, "number": bid, "status": "open", "itc_eligibility": "input", "date": when, "ims_status": ims,
            "vendor_id": "v", "gst_no": "27AAAAA0000A1Z5", "total_tax": 180,
            "taxes": [{"tax_type": "IGST", "amount": 180}], **extra}


def run(make_ctx, ds, bills, as_of=date(2026, 10, 4), returns=()):
    return ItcEntitlementAudit().evaluate(ds(bills=bills, parties=[], returns=list(returns)), make_ctx(as_of=as_of))


def test_rejected_but_eligible_and_pending_before_2b(make_ctx, ds):
    found = run(make_ctx, ds, [bill("R", "reject"), bill("P", "pending")])
    assert sorted(f.rule for f in found) == ["itc_awaiting_ims_action", "itc_on_rejected_document"]
    pend = next(f for f in found if f.rule == "itc_awaiting_ims_action")
    assert pend.details["gstr2b_on"] == "2026-10-14"


def test_pending_after_2b_is_deemed_accepted(make_ctx, ds):
    assert run(make_ctx, ds, [bill("P", "pending")], as_of=date(2026, 10, 20)) == []


def test_lapsing_and_no_gstin(make_ctx, ds):
    old = bill("O", "accept", when="2025-12-01", gst_no=None)
    found = run(make_ctx, ds, [old], as_of=date(2026, 10, 1))
    assert sorted(f.rule for f in found) == ["itc_lapsing", "itc_supplier_not_identified"]
