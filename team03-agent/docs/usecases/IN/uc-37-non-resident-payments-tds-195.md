# UC-37 — Payments to Non-Residents: TDS under s.195 and Form 15CA/15CB

**Domains: agency (overseas freelancers, platforms, licences); manufacturing (foreign technical fees, royalties); clinic and school (foreign software and journals) · Category: TDS / withholding · Verdict: 🟡 Partial — buildable; no genuine non-resident vendor in the data**
**Status: draft · live evidence 2026-10-04 · GST side of the same payments: [UC-21](uc-21-import-of-services-rcm.md)**

---

## 1. Question

> *"Before we pay a foreign vendor, have we deducted the right tax and got the remittance paperwork done?"*

---

## 2. Statutory basis

*Section numbers are from the Income-tax Act 1961. Our understanding is that the Income-tax Act 2025
renumbers them from 1 April 2026; confirm before showing output to a user (IN README caveat).*

- **s.195:** whoever pays a **non-resident** any sum chargeable to tax in India (fees for technical
  services, royalty, interest, and others) must deduct tax at the time of payment or credit, whichever is
  earlier.
  - The rate is the rate in force (e.g. s.115A for royalty and technical fees, plus surcharge and cess), or
    the **tax-treaty rate** if lower.
  - Using the treaty rate needs a tax residency certificate, Form 10F, and usually a no-permanent-
    establishment declaration.
- **s.206AA:** with no PAN (or the alternative documents under Rule 37BC), TDS is at least 20%.
- **Rule 37BB / Form 15CA–15CB:** an online declaration (15CA) before remitting, and a chartered
  accountant's certificate (15CB) above ₹5 lakh, unless the payment is on the exempt list.
- *Our understanding (caveat):* the **6% equalisation levy** on online advertising paid to non-residents
  was **abolished from 1 April 2025** (Finance Act 2025). Payments made after that date don't need it.
- **Consequence:** deduction not made → the **payment is disallowed** (s.40(a)(i)), the payer is an
  "assessee in default" (s.201), and interest runs at 1–1.5% per month.

---

## 3. Trigger

- **On event:** `bill.created` or `bill.approval_status_changed` for a vendor with a non-Indian address or
  `gst_treatment = overseas`, **before payment**.
- **On event:** `payment_made.created` to such a vendor, to check that TDS and 15CA/CB were done.
- **Scheduled monthly**, before the 7th TDS deposit date.
- **On request.**

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Party.list` / `Party.get` | `gst_treatment`, `addresses[].country`, `pan`, `tax_id`, `currency_id` |
| `Bill.list` | `vendor_id`, `currency_code`, `items[]` (`hsn_or_sac`, description), `tds_percentage`, `tds_amount`, `tds_section` |
| `PaymentMade.list` | `vendor_id`, `amount`, `tds_amount`, `date`, `exchange_rate` |
| `Expense.list` | Card-paid foreign subscriptions: `gst_treatment = overseas`, `currency_code` |
| `config/overrides/nonresident_docs.yaml` | Tax residency certificate, Form 10F, no-PE declaration, 15CA/CB references (not in the data model) |

---

## 5. Algorithm

1. **Who is non-resident:** the vendor's address country ≠ India, **or** non-INR billing. `gst_treatment =
   overseas` alone is **not** enough: UC-21 found it on Indian vendors.
2. **Classify the payment** (playbook table, G6): technical fees / royalty / software licence /
   advertising / goods. Goods purchases are generally outside s.195 (no Indian income).
3. **`tds_195_not_deducted`:** taxable class, and `tds_amount = 0` on the bill or payment. Exposure =
   applicable rate × amount.
4. **`dtaa_rate_without_documents`:** a reduced rate applied, but no tax residency certificate / Form 10F
   on file.
5. **`tds_206aa_rate_short`:** no PAN or alternative documents, and rate < 20%.
6. **`form_15ca_cb_missing`:** remittance with no 15CA (and no 15CB above ₹5 lakh) reference on file.
7. **`overseas_tag_on_resident`:** `gst_treatment = overseas` but an Indian address and INR billing. This
   is the vendor-master conflict, sent to [UC-40](uc-40-vendor-master-audit.md).

### Worked example

> **Live:**
> - 12 bills, 11 expenses and 15 vendor credits are tagged `overseas`;
> - **all are in INR**, and every vendor with an address is in **India**;
> - no TDS on any of them.
> → 0 genuine non-resident payments, and the overseas-tagged documents produce
> `overseas_tag_on_resident` rows instead.
>
> **Constructed:** an agency pays a US freelancer USD 6,000 (₹5,04,000 at 84.00) for design (technical
> services).
> ```
> treaty rate (India–US, fees for included services) 15% with TRC + Form 10F → TDS ₹75,600
> no documents → domestic rate ~20% + surcharge + cess → TDS ≈ ₹1,04,000
> remittance > ₹5 lakh → Form 15CB + 15CA Part C required before payment
> ```

---

## 6. Known-bad data

- **`gst_treatment = overseas` is set on Indian, INR vendors** (UC-21 §11, confirmed again here). Never
  infer non-residence from it alone.
- `PaymentMade.tds_amount` is 0 on all 134 payments, and `DirectTaxPreferences.auto_apply_tds = 0`. TDS
  isn't being applied at payment for any vendor ([UC-39](uc-39-tds-deductor-setup.md)).

---

## 7. Output contract

`finding_type: "nonresident_withholding"`, `rule ∈ {tds_195_not_deducted, dtaa_rate_without_documents,
tds_206aa_rate_short, form_15ca_cb_missing, overseas_tag_on_resident}`.

---

## 8. Limits

- **Not tax advice.** Treaty rates, PE status and whether income is chargeable at all are judgments
  flagged for a professional. The agent applies a table and says which entry it used.
- Never files 15CA, never certifies 15CB, never remits.

---

## 9. Validation

1. **Live:** 38 overseas-tagged documents (12 bills, 11 expenses, 15 vendor credits). Expect 0
   `tds_195_*` findings and up to 38 `overseas_tag_on_resident` rows.
2. **Fixtures:**
   - foreign address, technical fees, TDS 0 → `tds_195_not_deducted`;
   - the same with TDS at 15% but no Form 10F on file → `dtaa_rate_without_documents`.

---

## 10. Open questions

- Where would treaty documents and 15CA/CB references live? `FileAttachment` exists, but linking it to a
  vendor and a payment isn't modelled.
- Does s.195 need its own playbook, or should it be a section row in a broadened TDS playbook (UC-09 +
  UC-39)? Recommend one TDS playbook with a section table.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Bill.list`, `Expense.list`, `VendorCredit.list` → documents with `gst_treatment = overseas`:

  | Entity | Count | Currency | Vendor country |
  |---|---|---|---|
  | Bill | 12 | INR | India (12) |
  | Expense | 11 | INR | India (5 with addresses) |
  | VendorCredit | 15 | INR | India (5 with addresses) |

  `tds_amount > 0` on none.
- `DirectTaxPreferences.list` → `auto_apply_tds: 0`, `default_tds_section: null`.
