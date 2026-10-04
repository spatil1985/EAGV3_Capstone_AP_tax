# UC-40 — Vendor Master Data Audit (GSTIN, PAN, MSME, Bank Details, Duplicates)

**Domains: all five · Category: AP control · Verdict: 🟢 Buildable — live findings**
**Status: draft · live evidence 2026-10-04 · US counterpart: [US-16](../US/us-16-vendor-master-audit.md)**

Most other use cases read the vendor record: credit (UC-24), TDS (UC-09/UC-39), MSME (UC-04), RCM
(UC-03/UC-21) and duplicates (UC-05). When the master is wrong, they are all wrong in the same way. This
use case audits the master itself.

---

## 1. Question

> *"Are our vendor records complete and trustworthy enough to pay against, claim credit on and deduct tax for?"*

---

## 2. Statutory basis

- **s.16(2)(a) CGST Act + Rule 36(1) + Rule 46:** credit needs a tax invoice that carries the **supplier's
  GSTIN**. A registered vendor with no GSTIN on record means no credit can be supported.
- **GSTIN structure:** characters 1–2 are the state code, 3–12 the holder's **PAN**, 15 a checksum. A
  GSTIN that fails this is invalid on its face.
- **s.206AA Income-tax Act:** a payee without PAN suffers TDS at **20%** or more. The payer
  short-deducting at the normal rate is in default ([UC-39](uc-39-tds-deductor-setup.md)).
- **MSMED Act s.8 / Udyam:** MSME status is evidenced by a Udyam number. `is_msme` without it can't
  support UC-04's s.15/s.43B(h) treatment.
- **Controls (not statute):** vendor bank-detail changes just before payment are the classic business
  email compromise fraud. Duplicate vendor records are how duplicate payments (UC-05) get past a
  same-vendor check.

---

## 3. Trigger

- **On event:** `party.created` / `party.updated` for parties used as vendors (watcher G4, `Party` added).
  A change of bank details, GSTIN or PAN is a **transition event** and is checked immediately.
- **On event:** `payment_made.created`, to compare the destination account with the master.
- **Scheduled weekly** full sweep.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `Party.list {"limit":1000}` | `name`, `type`, `contact_type`, `gst_no`, `gst_treatment`, `pan`, `tax_id`, `is_msme`, `msme_type`, `msme_no`, `addresses[]` (`state`, `state_code`, `country`), `bank_details[]`, `vendor_bank_account_number`, `vendor_bank_name`, `vendor_bank_code`, `email`, `phone` |
| `Bill.list`, `PaymentMade.list`, `VendorCredit.list` | `vendor_id` (who is actually used as a vendor), bill-level `gst_no`, `PaymentMade.vendor_bank_account_number` |
| `CustomerVendorPreferences.list` | `allow_duplicate_names` |

---

## 5. Algorithm

1. **Population:** every `Party` referenced as `vendor_id` on a bill, payment or vendor credit. **Not**
   just `contact_type = vendor`, which misses most of them (§11).
2. **Identity:**
   - `vendor_type_conflict`: used as a vendor but `contact_type` is `customer` or null, or `gst_treatment
     = consumer` (a consumer doesn't supply).
   - `vendor_address_missing`.
3. **GST:**
   - `vendor_gstin_missing`: `gst_treatment ∈ {business_gst, sez}` and no `gst_no` on the party. Bills
     inherit the risk (UC-24's `itc_supplier_not_identified`).
   - `vendor_gstin_invalid`: format or checksum fails.
   - `vendor_gstin_pan_mismatch`: GSTIN characters 3–12 ≠ `pan`.
   - `vendor_gstin_state_mismatch`: GSTIN state code ≠ the address state.
   - `overseas_tag_on_resident`: from UC-37.
4. **TDS:** `vendor_pan_missing` for payees with TDS-liable spend (UC-09 sections) → s.206AA rate.
5. **MSME:** `vendor_msme_no_missing`: `is_msme` with a blank `msme_no`.
6. **Bank:**
   - `vendor_bank_missing`;
   - `payment_account_mismatch`: the payment's `vendor_bank_account_number` isn't on the master;
   - `bank_change_before_payment`: master bank fields changed within N days (rulebook, default 30) of a
     payment. This needs the watcher's field snapshots.
7. **Duplicates:** `duplicate_vendor` on the same GSTIN, PAN, bank account, email or phone, or the same
   normalised name (legal suffixes stripped).

### Worked example (REAL, 2026-10-04)

> **88 parties are used as vendors.**
> - `contact_type`: vendor **12**, customer **34**, null **42** → **76 `vendor_type_conflict`**.
> - `type`: individual 72, organization 16.
> - `gst_treatment`: null 42, **consumer 30**, business_gst 15, sez 1.
> - **GST:** **0 of 88 have a GSTIN.** **15** are `business_gst` with no GSTIN: Bosch Rexroth India,
>   Kirloskar Pumps Ltd, Godrej Material Handling, Chakan Transport Lines, Precision Fasteners Co, and
>   others. Bill-level `gst_no` is present on 31 of 100 open bills, so **69 credit-bearing bills have no
>   supplier GSTIN anywhere**.
> - **PAN:** 0 of 88.
> - **MSME:** 8 vendors, `msme_no` blank on all 8.
> - **Bank:** 0 vendors with bank details, and `vendor_bank_account_number` is empty on all 134 payments.
>   **Where money went can't be verified at all.**
> - **Duplicates:** none on GSTIN, PAN, bank, email, phone or normalised name.
>
> Output: *"No vendor record carries a GSTIN, PAN or bank details. 15 GST-registered vendors and 69
> credit-bearing bills can't support input credit; every TDS payee is exposed to the 20% no-PAN rate; and
> no payment's destination can be checked against the master."*

---

## 6. Known-bad data

- **Vendors are typed as customers or untyped**, so filtering `contact_type = vendor` finds 12 of 88.
  Always derive the population from documents.
- 30 vendor parties have `gst_treatment = consumer`, meaningless for a supplier → `vendor_type_conflict`.
- US 1099 fields (`tin`, `w9_on_file`, …) exist on India parties and are empty. They must not be read on
  a GST tenant.

---

## 7. Output contract

`finding_type: "vendor_master"`, `entity_type: "Party"`, `rule ∈ {vendor_type_conflict,
vendor_address_missing, vendor_gstin_missing, vendor_gstin_invalid, vendor_gstin_pan_mismatch,
vendor_gstin_state_mismatch, overseas_tag_on_resident, vendor_pan_missing, vendor_msme_no_missing,
vendor_bank_missing, payment_account_mismatch, bank_change_before_payment, duplicate_vendor}`. Each row
carries `affected_documents` (count and value of bills, payments and credits relying on the record), which
is what ranks them.

---

## 8. Limits

- Never edits a vendor record and never blocks a vendor. It escalates with evidence.
- It can't check a GSTIN against the GST portal (active, cancelled or suspended) or a PAN against the
  income-tax database. There's no external API, and those checks are listed as needing one.
- "Vendor is also an employee" can't be checked: employee data is out of this seat's scope.

---

## 9. Validation

1. **Live:** recompute 76 / 15 / 69 / 0 / 8.
2. **Fixtures:**
   - GSTIN `27AASCS7781M1ZQ` with PAN `AASCS7781M` → valid;
   - a changed checksum character → `vendor_gstin_invalid`.
3. **Snapshot fixture:** bank account changed 5 days before a payment → `bank_change_before_payment`;
   changed 60 days before → none.

---

## 10. Open questions

- Ask the platform for **GSTIN status verification** (an `endpoint.gst.verify_gstin`). It would turn
  "format valid" into "active registration", and supplier cancellation is the biggest credit risk not
  checked anywhere.
- Is `bank_details[]` or the flat `vendor_bank_account_number` the source of truth? Both are empty today.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Party.list {"limit":1000}` → 230 parties; 88 referenced as vendors by `Bill` (281), `PaymentMade`
  (134) and `VendorCredit` (100).
  - Vendor address states: Maharashtra 30, Gujarat 8, Karnataka 5, Madhya Pradesh 3; 42 with no address.
- `CustomerVendorPreferences.list` → `allow_duplicate_names: 0`.
- `PaymentMade.list` → `vendor_bank_account_number`, `vendor_bank_name` and `vendor_bank_code` empty on
  all 134.
