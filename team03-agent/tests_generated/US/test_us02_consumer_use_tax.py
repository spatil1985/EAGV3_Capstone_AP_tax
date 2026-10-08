"""LLM-generated, not graded. US-02 use tax."""

from datetime import date
from decimal import Decimal

from scripts.uc.US.us02_consumer_use_tax import ConsumerUseTax

JURIS = [{"name": "Ohio State Sales Tax", "state_code": "OH", "rate_percentage": 5.75},
         {"name": "Stark County (OH)", "state_code": "OH", "rate_percentage": 0.75},
         {"name": "Michigan State Sales Tax", "state_code": "MI", "rate_percentage": 6}]


def bill(n, desc, amount):
    return {"id": n, "number": n, "status": "paid", "date": "2026-05-01", "currency_code": "USD", "total_tax": 0,
            "taxes": [], "net_total": amount, "items": [{"description": desc, "amount": amount}]}


def run(make_ctx, ds, bills):
    data = ds(bills=bills, jurisdictions=JURIS, org=[{"state": "OH"}])
    return ConsumerUseTax().evaluate(data, make_ctx(tenant="us", as_of=date(2026, 10, 3)))


def test_janitorial_owes_use_tax_production_material_does_not(make_ctx, ds):
    found = run(make_ctx, ds, [bill("j", "Daily housekeeping — Mon-Sat", 1000),
                               bill("p", "Hot-Rolled Steel Sheet — production material", 5000)])
    assert [(f.entity_id, f.rule) for f in found] == [("j", "use_tax_due")]
    assert found[0].total_exposure == Decimal("65.00")


def test_unclassified_is_a_range(make_ctx, ds):
    found = run(make_ctx, ds, [bill("t", "Perishable tooling and abrasives", 10000)])
    assert [f.rule for f in found] == ["use_tax_unclassified"]
    assert found[0].total_exposure == Decimal("650.00")
