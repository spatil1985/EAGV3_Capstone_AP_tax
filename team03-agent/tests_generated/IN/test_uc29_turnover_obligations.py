"""LLM-generated, not graded. UC-29 turnover obligations (spec §5 worked example)."""

from datetime import date

from scripts.uc.IN.uc29_turnover_obligations import TurnoverBasedObligations


def inv(n, when, value, treatment="business_gst"):
    return {"id": n, "number": n, "direction": "receivable", "status": "paid", "date": when, "taxable_value": value,
            "grand_total": value, "total_tax": 0, "gst_treatment": treatment}


def run(make_ctx, ds, invoices, prefs=None, org=None, locale=None):
    data = ds(invoices=invoices, credit_notes=[], org=[org or {"enable_e_invoicing": 1}],
              einvoice_prefs=[prefs or {"enabled": 0, "sandbox_mode": 1}], locations=[], locale=locale or {})
    playbook = TurnoverBasedObligations()
    ctx = make_ctx(as_of=date(2026, 10, 4))
    return playbook.evaluate(data, ctx), playbook.context(data, [], ctx)


def test_einvoicing_required_and_settings_conflict(make_ctx, ds):
    found, ctx = run(make_ctx, ds, [inv("old", "2025-09-19", 67065518.43), inv("new", "2026-05-01", 1000)])
    assert sorted(f.rule for f in found) == ["classification_conflict", "einvoice_required_not_generated"]
    assert ctx["turnover is a floor"] is True


def test_floor_below_a_line_is_undeterminable(make_ctx, ds):
    _, ctx = run(make_ctx, ds, [inv("old", "2025-09-19", 67065518.43)], org={"enable_e_invoicing": 0},
                 prefs={"enabled": 1})
    assert ctx["obligation matrix"]["s.194Q buyer TDS"].startswith("undeterminable")
