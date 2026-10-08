---
id: uc-40
title: Vendor master audit
capability: vendor_master
description: >-
  UC-40 (India): checks every party actually used as a vendor for what payment, input credit and TDS
  rely on — GSTIN present, valid and matching its PAN and state; PAN; Udyam number for MSMEs; bank
  details and whether payments went to them; vendor typing; duplicates — with the bills, payments
  and credits that rely on each record.
questions:
  - "Are our vendor records complete and trustworthy enough to pay against, claim credit on and deduct tax for?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Party.list, Bill.list, PaymentMade.list, VendorCredit.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: event, on: party.updated}
  - {kind: on_request}
compute: scripts.uc.IN.uc40_vendor_master_audit:VendorMasterAudit
tools: [Party.list, Bill.list, PaymentMade.list, VendorCredit.list]
escalate: digest
spec: docs/usecases/IN/uc-40-vendor-master-audit.md
---

# UC-40 · Vendor master audit — SOP

**Full spec:** [`docs/usecases/IN/uc-40-vendor-master-audit.md`](../../docs/usecases/IN/uc-40-vendor-master-audit.md)
**Code:** [`scripts/uc/IN/uc40_vendor_master_audit.py`](../../scripts/uc/IN/uc40_vendor_master_audit.py) ·
shared in [`scripts/uc/common/vendor_master.py`](../../scripts/uc/common/vendor_master.py)

## When it runs
Weekly, when a vendor record or payment changes, and on request.

## What it checks
One finding per vendor in use, led by its most serious gap (others in `also`):

| Rule | Gap |
|---|---|
| `vendor_gstin_invalid` / `_pan_mismatch` / `_state_mismatch` | GSTIN fails format/checksum, or doesn't match the PAN or address state |
| `vendor_gstin_missing` | Registered supplier with no GSTIN (credit can't be supported) |
| `vendor_pan_missing` | No PAN: TDS at 20% (s.206AA) |
| `vendor_msme_no_missing` | MSME with no Udyam number |
| `vendor_bank_missing` / `payment_account_mismatch` | No bank details, or paid to an account not on the master |
| `vendor_type_conflict` / `vendor_address_missing` / `duplicate_vendor` | Typing, address, duplicates on GSTIN/PAN/bank/email/phone/name |

## How to explain the result
Rank by the documents relying on each record. The population is vendors on documents, not
`contact_type = vendor` (which finds 12 of 88).

## Limits
GSTIN validation is format + checksum, not a portal lookup (N426 T4.2). Bank-change-before-payment
needs field history the watcher doesn't keep yet.
