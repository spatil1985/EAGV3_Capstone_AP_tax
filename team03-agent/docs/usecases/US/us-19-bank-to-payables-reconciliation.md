# US-19 — Bank-to-Payables Reconciliation (US instance of UC-43)

**US · Domains: all five · Verdict: 🟢 Buildable — live findings (6 of 9 payments in the bank window have no matching debit)**
**IN spec (algorithm, output contract):** [`../IN/uc-43-bank-to-payables-reconciliation.md`](../IN/uc-43-bank-to-payables-reconciliation.md) · **live evidence 2026-10-04**

---

Regime-agnostic. Sections 1, 2, 3, 5 and 7 are as UC-43. On Keystone the matching runs mostly on voucher
links, because bank debits carry no payee.

## 4. Input contract (US differences)

- `BankTransaction.matched_voucher_type` / `matched_voucher_id` **are populated** here (`PaymentMade`,
  `Expense`, `JournalEntry`). Unlike India, the platform's own matches can be trusted and followed.
- `BankTransaction.payee` is **null on every debit**. UC-43's payee-name key can't run, so unmatched
  debits fall back to amount + date (`possible_match` only).

## 6. Known-bad data (US)

- No payee on bank debits (above).
- The bank feed covers only 2026-06-30 … 2026-08-31, while payments run from 2026-01-18. The
  reconciliation is limited to the window, and the summary says so.

## 9. Validation (US)

1. **Live:** 20 debits in the window, **$373,780.31**, on Chase Business Checking (19) and Savings (1).
   - Matched by voucher: `PaymentMade` 3, `Expense` 7, `JournalEntry` 3.
   - Categorized but unlinked: 4. Uncategorized: 3.
2. **Live:** 9 `PaymentMade` in the window ($57,000.00); **6 have no matching debit ($45,825.00)**:
   - POUT-2026-00066 (2026-07-29, $8,250.00);
   - POUT-2026-00065 (2026-07-13, $6,750.00);
   - POUT-2026-00064 (2026-07-10, $6,750.00);
   - POUT-2026-00053 (2026-07-26, $11,000.00);
   - POUT-2026-00052 (2026-07-05, $10,000.00);
   - one more.
3. **Unidentified:** `be42052d-706d-4eea-aece-174ac4044a21`, 2026-08-06, **$3,000.00**, uncategorized, no
   payee, no voucher → `unidentified_debit`.

## 10. Open questions (US)

- Were the 6 unmatched payments made from an account not in the feed (the Chase Ink card), or not made?
  `PaymentMade.paid_through` is null on all 9.

## 11. Live evidence — actual calls, 2026-10-04

- `BankTransaction.list` → 46: 26 credits, 20 debits. Categorization: matched 35, categorized 7,
  uncategorized 4.
  - Example voucher link: `3e589d49-3534-4d64-8ea5-aef65c3da3b0` (2026-08-08, $1,950.00) →
    `PaymentMade` `ebac3cb9-963c-4f82-9719-ac1954e23d9f`.
- `BankAccount.list` → Shop Petty Cash (cash), Chase Ink Business Card …9021 (credit card), Chase Business
  Savings …7730, Chase Business Checking …4417.
- `PaymentMade.list` → 67 (2026-01-18 … 2026-08-31), `payment_mode: bank_transfer` ×67.
