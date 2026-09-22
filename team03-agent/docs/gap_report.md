# Gap Report — AgentSwitch vs. Indian AP/GST Automation Platforms

**v3 — Clear deep dive added 2026-09-22.** v1 only listed features competitors have
that we lack. v2 added the reverse (what AgentSwitch has that none of
these six do), a feature-by-feature matrix so both directions are scannable at a
glance, and prioritized, actionable recommendations split by who can actually act
on each one — the AgentSwitch platform team vs. our own Team 03 agent.

v3 adds §4, a source-verified deep dive on Clear (ClearTax) — our closest
comparator and the only one of the six with a regulatory moat. It also upgrades
Clear's row in the feature matrix from "not stated" to evidenced where the
research supports it. Clear's cells are now the only competitor cells in this
report backed by fetched primary sources rather than recalled product research.

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

**†** on a Clear cell = evidenced against fetched primary sources in §4, not
recalled product research. Still vendor-published, but adversarially checked and
dated 2026-09-22. Cells without † are unchanged from v2.

| Feature | Clear | Mysa | CashFlo | RazorpayX | OPEN Money | Kodo/EnKash | **AgentSwitch** |
|---|---|---|---|---|---|---|---|
| OCR / AI invoice extraction | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ❌ no OCR engine in this deployment |
| Duplicate invoice/payment detection | ✅† keyed on doc number + FY + vendor/buyer GSTIN | not stated | ✅ (35+ checks incl. duplicate payments) | not stated | not stated | not stated | ❌ — **this is our Core Challenge Prompt** |
| PO ↔ GRN ↔ Invoice matching | not stated | ✅ 3-way | ✅ 6-way | ✅ 3-way | not stated | ✅ 2-/3-way | ❌ **structurally absent — no GRN entity anywhere in the 425-entity schema** |
| E-invoicing (IRN / signed QR / IRP) | ✅† **operates IRP 4** (einvoice4.gst.gov.in) + GSP licence | not stated | ✅ (IRN in its 6-way match) | not stated | not stated | not stated | ❌ not implemented at all (GST-28) |
| GSTR-2A/2B fetch & ITC reconciliation | ✅† MaxITC — fuzzy PAN-level match, scheduled auto-recon, own API | not stated | ✅ | not stated | not stated | not stated | ⚠️ `Bill.ims_status` field exists; no GSTN-fetch tool over MCP |
| GST return filing (1/3B/9) | ✅† GSTR-1→9/9C + 4/6/7/8 + ITC-04, as ASP/GSP | not stated | not stated | not stated | not stated | not stated | ❌ read-only for our role; GSTR-9 returns HTTP 501 platform-wide |
| TDS automation (deduction by section/threshold) | ⚠️† e-TDS *return filing*, cert distribution, 26AS recon — auto-deduction not evidenced | ✅ (u/s 194) | not stated | ✅ (194C/J/Q) | ✅ | ✅ | ⚠️ fields + GL posting done; no auto-deduction by section/threshold |
| MSME 45-day payment tracking | not stated | not stated | not stated | not stated | ✅ | ✅ | ⚠️ `is_msme`/`msme_type` fields exist; no automated 45-day alert |
| Vendor KYC verification | ✅† vendor KYC / GSTIN validation + vendor communication | not stated | not stated | ✅ | not stated | not stated | ❌ fields stored (GSTIN/PAN/TIN/W-9), never verified against a registry |
| Bulk payout execution (IMPS/NEFT/RTGS/UPI) | ⚠️† orchestrates early payment (treasury/TReDS/bank-NBFC), not lender or PA of record; UPI/netbanking is AR collection in ClearOne | ✅ (connected banking) | not stated | ✅ | ✅ | ✅ (cards + rails) | ❌ `PaymentMade` records a payment; no tool initiates a transfer |
| Multi-level configurable approval | ⚠️† AP "approval workflows" claimed; hierarchy depth not evidenced | not stated | not stated | not stated | ✅ | not stated | ⚠️ single approve/reject gate (`approval_status`), no hierarchy evidenced |
| Bank reconciliation | not stated | ✅ (auto-reconciliation) | not stated | not stated | ✅ | not stated | ✅ `BankRule`, `BankTransaction.match_voucher` — real, agent-callable |
| Composite/group tax, broad tax-type taxonomy | not stated | not stated | not stated | not stated | not stated | not stated | ✅ `Tax`/`TaxGroup` cover IGST/CGST/SGST/UTGST/CESS/TDS/TCS/SALES_TAX/USE_TAX/EXCISE/1099 in one model |
| Dual-jurisdiction (India **and** US) in one system | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ❌ India-only | ✅ unique among these seven |
| Native agent/job/escalation framework | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ unique: `AgentJob`/`AgentSession`/`AgentTask`/`AgentEscalation`/`AgentMemory` |
| Job-ledger forensics/audit replay | ❌ | ❌ | ❌ | ❌ | ❌ | ❌ | ✅ `AgentLedgerSeal`, `endpoint.job_ledger.{forensics,verify,replay}` |
| Documented agent-callable API (MCP, JSON-RPC 2.0) | ⚠️† public REST API docs (docs.cleartax.in, incl. a MaxITC API) — REST, **not** MCP | not stated | not stated | not stated | not stated | not stated | ✅ confirmed: 436 tools, live-tested this session |

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

## 4. Clear (ClearTax) deep dive

Added v3, 2026-09-22. Clear is the closest comparator to our seat and the only
one of the six with a *regulatory* moat rather than a purely functional one, so
it earns a section of its own.

**Method and its limits.** 28 sources fetched; 134 candidate claims extracted;
25 taken through adversarial verification; **15 confirmed, 10 refuted**. The
refuted list is recorded in §4.7 deliberately — several of those numbers appear
in Clear's own marketing and in competitor blog posts, and we should not
recycle them. The evidence is still overwhelmingly Clear's own live marketing
and documentation pages. That is the right evidence class for *which products
exist and what they are called*; it is **not** evidence of functional depth, GA
maturity, or reliability. Independent corroboration exists for only a few
points: IRP status (government `gst.gov.in` subdomains), the GSP licence (trade
press + third-party compilations), and the CimplyFive / Xpedize acquisitions.

### 4.1 What Clear actually is

Three businesses under one brand (legal entity **Defmacro Software Pvt Ltd**):

1. **Consumer** — mass-market ITR e-filing, free self-service plus a paid
   CA-assisted ladder.
2. **SMB** — **ClearOne**, billing/invoicing with embedded e-invoice and e-way
   bill generation, plus payment-link collection.
3. **Enterprise** — the compliance and AP suite, sold as three "clouds".

The clouds — **Finance** (AP/AR/treasury), **Compliance** (GST + direct tax) and
**Supply Chain** — are packaging umbrellas, not exclusive bundles. The same
modules are also sold standalone, and the boundaries overlap: AP sits under both
Finance and Supply Chain; GST/TDS under both Finance and Compliance. The global
site (cleartax.com) uses a different taxonomy again.

**Benchmark Clear at module level, not cloud level.** Any comparison built on
the cloud names will double-count.

### 4.2 Verified module inventory

GST return filing (GSTR-1→9/9C, plus 4/6/7/8 and ITC-04) as ASP/GSP ·
e-invoicing · e-way bill · TDS/e-TDS return filing with certificate distribution
and 26AS reconciliation · AP automation (OCR ingestion, approval workflows,
duplicate detection, payment tracking) · vendor KYC/GSTIN validation and vendor
communication · **MaxITC** 2A/2B reconciliation · GSTN historical data pulls
(2 years) · smart reporting and CFO dashboard · billing · **CimplyFive**
secretarial compliance (Companies Act 2013 / SEBI LODR, acquired 2022) ·
employee ITR.

**Three gaps, confirmed by absence across every product menu checked:**

- **No payroll product.**
- **No notices / litigation / assessment-management module.**
- **No corporate income-tax computation or return filing.** Clear's "direct tax"
  is effectively TDS/TCS plus employee ITR. No transfer pricing either.

Worth noting against our own §3.1 list: Clear publishes **no PO↔GRN↔invoice
matching claim** either. The GRN gap is not something Clear solves and we don't.

### 4.3 The regulatory moat — the finding that actually matters

This is the one part of the Clear picture backed by government-domain evidence
rather than vendor copy:

- Clear **operates Invoice Registration Portal 4** at `einvoice4.gst.gov.in`.
  The portal states it is "operated by Clear, a GSTN authorized IRP" and
  publishes GSTN-issued sandbox (26 Sep 2022) and production (13 Jan 2023)
  certificates naming Defmacro Software Pvt Ltd. Live and unsuspended as of
  Sept 2026.
- Only **four private IRPs** exist — IRIS, Cygnet, ClearTax, E&Y — with NIC
  running einvoice1/2. Independently corroborated by a competitor-authored page
  on another `gst.gov.in` subdomain.
- Separately one of roughly **62 empanelled GSPs**.

Direct read-across to us: `CURRENT_STATUS.md` §2 records AgentSwitch as
`einvoicing: false` with nothing implemented (ticket GST-28). §3.1 already ranks
that High. This section is the evidence for *why* it is High — IRP/GSP
connectivity is the foundation of Clear's entire enterprise business, not a
feature bullet.

Caution on their security posture: **ISO 27001:2022 and SOC 2 Type II are
self-attested** on the global trust center with no certificate number or
registrar published, and no data-residency commitment was verified. A more
expansive security claim circulating about Clear (SOC 2 + AWS + quarterly VAPT +
128-bit SSL + 2FA + IP whitelisting + 8-year audit trails + 99.99% uptime) was
**refuted 0-3** — do not reuse those specifics.

### 4.4 Money movement — Clear is an orchestrator, not a rail

The single most-corrected claim in verification. Two distinct mechanisms:

**Enterprise supply-chain finance / invoice discounting.** Non-collateralised
early payment to suppliers against a discount, with funding selectable from
three sources: **buyer treasury, TReDS exchanges, or banks/NBFCs**. But Clear is
**not the lender of record**. Its own FAQ describes the programme as run "in
partnership with our financing partners, e.g. Bajaj Finance," with limits
underwritten by the partner. No RBI NBFC registration surfaced, and Clear is
**not** a TReDS operator (RXIL, M1xchange, Invoicemart, C2treds are) — the TReDS
route hands off to an external exchange.

**SMB collection (ClearOne, AR side).** Payment links with or without an
invoice, shared via **WhatsApp or Email**, with status tracking and reminders.
Collection via **UPI and netbanking only — cards are not listed.** "Free payment
links" means free link *generation*, not zero MDR; transaction economics are
undisclosed. Clear is not evidenced as an RBI-licensed payment aggregator, so a
third-party PA/PG almost certainly sits underneath, partner undisclosed.

Read-across: our §3.1 "bulk payout execution" gap is real, but Clear is a weaker
benchmark for it than RazorpayX, OPEN Money or Kodo/EnKash, which operate actual
rails. Clear's differentiator here is the *financing* layer, not the payment
layer.

### 4.5 Integrations and pricing

**Named connectors** (the reliable part): SAP (ECC and S/4HANA add-on), Oracle
(Fusion Cloud / EBS / NetSuite), Microsoft Dynamics 365 F&O and Business
Central, Tally, Zoho, Busy, JD Edwards. Everything else via public API, SFTP or
templates. Public developer docs at `docs.cleartax.in` including a MaxITC API.

**The integration counts are unusable.** "500+ ERP integrations" refuted 1-2;
"50+ ERPs / 50-member integrations team" refuted 0-3; other Clear properties
simultaneously claim "2,000+" and "3000+". Undated, unaudited, mutually
contradictory. Cite the named-connector list and the API/SFTP/template ingestion
modes; cite nothing numeric.

**Enterprise pricing is entirely undisclosed** — no rate card, no
per-GSTIN/per-invoice/per-seat model, no bundle-vs-module licensing, and no
statement of how enterprises pay Clear. The only published pricing is the B2C
CA-assisted ITR ladder (AY 2026-27: Basic → Premium → Elite ₹11,998 list /
₹5,999 discounted → Luxe ₹29,998 / ₹14,999). Tier names change every assessment
year, so date any citation.

### 4.6 Scale figures — do not restate as fact

Clear's own properties contradict each other on customer count: **4,000+**
(India Compliance Cloud) vs **5,000+** (global about page) vs **10,000+
businesses** (India footer) vs **3,000+** (invoice-discounting page). Different
scopes, no as-of date on any of them. Same problem with MaxITC's savings claims
— "4% GST saved", "grow profits by 7%", "up to 8% working-capital impact" — no
sample, no methodology, no date. These are positioning, not evidence.

### 4.7 Refuted — do not reuse if these appear in downstream material

| Claim | Vote |
|---|---|
| "500+ completed ERP integrations" | 1-2 |
| "SAP/Tally + 50+ ERPs, 50-member in-house integrations team" | 0-3 |
| Detailed security posture (SOC 2 + AWS + quarterly VAPT + 128-bit SSL + 2FA + IP whitelisting + 8-yr audit trails + 99.99% uptime) | 0-3 |
| E-invoicing scale (4,000+ businesses / 9,000+ GSTINs / 200M+ IRNs) | 0-3 |
| Named enterprise logos (Flipkart, Swiggy, Ola, Blinkit, Intel, BYJU'S et al.) | 1-2 |
| ITR price points ₹1,299 / ₹2,999 / ₹3,999 | 0-3 |
| "Clear provides credit itself" / "full AR+AP lifecycle" framings | 1-2, 0-3 |

### 4.8 What this changes for our agent

1. **Clear's duplicate-detection key is narrower and better than ours.** They
   match on **document number + FY + vendor/buyer GSTIN**. Our
   `scripts/invoice_matcher.py` matches on same-vendor + identical amount within
   ±3 days, which is a heuristic, not an identity. Live-tested against Keystone
   on 2026-09-22 it produced **three false positives** — recurring bills from
   four templates fired on consecutive days, flagged purely because the amounts
   repeat. Adopting a document-identity key (number + FY + party) as the *exact*
   tier, and demoting amount-proximity to a *suspicious* tier that must also
   clear a recurring-template check, is a concrete, cheap improvement. This
   reinforces §3.2 item 1.
2. **MaxITC is a standalone product with its own API, not a feature.** Clear
   treats "what ITC is unclaimed" as important enough to separately brand,
   separately document and separately sell. Our §3.2 item 2 (unified liability +
   unclaimed ITC in one answer) is aimed at the same target and should be scoped
   with that seriousness.
3. **Their three gaps are our opening.** No payroll, no notices/litigation
   management, no corporate ITR — and, like everyone else in this set, no native
   agent framework and no dual-jurisdiction support. §2 stands unchanged after
   this deeper look at the strongest competitor, which is the useful result.
4. **IRP/GSP is not a gap we can close.** It is a licence, not a feature. Our
   agent should be designed to be *correct without* GSTN connectivity rather
   than to pretend at it — which is what §3.1's "escalate rather than assume"
   posture already implies.

### 4.9 Still open on Clear

- Enterprise pricing/packaging model and how enterprises actually pay Clear.
- The regulated rails behind ClearOne's UPI/netbanking collection and behind
  enterprise vendor payouts — which PA, bank or NBFC, and at what MDR.
- Whether notice management and corporate ITR are roadmap, partnership, or
  deliberately out of scope. Absence from every menu is suggestive, not
  conclusive.
- Real ERP integration depth — certified bidirectional posting with error
  handling, or batch push. The published counts are unreliable, so this needs a
  technical evaluation.
- **Head-to-head positioning against the rest of this set was not established.**
  No market-share, win-rate or analyst data was verified for any competitor.
  Note that IRP status differentiates Clear from Zoho/Tally/CashFlo/RazorpayX
  but **not** from IRIS or Cygnet.

## Caveats

- **§4 (Clear) is the exception to the bullet below**, and only partly: its
  claims were fetched and adversarially verified on 2026-09-22, with 10 of 25
  verified claims refuted and recorded in §4.7. But it is still vendor-published
  evidence for everything except IRP/GSP status. It proves what Clear *offers*,
  not how well any of it works. The other five competitors are unchanged from v2.
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
- **Provenance note on §4.8 item 1.** The three false positives from
  `invoice_matcher.py` were observed on 2026-09-22 against the **Keystone (US)**
  instance at `class.agentswitch.theschoolofai.in` — 7 draft bills from 4
  recurring templates, fired 2026-09-20 and again 2026-09-21, all Apex Metals
  Supply LLC. `CURRENT_STATUS.md` is Suryodaya/India only and does not cover
  this instance, so that observation is not yet written up anywhere else in the
  repo. The repeated same-day-amount generation is itself an unfiled bug
  candidate, pending a check of the templates' declared frequency.
