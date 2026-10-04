# UC-23 — Period GST Liability and Credit Utilisation (GSTR-3B)

**Domains: all five · Category: core tax · Verdict: 🟡 Partial — computable from the ledger; the platform's own return figures do not reconcile**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

The India half of *"what is our tax liability this period?"*, which is the first part of the Core Challenge
Prompt. Its US counterpart is [US-01](../US/us-01-period-sales-use-tax-liability.md). The two share one
playbook, with a strategy per `tax_regime`.

---

## 1. Question

> *"How much GST do we owe for this month, under each head, and how much of it must be paid in cash?"*

---

## 2. Statutory basis

- **s.39(1) CGST Act + Rule 61**: monthly GSTR-3B by the 20th of the next month for a taxpayer with
  aggregate turnover above ₹5 crore. Smaller taxpayers may use QRMP (quarterly; see [UC-29](uc-29-turnover-based-obligations.md)).
- **s.49 + s.49A + Rule 88A**: the order in which credit is used:
  - IGST credit is used first, against IGST, then against CGST and SGST.
  - CGST credit pays CGST, then IGST.
  - SGST credit pays SGST, then IGST.
  - CGST credit never pays SGST, and SGST credit never pays CGST.
- **Reverse-charge tax is paid in cash.** It can't be paid from the credit ledger (s.49(4) read with the
  definition of output tax). It comes from [UC-03](uc-03-rcm-self-invoicing.md) and [UC-21](uc-21-import-of-services-rcm.md).
- **Rule 86B**: if taxable supplies in a month (excluding exempt and zero-rated) exceed **₹50 lakh**,
  credit may pay at most **99%** of output tax, so at least 1% goes in cash. Exceptions: income tax above
  ₹1 lakh paid in each of the last two FYs, refunds above ₹1 lakh, and others.
- **s.50(1) proviso**: interest at **18% p.a.** on the net tax paid late in cash. Under-declaration is
  recovered under s.73/74 with interest and penalty.

---

## 3. Trigger

- **Scheduled monthly**, on the 15th, so the result is ready before the 20th due date. It runs again on
  the 19th as a final check.
- **On request** for any month, including the current month to date.
- **Period:** the tax period (calendar month). For a QRMP tenant, the quarter.

---

## 4. Input contract

| Tool | Arguments | Fields used |
|---|---|---|
| `Invoice.list` | `{"limit":1000}` (client-side: `direction=receivable`, status not draft/cancelled, date in period) | `date`, `gst_treatment`, `place_of_supply`, `taxable_value`, `taxes[]` (`tax_type`, `amount`), `items[]` tax fields, `is_reverse_charge` |
| `CreditNote.list` | `{"limit":1000}` | Outward reductions, item-level only (N128), filtered by the [UC-19](uc-19-credit-note-time-limit.md) window |
| `Bill.list` | `{"limit":1000}` | `itc_eligibility`, `ims_status`, `is_reverse_charge`, `taxes[]`/`items[]` |
| `VendorCredit.list` | `{"limit":1000}` | Inward credit notes that reduce credit, from [UC-25](uc-25-vendor-credit-debit-notes-itc.md) |
| `GSTReturn.list` | `{"limit":1000}` | `return_type=GSTR-3B`, `return_period`, `taxable_amount`, `igst/cgst/sgst/cess_amount`, `net_tax_payable`, `filing_status`. **The oracle** |

Fields confirmed in `/api/schemas` and on live records on 2026-10-04. The tax source is chosen per
document (IN README, correction of 2026-09-30): `taxes[]` where it reconciles to `total_tax`, otherwise
valid `items[]` lines.

---

## 5. Algorithm

1. **Output tax by head** (IGST, CGST, SGST, cess) from receivable invoices in the period. Add RCM liability
   (UC-03/UC-21) as a separate cash-only line. Subtract outward credit notes inside their s.34 window.
2. **Eligible credit by head:** bills with `itc_eligibility ≠ ineligible`, then remove:
   - IMS-rejected bills ([UC-24](uc-24-unclaimed-itc-ims-2b.md));
   - blocked credit ([UC-02](uc-02-blocked-credit-audit.md), [UC-33](uc-33-expense-claims-itc.md));
   - Rule 37 reversals ([UC-01](uc-01-rule-37-itc-reversal.md));
   - Rule 42/43 reversals ([UC-08](uc-08-rule-42-apportionment-school.md));
   - credit reductions from registered-vendor credit notes ([UC-25](uc-25-vendor-credit-debit-notes-itc.md)).
3. **Utilise credit in the statutory order** (s.49/49A/Rule 88A, §2). What remains on each head is cash
   payable.
4. **Rule 86B test:** taxable outward supplies in the month above ₹50 lakh and no exception recorded in
   overrides → cash must be at least 1% of output tax.
5. **Oracle cross-check:** compare step 1's taxable value and head totals with the GSTR-3B row for the
   period. A difference of more than ₹1 per head is a `stored_value_mismatch` finding.
6. Emit one `period_liability` row per head, plus findings for 86B, RCM, oracle mismatch and every document
   excluded by the tax-source rule.

### Worked example (REAL: August 2026, Suryodaya)

> **Output:** 14 receivable invoices, taxable ₹46,44,015.04 → CGST ₹3,98,398.95 + SGST ₹3,98,398.97.
> **Credit:** 10 bills, CGST ₹1,14,142.32 + SGST ₹1,14,142.32 (none IMS-rejected).
> **Credit reduction:** registered-vendor credit notes dated August, clean heads only: CGST ₹1,780.20 + SGST ₹1,780.20.
> ```
> CGST  = 3,98,398.95 − 1,14,142.32 + 1,780.20 = 2,86,036.83
> SGST  = 3,98,398.97 − 1,14,142.32 + 1,780.20 = 2,86,036.85
> cash  = ₹5,72,073.68     RCM: 0     Rule 86B: taxable ₹44,26,655.04 ≤ ₹50 lakh → not triggered
> ```
> **July 2026:** taxable outward ₹1,29,15,228.02, which is above ₹50 lakh, so **Rule 86B applies**. At
> least 1% of output tax (₹23,247.41) must be paid in cash unless an exception is recorded.
>
> **Oracle:** the August GSTR-3B row says taxable ₹2,63,10,000 over 161 transactions, against ₹46,44,015.04
> over 14 invoices in the ledger. The filed July GSTR-3B says ₹2,48,50,000 against ₹1,34,98,123.63.
> `net_tax_payable` is null on every row → `stored_value_mismatch`, and the oracle cannot be used.

---

## 6. Known-bad data

- **`GSTReturn` figures are round numbers that do not reconcile to the ledger** (above), and `summary[]` is
  empty on all 5 rows. Treat the return rows as a claim to check, never as the answer. This is a candidate
  bug report.
- **`VendorCredit.taxes[].tax_type` carries product names** on part of the population ("Feeler Gauge Set
  10337", "C-Clamp 10400"). This is the same seeder pattern as N127/N128. Use only rows whose head
  resolves to IGST/CGST/SGST/cess; otherwise use valid `items[]` lines (Rule 0).
- **Recurring-generated invoices** fall to tax source "none" (N10). Exclude them and say so in the summary.

---

## 7. Output contract

`finding_type: "period_liability"`, `rule ∈ {head_payable, rule_86b_cash_floor, rcm_cash_liability,
stored_value_mismatch, data_quality}`.

```json
{
  "finding_type": "period_liability", "rule": "head_payable", "period": "2026-08",
  "head": "CGST", "output_tax": 398398.95, "credit_used": 112362.12, "cash_payable": 286036.83,
  "currency": "INR", "status": "context",
  "summary": "August 2026: ₹5,72,073.68 payable in cash (CGST ₹2,86,036.83, SGST ₹2,86,036.85); no IGST; Rule 86B not triggered."
}
```

The run's one-sentence summary gives the cash total, the split by head, the Rule 86B status and whether
the oracle agrees.

---

## 8. Limits

- Computes and reports only. It never files GSTR-3B or pays tax: there is no filing tool, and
  `JournalEntry` is read-only.
- It doesn't know Rule 86B exceptions (income-tax history, refunds). They come from `config/overrides/`.
- Interest on late payment is computed in [UC-27](uc-27-return-filing-timeliness.md), not here.

---

## 9. Validation

1. **Hand-computed control:** the August example above, recomputed independently.
2. **Utilisation fixture:**
   - IGST credit 100, CGST output 60, SGST output 60, IGST output 0 → IGST credit pays CGST 60, then SGST 40,
     leaving SGST cash 20.
   - The same fixture with CGST credit instead must never pay SGST.
3. **86B fixture:** taxable ₹50,00,001 → floor applies; ₹50,00,000 → does not.
4. **Oracle:** once a return row is populated (`net_tax_payable` not null), compare head by head.

---

## 10. Open questions

- Are IMS-`pending` bills deemed accepted (counted in credit) or kept pending (excluded)? See UC-24 §10.
  This example counts them.
- Should the oracle be the platform's own tax-summary report instead of `GSTReturn`? Is there a REST
  endpoint that computes 3B from the ledger?
- The ₹2.48 Cr filed July return vs ₹1.35 Cr of July invoices: is this a seeding artefact or a defect in
  how returns are generated? Worth filing with these numbers.

---

## 11. Live evidence — actual calls, 2026-10-04

- `GSTReturn.list {"limit":1000}` → 5 rows:

  | Return | Period | Status | Due | Filed | Taxable | Transactions |
  |---|---|---|---|---|---|---|
  | GSTR-3B `c13b302d…` | 07-2026 | filed | 2026-08-20 | 2026-08-08 | ₹2,48,50,000 | 148 |
  | GSTR-3B `b66093cf…` | 08-2026 | unfiled | 2026-09-20 | — | ₹2,63,10,000 | 161 |

  Also GSTR-1 07-2026 and 08-2026 and GSTR-2B 08-2026. `net_tax_payable` is null and `summary` is `[]` on
  all five.
- `Invoice.list {"limit":1000}` → 487 invoices, 250 live receivable. July has 27 invoices, taxable
  ₹1,34,98,123.63, tax ₹23,24,741.06 (IGST ₹5,11,927.52). August has 14, taxable ₹46,44,015.04.
- `Bill.list {"limit":1000}` → 281 bills, 100 open + 17 draft + 164 void. August credit ₹2,28,284.64.
- `VendorCredit.list {"limit":1000}` → 100. August registered-vendor credits have clean CGST/SGST of
  ₹1,780.20 each, plus product-named tax rows.
