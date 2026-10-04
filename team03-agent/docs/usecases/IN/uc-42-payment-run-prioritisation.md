# UC-42 — Payment Run Prioritisation (Pay-By Plan from Statutory Deadlines)

**Domains: all five · Category: AP control · Verdict: 🟢 Buildable — live data**
**Status: draft · live evidence 2026-10-04 · US counterpart: [US-18](../US/us-18-payment-run-prioritisation.md)**

Several use cases each say "this bill is costing you money": UC-01, UC-04, UC-05, UC-24, UC-38 and
UC-41. A finance user with limited cash needs **one ranked list**: what to pay this week, what to hold, and
what to net off first.

---

## 1. Question

> *"We can't pay everything this week. Which bills should we pay first to avoid penalties and lost credit, and which should we hold?"*

---

## 2. Basis: the cost of paying late, by source

| Source | Cost of delay | Spec |
|---|---|---|
| MSME vendor past 45 days | Penal interest at **3× RBI bank rate**, compounding monthly (MSMED s.16); the expense is **disallowed** until paid (s.43B(h)) | [UC-04](uc-04-msme-45-day-exposure.md) |
| Bill approaching **180 days** unpaid | The credit taken must be reversed, with 18% interest (Rule 37) | [UC-01](uc-01-rule-37-itc-reversal.md) |
| Contractual due date | Late fee or interest per the vendor's terms (`payment_terms`) | — |
| Early-payment discount | Lost discount (terms such as 2/10 net 30) | — |

**Reasons to hold or adjust instead of paying:**
- suspected duplicate ([UC-05](uc-05-duplicate-vendor-payment.md));
- IMS-rejected or disputed invoice ([UC-24](uc-24-unclaimed-itc-ims-2b.md));
- vendor master unverifiable ([UC-40](uc-40-vendor-master-audit.md));
- open vendor credit to apply first ([UC-41](uc-41-unapplied-vendor-credits.md));
- payment planned in cash above the limit ([UC-38](uc-38-cash-payment-limits.md));
- TDS to deduct at payment ([UC-09](uc-09-vendor-tds-verification.md), [UC-39](uc-39-tds-deductor-setup.md)).

---

## 3. Trigger

- **Scheduled weekly**, before the usual payment day (configurable, default Thursday 09:00 IST).
- **On request** with a cash budget: *"I have ₹40 lakh this week: what should I pay?"*
- **On event:** an MSME bill reaching day 40 or a bill reaching day 170 pulls it into the next run
  (reusing UC-04/UC-01 thresholds).

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Bill.list` | `status`, `date`, `due_date`, `payment_terms`, `balance_due`, `vendor_id`, `payment_gateway`, `ims_status`, `itc_eligibility`, `approval_status` |
| `Party.get` | `is_msme`, `msme_no` |
| Outputs of UC-01, UC-04, UC-05, UC-24, UC-38, UC-40, UC-41 | Exposure and hold flags per bill |
| Rulebook | RBI bank rate (refreshed, UC-04), weekly cash budget (optional) |

---

## 5. Algorithm

1. **Population:** open bills with `balance_due > 0`.
2. **Holds** (removed from the pay list, each with its reason): a duplicate candidate, IMS `reject`,
   approval `pending_approval`/`rejected`, or a vendor master critical failure.
3. **Net off:** reduce each vendor's payable by applicable open credits (UC-41).
4. **Score each remaining bill** by **cost of one more week's delay**:
   - **MSME:** past 45 days → penal interest for 7 days, plus the 43B(h) disallowance risk if the FY end
     falls before payment; within 7 days of day 45 → the same, counted from day 45.
   - **Rule 37:** within 14 days of day 180 → the credit on the bill (full reversal), plus interest.
   - **Contractual:** past or within 7 days of `due_date` → a nominal rate from the rulebook.
   - Otherwise 0.
5. **Rank** by score, then by `due_date`. Under a cash budget, fill greedily by score per rupee.
6. **Annotate** each line with TDS to deduct, the payment mode to use (never cash above the limit), and
   the credit applied.
7. **Output:** a pay-by plan (pay now / pay by date / hold) and the exposure avoided if followed.

### Worked example (REAL, 2026-10-04)

> **Open bills:** 100, **₹1,41,27,710.13**.
> - **Overdue: 52, ₹72,53,123.33.**
> - **MSME vendors' open bills: 55, ₹83,98,846.05.** These are top of the list, and UC-04 found 7 real
>   45-day breaches.
> - Due in the next 7 days: 2, ₹2,67,270.00.
>
> **Top of the plan:**
> - **BILL-2026-00001** (`60f30f05-df43-4a1c-9e6e-7409d0a86083`): dated 2026-06-07, due 2026-07-22,
>   **₹5,85,162.00** to an MSME vendor. It is UC-04's worst breach (68 days over at its spec date), and on
>   **2026-12-05** it becomes UC-01's first 180-day reversal (₹1,02,672 of credit). Paying it removes two
>   statutory exposures at once.
> - **BILL-2026-00002** (`617f53e8-7a6d-4949-b79d-8d8bd25c9355`): dated 2026-06-26, due 2026-08-10,
>   ₹3,34,176.00.
>
> **Net off before paying:**
> - ₹4,91,099.27 of vendor credits across 7 vendors (UC-41), e.g. Jindal Steel Depot ₹3,17,137.59;
> - **hold** 10 IMS-rejected bills (UC-24);
> - pay the 4 cash-mode bills by bank transfer instead (UC-38).

---

## 6. Known-bad data

- `payment_terms` is null on 68 of 100 open bills, and odd on others (77.8, 207.68, 275.93 days). When
  null, fall back to `due_date`; when `due_date` is also null, use the rulebook default (30 days).
- Earlier negative `grand_total` bills (N7) are all void now: 0 open bills carry a negative total. The
  check is kept as a regression guard.

---

## 7. Output contract

`finding_type: "payment_plan"`. One row per bill:
- `action ∈ {pay_now, pay_by, hold, net_off}`, `pay_by_date`, `amount_to_pay` (after credits and TDS);
- `cost_of_delay_7d`, `reasons[]` (rule ids from the source use cases).

The summary gives the total to pay this week, the exposure avoided and the amount held.

---

## 8. Limits

- **Never pays.** `PaymentMade.create` and `Bill.record_*payment` are T3 and never registered. The plan
  is a recommendation for a human to execute.
- Cost-of-delay figures depend on the rulebook's RBI rate and contractual assumptions, both shown on each
  row.

---

## 9. Validation

1. **Live:** recompute the open, overdue, MSME and next-7-days figures.
2. **Fixture:** two bills of ₹1,00,000, one MSME at day 46 and one non-MSME at day 60 → the MSME bill ranks
   first.
3. **Budget fixture:** budget ₹1,50,000 and three bills (₹1,00,000 MSME, ₹80,000 day-175 Rule 37, ₹50,000
   ordinary) → pay the MSME bill and hold the rest, unless the Rule 37 reversal cost per rupee is higher.

---

## 10. Open questions

- Should the plan be written back as `AgentTodo` items (one per pay-now bill) for finance to tick off?
  That is allowed (T1) and visible in-platform.
- Is there a cash-budget field anywhere (`Budget` entity)? Otherwise the budget comes from the request.

---

## 11. Live evidence — actual calls, 2026-10-04

- `Bill.list {"limit":1000}` → 100 open bills.
  - `due_date` present on all 100; 52 past due.
  - Oldest open: BILL-2026-00001 (2026-06-07), BILL-2026-00002 (2026-06-26), BILL-2026-00003
    (2026-07-11).
- `Party.list` → 8 MSME vendors (`msme_no` blank on all).
