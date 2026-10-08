---
id: us-05
title: Sourcing and rate correctness
capability: rates
description: >-
  US-05 (US, sales tax): checks each sales tax row — amount equals net × rate, rate equals the
  configured jurisdiction's, state matches the customer's state, and a destination-sourced county tax
  is only charged to customers in that county — and lists counties customers are in with no local
  jurisdiction configured.
questions:
  - "Are we charging each customer the right state and local rate for where the sale is sourced?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Invoice.list, Party.list, TaxJurisdiction.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: scripts.uc.US.us05_sourcing_and_rate:SourcingAndRate
tools: [Invoice.list, Party.list, TaxJurisdiction.list]
escalate: digest
spec: docs/usecases/US/us-05-sourcing-and-rate-correctness.md
---

# US-05 · Sourcing and rate correctness — SOP

**Full spec:** [`docs/usecases/US/us-05-sourcing-and-rate-correctness.md`](../../docs/usecases/US/us-05-sourcing-and-rate-correctness.md)
**Code:** [`scripts/uc/US/us05_sourcing_and_rate.py`](../../scripts/uc/US/us05_sourcing_and_rate.py)

## When it runs
Monthly, on each new invoice, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `tax_amount_wrong` | Row amount ≠ net × rate / 100 (± $0.05) |
| `rate_drift` | Row rate ≠ the configured jurisdiction rate |
| `state_sourcing_mismatch` | Row state ≠ customer's state |
| `local_sourcing_mismatch` | Destination-sourced county row for a customer in another county (city→county table) |
| `local_rate_unconfigured` (context) | Taxed customers in a county with no local jurisdiction |

## How to explain the result
The Stark County pattern has two readings: the sourcing setting is wrong (Ohio may source in-state
deliveries to the seller), or customers were charged the wrong county. It needs a sourcing ruling.

## Limits
Destination comes from the customer's address (no ship-to on invoices). Rates are manual by design
(not a bug).
