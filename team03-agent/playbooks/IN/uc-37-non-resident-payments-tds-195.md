---
id: uc-37
title: Payments to non-residents (s.195 TDS, Form 15CA/CB)
capability: nonresident_tds
description: >-
  UC-37 (India): before paying a foreign vendor, checks s.195 TDS on services (none deducted, a
  treaty rate without residency documents, below the 20% no-PAN floor) and Form 15CA/15CB for the
  remittance. Non-residence needs a foreign address or non-INR billing; bills merely tagged overseas
  from Indian INR vendors are reported as tagging errors.
questions:
  - "Before we pay a foreign vendor, have we deducted the right tax and got the remittance paperwork done?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: bill.created}
  - {kind: on_request}
compute: scripts.uc.IN.uc37_nonresident_payments:NonResidentPayments
tools: [Bill.list, Party.list]
escalate: digest
spec: docs/usecases/IN/uc-37-non-resident-payments-tds-195.md
---

# UC-37 · Payments to non-residents — SOP

**Full spec:** [`docs/usecases/IN/uc-37-non-resident-payments-tds-195.md`](../../docs/usecases/IN/uc-37-non-resident-payments-tds-195.md)
**Code:** [`scripts/uc/IN/uc37_nonresident_payments.py`](../../scripts/uc/IN/uc37_nonresident_payments.py)

## When it runs
Monthly, and before a bill or payment to a non-resident is approved.

## What it checks
| Rule | Finding |
|---|---|
| `tds_195_not_deducted` | Non-resident, service lines, no TDS: exposure at the s.115A rate (20.8% incl. cess) |
| `dtaa_rate_without_documents` | Reduced (treaty) rate without TRC + Form 10F on file |
| `tds_206aa_rate_short` | No PAN and a rate below 20% |
| `form_15ca_cb_missing` | FY remittance with no 15CA (and 15CB above ₹5 lakh) on file |
| `overseas_tag_on_resident` (data_quality) | Tagged overseas, Indian address, INR |

Treaty and remittance documents live in `config/overrides/nonresident_docs.yaml`.

## How to explain the result
Say what evidence makes a vendor non-resident. Goods purchases are generally outside s.195. The
equalisation levy is understood abolished from April 2025.

## Limits
Section numbers are 1961 Act numbering (confirm under the 2025 Act). Surcharge is not computed.
