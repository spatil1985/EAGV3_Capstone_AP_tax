"""LLM-generated, not graded. UC-33 expense credit."""

from scripts.uc.IN.uc33_expense_claims_itc import ExpenseClaimsItc


def exp(eid, **extra):
    base = {"id": eid, "number": eid, "status": "unbilled", "date": "2026-09-10", "amount": 10000, "tax_amount": 1800,
            "itc_eligibility": "input", "gst_no": "27AAAAA0000A1Z5", "_account_id_display": "Office Supplies"}
    return {**base, **extra}


def run(make_ctx, ds, expenses):
    return ExpenseClaimsItc().evaluate(ds(expenses=expenses, parties=[]), make_ctx())


def test_personal_claim_leads_and_lists_the_rest(make_ctx, ds):
    found = run(make_ctx, ds, [exp("p", is_personal=1, gst_no=None)])
    assert found[0].rule == "itc_on_personal_expense"
    assert found[0].details["also"] == ["itc_without_supplier_gstin"]


def test_gst_on_salary_and_implausible_tax(make_ctx, ds):
    found = run(make_ctx, ds, [exp("s", _account_id_display="Salaries & Wages", itc_eligibility="ineligible"),
                               exp("x", amount=2183.09, tax_amount=75456.61)])
    rules = {f.entity_id: f.rule for f in found}
    assert rules == {"s": "gst_on_non_supply", "x": "tax_exceeds_possible_rate"}


def test_clean_expense_is_quiet(make_ctx, ds):
    assert run(make_ctx, ds, [exp("ok")]) == []
