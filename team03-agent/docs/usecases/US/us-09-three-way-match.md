# US-09 — Three-Way Match (US instance of UC-11)

**US · Proposed owner: Sandip · Verdict: 🟢 Buildable — regime-agnostic; 0 findings on live data**
**IN spec (algorithm, output contract):** [`../IN/uc-11-three-way-match.md`](../IN/uc-11-three-way-match.md) · **live evidence 2026-10-03**

---

Identical check in both jurisdictions (`tax_regimes: [all]`). Sections 1, 3, 4, 5 and
7 are as UC-11. US-specific notes and evidence only.

## 2. Statutory basis (US)

No input-credit rule (UC-11 cites CGST s.16(2)(b)). This is a payables control:
paying for goods not received is a cash loss, and three-way match is the standard key
control under SOX §404.

## 6. Known-bad data (US)

- **N2 (filed against this tenant) appears fixed.** It reported `recorded_status: null`
  on 81/81 PO-linked bills. On 2026-10-03, `recorded_status` is populated on **81/81**
  (e.g. `"within_tolerance"`). UC-11's rule "always call the endpoint" can relax to
  "read the stored status, call the endpoint when it is stale". Keep the comparison as
  a regression guard.
- `received_qty` comes back null on the sampled lines, though status is
  `within_tolerance`. The match basis on this tenant may not be receipts. Confirm
  `live.basis` before relying on received quantities.

## 9. Validation (US)

1. Live: 81 PO-linked bills, **81 `within_tolerance`**, 0 exceeds tolerance, 0
   over-billed, 0 errors.
2. Stored `recorded_status` equals the live status on all 81.

## 10. Open questions (US)

- Tell triage N2 looks fixed? Recommend a comment on the N2 card.
- If `received_qty` is null, what is the match basis on Keystone? Read `live.basis`
  on one bill.

## 11. Live evidence — actual calls, 2026-10-03

`endpoint.accounting.bill_match {"bill_id": …}` on all 81 non-void PO-linked bills.
BILL-2026-00081 (`6d7e27f8-e0e3-4bc5-af60-f5e2e9d6ea74`, Ohio Valley Freight Lines,
$6,750.00) is the same sample N2 cited: `live.status "within_tolerance"`,
`recorded_status "within_tolerance"` (was null at filing).
