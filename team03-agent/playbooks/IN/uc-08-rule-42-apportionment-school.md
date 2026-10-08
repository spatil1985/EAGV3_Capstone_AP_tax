---
id: uc-08
title: "School: Rule 42 ITC apportionment"
capability: apportionment_school
description: >-
  UC-08 (India, school vertical): how much common input credit a school with exempt and
  taxable income may keep under Rule 42 (D1 = E/F × common credit, D2 = 5% for non-business
  use), and the annual true-up. Blocked: the agent can compute the reversal but the platform
  can't post it, and no school tenant exists.
questions:
  - "How much of our input credit are we actually entitled to keep?"
status: blocked
blocked_by: "F18 / N273 (no ITC apportionment or reversal posting; JournalEntry is read-only) and N426 T4.1; no school tenant"
tax_regimes: [gst]
requires:
  tools: [Bill.list, Invoice.list, Item.list]
  verticals: [school]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: null
tools: [Bill.list, Invoice.list, Item.list]
escalate: never
spec: docs/usecases/IN/uc-08-rule-42-apportionment-school.md
---

# UC-08 · School: Rule 42 ITC apportionment — blocked

**Full spec:** [`docs/usecases/IN/uc-08-rule-42-apportionment-school.md`](../../docs/usecases/IN/uc-08-rule-42-apportionment-school.md)

## Why it is blocked
- **Posting:** `JournalEntry` is read-only for `finance_user`, and the platform has no
  apportionment engine (F18, board N273; `IndirectTax.reverse` asked for as N426 T4.1).
  A computed reversal (the spec's live example: ₹4,05,733.76 for September) would leave the
  books wrong until a person posts it.
- **Tenant:** no school tenant exists; Suryodaya is manufacturing.

## What the agent says when asked
Explain Rule 42 (T → C1 → C2 → D1 = E/F × C2, D2 = 5% of C2, C3 = C2 − D1 − D2), that the
E/F split comes from UC-07, and that the reversal can be computed but not posted. Point to
the spec's worked figures.

## To unblock
F18 / N426 T4.1 delivered, plus a school tenant (or OrgProfile.industry = education). Then
write `scripts/uc/IN/uc08_*.py` reusing `common/exempt_split.py` (E/F) and UC-02's blocked
lines (T3), and set `status: live`.
