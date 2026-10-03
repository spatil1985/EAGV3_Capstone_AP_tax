# UC-11 — Three-Way Match (PO ↔ Receipt ↔ Bill)

**Workstream C · Verdict: 🔴 Structurally blocked (spec.md) → 🟡 Partial — receipt leg exists (live data)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Backs:** F1 / GAP-4 — **the live data weakens F1's premise; see §10–11**

---

## 1. Question

> *"Were the goods we're being billed for actually received?"*

(Verbatim from `spec.md` UC-11.)

---

## 2. Statutory basis

- **Section 16(2)(b), CGST Act** — ITC is available only if the recipient **has
  received** the goods or services. A bill for goods not received carries **no
  claimable ITC**, whatever the invoice says.
- **Financial control** — three-way match (order = receipt = invoice, within tolerance)
  is the primary AP control against paying for goods never delivered.
- **Consequence if missed:** payment for undelivered goods, and ITC claimed in breach of
  s.16(2)(b) — reversed with s.50 interest and s.73/74 penalty.

---

## 3. Trigger

- **Document event:** on every bill with `purchase_order_id`, before approval for
  payment.
- **Scheduled:** daily re-match of `open` PO-linked bills. Receipts can land after the
  bill, so a bill that fails today may pass tomorrow.
- **Period:** point-in-time, per bill.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Bill.list` | `{"limit": 1000}` | Filter client-side on `purchase_order_id != null` (101 live) |
| `endpoint.accounting.bill_match` | `{"bill_id": id}` **or** `{"invoice_id": id}` | **The engine.** `inputSchema`: exactly one of the two, `additionalProperties: false` |
| `PurchaseOrder.get` | `{"id": purchase_order_id}` | Context only |

⚠️ `bill_match` is tagged `risk: WRITE`, `permission: Bill.read`, while its description
says "Read-only". That is N3. N2 showed it never persists (`recorded_status` stays
null), and 101 calls on 2026-09-28 confirmed it again. Treat it as read-only in
practice. Note the contradiction if an orchestrator gates on `risk`.

**`bill_match` response shape** (live):
```
result.live.basis                    "receipts_against_purchase_order"
result.live.status                   within_tolerance | exceeds_tolerance
result.live.price_tolerance_pct      2.0
result.live.qty_tolerance_pct        0.0
result.live.receipt_problem          null | "receipt_not_for_purchase_order"
result.live.stock_entry_id           the receipt document, when found
result.live.lines[]                  ordered_qty, received_qty, billed_qty, billed_to_date_qty,
                                     po_rate, bill_rate, price_variance_pct, qty_variance, flags[]
result.recorded_status               null on 101/101 (N2)
```

---

## 5. Algorithm

1. For every bill with `purchase_order_id`, call `bill_match`.
2. Classify from `live`:
   - `receipt_problem` non-null, or any line `received_qty = 0` with `billed_qty > 0`
     → **`billed_not_received`** (s.16(2)(b): no ITC; do not pay).
   - any line flag `qty_over_ordered` / `billed_to_date_qty > ordered_qty`
     → **`over_billed`** (also a UC-05 Tier 2 duplicate signal).
   - `|price_variance_pct| > price_tolerance_pct` → **`price_variance`**.
   - otherwise `within_tolerance` → no finding.
3. For `billed_not_received`, compute the ITC at risk: the bill's Rule 0-valid
   item-level tax.
4. **Cross-check against UC-04:** a `billed_not_received` bill from an MSME vendor must
   **not** be recommended for payment, even if it is past 45 days (§10).

### Worked example (REAL — BILL-2026-00018)

> **BILL-2026-00018** (`493e0627-3489-4ca0-bc1c-e8bb568110df`), vendor Pune Industrial
> Consumables (**MSME, micro**), dated 2026-08-02, `grand_total = balance_due =
> ₹64,664.00`, status `open`.
>
> `bill_match` live:
> ```
> ordered_qty 40000.0   received_qty 0.0   billed_qty 40000.0   billed_to_date_qty 40000.0
> receipt_problem "receipt_not_for_purchase_order"     status "exceeds_tolerance"
> ```
>
> ```
> classification = billed_not_received (40,000 units billed, 0 received against this PO)
> action         = do not pay; do not claim ITC (s.16(2)(b))
> UC-04 conflict = the same bill is 57 days old and 12 days past the MSME 45-day limit
> ```
>
> Output: *"BILL-2026-00018 (Pune Industrial Consumables, MSME) — billed for 40,000
> units, none received against the PO. Do not pay or claim ITC until receipt is
> confirmed. Note: UC-04 also flags this bill as past 45 days."*

---

## 6. Known-bad data

- **`Bill.match_status` / `match_detail` are null on 101/101** (N2). Always call the
  endpoint; never read the stored field.
- **`receipt_not_for_purchase_order`** may mean the goods arrived against a *different*
  receipt, not that they never arrived. Treat it as "unmatched receipt", worded
  carefully (§10).
- **Seed quantities are implausible** (40,000 units for ₹64,664). The logic is right
  even when the data is odd.

---

## 7. Output contract

```json
{
  "finding_type": "three_way_match",
  "rule": "billed_not_received",
  "entity_type": "Bill",
  "entity_id": "493e0627-3489-4ca0-bc1c-e8bb568110df",
  "entity_ref": "BILL-2026-00018",
  "counterparty_name": "Pune Industrial Consumables",
  "purchase_order_id": "…",
  "ordered_qty": 40000.0,
  "received_qty": 0.0,
  "billed_to_date_qty": 40000.0,
  "receipt_problem": "receipt_not_for_purchase_order",
  "amount_at_risk": 64664.00,
  "itc_at_risk": 0.00,
  "cross_flags": ["uc04_msme_past_45"],
  "action": "hold_payment",
  "status": "finding",
  "summary": "BILL-2026-00018 — 40,000 units billed, 0 received. Hold payment and ITC."
}
```

---

## 8. Limits

- Uses the platform's match engine as-is, including its tolerances (price 2%, qty 0%).
  It does not re-implement matching.
- Never writes `Bill.match_status`. Persisting the result is the platform's missing
  step (N2).
- Cannot inspect the receipt document directly. No `StockEntry` list/get tool is exposed
  to `finance_user` over MCP.

---

## 9. Validation

1. **Live distribution** (§11): 101 bills → 92 within, 9 exceeds. Re-running on the
   same snapshot must reproduce this exactly.
2. **Positive controls:** BILL-2026-00018 → `billed_not_received`; BILL-2026-00101 →
   `over_billed`.
3. **`recorded_status` remains null after every call.** If it ever becomes non-null,
   N2 is fixed, and the spec can read the stored field instead.

---

## 10. Open questions

- **F1 / GAP-4 needs rewording.** Filed as *"no record of goods being received … you
  cannot match against a document type that does not exist."* `bill_match` does compute
  `received_qty` from receipts (`stock_entry_id`, basis
  `receipts_against_purchase_order`). The accurate gap is narrower: **the receipt
  document is not exposed over MCP, and the match result is not persisted.** Update
  before triage reads it.
- **UC-04 interaction:** under MSMED Act s.15 the 45-day clock runs from the *day of
  acceptance*. If goods were never received, arguably there was no acceptance and the
  clock has not started. UC-04 should suppress its finding (or downgrade it) when UC-11
  says `billed_not_received`. **Needs agreement between UC-04 and
  UC-11.**

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-11 Three-way match`.

**Call — `endpoint.accounting.bill_match {"bill_id": …}` on all 101 PO-linked bills.**
0 errors.

| `live.status` | Bills |
|---|---|
| within_tolerance | 92 |
| **exceeds_tolerance** | **9** |
| `recorded_status` null | **101 / 101** |

The nine:

| Bill | Vendor | `grand_total` | Ordered | Received | Billed to date | Problem |
|---|---|---|---|---|---|---|
| BILL-2026-00101 `08837e85…` | Bosch Rexroth India | ₹4,444.00 | 2 | 2 | **4** | `qty_over_ordered` |
| BILL-2026-00005 `f69a13f0…` | Jindal Steel Depot *(MSME)* | ₹9,26,276.00 | 1,500 | **0** | 1,500 | receipt_not_for_purchase_order |
| BILL-2026-00006 `a20d0bf0…` | Pune Industrial Consumables *(MSME)* | ₹13,169.00 | 12,000 | **0** | 12,000 | 〃 |
| BILL-2026-00008 `56ef8b6a…` | Precision Fasteners Co *(MSME)* | ₹1,12,808.00 | 16,000 | **0** | 16,000 | 〃 |
| BILL-2026-00010 `62aa42e0…` | Shreeji Powder Coating *(MSME)* | ₹3,72,724.00 | 200 | **0** | 200 | 〃 |
| BILL-2026-00013 `02bc055d…` | Maharashtra Laser Gases *(MSME)* | ₹59,948.00 | 540 | **0** | 540 | 〃 |
| BILL-2026-00015 `e43e2d7f…` | Sandvik Tooling India | ₹3,99,969.00 | 1,680 | **0** | 1,680 | 〃 |
| BILL-2026-00017 `a0ef8c0f…` | Jindal Steel Depot *(MSME)* | ₹98,554.00 | 1,500 | **0** | 1,500 | 〃 |
| BILL-2026-00018 `493e0627…` | Pune Industrial Consumables *(MSME)* | ₹64,664.00 | 40,000 | **0** | 40,000 | 〃 |

**₹20,48,112 of open payables are billed against POs with nothing received.** 7 of the
8 are MSME vendors, which is exactly the UC-04 interaction in §10.

**What the live data changed:** the verdict moves from 🔴 to 🟡. The receipt leg exists
inside the platform. What is missing is its exposure and persistence, not its existence.
