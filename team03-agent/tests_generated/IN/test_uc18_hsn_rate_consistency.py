"""LLM-generated, not graded. UC-18 HSN rate checks (spec §5 worked example HSN 73269099)."""

from scripts.uc.IN.uc18_hsn_rate_consistency import HsnRateConsistency


def inv(n, rate, when="2026-09-10"):
    return {"id": n, "number": n, "direction": "receivable", "status": "sent", "date": when,
            "items": [{"hsn_or_sac": "73269099", "tax_percentage": rate, "taxable_amount": 100}]}


def run(make_ctx, ds, invoices, items=()):
    return HsnRateConsistency().evaluate(ds(invoices=invoices, items=list(items)), make_ctx())


def test_one_hsn_five_rates(make_ctx, ds):
    found = run(make_ctx, ds, [inv(f"I{r}", r) for r in (0, 5, 9, 12, 18)])
    inconsistent = [f for f in found if f.rule == "hsn_rate_inconsistent"]
    assert len(inconsistent) == 1 and len(inconsistent[0].details["rates_seen"]) == 5


def test_slabs_are_effective_dated(make_ctx, ds):
    found = run(make_ctx, ds, [inv("old", 12, "2025-06-01"), inv("new", 12, "2026-06-01"), inv("half", 9)])
    bad = {f.entity_id: f for f in found if f.rule == "rate_not_a_slab"}
    assert set(bad) == {"new", "half"}                 # 12% was a slab before 22 Sep 2025
    assert bad["half"].details["likely_half_of"] == "18"
