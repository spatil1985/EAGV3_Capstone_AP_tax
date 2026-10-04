# US-16 — Vendor Master Data Audit (US instance of UC-40)

**US · Domains: all five · Verdict: 🟢 Buildable — live findings**
**IN spec (algorithm, output contract):** [`../IN/uc-40-vendor-master-audit.md`](../IN/uc-40-vendor-master-audit.md) · **related:** [US-06](us-06-form-1099-readiness.md) (1099 and backup withholding) · **live evidence 2026-10-04**

---

UC-40's structure carries over: the population is derived from documents, and the checks cover
identity, tax ID, bank and duplicates. The tax-ID checks are US-specific. Sections 1, 3 and 7 are as UC-40.

## 2. Statutory basis (US)

- **IRC §6109 / Form W-9:** a payee's **TIN** (SSN or EIN) is needed for information returns. **IRC
  §3406:** a missing or incorrect TIN requires **backup withholding at 24%** on reportable payments
  (US-06).
- **1099 scope:** payments to corporations are generally not reportable, **except attorneys' fees and
  medical and health-care payments** (1099-MISC box 6). So `us_tax_classification` has to agree with
  `is_1099_vendor`.
- **Sales tax and unclaimed property:** the vendor's address state drives use-tax sourcing (US-02) and the
  escheat state ([US-21](us-21-unclaimed-property-escheat.md)).
- **Controls:** duplicate vendor records and bank-detail changes, as UC-40.

## 4. Input contract (US fields)

`Party`: `tin`, `tin_type` (`ssn\|ein\|itin\|atin`), `w9_on_file`, `w9_received_date`, `w9_signed_name`,
`us_tax_classification`, `is_1099_vendor`, `form_1099_type`, `form_1099_box`, `exempt_payee_code`,
`backup_withholding`, `addresses[]`, `vendor_bank_account_number`, `bank_details[]`.

## 5. Algorithm (US rules, in addition to UC-40's identity, bank and duplicate rules)

1. **`vendor_tin_missing`:** `tin` empty, for a vendor with reportable or significant spend. Check
   `Party.get` before concluding, because list output may mask the TIN (§6).
2. **`vendor_tin_format_invalid`:** EIN not 9 digits (`XX-XXXXXXX`), or SSN not 9 digits.
3. **`tin_type_classification_conflict`:** a corporation (`c_corporation`, `s_corporation`, `llc_c_corp`,
   `llc_s_corp`) with `tin_type = ssn`.
4. **`w9_missing`:** `w9_on_file = 0` for a vendor with 1099-relevant spend (→ US-06 backup withholding).
5. **`form_1099_flag_conflict`:** `is_1099_vendor = 1` on a corporation, outside the attorney and medical
   exceptions; or `is_1099_vendor = 0` on a sole proprietor or partnership with service payments.
6. **`form_1099_box_conflict`:** `form_1099_box` inconsistent with what the vendor supplies (e.g. MISC-1
   Rents for a service vendor). Account / description → expected box comes from the rulebook.
7. **`vendor_address_missing`:** needed for sourcing and escheat.

### Worked example (REAL, 2026-10-04)

> 8 vendors used on bills and payments, all with Ohio addresses, `contact_type` null on all 8 (as on
> India, UC-40 §6).
>
> | Vendor | `us_tax_classification` | TIN type | W-9 | 1099 box |
> |---|---|---|---|---|
> | Hartville Sign & Graphics | individual_sole_proprietor | ssn | ✓ | **MISC-1** |
> | J. Miller Welding | individual_sole_proprietor | ssn | ✓ | NEC-1 |
> | Canton Industrial Consulting | individual_sole_proprietor | ssn | **✗** | NEC-1 |
> | Tuscarawas Machining Services LLC | llc_partnership | ein | ✓ | NEC-1 |
> | Ohio Valley Freight Lines | s_corporation | ein | ✓ | — |
> | Midwest Tool & Abrasive Co | c_corporation | ein | ✓ | — |
> | Stark County Powder Coating Inc | c_corporation | ein | ✓ | — |
> | Apex Metals Supply LLC | llc_c_corp | ein | ✓ | — |
>
> - `tin` is **empty in `Party.list` output on all 8**, while `tin_type` is set → `vendor_tin_missing`
>   candidates, pending a `Party.get` check.
> - Classification and 1099 flags are consistent: corporations are not flagged; sole proprietors and the
>   partnership are.
> - **Hartville Sign & Graphics is set to box MISC-1 (Rents).** For a sign-and-graphics service vendor,
>   NEC-1 (non-employee compensation) is the likely box, so this is a `form_1099_box_conflict` candidate
>   for human review.
> - `w9_missing`: Canton Industrial Consulting. US-06 found the same; it is already on the board as N398
>   (team07).
> - No bank details on any vendor, and `PaymentMade.vendor_bank_account_number` is empty on all 67
>   payments, so destinations can't be verified (as UC-40).
> - Duplicates: none.

## 6. Known-bad data (US)

- **TIN may be withheld from list responses** (privacy masking), or it may genuinely be blank. Resolve with
  `Party.get` on one vendor before reporting 8 missing TINs as a defect.
- India-only fields (`gst_no`, `pan`, `msme_*`) exist on US parties and are empty. They are never read.

## 8–9. Limits and validation (US)

As UC-40. No IRS TIN-matching API is available, so "format valid" is the limit of verification.
Fixtures:
- `c_corporation` + `ssn` → `tin_type_classification_conflict`;
- a sole proprietor with `w9_on_file = 0` and $2,500 of service payments → `w9_missing` → US-06 backup
  withholding.

## 10. Open questions (US)

- Is `tin` masked in list output? Decide by `Party.get` on Hartville Sign & Graphics
  (`f9af86af-4604-4abd-856d-473057ce7b75`).

## 11. Live evidence — actual calls, 2026-10-04

- `Party.list {"limit":1000}` → 120 parties; 8 referenced by `Bill` (101) and `PaymentMade` (67).
  - `tin_type`: ein 5, ssn 3. `w9_on_file`: 7. `is_1099_vendor`: 4. `backup_withholding`: 0.
  - `us_tax_classification`: individual_sole_proprietor 3, c_corporation 2, llc_c_corp 1, s_corporation 1,
    llc_partnership 1. All addresses OH.
- `PaymentMade.list` → 67, `vendor_bank_account_number` empty on all.
