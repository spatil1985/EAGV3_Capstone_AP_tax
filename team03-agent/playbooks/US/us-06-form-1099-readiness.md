---
id: us-06
title: Form 1099 readiness and backup withholding
capability: form_1099
description: >-
  US-06 (US): lists the vendors that will need a Form 1099 this year (from the platform's 1099
  summary), and for each whether a W-9 and TIN are on file, the box is mapped, and backup withholding
  (24%) was required; flags vendors paid over the threshold with no tax classification, and checks
  the report against the year's payments.
questions:
  - "Which vendors will need a 1099 for this year, and do we have what we need to file it — or should we be withholding?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Party.list, PaymentMade.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: payment_made.created}
  - {kind: on_request}
compute: scripts.uc.US.us06_form_1099_readiness:Form1099Readiness
tools: [Party.list, PaymentMade.list]
escalate: digest
spec: docs/usecases/US/us-06-form-1099-readiness.md
---

# US-06 · Form 1099 readiness — SOP

**Full spec:** [`docs/usecases/US/us-06-form-1099-readiness.md`](../../docs/usecases/US/us-06-form-1099-readiness.md)
**Code:** [`scripts/uc/US/us06_form_1099_readiness.py`](../../scripts/uc/US/us06_form_1099_readiness.py)

## When it runs
Monthly and in December, when a vendor with no TIN is paid, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `w9_missing` | Reportable vendor with no W-9 |
| `backup_withholding_required` | Reportable, no TIN: 24% of the reportable amount |
| `box_unmapped` | Reportable vendor with no 1099 box |
| `classification_missing` | Paid ≥ threshold with no US tax classification |
| `stored_value_mismatch` (data_quality) | Report `total_paid` ≠ the year's PaymentMade |

Oracle: `GET /api/cpa/reports/1099-summary` (REST, allowlisted; not an MCP tool — not yet requested).
Threshold $2,000 from 2026 (effective-dated in `constants.yaml`).

## How to explain the result
Lead with who gets a 1099 and the total, then the W-9s to collect. Corporations are correctly
excluded. TIN matching and e-file are platform-documented gaps, not bugs.

## Limits
`Party.tin` is redacted for our role; TIN presence comes from the report.
