"""LLM-generated, not graded. UC-14 clinic split (spec §5 worked example)."""

from datetime import date

from scripts.uc.IN.uc14_clinic_exempt_split import ClinicExemptSplit

ROOM = {"id": "r", "name": "Deluxe Ward", "hsn_or_sac": "999311", "product_type": "services",
        "tax_preference": "taxable", "taxable": 1}
CONSULT = {"id": "c", "name": "Consultation", "hsn_or_sac": "999312", "product_type": "services",
           "tax_preference": "taxable", "taxable": 1}


def run(make_ctx, ds, items, invoices=()):
    return ClinicExemptSplit().evaluate(ds(items=items, invoices=list(invoices)),
                                        make_ctx(as_of=date(2026, 9, 28), vertical="clinic"))


def test_consultation_marked_taxable_breaks_entry_74(make_ctx, ds):
    rules = [f.rule for f in run(make_ctx, ds, [CONSULT])]
    assert rules == ["stream_treatment_mismatch"]


def test_room_above_5000_per_day_untaxed(make_ctx, ds):
    inv = {"id": "i", "number": "INV-1", "direction": "receivable", "status": "sent", "date": "2026-09-20",
           "total_tax": 0, "taxes": [],
           "items": [{"item_id": "r", "description": "Deluxe Ward", "qty": 3, "rate": 6500, "taxable_amount": 19500}]}
    found = run(make_ctx, ds, [ROOM], [inv])
    room = [f for f in found if f.rule == "room_rent_tax_wrong"]
    assert len(room) == 1 and room[0].details["expected_tax"] == "975.00"
