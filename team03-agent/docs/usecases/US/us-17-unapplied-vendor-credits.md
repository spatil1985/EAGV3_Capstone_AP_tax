# US-17 — Unapplied Vendor Credits and Advances (US instance of UC-41)

**US · Domains: all five · Verdict: 🟢 Buildable — 0 findings on live data (no vendor credits, no advances)**
**IN spec (algorithm, output contract):** [`../IN/uc-41-unapplied-vendor-credits.md`](../IN/uc-41-unapplied-vendor-credits.md) · **live evidence 2026-10-04**

---

Regime-agnostic (`tax_regimes: [all]`). Sections 1, 3, 4, 5 and 7 are as UC-41.

## 2. Basis (US)

Commercial, as UC-41. US-specific tie-ins:
- A vendor credit is money the **vendor owes us**. It is our receivable, so it is not unclaimed property
  we report. The reverse case is: money **we owe a vendor** that is never claimed (an uncashed or returned
  payment, a refund we owe them). That is escheatable, and is handled in [US-21](us-21-unclaimed-property-escheat.md).
- Applying a credit reduces 1099-reportable payments to that vendor ([US-06](us-06-form-1099-readiness.md)).

## 6. Known-bad data (US)

None found. The entity is simply empty on this tenant.

## 9. Validation (US)

1. **Live:** `VendorCredit` = 0 rows; `PaymentMade.unused_amount > 0` on 0; `payment_type` regular on all
   67 → 0 findings, the correct result.
2. **Fixtures** as UC-41 §9.

## 10. Open questions (US)

- Are vendor credits recorded some other way on Keystone (negative bills, journal entries)? 0 vendor
  credits in nine months of purchasing is unusual for a manufacturer.

## 11. Live evidence — actual calls, 2026-10-04

- `VendorCredit.list {"limit":1000}` → 0 rows.
- `PaymentMade.list {"limit":1000}` → 67: `payment_type: regular` ×67, `unused_amount` 0 on all,
  `payment_mode: bank_transfer` ×67.
