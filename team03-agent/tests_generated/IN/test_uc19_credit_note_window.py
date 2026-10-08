"""LLM-generated, not graded. UC-19 credit-note window (spec §5 worked example)."""

from datetime import date

from scripts.uc.IN.uc19_credit_note_window import CreditNoteTimeLimit

AS_OF = date(2026, 9, 28)


def inv(iid, when, direction="receivable"):
    return {"id": iid, "number": iid, "date": when, "direction": direction, "status": "paid", "grand_total": 100}


def cn(cid, when, invoice_id):
    return {"id": cid, "number": cid, "date": when, "invoice_id": invoice_id, "status": "open", "total_tax": 18}


def run(make_ctx, ds, cns, invoices):
    return CreditNoteTimeLimit().evaluate(ds(credit_notes=cns, invoices=invoices), make_ctx(as_of=AS_OF))


def test_fy_2025_26_window_has_63_days_left(make_ctx, ds):
    found = run(make_ctx, ds, [cn("CN-23", "2026-09-12", "INV-9")], [inv("INV-9", "2026-01-13")])
    closing = [f for f in found if f.rule == "window_closing"]
    assert len(closing) == 1 and closing[0].details["days_left"] == 63
    assert closing[0].details["cutoff"] == "2026-11-30"
    assert not [f for f in found if f.rule == "credit_note_out_of_window"]


def test_late_credit_note_and_payable_link(make_ctx, ds):
    found = run(make_ctx, ds, [cn("late", "2025-12-05", "old"), cn("pinv", "2026-09-12", "P1")],
                [inv("old", "2024-06-01"), inv("P1", "2026-01-01", "payable")])
    rules = sorted(f.rule for f in found)
    assert "credit_note_out_of_window" in rules and "classification_conflict" in rules
