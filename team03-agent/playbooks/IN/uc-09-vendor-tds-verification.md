---
id: uc-09
title: Vendor TDS verification
capability: tds
description: >-
  UC-09 (India): recomputes TDS on every open or draft supplier bill from its lines (section from
  the SAC: 194C contracts, 194J professional/technical, 194I rent; goods attract none) and
  flags TDS above the bill (negative payable), wrong arithmetic, TDS on goods, a missing
  section, the wrong rate, and service bills above the threshold with no TDS.
questions:
  - "Are we deducting the right TDS on every vendor payment, under the right section?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.approved}
  - {kind: on_request}
compute: scripts.uc.IN.uc09_vendor_tds:VendorTdsVerification
tools: [Bill.list, Party.list]
escalate: digest
spec: docs/usecases/IN/uc-09-vendor-tds-verification.md
---

# UC-09 · Vendor TDS verification — SOP

**Full spec:** [`docs/usecases/IN/uc-09-vendor-tds-verification.md`](../../docs/usecases/IN/uc-09-vendor-tds-verification.md)
**Code:** [`scripts/uc/IN/uc09_vendor_tds.py`](../../scripts/uc/IN/uc09_vendor_tds.py) ·
section table in [`scripts/uc/common/tds.py`](../../scripts/uc/common/tds.py)

## When it runs
Monthly (before the 7th, when TDS is due), when a bill is approved, and on request.

## What it checks
One finding per bill, led by the most serious rule; the others are listed in `also`.

| Rule | Finding |
|---|---|
| `tds_exceeds_bill` | Stored TDS > base: payable negative. Do not pay |
| `tds_arithmetic_wrong` | Stored amount ≠ base × stored rate |
| `tds_on_goods` | TDS on a goods-only bill (194Q is UC-13) |
| `tds_section_missing` | TDS with no section |
| `tds_rate_wrong` | Stored rate ≠ the section's rate (194C 1%/2% by PAN type, 194J 10%/2%, 194I 10%/2%) |
| `tds_not_deducted` | A 194C/J/I bill above the threshold with no TDS |

The stored `tds_amount` is quarantined at fetch (N7) and only compared, never trusted.

## How to explain the result
Lead with bills that would go out with a negative payable. Note that vendor PANs are
blank, so s.206AA (20%) may apply; the rate used is the section rate.

## Limits
Citations are Income-tax Act 1961 numbering; confirm under the 2025 Act. Drafts are checked (fix them before approval); void
bills are not (the count is in the run context).
