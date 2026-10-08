---
id: uc-15
title: "Clinic: Rule 42/43 ITC apportionment"
capability: apportionment_clinic
description: >-
  UC-15 (India, clinic vertical): how much input credit a clinic may keep when most of its
  supplies are exempt — Rule 42 for inputs (as UC-08) and Rule 43 for common capital goods
  (credit spread over 60 months, the exempt share reversed monthly), plus the room-rent
  stream taxed at 5% without ITC. Blocked: computable, but the reversal can't be posted and
  no clinic tenant exists.
questions:
  - "Of all the GST we paid on purchases, how much can we actually keep?"
status: blocked
blocked_by: "F18 / N273 (no apportionment engine or reversal posting; JournalEntry is read-only) and N426 T4.1; no clinic tenant"
tax_regimes: [gst]
requires:
  tools: [Bill.list, Invoice.list, Item.list]
  verticals: [clinic]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: null
tools: [Bill.list, Invoice.list, Item.list]
escalate: never
spec: docs/usecases/IN/uc-15-rule-42-43-apportionment-clinic.md
---

# UC-15 · Clinic: Rule 42/43 ITC apportionment — blocked

**Full spec:** [`docs/usecases/IN/uc-15-rule-42-43-apportionment-clinic.md`](../../docs/usecases/IN/uc-15-rule-42-43-apportionment-clinic.md)

## Why it is blocked
- **Posting:** as UC-08 — no apportionment engine and `JournalEntry` is read-only (F18,
  board N273; N426 T4.1).
- **Tenant:** no clinic tenant; Suryodaya is manufacturing.

## What the agent says when asked
Rule 42 works as in UC-08 (E/F from UC-14). Rule 43: common capital-goods credit is spread
over 60 months (Tm = A ÷ 60), and the exempt share Te = (E ÷ F) × Tr is reversed each month.
Room rent above ₹5,000/day is taxed at 5% with no ITC. The reversal can be computed, not posted.

## To unblock
F18 / N426 T4.1, a clinic tenant, and a capital-goods marker on items or bills. Then write
`scripts/uc/IN/uc15_*.py` reusing `common/exempt_split.py` and set `status: live`.
