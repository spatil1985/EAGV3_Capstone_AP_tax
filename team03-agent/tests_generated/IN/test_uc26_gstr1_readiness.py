"""LLM-generated, not graded. UC-26 GSTR-1 readiness (spec §5 worked example INV-2026-00179)."""

from datetime import date

from scripts.uc.IN.uc26_gstr1_readiness import Gstr1ReadinessAudit

ORG = [{"gstin": "27AASCS7781M1ZQ"}]


def inv(n, pos, heads, **extra):
    return {"id": n, "number": n, "direction": "receivable", "status": "sent", "date": "2026-08-25",
            "gst_treatment": "business_gst", "gst_no": "24ABCDE1234F1Z5", "place_of_supply": pos,
            "taxable_value": 47996, "total_tax": sum(heads.values()),
            "taxes": [{"tax_type": h.upper(), "amount": a} for h, a in heads.items()],
            "items": [{"hsn_or_sac": "73269099"}], **extra}


def run(make_ctx, ds, invoices):
    return Gstr1ReadinessAudit().evaluate(ds(invoices=invoices, parties=[], org=ORG, returns=[]),
                                          make_ctx(as_of=date(2026, 10, 4)))


def test_inter_state_charged_cgst_sgst(make_ctx, ds):
    found = run(make_ctx, ds, [inv("INV-2026-00179", "24", {"cgst": 4319.64, "sgst": 4319.64})])
    assert [f.rule for f in found] == ["wrong_tax_head_for_pos"]
    assert str(found[0].total_exposure) == "8639.28"


def test_intra_state_igst_and_missing_gstin_and_short_hsn(make_ctx, ds):
    bad = inv("I2", "27", {"igst": 100}, gst_no=None, items=[{"hsn_or_sac": "7326"}])
    assert sorted(f.rule for f in run(make_ctx, ds, [bad])) == [
        "b2b_without_gstin", "hsn_digits_short", "wrong_tax_head_for_pos"]


def test_correct_invoice_is_quiet(make_ctx, ds):
    assert run(make_ctx, ds, [inv("ok", "24", {"igst": 8639.28})]) == []
