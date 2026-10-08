---
id: uc-14
title: "Clinic: exempt / taxable supply split"
capability: clinic_exempt_split
description: >-
  UC-14 (India, clinic vertical): checks that a clinic's streams are classified as GST law
  treats them (consultations and procedures exempt, cosmetic procedures taxable, room rent
  above ₹5,000/day taxed at 5% without ITC, OP pharmacy taxable), flags item-master conflicts
  and sale lines charged against their classification, and reports E/T/F turnover by month.
questions:
  - "Which parts of what we do are taxable, and are we charging GST on the right ones?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Item.list, Invoice.list]
  verticals: [clinic]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: item.updated}
  - {kind: on_request}
compute: scripts.uc.IN.uc14_clinic_exempt_split:ClinicExemptSplit
tools: [Item.list, Invoice.list]
escalate: digest
spec: docs/usecases/IN/uc-14-clinic-exempt-taxable-split.md
---

# UC-14 · Clinic: exempt / taxable supply split — SOP

**Full spec:** [`docs/usecases/IN/uc-14-clinic-exempt-taxable-split.md`](../../docs/usecases/IN/uc-14-clinic-exempt-taxable-split.md)
**Code:** [`scripts/uc/IN/uc14_clinic_exempt_split.py`](../../scripts/uc/IN/uc14_clinic_exempt_split.py) ·
engine in [`scripts/uc/common/exempt_split.py`](../../scripts/uc/common/exempt_split.py)

## When it runs
Monthly, when an item changes, and on request. Only for a tenant whose industry maps to
`clinic`; none exists, so the router skips it on Suryodaya (`--vertical clinic` exercises it).

## What it checks
As UC-07 (`classification_conflict`, `stream_treatment_mismatch`, `exempt_but_taxed`,
`taxable_but_untaxed`, `item_tax_line_invalid`) with the clinic stream table, plus:

| Rule | Finding |
|---|---|
| `room_rent_tax_wrong` | A ward/room line (not ICU) above ₹5,000 per day not charged exactly 5% |

## How to explain the result
No field says whether a medicine went to an in-patient, so pharmacy lines are treated as OP
(taxable): say so. Room-rent tax carries no ITC.

## Limits
Cosmetic vs reconstructive surgery can't be read from the data; matches are for review.
