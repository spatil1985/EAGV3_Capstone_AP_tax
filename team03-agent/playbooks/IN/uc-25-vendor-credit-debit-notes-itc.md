---
id: uc-25
title: Inward credit notes and the credit they reduce
capability: vendor_notes
description: >-
  UC-25 (India, GST): for supplier credit notes (vendor credits), reports the input credit that must
  be reduced in the note's month, reverse-charge credits that reduce the RCM liability, GST on credits
  from suppliers who can't charge it, credits not linked to an original bill, outward credit notes
  that look like misfiled vendor credits, and product-named tax rows.
questions:
  - "Our suppliers have given us credit notes. Have we reduced our input credit for them, and are any of them wrong?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [VendorCredit.list, Bill.list, CreditNote.list, Invoice.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: vendor_credit.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc25_vendor_notes_itc:VendorNotesItc
tools: [VendorCredit.list, Bill.list, CreditNote.list, Invoice.list]
escalate: digest
spec: docs/usecases/IN/uc-25-vendor-credit-debit-notes-itc.md
---

# UC-25 · Inward credit notes and the credit they reduce — SOP

**Full spec:** [`docs/usecases/IN/uc-25-vendor-credit-debit-notes-itc.md`](../../docs/usecases/IN/uc-25-vendor-credit-debit-notes-itc.md)
**Code:** [`scripts/uc/IN/uc25_vendor_notes_itc.py`](../../scripts/uc/IN/uc25_vendor_notes_itc.py)

## When it runs
Monthly, when a vendor credit is created, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `itc_reduction_due` | Registered supplier (business_gst, sez, deemed_export), not RCM, tax > 0 |
| `rcm_liability_reduction` | Reverse-charge vendor credit |
| `credit_tax_impossible` | Tax from an unregistered, composition, consumer or overseas supplier |
| `credit_unlinked` | No `reference_number`, or it matches no bill |
| `misfiled_vendor_credit` | Outward credit note linked to a payable invoice |
| `stored_value_mismatch` (data_quality) | Product-named `taxes[]` rows (set aside at fetch) |

## How to explain the result
Lead with the credit to reduce and the month. Tax comes from clean GST heads, else valid lines,
else the stored total (labelled per row).

## Limits
There is no inward debit-note entity; a supplementary bill can't be told from a normal one.
