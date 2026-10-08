---
id: uc-34
title: "School: GST charged on exempt inward services"
capability: school_inward
description: >-
  UC-34 (India, school vertical): whether bus, canteen, security, cleaning and exam vendors are
  charging a school GST on services that are exempt when supplied to an educational institution
  (Notification 12/2017-CT(R) entry 66(b)). Spec only: the fields exist, but no education tenant
  exists on either instance.
questions:
  - "Are our bus, canteen, security, cleaning and exam vendors charging us GST they shouldn't?"
status: spec
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list]
  verticals: [school]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: null
tools: [Bill.list, Party.list]
escalate: never
spec: docs/usecases/IN/uc-34-school-exempt-inward-services.md
---

# UC-34 · School: GST charged on exempt inward services — spec only

**Full spec:** [`docs/usecases/IN/uc-34-school-exempt-inward-services.md`](../../docs/usecases/IN/uc-34-school-exempt-inward-services.md)

## Why it is spec only
No tenant has `OrgProfile.industry = education`; Suryodaya is manufacturing. The data it needs
(bill lines with SAC, vendor treatment, tax charged) exists, so it can be built when a school
tenant appears.

## What the agent says when asked
Entry 66(b) exempts services *to* a school for student/staff transport, catering, security,
cleaning and housekeeping on campus, and admissions/exams (pre-school to higher secondary; online
journals for higher education). A vendor charging GST on these is charging tax nobody owes: ask for
a revised invoice, and don't claim the credit (the school's outward supplies are mostly exempt anyway — UC-07/08).

## To build
`scripts/uc/IN/uc34_*.py`: bills to a school with SAC 9964 (transport), 9963 (catering), 9985
(security/cleaning), 9992 (exam services) and tax > 0 → `gst_on_exempt_inward_service`. Reuse
`common/lines.py` for the line's tax share; then set `status: live`.
