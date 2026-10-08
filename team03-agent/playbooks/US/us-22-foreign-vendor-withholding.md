---
id: us-22
title: "Foreign vendors: Chapter 3 withholding and Form 1042-S"
capability: foreign_withholding
description: >-
  US-22 (US): before paying a foreign vendor, whether the right US tax was withheld (30% on US-source
  FDAP income, or a treaty rate with a valid W-8) and the right form collected, with 1042-S reporting
  by 15 March. Spec only: no foreign vendor exists on Keystone, and Party has no W-8 fields.
questions:
  - "Before we pay a foreign vendor, have we withheld the right US tax and collected the right form?"
status: spec
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Party.list, Bill.list, PaymentMade.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: null
tools: [Party.list, Bill.list, PaymentMade.list]
escalate: never
spec: docs/usecases/US/us-22-foreign-vendor-withholding.md
---

# US-22 · Foreign vendors: Chapter 3 withholding — spec only

**Full spec:** [`docs/usecases/US/us-22-foreign-vendor-withholding.md`](../../docs/usecases/US/us-22-foreign-vendor-withholding.md) ·
India counterpart [`UC-37`](../IN/uc-37-non-resident-payments-tds-195.md)

## Why it is spec only
All 8 vendors on Keystone are in Ohio, and `Party` has no W-8 fields (W-8BEN / W-8BEN-E, treaty
claim). The ask — W-8 fields on Party — is listed in `usecase_feasibility.md` as not yet requested.

## What the agent says when asked
US-source FDAP income (royalties, rents, services performed in the US) paid to a foreign person is
withheld at 30% (IRC §§1441–1442) unless a treaty reduces it with a valid W-8; services performed
entirely abroad are generally foreign-source and not withheld. Payments are reported on Form 1042-S
by 15 March. Missing withholding makes us liable for it.

## To build
W-8 fields on Party (or a `config/overrides` file like UC-37's), then follow UC-37's pattern:
`scripts/uc/US/us22_*.py` and `status: live`.
