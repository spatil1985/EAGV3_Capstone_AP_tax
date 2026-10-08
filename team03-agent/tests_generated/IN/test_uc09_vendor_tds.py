"""LLM-generated, not graded. UC-09 TDS checks (spec §5 worked example BILL-2026-00227)."""

from scripts.uc.IN.uc09_vendor_tds import VendorTdsVerification


def run(make_ctx, ds, bills, parties=()):
    return VendorTdsVerification().evaluate(ds(bills=bills, parties=list(parties)), make_ctx())


def test_phantom_tds_on_goods_bill(make_ctx, ds):
    bill = {"id": "b", "number": "BILL-2026-00227", "status": "open", "date": "2026-09-27",
            "items": [{"hsn_or_sac": "73269099", "taxable_amount": 8.55}], "tds_percentage": 5.0,
            "_suspect_tds_amount": 9178.58, "tds_section": None, "grand_total": -9170.0}
    found = run(make_ctx, ds, [bill])
    assert found[0].rule == "tds_exceeds_bill"
    assert set(found[0].details["also"]) == {"tds_arithmetic_wrong", "tds_on_goods", "tds_section_missing"}


def test_transport_bill_above_threshold_without_tds(make_ctx, ds):
    bill = {"id": "t", "number": "BILL-T", "status": "open", "date": "2026-09-10", "vendor_id": "v",
            "items": [{"hsn_or_sac": "996511", "taxable_amount": 40000}], "tds_percentage": 0}
    found = run(make_ctx, ds, [bill], [{"id": "v", "pan": "ABCPK1234L"}])
    assert [f.rule for f in found] == ["tds_not_deducted"]
    assert found[0].details["expected_tds_amount"] == "400.00"   # 194C individual 1%


def test_correct_tds_is_quiet(make_ctx, ds):
    bill = {"id": "ok", "number": "BILL-OK", "status": "open", "date": "2026-09-10", "vendor_id": "v",
            "items": [{"hsn_or_sac": "998211", "taxable_amount": 60000}], "tds_percentage": 10,
            "_suspect_tds_amount": 6000, "tds_section": "194J"}
    assert run(make_ctx, ds, [bill], [{"id": "v", "pan": "ABCFK1234L"}]) == []
