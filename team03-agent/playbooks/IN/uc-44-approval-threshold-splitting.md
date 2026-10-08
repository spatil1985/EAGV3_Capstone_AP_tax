---
id: uc-44
title: Approval-threshold splitting
capability: threshold_split
description: >-
  UC-44 (India): finds groups of bills or purchase orders from one vendor within 3 days where each is
  under the approval limit but together they exceed it and none went through approval — a sign a
  purchase was split to avoid approval — scored by similar amounts, same creator and timing. The
  limit is assumed from config because the approval policy can't be read.
questions:
  - "Is anyone splitting purchases into smaller bills so each one stays under the approval limit?"
status: live
blocked_by: null
tax_regimes: [gst]          # the US tenant runs its own US-xx instance
requires:
  tools: [Bill.list, PurchaseOrder.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc44_approval_threshold_splitting:ApprovalThresholdSplitting
tools: [Bill.list, PurchaseOrder.list]
escalate: digest
spec: docs/usecases/IN/uc-44-approval-threshold-splitting.md
---

# UC-44 · Approval-threshold splitting — SOP

**Full spec:** [`docs/usecases/IN/uc-44-approval-threshold-splitting.md`](../../docs/usecases/IN/uc-44-approval-threshold-splitting.md)
**Code:** [`scripts/uc/IN/uc44_approval_threshold_splitting.py`](../../scripts/uc/IN/uc44_approval_threshold_splitting.py) ·
engine in [`scripts/uc/common/threshold_split.py`](../../scripts/uc/common/threshold_split.py)

## When it runs
Weekly, when a bill is created, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `split_candidate` | Same vendor, documents within 3 days, each below the limit, sum at or above it, none approved; strength low/medium/high |
| `policy_unreadable` (context) | The limit used and where it came from |

Recurring standing orders are excluded. The limit lives in `config/overrides/approval_thresholds.yaml`
(₹1,00,000 assumed for India).

## How to explain the result
It is a pattern for a person to check, not proof. Always say the limit is assumed (ApprovalPolicy is
403 — N426 T2.1). The seed day (12 Sep) concentrates bills, so same-day groups are common here.

## Limits
Splits across vendors, or across more than 3 days, aren't detected.
