---
id: uc-26
title: GSTR-1 readiness
capability: gstr1
description: >-
  UC-26 (India, GST): checks that every live sale can go into the right GSTR-1 table with the right
  kind of GST — inter-state sales charged CGST+SGST (or intra-state charged IGST), B2B sales with no
  recipient GSTIN, missing or short HSN codes, sales with no GST treatment — previews the filing
  period's tables, and compares them with the GSTR-1 row.
questions:
  - "Is every sale this month going into the right part of GSTR-1, with the right kind of GST?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Invoice.list, Party.list, OrgProfile.list, GSTReturn.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc26_gstr1_readiness:Gstr1ReadinessAudit
tools: [Invoice.list, Party.list, OrgProfile.list, GSTReturn.list]
escalate: digest
spec: docs/usecases/IN/uc-26-gstr1-readiness.md
---

# UC-26 · GSTR-1 readiness — SOP

**Full spec:** [`docs/usecases/IN/uc-26-gstr1-readiness.md`](../../docs/usecases/IN/uc-26-gstr1-readiness.md)
**Code:** [`scripts/uc/IN/uc26_gstr1_readiness.py`](../../scripts/uc/IN/uc26_gstr1_readiness.py)

## When it runs
Monthly (8th and 10th, before the 11th due date), on each new invoice or credit note, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `wrong_tax_head_for_pos` | Supplier state (`OrgProfile.gstin[:2]`) ≠ place of supply with CGST+SGST charged, or the reverse |
| `b2b_without_gstin` | `business_gst` sale with no recipient GSTIN |
| `hsn_missing` / `hsn_digits_short` | Live line with no HSN, or fewer than 6 digits on B2B (AATO > ₹5 crore) |
| `table_classification_missing` (data_quality) | `gst_treatment` blank |
| `stored_value_mismatch` (data_quality) | Filing period's GSTR-1 row ≠ ledger taxable or document count |

Table rule: SEZ/export/deemed export → 6; business_gst → 4; inter-state B2C above ₹1 lakh → 5;
other B2C → 7.

## How to explain the result
A wrong-head invoice means paying again under the right head and claiming the wrong-head tax back.
Give the period's table preview from the run context.

## Limits
GSTR-1 rows on this tenant are round numbers that don't reconcile (spec §6). Table 8 (exempt lines)
and Table 11 (advances) are not split out.
