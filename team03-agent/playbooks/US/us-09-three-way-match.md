---
id: us-09
title: Three-way match (US)
capability: three_way_us
description: >-
  US-09 (US): runs the platform's bill_match on every PO-linked bill and reports bills billed with
  nothing received (hold payment), POs billed beyond the ordered quantity, and rates outside the price
  tolerance; also checks that the recorded match status agrees with the live match (the N2 fix).
questions:
  - "Were the goods we're being billed for actually received?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Bill.list, Party.list, endpoint.accounting.bill_match]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.US.us09_three_way_match:ThreeWayMatchUS
tools: [Bill.list, Party.list, endpoint.accounting.bill_match]
escalate: digest
spec: docs/usecases/US/us-09-three-way-match.md
---

# US-09 · Three-way match (US) — SOP

**Full spec:** [`docs/usecases/US/us-09-three-way-match.md`](../../docs/usecases/US/us-09-three-way-match.md) ·
algorithm in [`UC-11`](../IN/uc-11-three-way-match.md)
**Code:** [`scripts/uc/US/us09_three_way_match.py`](../../scripts/uc/US/us09_three_way_match.py) ·
shared in [`scripts/uc/common/three_way.py`](../../scripts/uc/common/three_way.py)

## When it runs
Daily, when a bill with a PO arrives, and on request.

## What it checks
As UC-11 (`billed_not_received`, `over_billed`, `price_variance`), plus:

| Rule | Finding |
|---|---|
| `stored_value_mismatch` (data_quality) | `recorded_status` ≠ the live match status (N2 regression guard) |

## How to explain the result
SOX §404 key control; no input credit is involved. `received_qty` null means no receipt basis — a
two-way match — not missing goods.

## Limits
Inventory receipts aren't readable directly; only bill_match's verdict is.
