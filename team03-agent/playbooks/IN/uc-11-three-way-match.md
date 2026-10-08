---
id: uc-11
title: Three-way match (PO, receipt, bill)
capability: three_way
description: >-
  UC-11 (India): runs the platform's bill_match on every PO-linked bill and reports bills
  billed with nothing received against the PO (hold payment and ITC), POs billed beyond the
  ordered quantity, and bill rates outside the price tolerance. Flags MSME vendors so late-
  payment advice is not applied to goods never received.
questions:
  - "Were the goods we're being billed for actually received?"
status: live
blocked_by: null
tax_regimes: [all]
requires:
  tools: [Bill.list, Party.list, endpoint.accounting.bill_match]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc11_three_way_match:ThreeWayMatch
tools: [Bill.list, Party.list, endpoint.accounting.bill_match]
escalate: digest
spec: docs/usecases/IN/uc-11-three-way-match.md
---

# UC-11 · Three-way match — SOP

**Full spec:** [`docs/usecases/IN/uc-11-three-way-match.md`](../../docs/usecases/IN/uc-11-three-way-match.md)
**Code:** [`scripts/uc/IN/uc11_three_way_match.py`](../../scripts/uc/IN/uc11_three_way_match.py) ·
shared in [`scripts/uc/common/three_way.py`](../../scripts/uc/common/three_way.py)

## When it runs
Daily, when a bill with a PO arrives, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `billed_not_received` | `receipt_problem` set, or a line billed with 0 received: hold payment, no ITC (s.16(2)(b)) |
| `over_billed` | `billed_to_date_qty > ordered_qty` |
| `price_variance` | `price_variance_pct` beyond `price_tolerance_pct` |

`bill_match` is read-only in practice despite its WRITE tag (N3); the stored
`match_status` is never read (N2).

## How to explain the result
Word `receipt_not_for_purchase_order` carefully: the goods may have arrived on another
receipt. Bills from MSME vendors carry `uc04_msme_vendor`, so don't advise paying them
before receipt is confirmed.

## Limits
Inventory receipts themselves are not readable (N426 T2.2); only bill_match's verdict is.
