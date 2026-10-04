# UC-24 — Unclaimed and At-Risk Input Tax Credit (IMS / GSTR-2B and the s.16(4) Deadline)

**Domains: all five · Category: core tax · Verdict: 🟡 Partial — IMS-status checks run live; matching to GSTR-2B at line level is blocked (no line data)**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

The India half of *"what is unclaimed?"*, which is the second part of the Core Challenge Prompt. For
exempt-output tenants such as schools and clinics, the question inverts (spec.md §2.1): the useful answer
is credit claimed that must be reversed, which comes from UC-08/UC-15.

---

## 1. Question

> *"Which input credit can we still claim, which have we claimed that we shouldn't have, and what will we lose if we wait?"*

---

## 2. Statutory basis

- **s.16(2)(aa) CGST Act + Rule 36(4)** (from 1 January 2022): credit is available only for invoices the
  supplier has reported and that appear in the recipient's **GSTR-2B**.
- **Invoice Management System (IMS)** (from October 2024): the recipient can accept, reject or keep
  pending each supplier document before GSTR-2B is generated on the 14th.
  - Documents with no action are **deemed accepted** into GSTR-2B.
  - Rejected documents are excluded.
  - *Our understanding (caveat): "pending" is allowed only for a limited period and for certain document
    types.*
- **s.16(4)** (Finance Act 2022): credit on an invoice or debit note of an FY can't be taken after
  **30 November following the end of that FY**, or the annual return date if earlier. For debit notes,
  the FY is that of the debit-note date.
- **Consequence:**
  - Credit taken on a rejected invoice, or one not in GSTR-2B, is reversed with **interest at 18%**
    (s.50(3), when the credit was both availed and used).
  - Credit not taken by the s.16(4) date is **lost permanently**.

---

## 3. Trigger

- **Scheduled monthly on the 12th**, before GSTR-2B generation on the 14th, so pending IMS actions can
  still be taken. It runs again on the 15th, after GSTR-2B.
- **Scheduled monthly from August to November** for the s.16(4) countdown on the previous FY. This uses
  the same calendar as [UC-19](uc-19-credit-note-time-limit.md).
- **On event:** `bill.updated` where `ims_status` changes, through watcher transitions (G4).
- **On request.**

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Bill.list {"limit":1000}` | `date`, `status`, `ims_status` (`pending\|accept\|reject`), `itc_eligibility`, `gst_no`, `total_tax`, `taxes[]`, `items[]`, `vendor_id` |
| `VendorCredit.list` | Inward credit notes, also actioned in IMS (UC-25) |
| `GSTReturn.list` | `return_type=GSTR-2B`: `return_period`, `taxable_amount`, `total_transactions`, `summary[]`, `tables` (aggregate only) |
| `Party.get` | Supplier GSTIN, for documents with no bill-level `gst_no` |

---

## 5. Algorithm

1. **Population:** bills that are not void or draft, with `itc_eligibility ≠ ineligible` and tax above 0
   (tax source per document, Rule 0).
2. **`itc_on_rejected_document`:** `ims_status = reject`. The credit must not be claimed; if it already was,
   it must be reversed. Exposure is the tax, plus interest if claimed (UC-23 shows claim status).
3. **`itc_awaiting_ims_action`:** `ims_status = pending` on documents whose period's GSTR-2B hasn't been
   generated (today before the 14th of the next month). These are listed so they get actioned before they
   are deemed accepted.
4. **`itc_supplier_not_identified`:** no supplier GSTIN on either the bill or the vendor's record. The
   credit can't be matched to GSTR-2B, and Rule 46 invoice particulars are missing (see
   [UC-40](uc-40-vendor-master-audit.md)).
5. **`itc_lapsing`:** for each FY whose s.16(4) date is less than 90 days away, list eligible documents not
   yet claimed. An aggregate row gives days left, count and tax.
6. **`itc_not_in_2b` (blocked):** matching books to GSTR-2B line by line needs 2B line data. `GSTReturn`
   carries only aggregates (`summary[]` is empty), so the agent compares totals only and says that it did.
7. **Unclaimed** = eligible, accepted (or deemed accepted), not rejected, and not claimed in a filed
   GSTR-3B. Claim status per document doesn't exist on the platform. The agent reports the eligible pool
   against UC-23's computed claim and states the limitation.

### Worked example (REAL, 2026-10-04)

> Open bills carrying credit (eligible, tax above 0): **91, ₹19,56,062.01 of tax**.
> - `reject` while still marked ITC-eligible: **10 bills, ₹41,226.79 of tax**. Largest:
>   - BILL-2026-00068 (`73d0685c-7bbb-499e-9e1c-b440b6be5938`, Kirloskar Pumps, ₹11,385.92);
>   - BILL-2026-00044 (`5c9ad0c9…`, Bharat EV Motors, ₹11,113.92).
> - `pending`: **67 bills, ₹18,70,492.89**. September documents can still be actioned before GSTR-2B on
>   14 October.
> - `accept`: **14 bills, ₹44,342.33**.
> - **69** credit-bearing bills have no supplier GSTIN on the bill or the vendor record.
> - **s.16(4):** every bill is FY 2026-27 (the ledger starts 2026-06-07), so the first deadline is
>   **2027-11-30**. No lapse today.
>
> Output: *"₹41,226.79 of credit sits on 10 IMS-rejected invoices still marked eligible: do not claim it.
> ₹18.70 lakh is pending IMS action before 14 October. 69 credit-bearing bills have no supplier GSTIN."*

---

## 6. Known-bad data

- **GSTR-2B rows have no lines:** `summary: []`, `tables: null`. The 08-2026 2B row also has
  `filing_status: unfiled` and `due_date: 2026-09-14`, but GSTR-2B is system-generated and never filed.
  Report the status field as `data_quality` and don't use it.
- **No supplier GSTIN on any vendor `Party`** (0 of 88 referenced vendors). The bill-level `gst_no` is
  present on only 31 of 100 open bills.
- **`ims_status` is `pending` on all 101 Keystone (US) bills.** This is a GST field on a US tenant, and
  the playbook must not run there (`tax_regimes: [gst]`).

---

## 7. Output contract

`finding_type: "itc_entitlement"`, `rule ∈ {itc_on_rejected_document, itc_awaiting_ims_action,
itc_supplier_not_identified, itc_lapsing, itc_not_in_2b, data_quality}`. Rejected-document rows reuse the
UC-01 reversal fields: `reversal_base_amount`, `interest_amount`, `total_exposure`. Rows are sorted by
exposure.

---

## 8. Limits

- It never changes `ims_status` and never accepts or rejects on IMS. It reports and escalates only.
- It can't prove a document is missing from GSTR-2B until line data exists. It says so rather than
  inferring.
- It doesn't decide commercial disputes behind a rejection.

---

## 9. Validation

1. **Live:** of the 91 credit-bearing open bills, 67 pending / 14 accepted / 10 rejected, recomputed by
   hand from `Bill.list`.
2. **Boundary fixture:** an FY 2025-26 invoice with today 2026-11-30 → claimable; 2026-12-01 → `itc_lapsing`
   becomes a lost-credit finding.
3. **Debit-note fixture:** the s.16(4) FY follows the debit-note date, not the original invoice date.

---

## 10. Open questions

- **What does AgentSwitch's `pending` mean:** "not yet actioned" (deemed accepted at GSTR-2B) or "kept
  pending" (excluded)? This changes credit by ₹18.70 lakh. Ask the platform team.
- **Can GSTR-2B line data be exposed** (a `GSTR2BLine` entity or the `tables` field filled)? Request it in
  `requested_tools.md`.
- Should credit "claimed" be tracked per document (a claim period on `Bill`), so "unclaimed" can be exact?

---

## 11. Live evidence — actual calls, 2026-10-04

- `Bill.list {"limit":1000}` → 281 bills. `ims_status` across all: pending 252, accept 16, reject 13.
  Non-void, by status and eligibility:

  | | input | input_services | capital_goods | ineligible |
  |---|---|---|---|---|
  | **pending** | 65 | — | 2 | 4 |
  | **accept** | 1 | 8 | 5 | 2 |
  | **reject** | 5 | 3 | 2 | 3 |

- All 10 rejected-but-eligible bills are dated 2026-09-12 (the seed day): BILL-2026-00095, -00081, -00072,
  -00068, -00052, -00044, -00028, -00026, -00025, -00022.
- `GSTReturn.list` → GSTR-2B 08-2026 (`9290c9da-7e53-4d22-bead-639acee658f4`): taxable ₹1,89,40,000, 132
  transactions, `summary: []`.
