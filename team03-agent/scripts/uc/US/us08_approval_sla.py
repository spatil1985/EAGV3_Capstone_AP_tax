"""US-08 — Approval SLA and segregation of duties (US instance of UC-06).

Spec: docs/usecases/US/us-08-approval-sla-audit.md (algorithm as UC-06).
Question: "Who approved what, was it within policy, and did anyone approve their own bill?"

Same checks as UC-06 (scripts/uc/common/approvals.py). Statutory basis here is SOX §404 internal control
over financial reporting rather than the Companies Act. N1 (filed against this tenant) appears fixed —
the "recompute, never trust is_overdue" rule stays as its regression guard.
"""

from scripts.uc.IN.uc06_approval_sla import ApprovalSlaAudit


class ApprovalSlaAuditUS(ApprovalSlaAudit):
    """UC-06's playbook unchanged; kept as its own class so the US manifest and SOP stand alone."""
