# UC-19 — Credit-Note Time-Limit Monitoring (s.34(2))

**Workstream C · Owner: Sandip · Verdict: 🟢 Buildable**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Which returns can we still issue a tax-effective credit note for?"*

(Verbatim from `spec.md` UC-19.)

---

## 2. Statutory basis

- **Section 34(1), CGST Act** — a supplier may issue a credit note where the taxable
  value or tax charged exceeds what is payable, or goods are returned, or services are
  deficient.
- **Section 34(2)** — the credit note reduces the supplier's output tax **only if
  declared in a return for a month no later than 30 November following the end of the
  FY** in which the original supply was made, **or the date of furnishing the annual
  return, whichever is earlier** (the 30 November date is from the Finance Act 2022
  amendment; previously September).
- **Proviso** — no reduction if the incidence of tax has been passed on to another
  person. The recipient must also reverse the corresponding ITC.
- **Consequence if missed:** a commercial credit note issued after the window still
  reduces what the customer owes, but the supplier **does not get its GST back**. The
  tax is lost.

---

## 3. Trigger

- **Scheduled monthly from August to November** — the window for the previous FY's
  invoices closes on 30 November.
- **On document event:** when a `CreditNote` is created, check its original invoice's
  FY against the window.
- **Period:** per original invoice's FY.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `CreditNote.list` | `{"limit": 1000}` | 25 live |
| `Invoice.list` | `{"limit": 1000}` | **Both directions** — see §6: some credit notes link to *payable* invoices |
| `Invoice.get` | `{"id": invoice_id}` | Original invoice date |

**CreditNote fields** (confirmed live): `id`, `number`, `credit_note_number`, `date`,
`invoice_id`, `customer_id`, `reason`, `items`, `taxable_value`, `total_tax`,
`grand_total`, `status`, `reference_number`. **Do not use `taxes[]`** (N128).

---

## 5. Algorithm

1. **FY of a date:** `fy_end(d) = 31 March of year(d)` if `month(d) ≤ 3`, else
   `31 March of year(d)+1`.
2. **Window close:** `cutoff(invoice) = 30 November of year(fy_end(invoice.date))`,
   or the annual-return filing date if known and earlier.
3. **Existing credit notes:** for each CN, if `cn.date > cutoff(original)` →
   `credit_note_out_of_window`: the GST on it is not recoverable.
4. **Forward-looking (the real question):** for each receivable invoice whose FY window
   is still open, `days_left = cutoff − today`. When `days_left ≤ 90`, list the invoices
   still eligible, with a count and value, so disputes can be settled before the window
   shuts.
5. **Tax effect** of each CN: item-level tax from `CreditNote.items[]`, with Rule 0
   applied.

### Worked example (REAL — the FY 2025-26 window)

> Today 2026-09-28. Invoices dated 2025-04-01 … 2026-03-31 belong to FY 2025-26;
> `cutoff = 2026-11-30` → **63 days left**.
> Receivable invoices in FY 2025-26: **125**.
>
> Existing CN: **CN-2026-00023** (`f7aa6705-2703-4403-ba36-926197945859`), dated
> 2026-09-12, against **INV-2026-00009** dated 2026-01-13 (FY 2025-26), taxable value
> ₹19,70,472.94.
> ```
> cutoff(INV-2026-00009) = 2026-11-30;   2026-09-12 ≤ cutoff → within window ✓
> ```
>
> Output: *"63 days remain to issue tax-effective credit notes against 125 FY 2025-26
> invoices. All 25 existing credit notes are within their windows."*

---

## 6. Known-bad data

- **12 of 25 credit notes link to *payable* invoices** (`PINV-…`). A credit note we
  issue against a purchase invoice is the wrong document: that is a debit note from us,
  or a credit note *from* the vendor. `Invoice.list` must be fetched in both directions
  to resolve these links, and each one is emitted as `classification_conflict`.
- **`CreditNote.taxes[]` is corrupt** (N128: 0% lines carrying tax, amounts 9× the
  base). Item-level only, with Rule 0.
- **All 25 CNs are dated 2026-08-22 … 2026-09-12** (seed clustering). The window logic
  is exercised, but not near its boundary.

---

## 7. Output contract

`finding_type: "credit_note_window"`, `rule ∈ {credit_note_out_of_window,
window_closing, classification_conflict}`. The window-closing row is an aggregate:

```json
{
  "finding_type": "credit_note_window",
  "rule": "window_closing",
  "fy": "2025-26",
  "cutoff": "2026-11-30",
  "days_left": 63,
  "eligible_invoice_count": 125,
  "existing_credit_notes_in_window": 25,
  "status": "finding",
  "summary": "63 days left to issue tax-effective credit notes against 125 FY 2025-26 invoices."
}
```

---

## 8. Limits

- Does not know the annual-return filing date. It uses 30 November and states that the
  earlier date may apply.
- Does not decide whether a credit note is *warranted*. It says only whether it would
  be *tax-effective*.
- Never creates credit notes.

---

## 9. Validation

1. **Live:** 25 CNs → 0 `out_of_window`; 12 `classification_conflict` (payable links).
2. **Boundary fixture:** invoice 2025-06-01; CN 2026-11-30 → within; CN 2026-12-01 →
   out.
3. **FY-boundary fixture:** invoice 2026-03-31 → cutoff 2026-11-30; invoice 2026-04-01
   → cutoff 2027-11-30.

---

## 10. Open questions

- **Payable-linked CNs:** data error, or does the platform use `CreditNote` for both
  directions? If the latter, the spec must split by the linked invoice's `direction`
  instead of flagging.
- **Annual-return date** — should the playbook carry the tenant's GSTR-9 filing date
  once filed?

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-19 Credit note time limit`.

**Call 1 — `CreditNote.list {"limit":1000}`** → 25 credit notes, all with `invoice_id`.

**Call 2 — `Invoice.list {"limit":1000}`** (both directions) → every CN's original
resolved. All 25 within window. Samples:

| CN | CN date | Original | Orig. date | FY cutoff | Within |
|---|---|---|---|---|---|
| CN-2026-00023 `f7aa6705…` | 2026-09-12 | INV-2026-00009 | 2026-01-13 | 2026-11-30 | ✓ |
| CN-2026-00025 `d21b5977…` | 2026-09-12 | **PINV**-2025-00042 | 2025-12-22 | 2026-11-30 | ✓ (payable link) |
| CN-2026-00004 `b7aea2d3…` | 2026-08-27 | INV-2025-00055 | 2025-12-14 | 2026-11-30 | ✓ |
| CN-2026-00022 `08749498…` | 2026-09-12 | INV-2026-00175 | 2026-09-10 | 2027-11-30 | ✓ |

CNs linked to `PINV-…` (payable) invoices: **12** — CN-2026-00025, 00024, 00021, 00019,
00018, 00016, 00015, 00013, 00012, 00008, 00006, 00005.

Receivable invoices in FY 2025-26: **125** → window closes **2026-11-30, 63 days from
the snapshot**.
