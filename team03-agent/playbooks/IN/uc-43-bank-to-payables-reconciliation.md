---
id: uc-43
title: Bank-to-payables reconciliation
capability: bank_recon
description: >-
  UC-43 (India): matches bank debits to recorded vendor payments and reports money that left the bank
  to a vendor with no payment in AP (and open bills of the same amount that could be paid again), AP
  payments that never reached the bank, debits marked matched to no voucher, and unidentified debits.
questions:
  - "Does every vendor payment in the bank match a payment in our books, and the other way round?"
status: live
blocked_by: null
tax_regimes: [gst]          # the US tenant runs its own US-xx instance
requires:
  tools: [BankTransaction.list, PaymentMade.list, Party.list, Bill.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: bank_transaction.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc43_bank_to_payables:BankToPayables
tools: [BankTransaction.list, PaymentMade.list, Party.list, Bill.list]
escalate: digest
spec: docs/usecases/IN/uc-43-bank-to-payables-reconciliation.md
---

# UC-43 · Bank-to-payables reconciliation — SOP

**Full spec:** [`docs/usecases/IN/uc-43-bank-to-payables-reconciliation.md`](../../docs/usecases/IN/uc-43-bank-to-payables-reconciliation.md)
**Code:** [`scripts/uc/IN/uc43_bank_to_payables.py`](../../scripts/uc/IN/uc43_bank_to_payables.py) ·
engine in [`scripts/uc/common/bank_recon.py`](../../scripts/uc/common/bank_recon.py)

## When it runs
Weekly and at month end, on each bank debit, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `bank_debit_unrecorded` | Debit to a vendor payee with no matching payment (voucher, reference, or payee + amount ±1 + date ±5 days) |
| `payment_not_in_bank` | AP payments inside the bank window with no debit (aggregate) |
| `match_without_voucher` (data_quality) | Debits marked `matched` with no voucher (aggregate) |
| `unidentified_debit` | No payee, uncategorised, older than 7 days |

## How to explain the result
State the bank window and counts: the feed may be partial. Flag any open bill whose amount equals
an unrecorded debit, since it may be paid twice.

## Limits
`PaymentMade.paid_through` is null, so payments can't be tied to a bank account; matching runs across
all accounts.
