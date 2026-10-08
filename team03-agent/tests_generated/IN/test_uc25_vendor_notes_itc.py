"""LLM-generated, not graded. UC-25 vendor credits."""

from scripts.uc.IN.uc25_vendor_notes_itc import VendorNotesItc


def vc(vid, treatment, **extra):
    return {"id": vid, "number": vid, "status": "open", "date": "2026-08-10", "gst_treatment": treatment,
            "is_reverse_charge": 0, "reference_number": "BILL-1", "total_tax": 100,
            "taxes": [{"tax_type": "CGST", "amount": 50}, {"tax_type": "SGST", "amount": 50}], **extra}


def run(make_ctx, ds, vcs, credit_notes=(), invoices=()):
    return VendorNotesItc().evaluate(ds(vendor_credits=vcs, bills=[{"number": "BILL-1"}],
                                        credit_notes=list(credit_notes), invoices=list(invoices)), make_ctx())


def test_registered_rcm_and_impossible(make_ctx, ds):
    found = run(make_ctx, ds, [vc("A", "business_gst"), vc("B", "business_gst", is_reverse_charge=1),
                               vc("C", "unregistered_business"), vc("D", "business_gst", status="draft")])
    assert sorted((f.entity_id, f.rule) for f in found) == [
        ("A", "itc_reduction_due"), ("B", "rcm_liability_reduction"), ("C", "credit_tax_impossible")]


def test_unlinked_and_product_named_rows(make_ctx, ds):
    v = vc("E", "sez", reference_number=None, _suspect_taxes=[{"tax_type": "Feeler Gauge Set 10337"}])
    rules = sorted(f.rule for f in run(make_ctx, ds, [v]))
    assert rules == ["credit_unlinked", "itc_reduction_due", "stored_value_mismatch"]


def test_misfiled_outward_credit_note(make_ctx, ds):
    found = run(make_ctx, ds, [], [{"id": "cn", "number": "CN-1", "invoice_id": "p", "status": "open"}],
                [{"id": "p", "number": "PINV-1", "direction": "payable"}])
    assert [f.rule for f in found] == ["misfiled_vendor_credit"]
