---
id: uc-22
title: GST on advances received
capability: advances
description: >-
  UC-22 (India): finds client advances held but not yet adjusted against an invoice
  (retainers with money received, on-account receipts) and computes the GST due on receipt if
  they are for services (18% tax-inclusive), 0% for an SEZ customer under LUT, nothing for
  goods. The platform can't record tax on advances, so this is computed, never verified.
questions:
  - "Have we paid GST on client advances we're still holding?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [RetainerInvoice.list, PaymentReceived.list, Party.list, Invoice.list, Item.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: retainer_invoice.paid}
  - {kind: on_request}
compute: scripts.uc.IN.uc22_advance_receipt_gst:AdvanceReceiptGst
tools: [RetainerInvoice.list, PaymentReceived.list, Party.list, Invoice.list, Item.list]
escalate: digest
spec: docs/usecases/IN/uc-22-advance-receipt-gst.md
---

# UC-22 · GST on advances received — SOP

**Full spec:** [`docs/usecases/IN/uc-22-advance-receipt-gst.md`](../../docs/usecases/IN/uc-22-advance-receipt-gst.md)
**Code:** [`scripts/uc/IN/uc22_advance_receipt_gst.py`](../../scripts/uc/IN/uc22_advance_receipt_gst.py)

## When it runs
Monthly, when a retainer is paid, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `advance_gst_unverifiable` | Advance held (`payment_made − amount_applied > 0`); GST if services = held × 18/118, due in the month of receipt |
| `advance_gst_zero_rated` | Same, SEZ customer: 0% under LUT (unconfirmed), receipt voucher still needed |

Goods vs services is taken from the customer's invoices; with no evidence it is assumed
services (conservative) and says so.

## How to explain the result
Give the range: ₹0 (goods, or services under a valid LUT) up to the services figure. Ask
the user to confirm the supply type and whether a receipt voucher was issued.

## Limits
`RetainerInvoice` has no items or tax fields (N426 T4.6).
