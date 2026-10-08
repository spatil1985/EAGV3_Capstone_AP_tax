"""LLM-generated, not graded. US-05 sourcing (spec §5 worked example INV-2026-00148)."""

from scripts.uc.US.us05_sourcing_and_rate import SourcingAndRate

JURIS = [{"id": "oh", "name": "Ohio State Sales Tax", "state_code": "OH", "rate_percentage": 5.75,
          "jurisdiction_level": "state", "sourcing": "destination"},
         {"id": "stark", "name": "Stark County (OH)", "county": "Stark County", "state_code": "OH",
          "rate_percentage": 0.75, "jurisdiction_level": "county", "sourcing": "destination"}]


def inv(n, party, net, rows):
    return {"id": n, "number": n, "status": "paid", "party_id": party, "net_total": net, "taxes": rows}


def rows(net):
    return [{"jurisdiction_id": "oh", "jurisdiction_name": "Ohio State Sales Tax", "state_code": "OH", "rate": 5.75,
             "amount": round(net * 0.0575, 2), "jurisdiction_level": "state"},
            {"jurisdiction_id": "stark", "jurisdiction_name": "Stark County (OH)", "state_code": "OH", "rate": 0.75,
             "amount": round(net * 0.0075, 2), "jurisdiction_level": "county"}]


def run(make_ctx, ds, invoices):
    parties = [{"id": "col", "addresses": [{"state": "OH", "city": "Columbus"}]},
               {"id": "can", "addresses": [{"state": "OH", "city": "Canton"}]}]
    return SourcingAndRate().evaluate(ds(invoices=invoices, parties=parties, jurisdictions=JURIS), make_ctx(tenant="us"))


def test_columbus_customer_charged_stark_county(make_ctx, ds):
    found = run(make_ctx, ds, [inv("INV-148", "col", 31377.78, rows(31377.78))])
    local = [f for f in found if f.rule == "local_sourcing_mismatch"]
    assert len(local) == 1 and str(local[0].total_exposure) == "235.33"


def test_canton_customer_is_consistent(make_ctx, ds):
    assert [f.rule for f in run(make_ctx, ds, [inv("INV-1", "can", 1000, rows(1000))])] == []
