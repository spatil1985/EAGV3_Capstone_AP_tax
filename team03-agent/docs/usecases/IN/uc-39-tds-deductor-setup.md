# UC-39 — TDS Deductor Setup and Section Coverage (TAN, Section Codes, 194A/194H/194R/194T/194-O)

**Domains: all five (194H: agency, retail · 194R: clinic, retail, agency · 194T: partnership agencies and clinics · 194-O: retail marketplace sellers) · Category: TDS / withholding · Verdict: 🟢 Buildable — live findings (no TAN; no valid section code on any bill)**
**Status: draft · live evidence 2026-10-04 · extends [UC-09](uc-09-vendor-tds-verification.md), which covers 194C/194J/194I recomputation**

---

## 1. Question

> *"Are we set up to deduct TDS at all, and are we deducting under every section that applies to what we pay?"*

---

## 2. Statutory basis

*Income-tax Act 1961 section numbers. Renumbering under the Income-tax Act 2025 (from 1 April 2026) is to
be confirmed. Rates and thresholds are our understanding after Finance Act 2025 (caveat).*

| Obligation | Rule | Consequence of default |
|---|---|---|
| **TAN** | Every deductor must obtain a TAN and quote it (s.203A) | Penalty ₹10,000 (s.272BB); deposits and returns can't be made without it |
| Deposit | By the **7th** of the next month (30 April for March) (s.200, Rule 30) | Interest 1%/month from deductible to deducted, 1.5%/month from deducted to paid (s.201(1A)) |
| Quarterly return | 26Q (residents) / 27Q (non-residents) by 31 Jul, 31 Oct, 31 Jan, 31 May (s.200(3)) | ₹200/day (s.234E); penalty (s.271H) |
| **194A** interest (not on securities) | 10%; threshold ₹10,000 per year for payers other than banks | Disallowance of 30% of the expense (s.40(a)(ia)) |
| **194H** commission / brokerage | 2% (from 1 Oct 2024); threshold ₹20,000 | same |
| **194R** business benefits / perquisites | 10%; threshold ₹20,000 per recipient per year (free samples to doctors, gifts to dealers, influencer products) | same |
| **194T** firm → partner remuneration / interest / commission | 10%; threshold ₹20,000 (from 1 April 2025) | same |
| **194-O** (receive side) | A marketplace deducts 0.1% from its sellers (from 1 Oct 2024). The seller claims it as credit | Unclaimed credit |
| **s.206AA** | No PAN → at least 20% | Short deduction |

---

## 3. Trigger

- **Scheduled monthly** on the 1st (deposit due on the 7th) and quarterly before each 26Q/27Q due date.
- **On event:** `bill.created` / `expense.created`, where the account or item maps to 194A/H/R/T.
- **On tenant onboarding:** the setup checks (TAN, preferences).
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `OrgProfile.list` | `enable_tds`, `tan`, `pan`, `enable_tcs` |
| `DirectTaxPreferences.list` | `tds_application_level`, `auto_apply_tds`, `default_tds_section`, `enable_tds_liabilities_report` |
| `Bill.list`, `Expense.list` | `tds_section_code`, `tds_section`, `tds_name`, `tds_percentage`, `tds_amount`, account / item mapping |
| `PaymentMade.list` | `tds_amount`, `unused_tds_amount` |
| `PaymentReceived.list` | `withholding_tax_amount`, `tax_deducted`: 194-O received from a marketplace |
| `Party.get` | `pan`, `type`, relationship (partner) via `PartyRelationship` |

---

## 5. Algorithm

1. **Setup checks:**
   - `tan_missing`: `enable_tds = 1` and `tan` empty.
   - `tds_not_auto_applied`: `auto_apply_tds = 0` and no TDS on payments. Context, not a finding by itself.
2. **Section validity:** `tds_section_code_invalid` when a document carries a TDS amount or percentage but
   the code isn't a statutory section (`192`–`196…` pattern), or the rate isn't a statutory rate for any
   section.
3. **Section coverage** (playbook table, account/item → section):
   - **194A:** interest expenses (including **MSME interest under MSMED s.16**) per payee per FY above
     the threshold.
   - **194H:** commission and brokerage accounts.
   - **194R:** samples, gifts, free products and sponsored travel to business recipients.
   - **194T:** payments to parties related as partners.
   For each payee-FY over the threshold with no TDS → `tds_section_not_applied`. Exposure = rate × amount,
   plus the s.40(a)(ia) disallowance.
4. **`tds_206aa_rate_short`:** payee without PAN, and the rate applied is below 20%.
5. **194-O credit (retail):** marketplace receipts net of 0.1% with no withholding recorded →
   `tds_194o_credit_unrecorded`.
6. **Deposit and return calendar:** reminder rows for the 7th and the quarterly due dates. The platform
   has **no challan tracking** (GST-18), so deposits can't be verified.

### Worked example (REAL, 2026-10-04)

> - **Setup:** `OrgProfile.enable_tds = 1`, **`tan = null`** → **`tan_missing`**. TDS can't be deposited
>   or reported under this profile.
> - **Preferences:** `auto_apply_tds = 0`, `default_tds_section = null`. `PaymentMade.tds_amount` is 0 on
>   all 134 payments.
> - **Section codes:** 9 non-void bills carry TDS fields. **0 of 9 have a valid section code**:
>   `tds_section_code` holds strings like `C5341/9637` and `FS2851/9624`, with `tds_section` and
>   `tds_name` null. The rates are 12% ×4, 15% ×4 and 5% ×1, none a statutory rate.
> - **194A on MSME interest:** 6 expenses booked to "MSME Interest (Section 16)", ₹2,60,427.54, no TDS.
>   For example, `8d4441b6-0eae-467c-a52f-9ba3a1718461` (2026-09-03, Rahul Sharma, ₹80,855.61). Each payee
>   above ₹10,000 in the FY → `tds_section_not_applied` (10%).
>   *Note: interest under MSMED s.16 is also **not deductible at all** (MSMED s.23). That is a
>   [UC-04](uc-04-msme-45-day-exposure.md) extension.*
>
> Output: *"TDS is switched on but the company has no TAN. No bill carries a valid TDS section. ₹2.60 lakh
> of MSME interest was paid without 194A deduction."*

---

## 6. Known-bad data

- **`tds_section_code` is seeded garbage** on every populated bill, the same family as N7 (`tds_amount`
  corrupt). Never derive the section from it; derive it from the account or item table.
- `tds_percentage` values (12, 15, 5) match no section. Treat them as suspect, like UC-09 does with
  `tds_amount`.

---

## 7. Output contract

`finding_type: "tds_setup"`, `rule ∈ {tan_missing, tds_section_code_invalid, tds_section_not_applied,
tds_206aa_rate_short, tds_194o_credit_unrecorded, tds_deposit_due, tds_return_due}`. Section findings carry
`section`, `payee_id`, `fy_total`, `threshold`, `rate`, `tds_due`, `disallowance_risk`.

---

## 8. Limits

- Verification only. It never deducts, deposits or files 26Q/27Q (no challan or return tools, GST-18).
- Payroll TDS (s.192) is out of scope: `SalarySlip` is prohibited for this seat.
- The 194R value of a benefit (e.g. free samples) needs the cost from purchase records, and may be partial.

---

## 9. Validation

1. **Live:** `tan` null; 0 of 9 valid codes; 6 MSME-interest expenses.
2. **Fixture (194A):** payee interest ₹9,000 in the FY → none; ₹11,000 → `tds_section_not_applied` at 10%
   = ₹1,100.
3. **Fixture (194H):** commission ₹25,000, no TDS → ₹500 at 2%.

---

## 10. Open questions

- Should the TDS playbooks merge? UC-09 (194C/J/I), UC-13 (194Q), UC-37 (195) and this use case share one
  section table. Recommend **one TDS playbook** with section strategies; this spec defines the setup and
  table half.
- Partner relationships for 194T: is `PartyRelationship` the right source? It has no "partner" type (it
  has `represents`, `associate`, …).

---

## 11. Live evidence — actual calls, 2026-10-04

- `OrgProfile.list` → `enable_tds: 1`, `tan: null`, `enable_tcs: 0`.
- `DirectTaxPreferences.list` → `tds_application_level: transaction`, `auto_apply_tds: 0`,
  `default_tds_section: null`.
- `Bill.list` → 9 non-void bills with TDS fields. Codes `C5341/9637`, `FS2851/9624`, `SP4335/9604`, …;
  rates 12% ×4, 15% ×4, 5% ×1.
- `Expense.list` → "MSME Interest (Section 16)" × 6, ₹2,60,427.54, `tds` absent.
- `PaymentMade.list` → `tds_amount = 0` on all 134.
