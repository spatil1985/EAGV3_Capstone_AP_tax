# US-11 — Sales Tax Paid on Exempt Purchases (Refund Opportunities)

**US · Domains: manufacturing (production exemption), school (nonprofit/government buyer), clinic (prescription/medical, nonprofit), retail (purchases for resale) · Verdict: 🟢 Buildable — 0 findings on live data (no bill carries vendor tax)**
**IN counterpart:** [UC-34](../IN/uc-34-school-exempt-inward-services.md) (exempt inward services), [UC-32](../IN/uc-32-itc-refund-zero-rated-inverted.md) (refunds) · **shares a playbook with [US-02](us-02-consumer-use-tax-on-purchases.md)** (purchase taxability, opposite direction) · **live evidence 2026-10-04**

This is the US form of *"what is unclaimed?"*. US sales tax gives no credit to reclaim, but it does have
**overpaid tax**: tax a vendor charged on a purchase that was exempt, recoverable from the vendor or the
state.

---

## 1. Question

> *"Have we paid sales tax to vendors on purchases that should have been tax-free, and can we still get it back?"*

## 2. Statutory basis

- **Exemptions a buyer claims by giving the vendor an exemption certificate** (Ohio shown; other states
  have equivalents in the rulebook):

  | Exemption | Ohio basis |
  |---|---|
  | **Resale:** items bought for resale aren't a retail sale | R.C. 5739.01(E) |
  | **Manufacturing:** things used directly in production | R.C. 5739.02(B)(42)(g), also cited by US-02 |
  | **Nonprofit and government buyers:** schools, charitable clinics | R.C. 5739.02(B)(12), (B)(1) |
  | **Prescription drugs and certain medical devices** | R.C. 5739.02(B)(18)–(19) |

  *Our understanding (caveat):* Pennsylvania (manufacturing exclusion, REV-1220), Michigan
  (industrial-processing exemption, Form 3372) and Illinois (manufacturing machinery and equipment, CRT-61)
  have parallel rules.
- **Refund:** the buyer asks the vendor to refund tax wrongly charged, or claims it from the state.
  *Our understanding (caveat):* Ohio allows a direct refund claim within **4 years** (R.C. 5739.07).
- **Consequence of doing nothing:** the overpaid tax is a permanent cost once the refund window closes.

## 3. Trigger

- **On event:** `bill.created` with vendor sales tax on a line in an exempt class. Catch it before
  payment, when the vendor can simply reissue the bill.
- **Scheduled monthly** sweep; **annual** refund-window review.
- **On request.**

## 4. Input contract

| Call | Fields |
|---|---|
| `Bill.list {"limit":1000}` | `taxes[]` (vendor-charged tax: `state_code`, `rate`, `amount`), `items[]` (`item_id`, description, `account_id`), `vendor_id`, `date` |
| `Expense.list` | `tax_amount`, `account_id`, `description`: purchases paid as expenses |
| `Item.list` | `product_type`, `tax_code`, `is_stock_item`, `is_sellable` (resale indicator) |
| `OrgProfile.list` | `industry` (`manufacturing / education / healthcare / retail / non_profit / government`) |
| Rulebook | Exemption classes by state and account / item class; refund windows |
| `config/overrides/exemption_certificates_issued.yaml` | Certificates **we** gave vendors. The platform models only certificates **received** (`ExemptionCertificate` is customer-side) |

## 5. Algorithm

1. **Taxed purchases:** bill lines or expenses with vendor sales tax above 0.
2. **Exemption class per line** (rulebook):
   - resale (sellable stock item, retail tenant);
   - manufacturing direct use (production material or equipment, manufacturing tenant);
   - buyer-status exemption (nonprofit or government tenant: everything except the listed exclusions);
   - Rx / medical (clinic).
3. **`tax_paid_on_exempt_purchase`:** taxed and exempt. Exposure = the tax.
4. **`exemption_certificate_not_issued`:** the vendor has no certificate from us on file (overrides). This
   is the root cause; issuing one prevents the next overcharge.
5. **`refund_window_closing`:** the purchase date plus the state's window is within 180 days.
6. **Opposite direction:** untaxed purchases that *are* taxable → US-02 (use tax). Both run in one
   playbook.

### Worked example

> **Live:** 101 bills and 78 expenses; vendor sales tax on **0** of them (`taxes[]` empty, `total_tax 0`).
> → 0 findings, the correct result for this tenant. US-02 found the opposite problem.
>
> **Constructed:** a clinic (nonprofit) buys exam-room supplies for $12,000; the vendor charges Ohio 5.75% +
> Stark County 0.75% = **$780**. The clinic holds nonprofit status, but no certificate was given to the
> vendor. → `tax_paid_on_exempt_purchase` $780 + `exemption_certificate_not_issued`.

## 6. Known-bad data

- `ExemptionCertificate` records certificates **received from customers** (1 resale certificate, OH, valid
  to 2029-04-01). It can't represent certificates we issue, so those come from overrides.
- Bill and expense GST fields (`itc_eligibility`, `ims_status`) are populated on US bills (filed B8). They
  are never read.

## 7. Output contract

`finding_type: "purchase_taxability"` (shared with US-02), `rule ∈ {tax_paid_on_exempt_purchase,
exemption_certificate_not_issued, refund_window_closing}`. `total_exposure` = refundable tax.

## 8. Limits

- Never contacts vendors or files a refund claim.
- Taxability calls (direct use in manufacturing, for example) are flagged for review with the rulebook
  entry cited. This is not tax advice.

## 9. Validation

1. **Live:** 0 taxed purchases → 0 findings.
2. **Fixture:** resale stock item, retail tenant, taxed $50 → finding; the same at a manufacturer, for
   office use → none.
3. **Window fixture:** an Ohio purchase 3.6 years old → `refund_window_closing`; 4.1 years → expired
   (reported as lost).

## 10. Open questions

- Should the platform model **certificates issued to vendors**? An `ExemptionCertificate.direction`
  field, perhaps.
- `Item.tax_code` is null on all 28 US items. Product taxability codes would make step 2 data-driven
  instead of table-driven.

## 11. Live evidence — actual calls, 2026-10-04

- `Bill.list {"limit":1000}` → 101; `total_tax > 0` on 0, `taxes[]` non-empty on 0,
  `use_tax_accrued > 0` on 0.
- `Expense.list {"limit":1000}` → 78; `tax_amount > 0` on 0.
- `OrgProfile.list` → `industry: manufacturing`, `state: OH`.
- `ExemptionCertificate.list` → 1 (resale, OH, expiry 2029-04-01).
