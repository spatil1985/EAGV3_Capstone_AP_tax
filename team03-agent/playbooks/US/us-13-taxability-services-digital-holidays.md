---
id: us-13
title: Taxability by state — services, digital, medical, shipping, holidays
capability: taxability
description: >-
  US-13 (US, sales tax): whether each thing we sell is taxable in the customer's state on that date —
  listed services, canned software and digital products, prescription and medical items, delivery
  charges, sales-tax holidays. Spec only for services and digital products (Keystone sells only goods,
  which are taxable and are checked by US-05); item tax codes are empty.
questions:
  - "Is each thing we sell actually taxable in the customer's state on that date — and are we charging accordingly?"
status: spec
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Invoice.list, Item.list, Party.list]
  verticals: [agency, clinic, retail, school]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: null
tools: [Invoice.list, Item.list, Party.list]
escalate: never
spec: docs/usecases/US/us-13-taxability-services-digital-holidays.md
---

# US-13 · Taxability by state — spec only

**Full spec:** [`docs/usecases/US/us-13-taxability-services-digital-holidays.md`](../../docs/usecases/US/us-13-taxability-services-digital-holidays.md) ·
complements [`US-05`](us-05-sourcing-and-rate-correctness.md) (rate, given taxable) and
[`US-04`](us-04-exemption-certificate-coverage.md) (customer exemptions)

## Why it is spec only
Keystone sells only tangible goods, which are taxable everywhere it sells (live check: 0 findings;
US-05 covers their rates). Services, digital products, medical items and holidays need a tenant that
sells them, and `Item.tax_code` is empty (data, not a platform request).

## What the agent says when asked
Goods are taxable by default; services only where a state lists them (Ohio taxes many business
services — data processing, janitorial, exterminating, security; Michigan and Illinois generally
don't). Canned software is taxable in OH, PA and MI. Prescription drugs are exempt (reduced in IL).
Delivery charges usually follow the item. Holidays are date-bounded. All per state, to confirm.

## To build
A per-state taxability table keyed on `Item.tax_code` (or product type), effective-dated for
holidays, checked against each invoice line's tax. Then write `scripts/uc/US/us13_*.py` and set
`status: live`.
