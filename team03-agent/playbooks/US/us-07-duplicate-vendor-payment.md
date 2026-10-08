---
id: us-07
title: Duplicate vendor payment (US)
capability: duplicates_us
description: >-
  US-07 (US): finds bills that may pay a vendor twice — a purchase order billed beyond its ordered
  quantity, or the same vendor and amount within 3 days outside a recurring template — and says
  whether to hold one or recover. Supplier bill numbers are empty on this tenant, so the exact tier
  can't run; fortnightly standing orders on separate POs are not duplicates.
questions:
  - "Is any vendor being paid twice?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Bill.list, Party.list, PaymentMade.list, endpoint.accounting.bill_match]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.US.us07_duplicate_vendor_payment:DuplicateVendorPaymentUS
tools: [Bill.list, Party.list, PaymentMade.list, endpoint.accounting.bill_match]
escalate: digest
spec: docs/usecases/US/us-07-duplicate-vendor-payment.md
---

# US-07 · Duplicate vendor payment (US) — SOP

**Full spec:** [`docs/usecases/US/us-07-duplicate-vendor-payment.md`](../../docs/usecases/US/us-07-duplicate-vendor-payment.md) ·
algorithm in [`UC-05`](../IN/uc-05-duplicate-vendor-payment.md)
**Code:** [`scripts/uc/US/us07_duplicate_vendor_payment.py`](../../scripts/uc/US/us07_duplicate_vendor_payment.py) ·
tiers in [`scripts/uc/common/duplicates.py`](../../scripts/uc/common/duplicates.py)

## When it runs
Daily, on each new bill, and on request.

## What it checks
As UC-05: `duplicate_exact` (can't run here — no supplier bill numbers), `duplicate_over_billed`
(bill_match), `duplicate_suspicious_strong` / `_weak` (same vendor and amount ≤ 3 days apart, not a
recurring template).

## How to explain the result
State tier-1 coverage (0 bills with a supplier number). Standing orders recurring every ~14 days on
separate POs are expected repetition, not duplicates.

## Limits
Holds need `Bill.hold` (N426 T3.3). A duplicate here costs cash, and any use tax self-assessed on it.
