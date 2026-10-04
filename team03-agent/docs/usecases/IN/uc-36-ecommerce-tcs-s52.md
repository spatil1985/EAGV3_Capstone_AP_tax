# UC-36 — Retail: Sales Through E-Commerce Operators — s.52 TCS and s.9(5)

**Domains: retail (marketplace sellers); clinic pharmacy and agency where they sell through platforms · Category: output tax, domain-specific · Verdict: 🔴 Blocked — no sales-channel field and no TCS-credit record (filed as F22, GAP-6)**
**Status: draft · spec for the gap argument · added 2026-10-04**

`assignment.md` §6 says GAP-6 *"has no use case of its own… it needs one, scoped alongside UC-17 and
UC-18 for retail."* This is that use case.

---

## 1. Question

> *"Do our marketplace sales, and the tax the marketplace collected on them, agree with what we report — and have we claimed that collected tax back?"*

---

## 2. Statutory basis

- **s.52 CGST Act:** an e-commerce operator (marketplace) **collects tax at source** on the net taxable
  supplies made through it.
  - *Our understanding (caveat):* the rate is **0.5%** (0.25% CGST + 0.25% SGST, or 0.5% IGST) from
    10 July 2024, reduced from 1%.
  - The operator reports it in GSTR-8 by the 10th. The seller **accepts it**, and it is credited to the
    seller's electronic **cash** ledger.
- **s.9(5):** for notified services sold through an operator, the **operator pays the GST** and the seller
  must not: restaurant services, accommodation, housekeeping, passenger transport.
- **s.24(ix):** sellers supplying through an operator must register, with notified exceptions.
  *Our understanding (caveat):* from 1 October 2023 small goods suppliers are exempted, and composition
  dealers may supply goods through operators. That affects [UC-17](uc-17-composition-scheme.md).
- **GSTR-1 Tables 14 and 15** report supplies through operators (s.52) and s.9(5) supplies separately.
- **Consequence:**
  - marketplace-reported sales that don't match the seller's GSTR-1 → notices;
  - TCS not accepted → the cash sits unclaimed;
  - GST paid on s.9(5) services → paid twice.

---

## 3. Trigger

- **Scheduled monthly** after the 10th, once GSTR-8 data is available, and before the seller's GSTR-1.
- **On request.**

---

## 4. Input contract: what would be needed

| Need | Platform today |
|---|---|
| Marketplace identity per sale | ❌ `Invoice` has no channel or operator field. A marketplace `Party` as customer is a workaround, but the end buyer's place of supply is then lost |
| Operator-reported sales (GSTR-8 / settlement report) | ❌ No entity, and no ingest tool |
| TCS credited to the cash ledger | ❌ No cash-ledger entity. `Invoice/Bill.tcs_*` fields are **income-tax** TCS (s.206C), not GST TCS |
| s.9(5) service flag on items | ❌ None. `Item.product_type` is goods/services only |
| `TaxNexus.nexus_type = marketplace_facilitator` | ⚠️ A US concept (see [US-12](../US/us-12-marketplace-facilitator-sales.md)); present as 26 stray rows on the India tenant |

---

## 5. Algorithm (as specified, for when the data exists)

1. Sales through each operator for the month, net of returns.
2. **`ecommerce_sales_mismatch`:** own sales vs operator-reported, per operator. Difference > ₹1 → finding.
3. **`tcs_expected`** = 0.5% × net taxable through the operator. Compare with the TCS credited →
   `tcs_unclaimed` / `tcs_short_collected`.
4. **`s9_5_tax_paid_by_seller`:** GST charged by the seller on s.9(5) services sold through an operator.
5. **`composition_ecommerce_breach`:** a composition dealer selling services through an operator, or goods
   outside the permitted conditions (handed to UC-17).

### Worked example (CONSTRUCTED)

> A retailer's August sales through a marketplace: ₹10,00,000 net taxable, intra-state.
> ```
> TCS expected = 0.5% × 10,00,000 = ₹5,000 (CGST ₹2,500 + SGST ₹2,500)
> TCS credited per operator statement = ₹4,250 → shortfall ₹750; own GSTR-1 Table 14 shows ₹9,20,000 → ₹80,000 unreported
> ```

---

## 6. Known-bad data

- **26 `TaxNexus` rows of type `marketplace_facilitator` exist on the India tenant**, with garbage state
  codes (`DG8594/5369`). They are US sales-tax constructs on a GST company, the same class of defect as
  N126 (fixed for `TaxJurisdiction` by removing the rows). Candidate bug report, and they must not be read
  as Indian marketplace data.

---

## 7. Output contract

`finding_type: "ecommerce_tcs"`, `rule ∈ {ecommerce_sales_mismatch, tcs_unclaimed, tcs_short_collected,
s9_5_tax_paid_by_seller, composition_ecommerce_breach}`.

---

## 8. Limits

- Can't run until a sales channel and operator statements exist. The playbook routes `blocked`, citing
  F22.
- Never accepts TCS on the portal.

---

## 9. Validation

Fixtures only, as in §5. **No live validation is possible:** neither tenant sells through a marketplace.

---

## 10. Open questions: the gap argument (F22)

- **Minimum platform change:**
  - a `sales_channel` / `ecommerce_operator_id` on `Invoice`;
  - a `MarketplaceSettlement` entity, or an import of GSTR-8 / operator reports;
  - a GST TCS credit record.
  This is enough for steps 1–4.
- Should s.9(5) be a per-item flag (`Item.ecommerce_operator_liable`)?

---

## 11. Live evidence — actual calls, 2026-10-04

- `/api/schemas` → `Invoice` has no channel/operator field. `tcs_tax_name`, `tcs_percentage`,
  `tcs_amount` and `nature_of_collection` are income-tax TCS fields, and are 0 or null on all 322
  receivable invoices.
- `TaxNexus.list` (India tenant) → 100 rows: physical 27, **marketplace_facilitator 26**, affiliate 20,
  economic 19, none 8. State codes like `LD3146/5370`.
