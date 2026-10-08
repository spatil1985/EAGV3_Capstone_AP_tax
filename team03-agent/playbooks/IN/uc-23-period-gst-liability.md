---
id: uc-23
title: Period GST liability (GSTR-3B)
capability: tax_liability
description: >-
  UC-23 (India, GST): computes the GST payable for the last return period — output tax by head
  (IGST, CGST, SGST, cess) less eligible input credit used in the statutory order, the cash
  payable per head, reverse-charge tax (cash only), the Rule 86B 1% cash floor, and whether the
  period's GSTR-3B row agrees with the ledger.
questions:
  - "How much GST do we owe for this month, under each head, and how much of it must be paid in cash?"
  - "What is our tax liability this period?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Invoice.list, CreditNote.list, Bill.list, VendorCredit.list, Party.list, Item.list, GSTReturn.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: scripts.uc.IN.uc23_period_gst_liability:PeriodGstLiability
tools: [Invoice.list, CreditNote.list, Bill.list, VendorCredit.list, Party.list, Item.list, GSTReturn.list]
escalate: digest
spec: docs/usecases/IN/uc-23-period-gst-liability.md
---

# UC-23 · Period GST liability (GSTR-3B) — SOP

**Full spec:** [`docs/usecases/IN/uc-23-period-gst-liability.md`](../../docs/usecases/IN/uc-23-period-gst-liability.md)
**Code:** [`scripts/uc/IN/uc23_period_gst_liability.py`](../../scripts/uc/IN/uc23_period_gst_liability.py)

## When it runs
Monthly on the 15th (ready before the 20th due date) and again on the 19th, and on request.
The period is the month before the run date; `--as-of` picks another.

## What it computes
1. Output tax by head from posted sales in the period, less in-window outward credit notes.
2. Eligible credit from posted, ITC-eligible, not IMS-rejected bills, less s.17(5) blocked lines
   and registered-vendor credit notes.
3. Credit used in the s.49 / s.49A / Rule 88A order; the rest is cash.
4. Rule 86B: taxable outward > ₹50 lakh → at least 1% of output tax in cash.
5. The GSTR-3B row as an oracle.

| Rule | Row |
|---|---|
| `head_payable` (context) | One per head: output, credit used, cash payable, credit carried forward |
| `rcm_cash_liability` | Reverse-charge tax for the period, cash only |
| `rule_86b_cash_floor` | Cash below the 1% floor |
| `stored_value_mismatch` | The GSTR-3B row disagrees with the ledger by more than ₹1 |
| `stored_value_mismatch` (per document) | Tax can't be sourced; excluded from totals |

## How to explain the result
Lead with total cash payable and the split by head; then Rule 86B and whether the return row
agrees. Cite the `head_payable` rows for every number.

## Limits
Rule 37 and Rule 42/43 reversals are not netted here (UC-01; UC-08/15 are blocked). GSTR-3B rows
on this tenant are round figures that don't reconcile (spec §6).
