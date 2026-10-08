---
id: us-08
title: Approval SLA and segregation of duties (US)
capability: approvals_us
description: >-
  US-08 (US): audits the approval control — self-approvals, approved AP documents with a skipped
  level, requests resolved after their SLA (recomputed, never the stored flag), and open requests past
  SLA per the platform's check_sla oracle (dry-run only) — with on-time rates by document type.
questions:
  - "Who approved what, was it within policy, and did anyone approve their own bill?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [ApprovalRequest.list, ApprovalLog.list, endpoint.approvals.check_sla]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: on_request}
compute: scripts.uc.US.us08_approval_sla:ApprovalSlaAuditUS
tools: [ApprovalRequest.list, ApprovalLog.list, endpoint.approvals.check_sla]
escalate: digest
spec: docs/usecases/US/us-08-approval-sla-audit.md
---

# US-08 · Approval SLA and segregation of duties (US) — SOP

**Full spec:** [`docs/usecases/US/us-08-approval-sla-audit.md`](../../docs/usecases/US/us-08-approval-sla-audit.md) ·
algorithm in [`UC-06`](../IN/uc-06-approval-sla-audit.md)
**Code:** [`scripts/uc/US/us08_approval_sla.py`](../../scripts/uc/US/us08_approval_sla.py) ·
checks in [`scripts/uc/common/approvals.py`](../../scripts/uc/common/approvals.py)

## When it runs
Weekly, and on request.

## What it checks
As UC-06: `self_approval`, `level_skipped`, `sla_breach`, `sla_breach_open` (check_sla with
`dry_run: true` — the policy refuses it otherwise), and data_quality rows where the stored
`is_overdue` disagrees with the truth.

## How to explain the result
SOX §404 is the control framework. N1 (wrong `is_overdue`, filed against this tenant) looks fixed:
0 disagreements is the expected result, and the check stays as a regression guard.

## Limits
`ApprovalPolicy` is 403 (N426 T2.1): whether policy allows self-approval can't be checked.
