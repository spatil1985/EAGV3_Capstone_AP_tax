# US-03 — Economic Nexus Threshold Monitoring

**US · Proposed owner: Sudip · Verdict: 🟢 Buildable — 0 findings on live data, which is the correct result**
**IN counterpart:** UC-13 (a cumulative threshold that starts an obligation) · **live evidence 2026-10-03**

---

## 1. Question

> *"Are we approaching a new state's sales tax registration obligation anywhere?"*

## 2. Statutory basis

- **South Dakota v. Wayfair (2018)** lets states require a remote seller to collect
  sales tax once its sales into the state pass an *economic nexus* threshold, even
  with no physical presence. Most states use **$100,000** of sales in the current or
  previous calendar year. Some also have, or had, a 200-transaction test.
  *Our understanding: Illinois dropped the 200-transaction test from 1 January 2026
  (caveat).*
- **Consequence if missed:** the seller owes the tax it should have collected from the
  date the threshold was crossed, out of its own pocket, plus interest and penalty.

## 3. Trigger

- **Monthly**, and on request.
- **Event:** on each invoice to a state without a registered nexus.
- **Period:** calendar year to date, and the previous calendar year.

## 4. Input contract

| Call | Fields |
|---|---|
| `TaxNexus.list` | `state_code`, `status` (active / monitoring), `is_registered`, `economic_threshold_amount`, `economic_threshold_transactions`, `ytd_sales_amount`, `ytd_transaction_count` |
| `Invoice.list {"limit":1000}` | `date`, `status`, `net_total`, `party_id`, `taxes[].state_code` |
| `Party.get` | `addresses[].state`, which is the destination when an invoice has no tax row (exempt or untaxed) |

## 5. Algorithm

1. Calendar-YTD invoices, excluding `draft` and `void`.
2. **State per invoice:** the `state_code` of its tax row (taxed or exempt); otherwise
   the customer's address state. Unknown → `missing_required_field`.
3. Aggregate sales (`net_total`) and transaction count per state.
4. For each state:
   - not registered and over the threshold → **`nexus_threshold_crossed`**, dated at
     the crossing invoice;
   - not registered and at 80% or more → `nexus_threshold_approaching`;
   - registered → no threshold finding.
5. **Recompute vs stored:** if `TaxNexus.ytd_*` differ from step 3, emit
   `stored_value_mismatch`. This is the check that found N4.
6. States with sales but no `TaxNexus` row at all → `nexus_unmonitored`.

### Worked example (REAL — 2026 YTD)

| State | Status | Platform YTD | Our recompute | Finding |
|---|---|---|---|---|
| OH | active, registered | $2,400,857.51 / 102 | $2,400,857.51 / 102 | none |
| PA | active, registered | $1,077,985.76 / 28 | $1,077,985.76 / 28 | none |
| MI | active, registered | $713,601.20 / 28 | $713,601.20 / 28 | none |
| IL | monitoring | $0.00 / 0 | $0.00 / 0 (no IL customers) | none |

> Output: *"No unregistered state is near an economic-nexus threshold. All 2026 sales
> are in OH, PA and MI, where we are registered. Platform counters agree with
> invoices."*

## 6. Known-bad data

- **N4 (filed) appears fixed.** On 2026-09-23 every `ytd_*` field read 0. On 2026-10-03
  all four equal our recompute. Keep the step-5 check permanently: it is the regression
  guard.
- Invoices carry no ship-to address (US README rule 2). An invoice with no tax row and
  a customer with no address cannot be placed (0 such today).

## 7. Output contract

`finding_type: "nexus"`, `rule ∈ {nexus_threshold_crossed, nexus_threshold_approaching,
nexus_unmonitored, stored_value_mismatch}`, `entity_type: "TaxNexus"` (or `"State"`
when unmonitored), `total_exposure` = sales past the threshold × that state's rate
(the uncollected tax risk).

## 8. Limits

- Uses the platform's threshold fields. Per-state rules (sales measured gross or
  retail, marketplace sales excluded, previous-year look-back) live in a playbook table.
- Never registers or changes `TaxNexus`.

## 9. Validation

1. Live: 0 findings, and 4/4 stored-vs-recomputed matches.
2. Fixture: an unregistered state at $95,000 → `approaching`; at $100,001 →
   `crossed`, dated at the invoice that crossed.

## 10. Open questions

- **Tell triage N4 looks fixed?** Recommend a comment on the N4 card with these
  numbers.
- Should the previous calendar year count (most states use "current or prior year")?
  It needs 2025 invoices; the tenant's ledger starts 2026-01-26.

## 11. Live evidence — actual calls, 2026-10-03

- `TaxNexus.list` → IL `4a70d682-f7b6-45f3-a15b-663404a8d6fa` (monitoring, 0 / 0),
  MI `61066fea-7c8c-4568-877f-47641211889d` ($713,601.20 / 28), PA
  `9d87f28e-facb-4265-91ce-e01fff5e02ee` ($1,077,985.76 / 28), OH
  `f39e96bb-1f7f-46dd-8992-65bd6568478b` ($2,400,857.51 / 102). All thresholds
  $100,000 / 200.
- `Invoice.list {"limit":1000}` → 158 invoices, 2026-01-26 … 2026-09-14. Customer
  address states: OH 102, MI 28, PA 28, IL 0.
