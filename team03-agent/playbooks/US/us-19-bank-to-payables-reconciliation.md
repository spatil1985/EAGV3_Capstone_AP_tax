---
id: us-19
title: Bank-to-payables reconciliation (US)
capability: bank_recon_us
description: >-
  US-19 (US): matches bank debits to recorded vendor payments (following the platform's voucher links)
  and reports AP payments inside the bank window that never reached the bank, debits to vendors with no
  payment in AP, and unidentified debits with no payee, voucher or category.
questions:
  - "Does every vendor payment in the bank match a payment in our books, and the other way round?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [BankTransaction.list, PaymentMade.list, Party.list, Bill.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: bank_transaction.created}
  - {kind: on_request}
compute: scripts.uc.US.us19_bank_to_payables:BankToPayablesUS
tools: [BankTransaction.list, PaymentMade.list, Party.list, Bill.list]
escalate: digest
spec: docs/usecases/US/us-19-bank-to-payables-reconciliation.md
---

# US-19 · Bank-to-payables reconciliation (US) — SOP

**Full spec:** [`docs/usecases/US/us-19-bank-to-payables-reconciliation.md`](../../docs/usecases/US/us-19-bank-to-payables-reconciliation.md) ·
algorithm in [`UC-43`](../IN/uc-43-bank-to-payables-reconciliation.md)
**Code:** [`scripts/uc/US/us19_bank_to_payables.py`](../../scripts/uc/US/us19_bank_to_payables.py) ·
engine in [`scripts/uc/common/bank_recon.py`](../../scripts/uc/common/bank_recon.py)

## When it runs
Weekly, on each bank debit, and on request.

## What it checks
As UC-43: `bank_debit_unrecorded`, `payment_not_in_bank`, `match_without_voucher`, `unidentified_debit`.
Voucher links are trusted here; there is no payee on bank debits.

## How to explain the result
State the bank window (the feed covers only part of the year). Unmatched payments may have gone out
from an account not in the feed (the credit card) — ask; `paid_through` is null.

## Limits
As UC-43.
