---
id: uc-17
title: Composition scheme eligibility and breach
capability: composition
description: >-
  UC-17 (India): whether we are still eligible for the GST composition scheme (s.10 — turnover
  up to ₹1.5 crore, no inter-state outward supply) and about to fall out of it. Blocked: the
  organisation's own tax mode and preceding-FY turnover are not in the data. A sub-check on
  bills from composition suppliers (they can't charge GST, and no ITC is available on them)
  is buildable but not built here.
questions:
  - "Are we still eligible for the composition scheme, and are we about to fall out of it?"
status: blocked
blocked_by: "N426 T4.3 / F20 — no company tax profile (registration type, preceding-FY turnover)"
tax_regimes: [gst]
requires:
  tools: [Bill.list, Invoice.list, OrgProfile.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: null
tools: [Bill.list, Invoice.list, OrgProfile.list]
escalate: never
spec: docs/usecases/IN/uc-17-composition-scheme.md
---

# UC-17 · Composition scheme eligibility and breach — blocked

**Full spec:** [`docs/usecases/IN/uc-17-composition-scheme.md`](../../docs/usecases/IN/uc-17-composition-scheme.md)

## Why it is blocked
`Company` and `OrgProfile` carry no registration type (regular vs composition) and no
preceding-FY turnover, so eligibility can't be evaluated (N426 T4.3; F20 not filed
separately). Suryodaya is in any case a regular taxpayer with inter-state supplies.

## What the agent says when asked
Explain s.10: ₹1.5 crore preceding-FY turnover (₹75 lakh in special-category states), 1% for
manufacturers and traders, no inter-state outward supply, no tax collected and no ITC. Say
the platform does not hold the organisation's own tax mode or turnover.

## Buildable sub-check (not built)
Spec §5 steps 4+: bills with `gst_treatment = business_composition` that show GST (a
composition supplier can't charge it) and any ITC claimed on them. UC-03's
`rcm_flag_spurious` already surfaces some of these bills.

## To unblock
A company tax profile (N426 T4.3). Then write `scripts/uc/IN/uc17_*.py` and set `status: live`.
