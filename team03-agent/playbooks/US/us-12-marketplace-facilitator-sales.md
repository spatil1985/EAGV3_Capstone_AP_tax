---
id: us-12
title: "Retail: marketplace facilitator sales"
capability: marketplace_us
description: >-
  US-12 (US, retail and other marketplace sellers): for sales made through marketplaces, whether the
  marketplace is collecting the tax (and we aren't charging it again), whether those sales are kept out
  of our own returns, and how they count toward economic nexus. Spec only: invoices carry no sales
  channel, and Keystone sells direct.
questions:
  - "For sales we make through marketplaces, is the marketplace collecting the tax, and are we keeping those sales out of our own returns and nexus totals correctly?"
status: spec
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Invoice.list, TaxNexus.list]
  verticals: [retail, clinic, school]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: null
tools: [Invoice.list, TaxNexus.list]
escalate: never
spec: docs/usecases/US/us-12-marketplace-facilitator-sales.md
---

# US-12 · Retail: marketplace facilitator sales — spec only

**Full spec:** [`docs/usecases/US/us-12-marketplace-facilitator-sales.md`](../../docs/usecases/US/us-12-marketplace-facilitator-sales.md) ·
India counterpart: [`UC-36`](../IN/uc-36-ecommerce-tcs-s52.md)

## Why it is spec only
`Invoice` has no sales-channel or marketplace field, and Keystone sells direct. The ask (sales
channel + marketplace settlement import) is listed in `usecase_feasibility.md` as not yet requested;
file it together with India's F22.

## What the agent says when asked
Every sales-tax state has a marketplace facilitator law: the marketplace collects and remits on the
sales it facilitates, and the seller excludes or deducts them on its return depending on the state.
States differ on whether marketplace sales count toward the seller's own economic-nexus threshold
(US-03). Charging tax as well as the marketplace is over-collection.

## To build
A sales channel on invoices (and settlement data). Then write `scripts/uc/US/us12_*.py` and set
`status: live`.
