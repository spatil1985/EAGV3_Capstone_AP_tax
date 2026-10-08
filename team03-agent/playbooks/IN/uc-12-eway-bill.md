---
id: uc-12
title: E-way bill coverage and expiry audit
capability: eway
description: >-
  UC-12 (India, GST): e-way bill coverage and expiry audit. Finds outward invoices and
  delivery challans above the Rule 138 threshold that moved without an e-way bill, e-way
  bills with no EWB number, expired bills still in transit, missing Part B vehicle details
  and wrong validity periods. Returns counts and exposure by rule, the top 10 rows and a
  run_ref for get_findings.
questions:
  - "Is anything moving on the road right now without valid documentation?"
status: live
blocked_by: null
tax_regimes: [gst]
verticals: [manufacturing, retail]
requires_features: [eway_bill]
triggers:
  - {kind: scheduled, cadence: daily}
  - {kind: on_request}
compute: scripts.uc.IN.uc12_eway_bill:EWayBillAudit
tools: [EWayBill.list, Invoice.list, DeliveryChallan.list]
escalate: new_findings
spec: docs/usecases/IN/uc-12-eway-bill-coverage.md
---

# UC-12 · E-way bill coverage and expiry audit — SOP

**Full spec:** [`docs/usecases/IN/uc-12-eway-bill-coverage.md`](../../docs/usecases/IN/uc-12-eway-bill-coverage.md)
**Code:** [`scripts/uc/IN/uc12_eway_bill.py`](../../scripts/uc/IN/uc12_eway_bill.py)

## When it runs
Daily (scheduled), and on request. Only for tenants whose locale has
`tax_regime: gst` and `features.eway_bill: true`. On Keystone (US) the router skips it
and says why.

## What it checks
| Rule | Finding |
|---|---|
| `ewb_missing` | Outward invoice or delivery challan above the Rule 138 threshold, already moved (not draft), with no e-way bill |
| `ewb_not_real` | E-way bill marked `active`/`generated` with no EWB number |
| `ewb_expired_in_transit` | E-way bill still `active`/`generated` after `expiry_date` |
| `ewb_part_b_missing` | `active` with no vehicle number |
| `ewb_validity_wrong` | Expiry ≠ generation + ⌈km ÷ 200⌉ days (÷ 20 for over-dimensional cargo) |

`ewb_not_real`, `ewb_expired_in_transit` and `ewb_validity_wrong` are platform-state
contradictions, so they are also written to `anomalies.jsonl` for bug review (N13).

## What it never does
It never generates, extends or cancels an e-way bill (generation is GST-29, out of
scope). It reads and reports. Escalations are sent only with `--commit`.

## Human follow-up
For `ewb_missing` on a non-draft document, confirm with logistics whether the goods
have left. If so, generate the EWB before the next checkpoint. For expired or
number-less EWBs, confirm whether the movement is complete and close the record.
