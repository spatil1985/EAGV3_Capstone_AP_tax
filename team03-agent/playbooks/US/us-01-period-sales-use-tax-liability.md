---
id: us-01
title: Period sales and use tax liability
capability: tax_liability_us
description: >-
  US-01 (US, sales and use tax): computes sales tax collected by jurisdiction for the year to date
  from invoice tax rows, reconciles each jurisdiction to the cent (and by invoice count) with the
  platform's sales-tax liability report, and reports use tax accrued on purchases.
questions:
  - "What is our sales and use tax liability this period, by jurisdiction?"
  - "What is our tax liability this period?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Invoice.list, Bill.list, TaxJurisdiction.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: scripts.uc.US.us01_period_sales_use_tax:PeriodSalesUseTax
tools: [Invoice.list, Bill.list, TaxJurisdiction.list]
escalate: digest
spec: docs/usecases/US/us-01-period-sales-use-tax-liability.md
---

# US-01 · Period sales and use tax liability — SOP

**Full spec:** [`docs/usecases/US/us-01-period-sales-use-tax-liability.md`](../../docs/usecases/US/us-01-period-sales-use-tax-liability.md)
**Code:** [`scripts/uc/US/us01_period_sales_use_tax.py`](../../scripts/uc/US/us01_period_sales_use_tax.py)

## When it runs
Monthly, and on request. Window: 1 January to the run date.

## What it computes
| Rule | Row |
|---|---|
| `tax_liability` (context) | One per jurisdiction: tax collected, invoice count, the report's figures, reconciled? |
| `use_tax_accrued` (context) | `Bill.use_tax_accrued` in the window |
| `stored_value_mismatch` (data_quality) | Amount or invoice count disagrees with the liability report |

Oracle: `GET /api/accounting/reports/sales-tax-liability` (REST, allowlisted; requested as MCP in N426).

## How to explain the result
Lead with the total and whether it matches the platform report to the cent. The Stark County
count gap (102 vs 71) is the report counting exempt rows; amounts agree. Use tax of $0 points to US-02.

## Limits
Rates are hand-entered (`rate_source: manual`); consistency is checked, not "the correct rate".
