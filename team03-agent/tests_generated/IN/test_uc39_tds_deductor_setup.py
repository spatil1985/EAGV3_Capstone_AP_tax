"""LLM-generated, not graded. UC-39 TDS setup."""

from datetime import date
from decimal import Decimal

from scripts.uc.IN.uc39_tds_deductor_setup import TdsDeductorSetup


def run(make_ctx, ds, org=None, bills=(), expenses=()):
    data = ds(org=[org or {"enable_tds": 1, "tan": None}], prefs=[{}], bills=list(bills), expenses=list(expenses),
              payments=[])
    return TdsDeductorSetup().evaluate(data, make_ctx(as_of=date(2026, 10, 4)))


def test_tan_missing_and_seeded_section_code(make_ctx, ds):
    bill = {"id": "b", "number": "BILL-1", "status": "open", "date": "2026-09-01", "tds_percentage": 12,
            "_suspect_tds_amount": 100, "_suspect_tds_section_code": "C5341/9637", "items": []}
    assert sorted(f.rule for f in run(make_ctx, ds, bills=[bill])) == ["tan_missing", "tds_section_code_invalid"]


def test_msme_interest_above_194a_threshold(make_ctx, ds):
    exps = [{"id": f"e{i}", "date": "2026-09-03", "amount": 80855.61, "vendor_id": "rs", "_vendor_id_display": "Rahul",
             "_account_id_display": "MSME Interest (Section 16)", "status": "unbilled"} for i in range(2)]
    found = run(make_ctx, ds, org={"enable_tds": 1, "tan": "PNEA12345B"}, expenses=exps)
    assert [f.rule for f in found] == ["tds_section_not_applied"]
    assert found[0].total_exposure == Decimal("16171.12")
