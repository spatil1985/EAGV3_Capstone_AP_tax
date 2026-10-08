"""LLM-generated, not graded. UC-21 import of services (spec §5 worked example BILL-2026-00090)."""

from decimal import Decimal

from scripts.uc.IN.uc21_import_of_services_rcm import ImportOfServicesRcm

INDIAN = {"id": "bosch", "gst_treatment": "business_gst", "gst_no": "27AAACB1234C1Z5"}
FOREIGN = {"id": "aws", "gst_treatment": "overseas", "gst_no": None}


def bill(vendor, **extra):
    base = {"id": "b", "number": "BILL-X", "vendor_id": vendor, "status": "open", "gst_treatment": "overseas",
            "currency_code": "INR", "is_reverse_charge": 0, "total_tax": 0, "taxes": [],
            "items": [{"hsn_or_sac": "998315", "taxable_amount": 10000}]}
    return {**base, **extra}


def run(make_ctx, ds, bills):
    return ImportOfServicesRcm().evaluate(ds(bills=bills, parties=[INDIAN, FOREIGN], items=[]), make_ctx())


def test_tag_only_is_a_classification_conflict(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [bill("bosch", is_reverse_charge=1)])] == ["classification_conflict"]


def test_genuine_import_without_rcm_owes_igst(make_ctx, ds):
    found = run(make_ctx, ds, [bill("aws", currency_code="USD")])
    assert [f.rule for f in found] == ["rcm_import_of_services"]
    assert found[0].total_exposure == Decimal("1800.00")


def test_imported_goods_are_customs_not_rcm(make_ctx, ds):
    goods = bill("aws", currency_code="USD", items=[{"hsn_or_sac": "82055900", "taxable_amount": 10000}])
    assert run(make_ctx, ds, [goods]) == []
