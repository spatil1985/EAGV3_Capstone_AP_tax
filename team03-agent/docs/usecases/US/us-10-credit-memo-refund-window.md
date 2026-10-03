# US-10 — Sales Tax on Credit Memos & Refund Windows

**US · Proposed owner: Sandip · Verdict: ⚪ spec — no credit memos exist on the tenant**
**IN counterpart:** UC-19 (s.34(2) credit-note time limit) · **live evidence 2026-10-03**

---

## 1. Question

> *"For returns and price adjustments, did we refund the sales tax correctly, and are
> we still inside the window to recover tax we remitted?"*

## 2. Statutory basis

- When a seller refunds a customer (a return or price reduction) on a taxed sale, it
  refunds the tax on the refunded amount and may **deduct or credit** that tax on its
  next return, or claim a refund from the state.
- **Refund windows are set by state**, not federally. Ohio allows a refund
  application within **four years** of payment (R.C. 5739.07), and other states
  commonly allow three to four years. *Each state's window is carried as a constant
  with its citation, and must be confirmed before use.*
- **Consequence:** refunding tax to the customer without recovering it from the state
  is a direct loss. Recovering it without refunding the customer is a liability to
  the customer.

## 3. Trigger

- **Event:** on each credit memo against a taxed invoice.
- **Monthly:** credit memos approaching the state refund window.

## 4. Input contract

| Call | Fields |
|---|---|
| `CreditNote.list` | `invoice_id`, `date`, `items`, `total_tax`, `taxable_value`, `grand_total` — **not `taxes[]`** (N128 is on CreditNote) |
| `Invoice.get {"id": invoice_id}` | original `taxes[]` (jurisdiction, rate) and `date` |
| **Oracle** sales-tax-liability report | `tax_credited`, `credit_note_count`, `credited_sales` |

## 5. Algorithm

1. For each credit memo against a taxed invoice: expected tax credited = credited net
   × the original invoice's rate per jurisdiction. Mismatch → `credit_tax_wrong`.
2. Credit memo larger than the original invoice → `credit_exceeds_invoice` (the US
   form of IN N11).
3. Tax remitted on the original but not yet recovered, with the state window closing
   within 180 days → `refund_window_closing`.
4. Reconcile Σ credited tax against the report's `tax_credited` per jurisdiction.

### Worked example

None possible on live data: **0 credit notes** on Keystone, and the liability report
shows `credited_sales: 0.0` and `credit_note_count: 0` in every jurisdiction.

## 6. Known-bad data

- If credit notes appear, `CreditNote.taxes[]` is quarantined (N128). Use item-level
  amounts and the original invoice's rates.

## 7. Output contract

`finding_type: "sales_tax_credit"`, `rule ∈ {credit_tax_wrong, credit_exceeds_invoice,
refund_window_closing}`, `entity_type: "CreditNote"`, `total_exposure` = tax at risk.

## 8. Limits

Never files a refund claim and never edits credit notes.

## 9. Validation

Fixtures only, until a credit memo exists: a 50% credit on an OH invoice taxed at 6.5%
→ tax credited must be half the original tax; a credit dated past the window →
`refund_window_closing` suppressed, and `refund_window_lapsed` emitted instead.

## 10. Open questions

- Promote to 🟢 when the tenant's first credit memo appears. The playbook is `spec`
  until then.
- The state refund-window table: owner and source?

## 11. Live evidence — actual calls, 2026-10-03

- `GET /api/CreditNote?limit=1000` → `{"data":[],"total":0}`.
- Sales-tax-liability report (2026-01-01 … 09-30) → `credited_sales: 0.0`;
  `tax_credited: 0.0` and `credit_note_count: 0` in all 4 jurisdictions.
