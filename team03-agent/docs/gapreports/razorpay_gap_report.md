# RazorpayX — Detailed Competitor Analysis

Deep-dive companion to [`gap_report.md`](gap_report.md), which covers all six
competitors at a summary level. This document walks **every RazorpayX screen and
feature observed**, explains what each one does, and states what it implies for the
Team 03 Payables & Tax Agent.

**Date of observation:** 2026-09-22
**Product:** RazorpayX (`x.razorpay.com`), account branded **"RazorpayX Lite"**
**Why RazorpayX:** it is the only competitor in our set we have seen running. Every
other entry in the main gap report is marketing copy.

---

## Evidence tiers — read this first

Not all observations are equally strong. This document tags each one:

| Tag | Meaning | Reliability |
|---|---|---|
| **[LIVE]** | Seen in the actual logged-in account | Strongest — this is what the product does today |
| **[DEMO]** | Seen in RazorpayX's own marketing/product video | Weaker — vendor's chosen happy path, may be outdated or aspirational |

**This distinction is not pedantic — it materially changed our conclusions.**
RazorpayX's demo material still showcases a TDS payments module that the live
account says has been **discontinued**. An earlier version of the main gap report
treated demo footage as verified product behaviour and drew the wrong conclusion
from it. Marketing shows the product as the vendor wishes it were.

---

## 1. Payouts — the core of the product

### 1.1 Single Payouts **[LIVE]**

*Screen: Payouts → Single Payouts*

Individual payments to a beneficiary. The screen carries a feature called **Payout
Processing Stages**, which surfaces where a payment is in the banking pipeline:

- **"Processing within TAT"** — the payout is moving normally inside the expected
  turnaround time.
- **"Slightly delayed on bank's end"** — *"Occurs during holidays or with Grameen
  Banks. We are actively following up with the bank on this."*

**What this actually means:** RazorpayX is not recording that a payment happened —
it is *executing* the payment and tracking it through the banking rails, including
distinguishing "we're fine" from "the receiving bank is slow." That is an
operational capability, not a bookkeeping one.

Quick filters: All Payouts · Scheduled for next 2 days · Queued Payouts — so
payouts have a forward schedule and a queue, not just a history.

**Implication for us:** AgentSwitch's `PaymentMade` records that a payment
occurred. There is no tool in the 436 MCP tools that initiates a transfer, and
no execution state to track even if there were. Our agent can decide *that* a
vendor should be paid; it cannot pay them, and cannot tell you whether a payment
is stuck.

### 1.2 Bulk Payouts **[LIVE]**

*Screen: Payouts → Bulk Payouts*

Batch uploads: *"A batch is the group of payouts uploaded in bulk. Once a batch is
created, they will show up here."* Filters: All / Pending.

**What this means:** vendor payment runs — paying 200 vendors from one uploaded
file — are a first-class workflow, not 200 separate actions.

**Implication for us:** the classic AP "payment run" has no equivalent in
AgentSwitch. An agent settling many bills would have to create `PaymentMade`
records one at a time, with no batch identity to track or reverse as a unit.

### 1.3 Payout Links / Bulk Payout Links **[LIVE]**

*Screen: Payouts → Payout Links*

*"Send money to recipients without their account details. Works perfectly for cash
on delivery, deposit refunds, one time payments etc."*

**What this means:** you can pay someone whose bank details you do not have — the
recipient supplies them by clicking a link. This solves vendor-onboarding friction
for one-off payees.

**Implication for us:** no equivalent. Not a core AP-audit gap, but relevant to the
"vendor dispute resolution" scenario the brief mentions — refunding a vendor
without holding their bank details is impossible in AgentSwitch.

### 1.4 Tally Payouts **[LIVE]**

*Screen: Payouts → Tally Payouts*

A dedicated payout path for Tally, India's dominant SME accounting package.

**Implication for us:** AgentSwitch has no Tally integration. For Indian SMEs, Tally
compatibility is often the deciding purchase criterion — most competitors in our
set list Tally first among integrations.

---

## 2. Vendor Payments — the AP module

### 2.1 The stated flow **[DEMO]**

RazorpayX describes Vendor Payments as: *"Auto-pull details from invoices. Schedule
and pay invoices. Automate and simplify TDS payments."*

The four-step flow: **Upload Invoice → Track Invoices → Pay Invoices → TDS Payments**

This is the same conceptual pipeline as our seat's mandate, with one difference: it
terminates in *paying* — both the vendor and the tax authority.

### 2.2 Track Invoices **[DEMO]**

Invoice register with columns: Invoice Date · Vendor · Amount · Status · Due On ·
Description. Statuses observed: **Unpaid, Processing, Scheduled, Paid, Cancelled**.
Overdue due-dates are flagged with a red clock icon.

**What this means:** a "Processing" status distinct from "Paid" only exists if
payment is asynchronous and executed in-product. "Scheduled" implies future-dated
payment instructions.

**Implication for us:** AgentSwitch's `Bill` has a `BillFlow` state machine with
named transitions (`Bill.open`, `Bill.submit`, `Bill.record_partial_payment`,
`Bill.record_full_payment.*`). Conceptually comparable for *tracking*, but with no
"Processing" equivalent, because nothing is being executed.

### 2.3 Pay Invoices — approval chain **[DEMO]**

The most significant demo observation. A vendor payment (ACME Corp, ₹10,000) shows a
timeline:

```
Issued on              12 FEB 2020, 08:10 PM
Added on               12 FEB 2020, 08:10 PM
Processing             08:10 PM
  Payout approval pending    13 FEB 2020, 05:34 PM   On Finance L2
Unpaid  Finance L2     08:10 PM
  Payout rejected by         On Finance L2
```

Actions available: **PAY**, edit, cancel.

**What this means:** a **named approval level** ("Finance L2"), an approve/reject
decision recorded against that level, and a timestamped audit trail of the whole
lifecycle including the rejection. This is a genuine approval *chain*, not a
single boolean gate.

⚠️ **[DEMO] caveat:** this was not confirmed in the live account. An earlier version
of the main gap report recorded it as verified, which was an overreach.

**Implication for us:** AgentSwitch has `approval_status` with four values
(`not_required` / `pending_approval` / `approved` / `rejected`) plus
`Bill.approval.submit` and `Invoice.approval.submit` tools. What is missing: named
approver levels, routing rules, and a per-decision audit trail. Our agent can move
a bill to `pending_approval` but cannot say *who* must approve it, and there is no
recorded history of who rejected what.

### 2.4 Import: Purchase Orders | Items | **GRNs** **[LIVE]**

*Screen: Vendor Payments → Import*

Three import tabs. The third is **GRNs** — Goods Receipt Notes.

**What this means:** RazorpayX can ingest the receipt-of-goods document, which is
the third leg of three-way matching (PO ↔ GRN ↔ Invoice). Without a GRN you can
only two-way match (PO ↔ Invoice) and cannot verify that what was billed was
actually *received*.

**Implication for us — this is the sharpest gap in the entire analysis.**
AgentSwitch has **no goods-receipt entity anywhere in its 425-entity schema**
(verified by grepping every entity name; only unrelated `EsignConsentReceipt` and
`FormConsentReceipt` matched). `Bill.purchase_order_id` links a bill to a PO, so
two-way matching is possible — but three-way is **structurally impossible**, not
merely unbuilt. This is the one gap our agent categorically cannot orchestrate
around: you cannot match against a document type that does not exist.

### 2.5 Vendors / Vendor Balances / Advances **[LIVE]**

Sub-navigation shows Advances, Invoices, Vendors → Vendor Balances, Import.

**Vendor Advances** appear as a distinct concept with their own report type,
meaning prepayments to vendors are tracked and presumably offset against future
invoices.

**Implication for us:** AgentSwitch has `VendorCredit` (with `apply_to_bill`) which
covers credit notes, and `PaymentMade.unused_amount` which covers unapplied
payments — so advance/prepayment handling exists in some form. Roughly at parity.

---

## 3. Tax Payments — and the retreat from it

This section produced the most strategically important finding in the analysis.

### 3.1 What the demo advertises **[DEMO]**

A **Tax Payments** screen: *"Track and manage Vendor related TDS Payments."*
Itemised by TDS section code, grouped by month:

```
195 J  Commission/Brokerage       ₹4,80,000.00   UNPAID
195 J  Resident Contractor        ₹11,089.00     PAID
195 J  Rent of Land or Building   ₹11,089.00     PAID
195 J  Professional Service       ₹11,089.00     PAID
```

### 3.2 What the live account actually says **[LIVE]**

Three withdrawal notices, one per tax type:

**Manual TDS Payments:**
> *"Important Update: Manual TDS payments have been discontinued due to regulatory
> issues. Auto TDS payments on your invoices will continue as usual."*

The page still describes the intended capability — *"Initiate TDS payments from the
dashboard. Receive a CRN and CIN once payment is complete"* — with a "Setup TDS
Payments" button, but the feature is gated behind that notice.

**Advance Tax:**
> *"We regret to inform you that Advance Tax payments via RazorpayX are no longer
> available, due to unavailability of automated payments APIs from our partner
> bank."*

The page is otherwise empty.

**GST Payments:**
> *"We regret to inform you that GST payments via RazorpayX are no longer available,
> due to unavailability of automated payments APIs from our partner bank."*

All three carry warning triangles in the sidebar navigation.

### 3.3 Why this matters more than the feature itself

Two distinct reasons are given, and both generalise beyond RazorpayX:

1. **"Regulatory issues"** (manual TDS) — a fintech intermediating statutory tax
   payments attracts regulatory attention.
2. **"Unavailability of automated payments APIs from our partner bank"** (GST,
   advance tax) — a non-bank platform depends on a partner bank's rails, and those
   rails were withdrawn.

**Implication for us — this reframes a gap we were about to chase.** An earlier
version of this analysis listed TDS/GST remittance as a Medium-priority gap for
AgentSwitch to close. But the best-capitalised payments company in the comparison
set just *exited* that exact capability, for reasons that would apply to
AgentSwitch equally or worse. The defensible target is **computing and tracking the
liability** (what is owed, what is unclaimed, what is overdue) — not moving the
money. Notably, "Auto TDS payments on your invoices will continue" — so deduction
at source survived while discretionary remittance did not.

This is a case where a competitor gap analysis produced a *negative* recommendation:
do not build this.

---

## 4. Money movement and reconciliation

### 4.1 Account Statement **[LIVE]**

*Screen: Account Statement (URL: `/ledger?balance_id=…`)*

Tabs: All / Credit / Debit. Filters: **Date Range, Payment Method, Source, Contact
Type, Payout Purpose**. An **"Automate Accounting"** action sits top-right.

*"You can view all credit and debit transactions for this account here. Once a
payout is processed, related debit transactions will show up here as well."*

**What this means:** a real bank-account ledger, where a payout automatically
produces the corresponding debit. The filter on **Payout Purpose** implies payouts
carry a business-purpose classification useful for categorisation.

**Implication for us:** AgentSwitch has `BankAccount`, `BankTransaction`,
`BankRule`, and `BankTransaction.match_voucher` — genuinely comparable
reconciliation primitives, and ours are agent-callable over MCP. **This is an area
where we are at or above parity.** The difference is that RazorpayX's ledger is the
actual account; ours reconciles an external one.

### 4.2 Contacts **[LIVE]**

*"Contacts are beneficiaries to whom payouts are made."*
Quick filters: **All Contacts / Vendors / Employees / Customers**. Import Contacts
supported.

**What this means:** one beneficiary master typed by relationship, rather than
separate vendor and customer tables.

**Implication for us:** this is **the same architecture as AgentSwitch's `Party`**,
which uses `contact_type` (`customer` / `vendor` / `both`) plus a `roles[]` child
table carrying `role` / `since` / `active`. Ours is arguably richer, since it tracks
role history with effective dates. **Parity, if not a slight edge to us** — worth
noting because the main gap report should not claim the unified-party model as a
differentiator.

### 4.3 Cashflow Insights **[LIVE]**

*Screen: Insights*

Period selector (Past 30 Days, with explicit from/to). Overview cards: **Payouts
Volume, Number of Payouts, Inflow Volume, Number of Inflows**, plus Account
Balance. **Payout Trends** charted Daily / Weekly / Monthly with a metric selector
and CSV export. Shows a "Updated N mins ago" freshness stamp.

**What this means:** historical cash analytics — what went out, what came in, how
that is trending.

**Implication for us:** AgentSwitch has `endpoint.accounting.cash_flow_scenario_sources`,
which is a *forward-looking simulation* ("what if customers pay 15 days late"), a
genuinely different and arguably more sophisticated tool. What we lack is the
backward-looking analytics. Note also that **no reports API is exposed over MCP at
all** — so an agent cannot read P&L, balance sheet, or cash-flow statements; those
exist only as REST endpoints (`/api/accounting/reports/*`).

### 4.4 Reports **[LIVE]**

*Screen: Reports*

Generate a report by type and period. Available types:

- Account Statement
- Payouts
- Vendor payments
- Payouts on Vendor Payments
- Purchase Orders
- Vendor Advances
- Vendor Invoices V2
- Fund Account Validation report

Note: *"Report generation can take up to 10 min. Try emailing instead."*

**The CA feature:** *"Let Your CA Download These Reports — CA can download reports
without troubling you! No access to your RazorpayX account except [reports]."*

**What this means, and why it is clever:** a scoped external-accountant role. The
chartered accountant gets exactly the reports they need and nothing else — no
access to payouts, balances or the ability to move money. In India, where the CA
relationship is central to SME compliance, this removes a real friction point
(sharing a login) and a real risk.

**"Fund Account Validation report"** implies penny-drop bank account verification —
confirming a vendor's account is valid and belongs to them before paying it. This
is a fraud control AgentSwitch has no equivalent for.

**Implications for us:**
- **No scoped external-accountant role** in AgentSwitch that we found. Roles are
  internal (`finance_user`, `finance_admin`, `accountant`, `auditor`) and are not
  a shareable, report-only external grant.
- **No bank account validation** — `Party` stores `vendor_bank_account_number`,
  `vendor_bank_name`, `vendor_bank_code` but nothing validates them. Paying a
  wrong/fraudulent account is a classic AP fraud vector, and it is unguarded.
- Notably, **no tax/GST report** appears in RazorpayX's list — consistent with
  their retreat from tax (§3).

---

## 5. Platform-level capabilities

### 5.1 Embedded AI assistant **[LIVE]**

*Screen: Home*

> **"How can I help you?"**
> *"Are any of my payouts stuck in processing?"*
> Quick actions: **Create & check on Payouts · How's my cash looking? · Help me pay
> vendors** · file upload supported.

**What this means:** conversational natural-language access over payments data,
including an action-oriented prompt ("Help me pay vendors") that implies the
assistant can *initiate* work, not just answer questions.

**Implication for us — this corrected an overclaim.** An earlier version of the main
gap report asserted that a native agent capability was unique to AgentSwitch, with
a flat "no" across all six competitors. That was wrong. What survives as a
differentiator is narrower and more specific:

| | RazorpayX | AgentSwitch |
|---|---|---|
| Chat assistant over the data | ✅ | ✅ ("Ask Agent" in UI) |
| Agent work modelled as queryable records | unknown (not visible from outside) | ✅ `AgentJob`, `AgentSession`, `AgentTask`, `AgentEscalation`, `AgentMemory`, `AgentRunbook`, `AgentSkill` |
| Forensic replay of agent actions | not stated | ✅ `AgentLedgerSeal`, `endpoint.job_ledger.{forensics,verify,replay}` |
| Documented external agent API | not stated | ✅ MCP, JSON-RPC 2.0, 436 tools |

Honest caveat: we see RazorpayX's assistant only from the outside. We do not know
what it records underneath, so "unknown" is the correct entry, not "absent."

### 5.2 Sandbox / test mode **[LIVE]**

The account runs in test mode with a **Test balance (₹0.00)**, an "Add test balance"
action, and a banner: *"These are test payouts and do not affect the actual
balance. They are used only for the purpose of integrating events."*

**What this means:** you can rehearse a payment, and integrate against webhooks,
without moving real money.

**Implication for us — this is a real risk we had not flagged.** AgentSwitch's
Suryodaya ledger is **shared live with Teams 01 and 02**. There is no sandbox. Our
agent's job involves mutating records (holding duplicate bills, submitting for
approval), and there is nowhere to rehearse a write before doing it for real — and
any mistake is immediately visible to two other teams. For an autonomous agent
that writes, the absence of a test environment is arguably a bigger operational
problem than any single missing feature.

### 5.3 Payroll **[LIVE]**

A Payroll module sits in the main navigation.

**Implication for us:** out of Seat 03's scope (and `SalarySlip` is explicitly a
prohibited entity for our seat), but worth noting RazorpayX spans AP + payroll +
tax in one product.

---

## 6. Consolidated scorecard

| Capability | RazorpayX | AgentSwitch | Verdict |
|---|---|---|---|
| Payout execution over bank rails | ✅ LIVE | ❌ records only | **Gap** |
| Bulk payment runs | ✅ LIVE | ❌ | **Gap** |
| Payout stage tracking | ✅ LIVE | ❌ | **Gap** |
| Payout links (no bank details needed) | ✅ LIVE | ❌ | Gap (minor for our seat) |
| GRN import → 3-way matching | ✅ LIVE | ❌ **no GRN entity exists** | **Gap — structural, cannot be orchestrated around** |
| Bank account validation (penny-drop) | ✅ LIVE (report) | ❌ fields stored, never validated | **Gap — fraud control** |
| Scoped CA / external-accountant access | ✅ LIVE | ❌ | **Gap** |
| Sandbox / test environment | ✅ LIVE | ❌ shared live ledger only | **Gap — operational risk** |
| Historical cashflow analytics | ✅ LIVE | ⚠️ forward simulation only; no reports over MCP | Partial gap |
| Tally integration | ✅ LIVE | ❌ | Gap (market-relevant for Indian SMEs) |
| Multi-level named approval | ✅ DEMO | ⚠️ single gate, no levels/history | Gap (weaker evidence) |
| TDS per-section tracking | ⚠️ DEMO, **manual discontinued** | ❌ (GST-18) | Gap, but **do not chase remittance** |
| GST payment / remittance | ❌ **withdrawn** | ❌ | Neither — market signal |
| Advance tax payment | ❌ **withdrawn** | ❌ | Neither — market signal |
| Bank reconciliation primitives | ✅ LIVE | ✅ `BankRule`, `match_voucher`, agent-callable | **Parity** |
| Unified beneficiary/party master | ✅ LIVE | ✅ `Party` + `roles[]` with history | **Parity / slight edge to us** |
| Vendor advances / credits | ✅ LIVE | ✅ `VendorCredit`, `unused_amount` | **Parity** |
| Conversational AI assistant | ✅ LIVE | ✅ "Ask Agent" | **Parity** |
| Agent work as queryable records | unknown | ✅ full `Agent*` entity family | **Our edge** |
| Agent-action forensics / replay | not stated | ✅ job ledger | **Our edge** |
| Documented agent API (MCP) | not stated | ✅ 436 tools | **Our edge** |
| Dual jurisdiction (India + US) | ❌ India-only | ✅ locale-driven | **Our edge** |

---

## 7. What Team 03 should take from this

1. **Stop treating "they have X, we don't" as automatically actionable.** The TDS/GST
   remittance finding shows a capability a competitor *removed*. Gap analysis has to
   distinguish "we're behind" from "nobody can do this sustainably."

2. **The GRN absence is the one hard blocker.** Everything else in the gap column is
   something our agent could partially bridge through orchestration. Three-way
   matching cannot be — it needs a schema change, and it should be the top platform
   ask.

3. **Two unglamorous gaps deserve more attention than they've had:** bank account
   validation (an unguarded fraud vector directly relevant to a Payables & Tax
   agent) and the absence of a sandbox (we mutate a live ledger shared with two
   other teams, with no rehearsal environment).

4. **Our differentiators are narrower than claimed, but real.** Not "we have AI and
   they don't" — they do. It is that agent work is *modelled as data* here
   (`AgentJob`, `AgentEscalation`, job-ledger forensics) and exposed over a
   documented MCP API. That only becomes an actual advantage once `run_agent.py`
   uses those primitives, which it currently does not.

5. **Verify before claiming.** Checking one competitor properly cost us two claimed
   advantages and one false gap. The other five have not had that scrutiny.
