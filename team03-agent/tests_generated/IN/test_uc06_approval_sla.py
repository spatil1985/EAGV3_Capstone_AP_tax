"""LLM-generated, not graded. UC-06 approval controls (spec §5 worked example)."""

from datetime import date

from scripts.uc.IN.uc06_approval_sla import ApprovalSlaAudit

AS_OF = date(2026, 9, 28)


def req(rid, **extra):
    base = {"id": rid, "number": f"APR-{rid}", "document_type": "Invoice", "status": "recalled",
            "requested_by": "u1", "sla_deadline": "2026-10-21T18:00:00",
            "resolved_at": "2026-09-12T17:19:15.683726", "_suspect_is_overdue": 1, "total_levels": 1}
    return {**base, **extra}


def run(make_ctx, ds, requests, logs=(), breaches=None):
    return ApprovalSlaAudit().evaluate(ds(requests=requests, logs=list(logs), breaches=breaches or {}),
                                       make_ctx(as_of=AS_OF))


def test_early_resolution_flagged_overdue_is_a_data_quality_row(make_ctx, ds):
    found = run(make_ctx, ds, [req("25")])
    assert [f.rule for f in found] == ["stored_value_mismatch"]


def test_self_approval_and_skipped_level(make_ctx, ds):
    r = req("1", document_type="Bill", status="approved", total_levels=2, _suspect_is_overdue=0)
    logs = [{"request_id": "1", "action": "approved", "actor_id": "u1", "level": 1}]
    rules = sorted(f.rule for f in run(make_ctx, ds, [r], logs))
    assert rules == ["level_skipped", "self_approval"]


def test_open_breach_comes_from_the_oracle(make_ctx, ds):
    r = req("2", status="pending", resolved_at=None, _suspect_is_overdue=1)
    found = run(make_ctx, ds, [r], breaches={"2": {"request_id": "2", "hours_overdue": 321.7}})
    assert [f.rule for f in found] == ["sla_breach_open"]


def test_future_resolution_is_impossible_and_contract_is_excluded(make_ctx, ds):
    found = run(make_ctx, ds, [req("50", resolved_at="2026-11-05"), req("9", document_type="Contract")])
    assert [f.rule for f in found] == ["impossible_timestamp"]
