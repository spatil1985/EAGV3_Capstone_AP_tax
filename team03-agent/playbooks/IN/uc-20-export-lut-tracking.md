---
id: uc-20
title: Export / SEZ zero-rating and LUT cover
capability: export_lut
description: >-
  UC-20 (India): checks zero-rated sales — SEZ invoices carrying CGST/SGST, exports failing the
  s.2(6) IGST conditions (place of supply in India, INR), deemed exports left untaxed — and
  whether zero-tax zero-rated invoices are covered by a Letter of Undertaking for their FY.
  The platform stores no LUT dates or ARN, so cover is reported as unconfirmed.
questions:
  - "Are our export invoices genuinely zero-rated, and is our LUT still valid?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Invoice.list, TaxExemption.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc20_export_lut:ExportLutTracking
tools: [Invoice.list, TaxExemption.list]
escalate: digest
spec: docs/usecases/IN/uc-20-export-lut-tracking.md
---

# UC-20 · Export / SEZ zero-rating and LUT cover — SOP

**Full spec:** [`docs/usecases/IN/uc-20-export-lut-tracking.md`](../../docs/usecases/IN/uc-20-export-lut-tracking.md)
**Code:** [`scripts/uc/IN/uc20_export_lut.py`](../../scripts/uc/IN/uc20_export_lut.py)

## When it runs
Monthly, on each zero-rated invoice, on 1 April (LUT renewal), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `sez_intra_state_tax_charged` | SEZ invoice with CGST/SGST |
| `export_condition_failed` | `overseas` invoice with an Indian place of supply or in INR |
| `deemed_export_untaxed` | Deemed export with no tax |
| `lut_missing` | FY's zero-tax zero-rated invoices, no LUT record at all |
| `lut_validity_unknown` | An LUT record exists with no dates/FY/ARN: cover unconfirmed |

## How to explain the result
SEZ invoices in INR are correct. Ask the user to record the LUT ARN and FY; until the
platform holds them (N426 T4.4), cover can only be "unconfirmed".

## Limits
No genuine export (overseas) invoice exists on the tenant yet.
