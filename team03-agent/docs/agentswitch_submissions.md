# AgentSwitch — Bug Reports & Feature Requests (Team 03, Seat 03 Payables & Tax)

Consolidated, submission-ready list of everything we've found on the AgentSwitch
platform: confirmed defects, and feature gaps identified by comparing against real
competitor products.

**Submission channel:** `POST /api/bug-report` (per the brief, §Week 4 Milestone 2 —
100 points per *verified* bug). Body fields: `description` (required), `page`,
`agent_seat`, `job_id`. `reporter` and `app_version` are server-stamped and are
deliberately not settable by the reporter.

**Scoring note:** the brief's bug bar asks for reproducible steps, expected vs.
actual, **job ID**, and entity IDs. Everything below has steps, expected/actual and
entity IDs. **None has a `job_id`**, because all were found by direct REST/MCP
inspection rather than an agent run. Wiring `run_agent.py` to create an
`AgentSession`/`AgentTask` would let future findings carry one.

**Do not submit §3.** Those items are already self-documented by the platform in the
locale endpoint's `not_yet_supported` list and would likely be rejected as known.

---

## Status summary

| # | Title | Type | Severity | Status |
|---|---|---|---|---|
| B1 | US tax jurisdictions on an India-locale company | Bug | High | **Filed** `2a655790-2b05-4528-ade1-cff6d9c5ce15` |
| B2 | `is_group=false` with `group_taxes` children (67/100) | Bug | Medium | **Filed** `5c8b16e3-3761-4fa3-b482-9d486c977411` |
| B3 | Tax Summary renders product names as tax heads | Bug | High | **Filed** `84955e11-7f36-4fc5-bb85-7bba1d7a3257` |
| B4 | Tax lines storable that the platform's own calculator can't produce | Bug | High | Ready — split out of B3 |
| B5 | Journal voucher shows ₹0.00 with no lines despite non-zero Total Debit | Bug | Medium | Needs reproduction |
| F1 | No Goods Receipt Note entity — 3-way matching impossible | Feature | High | Ready |
| F2 | No sandbox / test environment | Feature | High | Ready |
| F3 | No reports exposed over MCP | Feature | Medium | Ready |
| F4 | No bank account validation (penny-drop) | Feature | Medium | Ready |
| F5 | No scoped external-accountant (CA) access | Feature | Medium | Ready |
| F6 | `approval_status` has no named levels, routing or history | Feature | Medium | Ready |
| F7 | No batch/payment-run concept for `PaymentMade` | Feature | Low | Ready |
| F8 | MSME 45-day statutory tracking not automated | Feature | Medium | Ready |

---

## 1. Bugs — filed

### B1 · US tax jurisdictions on an India-locale company **[FILED `2a655790…`]**

**Severity:** High · **Area:** Tax / Settings

All 100 `TaxJurisdiction` rows on Suryodaya (India) have `country="US"` with
US-only `jurisdiction_level` values (special_district 33, county 25, city 22,
state 20) and 18 with `has_nexus=true` — while `GET /api/accounting/locale` reports
`features.sales_tax_jurisdictions=false` and `sales_tax_nexus=false` for India.
Indian GST has no county/special-district jurisdiction or nexus-sourcing concept.

Sample `c6fc62d8-180d-4dde-bc9e-01b36cce2f5f`: `name="Depth Gauge 301mm (Kg)"`,
`country="US"`, `city="Thane"` (an Indian city), `county="File Set 9004"`,
`state_code="VP3433/9004"`, `sourcing="origin"`, and `liability_account_id`
pointing at **"Unsecured Loans"** — a loan account as a tax liability account.

**Impact:** `Tax.jurisdiction_id` links to these, so if the GST computation path
reads `TaxJurisdiction`, Indian GST routes through US nexus logic.

---

### B2 · `is_group=false` with `group_taxes` children **[FILED `5c8b16e3…`]**

**Severity:** Medium · **Area:** Tax / Settings

67 of 100 `Tax` rows have `is_group=false` yet carry `group_taxes` children (16 are
correctly flagged, 17 have no children). Visible in the UI: Tax "V-Block Pair 5131"
shows "Is Group: No" while a GROUP TAXES section below lists a component.

Related: `group_taxes[].tax_type` is unconstrained free text — **0 of 88** populated
values match the `Tax.tax_type` enum, while the *parent* `Tax.tax_type` correctly
enforces it on the same records.

**Impact:** no consumer can decide whether to expand a composite tax; the flag and
the data disagree on two-thirds of the tax master.

---

### B3 · Tax Summary renders product names as tax heads **[FILED `84955e11…`]**

**Severity:** High · **Area:** Reports / Tax

The Tax Summary report (01-04-2026 → 21-09-2026) lists rows labelled
"Hex Key Set 7355", "V-Block Pair 7359", "Drill Chuck 7357" etc. under OUTPUT TAX
(SALES), and includes their amounts in the Total of ₹1,08,80,907.12. The report
groups by `CreditNote.taxes[].tax_type`, declared `"type": "text"`. Each row maps
to the paisa to one credit note.

The six rows total ₹4,991.76, while those documents' own `total_tax` sums to
₹62,402.95 — the report counts amounts the documents themselves exclude.

> **Note:** consider asking for this to be split against B4, or reference B4 as the
> data-layer half. Filed as one report before the split was identified.

---

## 2. Bugs — ready to submit

### B4 · Tax lines can be stored that the platform's own calculator cannot produce

**Severity:** High · **Area:** Tax / Data integrity · **Split from B3**

```
Documents can store tax lines that the platform's own tax calculator would never
produce. Nothing validates taxes[] on write.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c),
India locale, tax_regime "gst".

SUMMARY
This is NOT a calculation bug. POST /api/accounting/tax/compute is correct, and that
was verified first. The defect is that stored CreditNote.taxes[] rows contradict what
that endpoint returns for the same inputs, meaning they were written without ever
being validated against it.

THE CALCULATOR IS CORRECT (control tests)
  POST /api/accounting/tax/compute {"amount": 100000, "rate": 18}
    -> total_tax 18000.0, taxes[{tax_type "IGST", rate 18.0, amount 18000.0}]
  POST /api/accounting/tax/compute {"amount": 288886.74, "rate": 18}
    -> total_tax 51999.61
  POST /api/accounting/tax/compute {"amount": 100000, "rate": 0}
    -> total_tax 0, taxes[]        <- a 0% rate correctly yields NO tax row at all
The calculator also emits a valid Tax.tax_type enum value ("IGST").

WHAT IS ACTUALLY STORED
  CN-2026-00022  08749498-9898-423a-a4ab-6bac6b679c7d
    taxable_value 288886.74, taxes[{rate 18, amount 975.17}]
    The calculator returns 51999.61 for this exact base and rate.
  CN-2026-00023  f7aa6705-2703-4403-ba36-926197945859
    taxes[{rate 0, amount 1381.05}]
    A 0% rate carrying tax. The calculator returns an empty taxes[] for rate 0, so
    this row is not something the compute path can emit.
  CN-2026-00020
    taxable_value 3469.53, taxes[{rate 5, amount 1635.97}]
    5% of 3469.53 is 173.48. The stored amount exceeds rate x base by ~9x.

Additionally taxes[].tax_type holds product names ("V-Block Pair 7363") rather than a
tax head, whereas the calculator emits "IGST". The field is declared "type": "text",
so nothing constrains it despite the canonical Tax.tax_type enum existing.

REPRODUCTION
1. POST /api/accounting/tax/compute {"amount": 288886.74, "rate": 18} -> 51999.61
2. tools/call CreditNote.get {"id": "08749498-9898-423a-a4ab-6bac6b679c7d"} -> 975.17
3. POST /api/accounting/tax/compute {"amount": 100000, "rate": 0} -> taxes[]
   then inspect f7aa6705-2703-4403-ba36-926197945859 -> rate 0, amount 1381.05

EXPECTED
A stored tax line should be reconcilable against the platform's own calculator:
amount follows from rate and base, a 0% line carries no tax, tax_type is a recognised
head. Violating writes should be rejected or flagged.

ACTUAL
Arbitrary rate/amount combinations persist, including amounts exceeding the taxable
base and 0% lines carrying tax. These flow into compliance reporting.

IMPACT
Every consumer of taxes[] is affected, not just one report. Because
/api/accounting/tax/compute already implements correct behaviour, it can serve as the
validation oracle on write.

ENTITY IDS
CreditNote: 08749498-9898-423a-a4ab-6bac6b679c7d, f7aa6705-2703-4403-ba36-926197945859
Company: 5cbe5a55-af74-4363-a436-f5350593114c
No job_id — found by direct REST/MCP inspection.
```

---

### B5 · Journal voucher renders ₹0.00 with no lines despite non-zero Total Debit

**Severity:** Medium · **Area:** Accountant / Manual Journals · **Needs reproduction**

Observed in the UI inventory (`UI.MD` SCR-041): the Manual Journals **list** shows a
non-zero `Total Debit`, but opening the journal renders a voucher with no line items
and subtotal/total ₹0.00. `JournalEntry.lines` is a real schema field, so the data
should be present.

**Before submitting:** reproduce against a specific `JournalEntry.id` and confirm via
`tools/call JournalEntry.get` whether `lines` is populated in the API response. If
populated → UI rendering bug (strong). If empty while `total_debit` is non-zero →
data-integrity bug (stronger). Capture the id either way.

---

## 3. Do NOT submit — already self-documented by the platform

These appear in `GET /api/accounting/locale` → `not_yet_supported`, with the
platform's own ticket ids. Re-filing risks rejection as already-known.

| Ticket | Item |
|---|---|
| GST-28 | E-invoicing (IRN / signed QR / IRP) not implemented despite a full settings page |
| GST-29 | E-way bill generation — no NIC portal integration, no Part A/B, no threshold auto-generate |
| GST-32 | No GSTR-1 amendment tables; back-dated invoice into a filed period accepted silently |
| GST-39 | GSTR-9 annual return returns HTTP 501 |
| GST-18 | TDS/TCS — no auto-deduction by section/threshold, no challan tracking, no 26Q/27Q |
| — | Depreciation posting produces zero GL rows |
| — | Inventory costing method setting read by no code path |
| — | Multi-entity consolidation absent |

---

## 4. Feature requests

Derived from the competitor analysis in [`gap_report.md`](gap_report.md) and
[`razorpay_gap_report.md`](razorpay_gap_report.md). These are gaps, not defects —
submit separately from bugs, or raise with the instructor, since the bug bounty is
for defects.

### F1 · Goods Receipt Note entity — enable 3-way matching · **High**

**The single highest-value ask.** There is no goods-receipt concept anywhere in the
425-entity schema (verified by grepping every entity name; only unrelated
`EsignConsentReceipt` / `FormConsentReceipt` match). `Bill.purchase_order_id`
enables two-way matching (PO ↔ Bill), but three-way (PO ↔ GRN ↔ Bill) is
**structurally impossible**.

Why it matters: 3-way matching is the core AP control for verifying that what was
billed was actually received. Mysa (3-way), CashFlo (6-way), Kodo (2-/3-way) all
advertise it, and **RazorpayX demonstrably imports GRNs** as a first-class tab
(verified in the live product).

This is the one gap an agent cannot orchestrate around — you cannot match against a
document type that does not exist. Requires: a `GoodsReceiptNote` entity with
line-level quantities, links to `PurchaseOrder` and `Bill`, and a matching tool.

### F2 · Sandbox / test environment · **High**

There is no test mode. The Suryodaya ledger is shared live with Teams 01 and 02,
so there is nowhere to rehearse a write before doing it for real, and any mistake is
immediately visible to other teams.

This is acute for agent development specifically: our seat's playbooks mutate
records (hold duplicate bills, submit for approval), and we cannot validate that
behaviour without touching shared production data. RazorpayX provides test balances
and test payouts that explicitly "do not affect the actual balance."

Requires: a resettable per-team sandbox company, or a dry-run flag on write tools
that validates without persisting.

### F3 · Expose reports over MCP · **Medium**

No report is callable from MCP. P&L, Balance Sheet, Trial Balance, AR/AP Aging and
Cash Flow exist only as REST endpoints (`/api/accounting/reports/*`), and
`/api/reports` supports `trial_balance, profit_and_loss, balance_sheet, receivables,
payables, stock_balance, gst_r1`. None appears among the 436 MCP tools.

An agent therefore cannot read the financial statements it is reasoning about. For a
platform whose premise is agent-driven accounting, this is a notable omission.

### F4 · Bank account validation (penny-drop) · **Medium**

`Party` stores `vendor_bank_account_number`, `vendor_bank_name`, `vendor_bank_code`
and `beneficiary_name`, but nothing validates that the account exists or belongs to
the named vendor.

Paying a wrong or fraudulently-altered bank account is a classic AP fraud vector,
and it is directly in Seat 03's remit. RazorpayX ships a "Fund Account Validation
report," implying penny-drop verification.

### F5 · Scoped external-accountant (CA) access · **Medium**

Roles are internal (`finance_user`, `finance_admin`, `accountant`, `auditor`) with
no shareable, report-only external grant. RazorpayX offers exactly this: *"CA can
download reports without troubling you! No access to your RazorpayX account except"*
reports.

In India the CA relationship is central to SME compliance, and the current
alternative — sharing a login — is both friction and a security risk.

### F6 · Approval levels, routing and decision history · **Medium**

`approval_status` has four values (`not_required` / `pending_approval` / `approved`
/ `rejected`) with `Bill.approval.submit` / `Invoice.approval.submit` tools. Missing:
named approver levels, routing rules (by amount, vendor, category), and a
per-decision audit trail.

Our agent can move a bill to `pending_approval` but cannot express *who* must
approve, and no history records who approved or rejected. RazorpayX's demo shows a
named "Finance L2" level with the rejection recorded on a timestamped timeline.

### F7 · Batch / payment-run concept · **Low**

`PaymentMade` is per-payment. There is no batch identity, so a vendor payment run
(settling many bills together) cannot be tracked, reported on, or reversed as a
unit. RazorpayX treats bulk payouts as a first-class batch object.

### F8 · MSME 45-day statutory tracking · **Medium**

`Party.is_msme`, `msme_type` and `msme_no` exist, and `MSMEPreferences` is an entity,
but nothing surfaces MSME bills approaching or past the statutory 45-day payment
window. Late payment to an MSME vendor attracts penal interest under the MSME Act,
so this is a live compliance exposure rather than a convenience.

Note: our agent **can** bridge this today by joining `Party.list(is_msme=true)`
against `Bill.due_date` — so it is a good candidate for demonstrating agent value
over the stock UI, and only needs platform support if it should be native.

---

## 5. Suggested submission order

1. **B4** first — it has a control test proving the calculator is correct before
   claiming the data is wrong, so it is the hardest to dismiss.
2. **B5** once reproduced with a concrete `JournalEntry.id`.
3. **F1 (GRN)** as the headline feature request — structural, competitor-verified,
   and unblockable by orchestration.
4. **F2 (sandbox)** — frame it as blocking safe agent development, which is the
   platform's own stated purpose.
5. The remaining feature requests as a single batch, referencing the competitor
   evidence in `razorpay_gap_report.md`.

**Before submitting anything further, confirm with the instructor** whether
`/api/bug-report` is the channel that earns bounty credit, or whether submissions
should also land on the class bug board — the two are not connected as far as we can
tell, and our three filed reports (`status: new`, `delivery: local`) have not
appeared on the board.
