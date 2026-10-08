---
id: uc-30
title: Multiple registrations, branch transfers and ISD
capability: registrations
description: >-
  UC-30 (India, GST): checks the company's state registrations — location GSTINs that don't carry
  the company's PAN, a primary GSTIN that differs from the company profile, GSTIN/state mismatches,
  invalid state codes — and reports sales into states with a branch registration. Branch-transfer and
  ISD checks need the registration on each document, which the platform doesn't record.
questions:
  - "We're registered in several states. Are our branches dealing with each other the way GST requires?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Location.list, OrgProfile.list, Invoice.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: location.updated}
  - {kind: on_request}
compute: scripts.uc.IN.uc30_multiple_registrations:MultipleRegistrations
tools: [Location.list, OrgProfile.list, Invoice.list]
escalate: digest
spec: docs/usecases/IN/uc-30-multiple-registrations.md
---

# UC-30 · Multiple registrations — SOP

**Full spec:** [`docs/usecases/IN/uc-30-multiple-registrations.md`](../../docs/usecases/IN/uc-30-multiple-registrations.md)
**Code:** [`scripts/uc/IN/uc30_multiple_registrations.py`](../../scripts/uc/IN/uc30_multiple_registrations.py)

## When it runs
Monthly, when a location changes, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `registration_pan_mismatch` | Location GSTIN chars 3–12 ≠ `OrgProfile.pan` (s.25(6)) |
| `primary_gstin_mismatch` | Primary location GSTIN ≠ `OrgProfile.gstin` |
| `registration_state_mismatch` | GSTIN state digits ≠ the location's state code |
| `location_state_code_invalid` | State code not a 2-digit GST code |

## How to explain the result
Either the company profile or the locations are wrong; say both readings. Branch transfers
(Rule 28), wrong-registration supplies and ISD can't be checked: documents don't record which
GSTIN despatched or received them (a request not yet filed).

## Limits
Location rows look seeded (state codes like `MS1298/4033`).
