---
id: us-21
title: Unclaimed property (escheat)
capability: escheat
description: >-
  US-21 (US): finds vendor payments that never cleared the bank (outstanding cheques, returned
  transfers) and ages them against the owner state's dormancy period — due-diligence notices due
  within 120 days, items already reportable to the state — and flags items whose owner state is
  unknown. Payments outside the bank feed are "unknown", not outstanding.
questions:
  - "Do we hold money owed to vendors that nobody has claimed, and must we report it to a state?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [PaymentMade.list, BankTransaction.list, Party.list, OrgProfile.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: scripts.uc.US.us21_unclaimed_property:UnclaimedProperty
tools: [PaymentMade.list, BankTransaction.list, Party.list, OrgProfile.list]
escalate: digest
spec: docs/usecases/US/us-21-unclaimed-property-escheat.md
---

# US-21 · Unclaimed property (escheat) — SOP

**Full spec:** [`docs/usecases/US/us-21-unclaimed-property-escheat.md`](../../docs/usecases/US/us-21-unclaimed-property-escheat.md)
**Code:** [`scripts/uc/US/us21_unclaimed_property.py`](../../scripts/uc/US/us21_unclaimed_property.py)

## When it runs
Monthly, plus before each state's annual report date, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `escheat_due_diligence` | Outstanding payment within 120 days of dormancy: send owner notices |
| `escheat_reportable` | Past dormancy: report and remit to the owner state |
| `escheat_owner_state_unknown` | No vendor address; the holder's state takes it |

Outstanding = no clearing bank debit (US-19 matching) after a 60-day grace. Dormancy years per state
are rulebook values to confirm.

## How to explain the result
All payments here are bank transfers under a year old, so 0 is expected; say when the earliest item
could become reportable.

## Limits
The bank feed covers only June–August 2026; clearing outside it is unknown. Formation state isn't modelled.
