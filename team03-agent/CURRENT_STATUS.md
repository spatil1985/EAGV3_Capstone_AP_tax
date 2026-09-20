# CURRENT_STATUS.md — verified against the live Suryodaya (India) instance

Snapshot date: **2026-09-20**, taken by logging in as `team03@theschoolofai.in` against
`https://agentswitch.theschoolofai.in` and calling the real REST + MCP endpoints (via
PowerShell/curl, credentials as ephemeral env vars, never written to disk). Everything
below is what the platform actually returned, not what the brief's illustrative
examples described — see **Corrections needed** for where those two disagree.

The ledger is live and shared with Teams 01/02, and a background job scheduler keeps
running against it, so exact counts here will already be stale by the time you read
this. Treat this as "shape of the data," not a frozen number to code against.

## 1. Identity & access (confirmed via `/api/auth/login` + `/api/auth/me`)

- Account: `team03@theschoolofai.in`, display name "Team 03", `id`
  `a9851867-7424-4578-b2cf-66872da1312d`.
- `role`: `finance_user`. `roles`: `finance_user`, `user`, `agent_user`,
  `sales_viewer`. `allowed_apps`: `accounting`, `agent`, `crm`.
- `company_id` (Suryodaya Precision Works Pvt. Ltd.): `5cbe5a55-af74-4363-a436-f5350593114c`.
- **We are not scoped to a narrow "AP & Tax only" role.** `sales_viewer` plus the
  `crm` app grant means this account can also read CRM entities (Lead, Deal,
  Quotation, SalesOrder, Pipeline, ...) that have nothing to do with the Seat 03
  brief. The 403 boundary the brief describes is enforced per-entity (see §4), not
  by hiding everything outside "our" domain.

## 2. India locale (`GET /api/accounting/locale`)

```
country: IN, accounting_standard: ind_as ("Ind AS / Schedule III")
tax_regime: gst, base_currency: INR, fiscal_year_start_month: april
gst_filing_frequency: monthly, coa_template: india_standard (91 accounts)
fiscal_year (current): FY 2026-27, 2026-04-01 to 2027-03-31
ledger: gl_entry_count=11966, account_count=132, is_empty=false
feature flags: gst_returns=true, gst_ims=true, eway_bill=true, msme_45_day=true,
               tds_tcs=true, einvoicing=false,
               sales_tax_jurisdictions=false, sales_tax_nexus=false (US-only features, correctly off)
```

The response also carries a **`not_yet_supported` list that the platform documents
about itself**, each with an internal ticket-style id. This is directly useful for
both the Week 1 gap report and Week 4 bug hunting — **don't spend bug-bounty effort
rediscovering these; they're already known**:

| Key | Status | Ticket |
|---|---|---|
| `period_close` | Partial — closing entries work, no adjusting-entry checklist / soft-close | — |
| `depreciation_posting` | Asset activation computes depreciation but posts **zero GL rows** (account mappings unset) | — |
| `inventory_costing` | `default_valuation_method` setting exists, no code reads it; LIFO not blocked despite Ind AS 2 prohibiting it | — |
| `tds_returns` | TDS/TCS now hit `grand_total` and post their own GL legs; no 26Q/27Q filing, no challan tracking | GST-18 |
| `einvoicing` | **Not implemented at all** despite a full settings page; no IRN, no signed QR, invoices above ₹5 Cr turnover are legally invalid as a result | GST-28 |
| `eway_bill_generation` | Partial — records link to documents, validity from distance; no NIC portal integration, no auto-generate at ₹50k threshold | GST-29 |
| `gst_amendments` | No amendment concept; a back-dated invoice into an already-filed period is accepted silently | GST-32 |
| `gstr9` | Annual return endpoint returns **HTTP 501** | GST-39 |
| `consolidation` | No multi-entity consolidation | — |

(The US side has its own equivalent list — `asc_606`, `us_payroll`, `tax_rate_service`
[Avalara/TaxJar wired but never called against a live sandbox], `asc_830` [FX
remeasurement absent], etc. — tagged US-12/US-28/US-34/etc. Full text is in the raw
locale response if needed later for the Keystone side of the gap report.)

## 3. Real entity model (from `/api/schemas`, 425 entities total across the whole platform)

`/api/schemas` returns the **entire platform's** data model (CRM, HR/payroll, esign,
contracts, storefront, design review, everything) unfiltered by seat — it is not a
per-seat view. The per-seat view is `tools/list` over MCP (§4). Entities actually
relevant to Seat 03, with real field names:

| Entity | Domain | Role | Notes |
|---|---|---|---|
| `Invoice` | accounting | AR **and** AP | Single entity for both directions via `direction: "receivable" \| "payable"`. Carries `taxes[]`, `tds_amount`, `itc_eligibility`, `approval_status`. |
| `Bill` | accounting | AP (vendor bills) | Separate from `Invoice(direction=payable)` — see open question below. Has `vendor_id`, `ims_status` (`pending/accept/reject` — GSTR-2B Invoice Management System), `itc_eligibility`, `use_tax_accrued` (US). |
| `Party` | core | Customers **and** vendors | No separate `Vendor` entity. Filter with `contact_type: "vendor"` (flat field) — confirmed against a real record (Bosch Rexroth India, `contact_type: "vendor"`, `roles: [{role: "supplier", active: true}]`, `tags: [{tag: "vendor"}]`). MSME fields (`is_msme`, `msme_type`, `msme_no`) live here, not on the bill. |
| `Tax` / `TaxGroup` / `TaxJurisdiction` / `TaxExemption` / `TaxNexus` | accounting | Tax config, not a per-document ledger | No `TaxLine` entity exists anywhere in the schema. `Tax.tax_type` enum: `IGST/CGST/SGST/UTGST/CESS/TDS/TCS/SALES_TAX/USE_TAX/EXCISE/WITHHOLDING_1099/other`. |
| `GSTReturn` | accounting | Period-level GST filing | Already carries **computed** `taxable_amount`, `igst_amount`, `cgst_amount`, `sgst_amount`, `cess_amount`, `net_tax_payable` per period/return-type (GSTR-1/3B/2A/2B/9). 5 exist today for Suryodaya. |
| `JournalEntry` / `GLEntry` | accounting | Ledger | `finance_user` (our role) has **read-only** access to both — cannot post journal entries directly. |
| `Payment` | accounting | Read-only summary | `finance_user` gets `read` only; actual payment writes go through `PaymentMade` / `PaymentReceived`. |
| `SalarySlip`, `Contract`, `EsignDocument` | payroll / contracts / esign | **Prohibited per SKILL.md** | Confirmed absent from our `tools/list` entirely (see §4) — the boundary is enforced by not exposing the tool, not just a runtime 403. |

`status` fields on `Invoice`/`Bill`/`PaymentMade` are `type: "state"` bound to a named
flow (`InvoiceFlow`, `BillFlow`, `PaymentMadeFlow`) — **not a freeform string**. There
is no `hold_payment` field anywhere on `Invoice` or `Bill`.

## 4. Real MCP tool inventory (`tools/list`, protocol `2025-11-25`)

**436 tools** visible to this account (confirmed via the actual handshake:
`initialize` → `notifications/initialized` → `tools/list`). `initialize.result`
includes a server-provided instruction string: *"Tools are scoped to the
authenticated caller: you see only what your roles, app entitlements and row scope
permit, and every call is executed through the same permission-checked path the REST
API uses."*

Relevant groups for Seat 03:

- **Core AP/Tax CRUD**: `Invoice.{list,get,create,update}`, `Bill.{list,get,create,update}`,
  `Party.{list,get,create,update}`, `Tax.{list,get}`, `TaxGroup.{list,get}`,
  `TaxJurisdiction.{list,get}`, `GSTReturn.{list,get}` (no create/update/delete for
  `finance_user`), `JournalEntry.{list,get}`, `GLEntry.{list,get}`, `Payment.{list,get}`,
  `PaymentMade.{list,get,create,update}`, `PaymentReceived.{list,get,create,update}`,
  `CreditNote.{list,get,create,update}`, `VendorCredit.{list,get,create,update}`.
- **Named workflow/state-transition tools** (not plain field updates):
  `Bill.open`, `Bill.submit`, `Bill.record_partial_payment`,
  `Bill.record_full_payment.{open,partially_paid,overdue}.paid`, `Bill.approval.submit`,
  `Invoice.send`, `Invoice.record_partial_payment`,
  `Invoice.record_full_payment.{sent,partially_paid,overdue}.paid`,
  `Invoice.cancel.draft.cancelled`, `Invoice.approval.submit`,
  `PaymentMade.mark_paid`, `PaymentMade.cancel`, `VendorCredit.{open,close}`,
  `PurchaseOrder.make.Bill`.
- **Escalation / audit-trail tools that actually exist**: `AgentEscalation.{list,get,create,update}`,
  `AgentMessage.{list,get}` (**no `.create`**), `AgentTodo.{list,get,create,update}`,
  `Notification.{list,get,create,update}`.
- **Agent job/session framework** (own domain, not mentioned in the brief's SKILL.md
  example): `AgentJob.{list,get}`, `AgentJobStep.{list,get}`,
  `AgentSession.{list,get,create,update,pause,resume,close...}`,
  `AgentTask.{list,get,create,update,pause,resume,complete,fail,run_now}`,
  `AgentRunbook(Run).{list,get}`, `AgentMemory.{list,get,create,update}`,
  `AgentSkill.{list,get}`, `AgentPersona.{list,get,daily_limits}`,
  `endpoint.job_ledger.{forensics,verify,replay,retention.preview}`.
- **Bug reporting**: `BugReport.{list,get,create}` — see §5 for the real schema.
- **Confirmed absent** (matches SKILL.md's prohibited list): no `SalarySlip.*`, no
  `Contract.*` entity tools, no `EsignDocument.*` anywhere in the 436.
- Also present but **out of Seat 03's stated scope**: full CRM (`Lead`, `Deal`,
  `Quotation`, `SalesOrder`, `Pipeline`, `AccountPlan`, ...), storefront endpoints,
  email/calendar, design review, contracts-domain endpoints
  (`endpoint.contracts.attribute_spend`) — available to this account because of the
  `sales_viewer`/`crm` grant in §1, not because Seat 03 is supposed to use them.

## 5. `BugReport.create` — real schema (fixes the guessed template in `postman/`)

```json
{
  "required": ["description"],
  "properties": {
    "description": "string",
    "company_id": "string",
    "page": "string",
    "agent_seat": "string",
    "job_id": "string",
    "app_version": "string",
    "reporter": "string",
    "status": "new | triaged | fixed | wont_fix (default new)",
    "resolution_note": "string",
    "delivery": "filed | local (default local)",
    "issue_number": "number",
    "issue_url": "string"
  }
}
```

Only `description` is required — much simpler than the guessed
`title/job_id/entity_ids/expected/actual/steps` shape currently in
`postman/AgentSwitch.postman_collection.json`. **Action item**: update that template
request and put the reproduction detail (steps, expected vs. actual, entity ids) into
`description` itself, or as `page`/`resolution_note` free text, since there's no
structured field for them.

## 6. Live data volumes today (Suryodaya, will drift — background jobs are running)

| Entity/filter | Count |
|---|---|
| `Invoice(direction=receivable)` | 315 |
| `Invoice(direction=payable)` | 165 |
| `Bill` | 101 |
| `Party` (all) | 194 |
| `GSTReturn` | 5 |
| `Tax` | 100 |
| `JournalEntry` | 1,119 |
| `PaymentMade` | 134 |
| `PaymentReceived` | 215 |
| `GLEntry` | 11,966 (matches `locale.ledger.gl_entry_count` exactly — good cross-check) |

The brief's "415 records" figure doesn't match any single count or obvious subtotal
above — most likely stale from when the brief was written, or referring to a
different snapshot/subset. Don't treat 415 as a target to reconcile against.

Also notable: `AgentJob` has **985** records already, many with
`trigger_kind: "schedule"` / `trigger_entity: "AgentTask"` and
`status: "failed"`, `error: "agent_authority_unresolved"`. This looks like a
platform-side scheduled-agent-task runner that's failing to resolve some kind of
identity/authority binding — worth a closer look as a possible bug-bounty candidate
(not yet investigated further; not one of the documented `not_yet_supported` gaps in
§2).

## 7. Corrections needed (SKILL.md / playbooks / postman — not yet applied)

Everything below was written against the brief's **illustrative example**, which the
instructor explicitly flagged as simplified ("Section 8 works one example through for
you"). Now that we have the real schema, these need fixing:

1. **`SKILL.md`** lists allowed entities as `Invoice, Payment, TaxLine, Vendor,
   JournalEntry`. Real equivalents: `Invoice` (both directions) + `Bill` (AP-specific),
   `Party` (filter `contact_type="vendor"`) instead of `Vendor`, `Tax`/`TaxGroup`/
   `TaxJurisdiction`/`GSTReturn` instead of `TaxLine`, and `JournalEntry`/`Payment` are
   **read-only** for our `finance_user` role, not read/write.
2. **`playbooks/duplicate_audit.md`** step 4 calls
   `Invoice.update(id=..., status="under_review", hold_payment=True)`. Neither
   `hold_payment` nor a freeform `status="under_review"` exists — `status` is a
   flow-driven state. The real mechanism for "flag and hold" is almost certainly
   `AgentEscalation.create` (exists, matches "escalate to Admin or Human operator" in
   SKILL.md) plus `Invoice.approval.submit` / `Bill.approval.submit` to move
   `approval_status` to `pending_approval` — needs confirming against the tool's
   actual `inputSchema` before relying on it.
3. **`playbooks/duplicate_audit.md`** step 4 also calls `AgentMessage.create`, which
   does not exist (`AgentMessage` only has `.list`/`.get`). Use `AgentEscalation.create`,
   `AgentTodo.create`, or `Notification.create` instead.
2. **`postman/AgentSwitch.postman_collection.json`**: `Vendor.list` and `TaxLine.list`
   example requests use tool names that don't exist. `Invoice.update (hold suspected
   duplicate)` uses the same nonexistent `hold_payment` field. The `File Bug Report`
   template's body shape doesn't match the real `BugReport.create` schema in §5.
4. **`scripts/invoice_matcher.py` / `scripts/tax_math.py`**: logic is still sound in
   the abstract (group-by-vendor exact/suspicious matching; output-tax minus claimed-ITC),
   but the field names they assume (`vendor_id` on the invoice itself, `type` values
   `sales_invoice`/`purchase_bill`, `is_itc_eligible`/`is_claimed` booleans) don't match
   the real fields (`Bill.vendor_id` exists, but `Invoice` uses `party_id` + `direction`;
   real eligibility is `itc_eligibility: input/input_services/capital_goods/ineligible`,
   and there's no `is_claimed` boolean — claim status is closer to `Bill.ims_status`
   `accept/reject/pending`). These will need reworking once we decide the exact
   query/aggregation approach against real data.

None of the above has been changed yet — this file is a record of what's true, not a
diff. Next step is deciding how to re-derive SKILL.md/playbooks/scripts from this
real model (separate task).

## 8. Open questions for next session

- Why do both `Invoice(direction=payable)` (165 records) and `Bill` (101 records)
  exist as separate AP-document types? Is one legacy, or do they represent different
  AP flows (e.g., `Bill` = vendor-submitted, `Invoice(payable)` = something else)?
  Need a few real samples compared side by side.
- What's the intended way our agent's run ties to a gradable `job_id`
  (`TestDuplicatePaymentGoal.check(self, db, company_id, job_id)` takes one) — do we
  create an `AgentSession`/`AgentTask` ourselves, or does the grading harness supply
  the `job_id` externally? `AgentJob` itself has no `.create` tool for us.
- Is the `agent_authority_unresolved` failure pattern on scheduled `AgentJob`s (§6) a
  platform bug worth filing, or expected behavior for jobs not addressed to our seat?
