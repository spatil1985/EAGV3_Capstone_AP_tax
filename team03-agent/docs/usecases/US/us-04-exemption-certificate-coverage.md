# US-04 — Exemption Certificate Coverage on Untaxed Sales

**US · Proposed owner: Geetha · Verdict: 🟢 Buildable — 0 findings on live data**
**IN counterparts:** UC-07 (exempt vs taxable), UC-20 (zero-rating needs documentation) · **live evidence 2026-10-03**

---

## 1. Question

> *"For every sale we didn't charge tax on, do we hold a valid exemption certificate?"*

## 2. Statutory basis

- A seller in a nexus state must collect sales tax unless the sale is exempt **and the
  seller holds the buyer's exemption certificate** (resale, manufacturing, nonprofit,
  government …). In Ohio this is the blanket or unit certificate under R.C. 5739.03.
- **Consequence if missed:** on audit, an exempt sale without a certificate (or with
  an expired or out-of-state one) is treated as taxable. The *seller* owes the tax it
  did not collect.

## 3. Trigger

- **Event:** on each invoice with an exempt tax row.
- **Monthly:** certificates expiring within 90 days.
- **Period:** invoice date against the certificate's validity.

## 4. Input contract

| Call | Fields |
|---|---|
| `Invoice.list {"limit":1000}` | `taxes[]` where `is_exempt: true` (`state_code`, `tax_type`, e.g. "Sales tax — exempt (resale certificate)"), `party_id`, `date`, `net_total`, `status` |
| `ExemptionCertificate.list` | `party_id`, `certificate_number`, `exemption_reason`, `state_code`, `issue_date`, `expiry_date`, `status`, `certificate_file` |
| `TaxJurisdiction.list` | rates, to value the tax at risk |

## 5. Algorithm

1. Invoices with an `is_exempt` tax row, excluding `draft` and `void`.
2. **Covered** if the customer has a certificate with `status: active`, `state_code`
   equal to the invoice's state (or blank for a multistate certificate), and
   `issue_date ≤ invoice date ≤ expiry_date`.
3. Not covered → **`exemption_without_certificate`**, with exposure = `net_total` ×
   the combined rate for that state.
4. Covered, but the certificate expires within 90 days → `certificate_expiring`
   (context row).
5. Certificate with no `certificate_file` → `certificate_unsupported` (data quality: no
   document on file to show an auditor).

### Worked example (REAL)

31 exempt invoices, $570,195.62, all to **Tri-State Farm Equipment**, all in Ohio,
each tax row "Sales tax — exempt (resale certificate)". Certificate
**OH-ST1-2025-0447** (`e2caaa81-223e-4fdd-ae5f-35a89ade3884`): resale, OH, issued
2025-04-02, expires 2029-04-01, active.

> Output: *"All 31 exempt sales ($570,195.62) are covered by Tri-State Farm Equipment's
> Ohio resale certificate, valid to 1 April 2029. Note: no certificate file is attached
> to the record."*

## 6. Known-bad data

- The exempt tax rows point at `jurisdiction_id` = Stark County but are labelled
  `jurisdiction_level: "state"`. Read `state_code`, not the level (see US-01 §6).
- `certificate_file` is null, so coverage is "recorded", not "evidenced".

## 7. Output contract

`finding_type: "sales_exemption"`, `rule ∈ {exemption_without_certificate,
certificate_expiring, certificate_unsupported}`, `entity_type: "Invoice"` or
`"ExemptionCertificate"`, `total_exposure` = uncollected tax at risk.

## 8. Limits

- Does not judge whether the stated exemption reason is legitimate for that customer.
- Never edits certificates or invoices.

## 9. Validation

1. Live: 31/31 covered → 0 `exemption_without_certificate`; 1 `certificate_unsupported`.
2. Fixtures: an invoice dated a day after `expiry_date` → finding; a PA invoice
   against an OH-only certificate → finding.

## 10. Open questions

- Report `certificate_unsupported` on every run, or only once?
- Does any state accept a certificate collected *after* the sale (a "good faith" cure
  period)? That would downgrade some findings.

## 11. Live evidence — actual calls, 2026-10-03

- `ExemptionCertificate.list` → 1 record (above). Customer `e72f519c-19e7-4842-ae63-7e7f3f4c9874`.
- `Invoice.list {"limit":1000}` → 31 invoices with an exempt row, e.g. INV-2026-00150
  (`7f64b10c-6edf-4190-989c-6d452aa8d5f0`) 2026-06-20 $33,793.44; INV-2026-00145
  (`d1b5642e-6bb1-4877-b638-0deecbcb8ba6`) 2026-07-25 $26,359.84; INV-2026-00140
  (`301dc79e-1a75-4dc9-b2d0-9c874b77ea9d`) 2026-08-20 $13,179.92.
- Oracle: the liability report's `exempt_sales` = $570,195.62, matching exactly.
