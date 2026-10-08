"""LLM-generated, not graded. UC-03 reverse charge (spec §5 worked example, §11 corrections)."""

from decimal import Decimal

from scripts.uc.IN.uc03_rcm_self_invoicing import RcmSelfInvoicing


def gta_bill(**extra):
    base = {"id": "b1", "bill_number": "BILL-2026-00312", "_vendor_id_display": "Sri Balaji Road Carriers",
            "vendor_id": "v1", "status": "open", "is_reverse_charge": 0, "total_tax": 0, "taxes": [],
            "items": [{"hsn_or_sac": "996511", "taxable_amount": 40000}]}
    return {**base, **extra}


def run(make_ctx, ds, bills, parties=()):
    return RcmSelfInvoicing().evaluate(ds(bills=bills, parties=list(parties)), make_ctx())


def test_untaxed_gta_without_rcm_flag_owes_5pct(make_ctx, ds):
    found = run(make_ctx, ds, [gta_bill()])
    assert [f.rule for f in found] == ["rcm_undeclared_liability"]
    assert found[0].total_exposure == Decimal("2000.00")


def test_gta_that_charged_gst_is_forward_charge(make_ctx, ds):
    taxed = gta_bill(total_tax=7200, taxes=[{"tax_type": "CGST", "amount": 3600},
                                            {"tax_type": "SGST", "amount": 3600}])
    assert run(make_ctx, ds, [taxed]) == []


def test_rcm_flag_on_goods_is_spurious_but_import_of_services_is_not(make_ctx, ds):
    goods = gta_bill(id="g", is_reverse_charge=1, items=[{"hsn_or_sac": "82055900", "taxable_amount": 100}])
    imported = gta_bill(id="s", is_reverse_charge=1, gst_treatment="overseas",
                        items=[{"hsn_or_sac": "998314", "taxable_amount": 100}])
    found = run(make_ctx, ds, [goods, imported])
    assert [(f.rule, f.entity_id) for f in found] == [("rcm_flag_spurious", "g")]
