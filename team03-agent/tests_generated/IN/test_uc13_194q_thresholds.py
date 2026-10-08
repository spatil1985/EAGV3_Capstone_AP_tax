"""LLM-generated, not graded. UC-13 194Q buy and sell side."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc13_194q_thresholds import Thresholds194Q

AS_OF = date(2026, 9, 28)


def doc(did, when, value, **extra):
    return {"id": did, "number": did, "date": when, "status": "open",
            "items": [{"hsn_or_sac": "72283090", "taxable_amount": value}], **extra}


def run(make_ctx, ds, bills=(), invoices=(), receipts=()):
    return Thresholds194Q().evaluate(ds(bills=list(bills), invoices=list(invoices), receipts=list(receipts)),
                                     make_ctx(as_of=AS_OF))


def test_crossing_bill_owes_tds_on_the_excess_only(make_ctx, ds):
    bills = [doc("b1", "2026-05-01", 4000000, vendor_id="v"), doc("b2", "2026-06-01", 2000000, vendor_id="v")]
    found = run(make_ctx, ds, bills=bills)
    assert [f.rule for f in found] == ["194q_not_deducted"]
    assert found[0].total_exposure == Decimal("1000.00")     # 0.1% of 10 lakh over the line


def test_approaching_at_eighty_percent(make_ctx, ds):
    found = run(make_ctx, ds, bills=[doc("b1", "2026-05-01", 4500000, vendor_id="v")])
    assert [f.rule for f in found] == ["194q_approaching"]


def test_services_and_last_fy_do_not_count(make_ctx, ds):
    svc = doc("s", "2026-05-01", 6000000, vendor_id="v")
    svc["items"][0]["hsn_or_sac"] = "998873"
    old = doc("o", "2026-03-01", 6000000, vendor_id="v")
    assert run(make_ctx, ds, bills=[svc, old]) == []


def test_customer_past_the_line_without_tds_on_receipts(make_ctx, ds):
    inv = doc("i1", "2026-07-01", 7000000, party_id="c", direction="receivable")
    found = run(make_ctx, ds, invoices=[inv], receipts=[{"customer_id": "c", "date": "2026-08-01",
                                                         "withholding_tax_amount": 0}])
    assert [f.rule for f in found] == ["194q_customer_not_deducting"]
    assert found[0].details["expected_tds"] == "2000.00"
