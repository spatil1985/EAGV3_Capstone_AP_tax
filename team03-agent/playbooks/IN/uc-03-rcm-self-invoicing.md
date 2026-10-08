---
id: uc-03
title: Reverse-charge self-invoicing on notified services
capability: rcm
description: >-
  UC-03 (India, GST): finds supplier bills for notified reverse-charge services (GTA,
  legal, sponsorship, director fees) where reverse charge was not declared and the supplier
  charged no GST, with the liability derived at the notified rate. Also flags bills marked
  reverse charge where it can't apply, and unregistered-supplier bills to check under s.9(4).
questions:
  - "Which supplier bills make us liable to pay the tax ourselves, and have we?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Bill.list, Party.list]
triggers:
  - {kind: scheduled, cadence: weekly}
  - {kind: on_request}
compute: scripts.uc.IN.uc03_rcm_self_invoicing:RcmSelfInvoicing
tools: [Bill.list, Party.list]
escalate: digest
spec: docs/usecases/IN/uc-03-rcm-self-invoicing.md
---

# UC-03 · Reverse-charge self-invoicing — SOP

**Full spec:** [`docs/usecases/IN/uc-03-rcm-self-invoicing.md`](../../docs/usecases/IN/uc-03-rcm-self-invoicing.md)
**Code:** [`scripts/uc/IN/uc03_rcm_self_invoicing.py`](../../scripts/uc/IN/uc03_rcm_self_invoicing.py)

## When it runs
Weekly, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `rcm_undeclared_liability` | Notified service (SAC 9965/996791 GTA, 9982 legal, 998397 sponsorship, director fees by text), `is_reverse_charge` off, no GST charged by the supplier. Liability = rate × taxable value (5% GTA, 18% others), **derived** |
| `rcm_flag_spurious` | `is_reverse_charge` on, but no notified service and not an import of services |
| `rcm_unregistered_review` | Bill from an `unregistered_business` supplier: check the s.9(4) notified classes |

A GTA bill that carries GST has opted for forward charge, so no reverse charge is due
(spec §11 correction). Imports of services are UC-21's job.

## How to explain the result
Always say the liability is derived at the notified rate, not read from the bill. Whether
the transporter issues consignment notes (the GTA test) is not in the data.

## Limits
Checks the flag only; can't see whether the liability was self-invoiced or paid in a return.
