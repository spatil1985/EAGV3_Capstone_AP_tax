"""LLM-generated, not graded. UC-35 recharges (spec §5 constructed continuation)."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc35_pure_agent_recharges import PureAgentRecharges

EXP = {"id": "e", "number": "EXP-1", "date": "2026-09-01", "amount": 50000, "tax_amount": 0, "is_billable": 1,
       "status": "invoiced", "customer_id": "c", "itc_eligibility": "ineligible"}


def run(make_ctx, ds, expenses, invoices=(), contracts=()):
    return PureAgentRecharges().evaluate(ds(expenses=expenses, invoices=list(invoices), pure_agent=set(contracts)),
                                         make_ctx(as_of=date(2026, 10, 4)))


def test_unlinked_recharge(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [EXP])] == ["recharge_unlinked"]


def test_media_cost_rebilled_without_clause_owes_18pct(make_ctx, ds):
    inv = {"id": "i", "number": "INV-1", "status": "sent", "date": "2026-09-05", "party_id": "c", "expense_id": "e",
           "items": [{"amount": 50000}, {"amount": 100000}]}
    found = run(make_ctx, ds, [EXP], [inv])
    assert [f.rule for f in found] == ["reimbursement_undertaxed"]
    assert found[0].total_exposure == Decimal("9000.00")


def test_true_pure_agent_is_quiet(make_ctx, ds):
    inv = {"id": "i", "number": "INV-1", "status": "sent", "date": "2026-09-05", "party_id": "c", "expense_id": "e",
           "items": [{"amount": 50000}, {"amount": 100000}]}
    assert run(make_ctx, ds, [EXP], [inv], contracts=["c"]) == []
