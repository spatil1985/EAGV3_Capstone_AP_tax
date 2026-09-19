# Playbook: Tax Liability & ITC (Input Tax Credit) Audit

## Trigger
Invoked when asked: "What is our tax liability this period?", "What is unclaimed?",
or any request to reconcile output tax vs. input tax credit.

## Procedure
1. Call `GET /api/accounting/locale` to determine jurisdiction (`IN` vs `US`). Do not
   assume locale from company name.
2. Query the period's tax-bearing records:
   * `TaxLine.list(period=..., type=["sales_invoice", "purchase_bill"])`
3. Pass the raw record list to `scripts/tax_math.py::compute_tax_reconciliation`.
   Never sum currency amounts in-context; the agent must not do floating-point
   arithmetic over >5 records itself (see `SKILL.md` Hard Rule 3).
4. Interpret the result per locale:
   * **India (GST)**: `output_tax_total` = GST collected on sales; `claimed_itc_total`
     = Input Tax Credit already claimed; `unclaimed_itc_total` = eligible but
     unclaimed ITC (flag for follow-up, since ITC has a claim window under GST law).
     `net_liability` = GST payable this period.
   * **US (Sales & Use Tax)**: `output_tax_total` = Sales tax collected;
     `claimed_itc_total`/`unclaimed_itc_total` map to Use Tax already remitted vs.
     accrued-but-unremitted use tax where applicable.
5. Return structured summary: Locale, Output Tax, Claimed Credit, Unclaimed Credit,
   Net Liability, and the record IDs contributing to `unclaimed_itc_total` so a human
   can action the claim.

## Notes
* MSME vendors (India) require separate 45-day payment tracking; do not conflate with
  ITC eligibility.
* If `is_itc_eligible` is missing/null on a record, treat as not eligible and flag the
  record rather than guessing.
