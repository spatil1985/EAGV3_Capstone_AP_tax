# UC-43 — Bank-to-Payables Reconciliation: Vendor Money Out That AP Doesn't Know About

**Domains: all five · Category: AP control · Verdict: 🟢 Buildable — live findings (bank and AP don't reconcile at all)**
**Status: draft · live evidence 2026-10-04 · US counterpart: [US-19](../US/us-19-bank-to-payables-reconciliation.md)**

[UC-05](uc-05-duplicate-vendor-payment.md) asks whether a vendor is being paid twice **inside AP**. This
use case asks the question from the bank side:
- money left the bank to a vendor but AP never recorded the payment, so the bill stays open and gets paid
  again;
- or AP recorded a payment that never left the bank, so the vendor is unpaid and the MSME and Rule 37
  clocks are still running.

---

## 1. Question

> *"Does every vendor payment in the bank match a payment in our books, and the other way round?"*

---

## 2. Basis

- **Control, not statute:** bank reconciliation is the primary detective control over cash
  disbursements.
- **Tax tie-ins:**
  - An unrecorded payment leaves a bill "unpaid" in AP. UC-01 (Rule 37) and UC-04 (MSME) then report
    false exposure.
  - A recorded but unbanked payment makes those exposures **real** while AP shows them cured.
  - TDS deducted at payment (UC-09) depends on the payment being recorded.

---

## 3. Trigger

- **On event:** `bank_transaction.created` (debit) through the watcher, with `BankTransaction` added to
  its entities.
- **Scheduled weekly**, and at month-end before close.
- **On request.**

---

## 4. Input contract

| Tool | Fields (confirmed live) |
|---|---|
| `BankTransaction.list` | `date`, `amount`, `type` (`credit\|debit`), `payee`, `description`, `reference`, `categorization_status` (`uncategorized\|categorized\|matched\|excluded`), `matched_voucher_type`, `matched_voucher_id`, `bank_account_id` |
| `BankAccount.list` | `account_name`, `account_type` (`current\|savings\|credit_card\|cash`), `is_active` |
| `PaymentMade.list` | `vendor_id`, `date`, `amount`, `payment_mode`, `reference_number`, `bank_reference_number`, `paid_through` |
| `Party.list` | Vendor names, for matching `payee` |

---

## 5. Algorithm

1. **Window:** from the earliest to the latest bank transaction date, per bank account.
2. **Match** each bank debit to a `PaymentMade`:
   - first by `matched_voucher_id` when `matched_voucher_type = PaymentMade`;
   - otherwise by bank or reference number;
   - otherwise by normalised `payee` = vendor name, equal amount (±₹1), and date within ±5 days.
3. **`bank_debit_unrecorded`:** a debit whose payee is a vendor, with no matching payment. Exposure =
   amount. Then check the vendor's open bills of the same amount, which are at risk of a second payment.
4. **`payment_not_in_bank`:** a payment inside the window with no matching debit on any account it could
   come from.
5. **`match_without_voucher`:** `categorization_status = matched` but `matched_voucher_type` /
   `matched_voucher_id` null. The bank says matched, but to nothing (`data_quality`).
6. **`unidentified_debit`:** no payee, uncategorised, older than 7 days → ask treasury.

### Worked example (REAL: Suryodaya, bank window 2026-03-18 … 2026-09-11)

> **Bank side:** 21 debits, ₹56,25,320.00, all on "ICICI Current A/c — Chakan". **20 have a vendor payee
> and no matching payment in AP: ₹56,20,600.00.** For example:
>
> | Bank txn | Date | Amount | Payee | Status |
> |---|---|---|---|---|
> | `f2cfd103-0127-4c04-9cb1-0fe3e2fd5485` | 2026-09-05 | ₹5,12,400.00 | Suvarna Electricals | categorized |
> | `368e9906-f1ef-486c-8635-3298fad31f0b` | 2026-08-18 | ₹5,12,400.00 | Precision Fasteners Co | categorized |
> | `bd044f6c-72d3-48e5-b876-88261177082b` | 2026-08-09 | ₹3,85,000.00 | Jindal Steel Depot | uncategorized |
> | `1960d843-869e-4395-9138-7d2a8a75fe05` | 2026-07-22 | ₹2,43,000.00 | Chakan Transport Lines | uncategorized |
>
> **AP side:** **77 recorded payments inside the window (₹1,36,47,550.08) have no matching debit.**
> `paid_through` is null on all of them, so the account the money left from is unknown.
>
> **Bank status:** 14 debits say `matched` with no voucher type or id.
>
> Output: *"Bank and payables don't reconcile: ₹56.21 lakh left the bank to 20 vendors with no payment in
> AP (those bills may be paid again), and ₹1.36 crore of AP payments never appear in the bank."*

---

## 6. Known-bad data

- **`matched` without a voucher** on 14 of 21 debits. On the US tenant, the same field carries
  `PaymentMade` / `Expense` / `JournalEntry` with ids, so the India data is defective. Candidate bug
  report.
- `PaymentMade.paid_through` is null on every payment, so payments can't be attributed to a bank account.
  Matching runs across all active accounts.
- The bank feed may be partial (21 debits over six months for a company with 134 payments). The summary
  states the window and the counts, not a verdict on the business.

---

## 7. Output contract

`finding_type: "bank_reconciliation"`, `rule ∈ {bank_debit_unrecorded, payment_not_in_bank,
match_without_voucher, unidentified_debit}`. Fields: `bank_transaction_id` / `payment_id`, `amount`,
`counterparty`, `match_attempts` (which keys were tried), and `open_bills_same_amount` (the double-payment
risk).

---

## 8. Limits

- Never categorises, matches or excludes a bank transaction, and never records a payment.
- It can't see bank statements beyond what the feed loaded into `BankTransaction`.

---

## 9. Validation

1. **Live:** 20 / ₹56,20,600.00 and 77 / ₹1,36,47,550.08, recomputed.
2. **Fixtures:**
   - debit ₹10,000 to "Acme Ltd" with a payment ₹10,000 to Acme 3 days earlier → matched;
   - 6 days earlier → `bank_debit_unrecorded` plus `payment_not_in_bank`.

---

## 10. Open questions

- Is the India bank feed seeded independently of AP? The amounts repeat (₹5,12,400 twice, ₹64,800 twice,
  ₹1,18,600 twice), which suggests templates.
- Should a match by amount and date alone (no payee) count? Recommend it only as `possible_match`, never
  as a clean match.

---

## 11. Live evidence — actual calls, 2026-10-04

- `BankTransaction.list` → 62 rows: 41 credits, 21 debits.
  - Categorization of the debits: matched 14 (voucher null), uncategorized 4, categorized 3.
- `BankAccount.list` → 3 accounts: Petty Cash — Plant (cash), HDFC Cash Credit, ICICI Current — Chakan.
- `PaymentMade.list` → 134 (dated 2025-11-11 … 2026-08-22); 77 inside the bank window; `paid_through`
  null on all.
