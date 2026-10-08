---
id: us-14
title: State sales-tax filing calendar
capability: filing_calendar_us
description: >-
  US-14 (US, sales tax): builds each registered state's return calendar from its filing frequency and
  due day, flags returns due within a week with their liability and the timely-filing discount at
  stake, and reports past periods with no filing evidence (the platform has no return record), empty
  next-due fields, frequency conflicts and registered states with no jurisdiction.
questions:
  - "Which state returns are due when, are we ready to file them, and what do we lose if we're late?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [TaxNexus.list, TaxJurisdiction.list, Invoice.list]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.US.us14_filing_calendar:SalesTaxFilingCalendar
tools: [TaxNexus.list, TaxJurisdiction.list, Invoice.list]
escalate: digest
spec: docs/usecases/US/us-14-sales-tax-filing-calendar.md
---

# US-14 · State sales-tax filing calendar — SOP

**Full spec:** [`docs/usecases/US/us-14-sales-tax-filing-calendar.md`](../../docs/usecases/US/us-14-sales-tax-filing-calendar.md)
**Code:** [`scripts/uc/US/us14_filing_calendar.py`](../../scripts/uc/US/us14_filing_calendar.py)

## When it runs
Daily (reminders 7 days ahead), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `filing_due` | Period due within 7 days: liability (from invoice tax rows) and timely-filing discount at stake |
| `filing_unverifiable` | Past-due periods with no filing evidence (aggregate per state) |
| `next_filing_due_missing` (data_quality) | `TaxNexus.next_filing_due` empty |
| `frequency_conflict` | Nexus vs jurisdiction filing frequency |
| `registered_state_without_jurisdiction` | Registered state with no active jurisdiction |

Due days (OH 23rd, PA/MI/IL 20th) and discounts are rulebook values to confirm.

## How to explain the result
Give the next return per state. Past periods can't be shown filed: the platform has no return or
payment record (a request not yet filed). Late entries into filed periods are US-15.

## Limits
Discount caps by frequency are not modelled.
