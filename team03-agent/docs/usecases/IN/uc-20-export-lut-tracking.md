# UC-20 — Export of Services / LUT Tracking

**Workstream C · Verdict: 🟡 Partial (classification data exists; LUT validity does not)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Backs:** F21 / GAP-5 · **Owns shared contract:** place-of-supply determination (used by UC-03, UC-21)

---

## 1. Question

> *"Are our export invoices genuinely zero-rated, and is our LUT still valid?"*

(Verbatim from `spec.md` UC-20.)

---

## 2. Statutory basis

- **Section 16(1), IGST Act — zero-rated supply:** (a) export of goods or services;
  (b) supply to an **SEZ developer or unit**.
- **Section 16(3)** — zero-rated supply is made either **under a Letter of Undertaking
  (LUT) without paying IGST**, or on payment of IGST with a refund claimed.
- **Rule 96A, CGST Rules** — an LUT is furnished **for a financial year** (Form GST
  RFD-11). It lapses at year end and must be renewed.
- **Section 2(6), IGST Act — export of services** requires all five: supplier in India;
  recipient outside India; **place of supply outside India**; **payment in convertible
  foreign exchange** (or INR where RBI permits); and supplier and recipient are not
  merely establishments of one person.
- **SEZ supplies** are inter-state by law (s.7(5)(b), IGST Act): IGST under LUT, never
  CGST/SGST.
- **Consequence:** zero-rating without a valid LUT means IGST was payable and is
  recoverable with interest (a refund can be claimed later, but the cash is out). An
  "export" failing s.2(6) is a domestic supply with **unpaid tax**.

---

## 3. Trigger

- **Document event:** on every receivable invoice with `gst_treatment ∈ {overseas, sez,
  deemed_export}`.
- **Annually, 1 April:** every LUT lapses, and no zero-rated invoice should issue until
  the new FY's LUT is recorded.
- **Period:** invoice date against the FY of the LUT.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Invoice.list` | `{"direction":"receivable","gst_treatment":"sez","limit":1000}` and again for `"overseas"`, `"deemed_export"` — one enum value per call | 15 SEZ live; 0 overseas; 0 deemed_export (receivable) |
| `Party.get` | `{"id": party_id}` | Recipient location, `gst_treatment` |
| `TaxExemption.list` | `{"limit":100}` | **The only LUT record available** |

**Invoice fields:** `gst_treatment`, `place_of_supply`, `destination_of_supply`,
`currency_code`, `exchange_rate`, `party_id`, `items[].igst_amount` / `cgst_amount` /
`sgst_amount`.

**TaxExemption fields — all of them:** `id`, `exemption_reason`, `associated_with`
(`contact | item`), `description`, `created_at`, `updated_at`, `created_by`,
`updated_by`, `company_id`. **No `valid_from`/`valid_to`, no FY, no ARN, no link to a
specific party or item id.**

---

## 5. Algorithm

**Part A — zero-rating conditions (per invoice)**
1. `sez`: the supply must carry **no CGST/SGST** (it is inter-state by law). Either
   IGST = 0 under LUT, or IGST charged (refund route).
   - CGST or SGST > 0 → `sez_intra_state_tax_charged`.
   - All tax = 0 → requires a valid LUT (Part B).
2. `overseas` (export of services): all five s.2(6) conditions:
   - `place_of_supply` outside India;
   - `currency_code ≠ INR`, or an explicit RBI-permitted INR flag (none exists);
   - recipient `Party` located outside India.
   Any failure → `export_condition_failed`: treat as a domestic supply, with tax due.
3. `deemed_export`: not zero-rated. The supplier charges tax, and the recipient/supplier
   claims a refund. Tax = 0 → `deemed_export_untaxed`.

**Part B — LUT validity**
4. Find a `TaxExemption` row whose `exemption_reason` matches `/LUT|Letter of
   Undertaking/i`.
   - None → every zero-tax zero-rated invoice → `lut_missing`.
   - Found → **validity cannot be checked** (no dates). Emit `lut_validity_unknown` once
     per FY, not per invoice.
5. Where the playbook carries the LUT's ARN and FY (workaround until GAP-5 is closed),
   invoices dated outside that FY → `lut_expired`.

### Worked example (REAL — INV-2026-00126)

> **INV-2026-00126** (`0c02d5a7-a7e0-43b7-83bf-bc187a692a4e`), customer **Vardhman
> Aerospace SEZ Unit**, `gst_treatment: sez`, `place_of_supply: 29` (Karnataka),
> `currency_code: INR`, `exchange_rate: 1`, all tax = 0, `grand_total ₹3,58,087.00`.
>
> ```
> Part A: sez, CGST=SGST=IGST=0      → zero-rated without payment → LUT required
> Part B: TaxExemption "SEZ supply — Letter of Undertaking, no IGST" (13ff7f65…) exists
>         no valid_from / valid_to, no FY, no party link    → lut_validity_unknown
> ```
>
> Output: *"15 SEZ invoices (Vardhman Aerospace SEZ Unit, ₹X total) are zero-rated
> under an LUT. An LUT record exists, but the platform stores no validity period, so
> FY 2026-27 cover cannot be confirmed. Record the LUT ARN and FY."*

---

## 6. Known-bad data

- **No genuine export exists:** 0 receivable invoices with `gst_treatment = overseas`.
  Part A step 2 has no live case.
- **All 15 SEZ invoices are INR.** That is correct for SEZ (INR is permitted), so it
  must not be flagged by the overseas currency test. Keep the SEZ and overseas branches
  separate.
- **`destination_of_supply` is empty** on the SEZ invoices. Use `place_of_supply`.

---

## 7. Output contract

`finding_type: "zero_rated_supply"`, `rule ∈ {lut_missing, lut_validity_unknown,
lut_expired, export_condition_failed, sez_intra_state_tax_charged,
deemed_export_untaxed}`. The `lut_*` rules are FY-level aggregates listing the invoices
they cover.

---

## 8. Limits

- **Cannot verify LUT validity.** No entity models it (GAP-5 / F21). The workaround
  (LUT ARN + FY carried in the playbook) is manual.
- Cannot confirm FX realisation (payment in convertible foreign exchange) from
  `PaymentReceived`: there is no currency on receipts in the fields read.
- Never alters invoice treatment.

---

## 9. Validation

1. **Live SEZ count:** 15 invoices → 1 `lut_validity_unknown` aggregate covering all 15.
2. **Fixture:** an `overseas` invoice in INR to a Party in India →
   `export_condition_failed` (two conditions).
3. **Fixture:** an `sez` invoice with CGST + SGST → `sez_intra_state_tax_charged`.

---

## 10. Open questions

- **F21 evidence:** the `TaxExemption` field list is the proof. A row that *names* an
  LUT but cannot *date* it.
- **Should the playbook carry LUT ARNs per FY?** It is a manual step, but it closes the
  gap today.
- **Place-of-supply contract for UC-03/UC-21:** the determination here is invoice-side
  (outward). UC-21 needs the inward equivalent (recipient's location for import of
  services). Specify it once, here, before UC-21 implements its own.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-20 Export LUT tracking`.

**Call 1 — `Invoice.list {"direction":"receivable","gst_treatment":"sez","limit":1000}`**
→ **15** invoices, all to Vardhman Aerospace SEZ Unit, all `place_of_supply: 29`, all
INR, `exchange_rate 1`, **tax 0**. Samples: INV-2026-00126 ₹3,58,087 · INV-2026-00171
₹3,15,864 · INV-2026-00053 ₹2,48,106 · INV-2026-00151 ₹2,17,360.

**Call 2 — `TaxExemption.list {"limit":100}`** → 8 rows, including:

| id | `exemption_reason` | `associated_with` |
|---|---|---|
| `13ff7f65-e90a-49e1-9aa1-6c71a4c59ed2` | SEZ supply — Letter of Undertaking, no IGST | contact |
| `32ec18df-ffee-4ae3-8067-9196474b2a3f` | Export under LUT | contact |

Neither has dates or a party id. **GAP-5 confirmed at field level.**

**Related find:** `RetainerInvoice` RET-2026-00002 holds a ₹6,00,000 advance from the
same SEZ customer (UC-22).
