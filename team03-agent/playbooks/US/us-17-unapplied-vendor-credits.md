---
id: us-17
title: Unapplied vendor credits (US)
capability: vendor_balance_us
description: >-
  US-17 (US): finds vendors we are about to pay while they owe us money — open vendor credits that can
  be applied against their open bills now — plus stale credits to claim back as refunds and advances
  not set against a bill.
questions:
  - "Are we about to pay vendors in full while they owe us money from credits?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [VendorCredit.list, Bill.list, PaymentMade.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: bill.approved}
  - {kind: on_request}
compute: scripts.uc.US.us17_unapplied_vendor_credits:UnappliedVendorCreditsUS
tools: [VendorCredit.list, Bill.list, PaymentMade.list]
escalate: digest
spec: docs/usecases/US/us-17-unapplied-vendor-credits.md
---

# US-17 · Unapplied vendor credits (US) — SOP

**Full spec:** [`docs/usecases/US/us-17-unapplied-vendor-credits.md`](../../docs/usecases/US/us-17-unapplied-vendor-credits.md) ·
algorithm in [`UC-41`](../IN/uc-41-unapplied-vendor-credits.md)
**Code:** [`scripts/uc/US/us17_unapplied_vendor_credits.py`](../../scripts/uc/US/us17_unapplied_vendor_credits.py) ·
shared in [`scripts/uc/common/vendor_balance.py`](../../scripts/uc/common/vendor_balance.py)

## When it runs
Weekly, when a bill is approved or a vendor credit is created, and on request.

## What it checks
As UC-41: `credit_applicable_now`, `stale_credit` (> 90 days, nothing owed), `advance_unadjusted`.

## How to explain the result
Keystone has no vendor credits today: 0 is the expected answer. A credit left with a vendor long
enough may also become unclaimed property (US-21).

## Limits
The agent never applies a credit itself.
