---
id: uc-32
title: ITC refund on zero-rated supplies and inverted duty (Rule 89)
capability: refund
description: >-
  UC-32 (India, GST): computes the indicative refund of accumulated input credit for the FY to date —
  Rule 89(4) for zero-rated supplies under LUT (zero-rated turnover × net credit ÷ adjusted total
  turnover) and an inverted-duty check (inputs taxed above outputs) — with the 2-year window and the
  caveat that the LUT's validity can't be proved.
questions:
  - "We have credit piling up because we export or because our inputs are taxed higher than our sales. How much can we get refunded, and by when?"
status: live
blocked_by: null
tax_regimes: [gst]
requires:
  tools: [Invoice.list, Bill.list, TaxExemption.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: scripts.uc.IN.uc32_itc_refund:ItcRefund
tools: [Invoice.list, Bill.list, TaxExemption.list]
escalate: digest
spec: docs/usecases/IN/uc-32-itc-refund-zero-rated-inverted.md
---

# UC-32 · ITC refund (Rule 89) — SOP

**Full spec:** [`docs/usecases/IN/uc-32-itc-refund-zero-rated-inverted.md`](../../docs/usecases/IN/uc-32-itc-refund-zero-rated-inverted.md)
**Code:** [`scripts/uc/IN/uc32_itc_refund.py`](../../scripts/uc/IN/uc32_itc_refund.py)

## When it runs
Monthly, plus a warning before the 2-year window closes, and on request.

## What it checks
| Rule | Finding |
|---|---|
| `refund_eligible_zero_rated` | Rule 89(4) on the FY to date: zero-tax SEZ/export turnover × (inputs + input services credit) ÷ adjusted total turnover |
| `lut_unverified` | The refund rests on an LUT with no dates or ARN (UC-20) |
| `refund_window_closing` | 2-year window (s.54(1)) from the earliest zero-rated invoice < 90 days away |
| `refund_eligible_inverted` | An input rate above an output rate: compute Rule 89(5) per product |

## How to explain the result
It is indicative: filing the refund is out of scope, and it depends on the LUT. Capital-goods
credit is excluded from Rule 89(4).

## Limits
FY 2025-26 credit is not in the ledger (bills start 2026-06-07), so only the current FY is computed.
