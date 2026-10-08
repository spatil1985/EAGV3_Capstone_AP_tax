---
id: uc-38
title: Cash payments above the s.40A(3) limit
capability: cash_limit
description: >-
  UC-38 (India): finds cash paid to one vendor in one day above ₹10,000 (₹35,000 for goods-carriage
  hire) — payments in cash and expenses paid through cash or petty-cash accounts — which income tax
  disallows in full, with the tax effect; open bills set to be paid in cash above the limit; and
  payroll-like cash expenses (count only).
questions:
  - "Are we paying any vendor in cash above the limit, and losing the tax deduction for it?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [PaymentMade.list, Expense.list, Bill.list, BankAccount.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: payment_made.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc38_cash_payment_limits:CashPaymentLimits
tools: [PaymentMade.list, Expense.list, Bill.list, BankAccount.list]
escalate: digest
spec: docs/usecases/IN/uc-38-cash-payment-limits.md
---

# UC-38 · Cash payments above the s.40A(3) limit — SOP

**Full spec:** [`docs/usecases/IN/uc-38-cash-payment-limits.md`](../../docs/usecases/IN/uc-38-cash-payment-limits.md)
**Code:** [`scripts/uc/IN/uc38_cash_payment_limits.py`](../../scripts/uc/IN/uc38_cash_payment_limits.py)

## When it runs
Monthly, on each cash payment or cash-mode bill approval, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `cash_payment_disallowed` | Cash to one vendor in one day above ₹10,000 (₹35,000 goods carriage); tax effect at the company rate |
| `cash_payment_planned` | Open bill with `payment_gateway = cash` and balance above the limit |
| `cash_payment_wages` | Payroll-like accounts paid in cash (count and amount only) |

Daily totals are per vendor, so splitting a payment the same day doesn't avoid the limit.

## How to explain the result
Lead with what is already disallowed and its tax cost, then the bills to pay by bank instead.
Rule 6DD exceptions aren't in the data; mention them if the user names one.

## Limits
1961 Act numbering (confirm). The 25.17% tax rate assumes the s.115BAA regime.
