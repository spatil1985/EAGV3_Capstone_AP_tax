# US-07 — Duplicate Vendor Payment (US instance of UC-05)

**US · Verdict: 🟢 Buildable — regime-agnostic; 0 findings on live data**
**IN spec (algorithm, tiers, output contract):** [`../IN/uc-05-duplicate-vendor-payment.md`](../IN/uc-05-duplicate-vendor-payment.md) · **live evidence 2026-10-03**

---

This check is identical in both jurisdictions, and the harness manifest declares
`tax_regimes: [all]`. Sections 1, 3, 4, 5 and 7 are as UC-05. This file records only
what differs for the US tenant, and the US live evidence.

## 2. Statutory basis (US)

A financial control, not a tax statute. Internal control over financial reporting:
SOX §404 for issuers, and the auditor's controls testing generally. There is no input
credit to double-claim, so a duplicate costs cash plus any **use tax** self-assessed on
it (US-02).

## 6. Known-bad data (US)

- **`bill_number` (the supplier's document number) is empty on 101/101 bills**, so
  UC-05's Tier 1 `exact` key cannot run at all. Every candidate comes from Tier 2
  (`over_billed`, via `bill_match`) and Tier 3 (amount proximity).
- **Recurring runaway (filed B7 → N6).** The 3 monthly templates each produced 6 bills
  (2026-09-20, -21, -22, -23 ×2, 10-01). Now 15 are `void` and 5 `draft`.
  `next_bill_date` advances (2026-11-01), but `last_generated_date` is still null on
  all 4 templates. The recurring gate still suppresses them; the voids also remove
  them.
- **Standing orders are not duplicates.** 15 groups of identical bills (same vendor,
  total and lines) recur fortnightly, each on its own `purchase_order_id`. Example:
  Apex Metals Supply $16,739.38 on 2026-01-26, 02-11, 02-27, 03-15, 03-31, 04-16 and
  05-02, each with a different PO. A different PO plus a ≥ 14-day interval is the
  suppression rule. Add it to UC-05 §5 as a US-observed case.

## 8. Limits (US)

As UC-05. Holds would use the requested `Bill.hold` (`../../submissions/requested_tools.md` T3.3).

## 9. Validation (US)

1. Live: Tier 3 pairs within 3 days = **0**; Tier 2 `over_billed` = **0** (US-09).
2. The 15 standing-order groups must not be flagged.
3. Regression: the 3 Keystone false positives that motivated UC-05's rework
   (recurring templates) stay suppressed.

## 10. Open questions (US)

- `bill_number` absent on 100% of bills: escalate as a data-capture gap at bill entry?
  Without it, the strongest duplicate key never works on this tenant.

## 11. Live evidence — actual calls, 2026-10-03

- `Bill.list {"limit":1000}` → 101 bills; 0 same-vendor/same-amount pairs within 3
  days among non-void bills; 15 identical groups, all fortnightly with distinct POs.
- `RecurringBill.list` → "SaaS — CRM & helpdesk", "Office cleaning services",
  "Monthly internet & bandwidth" (monthly ×1, next 2026-11-01, last null, 6 bills
  each); "Quarterly pest control" (monthly ×3, next 2027-01-01, 2 bills).
