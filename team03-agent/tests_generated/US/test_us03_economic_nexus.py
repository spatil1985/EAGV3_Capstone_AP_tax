"""LLM-generated, not graded. US-03 economic nexus."""

from datetime import date

from scripts.uc.US.us03_economic_nexus import EconomicNexus

NEXUS = [{"id": "il", "state_code": "IL", "is_registered": 0, "economic_threshold_amount": 100000,
          "economic_threshold_transactions": 200, "ytd_sales_amount": 0, "ytd_transaction_count": 0},
         {"id": "oh", "state_code": "OH", "is_registered": 1, "economic_threshold_amount": 100000,
          "economic_threshold_transactions": 200, "ytd_sales_amount": 500, "ytd_transaction_count": 1}]


def inv(n, state, net):
    return {"id": n, "number": n, "status": "paid", "date": "2026-05-01", "net_total": net, "party_id": "c",
            "taxes": [{"state_code": state, "amount": 1}]}


def run(make_ctx, ds, invoices):
    data = ds(invoices=invoices, parties=[], nexus=NEXUS, jurisdictions=[{"state_code": "IL", "rate_percentage": 6.25}])
    return EconomicNexus().evaluate(data, make_ctx(tenant="us", as_of=date(2026, 10, 3)))


def test_registered_state_quiet_and_counters_agree(make_ctx, ds):
    assert run(make_ctx, ds, [inv("a", "OH", 500)]) == []


def test_illinois_approaching_then_crossed(make_ctx, ds):
    rules = {f.rule for f in run(make_ctx, ds, [inv("a", "IL", 85000)])}
    assert rules == {"nexus_threshold_approaching", "stored_value_mismatch"}   # IL counters still read 0
    crossed = [f for f in run(make_ctx, ds, [inv("a", "IL", 120000)]) if f.rule == "nexus_threshold_crossed"]
    assert crossed and str(crossed[0].total_exposure) == "1250.00"


def test_unmonitored_state(make_ctx, ds):
    assert "nexus_unmonitored" in {f.rule for f in run(make_ctx, ds, [inv("a", "TX", 1000)])}
