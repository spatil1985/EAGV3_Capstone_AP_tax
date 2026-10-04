# UC-31 — Annual Return Reconciliation (GSTR-9 / GSTR-9C)

**Domains: all five · Category: compliance calendar · Verdict: 🔴 Blocked as a platform capability (GSTR-9 returns HTTP 501, GST-39) · 🟡 the agent can compute the tables and the reconciliation**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Will our annual return agree with our monthly returns and our books, and what do we have to fix before it's due?"*

---

## 2. Statutory basis

- **s.44 CGST Act + Rule 80:**
  - **GSTR-9** (annual return) is due by **31 December** after the FY.
  - It is optional for aggregate turnover up to ₹2 crore (notified each year).
  - **GSTR-9C** (a self-certified reconciliation of the GSTR-9 turnover with audited financial statements)
    is due when aggregate turnover exceeds ₹5 crore.
- **GSTR-9 tables:**

  | Table | Contents |
  |---|---|
  | 4–5 | Outward supplies: taxable; exempt, nil and zero-rated |
  | 6 | Input credit availed |
  | 7 | Credit reversed |
  | 8 | Credit per GSTR-2B (8A) vs books (8B), and the difference |
  | 9 | Tax paid |
  | 10–14 | Next-FY amendments up to 30 November |
  | 17–18 | HSN summaries |

- **Late fee:** *our understanding of Notification 07/2023-CT (caveat)*:
  - aggregate turnover up to ₹5 crore: ₹50/day, capped at 0.04% of turnover;
  - ₹5–20 crore: ₹100/day, capped at 0.04%;
  - above ₹20 crore: ₹200/day, capped at 0.5%.
- **Consequence:**
  - Differences found here and not paid with the return are raised later in a s.73/74 notice, with
    interest from the original due date.
  - The annual return also closes the s.16(4) / s.34(2) / s.37(3) windows: the "date of furnishing the
    annual return, if earlier".

---

## 3. Trigger

- **Scheduled from 1 October to 31 December** each year, monthly then weekly, for the previous FY.
- **On request** for a draft at any time.
- **Period:** the FY (April–March), plus next-FY amendments up to 30 November.

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Invoice.list`, `CreditNote.list` | Outward supplies by table, as in [UC-26](uc-26-gstr1-readiness.md) |
| `Bill.list`, `VendorCredit.list` | Credit availed and reversed ([UC-23](uc-23-period-gst-liability.md), [UC-25](uc-25-vendor-credit-debit-notes-itc.md)) |
| `GSTReturn.list` | Monthly GSTR-1 / GSTR-3B for the FY (the "as filed" side); `return_type=GSTR-9` rows (none exist) |
| `AccountingPeriod.list` | `period_type`, `fiscal_year`, `from_date`, `to_date`, `status`, `total_income`: the **books** side for GSTR-9C |
| REST GSTR-9 endpoint | Returns **HTTP 501** per `not_yet_supported.gstr9` (GST-39) |

---

## 5. Algorithm

1. **FY tables from the ledger:** build Tables 4–9 from documents dated in the FY, using the UC-23 and UC-26
   logic, plus Table 10–14 amendments from [UC-28](uc-28-late-entered-documents.md) up to 30 November.
2. **Returns vs ledger:** sum the FY's filed GSTR-1 and GSTR-3B rows. Any difference from step 1 is
   `annual_vs_monthly_difference`, by table and head.
3. **Table 8, GSTR-2B vs books:** blocked. GSTR-2B line data doesn't exist ([UC-24](uc-24-unclaimed-itc-ims-2b.md)).
   Totals only.
4. **GSTR-9C, books vs returns:** FY turnover from `AccountingPeriod.total_income` (monthly rows, closed)
   vs Table 4+5 turnover. Difference → `reconciliation_difference`, with the reason left for a human.
5. **Applicability:** aggregate turnover from [UC-29](uc-29-turnover-based-obligations.md) decides whether
   GSTR-9 is optional and whether GSTR-9C is required.
6. **Countdown:** days to 31 December; the late-fee projection if missed.

### Worked example (REAL: FY 2025-26, due 2026-12-31, 88 days from 2026-10-04)

> **Applicability:** aggregate turnover is at least ₹6.71 crore → GSTR-9 is mandatory and **GSTR-9C
> required**.
>
> **Ledger side:**
> - Table 4 outward: live receivable taxable ₹6,70,65,518.43 (invoices from 2025-09-19).
> - Table 6 credit: **₹0**. No bill in the ledger is dated before 2026-06-07, so a full year of credit is
>   missing.
>
> **Books side:**
> - FY 2025-26 monthly `total_income` sums to ₹12,01,06,879.73.
> - **But March 2026 alone shows ₹6,70,65,518.43, the whole year's invoice turnover to the paisa.**
>   September–February sum to ₹5,30,41,361.30.
> - So either March holds a year-to-date figure (books ₹6.71 crore, no difference), or the books show
>   ₹12.01 crore (difference ₹5.30 crore).
> - The year-level period "FY 2025-26" is still `open`, with `total_income: null`.
>
> Output: *"FY 2025-26 GSTR-9 and GSTR-9C are due 31 December (88 days). The platform can't produce
> GSTR-9 (GST-39). Credit for the year is missing from the ledger, and the books' March figure looks
> cumulative, so the 9C reconciliation can't be closed yet."*

---

## 6. Known-bad data

- **`AccountingPeriod.total_income` for March 2026 equals the full-year invoice turnover.** It looks like
  a cumulative value in a monthly field. Flag it as `data_quality`, don't sum blindly, and consider it as a
  candidate bug report.
- **The ledger doesn't cover FY 2025-26:** invoices start 2025-09-19 and bills 2026-06-07.
- The monthly return rows don't reconcile to the ledger (UC-23 §6), so step 2 will show differences in
  every month that has a row.

---

## 7. Output contract

`finding_type: "annual_return"`, `rule ∈ {annual_vs_monthly_difference, reconciliation_difference,
table8_unverifiable, annual_return_due, data_quality}`. There is a context row per GSTR-9 table (the
draft), and a finding per difference, with `head`, `table`, `ledger_value`, `return_value`, `difference`.

---

## 8. Limits

- **The agent can't file GSTR-9 or GSTR-9C;** the endpoint returns 501. It produces a draft for a human.
- GSTR-9C needs *audited* financial statements. `AccountingPeriod` figures are unaudited, so the draft
  says so.
- It never posts adjusting entries; `JournalEntry` is read-only.

---

## 9. Validation

1. **Live:** recompute the FY totals above.
2. **Fixture:** 12 monthly GSTR-3B rows summing to output ₹10,00,000 while the ledger shows ₹10,50,000 →
   `annual_vs_monthly_difference` of ₹50,000 on Table 4.
3. **Window fixture:** an FY 2025-26 credit note issued 2026-11-30 belongs in Tables 10–11; one issued
   2026-12-01 doesn't (s.34(2)).

---

## 10. Open questions

- Is March's `total_income` a cumulative figure by design (a year-end closing entry), or an error?
- When GSTR-9 is supported, will it read `GSTReturn` rows (which don't reconcile) or the ledger?
- FY 2025-26 credit is absent from the ledger. Do the instructors expect the annual return to run on
  partial data, or only from FY 2026-27?

---

## 11. Live evidence — actual calls, 2026-10-04

- `GSTReturn.list` → 5 rows, **0 with `return_type = GSTR-9`**.
- `AccountingPeriod.list` → FY 2025-26 months April–August show `total_income` 0.
  - September 2025: ₹51,81,292.75.
  - October: ₹77,09,428.56.
  - November: ₹1,36,10,983.75.
  - December: ₹1,17,11,170.93.
  - January 2026: ₹85,84,377.27.
  - February: ₹62,44,108.04.
  - **March: ₹6,70,65,518.43.**
  - Year period "FY 2025-26": `open`, `total_income: null`.
- Locale `not_yet_supported.gstr9` → *"Annual return endpoint returns HTTP 501"* (GST-39, CURRENT_STATUS §2).
