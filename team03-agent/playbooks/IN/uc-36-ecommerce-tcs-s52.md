---
id: uc-36
title: "Retail: e-commerce TCS (s.52) and s.9(5)"
capability: marketplace_in
description: >-
  UC-36 (India, retail and other marketplace sellers): whether sales made through e-commerce
  operators, and the 1% TCS they collected under s.52, agree with what we report in GSTR-1, and
  whether that TCS has been claimed back. Blocked: invoices carry no sales channel or operator, and
  there is no TCS-credit record.
questions:
  - "Do our marketplace sales, and the tax the marketplace collected on them, agree with what we report — and have we claimed that collected tax back?"
status: blocked
blocked_by: "F22 (not filed): no sales-channel / operator field on Invoice and no TCS credit (GSTR-8) record — GAP-6"
tax_regimes: [gst]
requires:
  tools: [Invoice.list, Party.list]
  verticals: [retail, clinic, agency]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: null
tools: [Invoice.list, Party.list]
escalate: never
spec: docs/usecases/IN/uc-36-ecommerce-tcs-s52.md
---

# UC-36 · Retail: e-commerce TCS (s.52) — blocked

**Full spec:** [`docs/usecases/IN/uc-36-ecommerce-tcs-s52.md`](../../docs/usecases/IN/uc-36-ecommerce-tcs-s52.md)

## Why it is blocked
`Invoice` has no channel or operator field, so marketplace sales can't be told apart (a marketplace
`Party` as the customer loses the end buyer's place of supply), and there is no record of TCS the
operator collected (GSTR-8 / the electronic cash ledger). The ask is F22, listed in
`usecase_feasibility.md` as not yet filed — file it together with US-12's sales-channel need.

## What the agent says when asked
Under s.52 the operator collects 1% TCS (0.5% CGST + 0.5% SGST, or 1% IGST) on net taxable sales and
reports them in GSTR-8; the seller's GSTR-1 must agree, and the TCS is claimed back through the cash
ledger. Under s.9(5) the operator itself pays tax on notified services. None of it can be checked in
the current data model.

## To unblock
F22 (sales channel + marketplace settlement import). Then write `scripts/uc/IN/uc36_*.py` and set
`status: live`.
