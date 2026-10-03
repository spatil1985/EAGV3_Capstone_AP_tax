# US-05 — Sales Tax Sourcing & Rate Correctness

**US · Verdict: 🟡 Buildable as a consistency check — one live contradiction found**
**IN counterpart:** UC-18 (rate correctness by product code) · **live evidence 2026-10-03**

---

## 1. Question

> *"Are we charging each customer the right state and local rate for where the sale
> is sourced?"*

## 2. Statutory basis

- **Sourcing** decides which jurisdiction's rate applies. Under *destination*
  sourcing it is the rate where the buyer receives the goods. Under *origin* sourcing
  it is the seller's location. Interstate sales are destination-sourced. Intrastate
  rules vary by state.
- **Ohio** (R.C. 5739.033) sets its own rules for intrastate delivered sales. *Whether
  Keystone's in-state deliveries are sourced to the customer's county or to Keystone's
  is the statutory question this spec depends on (US README caveat).*
- **Consequence:** under-charging means the seller owes the difference; over-charging
  means tax collected that was not due, which must still be remitted and is refundable
  to the customer.

## 3. Trigger

- **Event:** on each new invoice.
- **Monthly:** sweep before the return.

## 4. Input contract

| Call | Fields |
|---|---|
| `Invoice.list {"limit":1000}` | `taxes[]`: `jurisdiction_id`, `jurisdiction_level`, `state_code`, `rate`, `amount`, `is_exempt`; `net_total`, `party_id` |
| `Party.get` | `addresses[].state`, `.city`, `.postal` (the destination, since invoices carry no ship-to) |
| `TaxJurisdiction.list` | configured `rate_percentage`, `sourcing`, `county`, `effective_from/to` |

## 5. Algorithm

1. **Arithmetic:** for each non-exempt tax row, `amount` must equal
   `net_total × rate / 100` to within $0.05; otherwise `tax_amount_wrong`.
2. **Rate drift:** each row's `rate` must equal its jurisdiction's configured
   `rate_percentage` on the invoice date; otherwise `rate_drift`.
3. **State sourcing:** the state on the tax row must equal the customer's address
   state; otherwise `state_sourcing_mismatch`.
4. **Local sourcing:** for a jurisdiction with `sourcing: destination` and level
   `county`/`city`, the customer's address must lie in that county or city (a
   playbook table maps city or ZIP to county). If not → **`local_sourcing_mismatch`**,
   with the county tax charged as exposure.
5. **Missing local tax:** under destination sourcing, a customer in a county with no
   configured jurisdiction → `local_rate_unconfigured` (context). Rates are manual by
   platform design (US README rule 3), so this is reported, never filed.

### Worked example (REAL)

- Steps 1–3: **0 findings.** Every tax row's arithmetic is exact, and every taxed
  state equals the customer's state.
- Step 4: **36 Ohio invoices charge Stark County's 0.75% ($7,919.93 in total) to
  customers outside Stark County**: Columbus 32, Youngstown, Toledo, Cleveland, Akron.
  The jurisdiction is configured `sourcing: destination`.

> **INV-2026-00148** (`2a60c88d-ccd0-4d5b-b723-cd98af4018f4`), Cardinal Tillage Works,
> **Columbus** OH (Franklin County), net $31,377.78: Ohio 5.75% plus **Stark County
> 0.75% = $235.33**.
>
> Output: *"36 Ohio invoices to customers outside Stark County were charged Stark
> County tax ($7,919.93) although the jurisdiction is set to destination sourcing.
> Either the sourcing setting is wrong (if Ohio sources these sales to the seller's
> county), or these customers were charged the wrong county's rate and their own
> county's tax was not charged."*

## 6. Known-bad data

- Destination is inferred from the customer's address, which is a proxy for the
  ship-to address.
- 31 exempt rows carry Stark County's id with `jurisdiction_level: "state"` (US-01 §6).
  Step 4 skips exempt rows.

## 7. Output contract

`finding_type: "sales_tax_rate"`, `rule ∈ {tax_amount_wrong, rate_drift,
state_sourcing_mismatch, local_sourcing_mismatch, local_rate_unconfigured}`,
`entity_type: "Invoice"`, `total_exposure` = tax charged in the wrong jurisdiction,
`details: {customer_city, customer_state, jurisdiction, configured_sourcing}`.

## 8. Limits

- Cannot state the correct rate for an unconfigured county; there is no rate service
  (platform-documented).
- Never re-rates or edits invoices.

## 9. Validation

1. Live controls: 0 arithmetic errors, 0 state mismatches, 36 local mismatches. The
   Canton (35) and Massillon (31) customers are inside Stark County and must *not* be
   flagged.
2. Fixture: a Columbus customer charged Stark County tax → `local_sourcing_mismatch`
   for that county line's amount.

## 10. Open questions

- **Ohio sourcing.** Settle R.C. 5739.033 for Keystone's delivered in-state sales
  before deciding what to do about the finding.
  - If they are origin-sourced, the charges are right and `sourcing: destination` is
    misconfigured. That is a setup fix.
  - If they are destination-sourced, 36 customers paid the wrong county's tax. That is
    a refund and remittance problem, and arguably a platform bug: the configured
    sourcing is not applied.
- The city → county table: which source? (ZIP-to-county files are public.)

## 11. Live evidence — actual calls, 2026-10-03

- `TaxJurisdiction.list` → Stark County (OH) `33864f88-190f-4eee-95cd-3032534f96f2`,
  county level, 0.75%, `sourcing: "destination"`. Ohio State Sales Tax
  `a9f5bab7-203f-48ba-8236-f2a0600becf6`, 5.75%.
- `Invoice.list` + `Party.list` → OH taxed invoices by customer city: Canton 35,
  Columbus 32, Massillon 31, and one each in Youngstown, Toledo, Cleveland and Akron.
  All 71 taxed OH invoices carry the Stark County line.
- INV-2026-00158 (`e31f99fd-bd47-46c7-bef8-d561ce9ec41e`), Kathy Lindstrom,
  **Youngstown** (Mahoning County), $296.00, Stark County $2.22.
