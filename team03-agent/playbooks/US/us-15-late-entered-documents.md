---
id: us-15
title: Late-entered documents (US)
capability: period_integrity_us
description: >-
  US-15 (US): finds invoices entered after their month's sales-tax return was due (that tax was
  probably missing from the filed return — amend it), documents entered into a locked or closed period,
  and documents back-dated more than 30 days, aggregated by document type and month.
questions:
  - "Has anyone entered or back-dated a document into a month we've already reported?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [TransactionLock.list, AccountingPeriod.list, OrgProfile.list, Invoice.list, Bill.list, CreditNote.list, VendorCredit.list, PaymentMade.list, Expense.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: event, on: document.created}
  - {kind: on_request}
compute: scripts.uc.US.us15_late_entered_documents:LateEnteredDocumentsUS
tools: [TransactionLock.list, AccountingPeriod.list, OrgProfile.list, Invoice.list, Bill.list, CreditNote.list, VendorCredit.list, PaymentMade.list, Expense.list]
escalate: digest
spec: docs/usecases/US/us-15-late-entered-documents.md
---

# US-15 · Late-entered documents (US) — SOP

**Full spec:** [`docs/usecases/US/us-15-late-entered-documents.md`](../../docs/usecases/US/us-15-late-entered-documents.md) ·
India counterpart [`UC-28`](../IN/uc-28-late-entered-documents.md)
**Code:** [`scripts/uc/US/us15_late_entered_documents.py`](../../scripts/uc/US/us15_late_entered_documents.py)

## When it runs
Daily, and when a back-dated document is created.

## What it checks
Aggregated per document type and month:

| Rule | Finding |
|---|---|
| `entered_into_reported_period` | Invoice entered after its month's return was due (US-14 calendar) |
| `entered_into_closed_period` / `entered_into_locked_period` | Into a closed period or past a lock |
| `backdated_document` | Entered more than 30 days after its date |

## How to explain the result
"Probably filed": there is no return record, so say that if the returns were filed on time they need
amending. Recommend month-end close: nothing is locked or closed on this tenant.

## Limits
Whether January–August returns were filed, and from what figures, can't be known from AgentSwitch.
