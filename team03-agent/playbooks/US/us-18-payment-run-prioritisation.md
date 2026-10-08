---
id: us-18
title: Payment-run prioritisation (US)
capability: payment_run_us
description: >-
  US-18 (US): builds this week's payment plan — pay first where a week's delay costs the most (overdue
  terms, early-payment discounts about to lapse), net off vendor credits, hold unapproved bills and
  possible duplicates, and reduce payments to 1099 vendors with no W-9 by 24% backup withholding.
questions:
  - "Which bills should we pay first this week, and which should we hold or withhold on?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Bill.list, Party.list, VendorCredit.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: on_request}
compute: scripts.uc.US.us18_payment_run:PaymentRunPrioritisationUS
tools: [Bill.list, Party.list, VendorCredit.list]
escalate: digest
spec: docs/usecases/US/us-18-payment-run-prioritisation.md
---

# US-18 · Payment-run prioritisation (US) — SOP

**Full spec:** [`docs/usecases/US/us-18-payment-run-prioritisation.md`](../../docs/usecases/US/us-18-payment-run-prioritisation.md) ·
India counterpart [`UC-42`](../IN/uc-42-payment-run-prioritisation.md)
**Code:** [`scripts/uc/US/us18_payment_run.py`](../../scripts/uc/US/us18_payment_run.py) ·
engine in [`scripts/uc/common/payment_run.py`](../../scripts/uc/common/payment_run.py)

## When it runs
Weekly, and on request.

## What it produces
One row per bill needing a decision: `pay_now` (cost of a week's delay: contractual lateness at a
nominal rate, or a lapsing early-payment discount), `net_off` (vendor credits cover it), `hold`
(approval pending/rejected, possible duplicate). A 1099 vendor with no W-9 is paid net of 24% backup
withholding (US-06).

## How to explain the result
There is no prompt-payment statute or input credit at stake: the plan is about terms, discounts and
withholding. Most open bills are long overdue — ask whether they are disputed (no dispute flag exists).

## Limits
The plan never pays anything; payments are T3 writes. No discount terms exist on this tenant today.
