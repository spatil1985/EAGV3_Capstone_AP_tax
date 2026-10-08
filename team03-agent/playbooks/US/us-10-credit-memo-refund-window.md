---
id: us-10
title: Sales tax on credit memos and refund windows
capability: credit_memo_window
description: >-
  US-10 (US, sales tax): for returns and price adjustments, whether the sales tax was refunded
  correctly to the customer and recovered from the state inside its refund window (Ohio: four years,
  R.C. 5739.07). Spec only: there are no credit memos on the tenant.
questions:
  - "For returns and price adjustments, did we refund the sales tax correctly, and are we still inside the window to recover tax we remitted?"
status: spec
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [CreditNote.list, Invoice.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: credit_note.created}
  - {kind: on_request}
compute: null
tools: [CreditNote.list, Invoice.list]
escalate: never
spec: docs/usecases/US/us-10-credit-memo-refund-window.md
---

# US-10 · Sales tax on credit memos and refund windows — spec only

**Full spec:** [`docs/usecases/US/us-10-credit-memo-refund-window.md`](../../docs/usecases/US/us-10-credit-memo-refund-window.md) ·
India counterpart: [`UC-19`](../IN/uc-19-credit-note-time-limit.md)

## Why it is spec only
`CreditNote.list` returns 0 records on Keystone, and the liability report shows `credited_sales: 0`.
There is nothing to check yet.

## What the agent says when asked
A refund on a taxed sale refunds the tax on the refunded amount; the seller then credits it on its
next return or claims it from the state, inside the state's window (Ohio four years; others commonly
three to four — confirm per state). Refunding the customer without recovering from the state is a
loss; recovering without refunding is a liability to the customer.

## To build
When credit memos appear: per memo, the tax refunded vs the original invoice's tax on the refunded
amount, and the window per state (constants with citations). Then write
`scripts/uc/US/us10_*.py` and set `status: live`.
