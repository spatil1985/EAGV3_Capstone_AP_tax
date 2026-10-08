"""LLM-generated, not graded. UC-07 school split (spec §5 worked example)."""

from datetime import date

from scripts.uc.IN.uc07_school_exempt_split import SchoolExemptSplit

WRENCH = {"id": "w", "name": "Pipe Wrench 138mm", "hsn_or_sac": "82055900", "product_type": "services",
          "tax_preference": "tax_exempt", "taxable": 0, "tax_exemption_reason": None}
TUITION = {"id": "t", "name": "Tuition fee term 1", "hsn_or_sac": "999210", "product_type": "services",
           "tax_preference": "taxable", "taxable": 1}


def run(make_ctx, ds, items, invoices=()):
    return SchoolExemptSplit().evaluate(ds(items=items, invoices=list(invoices)),
                                        make_ctx(as_of=date(2026, 9, 28), vertical="school"))


def test_item_master_conflicts(make_ctx, ds):
    found = run(make_ctx, ds, [WRENCH])
    assert [f.rule for f in found] == ["classification_conflict"]
    assert len(found[0].details["problems"]) == 2


def test_tuition_marked_taxable_breaks_school_rules(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [TUITION])] == ["stream_treatment_mismatch"]


def test_exempt_item_charged_gst(make_ctx, ds):
    inv = {"id": "i", "number": "INV-2026-00254", "direction": "receivable", "status": "sent",
           "date": "2026-09-22", "total_tax": 900, "taxes": [],
           "items": [{"item_id": "w", "taxable_amount": 10000, "tax_percentage": 9,
                      "igst_amount": 900}]}
    rules = [f.rule for f in run(make_ctx, ds, [{**WRENCH, "product_type": "goods",
                                                 "tax_exemption_reason": "x"}], [inv])]
    assert rules == ["exempt_but_taxed"]
