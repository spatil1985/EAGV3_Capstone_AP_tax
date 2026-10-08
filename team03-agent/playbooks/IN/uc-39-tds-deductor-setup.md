---
id: uc-39
title: TDS deductor setup and section coverage
capability: tds_setup
description: >-
  UC-39 (India): checks whether the company can deduct TDS at all (TDS on but no TAN), whether TDS on
  bills uses a statutory section and rate, and whether interest (194A, including MSME interest),
  commission (194H) and business perquisites (194R) paid this FY above the thresholds had TDS deducted.
questions:
  - "Are we set up to deduct TDS at all, and are we deducting under every section that applies to what we pay?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [OrgProfile.list, DirectTaxPreferences.list, Bill.list, Expense.list, PaymentMade.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc39_tds_deductor_setup:TdsDeductorSetup
tools: [OrgProfile.list, DirectTaxPreferences.list, Bill.list, Expense.list, PaymentMade.list]
escalate: digest
spec: docs/usecases/IN/uc-39-tds-deductor-setup.md
---

# UC-39 · TDS deductor setup and section coverage — SOP

**Full spec:** [`docs/usecases/IN/uc-39-tds-deductor-setup.md`](../../docs/usecases/IN/uc-39-tds-deductor-setup.md)
**Code:** [`scripts/uc/IN/uc39_tds_deductor_setup.py`](../../scripts/uc/IN/uc39_tds_deductor_setup.py)

## When it runs
Monthly (before the 7th deposit date) and quarterly (returns), when a bill or expense is created, and
on request.

## What it checks
| Rule | Finding |
|---|---|
| `tan_missing` | `enable_tds` on, `tan` empty |
| `tds_section_code_invalid` (data_quality) | Bill with TDS under a non-statutory code or rate |
| `tds_section_not_applied` | Per payee per FY: interest (194A), commission (194H) or perquisites (194R) above the threshold, no TDS; plus the 30% s.40(a)(ia) disallowance |

Section comes from the account name, never from the seeded `tds_section_code`. Thresholds and rates
are effective-dated (Finance Act 2025 changes).

## How to explain the result
Lead with the TAN gap: nothing else can be fixed until it is. MSME interest is also not deductible
at all (MSMED s.23).

## Limits
TDS deposits (challans) aren't tracked (GST-18). 194T (partners) and 194-O (marketplace) need data
the tenant doesn't have.
