---
id: us-04
title: Exemption certificate coverage
capability: exemption_certs
description: >-
  US-04 (US, sales tax): checks every sale invoiced tax-exempt against the customer's exemption
  certificates (active, right state, valid on the sale date), with the uncollected tax at risk where
  none covers it; warns of certificates expiring within 90 days and of certificates with no file.
questions:
  - "For every sale we didn't charge tax on, do we hold a valid exemption certificate?"
status: live
blocked_by: null
tax_regimes: [sales_use_tax]
requires:
  tools: [Invoice.list, ExemptionCertificate.list, TaxJurisdiction.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: event, on: invoice.created}
  - {kind: on_request}
compute: scripts.uc.US.us04_exemption_certificates:ExemptionCertificateCoverage
tools: [Invoice.list, ExemptionCertificate.list, TaxJurisdiction.list]
escalate: digest
spec: docs/usecases/US/us-04-exemption-certificate-coverage.md
---

# US-04 · Exemption certificate coverage — SOP

**Full spec:** [`docs/usecases/US/us-04-exemption-certificate-coverage.md`](../../docs/usecases/US/us-04-exemption-certificate-coverage.md)
**Code:** [`scripts/uc/US/us04_exemption_certificates.py`](../../scripts/uc/US/us04_exemption_certificates.py)

## When it runs
Monthly (with a 90-day expiry look-ahead), on each exempt invoice, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `exemption_without_certificate` | Exempt invoice; no active certificate for the customer and state covering its date. Exposure = net × combined rate |
| `certificate_expiring` | A certificate in use expiring within 90 days |
| `certificate_unsupported` (data_quality) | Active certificate with no file attached |

## How to explain the result
Covered sales are "recorded" until a file is attached. Read the state from the exempt row's
`state_code`, not its level.

## Limits
Certificate validity per state rules (e.g. blanket vs single-use) is not modelled.
