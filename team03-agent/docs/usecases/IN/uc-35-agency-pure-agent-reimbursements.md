# UC-35 — Agency: Recharged Costs and the Pure-Agent Test (Rule 33)

**Domains: agency (media buying, events, travel, consulting); also any vertical that rebills costs · Category: output tax, domain-specific · Verdict: 🟡 Partial — billable-expense data exists; the expense-to-invoice link is empty, so the test can't complete live**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"When we pass client costs back to them, are we charging GST correctly on the recharge?"*

---

## 2. Statutory basis

- **s.15(2)(c) CGST Act:** the value of a supply **includes incidental expenses** the supplier charges the
  recipient. By default, a recharged cost is taxed at the agency's own service rate, typically 18%.
- **Rule 33:** a cost incurred **as a pure agent** of the client is excluded from value, but only if
  **all** of these hold:
  - a contract makes the agency the client's pure agent for that cost;
  - the agency holds no title to the goods or services bought, and doesn't use them for its own interest;
  - it recovers **only the actual amount**;
  - the payment is **shown separately** on the invoice;
  - the cost is in addition to the agency's own services.
- **Interaction with credit:** a cost excluded as pure agent is the client's cost. The agency shouldn't
  also take credit on it.
- **Consequence:** a recharge that fails the test, invoiced without GST, is **under-declared output tax**:
  s.73/74 demand with 18% interest.

---

## 3. Trigger

- **On event:** `invoice.created` with billable expenses for that customer; `expense.updated` to
  `status = invoiced`.
- **Scheduled monthly** before GSTR-1.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `Expense.list` | `is_billable`, `customer_id`, `status` (`unbilled\|invoiced\|reimbursed\|non_billable`), `amount`, `tax_amount`, `itc_eligibility`, `gst_no`, `date`, `description` |
| `Invoice.list` | `expense_id` (link to the recharged expense), `party_id`, `items[]` (description, amount, tax), `taxes[]` |
| `GeneralPreferences.list` | `enable_billable_expenses` |
| `config/overrides/pure_agent_contracts.yaml` | Which customers have a pure-agent clause (not in the data model) |

---

## 5. Algorithm

1. **Recharged expenses:** `is_billable = 1` and `status = invoiced`.
2. **Link** each one to its invoice by `Invoice.expense_id`. If there is no link, try customer + amount +
   date within 30 days; otherwise `recharge_unlinked`.
3. **Pure-agent test** for each linked recharge, using the conditions from §2:
   - contract clause (overrides);
   - recovered at actual: invoice line amount = expense amount;
   - shown separately: its own line;
   - no credit taken: expense `itc_eligibility = ineligible` or tax 0.
   Pass → the recharge line must carry **no GST**.
4. **`reimbursement_undertaxed`:** the test fails, and the recharge line carries less than the agency's
   service rate. Exposure = rate × recharge value − tax charged.
5. **`pure_agent_with_itc`:** excluded from value, yet credit was claimed on the expense.
6. **`billable_not_recharged`:** billable, `status = unbilled`, older than 60 days. This is revenue
   leakage rather than tax, reported as context.
7. **`billable_flag_conflict`:** `status = unbilled` while `is_billable = 0`. The flag and the status
   disagree.

### Worked example (REAL data, test incomplete)

> 120 expenses:
> - **17 billable**, of which **15 are `invoiced`**. For example:
>   - `531fd095-0e62-4149-8559-cdc79bd36057` (2026-09-11, ₹80,855.61, customer "ISO 9001 surveillance
>     auditor");
>   - `170bcd1d-d43e-470f-a29e-fbd22aa0bab7` (2026-09-10, ₹80,855.61).
> - **Invoices carrying `expense_id`: 0 of 487** → all 15 are `recharge_unlinked`.
> - 3 billable expenses are still unbilled.
> - 48 expenses are `status = unbilled` while `is_billable = 0` → `billable_flag_conflict`.
>
> **Constructed continuation:** agency rebills ₹50,000 of media cost on a separate line, at actual, with
> no pure-agent clause on file. The test fails, so 18% (₹9,000) is due on the line; if the invoice charged
> nothing, `reimbursement_undertaxed` is ₹9,000.

---

## 6. Known-bad data

- **The `Invoice.expense_id` link is never populated**, although billable expenses are enabled and 15
  are marked invoiced. Either the "bill to customer" flow doesn't set the link, or the seeder skipped it.
  Candidate bug report.
- Expense amounts repeat (₹80,855.61 on many rows) and tax amounts fail UC-33's rate test. Exposure
  figures inherit UC-33's exclusions.

---

## 7. Output contract

`finding_type: "recharge"`, `rule ∈ {reimbursement_undertaxed, pure_agent_with_itc, recharge_unlinked,
billable_not_recharged, billable_flag_conflict}`. Fields: `expense_id`, `invoice_id`,
`pure_agent_test` (a per-condition pass/fail map), `total_exposure`.

---

## 8. Limits

- The contract condition can't be read from AgentSwitch (contracts are a prohibited entity for this
  seat). It comes from a human-maintained override file, and its absence makes the test "fail, unknown".
- Never edits invoices or expenses.

---

## 9. Validation

1. **Live:** 15 invoiced billable expenses, 0 links. Recompute.
2. **Fixtures:**
   - all five conditions pass and the line has no GST → no finding;
   - remove the contract clause → `reimbursement_undertaxed` at 18% of the line.
3. **Fixture:** pure agent and expense credit claimed → `pure_agent_with_itc`.

---

## 10. Open questions

- What does the platform's "bill expense to customer" action write: `Invoice.expense_id`, an item-level
  link, or nothing?
- Agency service rate: 18% for most services. Does any agency tenant need a different rate table
  (advertising space sale vs agency commission)?

---

## 11. Live evidence — actual calls, 2026-10-04

- `Expense.list {"limit":1000}` → `is_billable` 17, `status=invoiced` 15, `customer_id` present on 113.
- `Invoice.list {"limit":1000}` → `expense_id` null on all 487.
- `GeneralPreferences.list` → `enable_billable_expenses: 1`.
