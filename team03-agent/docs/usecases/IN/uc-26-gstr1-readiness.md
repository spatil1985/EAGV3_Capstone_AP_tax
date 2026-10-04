# UC-26 — GSTR-1 Readiness: Outward Supply Classification and Tax Head

**Domains: all five (retail B2C, agency exports, school/clinic exempt lines) · Category: output tax · Verdict: 🟡 Partial — classification and tax-head checks run live; the GSTR-1 oracle does not reconcile**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Is every sale this month going into the right part of GSTR-1, with the right kind of GST?"*

---

## 2. Statutory basis

- **s.37 CGST Act + Rule 59**: outward-supply statement GSTR-1, due on the 11th of the next month for
  monthly filers. Each document goes into one table:

  | Table | Contents |
  |---|---|
  | 4 | B2B, by recipient GSTIN |
  | 5 | B2CL: **inter-state** B2C invoices above ₹1 lakh |
  | 6 | Exports, SEZ and deemed exports |
  | 7 | B2CS: all other B2C, summarised |
  | 8 | Nil-rated, exempt and non-GST |
  | 9 | Amendments, credit and debit notes |
  | 11 | Advances |
  | 12 | HSN summary |
  | 13 | Documents issued |

  *Our understanding (caveat): Notification 12/2024-CT lowered the B2CL threshold from ₹2.5 lakh to
  ₹1 lakh from August 2024, and introduced the optional amendment form GSTR-1A.*
- **s.7–8 IGST Act**: the tax head follows the place of supply:
  - **inter-state** (supplier state ≠ place of supply) → **IGST**;
  - **intra-state** → **CGST + SGST**.
- **s.77 CGST / s.19 IGST**: tax paid under the wrong head must be paid again under the right head. The
  wrong-head amount is refunded (Rule 89(1A), within 2 years). *Our understanding: no interest is due on
  the right-head payment if made promptly (caveat).*
- **Consequence:**
  - wrong classification → recipient's credit is missing from their GSTR-2B (B2B shown as B2C);
  - wrong head → tax paid twice until refunded;
  - HSN errors → GSTR-1 validation failures.

---

## 3. Trigger

- **Scheduled monthly on the 8th**, ahead of the 11th due date. It runs again on the 10th.
- **On event:** `invoice.created` / `credit_note.created`. The tax-head and table checks are per document,
  so they can run at issue.
- **On request.**

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Invoice.list {"limit":1000}` | `direction`, `status`, `date`, `gst_treatment`, `gst_no`, `party_id`, `place_of_supply`, `source_of_supply`, `taxable_value`, `grand_total`, `taxes[]` (`tax_type`, `amount`), `items[]` (`hsn_or_sac`, tax fields) |
| `Party.get` | Customer `gst_no`, `gst_treatment`, `place_of_supply` |
| `CreditNote.list` | Table 9B (item-level tax, N128) |
| `Item.list` | `tax_preference`, `hsn_or_sac`, for Table 8 and Table 12 |
| `OrgProfile.list` | `gstin`, `state`: the supplier state for the inter/intra test |
| `GSTReturn.list` | `return_type=GSTR-1`: `taxable_amount`, `total_transactions`. **The oracle** |

---

## 5. Algorithm

1. **Population:** receivable invoices in the period, not draft or cancelled, plus credit notes.
2. **Table assignment** (deterministic):
   - `sez`/`deemed_export`/`overseas` → 6;
   - `business_gst` with recipient GSTIN → 4;
   - `consumer`/`unregistered` with inter-state POS and `grand_total` above ₹1,00,000 → 5;
   - other B2C → 7;
   - exempt-item lines → 8.
3. **`b2b_without_gstin`:** `business_gst` with no GSTIN on the invoice or the party.
4. **`wrong_tax_head_for_pos`:**
   - supplier state code (from `OrgProfile.gstin`[:2]) ≠ POS, but CGST/SGST charged;
   - or the reverse: intra-state but IGST charged.
   The exposure is the tax that must be paid again under the right head.
5. **`hsn_missing` / `hsn_digits_short`:** HSN digit count below the AATO rule (4 or 6 digits; [UC-29](uc-29-turnover-based-obligations.md)).
6. **`table_classification_missing`:** `gst_treatment` null on a live invoice.
7. **Oracle:** compare the period's computed taxable value and document count with the GSTR-1 row.
   Mismatch → `stored_value_mismatch`.

### Worked example (REAL, 2026-10-04)

> 250 live receivable invoices:
> - **Table 4 (B2B):** 208, all with recipient GSTIN.
> - **Table 7 (B2CS):** 27.
> - **Table 6 (SEZ):** 15, zero-rated.
> - **Table 5 (B2CL):** 0.
> - **Table 9B:** 25 credit notes.
>
> **Wrong tax head:** 12 invoices with a place of supply outside Maharashtra (27) were charged CGST+SGST
> instead of IGST:
> - by place of supply: Gujarat 24 ×6, Madhya Pradesh 23 ×3, Karnataka 29 ×3;
> - taxable ₹2,50,847.85, tax ₹45,152.62.
> - Example: **INV-2026-00179** (`dd9b9066-7e31-4e3c-8a49-af55897c6547`), 2026-08-25, POS 24, taxable
>   ₹47,996.00, charged CGST ₹4,319.64 + SGST ₹4,319.64 where IGST ₹8,639.28 was due.
>
> 0 intra-state invoices charged IGST; HSN present (8 digits) on every live line.
>
> Output: *"12 inter-state invoices (₹45,152.62 of tax) were charged CGST+SGST instead of IGST: that tax
> must be paid again as IGST and the wrong-head amount refunded. Table split: 208 B2B, 27 B2CS, 15 SEZ."*

---

## 6. Known-bad data

- **GSTR-1 rows don't reconcile:**
  - August 2026 row: ₹2,63,10,000 over 161 documents; the ledger has ₹46,44,015.04 over 14 invoices.
  - Filed July row: ₹2,48,50,000 over 148; the ledger has ₹1,34,98,123.63 over 27.
  Same issue as UC-23 §6.
- `items[].tax_percentage` is null on all 437 live outward lines, so the rate comes from the `taxes[]` head
  names ("CGST @ 9%", "IGST @ 18%").
- 100 lines without HSN exist, but **all on cancelled or draft invoices**. Count only live documents.

---

## 7. Output contract

`finding_type: "outward_return"`, `rule ∈ {wrong_tax_head_for_pos, b2b_without_gstin, hsn_missing,
hsn_digits_short, table_classification_missing, stored_value_mismatch}`. There is also a context row per
table with count and taxable value: the GSTR-1 preview.

---

## 8. Limits

- Never files GSTR-1 or GSTR-1A, and never edits an invoice. Correcting an invoice is a human action.
- The refund of wrong-head tax (s.77) is reported, not claimed.

---

## 9. Validation

1. **Live:** the 12 wrong-head invoices recomputed from `place_of_supply` and `taxes[]`.
2. **Fixtures:**
   - inter-state B2C at ₹1,00,000.01 → Table 5; at ₹1,00,000 → Table 7.
   - Intra-state with IGST → `wrong_tax_head_for_pos`.
3. **Oracle,** once GSTR-1 rows are generated from the ledger.

---

## 10. Open questions

- Is `place_of_supply` the state code (as observed: "27", "24") on every tenant? The schema says text.
- Should the 12 wrong-head invoices be filed as a candidate bug (the tax engine ignored POS), or are they
  manually keyed? `tax_computation_note` may say.
- Are exempt (Table 8) lines identified by `Item.tax_preference`, as UC-07 does? 15 `tax_exempt` items
  exist; none appear on live invoices.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Invoice.list {"limit":1000}` → 487 invoices, 322 receivable, 250 live.
  - `gst_treatment`: business_gst 208, consumer 27, sez 15.
  - `place_of_supply`: 27 ×177, 24 ×52, 29 ×18, 23 ×3.
  - Tax rows: "CGST @ 9%" 189, "SGST @ 9%" 189, "IGST @ 18%" 46.
- Wrong-head examples:
  - INV-2026-00176 `bded58ca-1e96-4cdd-aab6-7e6bc9b338e9` (POS 23, ₹8,718.10, CGST/SGST ₹784.63 each);
  - INV-2026-00182 `eacd744a-caa1-4e51-a072-9f245e663a64` (POS 24, ₹5,762.05).
- `GSTReturn.list` → GSTR-1 08-2026 `a0e4a5c8-5d51-40d2-a335-62ece0778c36` (unfiled, due 2026-09-11) and
  GSTR-1 07-2026 `4f2c8b10-e175-4957-9e62-c13dc14036fa` (filed 2026-08-08).
