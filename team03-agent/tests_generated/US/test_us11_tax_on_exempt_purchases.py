"""LLM-generated, not graded. US-11 tax on exempt purchases."""

from datetime import date
from decimal import Decimal

from scripts.uc.US.us11_tax_on_exempt_purchases import TaxOnExemptPurchases


def bill(n, desc, tax):
    return {"id": n, "number": n, "status": "paid", "date": "2026-03-01", "vendor_id": "apex",
            "_vendor_id_display": "Apex Metals", "total_tax": tax, "taxes": [], "items": [{"description": desc, "amount": 12000}]}


def run(make_ctx, ds, bills, issued=()):
    return TaxOnExemptPurchases().evaluate(ds(bills=bills, expenses=[], issued=set(issued)),
                                           make_ctx(tenant="us", as_of=date(2026, 10, 4)))


def test_tax_on_production_material_and_no_certificate(make_ctx, ds):
    found = run(make_ctx, ds, [bill("b", "Steel sheet — production material", 780)])
    assert sorted(f.rule for f in found) == ["exemption_certificate_not_issued", "tax_paid_on_exempt_purchase"]
    assert next(f for f in found if f.rule == "tax_paid_on_exempt_purchase").total_exposure == Decimal("780.00")


def test_taxable_line_and_untaxed_bill_are_quiet(make_ctx, ds):
    assert run(make_ctx, ds, [bill("t", "Office cleaning", 50), bill("u", "production material", 0)]) == []
