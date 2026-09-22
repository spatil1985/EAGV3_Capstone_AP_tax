# Gap Report — AgentSwitch (Team 03 seat) vs. Mysa

**Team 03 · Suryodaya Precision Works (India) · 2026-09-21**

Scope: one competitor, Mysa (mysa.io), against AgentSwitch as seen from our seat
(`finance_user`, 436 MCP tools). `gap_report.md` is the six-vendor survey; this
is the head-to-head answering three questions:

1. What do they do that we do not?
2. Which of those gaps can an agent close with the tools our seat already has?
3. What can an agent do that their product cannot?

## Evidence and its limits

| Side | Source | Confidence |
|---|---|---|
| Mysa | Public pages fetched 2026-09-21: `mysa.io`, `/ai-scan`, `/accounts-payable`, `/bill-pay`, and the "Top AP Automation Tools for India" blog | **Vendor marketing.** Not tested against a live account. |
| AgentSwitch | `CURRENT_STATUS.md` and `screen_api_mapping.md`: real logins, `/api/schemas`, MCP `tools/list`, real records (snapshot 2026-09-20/21) | Verified against the live instance |

**The linked API page could not be read.** `/docs` and the `tax_rate_service`
endpoint return `401 Authentication required` without a token, and no
credentials are set in this environment. What we know about it comes from the
platform's own `not_yet_supported` list in `CURRENT_STATUS.md` §2: `tax_rate_service`
is a **US-side** feature (Avalara/TaxJar wired but never called against a live
sandbox). It is out of scope for the India seat and irrelevant to Mysa, which is
India-only. It appears here only in Q3, as an example of a US capability Mysa
has no equivalent for.

Mysa's own pages are inconsistent: the AI Scan page says "30+ validation
checks", while the AP page and blog say "22+". We use "22+" and note the
discrepancy. "Not stated" means the pages we fetched did not mention it. It does
not mean Mysa lacks it.

---

## Q1. What Mysa does that we do not

| # | Mysa capability (vendor-claimed) | AgentSwitch today | Gap type |
|---|---|---|---|
| 1 | **AI Scan / OCR**: 99% claimed accuracy, handwritten bills at 95%, 22+ languages, trained on 10,000+ Indian bills; extracts GSTIN, PAN, invoice no., line items, due date | No OCR engine in this deployment. `BillIntakeEvent` / `endpoint.accounting.bill_intake.*` has confidence scoring and human review but cannot read scanned images | Platform |
| 2 | **22+ automated validations at intake**: duplicates, amount mismatch, bill-number change, outdated invoice, vendor mismatch, total mismatch, credit-note detection | None run natively. No duplicate check on `Bill` or `Invoice`. This is our Core Challenge Prompt | Platform (but see Q2) |
| 3 | **3-way match (PO ↔ GRN ↔ Invoice)**, stated explicitly | `PurchaseOrder` exists (`PurchaseOrder.make.Bill`). **No GRN entity anywhere in the 425-entity schema** | Structural |
| 4 | **Vendor PAN/GSTIN validation, Udyam (MSME) verification, KYC at onboarding** | `Party` stores `gstin`/`pan`/`is_msme`/`msme_no` as text. Nothing validates them | Platform |
| 5 | **Automated TDS (s.194C) and GST calculation, RCM applicability detection** | `tds_amount` field and GL posting legs exist. No automatic deduction by section/threshold. No 26Q/27Q filing (GST-18). RCM: no detection | Platform |
| 6 | **Multi-level approvals, up to 100 levels**, by department/amount/cost-centre; role, vendor and daily spend caps | Single approve/reject gate (`approval_status`). No hierarchy, no spend caps | Platform |
| 7 | **Payment execution across 15+ banks** (Axis, HDFC, ICICI, Yes, SBI, Kotak, IDFC…) from one multi-bank console; UTR-linked vendor ledger | `PaymentMade` records that a payment happened. No tool initiates a transfer | Platform |
| 8 | **ERP connectors**: Tally, Zoho Books, ERPNext, NetSuite, Dynamics, SAP | None. AgentSwitch is itself the ledger, so this is a different category, not a missing feature | Category |
| 9 | **Bill intake via Slack, WhatsApp, email**; Keka/Odoo/PetPooja/UrbanPiper connectors | Email and calendar endpoints exist on our seat. No Slack/WhatsApp intake. No HR/POS connectors | Platform |
| 10 | **Auto-reconciliation** of bills, payments and bank statements | `BankRule`, `BankTransaction.match_voucher` exist. Not confirmed as auto-run | Partial |
| 11 | **Auto GST-branch tagging** from the GSTIN on the invoice; per-line cost-centre allocation | Not evidenced in the schema we've read | Unverified |
| 12 | **Custom dashboards and reports** | No reports API over MCP (P&L, Balance Sheet, Cash Flow not agent-readable) | Platform |

**Where Mysa does *not* obviously lead:** its pages don't mention GSTR-2B/ITC
reconciliation, e-invoicing (IRN), GST return filing, or TDS return filing. We
lack those too (GST-28, GST-39, GST-18), so they are not a gap *versus Mysa*. They
matter because Clear and CashFlo do claim them (see `gap_report.md`).

---

## Q2. Which gaps an agent can close with tools our seat already has

Our seat: `Bill.*`, `Invoice.*`, `Party.*`, `PurchaseOrder.*`, `PaymentMade.*`,
`GSTReturn.{list,get}`, `BankRule` / `BankTransaction.match_voucher`,
`AgentEscalation.{list,get,create,update}`, `AgentTodo.*`, `Notification.*`,
`AgentTask.*`, `AgentSession.*`, `BugReport.create`, plus the model's own
reasoning and our local scripts.

**Verdict key:** ✅ close it · 🟡 close the *decision*, not the *enforcement* · ❌ can't

| # | Gap | Verdict | How, and where it stops |
|---|---|---|---|
| 2 | Intake validations (duplicate, amount mismatch, bill-no. change, vendor mismatch, total mismatch) | ✅ | `Bill.list` / `Invoice.list` + `scripts/invoice_matcher.py` (exact and near-duplicate grouping by vendor/amount/date/number-similarity). Flag via `AgentEscalation.create`. This is the highest-value gap and the one we are assigned. **Caveat:** `invoice_matcher.py` and `playbooks/duplicate_audit.md` still use fields and tools that don't exist (`hold_payment`, `AgentMessage.create`, `vendor_id` on `Invoice`). Fix per `CURRENT_STATUS.md` §7 |
| 10 | Bill ↔ payment ↔ bank reconciliation | ✅ | `BankTransaction.match_voucher` is agent-callable. Needs a test pass to confirm it works for `finance_user` and not only exists in `tools/list` |
| 1 | OCR / AI scan | 🟡 | The model can read an invoice image or PDF itself. What is unconfirmed is whether any seat tool accepts an attachment and creates a `Bill` from extracted fields (`bill_intake` or `Bill.create`). If yes, the agent is the OCR. We have not verified that path |
| 4 | Vendor PAN/GSTIN validation | 🟡 | Format and GSTIN checksum validation is pure code (`scripts/`), and can flag malformed IDs and PAN↔GSTIN mismatch. **Live registry verification** (is this GSTIN active? is this Udyam number real?) is ❌: no lookup tool exists |
| 5 | TDS / GST / RCM checks | 🟡 | Recompute expected TDS and GST from the invoice and flag disagreement. **Use item-level `cgst/sgst/igst_amount`, never `taxes[]` or the `Tax` master** (three filed bugs, `CURRENT_STATUS.md` §7a/§9). Can write a corrected `tds_amount` via `Bill.update`. Cannot deposit TDS or file 26Q |
| 3 | 3-way match | 🟡 | **2-way (PO ↔ Bill) yes**: `PurchaseOrder.list` vs `Bill.list`. The GRN leg is ❌: no receipt record exists, and an agent must not invent one. Report it as unverifiable rather than passing it |
| 6 | Multi-level approval | 🟡 | The agent can *route*: a chain of `AgentTodo` / `AgentEscalation` per amount tier, plus `Bill.approval.submit`. It cannot *block* a payment, because `PaymentMade.create` is not gated by our chain. Advisory only |
| 7 | Payment execution | ❌ | No transfer-initiation tool. The agent can prepare a payment list and call `PaymentMade.mark_paid` after a human pays, which is bookkeeping, not payment |
| 8 | ERP connectors | ❌ | Not applicable; a different product category |
| 9 | Intake via Slack/WhatsApp | ❌ | No such tools. Email endpoints exist on our seat but are out of the AP/Tax brief. Unverified whether reading them is in scope |
| 12 | Dashboards / reports | 🟡 | No reports API, but the agent can aggregate from `list` calls (e.g. GST liability from `GSTReturn`, ITC at risk from `Bill.itc_eligibility` + `ims_status`). Costlier per answer than a real report endpoint |
| 4b | MSME 45-day tracking | ✅ | Join `Party.is_msme` to `Bill.due_date`; alert via `Notification.create` / `AgentEscalation.create`. Mysa mentions MSME verification, not deadline tracking, so this arguably exceeds them |

**Scorecard:** of 12 gaps, **3 close fully** (2, 10, 4b), **6 close the analysis
but not the enforcement** (1, 3, 4, 5, 6, 12), **3 can't be closed** (7, 8, 9).
Everything in ❌ or the enforcement half of 🟡 is a platform gap that needs
AgentSwitch engineering, not a smarter agent.

**The honest ceiling:** an agent on our seat can make AgentSwitch *detect* as
well as Mysa but cannot make it *act* as Mysa does. Mysa can stop a payment;
we can raise an escalation and hope a human reads it. Our seat is read-mostly
(`finance_user` cannot post journal entries) and has no payment rail.

---

## Q3. What an agent can do that Mysa cannot

Mysa's AI runs inside a fixed intake pipeline: scan, validate, route,
pay, post to your ERP. It is a product with a UI and connectors. An agent on
AgentSwitch works *inside* the ledger with open-ended tools. Claims are tagged
**proven** (done, evidence exists), **buildable** (tools exist, we haven't built
it yet), or **structural** (true of the platform whether or not we build it).

1. **Audit the platform's own data, not just the incoming document.** *Proven.*
   Investigating one odd Tax Summary report, we found three defects and filed
   them (`CURRENT_STATUS.md` §9): 100 US `TaxJurisdiction` rows on the India
   company; 67 of 100 `Tax` rows with `is_group=false` yet carrying `group_taxes`
   children; a report showing ₹4,991.76 where the source documents total
   ₹62,402.95. Mysa validates the bill *in front of it* and pushes to your ERP,
   with no view of the ledger's integrity afterwards.
2. **Open-ended, cross-entity questions in plain language.** *Buildable.* "What's
   our MSME exposure this month, and which of those vendors also have
   unclaimed ITC?" spans `Party`, `Bill`, `GSTReturn`. That is one agent
   loop, not a configured dashboard. Mysa's reports are what Mysa ships.
3. **Reconcile the two AP representations.** *Buildable.* AgentSwitch holds
   payables as both `Invoice(direction=payable)` (165) and `Bill` (101). A
   duplicate can hide *across* them, where no single-entity check looks. This is
   a platform quirk that creates a detection surface Mysa's model doesn't
   have.
4. **ITC-at-risk against GSTR return data.** *Buildable.* Join
   `GSTReturn.net_tax_payable` to `Bill.itc_eligibility` / `ims_status` and
   pre-screen IMS accept/reject. Mysa's pages don't mention 2B/ITC.
5. **Two jurisdictions in one system.** *Structural.* The same agent serves
   Suryodaya (India, GST) and Keystone (US, sales tax) by flipping
   `AGENTSWITCH_BASE_URL`, and the US side has its own tax-rate-service. Mysa is
   built for India only.
6. **Auditable agent actions.** *Structural.* `AgentEscalation`, `AgentSession`,
   `AgentTask`, and `endpoint.job_ledger.{forensics,verify,replay}` make what the
   agent did and why replayable. **Not yet realised in our code:**
   `run_agent.py` doesn't create an `AgentSession` or call `AgentEscalation.create`
   (`gap_report.md` §3.2 item 6).
7. **Rules that change the same day.** *Buildable.* A playbook is a markdown file
   (`playbooks/*.md`); new vendor-specific or amount-tier rules are an edit, not
   a vendor roadmap request.

**Caveats:** items 2–4 and 6 are capability, not results; we have not yet run
them end to end. Only item 1 has shipped evidence. Mysa may do more than its
marketing pages say, and we've tested none of it.

---

## Priorities for Team 03

Ordered by score value against our mandate (duplicate-payment detection):

1. **Fix the duplicate-audit path** (Q2 #2): correct the playbook and matcher to
   real fields and `AgentEscalation.create`, then cover both `Invoice(payable)` and
   `Bill` (Q3 #3). This is the one gap where the agent fully matches Mysa.
2. **Wire the run to `AgentSession` / `AgentTask` / `AgentEscalation`** (Q3 #6), so
   the platform advantage becomes a demonstrable one.
3. **Add MSME 45-day and ITC-at-risk joins** (Q2 #4b, Q3 #4): cheap, and Mysa
   doesn't claim either.
4. **Format-level GSTIN/PAN checks** in `scripts/` (Q2 #4).
5. **Verify `BankTransaction.match_voucher` and the bill-intake attachment path**
   (Q2 #10, #1), which would upgrade two rows.

**Not ours to fix; name them and move on:** payment rails, GRN entity, multi-level
approval enforcement, OCR engine, GSTN connectivity, reports API.
