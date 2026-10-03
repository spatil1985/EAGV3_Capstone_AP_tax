# UC-16 — Drug Expiry and Batch Exposure → Blocked Credit

**Workstream B · Verdict: 🟢 Buildable (spec.md) → 🟡 Partial (live data)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Emits:** the UC-01 reversal row · **Reuses:** UC-02's blocking logic

---

## 1. Question

> *"What stock is about to expire, and what credit do we lose when it does?"*

(Verbatim from `spec.md` UC-16.)

---

## 2. Statutory basis

- **Section 17(5)(h), CGST Act** — ITC is **blocked** on goods lost, stolen, destroyed,
  **written off**, or disposed of by way of gift or free samples.
- Expired stock that is written off or destroyed therefore **reverses** the ITC
  originally claimed on it. The reversal is proportionate to the quantity written off,
  at the purchase-time tax.
- **Consequence if missed:** the write-off books a stock loss, while the credit stays
  claimed. It is recovered on audit with s.50 interest (18%) from the date of write-off.
- **Why it matters beyond clinics:** any batch-tracked perishable (retail food,
  chemicals, adhesives, and on this instance, powder coat) triggers the same rule.

---

## 3. Trigger

- **Scheduled daily:** find batches within the warning window (default 30 days) of
  expiry.
- **On write-off event:** a stock adjustment or scrap entry against an expired batch
  triggers the reversal computation.
- **Period:** point-in-time for the warning; transaction date for the reversal.

---

## 4. Input contract

| Need | Tool / field | Live status |
|---|---|---|
| Which items expire | `Item.list` → `shelf_life_days`, `batch_tracked` | ✅ 29 items with shelf life |
| **When a batch was received** (expiry = receipt + shelf life) | a batch / stock-entry record | ❌ **no `Batch.*`, `StockEntry.*` or `StockLedger.*` list/get tool among the 494 exposed to `finance_user`** |
| Purchase-time tax per unit | `Bill.items[]` for the item: `qty`, `cgst/sgst/igst_amount` | ✅ |
| Write-off event | a stock adjustment | ❌ not exposed |
| Movement of goods | `endpoint.inventory.shipments` | ✅ listed in `spec.md`; outward shipments only |

---

## 5. Algorithm

1. **Scope:** items with `shelf_life_days > 0` **and** `batch_tracked = 1`. An item with
   a shelf life but no batch tracking cannot be dated (§6).
2. **Receipt date proxy:** without batch records, use the most recent `Bill.date` whose
   lines include the item. `expiry_estimate = bill.date + shelf_life_days`. Record
   `basis: "bill_date_proxy"`.
3. **Warning:** `expiry_estimate − today ≤ 30` → `expiry_warning`, with quantity =
   that bill's `qty`.
4. **Credit at risk:** `per_unit_tax = line tax ÷ line qty` (Rule 0-valid lines only);
   `itc_at_risk = per_unit_tax × qty`.
5. **On write-off (when the event becomes observable):** emit a reversal row (UC-01 §7)
   with `rule = "s17_5_h_writeoff"`, `reversal_base_amount = per_unit_tax × qty
   written off`, and s.50 interest from write-off date to today if not reversed in that
   period's return.

### Worked example (real item, projected dates)

> Item **V-Block Pair 239mm (Mtr)** (`b19aa63c-8c2d-4b29-af26-c686fe508777`),
> `shelf_life_days = 53`, `batch_tracked = 1`, `product_type: goods`, HSN `82055900`.
>
> If a bill received 100 units on 2026-09-01 with ₹1,800 item-level GST (constructed):
> ```
> expiry_estimate = 2026-09-01 + 53 = 2026-10-24     → 26 days away → expiry_warning
> per_unit_tax    = 1,800 / 100 = 18.00
> itc_at_risk     = 18.00 × 100 = ₹1,800.00  (reversed only if written off)
> ```

---

## 6. Known-bad data

- **21 of 29 shelf-life items are not batch-tracked.** A shelf life with no batch is
  undatable, since you cannot know when *this* stock arrived. Emit
  `missing_required_field` for each.
- **Shelf lives are seed values on hand tools** (Pipe Wrench, 28 days; Lathe Dog,
  12 days). They exercise the logic; they are not a real exposure.
- **`product_type = services` on batch-tracked physical items** (Machinist Square,
  Pipe Wrench — UC-07). A "service" cannot expire. Treat shelf life as authoritative and
  flag the conflict.

---

## 7. Output contract

`expiry_warning` rows (`finding_type: "stock_expiry"`) with `item_id`, `item_name`,
`expiry_estimate`, `days_to_expiry`, `qty`, `itc_at_risk`, `basis`. On write-off, a
UC-01 §7 reversal row with `rule: "s17_5_h_writeoff"`.

---

## 8. Limits

- **Cannot see batches, receipts or write-offs directly.** The bill-date proxy
  overstates exposure if stock was consumed first-in-first-out. This is the reason for
  the 🟡.
- Never writes a stock adjustment or reversal.

---

## 9. Validation

1. **Scope count on the live snapshot:** 8 items in scope (shelf life + batch).
2. **Undatable count:** 21 `missing_required_field` rows.
3. **Arithmetic fixture** as the worked example. Boundary: `days_to_expiry = 30` warns;
   31 does not.

---

## 10. Open questions

- **Ask for a read-only batch/stock-entry tool.** This is the one change that moves
  UC-16 to 🟢, and it would also let UC-11 show the receipt document. File it alongside
  the F1 rewording.
- **Is expiry alone a trigger, or only write-off?** The statute blocks credit on
  write-off. Expired-but-held stock is not yet a reversal. The warning is commercial,
  and the reversal is statutory.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-16 Expiry blocked credit`.

**Call 1 — `Item.list {"limit":1000}`** → `shelf_life_days > 0` on **29** items;
`batch_tracked = 1` on **8** of those; `serial_tracked = 1` on 6 items overall.
Batch-tracked samples: Machinist Square 139mm (37 days), Lathe Dog 133mm (31), Pipe
Wrench 138mm (28), V-Block Pair 239mm (53), Vernier Caliper 213mm (56).

**Call 2 — `tools/list`** → 494 tools. **No** tool name matches `Batch.*`,
`StockEntry.*`, `StockLedger.*` or `SerialNo.*` with `.list`/`.get`.

**What the live data changed:** 🟢 → 🟡. `spec.md` listed `batch_tracked` and
`shelf_life_days` as sufficient. They say *that* an item expires, not *when a given lot
does*.
