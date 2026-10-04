# UC-41 — Unapplied Vendor Credits and Advances Before Payment

**Domains: all five · Category: AP control · Verdict: 🟢 Buildable — live findings**
**Status: draft · live evidence 2026-10-04 · US counterpart: [US-17](../US/us-17-unapplied-vendor-credits.md)**

[UC-25](uc-25-vendor-credit-debit-notes-itc.md) handles the **tax** effect of a supplier's credit note.
This use case handles the **cash** effect: the money is ours, and it should come off the next payment to
that vendor before anything else is paid.

---

## 1. Question

> *"Are we about to pay vendors in full while they owe us money from credit notes or advances?"*

---

## 2. Basis

- **Commercial, not statutory.** An open vendor credit or unused advance is a receivable from the vendor.
  Paying their open bills in full while it sits unapplied is overpayment, and it often goes unrecovered
  when the vendor relationship ends.
- **Tax tie-ins:**
  - Applying a credit reduces what is unpaid, which changes the **Rule 37** 180-day exposure ([UC-01](uc-01-rule-37-itc-reversal.md))
    and the **MSME 45-day** exposure ([UC-04](uc-04-msme-45-day-exposure.md)).
  - An **advance paid** for services can carry RCM or TDS obligations at the time of payment (UC-03/UC-09).
- **Reporting:** *our understanding (caveat):* under Schedule III, trade payables are shown net, and debit
  balances with vendors are presented as other assets, so long-unapplied credits misstate both.

---

## 3. Trigger

- **On event:** `bill.approval_status_changed → approved`, and before a payment run ([UC-42](uc-42-payment-run-prioritisation.md)),
  when the vendor has an open credit or unused advance.
- **On event:** `vendor_credit.created`, when that vendor has open bills.
- **Scheduled weekly:** an ageing sweep of all open credits and advances.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `VendorCredit.list` | `status` (`draft/open/closed`), `vendor_id`, `date`, `balance`, `grand_total`, `allocation_history[]` |
| `Bill.list` | `vendor_id`, `status`, `balance_due`, `due_date` |
| `PaymentMade.list` | `payment_type` (`regular\|advance\|refund`), `unused_amount`, `vendor_id`, `date` |

---

## 5. Algorithm

1. **Open credits:** `status = open`, `balance > 0`. **Unused advances:** `PaymentMade.unused_amount > 0`,
   or `payment_type = advance`. Ignore residues below ₹1 (rounding) as context.
2. **`credit_applicable_now`:** the vendor has open bills. Amount applicable = `min(open credit, open bills
   balance)`. Rank by that amount.
3. **`credit_before_payment`:** an event variant. A bill of that vendor is approved, or in the payment run,
   while a credit is open → apply the credit first.
4. **`stale_credit`:** open credit older than 90 days with no open bills to apply it against → ask the
   vendor for a refund.
5. **`advance_unadjusted`:** advance older than 90 days not set against a bill.
6. **Knock-ons:** recompute UC-01/UC-04 exposure as if applicable credits were applied, and report the
   difference.

### Worked example (REAL, 2026-10-04)

> **Open credits:** 71 credits across 53 vendors, **₹39,83,502.62**. By age: 22 under 30 days, 48 at
> 30–59 days, 1 at 60–89 days.
>
> **Vendors with open credits and open bills: 7. Applicable now: ₹4,91,099.27.**
>
> | Vendor | Open credit | Open bills | Of which overdue |
> |---|---|---|---|
> | Jindal Steel Depot | ₹3,17,137.59 | ₹34,35,771.00 | ₹22,29,950.00 |
> | Tata Ficosa Automotive Systems | ₹68,881.00 | ₹1,91,081.01 | ₹1,91,081.01 |
> | Godrej Material Handling | ₹62,200.00 | ₹1,45,140.00 | — |
> | Chakan Transport Lines | ₹14,786.00 | ₹1,94,936.00 | ₹69,384.00 |
> | Shreeji Powder Coating | ₹11,894.00 | ₹21,48,781.05 | ₹6,92,787.69 |
> | Kirloskar Pumps Ltd | ₹9,655.68 | ₹2,41,964.57 | ₹65,268.44 |
> | Bharat EV Motors Ltd | ₹6,545.00 | ₹10,92,460.98 | ₹6,06,633.67 |
>
> Jindal's credits are VC-2026-00001 (`de278efa-1a20-471a-be1e-fce6c216d444`, ₹1,12,548.00) and
> VC-2026-00099 (`91fcf6a9-8922-4189-a90f-710ceecb8f2e`, ₹2,04,589.59).
>
> The other 46 vendors with open credits have no open bills. Those credits (₹34,92,403.35) can only be
> recovered as refunds, and they become `stale_credit` after 90 days.
>
> **Advances:** none (`payment_type = advance` on 0 payments). Unused amounts on 26 payments total ₹6.70,
> which is rounding.
>
> Output: *"Apply ₹4.91 lakh of open vendor credits before paying 7 vendors (Jindal Steel ₹3.17 lakh).
> Another ₹34.92 lakh of credits sits with vendors we no longer owe."*

---

## 6. Known-bad data

- Credits are dated from 2026-04-23, before the first bill (2026-06-07). Some credits refer to purchases
  outside the ledger, which is one reason 46 vendors have credits but no bills.
- `VendorCredit.taxes[]` is partly corrupt (UC-25 §6), but this use case reads only `balance`, which is
  unaffected.

---

## 7. Output contract

`finding_type: "vendor_balance"`, `rule ∈ {credit_applicable_now, credit_before_payment, stale_credit,
advance_unadjusted}`. Fields: `vendor_id`, `open_credit`, `open_bills`, `applicable_amount`,
`oldest_credit_days`, plus the UC-01/UC-04 exposure change.

---

## 8. Limits

- Never applies a credit or records a refund (`VendorCredit` writes are T3, never registered). It
  recommends; a human applies.
- Doesn't decide disputed credits. A credit under dispute is marked in overrides and excluded.

---

## 9. Validation

1. **Live:** recompute the 7-vendor table and the ₹4,91,099.27 applicable total.
2. **Fixtures:**
   - credit 100, open bills 60 → applicable 60;
   - credit 100 with no bills and 91 days old → `stale_credit`.

---

## 10. Open questions

- What does `allocation_history[]` record when a credit is applied: is it the evidence of application?
  Every sampled credit shows only a `posted` event.
- Should application be suggested per bill (oldest first, or MSME first)? Recommend MSME first, then
  oldest, to reduce statutory exposure fastest.

---

## 11. Live evidence — actual calls, 2026-10-04

- `VendorCredit.list {"limit":1000}` → 100: open 71 (balance ₹39,83,502.62), draft 26, closed 3.
- `Bill.list {"limit":1000}` → 100 open bills, balance ₹1,41,27,710.13.
- `PaymentMade.list {"limit":1000}` → 134, all `payment_type: regular`, `unused_amount > 0` on 26 (total
  ₹6.70).
