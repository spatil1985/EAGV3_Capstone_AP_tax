"""Approval-control checks shared by UC-06 (India) and US-08 (US).

Never trust the stored `is_overdue` (N1/N8; quarantined to `_suspect_is_overdue` at fetch):
resolved requests are recomputed from `resolved_at > sla_deadline`, open requests use the
platform oracle `endpoint.approvals.check_sla {"dry_run": true}`. Approvers come from
`ApprovalLog.actor_id` only, never `steps[]` (N5 tool names).
"""

from datetime import datetime

from scripts.findings import DATA_QUALITY, Finding

RESOLVED = {"approved", "rejected", "recalled", "cancelled"}
OPEN = {"pending", "escalated", "in_review"}
AP_DOCS = {"Bill", "Invoice", "PurchaseOrder", "Expense", "VendorCredit", "PaymentMade"}
# Test traffic and documents outside Seat 03 (Contract* is a prohibited entity in our charter).
EXCLUDED_DOCS = {"Lead", "AgentJob", "Contract", "ContractClauseDeviation", "ContractRenewal"}


def ts(value) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(str(value).replace("Z", "+00:00")).replace(tzinfo=None)
    except ValueError:
        return None


def in_scope(req) -> bool:
    return req.get("document_type") not in EXCLUDED_DOCS


def resolved_late(req) -> bool | None:
    deadline, done = ts(req.get("sla_deadline")), ts(req.get("resolved_at"))
    return (done > deadline) if deadline and done else None


def oracle_breaches(raw) -> dict:
    """{request_id: breach row} from check_sla's reply ({"result": {...}} or the object)."""
    body = raw.get("result", raw) if isinstance(raw, dict) else {}
    return {b.get("request_id"): b for b in body.get("breached") or [] if b.get("request_id")}


def _row(rule, req, ctx, *, severity, summary, finding_type="approval_control", status="finding", **details):
    return Finding(finding_type=finding_type, rule=rule, severity=severity, entity_type="ApprovalRequest",
                   entity_id=req["id"], entity_ref=req.get("number"), currency=ctx.currency, status=status,
                   summary=summary,
                   details={"document_type": req.get("document_type"), "document_name": req.get("document_name"),
                            "sla_deadline_evaluated": req.get("sla_deadline"),
                            "resolved_at_evaluated": req.get("resolved_at"),
                            "stored_is_overdue": req.get("_suspect_is_overdue"), **details})


def approval_findings(requests, logs, breaches: dict, ctx, now: datetime):
    by_id = {r["id"]: r for r in requests}
    approvals: dict = {}
    for log in logs:
        if log.get("action") == "approved" and log.get("request_id") in by_id:
            approvals.setdefault(log["request_id"], []).append(log)

    for req in requests:
        if not in_scope(req):
            continue
        number, doc = req.get("number"), req.get("document_type")
        stored = bool(req.get("_suspect_is_overdue"))
        status = (req.get("status") or "").lower()
        if status in RESOLVED:
            done = ts(req.get("resolved_at"))
            if done and done > now:
                yield _row("impossible_timestamp", req, ctx, severity=10, finding_type=DATA_QUALITY,
                           status=DATA_QUALITY,
                           summary=f"{number} ({doc}) has resolved_at {req.get('resolved_at')} in the future; "
                                   f"excluded from the compliance rate.")
                continue
            late = resolved_late(req)
            if late is None:
                continue
            if late:
                hours = round((done - ts(req["sla_deadline"])).total_seconds() / 3600, 1)
                yield _row("sla_breach", req, ctx, severity=60, late=True, hours_late=hours,
                           summary=f"{number} ({doc}, {req.get('document_name')}) was resolved {hours} h after "
                                   f"its SLA deadline.")
            if late != stored:
                yield _row("stored_value_mismatch", req, ctx, severity=10, finding_type=DATA_QUALITY,
                           status=DATA_QUALITY, late=late,
                           summary=f"{number} ({doc}) was resolved {'late' if late else 'on time'}; the platform "
                                   f"flags it {'overdue' if stored else 'not overdue'} — counted "
                                   f"{'late' if late else 'on time'}.")
        elif status in OPEN:
            hit = breaches.get(req["id"])
            if hit:
                yield _row("sla_breach_open", req, ctx, severity=65, hours_overdue=hit.get("hours_overdue"),
                           approver=hit.get("approver"),
                           summary=f"{number} ({doc}, {req.get('document_name')}) is {hit.get('hours_overdue')} h "
                                   f"past its SLA, waiting on {hit.get('approver') or 'an approver'}.")
            if bool(hit) != stored:
                yield _row("stored_value_mismatch", req, ctx, severity=10, finding_type=DATA_QUALITY,
                           status=DATA_QUALITY, oracle_breached=bool(hit),
                           summary=f"{number} ({doc}): check_sla says {'breached' if hit else 'not breached'}, "
                                   f"the stored flag says {'overdue' if stored else 'not overdue'}.")
        for log in approvals.get(req["id"], []):
            if log.get("actor_id") and log.get("actor_id") == req.get("requested_by"):
                yield _row("self_approval", req, ctx, severity=90, actor_id=log.get("actor_id"),
                           actor_name=log.get("actor_name"), level=log.get("level"),
                           summary=f"{number} ({doc}, {req.get('document_name')}) was approved by the person who "
                                   f"requested it ({log.get('actor_name') or log.get('actor_id')}). Whether policy "
                                   f"allows self-approval can't be read (ApprovalPolicy is 403).")
        if status == "approved" and doc in AP_DOCS:
            levels = int(float(req.get("total_levels") or 1))
            got = {int(float(l.get("level") or 0)) for l in approvals.get(req["id"], [])}
            missing = [n for n in range(1, levels + 1) if n not in got]
            if missing:
                yield _row("level_skipped", req, ctx, severity=70, missing_levels=missing, total_levels=levels,
                           summary=f"{number} ({doc}, {req.get('document_name')}) is approved, but no approval is "
                                   f"logged at level(s) {missing} of {levels}.")


def compliance(requests, now: datetime) -> dict:
    out: dict = {}
    for req in requests:
        if not in_scope(req) or (req.get("status") or "").lower() not in RESOLVED:
            continue
        done = ts(req.get("resolved_at"))
        late = resolved_late(req)
        if late is None or (done and done > now):
            continue
        row = out.setdefault(req.get("document_type"), [0, 0])
        row[0] += 0 if late else 1
        row[1] += 1
    return {doc: f"{ok}/{n} on time" for doc, (ok, n) in sorted(out.items(), key=lambda kv: kv[0] not in AP_DOCS)}
