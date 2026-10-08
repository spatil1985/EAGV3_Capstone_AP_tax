"""LLM-generated, not graded. US-04 exemption certificates."""

from datetime import date
from decimal import Decimal

from scripts.uc.US.us04_exemption_certificates import ExemptionCertificateCoverage

CERT = {"id": "c", "certificate_number": "OH-ST1-2025-0447", "party_id": "tri", "state_code": "OH", "status": "active",
        "issue_date": "2025-04-02", "expiry_date": "2029-04-01", "certificate_file": None}


def inv(n, party, when="2026-06-20"):
    return {"id": n, "number": n, "status": "paid", "date": when, "party_id": party, "net_total": 10000,
            "taxes": [{"is_exempt": True, "state_code": "OH", "tax_type": "Sales tax — exempt (resale certificate)"}]}


def run(make_ctx, ds, invoices):
    data = ds(invoices=invoices, certificates=[CERT],
              jurisdictions=[{"state_code": "OH", "rate_percentage": 5.75}, {"state_code": "OH", "rate_percentage": 0.75}])
    return ExemptionCertificateCoverage().evaluate(data, make_ctx(tenant="us", as_of=date(2026, 10, 3)))


def test_covered_sale_only_flags_missing_file(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [inv("a", "tri")])] == ["certificate_unsupported"]


def test_uncovered_customer_and_pre_issue_date(make_ctx, ds):
    found = [f for f in run(make_ctx, ds, [inv("b", "other"), inv("c", "tri", when="2025-01-01")])
             if f.rule == "exemption_without_certificate"]
    assert {f.entity_id for f in found} == {"b", "c"}
    assert found[0].total_exposure == Decimal("650.00")
