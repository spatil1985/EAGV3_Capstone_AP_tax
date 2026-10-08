---
id: us-20
title: Approval-threshold splitting (US)
capability: threshold_split_us
description: >-
  US-20 (US): finds groups of bills or POs from one vendor within 3 days where each is under the
  approval limit, together they exceed it, and none went through approval. The limit ($10,000) is
  inferred from the bill approval bands and re-checked each run.
questions:
  - "Is anyone splitting purchases to stay under the approval limit?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Bill.list, PurchaseOrder.list, ApprovalRequest.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.US.us20_approval_threshold_splitting:ApprovalThresholdSplittingUS
tools: [Bill.list, PurchaseOrder.list, ApprovalRequest.list]
escalate: digest
spec: docs/usecases/US/us-20-approval-threshold-splitting.md
---

# US-20 · Approval-threshold splitting (US) — SOP

**Full spec:** [`docs/usecases/US/us-20-approval-threshold-splitting.md`](../../docs/usecases/US/us-20-approval-threshold-splitting.md) ·
algorithm in [`UC-44`](../IN/uc-44-approval-threshold-splitting.md)
**Code:** [`scripts/uc/US/us20_approval_threshold_splitting.py`](../../scripts/uc/US/us20_approval_threshold_splitting.py) ·
engine in [`scripts/uc/common/threshold_split.py`](../../scripts/uc/common/threshold_split.py)

## When it runs
Weekly, on each new bill, and on request.

## What it checks
As UC-44: `split_candidate` (strength low/medium/high) and the `policy_unreadable` context row. The
run context shows the edge inferred from approval history next to the configured one.

## How to explain the result
Fortnightly standing orders contain bills above the limit, so they aren't splits. Confirm the
$10,000 edge with the operators: one exception in the 45 approvals would move it.

## Limits
`ApprovalPolicy` is 403 (N426 T2.1); the edge is inferred, not read.
