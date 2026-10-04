# US-22 — Payments to Foreign Vendors: Chapter 3 Withholding and Form 1042-S

**US · Domains: agency (overseas freelancers and platforms), manufacturing (foreign royalties, licences, technical services), clinic and school (foreign software and content) · Verdict: ⚪ Spec only — buildable; no foreign vendor on Keystone (all 8 vendors are in Ohio)**
**IN counterpart:** [UC-37](../IN/uc-37-non-resident-payments-tds-195.md) (s.195 TDS) · **related:** [US-06](us-06-form-1099-readiness.md) (domestic 1099), [US-16](us-16-vendor-master-audit.md) (vendor master) · **live evidence 2026-10-04**

---

## 1. Question

> *"Before we pay a foreign vendor, have we withheld the right US tax and collected the right form?"*

## 2. Statutory basis

*Our understanding (caveat):*

- **IRC §§1441–1442 (Chapter 3):** US-source **FDAP income** paid to a foreign person is subject to
  **30% withholding**. FDAP is fixed, determinable, annual or periodical income, such as royalties, rents,
  and services **performed in the US**. A **tax treaty** may reduce the rate.
- **Exempt from withholding:** services performed **entirely outside the US** are foreign-source and
  generally not withheld on. Most offshore freelancers fall here. The **sourcing of services by where
  they are performed** is the key test.
- **Forms:**
  - **W-8BEN** (individual) or **W-8BEN-E** (entity) establishes foreign status and any treaty claim. A
    W-8 is generally valid for 3 years.
  - The withholding agent files **Form 1042** and gives each payee a **Form 1042-S** by **15 March**
    following the year.
  - Without a valid W-8 (or a W-9), presumption rules may treat the payee as a US person subject to backup
    withholding, or as foreign at 30%.
- **Consequence:** the withholding agent is **liable for tax not withheld**, plus interest and penalties
  for late or missing 1042/1042-S filings.

## 3. Trigger

- **On event:** `bill.created` / approval for a vendor with a non-US address, **before payment**.
- **Scheduled monthly** (deposit tracking) and **annually by 15 March** (1042-S readiness).
- **On request.**

## 4. Input contract

| Call | Fields |
|---|---|
| `Party.list` / `Party.get` | `addresses[].country`, `us_tax_classification`, `tin`, `tin_type`, `w9_on_file`, `exempt_payee_code`, `fatca_exemption_code` |
| `Bill.list` | `vendor_id`, `currency_code`, `items[]` (description, account): the income type (royalty, services, rent) |
| `PaymentMade.list` | `amount`, `date`, `vendor_id`, `exchange_rate` |
| `config/overrides/w8_forms.yaml` | W-8 type, signed date, treaty article and rate, and where services are performed (not modelled on `Party`) |

## 5. Algorithm

1. **Foreign vendor:** address country ≠ US and no W-9 on file. Foreign currency is a supporting signal
   only: Keystone's INR bills are a platform defect (B8), not foreign vendors.
2. **Income type and source** (rulebook): royalty or licence → US-source FDAP; services → **where they are
   performed**:
   - outside the US → no Chapter 3 withholding, but keep the W-8 for documentation;
   - inside the US → withholding.
3. **`foreign_withholding_missing`:** FDAP payment with no withholding recorded. Exposure = 30% (or the
   treaty rate) × payment.
4. **`w8_missing_or_expired`:** no W-8 on file, or signed more than 3 years ago.
5. **`treaty_rate_without_w8`:** a reduced rate applied without a W-8 treaty claim.
6. **`form_1042s_due`:** after year end, payees with Chapter 3 payments, due 15 March.
7. **`foreign_vendor_on_1099`:** `is_1099_vendor = 1` on a foreign vendor. It belongs on 1042-S, not 1099.

### Worked example

> **Live:** 8 vendors used, **all with Ohio addresses** → 0 foreign vendors, 0 findings. The 16 INR bills
> (15 void, 1 draft) are the B8 defect, not foreign vendors.
>
> **Constructed:** a manufacturer pays a German company a $50,000 software licence royalty, US-source FDAP.
> - The US–Germany treaty royalty rate is 0%, but only with a valid W-8BEN-E on file.
>   - No W-8 → withhold **$15,000** (30%);
>   - with the W-8 → withhold $0, and a 1042-S is still due by 15 March.
> - The same vendor's design work performed in Germany → foreign-source, no withholding.

## 6. Known-bad data

None on Keystone. `Party.us_tax_classification` has no "foreign person" value (its options are
individual / corporations / partnership / trust / llc / other). Foreign status needs the address country or
a W-8 record.

## 7. Output contract

`finding_type: "foreign_withholding"`, `rule ∈ {foreign_withholding_missing, w8_missing_or_expired,
treaty_rate_without_w8, form_1042s_due, foreign_vendor_on_1099}`.

## 8. Limits

- **Not tax advice.** Sourcing and treaty eligibility are flagged for a professional, with the rulebook
  entry cited.
- Never withholds, deposits or files 1042/1042-S.

## 9. Validation

1. **Live:** 0 foreign vendors → 0 findings.
2. **Fixtures:**
   - foreign royalty, no W-8 → 30%;
   - foreign services performed abroad → no withholding finding, but `w8_missing_or_expired` if no W-8.

## 10. Open questions

- Should `Party` model W-8 status (type, signed date, treaty)? It models W-9 already (`w9_on_file`,
  `w9_received_date`).
- One withholding playbook for both regimes (UC-37 s.195 + US-22 Chapter 3) with jurisdiction strategies?
  Recommend yes: same shape, different tables.

## 11. Live evidence — actual calls, 2026-10-04

- `Party.list` → the 8 vendors used on Keystone bills and payments all have `addresses[].state = OH`.
  `us_tax_classification` options per `/api/schemas`: `individual_sole_proprietor | c_corporation |
  s_corporation | partnership | trust_estate | llc_c_corp | llc_s_corp | llc_partnership | other`.
- `Bill.list` → `currency_code`:
  - USD on all 85 paid, open and draft bills except one;
  - INR on 15 void bills and 1 draft. These are the filed B8 / N223 defect (INR bills on a USD company),
    not foreign vendors: the vendor addresses are in Ohio.
  A currency other than USD alone must not mark a vendor as foreign.
