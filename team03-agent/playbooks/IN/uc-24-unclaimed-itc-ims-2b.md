---
id: uc-24
title: Unclaimed and at-risk input credit (IMS, GSTR-2B)
capability: itc_unclaimed
description: >-
  UC-24 (India, GST): finds input credit on IMS-rejected bills still marked eligible (don't
  claim), credit pending IMS action before GSTR-2B is generated on the 14th, bills with no
  supplier GSTIN (can't be matched to 2B), credit about to lapse under s.16(4), and gaps
  between book credit and the GSTR-2B total.
questions:
  - "Which input credit can we still claim, which have we claimed that we shouldn't have, and what will we lose if we wait?"
  - "What is unclaimed?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list, GSTReturn.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.updated}
  - {kind: on_request}
compute: scripts.uc.IN.uc24_itc_entitlement:ItcEntitlementAudit
tools: [Bill.list, Party.list, GSTReturn.list]
escalate: digest
spec: docs/usecases/IN/uc-24-unclaimed-itc-ims-2b.md
---

# UC-24 · Unclaimed and at-risk input credit — SOP

**Full spec:** [`docs/usecases/IN/uc-24-unclaimed-itc-ims-2b.md`](../../docs/usecases/IN/uc-24-unclaimed-itc-ims-2b.md)
**Code:** [`scripts/uc/IN/uc24_itc_entitlement.py`](../../scripts/uc/IN/uc24_itc_entitlement.py)

## When it runs
Monthly (12th and 15th; Aug–Nov for s.16(4)), when a bill's IMS status changes, and on request.

## What it checks
Population: posted, ITC-eligible bills with tax above 0 (tax source per document).

| Rule | Finding |
|---|---|
| `itc_on_rejected_document` | IMS `reject` but still marked eligible |
| `itc_awaiting_ims_action` | Per period: `pending` before that period's GSTR-2B (14th of next month) |
| `itc_supplier_not_identified` | No supplier GSTIN on the bill or the vendor |
| `itc_lapsing` | Per FY: s.16(4) cutoff (30 Nov after FY end) within 90 days |
| `itc_not_in_2b` | Per period: book credit ≠ GSTR-2B total (totals only — 2B has no lines) |

## How to explain the result
Lead with the rejected credit (do not claim), then what to action in IMS and by when. Say
that claimed-per-document is not recorded on the platform and line-level 2B matching is not
possible (N426 T1.3).

## Limits
GSTR-2B rows carry no lines and a meaningless `filing_status`; never treat them as filed returns.
