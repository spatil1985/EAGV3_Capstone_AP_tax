# UC-08 — Rule 42 Apportionment for a Mixed-Supply School

**Workstream B · Owner: Geetha · Verdict: 🔴 Blocked as a platform capability · 🟢 computable and reportable by the agent**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Depends on:** [UC-07](uc-07-school-exempt-taxable-split.md) (supplies E and F) · **Emits:** the UC-01 reversal row · **Backs:** F18 / GAP-1

---

## 1. Question

> *"How much of our input credit are we actually entitled to keep?"*

(Verbatim from `spec.md` UC-08.)

---

## 2. Statutory basis

- **Section 17(1)–(2), CGST Act** — where inputs are used partly for taxable and partly
  for exempt supplies, credit is restricted to the portion attributable to taxable
  supplies.
- **Rule 42, CGST Rules** — the monthly mechanics for inputs and input services:
  - `T` = total input tax in the period; `T1` = used exclusively for non-business;
    `T2` = used exclusively for exempt supplies; `T3` = blocked under s.17(5).
    `C1 = T − (T1 + T2 + T3)`; `T4` = used exclusively for taxable supplies.
  - **Common credit** `C2 = C1 − T4`.
  - **Credit attributable to exempt supplies** `D1 = (E ÷ F) × C2`, where `E` = exempt
    turnover and `F` = total turnover in the tax period.
  - `D2 = 5% of C2` if common inputs are also used for non-business purposes.
  - **Eligible common credit** `C3 = C2 − (D1 + D2)`. `D1` and `D2` are reversed in the
    period's return.
- **Rule 42(2) — annual true-up:** recompute `D1`/`D2` on full-year `E`/`F`; any
  excess reversal is re-claimed, and any shortfall is reversed **with interest under
  s.50** from 1 April following the FY. It is due by the return for **September**
  following the end of the FY.
- **Consequence if missed:** full common credit claimed while making exempt supplies
  is recovered on assessment with interest (s.50(3), 18%) and penalty (s.73/74).

---

## 3. Trigger

- **Monthly**, after UC-07 has produced that month's `turnover_split`, and before
  GSTR-3B is filed.
- **Annually**, after the FY closes (true-up), reported against the September-return
  deadline.
- **Period:** tax period (month). The FY true-up uses April–March aggregates.

---

## 4. Input contract

| Source | Arguments | Provides |
|---|---|---|
| UC-07 `turnover_split` rows | — | `E`, `F` per month |
| `Bill.list` | `{"itc_eligibility": "input", "limit": 1000}` and again with `"input_services"`, `"capital_goods"`, `"ineligible"` — **one enum value per call** (README Rule 6) | Input tax `T` and its partitions |
| `Item.list` | `{"limit": 1000}` | Per-line attribution hints (§5 step 3) |

**Bill fields:** `date`, `itc_eligibility`, `items[].item_id`,
`items[].cgst_amount`/`sgst_amount`/`igst_amount`/`cess_amount`, `vendor_id`.

`capital_goods` bills are **excluded here** (Rule 43 governs them — see UC-15), and so
are `ineligible` ones (already `T3`).

---

## 5. Algorithm

1. **T** — for the month, sum the Rule 0-valid item-level tax on bills with
   `itc_eligibility ∈ {input, input_services}`.
2. **T3** — tax on lines UC-02 flags as blocked under s.17(5). Subtract.
3. **Attribution** (T2 / T4) — a line is `exclusive_exempt` if its item is only ever
   sold as `tax_exempt`, and `exclusive_taxable` if only as `taxable`. Everything else is
   **common**. With no reliable attribution data, the conservative default is **all
   common** (T2 = T4 = 0), and it is stated in the output.
4. `C2 = T − T1 − T2 − T3 − T4`.
5. `D1 = C2 × E ÷ F` (E, F from UC-07). If `F = 0`, skip the month and flag it.
6. `D2 = 5% × C2` only if the tenant declares non-business use. The default is 0, and
   it is stated.
7. `C3 = C2 − D1 − D2`.
8. Emit one reversal row (UC-01 §7 schema) with `rule = "rule_42_monthly"`,
   `reversal_base_amount = D1 + D2`, `interest_amount = 0` for the monthly row (interest
   applies only to a true-up shortfall).
9. **Annual true-up:** recompute on FY `E`/`F`. Compare with the sum of monthly `D1`.
   A shortfall emits `rule = "rule_42_annual_trueup"` with s.50 interest from 1 April
   following the FY to the computation date, using UC-01's simple-interest formula.

### Worked example (REAL numbers — Suryodaya, September 2026)

No school tenant exists, but Suryodaya has 15 items marked `tax_exempt`, so its
September figures produce a genuine, non-zero Rule 42 computation. This is a
manufacturing company, so it illustrates the mechanics; it is not a school result.

> ```
> E  (exempt turnover, Item.tax_preference = tax_exempt)  = ₹2,32,96,704.45
> F  (total receivable turnover, Sep 2026)                = ₹8,50,07,553.04
> E/F                                                     = 27.41%
> T  (item-level tax on input + input_services bills, Sep) = ₹55,491.28
> T1 = T2 = T3 = T4 = 0   (conservative default: all common)
> C2                                                      = ₹55,491.28
> D1 = 55,491.28 × 27.41%                                 = ₹15,207.64
> D2 = 0   (no non-business use declared)
> C3 = 55,491.28 − 15,207.64                              = ₹40,283.64
> ```
>
> Output: *"September 2026: 27.41% of turnover was exempt. ₹15,207.64 of ₹55,491.28
> common input credit must be reversed; ₹40,283.64 may be kept."*
>
> **Caveat carried into the row:** T includes item-level tax that fails Rule 0 on
> 37 of 96 bill lines. The reversal is therefore stated **with a data-quality range**,
> not as a single filing figure (§6).

---

## 6. Known-bad data

- **E must come from `Item.tax_preference`, never from zero-tax lines.** Using zero tax
  would give April–August 2026 an exempt ratio of 100% and reverse *all* credit.
- **April–August 2026 show E = 0 and T = 0.** No exempt items were invoiced, and no
  bill before September carries item-level tax (65 of the in-scope open bills have zero
  item-level tax). The only non-trivial month is September.
- **Rule 0:** 37 of 96 taxed bill lines fail validity. Report `D1` twice: over valid
  lines only (lower bound), and over all lines (upper bound).
- **The item master is itself unreliable** (UC-07 §11: 12 `tax_exempt` items with
  `taxable = 1`). E inherits every misclassification.

---

## 7. Output contract

UC-01 §7 reversal row, unchanged fields, plus:

```json
{
  "finding_type": "itc_reversal",
  "rule": "rule_42_monthly",
  "entity_type": "TaxPeriod",
  "entity_id": "2026-09",
  "entity_ref": "Sep 2026",
  "counterparty_id": null,
  "counterparty_name": null,
  "exempt_turnover_E": 23296704.45,
  "total_turnover_F": 85007553.04,
  "ratio": 0.2741,
  "common_credit_C2": 55491.28,
  "reversal_base_amount": 15207.64,
  "interest_amount": 0.00,
  "total_exposure": 15207.64,
  "attribution_basis": "all_common_default",
  "currency": "INR",
  "status": "finding",
  "summary": "Sep 2026 — 27.41% exempt turnover; reverse ₹15,207.64 of ₹55,491.28 common credit."
}
```

---

## 8. Limits

- **Cannot post the reversal.** `JournalEntry` is read-only for `finance_user`. This is
  the whole of GAP-1 / F18: the computation is complete, but the books stay wrong until
  a human posts it.
- Does not file GSTR-3B Table 4(B)(1). It reports what goes there.
- Attribution (T2/T4) defaults to "all common", because the platform has no field to
  mark an input as used exclusively for exempt or taxable output.

---

## 9. Validation

1. **Arithmetic oracle:** the formula is statutory. Re-derive D1 by hand from the three
   inputs in §11. Any mismatch is an implementation bug.
2. **Boundary controls:** `E = 0` → `D1 = 0` (April–August live); `E = F` → `D1 = C2`
   (fully exempt month); `F = 0` → month skipped and flagged.
3. **True-up control:** construct a two-month fixture where the monthly ratios differ
   (10%, 40%) but annual is 25%. The true-up must emit the difference.
4. **School validation needs a school tenant** — see F2 (sandbox).

---

## 10. Open questions

- **Is "turnover" E/F on invoice date or supply date?** Rule 42 uses the tax period's
  turnover. The spec uses `Invoice.date`.
- **Does zero-rated (SEZ/export) turnover count in F but not E?** Yes by statute
  (zero-rated is taxable). UC-07 must keep zero-rated out of E. The 15 live SEZ invoices
  are `taxable` items, so they are correctly in T today.
- **F18 framing:** the live example shows the gap concretely. A ₹15,207.64 reversal is
  computed and cannot be posted. Use this as the evidence line in F18's triage response.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-08 Rule 42 apportionment`.

**Call 1 — `Invoice.list {"direction":"receivable","limit":1000}`** and
**Call 2 — `Item.list {"limit":1000}`** → joined on `item_id` (UC-07 §11).

Monthly split, FY 2026-27 (by `Item.tax_preference`):

| Month | E (exempt) | F (total) | E/F | C2 (bill ITC) | D1 |
|---|---|---|---|---|---|
| 2026-04 | 0 | ₹1,03,58,998.01 | 0.00% | 0 | 0 |
| 2026-05 | 0 | ₹1,66,71,022.91 | 0.00% | 0 | 0 |
| 2026-06 | 0 | ₹1,92,72,518.28 | 0.00% | 0 | 0 |
| 2026-07 | 0 | ₹1,34,98,123.63 | 0.00% | 0 | 0 |
| 2026-08 | 0 | ₹46,44,015.04 | 0.00% | 0 | 0 |
| **2026-09** | **₹2,32,96,704.45** | **₹8,50,07,553.04** | **27.41%** | **₹55,491.28** | **₹15,207.64** |
| FY to date | ₹2,32,96,704.45 | ₹14,94,52,230.91 | 15.59% | — | — |

**Call 3 — `Bill.list`, once per enum value** (Rule 6):
```http
{"name":"Bill.list","arguments":{"itc_eligibility":"input","limit":1000}}          → 198 bills
{"name":"Bill.list","arguments":{"itc_eligibility":"input_services","limit":1000}} → 11
{"name":"Bill.list","arguments":{"itc_eligibility":"capital_goods","limit":1000}}  → 9   (→ UC-15, Rule 43)
{"name":"Bill.list","arguments":{"itc_eligibility":"ineligible","limit":1000}}     → 9   (T3)
```
Sending `"itc_eligibility": ["input","input_services"]` returns
`-32602 "/itc_eligibility must be string"`. Verified live.

**What the live data changed:** the spec's claim that E is "derivable by summing
`Invoice.items[]` where `Item.tax_preference = tax_exempt`" holds. The live data shows
it is the *only* safe derivation, because the obvious shortcut (zero-tax lines) is
wrong by a factor of ~9 on this instance.
