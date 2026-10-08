---
id: us-11
title: Sales tax paid on exempt purchases
capability: exempt_purchases
description: >-
  US-11 (US): finds purchases where a vendor charged sales tax although the purchase was exempt
  (manufacturing direct use, resale), with the tax to recover and the refund window, and vendors to
  whom we never gave an exemption certificate. The mirror of US-02 (untaxed purchases that are taxable).
questions:
  - "Have we paid sales tax to vendors on purchases that should have been tax-free, and can we still get it back?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Bill.list, Expense.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.US.us11_tax_on_exempt_purchases:TaxOnExemptPurchases
tools: [Bill.list, Expense.list]
escalate: digest
spec: docs/usecases/US/us-11-sales-tax-on-exempt-purchases.md
---

# US-11 · Sales tax paid on exempt purchases — SOP

**Full spec:** [`docs/usecases/US/us-11-sales-tax-on-exempt-purchases.md`](../../docs/usecases/US/us-11-sales-tax-on-exempt-purchases.md)
**Code:** [`scripts/uc/US/us11_tax_on_exempt_purchases.py`](../../scripts/uc/US/us11_tax_on_exempt_purchases.py) ·
line table in [`scripts/uc/common/us_purchase_tax.py`](../../scripts/uc/common/us_purchase_tax.py)

## When it runs
Monthly (and annually for refund windows), on each vendor-taxed bill, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `tax_paid_on_exempt_purchase` | Vendor-taxed bill line or expense in an exempt class; exposure = the tax |
| `exemption_certificate_not_issued` | No certificate from us on file for that vendor (root cause) |
| `refund_window_closing` | Purchase + the state's window (Ohio 4 years) within 180 days |

Certificates we issue live in `config/overrides/exemption_certificates_issued.yaml`; the platform only
models certificates received from customers.

## How to explain the result
On Keystone no vendor charges sales tax at all, so 0 is the right answer; the opposite problem is US-02.

## Limits
Line classification is a playbook table (CPA confirmation needed). Nonprofit/government buyer status
needs a non-manufacturing tenant.
