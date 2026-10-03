# UC-15 — Rule 42/43 Apportionment for a Clinic

**Workstream B · Verdict: 🔴 Blocked as a platform capability · 🟢 computable and reportable**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Depends on:** [UC-14](uc-14-clinic-exempt-taxable-split.md) (E, F) · **Reuses:** [UC-08](uc-08-rule-42-apportionment-school.md) Rule 42 engine · **Emits:** UC-01 reversal row · **Backs:** F18

> **Scope decision:** Rule 42 (inputs and input services) is identical to UC-08 and is
> not re-specified here. This spec adds only what a clinic changes: **Rule 43 for
> capital goods** (a clinic's medical equipment is a large common-credit pool) and the
> **5%-without-ITC room-rent stream**.

---

## 1. Question

> *"Of all the GST we paid on purchases, how much can we actually keep?"*

(Verbatim from `spec.md` UC-15.)

---

## 2. Statutory basis

- **Rule 42** — as UC-08 §2.
- **Rule 43, CGST Rules — capital goods used for both taxable and exempt supplies:**
  - ITC on capital goods used *exclusively* for exempt supplies is not creditable at
    all; capital goods used *exclusively* for taxable supplies are fully creditable.
  - For **common capital goods**, the ITC (`A`) is credited to the electronic credit
    ledger, and the useful life is taken as **5 years (60 months)** from invoice date.
  - Each month: `Tm = A ÷ 60` (credit attributable to the month). Summed over all common
    capital goods still within life: `Tr`.
  - **Credit attributable to exempt supplies:** `Te = (E ÷ F) × Tr`, which is added to
    output tax liability (reversed) that month.
- **Room rent above ₹5,000/day** is taxable at 5% **without ITC**. Inputs used for it
  are treated as used for exempt supply for apportionment purposes. For Rule 42, its
  turnover belongs in **E**, not T.
- **Consequence:** as UC-08, plus a 60-month tail. Rule 43 reversal runs every month
  for 5 years after each equipment purchase.

---

## 3. Trigger

**Monthly**, after UC-14's `turnover_split`. The Rule 43 schedule is maintained per
capital-goods invoice for 60 months.

---

## 4. Input contract

| Source | Arguments | Provides |
|---|---|---|
| UC-14 `turnover_split` | — | E (incl. no-ITC room rent), F |
| UC-08 engine | — | Rule 42 D1/D2 for inputs and input services |
| `Bill.list` | `{"itc_eligibility": "capital_goods", "limit": 1000}` | Rule 43 `A` per bill (9 bills live) |

---

## 5. Algorithm

1. Run UC-08 §5 for inputs/input services, with UC-14's E and F → Rule 42 rows.
2. **Rule 43 schedule:** for every `capital_goods` bill, `A` = its Rule 0-valid
   item-level tax. Start month = the bill's month; end = +59 months.
3. For the current month: `Tr = Σ (A ÷ 60)` over all capital-goods bills whose
   schedule covers it.
4. `Te = Tr × E ÷ F`.
5. Emit a reversal row with `rule = "rule_43_monthly"`, `reversal_base_amount = Te`.
6. Annual true-up as UC-08 step 9, for both rules.

### Worked example (Rule 43 mechanics on a REAL capital-goods bill; clinic ratio constructed)

> **BILL-2026-00022** (`2cfe5989-4a9a-45fa-b764-d9d98e3d21a5`), vendor Tata Ficosa
> Automotive Systems, `itc_eligibility: capital_goods`, item-level tax **₹155.49**.
>
> ```
> A  = 155.49            (the Rule 0 check must pass first — see §6)
> Tm = 155.49 / 60       = ₹2.59 per month, for 60 months from the bill's month
> clinic E/F (constructed, 40% exempt): Te = 2.59 × 0.40 = ₹1.04 reversed this month
> ```
>
> The live example is small; the mechanics are the point. A ₹25 lakh MRI machine with
> ₹4.5 lakh GST gives `Tm` ₹7,500/month, which is ₹3,000/month reversed at 40% exempt,
> every month for five years.

---

## 6. Known-bad data

- As UC-08 §6.
- **BILL-2026-00022 is also tagged `gst_treatment: business_composition`** (UC-17):
  a composition vendor cannot charge GST, so its ₹155.49 of GST is itself suspect, and
  **no ITC is available on it at all**. UC-17's finding takes precedence. The Rule 43
  schedule must skip bills UC-17 flags.
- **The ledger starts 2026-06-07.** A real 60-month schedule needs 5 years of
  capital-goods history. On this instance every schedule is in its first 4 months.

---

## 7. Output contract

UC-01 §7 reversal row, with `rule ∈ {rule_42_monthly, rule_43_monthly,
rule_42_annual_trueup}`. The Rule 43 row adds `capital_goods_bill_id`,
`schedule_month` (1–60) and `monthly_credit_Tm`.

---

## 8. Limits

- Cannot post the reversal (F18/GAP-1, as UC-08).
- Cannot see capital goods acquired before the platform ledger began. Opening Rule 43
  schedules must be supplied by the user.
- Useful life is fixed at 60 months by rule, and early disposal (s.18(6)) is not
  modelled.

---

## 9. Validation

1. **UC-08 engine regression** (the Sep-2026 real computation: ₹4,05,733.76 — corrected 30 Sep, was ₹15,207.64) must pass
   unchanged.
2. **Rule 43 arithmetic fixture:** A = ₹60,000 → Tm = ₹1,000; E/F = 25% → Te = ₹250;
   month 61 → 0.
3. **Composition precedence:** BILL-2026-00022 must *not* enter a Rule 43 schedule
   while UC-17 flags it.

---

## 10. Open questions

- **Merge with UC-08?** The Rule 42 halves are identical. Suggest one "apportionment"
  spec with a Rule 43 section at review time.
- **Opening balances** for pre-platform capital goods — where does the user supply
  them?
- **Is no-ITC room rent in E?** This spec says yes (inputs for it are not creditable).
  Confirm with a CA, since it is taxable output, not exempt output.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-15 Rule 42-43 apportionment`.

**Call — `Bill.list {"itc_eligibility":"capital_goods","limit":1000}`** → **9 bills**
eligible for a Rule 43 schedule. Includes BILL-2026-00022 (`2cfe5989…`, tax ₹155.49,
also `business_composition` — see §6).

Rule 42 inputs: see UC-08 §11 (the Sep-2026 figures are the same computation).

**What the live data changed:** Rule 43 was not in `spec.md`'s UC-15 text beyond its
title. The 9 live `capital_goods` bills make it concrete. The UC-17 overlap on
BILL-2026-00022 was found only because the specs were cross-checked against the same
snapshot.
