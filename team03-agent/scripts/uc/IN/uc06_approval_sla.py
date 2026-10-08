"""UC-06 — Approval SLA and segregation of duties (India).

Spec: docs/usecases/IN/uc-06-approval-sla-audit.md.
Question: "Who approved what, was it within policy, and did anyone approve their own bill?"

Rules (scripts/uc/common/approvals.py):
  self_approval          an ApprovalLog `approved` row whose actor is the requester
  level_skipped          an approved AP document with fewer logged approvals than levels
  sla_breach             resolved after sla_deadline (recomputed; is_overdue is never trusted)
  sla_breach_open        open and breached per check_sla {"dry_run": true}
  data_quality           stored is_overdue disagrees with the truth; resolved_at in the future

Policy-level checks (allow_self_approval, thresholds) need ApprovalPolicy, which is 403 for
our role (requested as N426 T2.1); self-approvals are reported with that caveat.
"""

from datetime import datetime

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.uc.common.approvals import approval_findings, compliance, oracle_breaches

CHECK_SLA = "endpoint.approvals.check_sla"


def _now(ctx) -> datetime:
    return datetime.combine(ctx.as_of, datetime.max.time())


class ApprovalControls(Rule):
    id = "approval_control"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        yield from approval_findings(data.get("requests", []), data.get("logs", []),
                                     data.get("breaches", {}), ctx, _now(ctx))


class ApprovalSlaAudit(Playbook):

    @property
    def rules(self):
        return [ApprovalControls()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(requests=fetcher.list("ApprovalRequest"), logs=fetcher.list("ApprovalLog"),
                       breaches=oracle_breaches(fetcher.call(CHECK_SLA, {"dry_run": True})))

    def context(self, data, findings, ctx):
        return {"approval requests": len(data["requests"]), "approval log rows": len(data["logs"]),
                "open requests breached (check_sla)": len(data["breaches"]),
                "resolved on time, by document type": compliance(data["requests"], _now(ctx)),
                "ApprovalPolicy": "unreadable (403) — policy limits not checked"}

    def summary(self, outcome, ctx):
        count = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"Self-approvals: {count('self_approval')}. Levels skipped: {count('level_skipped')}. "
                f"Resolved late: {count('sla_breach')}. Open and breached (check_sla): {count('sla_breach_open')}. "
                f"Platform is_overdue disagrees on {count('stored_value_mismatch')} request(s). "
                f"Resolved on time: {outcome.context.get('resolved on time, by document type')}.")
