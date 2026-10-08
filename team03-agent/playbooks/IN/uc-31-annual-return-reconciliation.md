---
id: uc-31
title: Annual return reconciliation (GSTR-9 / 9C)
capability: annual_return
description: >-
  UC-31 (India, GST): whether the annual return will agree with the monthly returns and the books,
  and what to fix before it is due (31 December after the FY). Blocked: the GSTR-9 endpoint returns
  HTTP 501 (GST-39, platform-documented) and GSTR-2B has no line data, so only a draft could be
  computed and nothing can be filed.
questions:
  - "Will our annual return agree with our monthly returns and our books, and what do we have to fix before it's due?"
status: blocked
blocked_by: "GST-39 (GSTR-9 endpoint returns HTTP 501, platform-documented — don't file); GSTR-2B lines not exposed (N426 T1.3)"
tax_regimes: [gst]
requires:
  tools: [GSTReturn.list, Invoice.list, Bill.list, CreditNote.list, AccountingPeriod.list]
triggers:
  - {kind: scheduled, cadence: monthly}
  - {kind: on_request}
compute: null
tools: [GSTReturn.list, Invoice.list, Bill.list, CreditNote.list, AccountingPeriod.list]
escalate: never
spec: docs/usecases/IN/uc-31-annual-return-reconciliation.md
---

# UC-31 · Annual return reconciliation (GSTR-9 / 9C) — blocked

**Full spec:** [`docs/usecases/IN/uc-31-annual-return-reconciliation.md`](../../docs/usecases/IN/uc-31-annual-return-reconciliation.md)

## Why it is blocked
- The GSTR-9 endpoint returns **HTTP 501**: the locale lists it as `not_yet_supported.gstr9`
  (GST-39). It is a documented platform gap — **don't file it as a bug**.
- Table 8 (GSTR-2B vs books) needs 2B line data, which doesn't exist (N426 T1.3).
- GSTR-9C needs audited statements; `AccountingPeriod` figures are unaudited.

## What the agent says when asked
GSTR-9 is due 31 December after the FY (mandatory above ₹2 crore AATO; 9C above ₹5 crore — see
UC-29). The monthly figures can be compared with the books today through UC-23 (per period) and
UC-26 (GSTR-1), but no annual draft or filing is produced here.

## To unblock
A GSTR-9 endpoint and 2B lines. Then write `scripts/uc/IN/uc31_*.py` aggregating UC-23 per period
over the FY and set `status: live`.
