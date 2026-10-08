---
id: uc-06
title: Approval SLA and segregation of duties
capability: approvals
description: >-
  UC-06 (India): audits the approval control. Finds self-approvals, approved AP documents
  with a skipped approval level, requests resolved after their SLA deadline (recomputed,
  never the stored flag) and open requests past SLA per the platform's check_sla oracle
  (dry-run only). Reports on-time rates by document type.
questions:
  - "Who approved what, was it within policy, and did anyone approve their own bill?"
status: live
blocked_by: null
tax_regimes: [all]
requires:
  tools: [ApprovalRequest.list, ApprovalLog.list, endpoint.approvals.check_sla]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: on_request}
compute: scripts.uc.IN.uc06_approval_sla:ApprovalSlaAudit
tools: [ApprovalRequest.list, ApprovalLog.list, endpoint.approvals.check_sla]
escalate: digest
spec: docs/usecases/IN/uc-06-approval-sla-audit.md
---

# UC-06 · Approval SLA and segregation of duties — SOP

**Full spec:** [`docs/usecases/IN/uc-06-approval-sla-audit.md`](../../docs/usecases/IN/uc-06-approval-sla-audit.md)
**Code:** [`scripts/uc/IN/uc06_approval_sla.py`](../../scripts/uc/IN/uc06_approval_sla.py) ·
shared checks in [`scripts/uc/common/approvals.py`](../../scripts/uc/common/approvals.py)

## When it runs
Weekly, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `self_approval` | `ApprovalLog` `approved` row by the requester |
| `level_skipped` | Approved Bill/Invoice/PO/Expense with no logged approval at some level |
| `sla_breach` | Resolved after `sla_deadline` (recomputed) |
| `sla_breach_open` | Open and breached per `check_sla {"dry_run": true}` (the policy refuses it without dry_run) |
| `stored_value_mismatch` / `impossible_timestamp` (data_quality) | The stored `is_overdue` disagrees with the truth; `resolved_at` in the future |

Lead/AgentJob test traffic and Contract approvals (outside Seat 03) are left out.

## How to explain the result
Self-approvals first, then breaches by hours late. Every row keeps the `sla_deadline` it
was judged against, because the platform has rewritten deadlines before (N8).

## Limits
`ApprovalPolicy` is 403 for our role (N426 T2.1), so whether policy allows self-approval,
and the amount thresholds, can't be checked.
