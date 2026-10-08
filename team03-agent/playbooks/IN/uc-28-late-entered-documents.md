---
id: uc-28
title: Late-entered documents in filed or closed periods
capability: period_integrity
description: >-
  UC-28 (India): finds invoices, bills, credit notes, vendor credits, payments and expenses dated in
  a month whose GST returns are filed, or that is locked or closed, but entered after that happened;
  and documents entered more than 30 days after their date. Reports gaps where a filed month was not
  locked until later.
questions:
  - "Has anyone entered or back-dated a document into a month we've already filed or closed?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [GSTReturn.list, TransactionLock.list, AccountingPeriod.list, Invoice.list, Bill.list, CreditNote.list, VendorCredit.list, PaymentMade.list, Expense.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: event, on: document.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc28_late_entered_documents:LateEnteredDocuments
tools: [GSTReturn.list, TransactionLock.list, AccountingPeriod.list, Invoice.list, Bill.list, CreditNote.list, VendorCredit.list, PaymentMade.list, Expense.list]
escalate: digest
spec: docs/usecases/IN/uc-28-late-entered-documents.md
---

# UC-28 · Late-entered documents — SOP

**Full spec:** [`docs/usecases/IN/uc-28-late-entered-documents.md`](../../docs/usecases/IN/uc-28-late-entered-documents.md)
**Code:** [`scripts/uc/IN/uc28_late_entered_documents.py`](../../scripts/uc/IN/uc28_late_entered_documents.py) ·
shared in [`scripts/uc/common/period_integrity.py`](../../scripts/uc/common/period_integrity.py)

## When it runs
Daily, and when a document dated in a closed period is created.

## What it checks
| Rule | Finding |
|---|---|
| `entered_after_filing` | Dated in a filed GSTR-1/3B month, created after the filing date |
| `entered_into_locked_period` | Dated ≤ a TransactionLock's date (module scope), created after the lock |
| `entered_into_closed_period` | Dated in a closed AccountingPeriod, created after it closed |
| `backdated_document` | Created more than 30 days after its date (Rule 47) |

The run context lists control gaps: filed months that were locked or closed only later.

## How to explain the result
A filed-period entry belongs in the next return or GSTR-1A, with interest on understated tax. A
locked-period entry also means the platform didn't enforce its own lock.

## Limits
Lock reasons are seed text on most rows; only dates are used. Amendments (GST-32) are a
platform-documented gap.
