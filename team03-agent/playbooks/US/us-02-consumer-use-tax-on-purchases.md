---
id: us-02
title: Consumer use tax on purchases
capability: use_tax
description: >-
  US-02 (US, sales and use tax): finds this year's purchases on which no vendor charged sales tax and
  no use tax was accrued, classifies each line (manufacturing-exempt, non-taxable service, taxable
  service or goods, unclassified), and computes the use tax owed at the combined place-of-use rate,
  with the unclassified lines given as a range.
questions:
  - "Which purchases did nobody charge us sales tax on, where we owe use tax ourselves?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Bill.list, TaxJurisdiction.list, OrgProfile.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.US.us02_consumer_use_tax:ConsumerUseTax
tools: [Bill.list, TaxJurisdiction.list, OrgProfile.list]
escalate: digest
spec: docs/usecases/US/us-02-consumer-use-tax-on-purchases.md
---

# US-02 · Consumer use tax on purchases — SOP

**Full spec:** [`docs/usecases/US/us-02-consumer-use-tax-on-purchases.md`](../../docs/usecases/US/us-02-consumer-use-tax-on-purchases.md)
**Code:** [`scripts/uc/US/us02_consumer_use_tax.py`](../../scripts/uc/US/us02_consumer_use_tax.py) ·
line table in [`scripts/uc/common/us_purchase_tax.py`](../../scripts/uc/common/us_purchase_tax.py)

## When it runs
Monthly, when a bill with no vendor tax arrives, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `use_tax_due` | Per bill: taxable lines × combined place-of-use rate (OH 5.75% + Stark County 0.75%) |
| `use_tax_unclassified` | Lines needing classification, as a ceiling, not as due |
| `stored_value_mismatch` (data_quality) | `use_tax_accrued` set but different from the computed figure |

## How to explain the result
Give the untaxed total, what is clearly due, and the range for unclassified lines. Line
classification is a playbook table and needs a CPA's confirmation.

## Limits
`use_tax_accrued` is null on every bill, so there is nothing stored to check yet.
