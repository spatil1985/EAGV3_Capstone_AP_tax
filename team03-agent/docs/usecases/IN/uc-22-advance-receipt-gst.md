# UC-22 — Advance-Receipt GST on Services

**Workstream C · Owner: Sandip · Verdict: 🟡 Partial (advances are visible; their tax is not representable)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Have we paid GST on client advances we're still holding?"*

(Verbatim from `spec.md` UC-22.)

---

## 2. Statutory basis

- **Section 13(2), CGST Act — time of supply of services:** the **earlier** of (a) the
  invoice date (if issued within the s.31 time limit) or (b) the date of **receipt of
  payment**. An advance received for services therefore triggers GST **on receipt**.
- **Rule 50, CGST Rules** — on receiving an advance, the supplier issues a **receipt
  voucher** showing the tax. **Rule 51** — a refund voucher if the service is not then
  supplied.
- **Goods are different:** Notification 66/2017-Central Tax exempts GST on advances for
  **goods** (for all taxpayers except composition dealers). The goods/services split
  therefore decides whether an advance is taxable at all.
- **Zero-rated recipients:** an advance for services to an SEZ unit under LUT carries
  tax at 0%, and the receipt voucher still has to be issued.
- **Consequence if missed:** GST on the advance is due in the return for the month of
  receipt. When paid later, on the final invoice, s.50 interest runs for the months in
  between.

---

## 3. Trigger

- **Document event:** on every `RetainerInvoice` that becomes `paid` (fully or
  partly), and on every `PaymentReceived` with `advance_amount > 0` or
  `unused_amount > 0`.
- **Monthly, before GSTR-1:** advances received and not yet adjusted go into Table
  11A. Adjustments go into 11B.
- **Period:** month of receipt.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `RetainerInvoice.list` | `{"limit": 1000}` | 100 live. **The advance construct** |
| `PaymentReceived.list` | `{"limit": 1000}` | `advance_amount`, `unused_amount`, `payment_type` |
| `Party.get` | `{"id": customer_id}` | `gst_treatment` (SEZ → zero-rated) |
| `Item.get` | `{"id": …}` | `product_type` — goods vs services |

**RetainerInvoice fields — all of them** (live): `id`, `number`, `customer_id`,
`date`, `due_date`, `amount`, `payment_terms`, `description`, `reference_number`,
`payment_made`, `amount_applied`, `status` (`draft | sent | paid`), `balance`,
`allocation_history`, `allocation_history_version`, `company_id`, `docstatus`, audit
fields.

**Not present:** `items`, any tax field, any goods/services marker, any link to a
receipt voucher.

---

## 5. Algorithm

1. **Advances held:** for each `RetainerInvoice`, `held = payment_made −
   amount_applied`. If `held > 0`, an advance is sitting unadjusted.
2. Also include `PaymentReceived` with `unused_amount > 0` (on-account receipts).
3. **Goods or services?** No field on the retainer answers this. In order:
   - the customer's later invoices' `Item.product_type` (the dominant type);
   - `description` / `reference_number` text (weak);
   - default **services** (conservative: it assumes tax is due) and flag
     `supply_type_assumed`.
4. **Rate:** services at the rate the playbook assigns to the SAC. SEZ customer under
   LUT → 0%. Oracle: `POST /api/accounting/tax/compute {"amount": held, "rate": r}`.
   Advances are **tax-inclusive**, so `tax = held × r ÷ (100 + r)`.
5. **Was GST paid?** The platform cannot record GST on a retainer, so it cannot be
   verified. Emit `advance_gst_unverifiable` with the computed liability, and
   `advance_gst_zero_rated` for SEZ/LUT cases, where a receipt voucher is still needed.
6. When the final invoice applies the advance (`amount_applied` increases), the
   liability moves to the invoice, and the finding closes.

### Worked example (REAL — RET-2026-00002)

> **RET-2026-00002** (`9b44457c-5b13-40b6-8217-3f091fa8a2d5`), dated 2026-08-25,
> customer **Vardhman Aerospace SEZ Unit**, `amount ₹12,00,000`, `payment_made
> ₹6,00,000`, `amount_applied 0`, `balance ₹6,00,000`, `status: paid`.
>
> ```
> held       = 600,000 − 0 = ₹6,00,000   (received, not yet adjusted against any invoice)
> customer   = SEZ unit → zero-rated if under a valid LUT (UC-20: validity unverifiable)
> if services under LUT:    tax = 0, but a receipt voucher is required (Rule 50)
> if services, no LUT:      tax = 6,00,000 × 18/118 = ₹91,525.42 IGST due in Aug-2026 return
> if goods:                 no GST on advance (Notif 66/2017)
> ```
>
> Output: *"RET-2026-00002 — ₹6,00,000 advance from Vardhman Aerospace SEZ Unit held
> since 25 Aug, not yet adjusted. GST exposure ranges from ₹0 (goods, or services under
> a valid LUT) to ₹91,525.42 (services without LUT). The platform records neither the
> supply type nor the tax. Confirm both."*

---

## 6. Known-bad data

- **`RetainerInvoice` cannot carry tax** (no items, no tax fields). "Have we paid GST
  on advances?" can never be answered *yes* from platform data, only *computed*.
- **`PaymentReceived.payment_type` is `invoice_payment` on 215/215**, `advance_amount >
  0` on 0, and `unused_amount > 0` on 0. Step 2 contributes nothing live. The retainers
  are the only advances.
- **61 of 100 retainers are `draft`** and have received nothing. Only `payment_made > 0`
  matters.

---

## 7. Output contract

`rcm_undeclared_liability` (UC-03 §7 shape) with `rule ∈ {advance_gst_unverifiable,
advance_gst_zero_rated, supply_type_assumed}`, plus fields `held_amount`,
`received_date`, `assumed_rate`, `tax_if_services`, `tax_if_goods` (always 0).

---

## 8. Limits

- Cannot verify that GST was paid: the platform cannot record it. Reports the
  computed exposure as a **range** when the supply type is unknown.
- Cannot issue receipt or refund vouchers.
- Never applies advances to invoices.

---

## 9. Validation

1. **Live positive control:** RET-2026-00002 must produce one finding with held
   ₹6,00,000 and the ₹0 – ₹91,525.42 range.
2. **Tax-inclusive arithmetic:** ₹1,18,000 at 18% → tax ₹18,000 (fixture).
3. **Closure fixture:** an `amount_applied` increase to equal `payment_made` → finding
   closes.

---

## 10. Open questions

- **Is the retainer construct meant for services only?** If yes, step 3's default is
  right and certain. Ask the platform team, or read `RetainerInvoice` docs.
- **Where should receipt vouchers live?** No entity models them. That is a candidate
  platform gap, weaker than F18–F22 because a retainer is close.
- **Links to UC-20:** the same SEZ customer's LUT validity decides whether the answer is
  ₹0 or ₹91,525.42. The two findings should cross-reference each other.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-22 Advance receipt GST`.

**Call 1 — `RetainerInvoice.list {"limit":1000}`** → 100 retainers: draft 61 · sent 36 ·
paid 3. Σ `amount` on sent + paid: **₹1,16,44,198.63**. Record shape (RET-2026-00002):
```json
{"number":"RET-2026-00002","date":"2026-08-25","customer_id":"…","amount":1200000,
 "payment_made":600000,"amount_applied":0,"balance":600000,"status":"paid",
 "description":null,"reference_number":null}
```
No `items`, no tax field.

**Call 2 — `PaymentReceived.list {"limit":1000}`** → 215 receipts; `payment_type =
invoice_payment` on **215/215**; `advance_amount > 0` on **0**; `unused_amount > 0` on
**0**.

**What the live data changed:** `spec.md` said *"Data exists (`RetainerInvoice` is
exactly the advance construct)"*. The advance data exists; the tax data cannot. The
verdict stays 🟡, for a more specific reason.
