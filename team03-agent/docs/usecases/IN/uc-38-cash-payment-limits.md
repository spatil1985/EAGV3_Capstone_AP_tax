# UC-38 — Cash Payments to Vendors: s.40A(3) Disallowance

**Domains: all five (most common in retail, clinic and school, which run petty cash) · Category: income tax (AP-triggered) · Verdict: 🟢 Buildable — live findings**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-04](uc-04-msme-45-day-exposure.md) (another AP fact with an income-tax cost)**

---

## 1. Question

> *"Are we paying any vendor in cash above the limit, and losing the tax deduction for it?"*

---

## 2. Statutory basis

*Section numbers are from the Income-tax Act 1961; renumbering under the 2025 Act is to be confirmed (IN
README caveat).*

- **s.40A(3):** an expense paid to a person **in a day** otherwise than by account-payee cheque or draft,
  bank transfer or a prescribed electronic mode, **above ₹10,000**, is **disallowed in full**.
  - The limit is **₹35,000** for payments to transporters for plying, hiring or leasing goods carriages.
- **s.40A(3A):** an expense allowed in an earlier year but paid in cash later, above the limit, becomes
  income in the year of payment.
- **Rule 6DD** lists the exceptions: payments to banks and government, certain purchases from
  cultivators, payments in places with no bank, and others. They live in the rulebook.
- Related but not AP: **s.269ST** (receiving ₹2 lakh or more in cash, penalty equal to the amount) is on
  the receivable side (Team 02). It is noted here only so the playbook doesn't confuse the two.
- **Consequence:** the whole expense is added back to taxable income. The cost is roughly the company tax
  rate × the amount; the rate comes from the rulebook.

---

## 3. Trigger

- **On event:** `payment_made.created` with `payment_mode = cash`; `expense.created` with a cash `paid_through_account`.
- **On event (pre-payment):** `bill.approval_status_changed → approved` where `payment_gateway = cash` and
  `balance_due > ₹10,000`. This warns *before* the cash leaves.
- **Scheduled monthly** sweep, aggregating per vendor per day.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `PaymentMade.list` | `payment_mode` (`cash\|bank_transfer\|card\|cheque\|upi\|online\|other`), `amount`, `date`, `vendor_id` |
| `Expense.list` | `paid_through_account` (`Cash`, `Petty Cash`, …), `amount`, `date`, `vendor_id`, `account_id` |
| `Bill.list` | `payment_gateway` (`cash`, …), `balance_due`, `approval_status` |
| `BankAccount.list` | `account_type = cash` accounts (e.g. "Petty Cash — Plant"): which `paid_through` values are cash |
| `Party.get` | Vendor category, for the transporter limit (playbook table) |

---

## 5. Algorithm

1. **Cash outflows:** `PaymentMade` with `payment_mode = cash`, plus `Expense` paid through a cash account
   (matched against `BankAccount.account_type = cash` and the names in the rulebook).
2. **Aggregate per vendor per calendar day.** The limit is per person per day, so splitting one payment
   into several the same day doesn't avoid it.
3. **Limit:** ₹35,000 if the payment is for hiring goods carriages (vendor category plus expense account
   in the table), otherwise ₹10,000.
4. **`cash_payment_disallowed`:** the daily total exceeds the limit and no Rule 6DD exception is recorded.
   Exposure = the disallowed amount (the full day's payments to that vendor). The tax effect = amount ×
   rulebook rate.
5. **`cash_payment_planned`:** an approved or open bill with `payment_gateway = cash` and balance above
   the limit. Warn before payment.
6. **`cash_payment_wages`:** payroll-like accounts paid in cash. Report only the count and amount; never
   read payroll entities.

### Worked example (REAL, 2026-10-04)

> - `PaymentMade` in cash: **0**; payments are bank transfer (92) or cheque (42).
> - Expenses paid through **Cash / Petty Cash: 30, ₹7,83,073.79**, of which **13 exceed ₹10,000**:
>   **₹7,02,867.40 across 13 vendor-days**.
>   - `0e46c7d7-5b6c-4bf7-b756-d69ecaf9d7b9`: 2026-09-11, Umesh Sonawane, Power & Fuel, ₹80,855.61, petty
>     cash.
>   - `99c276e7-1084-48ef-ba87-b9ef9e32396a`: 2026-09-07, Anil Deshpande, Advertising, ₹80,855.61, cash.
>   - `f3d4e0c2-8023-4d5e-b8a4-65dc71b37a3b`: 2026-08-29, Manisha Bhosale, Professional & Audit Fees,
>     ₹43,860.15, cash.
>   - Two payments to **Chakan Transport Lines** (₹80,855.61 each) are booked to Printing & Stationery and
>     Direct Wages, not goods-carriage hire. So the ₹10,000 limit applies, not ₹35,000.
> - **Planned:** 4 open bills carry `payment_gateway = cash`:
>   - BILL-2026-00044 ₹1,39,617.92;
>   - -00079 ₹57,503.66;
>   - -00082 ₹55,427.39;
>   - -00030 ₹14,831.73.
>
> Output: *"13 cash payments above ₹10,000 in August–September (₹7.03 lakh) will be disallowed for
> income tax. 4 open bills (₹2.67 lakh) are set to be paid in cash: pay them by bank transfer."*

---

## 6. Known-bad data

- **Expense amounts repeat:** ₹80,855.61 appears on many rows across unrelated vendors and accounts. That
  is seeded, but it is still exactly what the rule must catch.
- Payroll-like accounts (Direct Wages, Employer PF & ESI) appear among cash expenses. They are reported by
  count only (SalarySlip is prohibited).

---

## 7. Output contract

`finding_type: "cash_limit"`, `rule ∈ {cash_payment_disallowed, cash_payment_planned,
cash_payment_wages}`. Fields: `vendor_id`, `date`, `daily_total`, `limit_applied`,
`disallowed_amount`, `tax_effect` (amount × rulebook rate).

---

## 8. Limits

- Never blocks a payment and never edits a bill. It warns and escalates.
- Rule 6DD exceptions need facts the ledger doesn't hold (e.g. no bank in the village). They come from
  overrides.

---

## 9. Validation

1. **Live:** 13 vendor-days above ₹10,000, recomputed.
2. **Fixtures:**
   - two cash payments of ₹6,000 to one vendor on the same day → disallowed (₹12,000);
   - on different days → none.
3. **Transporter fixture:** ₹30,000 cash for truck hire → none; ₹36,000 → disallowed.

---

## 10. Open questions

- Is `Expense.paid_through_account` a free-text label or an account code? Cash detection currently
  matches names ("Cash", "Petty Cash"). `BankAccount.account_type = cash` should be the authority.
- Should the pre-payment warning run on bill approval or on the payment run ([UC-42](uc-42-payment-run-prioritisation.md))?
  Recommend both.

---

## 11. Live evidence — actual calls, 2026-10-04

- `PaymentMade.list {"limit":1000}` → 134: bank_transfer 92, cheque 42, cash 0.
- `Expense.list {"limit":1000}` → `paid_through_account`: Cash 17, Petty Cash 13, SBI Savings 12, ICICI
  11, HDFC 11, null 11.
- `Bill.list` → `payment_gateway = cash` on 4 open bills (BILL-2026-00082, -00079, -00044, -00030).
- `BankAccount.list` → "Petty Cash — Plant" (`account_type: cash`), HDFC Cash Credit, ICICI Current.
