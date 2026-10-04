# UC-28 — Documents Entered Late into Filed or Locked Periods (Amendments)

**Domains: all five · Category: compliance calendar · Verdict: 🟢 Buildable — 0 findings on Suryodaya (the locks hold), which is the correct result**
**Status: draft · live evidence 2026-10-04 · US counterpart: [US-15](../US/us-15-late-entered-documents.md)**

The platform documents this gap itself. `not_yet_supported.gst_amendments` (GST-32) says there is *"no
amendment concept; a back-dated invoice into an already-filed period is accepted silently."* This use case
is the agent covering for that, so it is not a bug to file.

---

## 1. Question

> *"Has anyone entered or back-dated a document into a month we've already filed or closed?"*

---

## 2. Statutory basis

- **s.37(3) and s.39(9) CGST Act**: an error or omission in a filed GSTR-1 or GSTR-3B is corrected in a
  later return, but not after **30 November following the FY**, or the annual return date if earlier.
  *Our understanding (caveat):* GSTR-1A (Rule 59(4A), from August 2024) allows amending the current
  period's GSTR-1 before GSTR-3B.
- **s.31 + Rule 47**: a tax invoice is issued at the time of supply; for services, within **30 days**. A
  document dated well before it was created is either issued late or back-dated. Both breach s.31.
- **Consequence:**
  - A document missing from the filed return understates tax → interest under s.50 from the original due
    date.
  - Back-dating is an offence under s.122(1)(ii) where it is used to issue an invoice in violation of the
    Act.

---

## 3. Trigger

- **On event:** `invoice.created`, `bill.created`, `credit_note.created`, `vendor_credit.created`. When the
  document's date falls in a filed or locked period, this fires at once.
- **Scheduled daily** sweep, as a backstop for documents the watcher missed.
- **On request.**

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `GSTReturn.list` | `return_type`, `return_period`, `filing_status`, `filed_date` |
| `TransactionLock.list` | `module` (`sales\|purchases\|banking\|accountant\|all`), `lock_date`, `reason`, `created_at` |
| `AccountingPeriod.list` | `from_date`, `to_date`, `status` (`open\|closed`), `closed_at` |
| `Invoice/Bill/CreditNote/VendorCredit/PaymentMade/Expense.list` | `date`, `created_at`, `updated_at`, `status`, `number` |

`created_at` and `updated_at` are system fields on every record (confirmed live).

---

## 5. Algorithm

1. **Closed windows:**
   - **filed:** each `GSTReturn` with `filing_status = filed` → (period, `filed_date`, return type);
   - **locked:** each `TransactionLock` → (module scope, `lock_date`, lock `created_at`);
   - **closed:** each `AccountingPeriod` with `status = closed` → (from, to, `closed_at`).
2. **`entered_after_filing`:** a sales document (invoice, credit note) or purchase document (bill, vendor
   credit) dated inside a filed period with `created_at > filed_date`. It belongs in the next return or
   GSTR-1A, and interest runs from the original due date for any tax understated.
3. **`entered_into_locked_period`:** a document in the lock's module scope dated `≤ lock_date` and created
   after the lock existed. If the platform let it through, it is also a lock-enforcement defect.
4. **`entered_into_closed_period`:** the same test against closed accounting periods.
5. **`backdated_document`:** `created_at − date > 30 days` (the Rule 47 window), whatever the period
   status.
6. **`amendment_window_closing`:** amendments still needed for an FY whose 30-November window is within
   90 days.

### Worked example (REAL, 2026-10-04)

> Closed windows on Suryodaya:
> - GSTR-1 and GSTR-3B for 07-2026, filed 2026-08-08;
> - 9 transaction locks, among them `sales`, `purchases` and `banking` up to 2026-07-31, each with reason
>   "GSTR-1 and GSTR-3B filed for this period" or similar, all created 2026-09-12;
> - 16 closed months, April 2025 to July 2026, all closed on 2026-09-12.
>
> Documents dated inside any of these and created after the filing, lock or close: **0** across invoices,
> bills, credit notes, vendor credits, payments and expenses. Documents created more than 30 days after
> their date: **0**.
>
> Output: *"No document has been entered into a filed, locked or closed period. July 2026 returns are
> intact."*
>
> **There is a gap in the controls.** July was filed on 8 August, but the locks and closes were only applied
> on 12 September. For 35 days a July-dated document would have been accepted silently. The daily sweep
> covers that window; the platform doesn't (GST-32).

---

## 6. Known-bad data

- **6 of the 9 locks carry seeded product text as their `reason`** ("Vernier Caliper: batch 818 at
  Latur…") and odd dates (`all` ≤ 2025-10-31, `purchases` ≤ 2025-09-30). Use the dates; ignore the reasons.
- Locks have no "who" other than `locked_by`. `created_at` is the only proof of when a lock started.

---

## 7. Output contract

`finding_type: "period_integrity"`, `rule ∈ {entered_after_filing, entered_into_locked_period,
entered_into_closed_period, backdated_document, amendment_window_closing}`. Each row carries
`period_closed_by` (the return, lock or period id), `days_after_close`, and the tax on the document as
`total_exposure`.

---

## 8. Limits

- Never edits, moves or deletes a document, and never reopens a period.
- It can't see the portal. A return "filed" in AgentSwitch is assumed to match what was filed with GSTN.

---

## 9. Validation

1. **Live:** 0 findings, recomputed.
2. **Fixture:**
   - an invoice dated 2026-07-20 created 2026-08-09 with July filed 2026-08-08 → `entered_after_filing`;
   - the same invoice created 2026-08-07 → none.
3. **Lock fixture:** a bill dated on the lock date and created after the lock → `entered_into_locked_period`.

---

## 10. Open questions

- Does AgentSwitch *enforce* `TransactionLock`, or only record it? A test write would prove it, but the
  ledger is shared, so agree it with Teams 01/02 first.
- Should a filed return automatically create the lock? The 35-day gap above suggests filing and locking
  are separate manual steps.

---

## 11. Live evidence — actual calls, 2026-10-04

- `TransactionLock.list` → 9 rows. The first three, all with lock date 2026-07-31:
  - `7448e519-6230-4179-b52d-19d3051a5dce` (sales);
  - `8c6b2148-7564-4d40-af15-79e20080e175` (purchases);
  - `d2816c13-a835-4636-990b-5737f001dbbd` (banking).
- `AccountingPeriod.list` → 26 rows: 16 closed months (closed_at 2026-09-12T17:20Z), 8 open months, 2 open
  years.
- `GSTReturn.list` → July GSTR-1 and GSTR-3B filed 2026-08-08.
- Late-created document scan across Bill (281), Invoice (487), CreditNote (25), VendorCredit (100),
  PaymentMade (134) and Expense (120): **0**.
