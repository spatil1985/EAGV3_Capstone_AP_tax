---
id: uc-21
title: Import of services under reverse charge
capability: rcm_import
description: >-
  UC-21 (India): finds bills for services bought from suppliers outside India where reverse
  charge (IGST paid by us) was not declared, with the liability derived from the line rate.
  Requires two agreeing overseas signals, because the bill tag alone is unreliable; bills
  tagged overseas on one signal are reported as tagging errors instead.
questions:
  - "Which foreign supplier bills create a GST liability we have to pay ourselves?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list, Item.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc21_import_of_services_rcm:ImportOfServicesRcm
tools: [Bill.list, Party.list, Item.list]
escalate: digest
spec: docs/usecases/IN/uc-21-import-of-services-rcm.md
---

# UC-21 · Import of services under reverse charge — SOP

**Full spec:** [`docs/usecases/IN/uc-21-import-of-services-rcm.md`](../../docs/usecases/IN/uc-21-import-of-services-rcm.md)
**Code:** [`scripts/uc/IN/uc21_import_of_services_rcm.py`](../../scripts/uc/IN/uc21_import_of_services_rcm.py)

## When it runs
Monthly, before a foreign bill is approved, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `rcm_import_of_services` | ≥ 2 overseas signals, service lines, RCM off: IGST to self-assess (line rate, else 18%), derived |
| `rcm_double_tax` | Import of services with RCM on, but the supplier charged GST |
| `classification_conflict` (data_quality) | Tagged overseas on one signal only: fix the tag |

Signals: bill tag, vendor tag, non-INR currency, vendor with no Indian GSTIN; a vendor
registered as an Indian taxpayer (e.g. `business_gst`) overrides them. Imported
goods are customs IGST and out of scope.

## How to explain the result
Say how many overseas-tagged bills were rejected and why, so a quiet result isn't read as
"no foreign vendors".

## Limits
No genuine overseas vendor exists on the tenant yet (spec §6).
