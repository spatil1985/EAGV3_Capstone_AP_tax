"""LLM-generated, not graded. UC-37 non-resident payments."""

from decimal import Decimal

from scripts.uc.IN.uc37_nonresident_payments import NonResidentPayments

US_VENDOR = {"id": "us", "name": "Design LLC", "addresses": [{"country": "United States"}]}
IN_VENDOR = {"id": "in", "name": "Bosch Rexroth India", "addresses": [{"country": "India"}]}


def bill(vendor, **extra):
    return {"id": f"b-{vendor}", "number": f"BILL-{vendor}", "vendor_id": vendor, "status": "open",
            "date": "2026-09-01", "currency_code": "USD", "grand_total": 504000,
            "items": [{"hsn_or_sac": "998391", "taxable_amount": 504000}], **extra}


def run(make_ctx, ds, bills, docs=None):
    return NonResidentPayments().evaluate(ds(bills=bills, parties=[US_VENDOR, IN_VENDOR], docs=docs or {}),
                                          make_ctx())


def test_foreign_designer_without_tds_and_paperwork(make_ctx, ds):
    found = {f.rule: f for f in run(make_ctx, ds, [bill("us")])}
    assert found["tds_195_not_deducted"].total_exposure == Decimal("104832.00")
    assert found["form_15ca_cb_missing"].details["needs_15cb"] is True


def test_overseas_tag_on_indian_vendor(make_ctx, ds):
    found = run(make_ctx, ds, [bill("in", currency_code="INR", gst_treatment="overseas")])
    assert [f.rule for f in found] == ["overseas_tag_on_resident"]
