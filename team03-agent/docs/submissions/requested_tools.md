# Requested tools — for the AgentSwitch platform team

**From:** Team 03 · Seat 03 (Payables & Tax) · **Date:** 2026-09-30
**Tenant verified on:** Suryodaya Precision Works (India), `finance_user`, 494 MCP tools

This lists the MCP tools our Payables & Tax agent needs and cannot get today. Every
item was checked against the live `tools/list`, `/openapi.json` (1,818 paths) and a
real call as our role, so we don't ask for something that already exists.

**Much of this is not new building.** 8 of the 20 asks expose something that already
works over REST, or grant read access to data that already exists. It becomes 9 if the
REST endpoint in T4.1 turns out to be the posting path we need.

| Tier | What we're asking | Count | Effort for you (our estimate) |
|---|---|---|---|
| **1** | Expose an existing REST endpoint as an MCP tool | 5 | Low — wrap and tag |
| **2** | Grant read access (app entitlement or role permission) | 3 | Low — configuration |
| **3** | Add an argument or action to an existing tool | 5 | Medium |
| **4** | New capability | 7 | High — most are already filed as feature requests |

`UC-nn` refers to our use-case specs in [`usecases/IN/`](../usecases/IN/). Each spec states the
statute behind the need.

---

## Tier 1 — Expose existing REST endpoints over MCP

These work today over REST for `finance_user`, or are pure computations. The agent
cannot reach them through MCP.

### T1.1 · `AccountingReport.ap_aging` and `AccountingReport.ar_aging` — **High**

- **Exists:** `GET /api/accounting/reports/ap-aging?as_of=` and `/ar-aging` → **200**
  for our role (buckets `current, 1_30, 31_60, 61_90, 91_120, …`).
- **Missing:** `tools/list` has `AccountingReport.balance_sheet / cash_flow /
  profit_and_loss / trial_balance` but not the two ageing reports.
- **Why:** payables ageing is the input to MSME 45-day exposure (UC-04), Rule 37
  180-day reversal (UC-01) and duplicate-payment triage (UC-05). Without it the agent
  rebuilds ageing from raw bills, and its numbers can drift from the screen.
- **Ask:** two READ tools with the same shape as the existing four — `as_of`,
  `book_id`, `view`.

### T1.2 · `Tax.compute` — **High**

- **Exists:** `POST /api/accounting/tax/compute` — verified correct
  (`{"amount":100000,"rate":18}` → IGST 18,000; rate 0 → empty `taxes[]`). It computes
  and does not persist.
- **Missing:** no MCP tool.
- **Why:** it is our validation oracle. We recompute stored tax against it in UC-07,
  UC-08, UC-09, UC-18, UC-21 and UC-22, and it is how we showed N128 and N10. Today the
  agent has to leave MCP for REST to use it.
- **Ask:** a READ-tagged MCP tool with the same body. See T3.4 for an HSN input.

### T1.3 · `GSTReturn.reconcile_2b` (read) and `GSTReturn.ims_action` (write) — **High**

- **Exists:** `POST /api/accounting/gst/reconcile-2b` and
  `POST /api/accounting/gst/ims-action`. `GSTReturn.list` already accepts
  `return_type: GSTR-2B`, and every `Bill` carries `ims_status` (`pending/accept/reject`).
- **Missing:** no MCP tool for either.
- **Why:** "what input credit is unclaimed?" is our core question. Under s.16(2)(aa)
  ITC is claimable only if the invoice appears in GSTR-2B, so an agent that cannot
  reconcile bills to 2B cannot answer it.
- **Ask:** `reconcile_2b` as READ (return matched / missing-in-2B / missing-in-books
  per bill, without persisting). `ims_action` as WRITE with a `dry_run` flag, per T3.2.

### T1.4 · `IndirectTax.ledger_balance`, `IndirectTax.reconcile`, `IndirectTax.determination` — **Medium**

- **Exists, 200 for our role:**
  - `GET /api/accounting/indirect-tax/ledger-balance?period=2026-09` →
    `ledger_total_minor −319258998`, `posting_count 334`
  - `GET /api/accounting/indirect-tax/reconcile?period=2026-09` →
    `status "variance"`, `variance_minor 319258998`
  - `GET /api/accounting/indirect-tax/determinations/{document_id}?document_entity=`
- **Missing:** no MCP tools.
- **Why:** period tax reconciliation (ledger vs documents) is the monthly check before
  GSTR-3B. The live September figure shows a ₹31.9 lakh variance, which is exactly
  what the agent should surface.
- **Ask:** three READ tools mirroring the GETs.

### T1.5 · `AccountingReport.drill` — **Low**

- **Exists:** `GET /api/accounting/reports/drill` (account refs, date range →
  contributing rows).
- **Why:** lets the agent tie a report figure back to documents, so a reconciliation
  finding can cite the entries behind a number.
- **Ask:** READ tool.

---

## Tier 2 — Read access to data that already exists

The same situation as F6 (the approvals app). The capability is built; our account
can't read it.

### T2.1 · Read `ApprovalPolicy` — **High**

- **Today:** `GET /api/ApprovalPolicy` → **403** *"None of your roles ['finance_user',
  …] can 'read' on ApprovalPolicy"*. `ApprovalRequest` and `ApprovalLog` are readable
  since F6 was granted.
- **Why:** the segregation-of-duties audit (UC-06) must know whether
  `allow_self_approval` is off before it can call a self-approval a violation. Without
  the policy, every finding is ambiguous.
- **Ask:** `read` on `ApprovalPolicy` for `finance_user`, plus
  `ApprovalPolicy.list/get` over MCP. Optionally also expose
  `POST /api/approvals/simulate-policy` as READ ("which policy would route this bill?").

### T2.2 · Enable the `inventory` app (read) and expose receipts — **High**

- **Today:** `GET /api/inventory/receipts` and `/api/inventory/stock-balance` →
  **403** *"App 'inventory' is not enabled for your account"*. No `StockEntry` or
  receipt tool in `tools/list`.
- **Why:** `endpoint.accounting.bill_match` already computes `received_qty` from
  receipts. On 2026-09-28 it found **8 bills billed with 0 received** (₹20.5 lakh,
  7 of them MSME vendors). The agent sees the verdict but cannot inspect the receipt
  behind it. Three-way match (UC-11) and expiry (UC-16) need the document.
- **Ask:** `inventory` read entitlement for Seat 03, plus `InventoryReceipt.list/get`
  and `StockBalance.get` over MCP.
- **Note:** this likely reduces our filed **F1** ("no Goods Receipt Note entity") to
  an entitlement ask, as happened with F6.

### T2.3 · Enable the `manufacturing` app (read) for `Batch` — **Medium**

- **Today:** `GET /api/Batch` → **403** *"App 'manufacturing' is not enabled"*.
- **Why:** 29 items carry `shelf_life_days`. Expiry is `receipt date + shelf life` per
  batch, and ITC on written-off stock is blocked under s.17(5)(h) (UC-16). Without
  batch dates the agent can only estimate.
- **Ask:** read entitlement, plus `Batch.list/get` over MCP.

---

## Tier 3 — Arguments or actions on existing tools

### T3.1 · List-tool filters: `updated_since`, ranges, multi-value — **High**

- **Today** (`Bill.list` and `Invoice.list` `inputSchema`): every filter is an exact
  match on one value. `{"itc_eligibility": ["input","input_services"]}` →
  `-32602 "/itc_eligibility must be string"`. No `updated_since`, no `date_from` /
  `date_to`, no `balance_due_gt`. Only `PartyRelationship.list` has an
  updated-since-style argument.
- **Why:**
  1. Event-driven checks, such as the duplicate check on each new bill (UC-05), need
     "bills changed since my last run". Today the agent re-reads every bill on every
     poll.
  2. "Unpaid bills older than 45 / 180 days" (UC-01, UC-04) is a range query that is
     always done client-side.
- **Ask:** on `Bill.list`, `Invoice.list`, `CreditNote.list`, `PaymentMade.list`,
  `ApprovalRequest.list`, add `updated_since` (ISO timestamp), `date_from`/`date_to`,
  and array values (`in`) for enum filters.
- **Also:** `Bill.list.date` declares `"default": "today"`. Unfiltered calls return all
  dates in practice, so the default is not applied. Worth correcting in the schema so
  agents don't send a date they don't mean.

### T3.2 · `dry_run` on write tools — **High** *(narrows filed F2)*

- **Today:** `endpoint.approvals.check_sla {"dry_run": true}` already exists and works.
  No other write tool accepts it.
- **Why:** our ledger is shared with Teams 01 and 02. Every write the agent proposes
  (hold a bill, escalate, IMS accept/reject) has to be tried on live data first.
- **Ask:** the same `dry_run` flag, returning the would-be diff without persisting, on
  `Bill.update`, `ims_action` (T1.3) and the hold action (T3.3). **We are not asking for
  a sandbox tenant.**

### T3.3 · `Bill.hold` / `Bill.release_hold` — **High**

- **Today:** `Bill` exposes `create`, `update`, `submit`, `open`, `approval.submit` and
  `record_*_payment`. There's no hold. The only lever is setting `approval_status`,
  which misuses the approval workflow and leaves no reason.
- **Why:** our strongest findings all end in *"do not pay this yet"*: suspected
  duplicates (UC-05), TDS larger than the bill (UC-09; 124 bills with negative
  payables), and billed-but-not-received (UC-11).
- **Ask:** a WRITE action with `reason_code` and `note`. It should block
  `PaymentMade.create` against the bill until released, and appear in `Bill.get` and
  the audit log.

### T3.4 · HSN/SAC rate lookup for GST — **Medium**

- **Today:** `Tax.compute` takes a rate on trust and reports
  `rate_source_authoritative: false`. `GET /api/accounting/tax/rate-service` → **409**
  *"not available under the active accounting locale (India / GST)"*.
- **Why:** rate correctness (UC-18). One HSN on our ledger (73269099) is charged at
  0 / 5 / 9 / 12 / 18%, and there is no source of truth to say which is right.
- **Ask:** an `hsn_or_sac` input on `Tax.compute` (or `Tax.rate_for_code`) returning
  the notified rate and its effective date.

### T3.5 · Structured `AgentEscalation` for compliance findings — **Low**

- **Today:** `AgentEscalation.create` exists (we'll use it). Its `reason_code` enum is
  support-oriented (`customer_asked_for_a_person`, `sensitive_topic`, …), and there is
  no structured link to the entities involved.
- **Ask:** add `reason_code: compliance_finding` and optional
  `entity_refs: [{entity, id}]` and `amount`, so escalations can be filtered and
  de-duplicated.

---

## Tier 4 — New capabilities

Most of these are already filed as feature requests. They are listed here as **tool
shapes**, so each request names what the agent would call.

| # | Tool shape | Filed as | Unblocks | Note |
|---|---|---|---|---|
| T4.1 | **ITC reversal posting**: `IndirectTax.reverse` (WRITE, `dry_run`, audited) scoped to `finance_user` | F18 part 3 | UC-01, UC-08, UC-15, UC-16, UC-17 | `POST /api/accounting/indirect-tax/reverse` **already exists over REST**. We did not call it, as it would write. If it posts an ITC reversal, T4.1 becomes a Tier 1 "expose it" ask. Please confirm what it does. Example: UC-08 computes a September Rule 42 reversal of ₹4,05,733.76 that cannot be posted today |
| T4.2 | **Party identity validation**: `Party.validate {gstin, pan, udyam}` → registered name, status | F11 (not yet filed) | UC-04, UC-13, UC-21 | All 8 MSME vendors have a blank `msme_no`. s.43B(h) applies only to Udyam-registered suppliers, so the agent cannot evidence it |
| T4.3 | **Company tax profile**: `Company.tax_profile` → GSTIN, registration type (regular / composition), preceding-FY turnover | F20 | UC-13, UC-17 | `Company` has no tax-mode or GSTIN field. The s.194Q ₹10 crore test and composition eligibility need it |
| T4.4 | **LUT registry**: `LUT.list/get` with `financial_year`, `arn`, `valid_from/to` | F21 | UC-20 | `TaxExemption` has an "Export under LUT" row with no dates and no party link |
| T4.5 | **Job-work return tracking**: `DeliveryChallan.returns` or a return-link field | F19 (**correct the wording**) | UC-10 | `challan_type=job_work` **exists** (19 challans). F19's claim of "no subtype" is wrong. The gap is recording the return |
| T4.6 | **Receipt voucher for advances**: tax fields on `RetainerInvoice`, or a `ReceiptVoucher` entity | — | UC-22 | GST on service advances is due on receipt (s.13(2)). `RetainerInvoice` has no tax fields |
| T4.7 | **OCR for scanned bills** in `bill_intake.extract` | F9 (narrowed) | intake | `endpoint.accounting.bill_intake.extract` exists, but reads the **text layer** only. The gap is scanned or photographed bills, not extraction in general |

---

## Already exists — not requested

Checked and found present, so they are not asked for. We list them to show the
absence claims above were checked.

`AgentMemory.*` · `AgentEscalation.*` · `BugReport.*` ·
`AccountingReport.{balance_sheet, cash_flow, profit_and_loss, trial_balance}` ·
`endpoint.accounting.bill_match` · `endpoint.approvals.check_sla` (with `dry_run`) ·
`endpoint.accounting.bill_intake.{extract, accept, reject, queue}` · `BillIntakeEvent.list` ·
`GSTReturn.list/get` (incl. GSTR-2B type) · `EWayBill.{create, generate, update, activate}` ·
`PaymentMade.create` · `VendorCredit.apply_to_bill` · `RecurringBill/RecurringInvoice.update` ·
`DirectTaxPreferences.list` · `ApprovalRequest/ApprovalLog.list/get`.

---

## Priority order

1. **T1.1, T1.2, T2.1** — cheapest and highest value. Two existing reports, one
   existing endpoint and one permission.
2. **T1.3 (2B reconcile)** and **T3.3 (bill hold)** — the core ITC question, and the
   action most findings need.
3. **T3.1 (filters)** and **T3.2 (dry-run)** — make the agent efficient and safe on
   a shared ledger.
4. **T2.2 (inventory receipts)** — likely closes F1 without a new entity.
5. **T4.1** — first confirm whether `indirect-tax/reverse` is already the posting path.
6. The rest of Tier 4 and T1.4, T1.5, T2.3, T3.4, T3.5.

---

*Verification: `tools/list` (494 tools), `/openapi.json` (1,818 paths), and GET calls as
`team03@theschoolofai.in` on 2026-09-30. No POST endpoint was called except
`tax/compute`, which does not persist. Where this document says an endpoint "exists"
but we did not call it (the `POST` endpoints in T1.3 and T4.1), the claim rests on the
OpenAPI listing alone.*
