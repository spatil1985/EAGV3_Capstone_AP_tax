---
id: uc-01
title: Rule 37 180-day ITC reversal
capability: rule37
description: >-
  UC-01 (India, GST): finds unpaid, ITC-eligible supplier bills older than 180 days, whose
  input credit must be reversed under s.16(2) / Rule 37 with 18% p.a. interest. Returns the
  reversal and interest per bill, the total, and the bills about to cross day 180.
questions:
  - "Which unpaid bills are about to cost me my input credit, and how much?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.IN.uc01_rule37_itc_reversal:Rule37Reversal
tools: [Bill.list]
escalate: digest
spec: docs/usecases/IN/uc-01-rule-37-itc-reversal.md
---

# UC-01 · Rule 37 180-day ITC reversal — SOP

**Full spec:** [`docs/usecases/IN/uc-01-rule-37-itc-reversal.md`](../../docs/usecases/IN/uc-01-rule-37-itc-reversal.md)
**Code:** [`scripts/uc/IN/uc01_rule37_itc_reversal.py`](../../scripts/uc/IN/uc01_rule37_itc_reversal.py)

## When it runs
Daily (the 180-day line moves every day, with no document event), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `rule_37_180_day` | ITC-eligible bill, posted, `balance_due > 0`, older than 180 days. Reversal = the bill's ITC; interest = ITC × 18% × (age − 180) / 365 |
| `stored_value_mismatch` (data_quality) | An in-scope bill whose tax reconciles neither from `taxes[]` nor from valid item lines; excluded from totals |

Tax is sourced per document (IN README, Correction 2026-09-30): `taxes[]` when it
reconciles to `total_tax`, otherwise valid item lines. Bills crossing day 180 in the next
30 days are listed in the run context, not as findings.

## How to explain the result
Lead with "N unpaid bills have crossed 180 days; total ITC ₹X, interest ₹Y". For each
bill give its number, vendor, age and the three amounts. A partially paid bill is reversed
in full (the conservative reading, spec §10); the pro-rata figure is in its details.

## Limits
Never posts the reversal (JournalEntry is read-only). Does not check whether a reversal
was already filed in a return, and does not track re-availment after payment.
