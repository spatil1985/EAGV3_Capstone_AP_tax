"""LLM-generated, not graded. UC-40 vendor master."""

from scripts.uc.IN.uc40_vendor_master_audit import VendorMasterAudit, gstin_checksum_ok


def run(make_ctx, ds, parties, bills):
    return VendorMasterAudit().evaluate(ds(parties=parties, bills=bills, payments=[], vendor_credits=[]), make_ctx())


def test_gstin_checksum():
    assert gstin_checksum_ok("27AAPFU0939F1ZV")          # a published example GSTIN
    assert not gstin_checksum_ok("27AAPFU0939F1ZA")


def test_registered_vendor_without_gstin_or_pan(make_ctx, ds):
    party = {"id": "v", "name": "Bosch Rexroth India", "contact_type": "customer", "gst_treatment": "business_gst",
             "addresses": [{"state": "Maharashtra"}]}
    found = run(make_ctx, ds, [party], [{"vendor_id": "v", "status": "open", "grand_total": 1000}])
    assert found[0].rule == "vendor_gstin_missing"
    assert {"vendor_pan_missing", "vendor_bank_missing", "vendor_type_conflict"} <= set(found[0].details["also"])


def test_unused_party_is_ignored(make_ctx, ds):
    assert run(make_ctx, ds, [{"id": "x", "name": "Idle"}], []) == []
