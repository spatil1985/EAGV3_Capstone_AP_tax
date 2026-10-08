---
id: uc-33
title: GST credit on expense claims
capability: expense_credit
description: >-
  UC-33 (India, GST): finds expense claims taking GST credit the law blocks — personal expenses
  (s.17(5)(g)), blocked categories, GST on salaries/PF/loans (not supplies), no supplier GSTIN — plus
  reverse charge on registered suppliers, outward categories on purchases, and expense tax larger
  than any GST rate allows (excluded from totals).
questions:
  - "Are we claiming GST credit on expense claims where the law says we can't?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Expense.list, Party.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: expense.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc33_expense_claims_itc:ExpenseClaimsItc
tools: [Expense.list, Party.list]
escalate: digest
spec: docs/usecases/IN/uc-33-expense-claims-itc.md
---

# UC-33 · GST credit on expense claims — SOP

**Full spec:** [`docs/usecases/IN/uc-33-expense-claims-itc.md`](../../docs/usecases/IN/uc-33-expense-claims-itc.md)
**Code:** [`scripts/uc/IN/uc33_expense_claims_itc.py`](../../scripts/uc/IN/uc33_expense_claims_itc.py)

## When it runs
Monthly, when an expense is created, and on request.

## What it checks
One finding per expense, led by its most serious rule (others in `also`):

| Rule | Finding |
|---|---|
| `itc_on_personal_expense` | `is_personal` with credit claimed (s.17(5)(g)) |
| `itc_blocked_category` | Account/description in a s.17(5) category (UC-02 table) |
| `gst_on_non_supply` | Tax on salary, wages, PF/ESI, loan or interest accounts |
| `itc_without_supplier_gstin` | Credit claimed, no GSTIN on expense or vendor |
| `rcm_on_registered_supplier` | Reverse charge on a `business_gst` supplier |
| `classification_conflict` | `sez`/`deemed_export` on a purchase |
| `tax_exceeds_possible_rate` (data_quality) | Tax above 40% of the amount: excluded from totals |

## How to explain the result
Lead with the blocked personal credit; say how many records were excluded as implausible.

## Limits
Never reads SalarySlip (prohibited); payroll accounts on Expense are reported only for the GST
anomaly. Descriptions are seed text, so category matching relies on account names.
