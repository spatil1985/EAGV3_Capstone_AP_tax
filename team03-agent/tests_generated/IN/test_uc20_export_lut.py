"""LLM-generated, not graded. UC-20 zero-rating and LUT (spec §5 worked example INV-2026-00126)."""

from scripts.uc.IN.uc20_export_lut import ExportLutTracking

SEZ = {"id": "s", "number": "INV-2026-00126", "direction": "receivable", "gst_treatment": "sez", "status": "sent",
       "date": "2026-09-10", "place_of_supply": "29", "currency_code": "INR", "total_tax": 0, "taxes": [],
       "items": [], "grand_total": 358087, "_party_id_display": "Vardhman Aerospace SEZ Unit"}
LUT_ROW = {"id": "l", "exemption_reason": "SEZ supply — Letter of Undertaking, no IGST"}


def run(make_ctx, ds, invoices, exemptions):
    return ExportLutTracking().evaluate(ds(invoices=invoices, exemptions=exemptions), make_ctx())


def test_sez_in_inr_under_undated_lut(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [SEZ], [LUT_ROW])] == ["lut_validity_unknown"]


def test_no_lut_record_at_all(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [SEZ], [])] == ["lut_missing"]


def test_export_invoiced_in_inr_with_indian_place_of_supply(make_ctx, ds):
    export = {**SEZ, "id": "e", "number": "INV-E", "gst_treatment": "overseas"}
    rules = sorted(f.rule for f in run(make_ctx, ds, [export], [LUT_ROW]))
    assert rules == ["export_condition_failed", "lut_validity_unknown"]
