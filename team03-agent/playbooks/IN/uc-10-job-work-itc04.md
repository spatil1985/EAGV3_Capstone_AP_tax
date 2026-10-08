---
id: uc-10
title: Job work return deadline (s.143, ITC-04)
capability: job_work
description: >-
  UC-10 (India, manufacturing): lists goods sent to job workers on delivered job_work challans
  that have not come back within 1 year (inputs) — now deemed supplies, with estimated tax and
  interest — and those due back within 60 days. Draft challans have not moved goods. Returns
  are inferred from later bills, as the platform has no return link.
questions:
  - "What have we sent out for job work that hasn't come back, and when does it become a taxable supply?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [DeliveryChallan.list, Bill.list, Item.list]
  verticals: [manufacturing]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: scripts.uc.IN.uc10_job_work:JobWorkItc04
tools: [DeliveryChallan.list, Bill.list, Item.list]
escalate: digest
spec: docs/usecases/IN/uc-10-job-work-itc04.md
---

# UC-10 · Job work return deadline (s.143, ITC-04) — SOP

**Full spec:** [`docs/usecases/IN/uc-10-job-work-itc04.md`](../../docs/usecases/IN/uc-10-job-work-itc04.md)
**Code:** [`scripts/uc/IN/uc10_job_work.py`](../../scripts/uc/IN/uc10_job_work.py)

## When it runs
Monthly, plus the ITC-04 dates (30 Sep, 31 Mar), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `s143_deemed_supply` | Delivered `job_work` challan older than 365 days, no return found: deemed supply on the send date, tax estimated from the item rate, s.50 interest |
| `s143_due_soon` | Within 60 days of the deadline, no return found |

## How to explain the result
Say the clock only runs on delivered challans (drafts have not moved goods), that the
1-year inputs limit is assumed (no field marks capital goods), and that a return is only
ever inferred.

## Limits
Return tracking is the platform gap (N426 T4.5); moulds, dies and tools sent for job work
have no limit and can't be told apart in the data.
