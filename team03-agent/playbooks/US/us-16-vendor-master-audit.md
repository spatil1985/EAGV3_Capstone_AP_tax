---
id: us-16
title: Vendor master audit (US)
capability: vendor_master_us
description: >-
  US-16 (US): checks every party used as a vendor for what paying and 1099 reporting rely on — TIN
  present and well-formed, TIN type consistent with the tax classification, W-9 on file, 1099 flag and
  box consistent with what the vendor is and supplies — plus bank details, typing, address and
  duplicates, with the documents relying on each record.
questions:
  - "Are our vendor records (TIN, W-9, 1099 settings) complete enough to pay and report on?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Party.list, Bill.list, PaymentMade.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: party.updated}
  - {kind: on_request}
compute: scripts.uc.US.us16_vendor_master_audit:VendorMasterAuditUS
tools: [Party.list, Bill.list, PaymentMade.list]
escalate: digest
spec: docs/usecases/US/us-16-vendor-master-audit.md
---

# US-16 · Vendor master audit (US) — SOP

**Full spec:** [`docs/usecases/US/us-16-vendor-master-audit.md`](../../docs/usecases/US/us-16-vendor-master-audit.md) ·
algorithm in [`UC-40`](../IN/uc-40-vendor-master-audit.md)
**Code:** [`scripts/uc/US/us16_vendor_master_audit.py`](../../scripts/uc/US/us16_vendor_master_audit.py) ·
shared in [`scripts/uc/common/vendor_master.py`](../../scripts/uc/common/vendor_master.py)

## When it runs
Weekly, when a vendor record or payment changes, and on request.

## What it checks
One finding per vendor in use, led by its most serious gap:

| Rule | Gap |
|---|---|
| `vendor_tin_missing` / `vendor_tin_format_invalid` | No TIN (when not merely redacted), or not 9 digits |
| `tin_type_classification_conflict` | Corporation with an SSN |
| `w9_missing` | 1099 vendor without W-9 (→ US-06 backup withholding) |
| `form_1099_flag_conflict` / `form_1099_box_conflict` | 1099 flag vs classification; MISC-1 (Rents) for a service vendor |
| shared | bank missing / payment to another account, typing, address, duplicates |

## How to explain the result
`tin` is redacted for our role: TIN presence is US-06's job (via the 1099 report). No IRS TIN matching
exists, so "format valid" is the limit.

## Limits
India-only fields on US parties are never read.
