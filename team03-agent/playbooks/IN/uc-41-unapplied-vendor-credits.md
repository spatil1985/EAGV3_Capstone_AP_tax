---
id: uc-41
title: Unapplied vendor credits and advances
capability: vendor_balance
description: >-
  UC-41 (India): finds vendors we are about to pay while they owe us money — open vendor credits
  that can be applied against their open bills now — plus credits older than 90 days with nothing to
  set them against (ask for a refund) and advances not adjusted against a bill.
questions:
  - "Are we about to pay vendors in full while they owe us money from credit notes or advances?"
status: live
blocked_by: null
tax_regimes: [gst]          # the US tenant runs its own US-xx instance
requires:
  tools: [VendorCredit.list, Bill.list, PaymentMade.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: bill.approved}
  - {kind: on_request}
compute: scripts.uc.IN.uc41_unapplied_vendor_credits:UnappliedVendorCredits
tools: [VendorCredit.list, Bill.list, PaymentMade.list]
escalate: digest
spec: docs/usecases/IN/uc-41-unapplied-vendor-credits.md
---

# UC-41 · Unapplied vendor credits and advances — SOP

**Full spec:** [`docs/usecases/IN/uc-41-unapplied-vendor-credits.md`](../../docs/usecases/IN/uc-41-unapplied-vendor-credits.md)
**Code:** [`scripts/uc/IN/uc41_unapplied_vendor_credits.py`](../../scripts/uc/IN/uc41_unapplied_vendor_credits.py) ·
shared in [`scripts/uc/common/vendor_balance.py`](../../scripts/uc/common/vendor_balance.py)

## When it runs
Weekly, when a bill is approved or a vendor credit is created, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `credit_applicable_now` | Vendor with open credits and open bills: apply min(credit, bills) before paying |
| `stale_credit` | Open credit older than 90 days, nothing owed to the vendor: ask for a refund |
| `advance_unadjusted` | Payment with unused amount older than 90 days |

Residues under ₹1 are rounding, counted in the context only.

## How to explain the result
Lead with the amount to apply and the largest vendor. The agent never applies a credit itself
(`VendorCredit.apply_to_bill` is a ledger write).

## Limits
Some credits predate the first bill in the ledger, so they may relate to purchases outside it.
