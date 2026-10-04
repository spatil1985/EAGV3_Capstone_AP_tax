# UC-25 — Inward Credit and Debit Notes: Credit Adjustment (VendorCredit)

**Domains: all five · Category: input tax · Verdict: 🟢 Buildable — live findings**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

[UC-19](uc-19-credit-note-time-limit.md) looks at credit notes **we issue**. This use case looks at credit
notes **our suppliers issue to us**, recorded as `VendorCredit`, and at debit notes that raise what we owe.

---

## 1. Question

> *"Our suppliers have given us credit notes. Have we reduced our input credit for them, and are any of them wrong?"*

---

## 2. Statutory basis

- **s.34(1) CGST Act**: a supplier issues a credit note when the value or tax was too high, goods came
  back, or services were deficient. Once the supplier declares it, the **recipient's credit falls by the
  same tax**. It appears in GSTR-2B and is actioned in IMS from October 2024.
- *Our understanding (caveat):* Finance Act 2025 amended s.34(2) so that the supplier gets its output-tax
  reduction only if the recipient has reversed the matching credit. The recipient's reversal now gates
  the supplier's refund.
- **s.34(3)–(4)**: debit notes increase value and tax. The recipient's credit follows the debit note.
  **s.16(4) runs from the debit-note date's FY** (Finance Act 2021).
- **Reverse charge:** a credit note on an RCM supply reduces the recipient's own RCM liability and the
  credit taken on it.
- **s.15(3)(b)**: a post-supply discount reduces value only if it was agreed before the supply and linked
  to the invoices. Otherwise the supplier's credit note does not reduce tax.
- **Consequence:** credit left unreduced is excess credit. It is recovered with **18% interest** (s.50(3))
  and possibly penalty.

---

## 3. Trigger

- **On event:** `vendor_credit.created` and `vendor_credit.updated` through the watcher (G4). The
  watcher's entity list needs `VendorCredit` added.
- **Scheduled monthly** before GSTR-3B (the 15th), feeding UC-23's credit-reduction line.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `VendorCredit.list {"limit":1000}` | `id`, `number`/`vendor_credit_number`, `date`, `status` (`draft/open/closed`), `vendor_id`, `gst_treatment`, `gst_no`, `is_reverse_charge`, `reference_number`, `items[]`, `taxes[]`, `taxable_value`, `total_tax`, `grand_total`, `balance`, `allocation_history[]` |
| `Bill.list` | The original invoice, through `reference_number` → `bill_number`/`number` |
| `CreditNote.list` | Outward credit notes that link to **payable** invoices (UC-19 §6). These are vendor-side documents recorded in the wrong entity |

---

## 5. Algorithm

1. **Population:** `VendorCredit` with status not `draft`.
2. **Tax per credit:** use `taxes[]` rows whose head resolves to IGST, CGST, SGST or cess. Otherwise use
   valid `items[]` lines (Rule 0). Product-named rows are `data_quality`.
3. **`itc_reduction_due`:** `gst_treatment ∈ {business_gst, sez, deemed_export}`, not reverse charge, tax
   above 0. The tax must reduce credit in the month of the credit note. Feeds UC-23.
4. **`rcm_liability_reduction`:** `is_reverse_charge = 1`. This reduces RCM liability and the matching
   credit. Feeds UC-03/UC-21.
5. **`credit_tax_impossible`:** tax above 0 while `gst_treatment ∈ {unregistered_business,
   business_composition, consumer}`. A supplier who can't charge GST cannot give it back, so this is a
   `classification_conflict` row.
6. **`credit_unlinked`:** no `reference_number`, or one that resolves to no bill. Under s.34 the credit must
   reference the original invoice, and it may be an unlinked discount (s.15(3)(b)).
7. **`misfiled_vendor_credit`:** `CreditNote` rows linked to a `direction=payable` invoice. These are
   probably vendor credits recorded as outward credit notes, and they distort both UC-19 and this use case.
8. **Debit notes:** there is no inward debit-note entity. A supplementary bill can't be told apart from a
   normal bill → open question.

### Worked example (REAL, 2026-10-04)

> 100 vendor credits; **74 non-draft** (71 open, 3 closed), carrying tax ₹1,56,450.17.
> - **Registered-supplier credits** (`business_gst`): **20**, tax **₹63,956.20**. This credit must be
>   reduced in the months of the notes.
> - **Reverse-charge credits:** 13, tax ₹19,667.47 → reduce RCM liability.
> - **Tax on credits from suppliers that can't charge GST:** 21 credits, ₹32,479.38. Examples:
>   - VC-2026-00060 (`5ec4c785-0399-4b28-9a66-fd36acadf85a`, unregistered, ₹949.12);
>   - VC-2026-00020 (`43725bb9…`, composition, ₹610.68).
> - **`reference_number` present on 80 of 100.**
>
> Output: *"₹63,956.20 of input credit must be reduced for 20 supplier credit notes. 21 credit notes carry
> GST from suppliers who cannot charge it."*

---

## 6. Known-bad data

- **`VendorCredit.taxes[].tax_type` holds product names** on part of the population ("Feeler Gauge Set
  10337", "Machinist Square 10360", "C-Clamp 10400"). This is the N127/N128 seeder pattern on a third
  entity. It is a candidate extension of N128.
- **SEZ, deemed-export and overseas suppliers carry tax on credits** (₹26,315.76 / ₹18,050.70 /
  ₹15,648.13). Overseas suppliers don't charge Indian GST, so those rows are `classification_conflict`.
- Credits are dated from 2026-04-23, before the first bill (2026-06-07), so some originals can't be in the
  ledger.

---

## 7. Output contract

`finding_type: "itc_adjustment"`, `rule ∈ {itc_reduction_due, rcm_liability_reduction,
credit_tax_impossible, credit_unlinked, misfiled_vendor_credit, data_quality}`. `entity_type:
"VendorCredit"`. Rows that reduce credit carry `reversal_base_amount` (the tax) and the period it belongs
to.

---

## 8. Limits

- It never applies, closes or edits a vendor credit. Applying credits to bills is [UC-41](uc-41-unapplied-vendor-credits.md).
- It doesn't decide whether a credit is commercially valid; it decides only its tax effect.

---

## 9. Validation

1. **Live:** recompute the 20 / 13 / 21 split from `VendorCredit.list`.
2. **Fixture:** a business_gst credit with CGST 900 + SGST 900 → `itc_reduction_due` of 1,800 in the
   credit's month; the same credit flagged reverse charge → `rcm_liability_reduction`.
3. **Head fixture:** a product-named tax row is excluded and emitted as `data_quality`.

---

## 10. Open questions

- How are inward **debit notes** recorded: as a `Bill`, as negative `VendorCredit`, or not at all?
- Do the 12 payable-linked `CreditNote` rows (UC-19 §6) duplicate any `VendorCredit`?
- Should IMS status apply to vendor credits (accept/reject a supplier's credit note)? The entity has no
  `ims_status` field.

---

## 11. Live evidence — actual calls, 2026-10-04

- `VendorCredit.list {"limit":1000}` → 100 rows, dated 2026-04-23 to 2026-09-11.
  - Status: open 71, draft 26, closed 3.
  - Open balance ₹39,83,502.62.
  - `gst_treatment`: business_gst 24, sez 19, unregistered_business 15, overseas 15, deemed_export 11,
    consumer 9, business_composition 7.
- Samples:
  - VC-2026-00076 `2cffc3f9-e55c-4741-b7e1-19fb27da8f76`: open, ₹52,273.00, tax ₹1,398.65.
  - VC-2026-00068 `fd569b80-e21c-4a8a-b8ae-5cb116a212f0`: open, ₹55,451.00, tax ₹1,142.10.
