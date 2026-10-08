---
id: uc-04
title: MSME 45-day payment exposure
capability: msme
description: >-
  UC-04 (India): finds unpaid bills from MSME suppliers past the MSMED Act 45-day limit
  (or an earlier agreed due date), with compound penal interest at 3 × the RBI bank rate and
  the s.43B(h) income-tax disallowance for micro and small suppliers. Also lists bills due
  within a week and MSME vendors with no Udyam number.
questions:
  - "Which small suppliers are we about to pay late, and what will it cost us?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.IN.uc04_msme_45_day:Msme45DayExposure
tools: [Bill.list, Party.list]
escalate: digest
spec: docs/usecases/IN/uc-04-msme-45-day-exposure.md
---

# UC-04 · MSME 45-day payment exposure — SOP

**Full spec:** [`docs/usecases/IN/uc-04-msme-45-day-exposure.md`](../../docs/usecases/IN/uc-04-msme-45-day-exposure.md)
**Code:** [`scripts/uc/IN/uc04_msme_45_day.py`](../../scripts/uc/IN/uc04_msme_45_day.py)

## When it runs
Daily (deadlines move every day), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `msme_45_day_breach` | Unpaid posted bill from an `is_msme` vendor past min(date + 45, due_date). Penal interest = balance × ((1 + 3 × bank rate / 12)^months − 1); s.43B(h) disallowance = balance for micro/small |
| `msme_45_day_due_soon` | Deadline within 7 days: pay these first |
| `stored_value_mismatch` (data_quality) | Negative `grand_total` (N7): no figures computed |
| `missing_required_field` (data_quality) | MSME vendor with blank `msme_no`: s.43B(h) needs Udyam registration |

The bank rate is effective-dated in `constants.yaml`; the run uses the rate in force today.

## How to explain the result
Lead with the count, total interest and total disallowance at risk. Say the 45 days run
from the bill date as a proxy for acceptance, and that s.43B(h) is subject to Udyam
confirmation where the number is blank.

## Limits
If UC-11 shows the goods were never received, there may have been no acceptance; check
before paying. s.43B(h) is cited in 1961 Act numbering (confirm under the 2025 Act).
