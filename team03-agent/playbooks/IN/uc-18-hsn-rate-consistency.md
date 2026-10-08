---
id: uc-18
title: HSN rate consistency
capability: hsn_rate
description: >-
  UC-18 (India): checks the GST rate charged on sale lines for consistency — HSNs charged at
  more than one rate, rates that are not a GST slab on the invoice date (12%/28% left the
  schedule on 22 Sep 2025; 9% is usually a CGST half), and lines that differ from the item
  master. There is no authoritative HSN rate table on the platform.
questions:
  - "Are we charging the right GST rate on every product we sell?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Invoice.list, Item.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: item.updated}
  - {kind: on_request}
compute: scripts.uc.IN.uc18_hsn_rate_consistency:HsnRateConsistency
tools: [Invoice.list, Item.list]
escalate: digest
spec: docs/usecases/IN/uc-18-hsn-rate-consistency.md
---

# UC-18 · HSN rate consistency — SOP

**Full spec:** [`docs/usecases/IN/uc-18-hsn-rate-consistency.md`](../../docs/usecases/IN/uc-18-hsn-rate-consistency.md)
**Code:** [`scripts/uc/IN/uc18_hsn_rate_consistency.py`](../../scripts/uc/IN/uc18_hsn_rate_consistency.py)

## When it runs
Monthly, when an item changes, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `hsn_rate_inconsistent` | One HSN charged at more than one rate across sale lines |
| `rate_not_a_slab` | Line rate not in the slab set in force on the invoice date (`gst_rate_slabs_pct`, effective-dated) |
| `rate_drift_from_master` | Line rate ≠ the item's master rate, when the master has one |

Rate basis per line: effective (tax ÷ taxable) when the line passes Rule 0, else
`tax_percentage`; each finding names its basis.

## How to explain the result
Say this is a consistency check: it can show that rates disagree, not which one is right
(the platform has no rate table — N426 T3.4). The September 2025 slab change is our reading;
confirm it.

## Limits
Item master rates are mostly blank, so master drift rarely fires.
