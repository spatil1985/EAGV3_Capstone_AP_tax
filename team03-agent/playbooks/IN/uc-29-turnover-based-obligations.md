---
id: uc-29
title: Turnover-based GST obligations
capability: turnover
description: >-
  UC-29 (India, GST): works out last FY's aggregate turnover from the ledger (a floor when the ledger
  starts mid-year) and which turnover-switched obligations apply — e-invoicing, 6-digit HSN, GSTR-9/9C,
  QRMP, composition, the s.194Q buyer test — then flags e-invoicing required but not done, quarterly
  filing above ₹5 crore, lines this year's run rate will cross, and contradictory e-invoicing settings.
questions:
  - "Given our turnover, which GST obligations apply to us this year, and are we meeting them?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Invoice.list, CreditNote.list, OrgProfile.list, EInvoicingPreferences.list, Location.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: scripts.uc.IN.uc29_turnover_obligations:TurnoverBasedObligations
tools: [Invoice.list, CreditNote.list, OrgProfile.list, EInvoicingPreferences.list, Location.list]
escalate: digest
spec: docs/usecases/IN/uc-29-turnover-based-obligations.md
---

# UC-29 · Turnover-based GST obligations — SOP

**Full spec:** [`docs/usecases/IN/uc-29-turnover-based-obligations.md`](../../docs/usecases/IN/uc-29-turnover-based-obligations.md)
**Code:** [`scripts/uc/IN/uc29_turnover_obligations.py`](../../scripts/uc/IN/uc29_turnover_obligations.py)

## When it runs
1 April (new FY) and monthly (run-rate projection), and on request.

## What it checks
| Rule | Finding |
|---|---|
| `einvoice_required_not_generated` | AATO above ₹5 crore, e-invoicing not enabled: this FY's B2B/SEZ/export invoices without IRN |
| `qrmp_ineligible` | Quarterly filing with AATO above ₹5 crore |
| `threshold_will_cross` | This FY's run rate crosses a line last FY didn't |
| `classification_conflict` (data_quality) | `OrgProfile.enable_e_invoicing` on but `EInvoicingPreferences.enabled` off |

The obligation matrix (applies / does not apply / undeterminable) is in the run context. Lines
are in `constants.yaml`, effective-dated where they changed.

## How to explain the result
Say when turnover is a floor, and never turn "undeterminable" into "does not apply". Missing IRNs
are a platform-documented gap (GST-28): don't file it, but the buyers' credit risk is real.

## Limits
Turnover counts invoices only; stock transfers between GSTINs (UC-30) are not in it.
