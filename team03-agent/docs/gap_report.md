# Gap Report — AgentSwitch vs. Indian AP/GST Automation Platforms

**v2 — reviewed and expanded 2026-09-20.** v1 only listed features competitors have
that we lack. This revision adds the reverse (what AgentSwitch has that none of
these six do), a feature-by-feature matrix so both directions are scannable at a
glance, and prioritized, actionable recommendations split by who can actually act
on each one — the AgentSwitch platform team vs. our own Team 03 agent.

AgentSwitch's capabilities below are not vendor claims — they're pulled from
`../CURRENT_STATUS.md` and `screen_api_mapping.md`, both built from real logins,
real `/api/schemas` and MCP `tools/list` calls, and real sample records against the
live Suryodaya instance. The competitors' capabilities are vendor-stated (from
public product research gathered earlier), not independently tested — that
asymmetry is real and called out again in Caveats. Where a competitor's claim is
unverified either way, this report says "not stated" rather than guessing.

## Competitors reviewed

| Platform | Core strength | Key integrations | Target segment |
|---|---|---|---|
| Clear (ClearTax) | Market-leading GST/ITC reconciliation & e-invoicing | SAP, Oracle, Tally, NetSuite | Mid-Large enterprises & CAs |
| Mysa | AI invoice scan with 22+ Indian tax checks (GST/TDS/RCM) | Zoho Books, Tally, ERPNext | Startups & SMBs |
| CashFlo | 6-way matching, fraud prevention & supply-chain financing | SAP, Oracle, MS Dynamics | Mid-market & large enterprises |
| RazorpayX S2P | Vendor payout rails & TDS automation | Tally, Zoho Books | Startups & growth businesses |
| OPEN Money | Connected banking + AP automation + MSME tracking | Tally, Zoho, Dynamics, NetSuite | SMBs & mid-market |
| Kodo / EnKash | Unified corporate cards + AP invoice workflows | Tally, QuickBooks, NetSuite | Startups & mid-market |

---

## Feature matrix — they vs. we

✅ = has it (vendor-claimed for competitors, verified for AgentSwitch) · ⚠️ = partial
· ❌ = doesn't have it · "not stated" = no public claim found, not assumed absent.

| Feature | Clear | Mysa | CashFlo | RazorpayX | OPEN Money | Kodo/EnKash | **AgentSwitch** |
|---|---|---|---|---|---|---|---|
| OCR / AI invoice extraction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ no OCR engine in this deployment |
| Duplicate invoice/payment detection | ✅ (detects duplicate bills) | not stated | ✅ (35+ checks incl. duplicate payments) | not stated | not stated | not stated | ❌ — **this is our Core Challenge Prompt** |
| PO ↔ GRN ↔ Invoice matching | not stated | ✅ 3-way | ✅ 6-way | ✅ 3-way | not stated | ✅ 2-/3-way | ❌ **structurally absent — no GRN entity anywhere in the 425-entity schema** |
| E-invoicing (IRN / signed QR / IRP) | ✅ | not stated | ✅ (IRN in its 6-way match) | not stated | not stated | not stated | ❌ not implemented at all (GST-28) |
| GSTR-2A/2B fetch & ITC reconciliation | ✅ (MaxITC AI) | not stated | ✅ | not stated | not stated | not stated | ⚠️ `Bill.ims_status` field exists; no GSTN-fetch tool over MCP |
| GST return filing (1/3B/9) | not stated | not stated | not stated | not stated | not stated | not stated | ❌ read-only for our role; GSTR-9 returns HTTP 501 platform-wide |
| TDS automation (deduction by section/threshold) | not stated | ✅ (u/s 194) | not stated | ✅ (194C/J/Q) | ✅ | ✅ | ⚠️ fields + GL posting done; no auto-deduction by section/threshold |
| MSME 45-day payment tracking | not stated | not stated | not stated | not stated | ✅ | ✅ | ⚠️ `is_msme`/`msme_type` fields exist; no automated 45-day alert |
| Vendor KYC verification | not stated | not stated | not stated | ✅ | not stated | not stated | ❌ fields stored (GSTIN/PAN/TIN/W-9), never verified against a registry |
| Bulk payout execution (IMPS/NEFT/RTGS/UPI) | not stated | ✅ (connected banking) | not stated | ✅ | ✅ | ✅ (cards + rails) | ❌ `PaymentMade` records a payment; no tool initiates a transfer |
| Multi-level configurable approval | not stated | not stated | not stated | not stated | ✅ | not stated | ⚠️ single approve/reject gate (`approval_status`), no hierarchy evidenced |
| Bank reconciliation | not stated | ✅ (auto-reconciliation) | not stated | not stated | ✅ | not stated | ✅ `BankRule`, `BankTransaction.match_voucher` — real, agent-callable |
| Composite/group tax, broad tax-type taxonomy | not stated | not stated | not stated | not stated | not stated | not stated | ✅ `Tax`/`TaxGroup` cover IGST/CGST/SGST/UTGST/CESS/TDS/TCS/SALES_TAX/USE_TAX/EXCISE/1099 in one model |
| Dual-jurisdiction (India **and** US) in one system | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ✅ unique among these seven |
| Native agent/job/escalation framework | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ unique: `AgentJob`/`AgentSession`/`AgentTask`/`AgentEscalation`/`AgentMemory` |
| Job-ledger forensics/audit replay | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ `AgentLedgerSeal`, `endpoint.job_ledger.{forensics,verify,replay}` |
| Documented agent-callable API (MCP, JSON-RPC 2.0) | not stated | not stated | not stated | not stated | not stated | not stated | ✅ confirmed: 436 tools, live-tested this session |

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
  `EsignConsentReceipt`/`FormConsentReceipt` matched). Mysa/CashFlo/RazorpayX/
  Kodo all tout 2-/3-/6-way matching against a receipt concept that doesn't exist
  here yet.
- **OCR / AI document scanning** — all six competitors claim this; AgentSwitch's
  intake pipeline (`BillIntakeEvent`, `endpoint.accounting.bill_intake.*`) has
  confidence scoring and human review, but this deployment explicitly has no OCR
  engine — scanned images/photos are unreadable.
- **Native duplicate-payment/fraud detection** — CashFlo specifically claims "35+
  checks... prevent duplicate payments"; Clear claims duplicate-bill detection.
  AgentSwitch has none natively. This is the literal reason Seat 03 exists.
- **Bulk payout execution** — RazorpayX, OPEN Money, and Kodo/EnKash all execute
  transfers (IMPS/NEFT/RTGS/UPI/cards). `PaymentMade` only records that a payment
  happened; nothing initiates one.
- **Vendor KYC verification** — RazorpayX verifies vendor KYC; AgentSwitch stores
  GSTIN/PAN/TIN/W-9 fields on `Party` but nothing evidences verification against
  an external registry.
- **Multi-level configurable approval hierarchy** — OPEN Money claims this
  explicitly; AgentSwitch has a single approve/reject gate, not a chain.

## 2. What we have that they lack

- **Native agent/job/escalation framework.** None of the six is described as an
  agent-native platform — they're SaaS UIs with APIs bolted on. AgentSwitch ships
  `AgentJob`, `AgentSession`, `AgentTask`, `AgentEscalation`, `AgentMemory`,
  `AgentRunbook`, `AgentSkill` as first-class entities with their own MCP tools.
  Building an autonomous AP/Tax agent on top of a platform that already models
  "jobs" and "escalations" natively is a structural head start none of the
  competitors offer.
- **Job-ledger forensics and replay.** `AgentLedgerSeal`,
  `LedgerRetentionPolicy`/`Event`, and `endpoint.job_ledger.{forensics,verify,replay}`
  give audit-grade traceability of what an agent did and why. This matters more
  in an AI-agent-first world than another GST reconciliation checkbox, and it's
  not a feature category any of the six competitors are described as offering —
  they're accounting products, not agent-observability products.
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
| High | GRN entity + PO-GRN-Bill linkage | Structural — no amount of agent orchestration can fake a receipt-of-goods record that doesn't exist |
| Medium | Reports API over MCP | Nothing agent-callable backs P&L/Balance Sheet/Cash Flow Statement — an agent can't even read these, let alone act on them |
| Medium | Bulk payout execution tool | `PaymentMade` is bookkeeping, not payment initiation — matters if the agent is ever asked to *pay*, not just *flag* |
| Low | Multi-level approval hierarchy | Single-gate `approval_status` may be enough for now; revisit if larger-enterprise use cases come up |
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

- Competitor capabilities are vendor-stated, gathered from public product
  research, not independently tested against a live account the way
  AgentSwitch's were. A fully fair comparison would verify Clear's actual
  e-invoicing flow, CashFlo's actual "35+ checks," etc. — out of scope this
  session.
- "Not stated" for a competitor means no public claim was found, not that the
  feature is confirmed absent — several of these products likely have
  capabilities beyond what their marketing copy highlighted.
- Several AgentSwitch gaps here are platform-documented as unimplemented (not
  this report guessing) — see `CURRENT_STATUS.md` §2 for exact ticket ids
  (GST-18/28/29/32/39). The GRN-entity absence and missing reports API were
  independently confirmed this session and are not in that documented list.
