"""LLM-generated, not graded. UC-12 e-way bill coverage and expiry."""

from scripts.uc.IN.uc12_eway_bill import EWayBillAudit


def test_missing_eway_bill_above_threshold(make_ctx, ds):
    inv = {"id": "i1", "number": "INV-1", "status": "sent", "date": "2026-10-01",
           "grand_total": 75000, "items": [{"hsn_or_sac": "8466"}]}
    small = {**inv, "id": "i2", "grand_total": 40000}
    draft = {**inv, "id": "i3", "status": "draft"}
    found = EWayBillAudit().evaluate(ds(ewb=[], invoices=[inv, small, draft], challans=[]), make_ctx())
    assert [f.entity_id for f in found] == ["i1"]


def test_expired_and_not_real(make_ctx, ds):
    ewb = {"id": "e1", "number": "EWB-1", "status": "active", "eway_bill_number": None,
           "vehicle_number": "MH12", "generation_date": "2026-09-01", "expiry_date": "2026-09-02",
           "distance_km": 150, "total": 60000}
    found = EWayBillAudit().evaluate(ds(ewb=[ewb], invoices=[], challans=[]), make_ctx())
    assert {f.rule for f in found} == {"ewb_not_real", "ewb_expired_in_transit"}
