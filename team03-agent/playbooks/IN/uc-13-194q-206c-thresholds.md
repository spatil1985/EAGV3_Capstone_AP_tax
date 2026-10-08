---
id: uc-13
title: 194Q goods-purchase TDS thresholds (buy and sell side)
capability: tds_194q
description: >-
  UC-13 (India): tracks FY-cumulative goods purchases per vendor against the ₹50 lakh s.194Q
  line (bills past it without 0.1% TDS, vendors at 80% of it), and mirrors it on sales:
  customers who bought over ₹50 lakh of goods from us but whose payments show no TDS (a 26AS
  reconciliation break). s.206C(1H) is treated as omitted from April 2025.
questions:
  - "Which suppliers or customers have we crossed the ₹50 lakh line with?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Invoice.list, PaymentReceived.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc13_194q_thresholds:Thresholds194Q
tools: [Bill.list, Invoice.list, PaymentReceived.list]
escalate: digest
spec: docs/usecases/IN/uc-13-194q-206c-thresholds.md
---

# UC-13 · 194Q goods-purchase TDS thresholds — SOP

**Full spec:** [`docs/usecases/IN/uc-13-194q-206c-thresholds.md`](../../docs/usecases/IN/uc-13-194q-206c-thresholds.md)
**Code:** [`scripts/uc/IN/uc13_194q_thresholds.py`](../../scripts/uc/IN/uc13_194q_thresholds.py)

## When it runs
Monthly, when a bill arrives, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `194q_not_deducted` | Buy side: a bill at or after the vendor's FY goods base crosses ₹50 lakh, with no TDS. Expected = 0.1% of the excess |
| `194q_approaching` | Buy side: FY goods base between 80% and 100% of the line |
| `194q_customer_not_deducting` | Sell side: customer's FY goods purchases from us past ₹50 lakh, payments record less TDS than 0.1% of the excess |

Bases are line `taxable_amount` (GST excluded, never `grand_total` — N7). Blank-HSN lines
count as goods; how many is reported.

## How to explain the result
Every buy-side finding is subject to our preceding-FY turnover exceeding ₹10 crore, which
the data doesn't hold (N426 T4.3). Sell-side findings are reconciliation checks with the
customer, not our liability.

## Limits
Income-tax Act 1961 numbering; the 2025 Act renumbers it. s.206C(1H) TCS is treated as
omitted from 1 April 2025 (confirm).
