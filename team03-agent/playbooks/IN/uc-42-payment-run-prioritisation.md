---
id: uc-42
title: Payment-run prioritisation
capability: payment_run
description: >-
  UC-42 (India): builds this week's payment plan from open bills — pay first where a week's delay
  costs the most (MSME 45-day interest and s.43B(h), Rule 37 credit about to be reversed, overdue
  terms), net off vendors' open credits, and hold bills that are IMS-rejected, unapproved or possible
  duplicates. Cash-mode bills are flagged to be paid by bank.
questions:
  - "We can't pay everything this week. Which bills should we pay first to avoid penalties and lost credit, and which should we hold?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list, VendorCredit.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: on_request}
compute: scripts.uc.IN.uc42_payment_run:PaymentRunPrioritisation
tools: [Bill.list, Party.list, VendorCredit.list]
escalate: digest
spec: docs/usecases/IN/uc-42-payment-run-prioritisation.md
---

# UC-42 · Payment-run prioritisation — SOP

**Full spec:** [`docs/usecases/IN/uc-42-payment-run-prioritisation.md`](../../docs/usecases/IN/uc-42-payment-run-prioritisation.md)
**Code:** [`scripts/uc/IN/uc42_payment_run.py`](../../scripts/uc/IN/uc42_payment_run.py) ·
engine in [`scripts/uc/common/payment_run.py`](../../scripts/uc/common/payment_run.py)

## When it runs
Weekly (before the payment run), and on request.

## What it produces
One row per bill that needs a decision, ranked:

| Action | When |
|---|---|
| `pay_now` | A week's delay has a cost: MSME penal interest (+ s.43B(h)), Rule 37 reversal within 14 days, contractual lateness |
| `net_off` | The vendor's open credits cover the bill (UC-41) |
| `hold` | IMS-rejected, approval pending or rejected, or a possible duplicate (UC-05) |

Bills with no cost of delay this week are counted in the context ("pay by due date").

## How to explain the result
Give the total to pay this week, the top bills and why, what to hold, and the credits to apply first.
Pay cash-mode bills by bank (UC-38).

## Limits
The plan never pays anything; payments are T3 writes. Contractual late cost uses a nominal 12% when
terms carry no rate.
