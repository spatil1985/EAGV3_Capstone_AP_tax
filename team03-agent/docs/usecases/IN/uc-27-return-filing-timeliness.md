# UC-27 — GST Return Filing Timeliness: Late Fee, Interest and Knock-On Blocks

**Domains: all five · Category: compliance calendar · Verdict: 🟢 Buildable — live findings (August returns overdue)**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Which GST returns are due or overdue, and what is lateness costing us?"*

---

## 2. Statutory basis

- **Due dates (monthly filer):**
  - GSTR-1 by the **11th** (s.37, Rule 59);
  - GSTR-3B by the **20th** (s.39, Rule 61);
  - GSTR-9 by **31 December** after the FY (s.44, [UC-31](uc-31-annual-return-reconciliation.md)).
- **s.47 late fee:** ₹100/day per return in law, **reduced by notification to ₹50/day (₹25 CGST + ₹25
  SGST)**, or ₹20/day for nil returns.
  - Caps by aggregate turnover (*our understanding of Notifications 19/2021 and 20/2021-CT, caveat*):
    - up to ₹1.5 Cr: ₹2,000;
    - ₹1.5–5 Cr: ₹5,000;
    - above ₹5 Cr: ₹10,000.
- **s.50(1) proviso:** **18% p.a.** interest on net tax paid late in cash, per day of delay.
- **Knock-on blocks:**
  - **Rule 59(6):** GSTR-1 can't be filed while the previous month's GSTR-3B is outstanding.
  - **Rule 138E:** *our understanding (caveat)* e-way bill generation is blocked once GSTR-3B is missing
    for **two consecutive** tax periods. That hits manufacturing and retail despatches ([UC-12](uc-12-eway-bill-coverage.md)).
  - **s.46 / s.62:** a non-filer gets a notice (GSTR-3A), then best-judgment assessment.
  - **Time bar:** *our understanding (caveat):* a return can't be filed more than **3 years** after its
    due date (Finance Act 2023; enforced on the portal from 2025).

---

## 3. Trigger

- **Scheduled daily.** The cost of lateness grows every day, the same reasoning as UC-01's moving
  boundary.
- **Calendar reminders:** T−5 and T−1 before each due date (`config/calendar.yaml`, G11).
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `GSTReturn.list {"limit":1000}` | `return_type`, `return_period` (`MM-YYYY`), `filing_frequency`, `filing_status` (`filed\|unfiled`), `due_date`, `filed_date`, `net_tax_payable`, `taxable_amount` |
| UC-23 output | Cash payable for the period: the interest base when `net_tax_payable` is null |
| UC-29 output | Aggregate turnover band: sets the late-fee cap |
| `GET /api/accounting/locale` | `gst_filing_frequency`, the expected cadence |

---

## 5. Algorithm

1. **Expected returns:** for each closed period since registration (or since the ledger starts), expect
   GSTR-1 and GSTR-3B. A missing row is `return_not_generated`.
2. **Overdue:** `filing_status ≠ filed` and `due_date < today` → `return_overdue`, with `days_late = today −
   due_date`.
3. **Late fee:** `min(days_late × ₹50, cap)` per return (₹20/day for nil).
4. **Interest (GSTR-3B only):** `cash_payable × 18% × days_late / 365`. The base is `net_tax_payable` if
   populated, otherwise UC-23's computed cash.
5. **Filed late:** `filed_date > due_date` → a historical `return_filed_late` row with the same arithmetic.
6. **Knock-ons:**
   - next GSTR-1 blocked if the previous GSTR-3B is outstanding;
   - `eway_block_risk` when one GSTR-3B is missing and the next is due within 30 days.
7. **`return_status_meaningless`:** a GSTR-2B row carrying a filing status or due date. GSTR-2B is
   system-generated and never filed.

### Worked example (REAL, as of 2026-10-04)

| Return | Period | Due | Status | Days late | Late fee | Interest |
|---|---|---|---|---|---|---|
| GSTR-1 | 08-2026 | 2026-09-11 | unfiled | **23** | 23 × ₹50 = **₹1,150** | — |
| GSTR-3B | 08-2026 | 2026-09-20 | unfiled | **14** | 14 × ₹50 = **₹700** | ₹5,72,073.68 × 18% × 14/365 = **₹3,949.66** |
| GSTR-1 / 3B | 09-2026 | 2026-10-11 / 2026-10-20 | **not generated** | — | — | — |
| GSTR-1 / 3B | 07-2026 | 2026-08-11 / 2026-08-20 | filed 2026-08-08 | on time | — | — |

> The interest base is UC-23's computed August cash, because `net_tax_payable` is null.
>
> **Knock-ons:**
> - September GSTR-1 can't be filed until August GSTR-3B is (Rule 59(6)).
> - If September GSTR-3B is also missed on 20 October, two consecutive periods are outstanding and **e-way
>   bill generation is blocked** (Rule 138E) for a manufacturer that despatches daily.
>
> Output: *"August GSTR-1 (23 days) and GSTR-3B (14 days) are overdue: ₹1,850 late fee and about ₹3,950
> interest so far, growing daily. Missing September GSTR-3B on 20 October blocks e-way bills."*

---

## 6. Known-bad data

- `net_tax_payable` is null on all 5 return rows, so the interest base comes from UC-23.
- The **GSTR-2B row carries `filing_status: unfiled` and `due_date: 2026-09-14`**, which is meaningless
  for a generated statement → `return_status_meaningless`.
- The return figures don't reconcile to the ledger (UC-23 §6). This affects the interest base, not the
  dates.

---

## 7. Output contract

`finding_type: "return_compliance"`, `rule ∈ {return_overdue, return_filed_late, return_not_generated,
eway_block_risk, return_status_meaningless}`. Fields: `return_type`, `period`, `due_date`, `days_late`,
`late_fee`, `interest_amount`, `total_exposure`. The day count is recomputed every run, never stored.

---

## 8. Limits

- Never files a return or pays a late fee.
- Late-fee waivers and amnesty notifications must be added to the rulebook. Without them the
  computation is the default law.

---

## 9. Validation

1. **Live:** the table above, recomputed by hand.
2. **Cap fixture:** 300 days late with aggregate turnover above ₹5 Cr → late fee ₹10,000, not ₹15,000.
3. **Nil fixture:** a nil GSTR-3B 10 days late → ₹200.
4. **Boundary:** filed on the due date → 0 days late.

---

## 10. Open questions

- Who generates `GSTReturn` rows, and when? September's rows don't exist 4 days after the month closed.
- Does the platform enforce Rule 59(6) or Rule 138E? Either is a test case: try filing September GSTR-1
  with August GSTR-3B unfiled.

---

## 11. Live evidence — actual calls, 2026-10-04

- `GSTReturn.list {"limit":1000}` → 5 rows:

  | Return | Period | Id | Status | Due | Filed |
  |---|---|---|---|---|---|
  | GSTR-1 | 08-2026 | `a0e4a5c8-5d51-40d2-a335-62ece0778c36` | unfiled | 2026-09-11 | — |
  | GSTR-3B | 08-2026 | `b66093cf-40c3-4a1e-97ac-79cebb419863` | unfiled | 2026-09-20 | — |
  | GSTR-2B | 08-2026 | `9290c9da-7e53-4d22-bead-639acee658f4` | unfiled | 2026-09-14 | — |
  | GSTR-1 | 07-2026 | `4f2c8b10-e175-4957-9e62-c13dc14036fa` | filed | 2026-08-11 | 2026-08-08 |
  | GSTR-3B | 07-2026 | `c13b302d-0fd8-427c-94a9-d302dd856da4` | filed | 2026-08-20 | 2026-08-08 |

- Locale: `gst_filing_frequency: monthly` (CURRENT_STATUS §2).
