---
id: uc-16
title: Stock expiry and blocked credit on write-off
capability: expiry
description: >-
  UC-16 (India): lists batch-tracked stock whose latest receipt has expired or expires within
  30 days (shelf life from the item, receipt date from the latest bill as a proxy), with the
  input credit that must be reversed under s.17(5)(h) if it is written off. Flags shelf-life
  items that can't be dated (not batch-tracked) or are typed as services.
questions:
  - "What stock is about to expire, and what credit do we lose when it does?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Item.list, Bill.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.IN.uc16_expiry_blocked_credit:ExpiryBlockedCredit
tools: [Item.list, Bill.list]
escalate: digest
spec: docs/usecases/IN/uc-16-drug-expiry-blocked-credit.md
---

# UC-16 · Stock expiry and blocked credit — SOP

**Full spec:** [`docs/usecases/IN/uc-16-drug-expiry-blocked-credit.md`](../../docs/usecases/IN/uc-16-drug-expiry-blocked-credit.md)
**Code:** [`scripts/uc/IN/uc16_expiry_blocked_credit.py`](../../scripts/uc/IN/uc16_expiry_blocked_credit.py)

## When it runs
Daily, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `expiry_warning` | Batch-tracked item: latest bill date + `shelf_life_days` is past or within 30 days. Exposure = that bill line's ITC |
| `missing_required_field` (data_quality) | Shelf life but not batch-tracked: undatable |
| `classification_conflict` (data_quality) | Shelf life on an item typed `services` |

## How to explain the result
Every date is an estimate from the latest bill date: batch and stock-entry records are not
readable by our role (N426 T2.2, T2.3). The credit is only lost if the stock is written off.

## Limits
Write-off events aren't exposed, so the s.17(5)(h) reversal row itself is not emitted.
Shelf lives on this tenant are seed values on hand tools.
