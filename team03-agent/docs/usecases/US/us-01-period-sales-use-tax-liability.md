# US-01 — Period Sales & Use Tax Liability

**US · Proposed owner: Geetha · Verdict: 🟢 Buildable — platform report is a working oracle**
**IN counterpart:** period liability, harness_plan.md §6.1 (US column) · **live evidence 2026-10-03**

---

## 1. Question

> *"What is our sales and use tax liability this period, by jurisdiction?"*

(The first leg of the Core Challenge Prompt, for `tax_regime: sales_use_tax`.)

## 2. Statutory basis

- **Sales tax** is a trust-fund tax: the seller collects it from customers in each
  state where it has nexus and remits it to that state, plus any local jurisdictions,
  on the state's filing schedule. Keystone files **monthly** for OH, PA and MI
  (`TaxJurisdiction.filing_frequency`).
- **Use tax** is owed by the buyer on taxable purchases where no sales tax was charged.
  It is reported on the same state return (US-02).
- **Consequence of misstatement:** under-remittance carries interest and penalties.
  Because collected tax is held in trust, responsible officers can be held personally
  liable for it in most states.

## 3. Trigger

- **Monthly**, after month end and before each state's due date.
- **On request** for any date range.
- **Period:** filing period per jurisdiction; month by default.

## 4. Input contract

| Source | Call | Use |
|---|---|---|
| `Invoice.list` | `{"limit": 1000}` | `taxes[]` rows: `jurisdiction_id`, `jurisdiction_name`, `state_code`, `rate`, `amount`, `is_exempt`; `net_total`, `date`, `status` |
| `Bill.list` | `{"limit": 1000}` | `use_tax_accrued` (purchase side) |
| `TaxJurisdiction.list` | `{"limit": 100}` | rates, `filing_frequency`, `liability_account_id` |
| **Oracle** | `GET /api/accounting/reports/sales-tax-liability?from_date&to_date&basis=accrual` | per-jurisdiction `tax_billed / tax_credited / tax_collected`, `taxable_sales`, `exempt_sales` |

The oracle is REST-only (`../../submissions/requested_tools.md` T1). It also accepts `basis=cash`,
which prorates tax by the share of each invoice paid — the one place the platform
honours cash basis (`not_yet_supported.cash_basis`).

## 5. Algorithm

1. Invoices in the period, excluding `draft` and `void`.
2. **Sales tax by jurisdiction** = Σ `taxes[].amount` where `is_exempt` is false,
   grouped by `jurisdiction_id`. Taxable sales = Σ `net_total` of invoices with a
   non-exempt row; exempt sales = Σ `net_total` of invoices with an exempt row.
3. **Use tax** = Σ `Bill.use_tax_accrued` for bills in the period, plus any US-02
   finding marked confirmed.
4. **Reconcile with the oracle.** For each jurisdiction, `tax_billed` must equal step
   2 to the cent, and invoice counts must agree. Any difference is a `data_quality`
   row naming the jurisdiction.
5. Emit one `liability` row per jurisdiction and one total row, then a reconciliation
   verdict.

### Worked example (REAL — 2026-01-01 … 2026-09-30)

| Jurisdiction | Ours | Platform report | Invoices (ours / report) |
|---|---|---|---|
| Ohio State Sales Tax (5.75%) | $105,263.08 | $105,263.08 | 71 / 71 |
| Pennsylvania State Sales Tax (6%) | $64,679.15 | $64,679.15 | 28 / 28 |
| Michigan State Sales Tax (6%) | $42,816.08 | $42,816.08 | 28 / 28 |
| Stark County (OH) (0.75%) | $13,729.96 | $13,729.96 | 71 / **102** |
| **Total sales tax** | **$226,488.27** | **$226,488.27** | |
| Use tax accrued | **$0.00** | — | 0 of 101 bills |

Taxable sales $3,622,248.85 and exempt sales $570,195.62 also agree exactly.

> Output: *"Jan–Sep 2026 sales tax liability: $226,488.27 across 4 jurisdictions,
> matching the platform's liability report to the cent. Use tax accrued: $0. See
> US-02, where up to $16,964.03 may be owed."*

## 6. Known-bad data

- **Stark County invoice count is overstated in the report (102 vs 71).** The 31 exempt
  invoices carry their `is_exempt` row against `jurisdiction_id` = Stark County with
  `jurisdiction_level: "state"` — a county id labelled as a state row. The amounts are
  unaffected (0), but the count is. Reconcile on amounts; report the count gap.
- **The report shows `liability_account_id: null` on every jurisdiction** while every
  `TaxJurisdiction` row carries one (`ecec6350-…`). GL-to-report reconciliation cannot
  use the report's field.
- Item-level GST fields on US invoices are never read (US README rule 1).

## 7. Output contract

`finding_type: "tax_liability"`, one row per jurisdiction: `entity_type:
"TaxJurisdiction"`, `entity_id`, `entity_ref` (name), `total_exposure` = tax
collected, `details: {state_code, rate, taxable_sales, invoice_count, oracle_amount,
oracle_count, reconciled}`. Plus `data_quality` rows for any reconciliation gap.
Summary leads with the total and the reconciliation verdict.

## 8. Limits

- Reports liability; never files or remits (`not_yet_supported.tax_rate_service`:
  "NOT yet done: return filing/remittance").
- Cannot vouch for the rates themselves: they are manual (US README rule 3).
- Use tax is only as complete as US-02's classification.

## 9. Validation

1. **Oracle agreement to the cent** on amounts (live: 4/4).
2. Re-run with `basis=cash`. Totals must be ≤ accrual and equal it once every invoice
   is paid.
3. Month boundary: September alone gives OH $1,048.67 and Stark County $136.79 over 3
   invoices. Summing monthly runs must equal the YTD run.

## 10. Open questions

- File the Stark County count and the null `liability_account_id` as one small bug, or
  as a comment on B1 (the India liability-account defect)?
- Which GL account holds sales tax payable (`ecec6350-…`), and does its balance equal
  the report's `tax_collected` net of remittances? That needs `AccountingReport.trial_balance`
  (MCP), which is now available.

## 11. Live evidence — actual calls, 2026-10-03

- `GET /api/accounting/reports/sales-tax-liability?from_date=2026-01-01&to_date=2026-09-30`
  → 200: `{"taxable_sales":3622248.85,"exempt_sales":570195.62,"untaxed_sales":0.0,
  "credited_sales":0.0,"jurisdictions":[{"jurisdiction":"Ohio State Sales Tax",
  "tax_billed":105263.08,"invoice_count":71,"liability_account_id":null}, …]}`
- `Invoice.list {"limit":1000}` → 158 receivable invoices (137 paid, 17 sent,
  4 partially paid). Sample INV-2026-00158 (`e31f99fd-bd47-46c7-bef8-d561ce9ec41e`):
  net $296.00, `taxes[]` = Stark County 0.75% $2.22 + Ohio 5.75% $17.02.
- `Bill.list {"limit":1000}` → `use_tax_accrued` null on **101/101**.
- `TaxJurisdiction.list` → MI 6%, PA 6%, OH 5.75%, Stark County 0.75%; all
  `sourcing: destination`, `rate_source: manual`, `liability_account_id: ecec6350-…`.
