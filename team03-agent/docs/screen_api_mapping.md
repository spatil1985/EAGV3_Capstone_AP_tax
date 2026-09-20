# screen_api_mapping.md — UI.MD screens mapped to real AgentSwitch API/MCP calls

> Companion to `UI.MD`. For every screen (`SCR-XXX`) in `UI.MD`, this maps the data
> shown to the **actual** MCP tool(s) and REST endpoints that back it, verified live
> against Suryodaya on 2026-09-20 (see `../CURRENT_STATUS.md` for the full
> methodology and raw findings). Where `UI.MD`'s screen name differs from the real
> entity name (e.g. "Vendors" vs. `Party`), that's called out explicitly.

## Legend

- ✅ **Mapped** — tool name and filters confirmed against the live `tools/list` /
  `/api/schemas` response.
- ⚠️ **Inferred** — entity/tool exists and is the obvious candidate, but the exact
  UI behavior (e.g. which fields a form actually writes) wasn't independently
  re-verified call-by-call.
- ❌ **No MCP tool found** — the UI action has no corresponding entry anywhere in
  the 436 tools returned by `tools/list` for this account. Either it's REST-only
  (not exposed over MCP), gated behind a role/permission we don't have, or not
  implemented server-side at all (see `CURRENT_STATUS.md` §2's
  `not_yet_supported` list for several of these).

All list tools share the same pagination shape:
`{limit, offset, sort_by, sort_order, search, ...entity-specific filters}` →
`{data: [...], total, limit, offset}`. That's omitted below except where a filter
is the whole point (e.g. `Invoice.list(direction=...)`).

---

## SCR-001 — Company Overview / Dashboard

- **Overdue supplier bills / recorded collections** — ✅ Derived, not a single
  endpoint. Overdue bills = `Bill.list()` filtered client-side on `due_date` vs.
  today and `status`/`balance_due` > 0. There is no dedicated "dashboard summary"
  tool; this screen is almost certainly computed by aggregating `Invoice.list`
  (direction=receivable) and `Bill.list` results, or by a REST-only dashboard
  endpoint not exposed as an MCP tool (`endpoint.*` list has no
  `dashboard`/`kpi` entries).
- **Reporting-period filter** — ⚠️ likely just narrows the `date`/`due_date`
  filters on the underlying `Invoice.list`/`Bill.list` calls.

## SCR-002 — Customers / Contacts List

- ✅ `Party.list()`. "Individuals/Organizations count" = client-side aggregation
  of `Party.type` (`individual`/`organization`) over the same result set, or two
  separate `Party.list(type=...)` calls with `total` read off each.
- "Add new contact/customer" → ✅ `Party.create`.
- "Open record detail" → ✅ `Party.get(id=...)`.

## SCR-003 — Customer / Business Partner Detail

- ✅ `Party.get(id=...)`. Every field listed in `UI.MD` (GST No, PAN, Tax, Taxable,
  TIN, W9 On File, W9 Signed Name, Is 1099 Vendor, Backup Withholding, Is MSME,
  MSME No, Vendor Bank Account Number, Beneficiary Name, Opening Balance, Portal
  Enabled, roles/since/active) is a real field on `Party` — confirmed in
  `CURRENT_STATUS.md` §3's field dump. `UI.MD`'s "Key architectural observation"
  (unified business-partner model) is fully confirmed: there's genuinely one
  `Party` entity for both customers and vendors, distinguished by `contact_type`
  and/or `roles[].role`.
- Note: a real `Party.get` response redacts some of these
  (`tax_id`,`gst_no`,`pan`,`msme_no`,`beneficiary_name`,`vendor_bank_account_number`,
  `tin`,`w9_signed_name` came back under `_redacted_fields` in our sample pull) —
  the detail screen may show masked values even when the underlying data exists.

## SCR-004 — New Customer / Business Partner

- ✅ `Party.create({name, type, email, phone, roles:[{role, since}], contacts:[...],
  addresses:[...], tags:[...]})`. All of these are real nested/array fields on
  `Party` (`roles` is a `children` shape with `role/since/active`; `contacts`,
  `addresses`, `tags` are similar array fields per the schema dump).
- `UI.MD`'s observation that the create form doesn't expose finance/tax fields is
  consistent with the schema: nothing stops a follow-up `Party.update(id=...,
  gst_no=..., is_msme=..., ...)` — it's a UI/UX choice, not a schema limitation.

## SCR-005 — Accounting Dashboard

- **Payables summary** (Total unpaid bills, current, overdue) — ✅ derived from
  `Bill.list()`, likely filtered/aggregated by `status` and `due_date`.
- **Receivables summary** — ✅ derived from `Invoice.list(direction=receivable)`.
- **Cash Flow / Income and Expense / Top Expenses** — ⚠️ likely a report-style
  aggregation over `GLEntry.list()` and/or `Expense.list()`; no dedicated
  "dashboard" MCP tool exists.
- **Recent Bills** — ✅ `Bill.list(sort_by=date, sort_order=desc, limit=N)`.
- **Bank & Credit Cards** — ✅ `BankAccount.list()` (has `account_name`,
  `bank_name`, `current_balance`, `is_active` / linkage fields).
- **Nav items** (Vendors, Expenses, Recurring Expenses, Purchase Requisitions,
  Purchase Orders, Bills, Recurring Bills, Payments Made, Vendor Credits) map
  1:1 to: `Party` (contact_type=vendor), `Expense`, `RecurringExpense`,
  `PurchaseRequisition`, `PurchaseOrder`, `Bill`, `RecurringBill`, `PaymentMade`,
  `VendorCredit` — all confirmed present in `tools/list`.

## SCR-006 — Supplier Bill Detail

- ✅ `Bill.get(id=...)`. Header/status, bill details, tax breakdown
  (`taxes[]`, `total_tax`), Grand Total/Balance Due (`grand_total`,
  `balance_due`) are all real `Bill` fields.
- **Void** → ⚠️ likely `Bill.update(status=...)` through the `BillFlow` state
  machine, or a dedicated cancel-style tool — `tools/list` doesn't show a
  `Bill.cancel` (unlike `Invoice.cancel.draft.cancelled`), so voiding a bill's
  exact tool is unconfirmed; `Bill.approval.submit` and `Bill.open`/`Bill.submit`
  are the only bill-flow tools we saw.
- **Edit** → ✅ `Bill.update(id=..., ...)`.
- **Email / Share / PDF / Print** → ❌ No MCP tool found. No `.pdf`, `.email`, or
  `.share` action anywhere in `tools/list` for `Bill` or any other entity —
  these are almost certainly REST-only, UI-rendered features.
- **Payments section** → ✅ `PaymentMade.list(vendor_id=...)` or filtering by
  the bill's id inside `PaymentMade.bills`/`applied_allocations` (both are real
  fields per the schema).
- **Not yet evidenced** items in `UI.MD` (TDS deduction, IGST, HSN/SAC, reverse
  charge, 2-/3-way match, PO/GRN match, approval workflow) — partially
  contradicted by the schema: `Bill` *does* carry `tds_name/tds_percentage/
  tds_amount/tds_section_code/tds_section`, `is_reverse_charge`, and
  `approval_status` fields, and `Bill.approval.submit` exists as a tool. Whether
  the *UI* currently renders/uses them is a separate question from whether the
  *data model* supports them — worth re-checking the live UI screen for these
  fields specifically before concluding they're unsupported.

## SCR-007 — Sales Invoices List

- ✅ `Invoice.list(direction=receivable)`. KPIs (Total Outstanding, Not Yet Due,
  Overdue, Total Invoices) are client-side aggregations over `outstanding` and
  `due_date` on the same result set.

## SCR-008 — Tax Invoice Detail

- ✅ `Invoice.get(id=...)` (direction=receivable). `taxes[]` per line item backs
  the tax lines; `UI.MD`'s observation that labels show generically as "Tax"
  (vs. `Bill`'s explicit CGST/SGST) is a UI rendering choice — the underlying
  `items[].cgst_amount/cgst_rate/igst_amount/igst_rate/...` fields exist on
  `Invoice` line items too (confirmed in a real sample pull in
  `CURRENT_STATUS.md`'s raw exploration), so the data is there even if this
  screen doesn't surface it.
- **Send** → ✅ `Invoice.send`. **Edit** → ✅ `Invoice.update`. **Email/Share/
  PDF/Print** → ❌ No MCP tool found (same as SCR-006).

## SCR-009 — Sales Orders List

- ✅ `SalesOrder.list()`. Note: `tools/list` shows `SalesOrder.{list,get,update}`
  but **no `SalesOrder.create`** for this account — creation may happen only via
  `Quotation.make.SalesOrder`-style conversion (we saw `Quotation.make.Invoice`
  and `SalesOrder.make.Invoice`/`SalesOrder.make.DeliveryChallan`, but no
  standalone `SalesOrder.create`).

## SCR-010 — Recurring Invoices

- ✅ `RecurringInvoice.list()` / `.get()` / `.create()` / `.update()` — all four
  CRUD tools exist. Filters include `frequency`, `next_invoice_date`, `status`,
  matching the Frequency/Status columns in `UI.MD`.

## SCR-011 / SCR-012 — Delivery Challans List / Detail

- ✅ `DeliveryChallan.{list,get,create,update}`.
- **Mark Returned / Mark Delivered** → ✅ `DeliveryChallan.mark_delivered`,
  `DeliveryChallan.mark_returned.delivered.returned`,
  `DeliveryChallan.mark_returned.invoiced.returned` (named state-transition
  tools, not a generic status write — matches the `state`/flow pattern seen on
  `Invoice`/`Bill`).
- **Create Invoice** → ✅ `DeliveryChallan.convert_to_invoice`.
- **Place of Supply / CGST / SGST** → ✅ real fields (`place_of_supply`,
  `taxes[]`) on `DeliveryChallan`.

## SCR-013 / SCR-014 — Payments Received List / Detail

- ✅ `PaymentReceived.{list,get,create,update}`. "Unused Amount" =
  `unused_amount` field (confirmed in schema).
- **Mark as Paid** → ✅ `PaymentReceived.mark_received`. **Void** →
  ✅ `PaymentReceived.cancel`. **Email/Share/PDF/Print** → ❌ No MCP tool found.

## SCR-015 — Retainer Invoice Detail

- ✅ `RetainerInvoice.{list,get,create,update}`.
- **Apply available funds / Record Payment** → ✅
  `RetainerInvoice.record_payment.sent.paid`,
  `RetainerInvoice.record_payment.draft.paid`. **Close** → ✅
  `RetainerInvoice.close`. **Send** → ✅ `RetainerInvoice.send`.

## SCR-016 / SCR-017 — Vendors List / Detail

- **`UI.MD` calls this "Vendors," but there is no `Vendor` entity or tool.** ✅
  Real mapping: `Party.list(contact_type="vendor")` for the list, `Party.get(id=...)`
  for detail — confirmed against a live record (Bosch Rexroth India,
  `contact_type: "vendor"`). "New vendor" → `Party.create(contact_type="vendor",
  roles=[{role:"supplier"}], ...)`.
- "GST Treatment" column → ✅ real field `Party.gst_treatment` (enum:
  `business_gst/business_composition/consumer/overseas/unregistered_business/
  sez/deemed_export`).
- `UI.MD`'s "Key architectural observation" that vendor/customer share a model
  is fully confirmed (§SCR-003 above) — it's the *same* `Party.get` call either
  way, just filtered differently in the list view.

## SCR-018 — Payments Made List

- ✅ `PaymentMade.list()`. "Unused Amount" → `unused_amount` field.
- **Mark Paid** → ✅ `PaymentMade.mark_paid`. **Cancel** → ✅ `PaymentMade.cancel`.

## SCR-019 / SCR-020 — General Ledger List / Entry Detail

- ✅ `GLEntry.list()` / `GLEntry.get(id=...)`. **Read-only for `finance_user`** —
  confirmed in `CURRENT_STATUS.md` §3 permissions table; there is no
  `GLEntry.create`/`.update` tool at all in the 436, for any role we could see.
  Fields (`account`, `party_id`, `debit`, `credit`, `voucher_type`, `voucher_id`,
  `posting_date`, `is_cancelled`, `remarks`) match `UI.MD`'s column list exactly.
- `UI.MD`'s note that the "Customer" label is generic even for vendor/expense
  contexts is explained by the schema: the field is literally `party_id` (a
  generic `Party` link), and the UI is presumably relabeling it "Customer"
  regardless of the party's actual role.

## SCR-021 — Transaction Locking

- ✅ `TransactionLock.list()` — real filters: `module`, `lock_date`,
  `locked_by`, `reason`. No `.create`/`.update` tool appeared in our `tools/list`
  scope, so the "Lock All Modules / Unlock per module / Configure date" actions
  either require a higher role than `finance_user` or go through a REST-only
  admin endpoint not exposed over MCP for this account. Confirm with
  `finance_admin`/`admin` credentials before assuming it's unreachable entirely.

## SCR-022 — Period Close

- ✅ `AccountingPeriod.list()` — filters include `period_type`, `fiscal_year`,
  `from_date`/`to_date`, `closes_fiscal_year`. Matches `UI.MD`'s fiscal
  year/monthly periods/status fields closely. As with Transaction Locking, no
  `AccountingPeriod.create`/`.update`/close-action tool showed up for
  `finance_user` — the Close/Reopen buttons likely need `finance_admin`/`admin`.
  `CURRENT_STATUS.md` §2 confirms period close is engine-enforced (postings into
  a closed period are refused at the hook level, not just the API), matching
  `UI.MD`'s "engine-level enforcement, not just UI state" note.

## SCR-023 — Budgets

- ✅ `Budget.{list,get}` — filters `fiscal_year`, `budget_type`
  (`monthly/quarterly/yearly`), `status`. No `Budget.create`/`.update` visible
  to `finance_user`.

## SCR-024 — Cash-flow Scenarios

- ✅ `endpoint.accounting.cash_flow_scenario_sources` — the one dedicated
  `endpoint.*` tool that matches this screen. This is a computed/simulation
  endpoint (matches `UI.MD`'s "non-posting timing simulation" description), not
  a plain entity CRUD tool — consistent with it living under `endpoint.*` rather
  than as `CashFlowScenario.list`.

## SCR-025 — Reports Catalogue

- ❌ No MCP tool found for a generic "reports catalogue" or the underlying P&L /
  Balance Sheet / Cash Flow Statement reports themselves. None of the 436 tools
  is named like `Report.*` or `endpoint.accounting.reports.*`. These are very
  likely REST-only report endpoints (`/api/reports/...`, matching the
  `not_yet_supported.cash_basis` note in `CURRENT_STATUS.md` §2 which literally
  references `/reports/sales-tax-liability?basis=cash`) — worth checking
  `/api/schemas` or `/docs` for a `reports` section specifically, since MCP
  doesn't seem to be the interface for this screen at all.

## SCR-026 / SCR-027 — Taxes List / New Tax

- ✅ `Tax.{list,get}` for read; `finance_user` does **not** get `Tax.create` per
  `tools/list` (schema permissions showed `finance_admin` only for
  create/write/delete). "Tax Type" column enum (`SALES_TAX, USE_TAX, TDS, CGST,
  UTGST, TCS, other`) matches the real `Tax.tax_type` enum exactly (it also
  includes `IGST, SGST, CESS, EXCISE, WITHHOLDING_1099` beyond what `UI.MD`'s
  screenshot happened to show).
- **Is Group Tax / Group Tax section** → ✅ `Tax.is_group` +
  `TaxGroup.{list,get}` (`TaxGroup` has `taxes` and `combined_rate` fields) —
  confirms `UI.MD`'s composite/group-tax capability claim.

## SCR-028 — Currencies

- ✅ `CurrencyConfig.list()` — fields `currency_code`, `currency_symbol`,
  `currency_name`, `exchange_rate`, `is_base` match `UI.MD` columns exactly.
  `ExchangeRate.{list,get}` is a **separate** entity (`currency_code`, `date`,
  `rate`, `base_currency`) for historical/dated rates — `UI.MD`'s "not yet
  evidenced: historical FX rates" claim may be worth re-checking against this
  entity specifically, since it exists in the schema even if the Currencies
  *settings* screen doesn't surface it.

## SCR-029 — Locations

- ✅ `Location.list()` — `city`, `state`, `gstin`, `is_primary` all real fields.

## SCR-030 — Reporting Tags

- ✅ `ReportingTag.list()` — `tag_name`, `is_mandatory`, `applies_to` (real
  field, confirmed enum-like values incl. `expenses/journals/bills/invoices/all`).

## SCR-031 / SCR-032 — Payments List / Detail

- ✅ `Payment.{list,get}` — **read-only** for `finance_user` (no create/update
  tool, matching `CURRENT_STATUS.md` §3). `type` (`pay/receive/internal_transfer`),
  `mode`, `total_allocated`/`unallocated` are real fields, confirming `UI.MD`'s
  "unified payment engine" and allocation-model observations. Actual payment
  *creation* happens through `PaymentMade`/`PaymentReceived` instead — `Payment`
  itself looks like a read-only unified view/ledger over both.

## SCR-033 — GST Filing / Returns (GSTR-1, GSTR-3B, GSTR-2A, GSTR-2B)

- ✅ `GSTReturn.list(return_type="GSTR-1"|"GSTR-3B"|"GSTR-2A"|"GSTR-2B"|"GSTR-9")`
  / `GSTReturn.get(id=...)` — one entity covers all five return types via the
  `return_type` enum; confirmed fields `taxable_amount`, `igst_amount`,
  `cgst_amount`, `sgst_amount`, `utgst_amount`, `cess_amount`,
  `net_tax_payable`, `filing_status`, `filed_date`.
- **Generate** (GSTR-1/3B) → ❌ No MCP tool found. `finance_user` gets
  `GSTReturn.list`/`.get` only; no `.create`/`.generate`-style tool appeared in
  our scope (schema permissions show `finance_admin` can create/write/delete/
  submit — likely a `finance_admin`-only action, REST or MCP).
- **Fetch from GSTN** (GSTR-2A/2B) → ❌ No MCP tool found anywhere in the 436 —
  no `endpoint.*.gstn` or similar. Matches `CURRENT_STATUS.md` §2: e-invoicing
  and several GST flows are explicitly documented as not fully implemented
  server-side, so this may not just be a permissions gap but a genuinely
  unbuilt integration (no live call to GSTN has ever been made, going by the
  locale response's own gap notes on the *US* tax-rate-service side — worth
  checking if the same "never called a live external endpoint" caveat applies
  here for GSTN too).

## SCR-034 — GST Filing / IMS Dashboard

- ✅ `Bill.list(ims_status="pending"|"accept"|"reject")` for the summary cards
  and table — `ims_status` is a real, confirmed `Bill` field (not a separate
  IMS entity). "Vendor / GSTIN / Invoice# / Taxable / Tax" columns are `Bill`
  fields joined with `Party` (via `vendor_id`).
- **Accept / Reject** → ⚠️ Inferred as `Bill.update(id=..., ims_status="accept"
  |"reject")`, but no dedicated `Bill.ims_accept`/`Bill.ims_reject` action tool
  was seen (unlike the named state-transition pattern used elsewhere, e.g.
  `DeliveryChallan.mark_delivered`) — worth confirming whether a plain
  `Bill.update` on `ims_status` is actually accepted, since `status` fields
  elsewhere in this platform are flow-gated rather than freely writable.

## SCR-035 — GST Filing / GST Payments

- ❌ **No dedicated `GSTPayment` entity exists anywhere in the 425-entity
  `/api/schemas` dump.** Challan Number / Amount / Payment Date / Bank Account
  most likely map to a generic `PaymentMade` or `JournalEntry` record tagged
  against a GST-liability `Account` (e.g. the `Input CGST` GL account seen in
  `UI.MD` SCR-019), or possibly a field group inside `GSTReturn` itself
  (`GSTReturn` doesn't show a payment sub-object in the schema dump we pulled).
  This needs a live sample GST-payment record to resolve — flagged as an open
  question rather than guessed.

## SCR-036 — GST Filing / Annual Returns (GSTR-9)

- ✅ `GSTReturn.list(return_type="GSTR-9")` / `.get()`.
- **Generate Summary** → ❌ No MCP tool found for `finance_user`; also,
  `CURRENT_STATUS.md` §2 confirms the GSTR-9 REST endpoint currently returns
  **HTTP 501** platform-wide (ticket GST-39) — this isn't just a permissions
  gap, generation is genuinely unimplemented right now regardless of role.

## SCR-037 / SCR-038 — e-Way Bills List / New

- ✅ `EWayBill.{list,get,create,update}`. Fields (`transaction_type`,
  `eway_bill_number`, `customer_gstin`, `vehicle_number`, `distance_km`,
  `transporter_id`, `generation_date`, `expiry_date`, `status`,
  `is_over_dimensional`) all confirmed real.
- **Generate / Activate** → ✅ `EWayBill.generate`, `EWayBill.activate` (named
  action tools, not plain field writes).
- `CURRENT_STATUS.md` §2 confirms distance-based validity (one day per 200km)
  is implemented, but NIC-portal generation, Part-A/Part-B split, and
  threshold-triggered auto-generation are **not** (ticket GST-29) — matches
  `UI.MD`'s "Not yet evidenced" list for this screen closely.

## SCR-039 — Bill Intake Review

- ✅ `BillIntakeEvent.{list,get}` — fields `kind`, `reason_code`, `source_state`,
  `lowest_confidence`, `fields_below_threshold`, `review_threshold`, `bill_id`,
  `bill_status`, `document_total`, `draft_total`, `total_variance` map closely
  to `UI.MD`'s "State / Lowest confidence / Fields needing review" columns.
- **Refresh queue / Add a document** → ✅ likely `AcctDocument.create` (has
  `document_type`, `file_url`, `vendor_id`, `linked_entity_type/id`,
  `amount`, `status`) feeding the intake queue, though the exact linkage to
  `BillIntakeEvent` creation wasn't independently traced.
- **Review this document / Accept / Reject** → ✅ dedicated `endpoint.*` tools
  exist specifically for this flow: `endpoint.accounting.bill_intake.queue`,
  `endpoint.accounting.bill_intake.extract`, `endpoint.accounting.bill_intake.accept`,
  `endpoint.accounting.bill_intake.reject` — this is the one screen in the
  whole inventory with a **purpose-built endpoint group**, not generic entity
  CRUD, which matches `UI.MD`'s emphasis on this being a distinct AP-automation
  workflow.
- `UI.MD`'s "no OCR engine" limitation is a deployment/config fact, not
  something visible in the tool schema itself — can't confirm or refute via
  `tools/list` alone.

## SCR-040 / SCR-041 — Manual Journals List / Detail

- ✅ `JournalEntry.{list,get}` — **read-only for `finance_user`** (confirmed in
  `CURRENT_STATUS.md` §3; only `admin`/`accountant` roles get create/write per
  the schema's permissions block). Fields `entry_type`, `journal_type`,
  `journal_entity_type`, `source_entity`, `source_id`, `narration`, `lines`,
  `total_debit`, `total_credit` are all real.
- `UI.MD`'s "narrations include source references" observation is explained by
  the real `source_entity`/`source_id` fields — journals genuinely do carry a
  back-link to whatever operational document generated them.
- `UI.MD`'s inconsistency finding (list shows non-zero Total Debit, detail
  shows ₹0.00 / no lines) can't be diagnosed further from the schema alone —
  `lines` is a real field so the data *should* be there; this looks like an
  actual UI rendering bug worth a `BugReport.create` once reproduced with a
  specific `JournalEntry.id` (see `postman/AgentSwitch.postman_collection.json`
  → REST API → File Bug Report, and note the real schema in
  `CURRENT_STATUS.md` §5 — only `description` is required).

---

## Capability-ID → tool cross-reference (for `UI.MD` §9's GAP matrix)

| Capability ID | Tool(s) |
|---|---|
| `AP-MDM-001` Vendor Master | `Party.{list,get,create,update}` (`contact_type="vendor"`) |
| `AP-MDM-002` Vendor Bank Details | `Party` fields `vendor_bank_account_number/name/code`, `beneficiary_name` |
| `AP-MDM-003` MSME Classification | `Party` fields `is_msme`, `msme_type`, `msme_no` |
| `AP-INTAKE-001..004` Supplier Doc Intake | `AcctDocument.create`, `BillIntakeEvent.{list,get}`, `endpoint.accounting.bill_intake.{queue,extract,accept,reject}` |
| `AP-BILL-001..003` Bill / Due Date / Outstanding | `Bill.{list,get,create,update}`, `Bill.open`, `Bill.submit` |
| `AP-PAY-001..003` Vendor Payments / Allocation / Reconciliation | `PaymentMade.{list,get,create,update,mark_paid,cancel}`, `Payment.{list,get}` (read-only) |
| `AP-CTRL-001` Transaction Locking | `TransactionLock.list` (read-only for `finance_user`) |
| `AP-CTRL-002` Period Close | `AccountingPeriod.list` (read-only for `finance_user`) |
| `TAX-MDM-001..002` Tax Master / Group Tax | `Tax.{list,get}`, `TaxGroup.{list,get}` |
| `TAX-MDM-003` GSTIN / PAN | `Party` fields `gst_no`, `pan`; `Location.gstin` |
| `TAX-LOC-001` Location GSTIN | `Location.{list,get}` |
| `TAX-TXN-001..003` CGST/SGST/Place of Supply | `Invoice`/`Bill` fields `taxes[]`, `place_of_supply` |
| `TAX-GL-001` Input GST GL Posting | `GLEntry.list` (filter/search on `account`) |
| `TAX-GST-001..007` GSTR-1/3B/2A/2B/IMS/Payments/GSTR-9 | `GSTReturn.list(return_type=...)` for read; **no generate/fetch/file tool found** for `finance_user` on any of these (see SCR-033/035/036) |
| `TAX-EWB-001..002` e-Way Bill | `EWayBill.{list,get,create,update,generate,activate}` |
| `ACC-GL-001..002` General Ledger / Voucher Linkage | `GLEntry.{list,get}` (read-only) |
| `ACC-JRN-001` Manual Journals | `JournalEntry.{list,get}` (read-only for `finance_user`) |
| `ACC-CUR-001` Currency Master | `CurrencyConfig.{list,get}`, `ExchangeRate.{list,get}` |
| `ACC-DIM-001` Reporting Tags | `ReportingTag.{list,get}` |
| `ACC-BUD-001` Budgets | `Budget.{list,get}` (read-only for `finance_user`) |
| `ACC-CF-001` Cash-flow Scenarios | `endpoint.accounting.cash_flow_scenario_sources` |
| `ACC-REP-001` Financial Statements | ❌ No MCP tool found — likely REST-only reports, not covered by `tools/list` at all |

## Cross-cutting gaps found while mapping (not in `UI.MD`)

1. **No PDF/Email/Share/Print tool exists for any entity.** Every document
   screen in `UI.MD` (Bill, Invoice, Payment Receipt, Retainer Invoice, Delivery
   Challan) lists these as UI actions; none appear in `tools/list`. If the
   agent ever needs to "send" or "print" something, that's a REST-only feature
   outside MCP's reach entirely — worth confirming with `/api/schemas`/`/docs`
   before assuming the agent can do this at all.
2. **No reports API surfaced over MCP** (`SCR-025`, `ACC-REP-001`) — Profit &
   Loss, Balance Sheet, Cash Flow Statement, and the dedicated Payables/Taxes
   report categories have no `tools/list` entry whatsoever.
3. **GST filing/generation/GSTN-fetch actions are read-only for `finance_user`**
   across the board (`SCR-033`, `034`, `035`, `036`) — our seat can read
   `GSTReturn` and `Bill.ims_status`, but every "do the filing" action either
   needs a different role or doesn't exist as an MCP tool yet. This directly
   affects what "Payables & Tax Agent" can autonomously do vs. what it can only
   surface for a human to action — relevant to `DESIGN.md`'s refusal-handling
   section and to the Week 1 gap report's "what can an agent do that the UI
   can't" question (answer, currently: less than hoped on the filing side).
4. **No `GSTPayment` entity** (`SCR-035`) — open question, not yet resolved.
