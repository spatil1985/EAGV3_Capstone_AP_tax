---
id: uc-27
title: GST return filing timeliness
capability: filing_calendar
description: >-
  UC-27 (India, GST): lists GSTR-1 and GSTR-3B returns that are overdue or were filed late, with the
  s.47 late fee and the s.50 interest on cash paid late (from UC-23's computed cash when the return
  holds no figure), closed periods with no return row, the Rule 138E e-way bill block risk, and
  GSTR-2B rows that carry a meaningless filing status.
questions:
  - "Which GST returns are due or overdue, and what is lateness costing us?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [GSTReturn.list, Invoice.list, CreditNote.list, Bill.list, VendorCredit.list, Party.list, Item.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.IN.uc27_return_filing_timeliness:ReturnFilingTimeliness
tools: [GSTReturn.list, Invoice.list, CreditNote.list, Bill.list, VendorCredit.list, Party.list, Item.list]
escalate: digest
spec: docs/usecases/IN/uc-27-return-filing-timeliness.md
---

# UC-27 · GST return filing timeliness — SOP

**Full spec:** [`docs/usecases/IN/uc-27-return-filing-timeliness.md`](../../docs/usecases/IN/uc-27-return-filing-timeliness.md)
**Code:** [`scripts/uc/IN/uc27_return_filing_timeliness.py`](../../scripts/uc/IN/uc27_return_filing_timeliness.py)

## When it runs
Daily (late fees and interest grow daily; reminders at T−5 and T−1), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `return_overdue` | Unfiled past due: days late × ₹50 (capped) late fee; for 3B, cash × 18% × days / 365 |
| `return_filed_late` | Filed after the due date (historical) |
| `return_not_generated` | Closed periods since the ledger starts with no return row (aggregate per type) |
| `eway_block_risk` | A 3B outstanding and the next due within 30 days (Rule 138E) |
| `return_status_meaningless` (data_quality) | GSTR-2B with a filing status or due date |

## How to explain the result
Lead with what is overdue and what it costs today, then the knock-ons (Rule 59(6), Rule 138E).
Say the interest base is UC-23's computed cash, since `net_tax_payable` is empty.

## Limits
The late-fee cap assumes turnover above ₹5 crore (₹10,000); UC-29 decides the band. Returns filed
outside the platform can't be seen.
