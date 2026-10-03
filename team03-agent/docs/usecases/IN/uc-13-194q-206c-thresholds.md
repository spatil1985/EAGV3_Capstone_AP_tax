# UC-13 — 194Q / 206C(1H) ₹50 Lakh Threshold Monitoring

**Workstream A · Owner: Sudip · Verdict: 🟡 Buildable by aggregation — with a statutory correction**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Which suppliers or customers have we crossed the ₹50 lakh line with?"*

(Verbatim from `spec.md` UC-13.)

---

## 2. Statutory basis

Income-tax Act 1961 numbering, as in `spec.md`. **README caveat: the Income-tax Act 2025
is understood to apply from 1 April 2026 and renumbers these.**

- **Section 194Q — TDS on purchase of goods.** A buyer whose turnover exceeded
  **₹10 crore** in the preceding FY must deduct TDS at **0.1%** on purchases of goods
  from a resident seller, on the amount by which FY-cumulative purchases from that
  seller exceed **₹50 lakh**. Deduct at credit or payment, whichever is earlier.
  Computed on value excluding GST when GST is shown separately (CBDT Circular 13/2021).
- **Section 206C(1H) — TCS on sale of goods.** ⚠️ **Our understanding is that it was
  omitted from 1 April 2025** (Finance Act 2025), leaving 194Q as the only mechanism on
  a goods transaction. `spec.md` treats 206C(1H) as live. **Confirm before
  implementing** (§10). This spec builds the sell side as the *mirror* of 194Q: what
  our customers should be deducting from us.
- **Consequence (buy side):** non-deduction → s.201(1A) interest and s.40(a)(ia)
  disallowance of 30% of the purchase.
  **Consequence (sell side):** if a customer should have deducted 194Q and did not, our
  26AS shows no credit. It is a reconciliation break, not our liability.

---

## 3. Trigger

- **Document event (buy side):** on each new `Bill` to a vendor, recompute that
  vendor's FY-cumulative. The obligation starts on **the bill that crosses ₹50 lakh**,
  not at year end.
- **Monthly (sell side):** reconcile receipts from large customers against TDS
  recorded on `PaymentReceived`.
- **Period:** financial year from `Company.fiscal_year_start` (live: `2026-04-01`).

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Bill.list` | `{"limit": 1000}` | FY filter client-side (no date-range operator — README Rule 6) |
| `Invoice.list` | `{"direction": "receivable", "limit": 1000}` | Sell side. Counterparty field is **`party_id`**, not `customer_id` |
| `PaymentReceived.list` | `{"limit": 1000}` | `tax_deducted`, `withholding_tax_amount`, `tds_tax_id`. Counterparty is **`customer_id`** here |
| `Company.list` | `{"limit": 5}` | `fiscal_year_start`. **No turnover field** — the ₹10 crore test cannot be evaluated from data (§10) |

---

## 5. Algorithm

**Buy side (194Q — our obligation)**
1. FY bills, grouped by `vendor_id`, **goods lines only** (non-`99` HSN).
2. Cumulative base = running Σ `taxable_amount` in `date` order.
3. The crossing bill is the first bill where the cumulative base > ₹50,00,000.
   TDS on that bill = 0.1% × (cumulative − 50,00,000); on later bills = 0.1% × bill
   base.
4. `194q_not_deducted` if the crossing bill or any later bill has `tds_amount = 0`.
5. `194q_approaching` when the cumulative base is within 20% of the line (₹40–50 lakh),
   so procurement knows before the crossing bill arrives.

**Sell side (mirror)**
6. FY receivable invoices grouped by `party_id`; cumulative Σ goods `taxable_amount`.
7. For customers past ₹50 lakh, compare the expected 194Q deduction (0.1% of the excess)
   with the `withholding_tax_amount` / `tax_deducted` recorded on that customer's
   `PaymentReceived` rows. Emit `194q_customer_not_deducting` for any gap. It is a
   26AS-reconciliation finding, not a liability.

### Worked example (REAL — sell side, Bharat EV Motors Ltd)

> Customer **Bharat EV Motors Ltd** (`dfbf9b89-7993-418c-8cf4-37d1ac423f23`).
> FY 2026-27 receivable invoices: **48**, `grand_total` Σ **₹3,96,60,415.00**.
> `PaymentReceived` from this customer in the ledger: **96 receipts, ₹7,07,85,189.23**,
> of which **0** carry `withholding_tax_amount > 0` or `tax_deducted ≠ 0`.
>
> ```
> threshold crossed          → yes, by a wide margin (goods-only base to be computed per step 6)
> expected 194Q by customer  → 0.1% × (FY goods base − 50,00,000)
> recorded TDS on receipts   → ₹0
> finding                    → 194q_customer_not_deducting (subject to Bharat EV's own turnover > ₹10 Cr,
>                               which is near-certain for an automotive OEM but not in our data)
> ```
>
> Output: *"Bharat EV Motors Ltd has bought well over ₹50 lakh of goods from us this FY,
> but no receipt records any TDS deducted. Expect a 26AS mismatch; confirm with the
> customer whether they are deducting under 194Q."*

**Buy side on live data:** no vendor is past ₹50 lakh. The largest is Jindal Steel Depot
at ₹29,86,170.40 taxable (₹35,23,681 incl. GST). Nothing is `approaching` either (<₹40
lakh).

---

## 6. Known-bad data

- **`grand_total` is negative on 101 bills** (N7). Always aggregate **`taxable_amount`
  from lines**, never `grand_total`, or the corrupt TDS reduces the cumulative.
- **Goods vs services by HSN prefix:** 54 bill lines have empty `hsn_or_sac`. The spec
  counts them as goods (conservative for 194Q) and reports how many were assumed.
- **`PaymentReceived.payment_type` is `invoice_payment` on all 215.** The ledger has no
  advance receipts, so there is no advance-timing complexity today.
- **`PaymentReceived` has no FY field**, and the ₹7.08 Cr is across all fetched
  receipts. Filter by `date` before stating an FY figure.

---

## 7. Output contract

```json
{
  "finding_type": "tds_threshold",
  "rule": "194q_not_deducted | 194q_approaching | 194q_customer_not_deducting",
  "side": "buy | sell",
  "counterparty_id": "dfbf9b89-7993-418c-8cf4-37d1ac423f23",
  "counterparty_name": "Bharat EV Motors Ltd",
  "fy": "2026-27",
  "cumulative_goods_base": null,
  "threshold": 5000000.00,
  "crossed_on_document": "INV-…",
  "expected_tds": null,
  "recorded_tds": 0.00,
  "status": "finding",
  "summary": "…"
}
```

---

## 8. Limits

- Cannot evaluate the **₹10 crore preceding-year turnover** condition. `Company` holds
  no turnover field. It is supplied by the user or the playbook, and stated in the
  output.
- Does not deduct TDS or file 26Q. It verifies and warns.
- Sell side is advisory: we cannot make a customer deduct.

---

## 9. Validation

1. **Boundary fixture:** vendor bills 30 L + 15 L + 10 L → crossing on the third bill;
   TDS = 0.1% × 5 L = ₹500.
2. **Live negative control (buy):** 0 vendors past ₹50 lakh → 0 `194q_not_deducted`
   findings.
3. **Live positive control (sell):** Bharat EV must appear as
   `194q_customer_not_deducting`.

---

## 10. Open questions

- **206C(1H) status** — confirm omission from 1 April 2025. If still live for our
  facts, re-add the TCS branch (collect 0.1% on receipts above ₹50 lakh), with the rule
  that TCS does not apply where the buyer deducts 194Q.
- **Income-tax Act 2025 renumbering** of 194Q.
- **₹10 crore turnover** — hardcode per tenant in the playbook, or ask the user once
  per FY?

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-13 194Q thresholds`.

**Call 1 — `Bill.list {"limit":1000}`** → top vendors by taxable base (all bills,
ledger starts 2026-06-07):

| Vendor | Bills | Σ `taxable_amount` |
|---|---|---|
| Jindal Steel Depot `e719db41…` | 6 | ₹29,86,170.40 |
| Shreeji Powder Coating `377141a6…` | 14 | ₹16,51,769.06 |
| Sandvik Tooling India `97717ad7…` | 5 | ₹15,17,532.80 |
| Chakan MIDC Utilities `448f90ae…` | 11 | ₹13,20,651.30 |

→ **0 vendors past ₹50 lakh.**

**Call 2 — `Invoice.list {"direction":"receivable","limit":1000}`** → top customers,
FY 2026-27 (`grand_total`):

| Customer (`party_id`) | Invoices | Σ `grand_total` |
|---|---|---|
| Bharat EV Motors Ltd `dfbf9b89…` | 48 | ₹3,96,60,415.00 |
| Tata Ficosa Automotive Systems `6a212827…` | 25 | ₹1,84,17,276.00 |
| Shubhangi Joshi `b5dedea8…` | 12 | ₹1,74,34,875.60 |
| Kirloskar Pumps Ltd `8ba32418…` | 28 | ₹1,61,40,477.00 |

**Call 3 — `PaymentReceived.list {"limit":1000}`** → 215 receipts; `tax_deducted = 0`
on **215/215**; from Bharat EV: 96 receipts, ₹7,07,85,189.23, **0 with TDS**.

**What the live data changed:** the buy-side use case `spec.md` had in mind has no live
case. The sell side, reframed as 194Q-by-customer, has a large one, and it is the more
useful output for this tenant.
