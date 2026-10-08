"""LLM-generated, not graded. UC-22 advances (spec §5 worked example RET-2026-00002)."""

from decimal import Decimal

from scripts.uc.IN.uc22_advance_receipt_gst import AdvanceReceiptGst

RET = {"id": "r", "number": "RET-2026-00002", "customer_id": "c", "date": "2026-08-25", "amount": 1200000,
       "payment_made": 600000, "amount_applied": 0, "status": "paid"}


def run(make_ctx, ds, parties, retainers=(RET,), invoices=(), items=()):
    return AdvanceReceiptGst().evaluate(ds(retainers=list(retainers), receipts=[], parties=parties,
                                           invoices=list(invoices), items=list(items)), make_ctx())


def test_sez_advance_is_zero_rated_with_services_fallback(make_ctx, ds):
    found = run(make_ctx, ds, [{"id": "c", "name": "Vardhman Aerospace SEZ Unit", "gst_treatment": "sez"}])
    assert [f.rule for f in found] == ["advance_gst_zero_rated"]
    assert found[0].details["tax_if_services"] == "91525.42"


def test_domestic_goods_customer_has_no_exposure(make_ctx, ds):
    inv = {"party_id": "c", "items": [{"item_id": "g"}]}
    found = run(make_ctx, ds, [{"id": "c", "gst_treatment": "business_gst"}], invoices=[inv],
                items=[{"id": "g", "product_type": "goods"}])
    assert found[0].rule == "advance_gst_unverifiable" and found[0].total_exposure == Decimal("0.00")


def test_fully_applied_advance_is_quiet(make_ctx, ds):
    assert run(make_ctx, ds, [], retainers=[{**RET, "amount_applied": 600000}]) == []
