# Gap Report — AgentSwitch vs. Indian AP/GST Automation Platforms

Week 1 deliverable (brief §8, step 3): AgentSwitch (Suryodaya/India) compared against
six modern AI-native AP + GST platforms. AgentSwitch's capabilities below are not
vendor claims — they're pulled from `../CURRENT_STATUS.md` and
`screen_api_mapping.md`, both built from real logins, real `/api/schemas` and MCP
`tools/list` calls, and real sample records against the live Suryodaya instance. The
competitors' capabilities are vendor-stated (from public product research), not
independently verified the same way — that asymmetry is a real limitation of this
report, called out again at the end.

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

## 1. Concrete features they have that AgentSwitch lacks

| Feature | Who has it | AgentSwitch status | Evidence |
|---|---|---|---|
| **E-invoicing (IRN / signed QR / IRP submission)** | Clear (core strength) | **Not implemented at all**, despite a full settings page (`EInvoicingPreferences`). No IRN requested, no QR stored, no IRP client. Above ₹5 Cr turnover this makes AgentSwitch-issued invoices legally invalid and blocks the buyer's ITC. | `CURRENT_STATUS.md` §2, ticket GST-28 |
| **Direct GSTN connectivity** (auto-fetch GSTR-2A/2B, file returns) | Clear, CashFlo (implied by "GST/ITC reconciliation") | `GSTReturn` is **read-only** for our role; no "fetch from GSTN" or "file return" tool exists anywhere in the 436 MCP tools. GSTR-9 generation returns HTTP 501 platform-wide, not just for our role. | `screen_api_mapping.md` SCR-033/036, `CURRENT_STATUS.md` §2 ticket GST-39 |
| **PO ↔ GRN ↔ Invoice matching (2-/3-/6-way)** | Mysa (3-way), CashFlo (6-way, "35+ checks") | **Structurally not possible today** — there is no Goods Receipt Note entity anywhere in the platform's 425-entity schema (confirmed by grep; only unrelated `EsignConsentReceipt`/`FormConsentReceipt` matched). `Bill.purchase_order_id` links a bill to a PO, but nothing links either to a receipt of goods. | Live schema search, this session |
| **OCR / AI document scanning** | Mysa, OPEN Money, Kodo/EnKash | Intake pipeline exists (`BillIntakeEvent`, `endpoint.accounting.bill_intake.{queue,extract,accept,reject}`) with confidence scoring and human review — but **this deployment explicitly has no OCR engine**; scanned images/photos are unreadable, only machine-readable documents parse. | `UI.MD` SCR-039 |
| **Automated duplicate-payment / fraud detection** | CashFlo ("35+ automated checks... prevent duplicate payments") | No evidence of a native duplicate-invoice/duplicate-payment detector anywhere in the schema or UI. **This is literally our seat's Core Challenge Prompt** — see §2 below. | `UI.MD` §7.5 |
| **Bulk payout execution over bank rails** (IMPS/NEFT/RTGS/UPI initiation) | RazorpayX, Kodo/EnKash | `PaymentMade` *records* a payment with a `payment_mode` field, but no tool actually initiates a transfer. This looks like a bookkeeping record of a payment made elsewhere, not a payment-execution API. | `CURRENT_STATUS.md` §3, `screen_api_mapping.md` SCR-018 |
| **Automated vendor KYC / onboarding verification** | RazorpayX ("vendor KYC verification") | `Party` carries KYC-adjacent fields (GSTIN, PAN, TIN, W-9, 1099) but nothing evidences automated verification against a registry — fields are just stored, not validated. | `screen_api_mapping.md` SCR-003/016 |
| **Configurable multi-level approval hierarchies** | OPEN Money | Partial at best: `approval_status` (`not_required/pending_approval/approved/rejected`) plus `Bill.approval.submit`/`Invoice.approval.submit` tools exist, but nothing evidences *multi-level* or *configurable* hierarchy — looks like a single approve/reject gate, not a chain. | `screen_api_mapping.md` SCR-006 |
| **Connected/live bank feeds** | OPEN Money ("connected banking") | Partial: `BankAccount`, `BankTransaction`, `BankRule` and a `BankTransaction.match_voucher` tool exist (reconciliation is real), but nothing confirms a *live* feed vs. manually imported/uploaded transactions. | `CURRENT_STATUS.md` §4 tool inventory |

---

## 2. Gaps our agent can bridge through tool orchestration over existing APIs

These don't require new AgentSwitch platform features — they're synthesis our agent
can do today by composing existing read-only tools, which is exactly what none of
the UI's 41 screens do in a single view (`screen_api_mapping.md` confirms no
dashboard/report tool exists over MCP at all — every cross-entity view has to be
built by the caller, UI or agent).

- **Duplicate vendor payment detection** (Core Challenge Prompt itself) — build
  entirely from `Bill.list()` + `PaymentMade.list()`, grouping by `vendor_id` and
  matching on `invoice_number`/`amount`/date window. No platform gap blocks this;
  it's pure orchestration (`playbooks/duplicate_audit.md`, `scripts/invoice_matcher.py`).
- **Tax liability + unclaimed ITC in one answer** — `GSTReturn` already computes
  `net_tax_payable` per period, but "what's unclaimed" requires cross-referencing
  `Bill.itc_eligibility` + `Bill.ims_status` (`pending`/`reject` = at-risk ITC)
  against what's already reflected in a filed `GSTReturn`. No single screen does
  this join today (SCR-033 shows returns, SCR-034 shows IMS, separately).
- **MSME 45-day payment compliance monitoring** — `Party.is_msme` + `Bill.due_date`
  exist, but no screen or tool surfaces "which MSME vendors are approaching/past
  the 45-day statutory window." The agent can compute this by joining
  `Party.list(is_msme=true)` with `Bill.list(vendor_id=...)` — a real
  compliance risk (penal interest under the MSME Act) no current screen flags.
- **IMS accept/reject triage assistance** — a human currently has to manually
  accept/reject each `Bill` against GSTR-2B data (SCR-034). Even without a GSTN
  auto-fetch tool (§1), the agent can pre-screen bills against internally
  recorded PO/vendor data and recommend accept/reject, cutting the manual review
  surface even if it can't close the loop with GSTN itself.
- **Cross-jurisdiction tax view** — none of the six competitors reviewed operate
  across both Ind AS/GST *and* US GAAP/Sales & Use Tax in one product (each is
  India-only). Our agent's `GET /api/accounting/locale`-driven design is a
  structural differentiator, not just a feature — it's the one thing none of
  them are built to do.

## 3. Actions an autonomous agent can accomplish that the traditional UI cannot

- **One synthesized answer instead of five screens.** "What's our tax liability,
  what's unclaimed, and is anyone being paid twice" today requires a human to
  visit SCR-006 (Bills), SCR-019 (GL), SCR-026 (Taxes), SCR-033 (Returns), and
  SCR-034 (IMS) separately and mentally combine them. An agent answers this in
  one pass.
- **Continuous background sweep, not a point-in-time glance.** A human opens the
  Bills list when they remember to; a scheduled `AgentTask`/`AgentSession` (the
  platform already has this framework — 985 `AgentJob` records exist) can sweep
  the growing shared ledger continuously and escalate the moment a suspicious
  duplicate appears, via `AgentEscalation.create` — a real tool, not a proposal.
- **Deterministic computation at scale.** `scripts/tax_math.py` avoids the
  floating-point drift/hallucination risk of an LLM (or a human in a spreadsheet)
  summing hundreds of tax lines by hand — and there's no reports API over MCP at
  all (`screen_api_mapping.md`'s cross-cutting gap #2), so *nothing* currently
  automates this arithmetic; a human is doing it visually today.
- **MSME/compliance risk surfaced proactively**, not only when someone happens to
  open the right screen (§2 above) — this is a genuine compliance exposure
  (penal interest for late MSME payment) that currently depends on someone
  remembering to check.

## Caveats

- Competitor capabilities here are vendor-stated, gathered from public product
  research, not independently tested against a live account the way AgentSwitch's
  were. A fully fair comparison would verify Clear's actual e-invoicing flow, or
  CashFlo's actual "35+ checks," the same way we verified AgentSwitch's real
  schema — that verification wasn't in scope this session.
- Several AgentSwitch gaps above (e-invoicing, GSTN fetch, GSTR-9) are
  *platform-documented as unimplemented*, not things this report is guessing at —
  see `CURRENT_STATUS.md` §2 for the exact ticket ids (GST-18/28/29/32/39).
- The GRN-entity absence is the one structural (not just "not yet built") finding
  here: without a receipt-of-goods concept anywhere in the schema, true 3-way
  matching can't be retrofitted by our agent alone — it would need a platform
  schema change, not just new orchestration.
