---
id: uc-07
title: "School: exempt / taxable supply split"
capability: school_exempt_split
description: >-
  UC-07 (India, school vertical): checks that each income stream is classified the way GST
  law treats it for a school (tuition, student transport and books exempt; stationery,
  uniforms, coaching and hall hire taxable), flags item-master conflicts, exempt items that
  were taxed and taxable items left untaxed, and reports exempt (E), taxable (T) and total (F)
  turnover by month for the Rule 42 apportionment.
questions:
  - "Which of our income streams are actually taxable, and are we treating them correctly?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Item.list, Invoice.list]
  verticals: [school]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: item.updated}
  - {kind: on_request}
compute: scripts.uc.IN.uc07_school_exempt_split:SchoolExemptSplit
tools: [Item.list, Invoice.list]
escalate: digest
spec: docs/usecases/IN/uc-07-school-exempt-taxable-split.md
---

# UC-07 · School: exempt / taxable supply split — SOP

**Full spec:** [`docs/usecases/IN/uc-07-school-exempt-taxable-split.md`](../../docs/usecases/IN/uc-07-school-exempt-taxable-split.md)
**Code:** [`scripts/uc/IN/uc07_school_exempt_split.py`](../../scripts/uc/IN/uc07_school_exempt_split.py) ·
engine in [`scripts/uc/common/exempt_split.py`](../../scripts/uc/common/exempt_split.py)

## When it runs
Monthly, when an item changes, and on request. Only for a tenant whose
`OrgProfile.industry` maps to `school`; none exists yet, so on Suryodaya the router skips
it and says why (`--vertical school` exercises it on manufacturing data).

## What it checks
| Rule | Finding |
|---|---|
| `classification_conflict` | Item master contradicts itself (HSN goods typed services, exempt with `taxable=1`, exempt with no reason) |
| `stream_treatment_mismatch` | Item maps to a school stream whose statutory treatment differs from its `tax_preference` |
| `exempt_but_taxed` / `taxable_but_untaxed` | A sale line (last two months) charged against its item's classification |
| `item_tax_line_invalid` (data_quality) | Invoice tax lines internally inconsistent (Rule 0) |

The run context carries E / T / F turnover by month: the input to UC-08.

## How to explain the result
Classification is `Item.tax_preference`; zero tax is never treated as proof of exemption.
Fix the item master first: line results mean little while the master conflicts.

## Limits
Hostel/boarding is a judgment call and is listed for review, not decided.
