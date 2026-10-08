"""LLM-generated, not graded. US-08: N1's two records now carry correct flags (spec §6)."""

from datetime import date

from scripts.uc.US.us08_approval_sla import ApprovalSlaAuditUS


def req(rid, resolved, flag):
    return {"id": rid, "number": rid, "document_type": "Bill", "status": "approved", "requested_by": "u1",
            "sla_deadline": "2026-05-10T18:00:00", "resolved_at": resolved, "_suspect_is_overdue": flag,
            "total_levels": 1}


def test_fixed_n1_records_are_quiet_apart_from_the_genuine_breach(make_ctx, ds):
    requests = [req("APR-121", "2026-05-17T10:00:00", 1), req("APR-107", "2026-05-09T10:00:00", 0)]
    logs = [{"request_id": r, "action": "approved", "actor_id": "u2", "level": 1} for r in ("APR-121", "APR-107")]
    found = ApprovalSlaAuditUS().evaluate(ds(requests=requests, logs=logs, breaches={}),
                                          make_ctx(tenant="us", as_of=date(2026, 10, 3)))
    assert [(f.entity_id, f.rule) for f in found] == [("APR-121", "sla_breach")]
