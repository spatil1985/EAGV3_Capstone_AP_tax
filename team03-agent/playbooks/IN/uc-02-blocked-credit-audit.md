---
id: uc-02
title: Blocked credit audit (s.17(5))
capability: blocked_credit
description: >-
  UC-02 (India, GST): finds supplier-bill lines that claim input credit on categories
  s.17(5) blocks (motor vehicles, food and catering, club and fitness, works contracts on
  immovable property, gifts), with the credit at risk per line. Also flags bills marked
  ineligible that look like ordinary inputs, and lines with no HSN/SAC.
questions:
  - "Have we claimed credit on anything the law blocks?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Item.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: on_request}
compute: scripts.uc.IN.uc02_blocked_credit:BlockedCreditAudit
tools: [Bill.list, Item.list]
escalate: digest
spec: docs/usecases/IN/uc-02-blocked-credit-audit.md
---

# UC-02 · Blocked credit audit (s.17(5)) — SOP

**Full spec:** [`docs/usecases/IN/uc-02-blocked-credit-audit.md`](../../docs/usecases/IN/uc-02-blocked-credit-audit.md)
**Code:** [`scripts/uc/IN/uc02_blocked_credit.py`](../../scripts/uc/IN/uc02_blocked_credit.py)

## When it runs
Weekly, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `section_17_5` | A line on a bill claiming ITC whose HSN/SAC prefix (8703, 8711, 2106, 2201, 2202, 9963, 9996, 9997, 9954; renting property, SAC 9972, is not blocked) or description matches a blocked category. Exposure = the line's share of the bill's tax |
| `itc_possibly_under_claimed` | A posted bill marked `ineligible` whose lines match no blocked category: credit may have been given up |
| `missing_required_field` (data_quality) | Lines with no HSN/SAC on bills claiming ITC; they can't be classified |

## How to explain the result
Every blocked match is a **suspicion for a person to confirm**, never a reversal: the
exceptions (further supply, obligatory under law, plant and machinery) can't be read from
the ledger. Say how many lines were classifiable, so "0 blocked" is never overstated.

## Limits
Goods written off or destroyed (s.17(5)(h)) are UC-16's job, not this table's.
