# US-21 — Unclaimed Property (Escheat) on Vendor Payments

**US · Domains: all five · Verdict: 🟢 Buildable — 0 candidates on live data (the ledger starts January 2026 and every payment is a bank transfer), which is the correct result**
**IN counterpart:** none. India has no general escheat of vendor payables; the IEPF covers unpaid dividends only · **live evidence 2026-10-04**

---

## 1. Question

> *"Do we hold money owed to vendors that nobody has claimed, and must we report it to a state?"*

## 2. Statutory basis

- **State unclaimed property laws:** most are based on the Uniform Unclaimed Property Acts, the latest
  being the Revised Uniform Unclaimed Property Act (2016). A business holding money **owed to someone
  else** that stays unclaimed past a **dormancy period** must:
  - send due-diligence notices to the owner;
  - **report and remit** the money to the state.
- **AP property types:**
  - vendor payments **issued but never cashed** (checks), or **returned and never reissued** (ACH);
  - refunds or credit balances **owed to** vendors.
  Vendor credits owed *to us* are not included ([US-17](us-17-unapplied-vendor-credits.md) §2).
- **Which state:** *Texas v. New Jersey* (1965) sets the priority:
  1. the owner's last known address state;
  2. if unknown, the holder's state of incorporation or formation.
- *Our understanding, per-state table in the rulebook (caveat):* dormancy for vendor payments is
  typically **3–5 years**, and annual report dates differ (e.g. Ohio, Pennsylvania, Michigan and Illinois
  each have their own deadline and cut-off date). Ohio's law is R.C. Chapter 169; the others are in the
  table with citations.
- **Consequence:** unreported property → interest and penalties, and in an audit, **estimation** of
  liability for years without records.

## 3. Trigger

- **Scheduled monthly:** age outstanding items.
- **Scheduled annually**, ahead of each state's report date: produce the due-diligence list (items
  reaching dormancy within 120 days) and the report list.
- **On request.**

## 4. Input contract

| Call | Fields |
|---|---|
| `PaymentMade.list` | `date`, `amount`, `payment_mode` (`cheque` matters most), `status`, `vendor_id`, `reference_number` |
| `BankTransaction.list` | `matched_voucher_type = PaymentMade`, `matched_voucher_id`, `date`: proof that a payment **cleared** |
| `Party.get` | `addresses[]` (last known state), contact details for due diligence |
| `OrgProfile.list` | `state` (the holder's location). Formation state isn't modelled → overrides |
| Rulebook | `us/tables/unclaimed_property.yaml`: state → dormancy (years), report date, cut-off date, due-diligence window |

## 5. Algorithm

1. **Outstanding payments:** `PaymentMade` with no clearing bank debit (US-19 matching), past a
   clearing grace period (default 60 days). Cheques and returned ACH first.
2. **Owner state:** the vendor's address state; if missing, the holder's formation state (overrides).
3. **Dormancy:** `today − payment date` against the state's dormancy period.
   - `escheat_due_diligence`: within 120 days of dormancy.
   - `escheat_reportable`: past dormancy, with the next report date.
4. **Refunds owed to vendors:** vendor overpayments to us or duplicate receipts (when modelled) feed the
   same ageing.
5. **`escheat_owner_state_unknown`:** no vendor address and no formation state on file.

### Worked example

> **Live:**
> - 67 vendor payments (2026-01-18 … 2026-08-31), all **bank transfer**, all `paid`, so there are no
>   uncashed cheques.
> - 0 vendor refunds owed.
> - The oldest payment is under a year old, and dormancy is at least 3 years.
> → **0 candidates**; the earliest any item could become reportable is 2029.
> - All 8 vendors have Ohio addresses, so the owner state is known.
>
> **Constructed:** a $4,200 cheque to a Michigan vendor issued 2026-02-10 never clears. If Michigan's
> dormancy for vendor checks is 3 years, it becomes dormant on 2029-02-10. Due diligence goes out
> ~2028-10, and it is reported with Michigan's next annual report.

## 6. Known-bad data

- `PaymentMade.paid_through` is null on all payments, so the clearing account is unknown. Clearing is
  inferred from bank matching across all accounts (US-19), and the bank feed covers only June–August 2026.
  An item outside the feed window is "unknown", **not** outstanding.

## 7. Output contract

`finding_type: "unclaimed_property"`, `rule ∈ {escheat_due_diligence, escheat_reportable,
escheat_owner_state_unknown}`. Fields: `payment_id`, `owner_state`, `dormant_on`, `report_due`, `amount`.

## 8. Limits

- Never contacts owners, files a report or remits. It produces the due-diligence and report lists.
- Customer credit balances and unidentified receipts are receivable-side (Team 02) and out of scope.

## 9. Validation

1. **Live:** 0 candidates (above), recomputed.
2. **Fixture:** an uncleared cheque 3 years and 1 day old, owner in a 3-year state → `escheat_reportable`;
   2 years 9 months → `escheat_due_diligence`.
3. **Fixture:** no vendor address and no formation state → `escheat_owner_state_unknown`.

## 10. Open questions

- What is Keystone Precision Works LLC's **state of formation**? It isn't modelled, and is needed as the
  fallback owner state.
- Should "returned ACH" be a payment status? `PaymentMade.status` shows only `paid` today.

## 11. Live evidence — actual calls, 2026-10-04

- `PaymentMade.list {"limit":1000}` → 67: `payment_mode: bank_transfer` ×67, `status: paid` ×67, dated
  2026-01-18 … 2026-08-31.
- `VendorCredit.list` → 0.
- `Party.list` → 8 vendors used, addresses OH ×8.
- `OrgProfile.list` → `state: OH`.
