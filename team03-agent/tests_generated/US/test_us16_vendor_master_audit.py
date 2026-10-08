"""LLM-generated, not graded. US-16 vendor master (spec §8-9 fixtures)."""

from scripts.uc.US.us16_vendor_master_audit import VendorMasterAuditUS

BANKED = {"vendor_bank_account_number": "123", "addresses": [{"state": "OH"}], "contact_type": "vendor"}


def run(make_ctx, ds, party):
    pays = [{"vendor_id": party["id"], "status": "paid", "amount": 2500}]
    return VendorMasterAuditUS().evaluate(ds(parties=[party], bills=[], payments=pays, vendor_credits=[]),
                                          make_ctx(tenant="us"))


def test_corporation_with_ssn(make_ctx, ds):
    party = {"id": "c", "name": "Midwest Tool", "us_tax_classification": "c_corporation", "tin_type": "ssn",
             "_redacted_fields": ["tin"], **BANKED}
    assert run(make_ctx, ds, party)[0].rule == "tin_type_classification_conflict"


def test_sole_proprietor_without_w9_and_rents_box(make_ctx, ds):
    party = {"id": "h", "name": "Hartville Sign & Graphics", "us_tax_classification": "individual_sole_proprietor",
             "tin_type": "ssn", "is_1099_vendor": 1, "w9_on_file": 0, "form_1099_box": "MISC-1",
             "_redacted_fields": ["tin"], **BANKED}
    found = run(make_ctx, ds, party)[0]
    assert found.rule == "w9_missing" and "form_1099_box_conflict" in found.details["also"]
