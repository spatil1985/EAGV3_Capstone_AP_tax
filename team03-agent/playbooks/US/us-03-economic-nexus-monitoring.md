---
id: us-03
title: Economic nexus monitoring
capability: nexus
description: >-
  US-03 (US, sales tax): adds up this calendar year's sales and transactions by destination state and
  compares them with each state's economic-nexus threshold — states crossed or at 80% where we aren't
  registered, sales into states nobody monitors — and checks the platform's nexus counters against
  the invoices.
questions:
  - "Are we approaching a new state's sales tax registration obligation anywhere?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Invoice.list, Party.list, TaxNexus.list, TaxJurisdiction.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: scripts.uc.US.us03_economic_nexus:EconomicNexus
tools: [Invoice.list, Party.list, TaxNexus.list, TaxJurisdiction.list]
escalate: digest
spec: docs/usecases/US/us-03-economic-nexus-monitoring.md
---

# US-03 · Economic nexus monitoring — SOP

**Full spec:** [`docs/usecases/US/us-03-economic-nexus-monitoring.md`](../../docs/usecases/US/us-03-economic-nexus-monitoring.md)
**Code:** [`scripts/uc/US/us03_economic_nexus.py`](../../scripts/uc/US/us03_economic_nexus.py)

## When it runs
Monthly, on an invoice to an unregistered state, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `nexus_threshold_crossed` | Unregistered state over its amount or transaction threshold |
| `nexus_threshold_approaching` | Unregistered state at ≥ 80% of either |
| `nexus_unmonitored` | Sales into a state with no TaxNexus row |
| `stored_value_mismatch` (data_quality) | `TaxNexus.ytd_*` ≠ recomputed from invoices (N4 regression guard) |
| `missing_required_field` (data_quality) | Invoice with no tax row and a customer with no address |

## How to explain the result
Say which states we sell into and where we're registered; a crossing means collecting from the
crossing date, or paying the tax ourselves.

## Limits
Prior-year sales also count toward most thresholds; only the current year is in the ledger.
