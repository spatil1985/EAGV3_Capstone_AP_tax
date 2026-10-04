# UC-33 — Expense Claims: GST Credit Eligibility

**Domains: all five (heaviest in agency, clinic and school, which run on staff expense claims) · Category: input tax · Verdict: 🟢 Buildable — live findings**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-02](uc-02-blocked-credit-audit.md)**

[UC-02](uc-02-blocked-credit-audit.md) audits blocked credit on **bills**. Expense claims are a separate
entity (`Expense`) with their own `itc_eligibility`, and nothing audits them today.

---

## 1. Question

> *"Are we claiming GST credit on expense claims where the law says we can't?"*

---

## 2. Statutory basis

- **s.16(1)–(2)(a) CGST Act + Rule 36(1):** credit needs a tax invoice **in the company's name and
  GSTIN**, for supplies used in the course of business. A receipt in an employee's name, or with no
  supplier GSTIN, gives no credit.
- **s.17(5) blocks credit on:**
  - **(g)** goods or services for **personal consumption**;
  - **(b)** food and beverages, outdoor catering, beauty and health services, club and fitness
    memberships, and travel benefits to employees on vacation (unless the law obliges the employer to
    provide them);
  - **(a)** motor vehicles (with exceptions).
- **Schedule III para 1:** services by an employee to the employer are **not a supply**. No GST exists on
  salaries or wages, so a salary expense carrying GST is impossible.
- **Consequence:** credit wrongly taken is reversed with **18% interest** (s.50(3)), and penalty may follow
  (s.122).

---

## 3. Trigger

- **On event:** `expense.created` / `expense.updated` through the watcher (G4). The watcher's entity list
  needs `Expense` added.
- **Scheduled monthly** before GSTR-3B. Expense credit flows into UC-23.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `Expense.list {"limit":1000}` | `date`, `amount`, `tax_amount`, `itc_eligibility`, `is_personal`, `is_reimbursable`, `is_reverse_charge`, `gst_no`, `gst_treatment`, `hsn_or_sac`, `expense_type`, `account_id` (`_account_id_display`), `vendor_id`, `paid_through_account`, `claimant_email`, `status` |
| `Party.get` | Supplier GSTIN where the expense has none |

---

## 5. Algorithm

1. **Population:** expenses with `itc_eligibility ∈ {input, input_services, capital_goods}` and
   `tax_amount > 0`.
2. **`itc_on_personal_expense`:** `is_personal = 1` (s.17(5)(g)).
3. **`itc_without_supplier_gstin`:** no `gst_no` on the expense or the vendor (s.16(2)(a)).
4. **`itc_blocked_category`:** the account or description matches the s.17(5)(b) table (food, meals,
   canteen, club, gym, health, beauty, LTC/vacation travel) or motor vehicles (a). The table is shared
   with UC-02 (`domain/reference/blocked_credit.yaml`, G6).
5. **`gst_on_non_supply`:** tax above 0 on salary, wages, PF/ESI, bank-loan or interest-only accounts.
   - Salaries are Schedule III, not a supply.
   - Most bank charges carry GST legitimately, but tax above 18% of the charge is impossible.
6. **`tax_exceeds_possible_rate`:** `tax_amount / amount > 0.40`, above the highest GST rate plus cess
   headroom → `data_quality`.
7. **`classification_conflict`:** `gst_treatment ∈ {deemed_export, sez}` on an expense. These are
   outward-supply categories and can't describe a purchase.
8. **`rcm_on_registered_supplier`:** `is_reverse_charge = 1` with `gst_treatment = business_gst` outside
   the notified RCM list (UC-03).

### Worked example (REAL, 2026-10-04)

> 120 expenses dated 2026-08-03 to 2026-10-02.
> - **Personal expenses claiming credit:** **18, tax ₹7,73,592.68**. For example:
>   - `170bcd1d-d43e-470f-a29e-fbd22aa0bab7` (2026-09-10, `input`, tax ₹2,07,178.64);
>   - `822a1620-73d5-4d62-9203-bfdd896bdaf5` (2026-09-08, `capital_goods`, ₹71,939.79).
> - **Credit claimed without supplier GSTIN:** 13.
> - **Tax above 40% of the amount:** 56. For example, amount ₹2,183.09 with tax ₹75,456.61.
> - **GST on non-supplies:**
>   - Salaries & Wages: 2 expenses, tax ₹19,092.55;
>   - EPF Payable: 2, tax ₹1,629.04;
>   - Bank Charges: tax ₹2,00,948.47 on ₹1,30,888.99 of charges.
> - **Outward categories on purchases:** `deemed_export` 18, `sez` 11.
> - **RCM flagged on registered suppliers:** 2.
>
> Output: *"18 personal expense claims carry ₹7.74 lakh of GST credit that s.17(5)(g) blocks. 13 claims
> have no supplier GSTIN. 56 expense records carry more tax than any GST rate allows."*

---

## 6. Known-bad data

- **Expense tax is not credible in bulk:** 56 of 120 exceed 40% of the amount, and several accounts have
  tax larger than the expense. Totals must exclude `data_quality` rows and say how much was excluded.
  This is a candidate bug report, the same seeder family as Rule 0.
- Many descriptions are seeded product text ("Machinist Square: lot 405 at Rajkot…"), so description
  matching (step 4) finds nothing on this tenant. It relies on account names instead.
- Payroll-like accounts appear on `Expense`. The agent reports only the GST anomaly and never reads
  `SalarySlip` (prohibited).

---

## 7. Output contract

`finding_type: "expense_itc"`, `rule ∈ {itc_on_personal_expense, itc_without_supplier_gstin,
itc_blocked_category, gst_on_non_supply, tax_exceeds_possible_rate, classification_conflict,
rcm_on_registered_supplier}`. Reversal rows reuse the UC-01 fields (`reversal_base_amount` = the claimed
tax).

---

## 8. Limits

- Never changes an expense's eligibility, and never rejects a claim.
- It doesn't judge whether an expense is a genuine business expense. It applies only the GST blocking
  rules.

---

## 9. Validation

1. **Live:** recompute 18 / 13 / 56 from `Expense.list`.
2. **Fixtures:**
   - `is_personal=1`, `input`, tax 180 → `itc_on_personal_expense`;
   - the same with `ineligible` → no finding.
3. **Rate fixture:** amount 1,000 with tax 500 → `tax_exceeds_possible_rate`.

---

## 10. Open questions

- Is `is_personal` set by the claimant or by approval? If by the claimant, a `personal` expense should
  never have been reimbursed.
- Should expense credit be read at all for UC-23 while 47% of rows fail the rate test? Recommend excluding
  `data_quality` rows from liability until fixed.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Expense.list {"limit":1000}` → 120 rows.
  - `status`: unbilled 51, non_billable 40, invoiced 15, reimbursed 14.
  - `itc_eligibility`: capital_goods 26, input_services 25, ineligible 25, null 22, input 22.
  - `gst_no` present on 83; `tax_amount > 0` on 88.
- Paid through: Cash 17, Petty Cash 13, SBI 12, ICICI 11, HDFC 11 (used by [UC-38](uc-38-cash-payment-limits.md)).
