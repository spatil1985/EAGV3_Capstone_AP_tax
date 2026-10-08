"""LLM-generated, not graded. UC-32 Rule 89(4) refund (spec §5 worked example)."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc32_itc_refund import ItcRefund


def sale(n, value, treatment, tax=0, rate=18):
    return {"id": n, "number": n, "direction": "receivable", "status": "paid", "date": "2026-07-01",
            "taxable_value": value, "total_tax": tax, "gst_treatment": treatment,
            "taxes": [{"tax_type": "IGST", "amount": tax, "rate": rate}] if tax else []}


def bill(n, kind, tax):
    return {"id": n, "number": n, "status": "open", "date": "2026-07-01", "itc_eligibility": kind, "ims_status": "accept",
            "total_tax": tax, "taxes": [{"tax_type": "IGST", "amount": tax}], "items": [{"tax_percentage": 18}]}


def test_zero_rated_refund_formula(make_ctx, ds):
    data = ds(invoices=[sale("s", 1305145.88, "sez"), sale("d", 63165471.14, "business_gst", tax=1000)],
              bills=[bill("i", "input", 1858462.59), bill("x", "input_services", 6724.43),
                     bill("c", "capital_goods", 15913.60)],
              exemptions=[{"id": "l", "exemption_reason": "Export under LUT"}])
    found = ItcRefund().evaluate(data, make_ctx(as_of=date(2026, 10, 4)))
    zr = next(f for f in found if f.rule == "refund_eligible_zero_rated")
    assert zr.total_exposure == Decimal("37758.92")
    assert "lut_unverified" in {f.rule for f in found}
    assert "refund_eligible_inverted" not in {f.rule for f in found}
