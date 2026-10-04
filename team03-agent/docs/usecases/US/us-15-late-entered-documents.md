# US-15 — Documents Entered Late into Past Periods (US instance of UC-28)

**US · Domains: all five · Verdict: 🟢 Buildable — live findings (147 invoices entered on 16 September for January–August; no period has ever been closed)**
**IN spec (algorithm, output contract):** [`../IN/uc-28-late-entered-documents.md`](../IN/uc-28-late-entered-documents.md) · **live evidence 2026-10-04**

---

The algorithm is UC-28's, with a `tax_regimes: [all]` manifest. Sections 1, 3, 5 and 7 are as UC-28. This
file records what differs for the US tenant: there are no filed-return records, no transaction locks and
no closed periods. The US live evidence is below.

## 2. Statutory basis (US)

- A sale belongs to the **sales tax return for the period in which it occurred** (accrual basis, US
  README). A sale recorded after that return was filed needs an **amended return**, or a prior-period
  adjustment where the state allows one, with interest from the original due date.
- **Control:** period close. Without it, any back-dated entry changes historical figures silently. That
  is internal control over financial reporting (SOX §404 for issuers; Keystone is a private LLC, so
  auditor and lender expectations apply instead).

## 4. Input contract (US differences)

| UC-28 source | On Keystone |
|---|---|
| `GSTReturn` (filed periods) | ❌ No equivalent. Filed periods are unknown ([US-14](us-14-sales-tax-filing-calendar.md) §10) |
| `TransactionLock` | 0 rows |
| `AccountingPeriod` closed | **0 closed**: 12 monthly periods and 1 year, all `open` |

So on this tenant the test becomes **`backdated_document`** (created more than 30 days after its date),
plus **`entered_into_reported_period`**: the document's date falls in a period whose return due date has
passed (US-14 calendar). A return was *probably* filed for that period, and the row says that.

## 6. Known-bad data (US)

- **Bulk back-entry on 2026-09-16:** these documents were all created that day with dates from January to
  August. This is probably seeding, but it is exactly the pattern the check exists for.
  - 147 invoices
  - 77 bills
  - 66 payments
  - 68 expenses
- No locks and no closed periods, so nothing on the platform would have stopped it.

## 8. Limits (US)

As UC-28. It can't know whether the January–August Ohio returns were filed, or what they contained.

## 9. Validation (US)

1. **Live:** 147 invoices created 2026-09-16 dated 2026-01 … 2026-08, carrying **$220,089.85** of tax on
   $4,300,869.71 of sales.
2. If the Ohio monthly returns for January–August were filed on time, that tax was **not on them**:
   amended returns are needed for every month.

## 10. Open questions (US)

- Were the January–August returns filed, and from what figures? No record exists in AgentSwitch.
- Should US month-end close (`AccountingPeriod` → closed) be recommended to the Keystone operators?
  Nothing has been closed in 2026.

## 11. Live evidence — actual calls, 2026-10-04

- `Invoice.list {"limit":1000}` → 158 invoices; **147** created on 2026-09-16 with dates more than 31 days
  earlier:

  | Month dated | Invoices | Tax |
  |---|---|---|
  | 2026-01 | 5 | $3,720.86 |
  | 2026-02 | 19 | $26,680.66 |
  | 2026-03 | 21 | $51,230.58 |
  | 2026-04 | 21 | $15,063.06 |
  | 2026-05 | 22 | $28,523.12 |
  | 2026-06 | 23 | $42,729.42 |
  | 2026-07 | 28 | $42,882.62 |
  | 2026-08 | 8 | $9,259.53 |
  | **Total** | **147** | **$220,089.85** |

  Examples: INV-2026-00152 (`c93b7e8e-95f6-4b72-bab5-8dca00a6af7e`, dated 2026-04-28) and INV-2026-00151
  (`143cc333-491b-4c93-8b66-450ce894b24c`, dated 2026-06-10).
- `Bill.list` → 77 created 2026-09-16 (e.g. BILL-2026-00079, dated 2026-08-06).
- `PaymentMade.list` → 66; `Expense.list` → 68 (e.g. EXP-2026-00161, dated 2026-08-14).
- `AccountingPeriod.list` → 13 rows, all `open`. `TransactionLock.list` → 0 rows.
