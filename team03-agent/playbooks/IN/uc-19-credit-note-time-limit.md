---
id: uc-19
title: Credit-note s.34(2) time limit
capability: credit_note_window
description: >-
  UC-19 (India): tells how many days are left to issue tax-effective credit notes against an
  FY's sales (30 November after the FY ends), with the invoices still eligible; flags credit
  notes issued after their window (GST lost) and credit notes we issued against purchase
  invoices (the wrong document).
questions:
  - "Which returns can we still issue a tax-effective credit note for?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [CreditNote.list, Invoice.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: credit_note.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc19_credit_note_window:CreditNoteTimeLimit
tools: [CreditNote.list, Invoice.list]
escalate: digest
spec: docs/usecases/IN/uc-19-credit-note-time-limit.md
---

# UC-19 · Credit-note s.34(2) time limit — SOP

**Full spec:** [`docs/usecases/IN/uc-19-credit-note-time-limit.md`](../../docs/usecases/IN/uc-19-credit-note-time-limit.md)
**Code:** [`scripts/uc/IN/uc19_credit_note_window.py`](../../scripts/uc/IN/uc19_credit_note_window.py)

## When it runs
Monthly (most useful Aug–Nov), when a credit note is created, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `window_closing` | An FY whose cutoff (30 Nov after FY end) is ≤ 90 days away: count and value of receivable invoices still eligible |
| `credit_note_out_of_window` | A credit note dated after its original invoice's cutoff: its GST can't be reduced |
| `classification_conflict` | A credit note linked to a payable invoice (PINV) |

The cutoff month-day is effective-dated (30 Sep before Finance Act 2022, 30 Nov after).

## How to explain the result
Lead with the days left and the invoices still eligible. The annual-return date can bring
the cutoff earlier; it isn't in the data, so say "30 November or the annual return, if
filed earlier".

## Limits
CreditNote `taxes[]` is corrupt (N128) and stripped at fetch.
