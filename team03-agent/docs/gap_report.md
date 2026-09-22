# Gap Report — AgentSwitch vs. Indian AP/GST Automation Platforms

**v4 — 2026-09-22: RazorpayX re-examined; v3's evidence tiers were wrong.**
v1 listed only what competitors have that we lack. v2 added the reverse direction, a
feature matrix, and recommendations split by who can act. v3 claimed RazorpayX was
"verified first-hand" — **that was partly wrong, and v4 corrects it.** Several v3
screenshots were RazorpayX *marketing videos*, not the running account, and the live
account contradicts them on tax payments. See "RazorpayX re-examined" below.

AgentSwitch's capabilities are not vendor claims — they're pulled from
`../CURRENT_STATUS.md` and `screen_api_mapping.md`, built from real logins, real
`/api/schemas` and MCP `tools/list` calls, and real sample records against the live
Suryodaya instance.

**Competitor evidence now has three tiers, and the matrix marks each cell:**

| Tier | Meaning |
|---|---|
| **L** — live account | Seen working in a real logged-in RazorpayX account |
| **D** — vendor demo | Seen in RazorpayX's own product video/marketing walkthrough. Shows a real UI, but is the vendor's chosen happy path and may not reflect current availability |
| *(unmarked)* | Vendor-stated text claim from public research (Clear, Mysa, CashFlo, OPEN Money, Kodo/EnKash) |

A **D** is weaker than an **L**: the live RazorpayX account shows three tax features
that its own demo material still advertises have since been **withdrawn**. Treat
vendor demos as aspirational, not current.

Where a competitor's capability is unverified either way, this report says "not
stated" rather than guessing absence.

⚠️ **Tier caveat:** the RazorpayX account inspected is branded **"RazorpayX Lite"**.
Some absences may be plan-gating rather than product gaps.

## Competitors reviewed

| Platform | Core strength | Key integrations | Target segment |
|---|---|---|---|
| **Clear (ClearTax)** *(sources verified)* | GST/ITC reconciliation & e-invoicing. **Operates GSTN-approved private IRP 4** — a regulatory moat, not just a feature set | SAP, Oracle, Tally, NetSuite, Dynamics, Zoho, Busy, JDE | Mid-Large enterprises & CAs |
| Mysa | AI invoice scan with 22+ Indian tax checks (GST/TDS/RCM) | Zoho Books, Tally, ERPNext | Startups & SMBs |
| CashFlo | 6-way matching, fraud prevention & supply-chain financing | SAP, Oracle, MS Dynamics | Mid-market & large enterprises |
| **RazorpayX S2P** *(live account inspected)* | Vendor payout rails & bulk payouts. **Actively withdrawing from tax remittance** — GST, Advance Tax and manual TDS payments all discontinued | Tally, Zoho Books | Startups & growth businesses |
| OPEN Money | Connected banking + AP automation + MSME tracking | Tally, Zoho, Dynamics, NetSuite | SMBs & mid-market |
| Kodo / EnKash | Unified corporate cards + AP invoice workflows | Tally, QuickBooks, NetSuite | Startups & mid-market |

> **Full module-by-module analysis of Clear: [`clear_gap_report.md`](clear_gap_report.md).**
> Its claims were fetched and adversarially verified on 2026-09-22 (15 confirmed,
> 10 refuted), so it is stronger than the unmarked vendor-text tier below — but it
> is still marketing, never a live account. The refuted list is kept in that
> document's §7 so those figures are not re-imported later.

---

## Feature matrix — they vs. we

✅ = has it · ⚠️ = partial · ❌ = doesn't have it · "not stated" = no public claim
found, not assumed absent. RazorpayX cells carry an evidence tier: **✅L** = seen in
the live account, **✅D** = seen only in RazorpayX's demo/marketing video. Other
competitors remain vendor-stated text claims.

| Feature | Clear | Mysa | CashFlo | RazorpayX | OPEN Money | Kodo/EnKash | **AgentSwitch** |
|---|---|---|---|---|---|---|---|
| OCR / AI invoice extraction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ no OCR engine in this deployment |
| Duplicate invoice/payment detection | ✅ (detects duplicate bills) | not stated | ✅ (35+ checks incl. duplicate payments) | not stated | not stated | not stated | ❌ — **this is our Core Challenge Prompt** |
| PO ↔ GRN ↔ Invoice matching | not stated | ✅ 3-way | ✅ 6-way | **✅L — Import tab carries Purchase Orders / Items / GRNs** | not stated | ✅ 2-/3-way | ❌ **structurally absent — no GRN entity anywhere in the 425-entity schema** |
| E-invoicing (IRN / signed QR / IRP) | ✅ | not stated | ✅ (IRN in its 6-way match) | not stated | not stated | not stated | ❌ not implemented at all (GST-28) |
| GSTR-2A/2B fetch & ITC reconciliation | ✅ (MaxITC AI) | not stated | ✅ | not stated | not stated | not stated | ⚠️ `Bill.ims_status` field exists; no GSTN-fetch tool over MCP |
| GST return filing (1/3B/9) | not stated | not stated | not stated | not stated | not stated | not stated | ❌ read-only for our role; GSTR-9 returns HTTP 501 platform-wide |
| TDS deduction automation (by section/threshold) | not stated | ✅ (u/s 194) | not stated | ⚠️L — "Auto TDS payments on your invoices will continue", but *manual* TDS is discontinued | ✅ | ✅ | ⚠️ fields + GL posting done; no auto-deduction by section/threshold |
| **TDS remittance / challan tracking** | not stated | not stated | not stated | **⚠️ Shown ✅D (195J sections, PAID/UNPAID by month) but live account says "Manual TDS payments have been discontinued due to regulatory issues"** | not stated | not stated | ❌ absent (GST-18: no challan tracking, no 26Q/27Q) |
| **GST payment / remittance** | not stated | not stated | not stated | **❌L — "GST payments via RazorpayX are no longer available, due to unavailability of automated payments APIs from our partner bank"** | not stated | not stated | ❌ no GSTPayment entity in the 425-entity schema |
| **Advance tax payment** | not stated | not stated | not stated | **❌L — "no longer available"**, same partner-bank reason | not stated | not stated | ❌ not modelled |
| MSME 45-day payment tracking | not stated | not stated | not stated | not stated | ✅ | ✅ | ⚠️ `is_msme`/`msme_type` fields exist; no automated 45-day alert |
| Vendor KYC verification | not stated | not stated | not stated | ✅ | not stated | not stated | ❌ fields stored (GSTIN/PAN/TIN/W-9), never verified against a registry |
| Bulk payout execution (IMPS/NEFT/RTGS/UPI) | not stated | ✅ (connected banking) | not stated | **✅L — Single + Bulk Payouts, batch upload, Payout Links** | ✅ | ✅ (cards + rails) | ❌ `PaymentMade` records a payment; no tool initiates a transfer |
| **Payout lifecycle/stage tracking** | not stated | not stated | not stated | **✅L — "Processing within TAT" vs "Slightly delayed on bank's end"** | not stated | not stated | ❌ `PaymentMade` has a status, but no execution stages to track |
| Multi-level configurable approval | not stated | not stated | not stated | **✅D only — "approval pending On Finance L2" / "rejected by On Finance L2" seen in the demo video, not confirmed in the live account** | ✅ | not stated | ⚠️ single approve/reject gate (`approval_status`), no hierarchy evidenced |
| **Sandbox / test mode** | not stated | not stated | not stated | **✅L — test balance + test payouts that don't affect real balance** | not stated | not stated | ❌ none found; the shared live ledger is the only environment |
| **Cashflow analytics (volume/trend)** | not stated | not stated | not stated | **✅L — Insights: payout & inflow volume, daily/weekly/monthly trends, export** | not stated | not stated | ⚠️ `cash_flow_scenario_sources` is forward *simulation*, not historical analytics |
| **Accountant/CA-scoped report access** | ✅ (CA-focused product) | not stated | not stated | **✅L — "CA can download reports… no access to your RazorpayX account except" reports** | not stated | not stated | ❌ no scoped external-accountant role found |
| **Unified beneficiary/contact master** | not stated | not stated | not stated | **✅L — Contacts filtered by Vendors / Employees / Customers** | not stated | not stated | ✅ `Party` with `contact_type` + `roles[]` — parity, not a gap either way |
| Bank reconciliation | not stated | ✅ (auto-reconciliation) | not stated | not stated | ✅ | not stated | ✅ `BankRule`, `BankTransaction.match_voucher` — real, agent-callable |
| Composite/group tax, broad tax-type taxonomy | not stated | not stated | not stated | not stated | not stated | not stated | ✅ `Tax`/`TaxGroup` cover IGST/CGST/SGST/UTGST/CESS/TDS/TCS/SALES_TAX/USE_TAX/EXCISE/1099 in one model |
| Dual-jurisdiction (India **and** US) in one system | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ✅ unique among these seven |
| **Conversational AI assistant over the product** | not stated | not stated | not stated | **✅L — "How can I help you?" with payout/cash/vendor prompts** | not stated | not stated | ✅ "Ask Agent" present in the AgentSwitch UI |
| Native agent **job/escalation entities** (not just a chat assistant) | not stated | not stated | not stated | not stated | not stated | not stated | ✅ `AgentJob`/`AgentSession`/`AgentTask`/`AgentEscalation`/`AgentMemory` as first-class records |
| Job-ledger forensics/audit replay | not stated | not stated | not stated | not stated | not stated | not stated | ✅ `AgentLedgerSeal`, `endpoint.job_ledger.{forensics,verify,replay}` |
| Documented agent-callable API (MCP, JSON-RPC 2.0) | not stated | not stated | not stated | not stated | not stated | not stated | ✅ confirmed: 436 tools, live-tested |

---

## RazorpayX re-examined (2026-09-22) — summary

> **Full screen-by-screen analysis: [`razorpay_gap_report.md`](razorpay_gap_report.md).**
> That document explains every observed feature, what it does, and what it implies
> for us. This is the condensed version.

**Three corrections to earlier versions of this report:**

1. **Evidence tiering was wrong (v3).** v3 called RazorpayX "verified first-hand"
   across the board. In fact several screenshots were RazorpayX's own *marketing
   videos* (dark-themed walkthroughs with play buttons), not the live account. The
   matrix now separates **L** (live) from **D** (demo).
2. **Multi-level approval is D, not L (v3).** The "Finance L2 approval pending /
   rejected" timeline came from the demo video. It is not confirmed in the live
   account. v2 said "not stated", v3 over-corrected to verified; the truth is in
   between — a vendor demo, which is weaker evidence than it first appeared.
3. **The agent-framework differentiator was overstated (v2).** RazorpayX ships a
   conversational assistant, so "no competitor has any agent capability" was wrong.
   Narrowed to: a chat assistant is not ours alone; first-class agent
   job/session/escalation records plus a forensic job ledger still appear to be.

**The biggest new finding — RazorpayX is retreating from tax remittance.** The live
account carries three withdrawal notices:

- *"Manual TDS payments have been discontinued due to regulatory issues. Auto TDS
  payments on your invoices will continue as usual."*
- *"Advance Tax payments via RazorpayX are no longer available, due to
  unavailability of automated payments APIs from our partner bank."*
- *"GST payments via RazorpayX are no longer available"* — same partner-bank reason.

This reframes one of our supposed gaps. v3 listed TDS remittance as a Medium
priority gap to close. But the best-funded payments company in this comparison set
just **exited** GST and advance-tax remittance, citing regulation and partner-bank
API availability — constraints that would apply to AgentSwitch equally. Statutory
*payment* execution in India looks structurally hard for a non-bank platform.
Tracking and computing the liability is defensible; moving the money is where
others have retreated.

**Sharpest genuine contrast — GRNs (tier L).** RazorpayX imports Goods Receipt Notes
as a first-class tab (Import: Purchase Orders | Items | GRNs). AgentSwitch has no
goods-receipt concept anywhere in its 425-entity schema. This remains the clearest
gap our agent cannot orchestrate around: you cannot three-way match against a
document type that does not exist.

---

## 1. What they have that we lack

- **E-invoicing (IRN / signed QR / IRP submission)** — Clear and CashFlo both claim
  this; AgentSwitch has a full settings page (`EInvoicingPreferences`) but nothing
  behind it. Above ₹5 Cr turnover this makes an AgentSwitch-issued invoice legally
  invalid and blocks the buyer's ITC. (`CURRENT_STATUS.md` §2, ticket GST-28)
- **Direct GSTN connectivity** (fetch 2A/2B, file returns) — `GSTReturn` is
  read-only for `finance_user`; no fetch/file tool exists anywhere in the 436 MCP
  tools; GSTR-9 generation 501s platform-wide, not just for our role. (ticket GST-39)
- **PO ↔ GRN ↔ Invoice matching** — the one gap here that isn't "unbuilt," it's
  **structural**: there is no Goods Receipt Note entity anywhere in the schema
  (confirmed by grepping all 425 entity names — only unrelated
  `EsignConsentReceipt`/`FormConsentReceipt` matched). Mysa/CashFlo/Kodo tout
  2-/3-/6-way matching, and **RazorpayX demonstrably imports GRNs** (Import tab:
  Purchase Orders | Items | GRNs) — so this is now confirmed against a product we
  have actually seen, not just claimed in marketing.
- **OCR / AI document scanning** — all six competitors claim this; AgentSwitch's
  intake pipeline (`BillIntakeEvent`, `endpoint.accounting.bill_intake.*`) has
  confidence scoring and human review, but this deployment explicitly has no OCR
  engine — scanned images/photos are unreadable.
- **Native duplicate-payment/fraud detection** — CashFlo specifically claims "35+
  checks... prevent duplicate payments"; Clear claims duplicate-bill detection.
  AgentSwitch has none natively. This is the literal reason Seat 03 exists.
- **Bulk payout execution** — OPEN Money and Kodo/EnKash claim it; **RazorpayX
  verifiably does it** (Single + Bulk Payouts with batch upload, and per-payout
  execution stages distinguishing "within TAT" from "delayed on bank's end").
  `PaymentMade` only records that a payment happened; nothing initiates one, and
  there is no execution state to track even if it did.
- **TDS remittance and challan tracking** — *downgraded in v4.* RazorpayX's demo
  shows per-section TDS tracking, but its live account says manual TDS payments are
  **discontinued**, and GST/advance-tax payments are **withdrawn** over partner-bank
  API availability. AgentSwitch lacks challan tracking and 26Q/27Q entirely
  (GST-18), so the gap is real — but the competitor evidence suggests the
  *remittance* half is hard for everyone, and computing/tracking the liability is
  the more defensible target.
- **Multi-level approval with an audit trail** — OPEN Money claims it; RazorpayX
  shows it in its demo video (named Finance L2 level, reject recorded on a
  timestamped timeline) though we could not confirm it in the live account.
  AgentSwitch has a single approve/reject gate with no named level and no chain.
- **Vendor KYC verification** — RazorpayX verifies vendor KYC; AgentSwitch stores
  GSTIN/PAN/TIN/W-9 fields on `Party` but nothing evidences verification against
  an external registry.
- **A sandbox/test environment** — **verified in RazorpayX**: a test balance and
  test payouts that explicitly don't affect the real balance. AgentSwitch offers no
  equivalent we could find, and the ledger is shared live with Teams 01 and 02 —
  so there is nowhere to rehearse a write before doing it for real. That is a
  material risk for an agent whose job involves mutating records.

## 2. What we have that they lack

- **Agent jobs and escalations as first-class records** — *narrowed in v3.* A
  conversational assistant is **not** a differentiator: RazorpayX has one, with
  prompts like "Are any of my payouts stuck in processing?". What still looks
  distinct is that AgentSwitch models the agent's *work* as data —
  `AgentJob`, `AgentSession`, `AgentTask`, `AgentEscalation`, `AgentMemory`,
  `AgentRunbook`, `AgentSkill` are queryable entities with their own MCP tools, not
  just a chat box over a product. Caveat: we can only see RazorpayX's assistant
  from the outside, so we don't know what it records underneath.
- **Job-ledger forensics and replay.** `AgentLedgerSeal`,
  `LedgerRetentionPolicy`/`Event`, and `endpoint.job_ledger.{forensics,verify,replay}`
  give audit-grade traceability of what an agent did and why. No competitor in the
  set is described as offering agent-action forensics — though note RazorpayX does
  provide a human approval audit trail (Finance L2 approve/reject with timestamps),
  so "auditability" broadly is not ours alone; agent-action replay specifically is.
- **Dual-jurisdiction data model in one system.** All six competitors are
  India-only. A business running both an Indian and a US entity would need two
  separate tools; AgentSwitch (and by extension our agent) serves both from one
  schema, toggled by `GET /api/accounting/locale`. This is the single biggest
  differentiator available to lean into, precisely because no competitor
  structurally can.
- **Broader native tax taxonomy.** `Tax`/`TaxGroup` cover
  IGST/CGST/SGST/UTGST/CESS/TDS/TCS/SALES_TAX/USE_TAX/EXCISE/WITHHOLDING_1099 in
  one composite-tax-capable model — wider than what's claimed by the SMB-focused,
  India-GST-only competitors (Mysa, Kodo).
- **Agent-callable bank reconciliation primitives already exist**
  (`BankRule`, `BankTransaction.match_voucher`) — a capability only OPEN Money and
  Mysa claim among the six, and ours is exposed as a direct MCP tool an agent can
  call today, not just a UI feature.
- **A documented, live, standards-based MCP server** (JSON-RPC 2.0, 436 tools,
  verified end-to-end this session). None of the six competitors publicly claim
  this. (Rillet, referenced in the brief as the worked example, does ship an MCP
  server — but Rillet isn't one of these six, so this isn't a claim of uniqueness
  across the whole market, just against this comparison set.)

## 3. Where we can improve

Split by who can actually act on it — conflating "AgentSwitch platform gaps" with
"our agent's implementation gaps" was the biggest weakness of v1 of this report.

### 3.1 Platform-level gaps (need AgentSwitch engineering — out of Team 03's control, but worth naming and prioritizing)

| Priority | Gap | Why it matters |
|---|---|---|
| High | E-invoicing (IRN/QR/IRP) | Legal blocker above ₹5 Cr turnover; already tracked as GST-28 |
| High | GSTN connectivity (fetch + file) | Currently fully manual; GSTR-9 hard-501s regardless of role (GST-39) |
| High | GRN entity + PO-GRN-Bill linkage | Structural — no amount of agent orchestration can fake a receipt-of-goods record that doesn't exist. RazorpayX imports GRNs as a first-class tab, so this is a confirmed competitive gap, not a theoretical one |
| High | Sandbox / test mode | *Raised in v3.* RazorpayX has test balances and non-affecting test payouts. We have one shared live ledger with Teams 01/02 and nowhere to rehearse a write — a real risk for an agent that mutates records |
| Medium | Reports API over MCP | Nothing agent-callable backs P&L/Balance Sheet/Cash Flow Statement — an agent can't even read these, let alone act on them |
| Medium | Bulk payout execution tool | `PaymentMade` is bookkeeping, not payment initiation — matters if the agent is ever asked to *pay*, not just *flag* |
| Medium | TDS/GST liability **tracking** (not remittance) | *Rescoped in v4.* Deduction fields post to the GL but challan/liability tracking is absent (GST-18). Note RazorpayX **withdrew** GST and advance-tax remittance over partner-bank API availability — so target tracking and computation, not moving money |
| Medium | Multi-level approval hierarchy | *v3 called this verified; v4 downgrades to vendor-demo evidence.* Still a real gap — our single `approval_status` gate has no named levels and no chain |
| Low | Automated vendor KYC verification | Fields exist; verification logic doesn't |

Note: several of these (GST-28, GST-39, and others in `CURRENT_STATUS.md` §2) are
**already self-documented by the platform** — filing them again via
`BugReport.create` for bounty points would likely be rejected as already-known.
The GRN absence and "no reports over MCP" finding are *not* in that documented
list and are the strongest genuinely-new candidates from this pass if we want to
verify them as bugs vs. intentional scope, before filing.

### 3.2 Agent-level opportunities (Team 03 can build now, no platform change needed)

Ranked by how directly each maps to the Core Challenge Prompt:

1. **Duplicate-payment detection** — our actual mandate. Already scaffolded
   (`scripts/invoice_matcher.py`, `playbooks/duplicate_audit.md`), but per
   `CURRENT_STATUS.md` §7 the scaffolding assumes fields/tools that don't exist
   (`hold_payment`, `AgentMessage.create`). **This is the single highest-value
   fix**: correct the playbook to use `AgentEscalation.create` and real
   `Bill`/`Invoice` fields, then it's genuinely competitive with CashFlo's
   duplicate-payment checks.
2. **Unified tax liability + unclaimed ITC in one answer** — join `GSTReturn`
   (has `net_tax_payable`) against `Bill.itc_eligibility`/`ims_status` to surface
   at-risk ITC no single screen currently shows combined.
3. **MSME 45-day compliance monitor** — join `Party.is_msme` against
   `Bill.due_date`; a real statutory-penalty risk (MSME Act) that currently
   depends on a human remembering to check, and that OPEN Money/Kodo both
   advertise natively — our version would be agent-driven and proactive rather
   than a dashboard someone has to open.
4. **IMS accept/reject pre-screening** — can't close the loop with GSTN (§3.1),
   but the agent can pre-screen `Bill` records against known vendor/PO data and
   recommend accept/reject, cutting the manual review surface at SCR-034.
5. **Lean hard into the dual-jurisdiction differentiator** (§2) — a single
   "tax liability across both Suryodaya and Keystone" answer, driven by locale,
   is something literally none of the six competitors can offer structurally.
   This should be a headline capability of our agent's design, not a footnote.
6. **Actually use the native agent framework.** `run_agent.py` currently doesn't
   create an `AgentSession`/`AgentTask`, and never calls `AgentEscalation.create`
   — the exact tools that make §2's "native agent framework" advantage real are
   sitting unused in our own code. This is the most concrete, immediately
   actionable item in this whole report: wiring the agent loop to the platform's
   own job/escalation primitives turns a comparative *platform* advantage into an
   actual *agent* advantage, which right now it isn't yet.

## Caveats

- **Evidence quality is uneven, and the matrix says so.** RazorpayX cells are
  tagged **L** (live account) or **D** (vendor demo video). Clear, Mysa, CashFlo,
  OPEN Money and Kodo/EnKash remain vendor-stated text claims with no tag.
- **A vendor demo is not proof of current availability.** v3 learned this the hard
  way: RazorpayX's demo material still showcases TDS payment tracking that the live
  account says has been discontinued. Any competitor capability sourced from
  marketing — which is *all five* of the others — may be aspirational, deprecated,
  or plan-gated.
- **The RazorpayX account inspected is "RazorpayX Lite."** Some absences may be
  plan-gating rather than product gaps.
- **Scrutiny has moved the comparison in both directions.** Looking closely cost us
  two claimed advantages (agent capability, approval parity) but also revealed a
  competitor retreating from tax remittance. The remaining "not stated" cells are
  *unexamined*, not points in our favour.
- RazorpayX was seen from the outside only — its UI tells us what it does, not how,
  and not what its AI assistant records underneath.
- Several AgentSwitch gaps here are platform-documented as unimplemented (not
  this report guessing) — see `CURRENT_STATUS.md` §2 for exact ticket ids
  (GST-18/28/29/32/39). The GRN-entity absence and missing reports API were
  independently confirmed this session and are not in that documented list.
