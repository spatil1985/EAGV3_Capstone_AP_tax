---
id: uc-05
title: Duplicate vendor payment
capability: duplicates
description: >-
  UC-05 (India): finds bills that may pay a vendor twice, in three tiers: the same supplier
  bill number (exact), a purchase order billed beyond its ordered quantity (over-billed), and
  the same vendor and amount within 3 days outside a recurring template (suspicious). Says
  whether to hold one bill or recover a payment, and how much of the ledger tier 1 covers.
questions:
  - "Is any vendor being paid twice?"
status: live
blocked_by: null
tax_regimes: [gst]          # the US tenant runs its own US-xx instance
requires:
  tools: [Bill.list, Party.list, PaymentMade.list, endpoint.accounting.bill_match]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc05_duplicate_vendor_payment:DuplicateVendorPayment
tools: [Bill.list, Party.list, PaymentMade.list, endpoint.accounting.bill_match]
escalate: digest
spec: docs/usecases/IN/uc-05-duplicate-vendor-payment.md
---

# UC-05 · Duplicate vendor payment — SOP

**Full spec:** [`docs/usecases/IN/uc-05-duplicate-vendor-payment.md`](../../docs/usecases/IN/uc-05-duplicate-vendor-payment.md)
**Code:** [`scripts/uc/IN/uc05_duplicate_vendor_payment.py`](../../scripts/uc/IN/uc05_duplicate_vendor_payment.py) ·
shared tiers in [`scripts/uc/common/duplicates.py`](../../scripts/uc/common/duplicates.py)

## When it runs
Daily, when a new bill arrives (on_event), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `duplicate_exact` | Same vendor (GSTIN, else id), same normalised supplier `bill_number`, same FY |
| `duplicate_over_billed` | `bill_match` shows `billed_to_date_qty > ordered_qty` on the bill's PO |
| `duplicate_suspicious_strong` / `_weak` | Same vendor, same positive `grand_total`, ≤ 3 days apart, not from one recurring template; strong if line items match |

Each pair says what to do: hold one (neither paid), hold the unpaid one, or recover (both paid).

## How to explain the result
Lead with the count by tier and the amount still stoppable. Always state tier-1 coverage
("18/127 bills carry a supplier bill number"), and that recurring-template repeats were
suppressed (that defect is filed as N6).

## Limits
Never holds or voids a bill itself; a hold needs a person (T3.3 `Bill.hold` is requested).
