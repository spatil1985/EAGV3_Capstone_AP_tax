# Gap Report — AgentSwitch vs. Mysa

**Team 03 · 2026-09-22.** Single-competitor deep-dive (the six-vendor survey is
`gap_report.md`). **Primary use: an AgentSwitch platform improvement backlog**,
sourced from one concrete competitor rather than generic best practice.

**Evidence:** AgentSwitch facts are from live logins/MCP calls (`CURRENT_STATUS.md`,
`screen_api_mapping.md`), refreshed against the 2026-09-22 post-fix state. Mysa
facts are vendor pages (`mysa.io/ai-scan`, `/accounts-payable`, `/bill-pay`), **not
independently tested** — treat as claims, not confirmed behavior. The linked
`tax_rate_service` API is US-side (Avalara/TaxJar, unwired) and irrelevant to
Mysa (India-only); it's out of scope here.

---

## Top 5 asks for AgentSwitch engineering

Ranked by how directly each blocks a real AP/GST workflow Mysa already ships.

| # | Ask | Why it's urgent | Existing ticket |
|---|---|---|---|
| 1 | **GRN entity + PO→GRN→Bill linkage** | Structural — no agent or UI workaround can fake a receipt-of-goods record that doesn't exist. Blocks 3-way match entirely | None — not in platform's own `not_yet_supported` list |
| 2 | **A payment-initiation tool/rail** | `PaymentMade` only records a payment happened; nothing transfers money. Every payments competitor (Mysa included) executes | None |
| 3 | **E-invoicing (IRN/QR/IRP)** | Legally blocks ITC for buyers above ₹5 Cr turnover | GST-28 |
| 4 | **GSTN connectivity (fetch 2A/2B, file returns)** | Fully manual today; GSTR-9 hard-501s regardless of role | GST-39 |
| 5 | **Multi-level configurable approval** | Single approve/reject gate vs. Mysa's up-to-100-level, amount/dept-based chains | None |

Items 3–4 are already tracked; 1, 2, 5 are not — worth filing.

---

## 1. Feature comparison

✅ has it · ⚠️ partial · ❌ absent · **Agent?** = can an agent on our seat close
the gap without a platform change (✅ fully / 🟡 detect-only, can't enforce / ❌ no).

| # | Capability (Mysa claims) | AgentSwitch today | Agent? | Type |
|---|---|---|---|---|
| 1 | AI Scan/OCR: 99% claimed accuracy, extracts GSTIN/PAN/line items | No OCR engine. `BillIntakeEvent` has confidence scoring but nothing to read an image | 🟡 model can read an attachment; unconfirmed whether any tool ingests one into `Bill.create` | Platform |
| 2 | 22+ intake validations (duplicate, amount/vendor mismatch, credit-note detection) | None run natively — our Core Challenge Prompt | ✅ `Bill`/`Invoice.list` + `invoice_matcher.py` logic, once rebuilt on real fields | Platform (agent covers it) |
| 3 | 3-way match (PO↔GRN↔Invoice) | `PurchaseOrder` exists; **no GRN entity in the 425-entity schema** | 🟡 2-way (PO↔Bill) only; GRN leg is impossible to fake | **Structural** |
| 4 | PAN/GSTIN validation + Udyam (MSME) KYC | Fields exist on `Party`; nothing validates them | 🟡 format/checksum only — no registry lookup tool | Platform |
| 5 | Automated TDS (s.194C) + RCM detection | `tds_amount` + GL posting exist; no auto-deduct by section/threshold; no RCM detection; no 26Q/27Q (GST-18) | 🟡 agent can recompute and flag disagreement; can't file | Platform |
| 6 | Multi-level approval (up to 100 levels), spend caps | Single `approval_status` gate, no hierarchy, no caps | 🟡 agent can route via `AgentEscalation`/`AgentTodo`; can't block a payment | Platform |
| 7 | Payment execution across 15+ banks | `PaymentMade` is bookkeeping only — nothing initiates a transfer | ❌ | Platform |
| 8 | Auto-reconciliation (bills/payments/bank) | `BankRule`, `BankTransaction.match_voucher` exist, agent-callable | ✅ (pending a live test of the tool) | Platform (agent covers it) |
| 9 | ERP connectors (Tally, Zoho, ERPNext, NetSuite, SAP) | N/A — AgentSwitch is the ledger, not a connector | ❌ | Category, not a gap |
| 10 | Bill intake via Slack/WhatsApp/email | Email/calendar tools exist on our seat but are out of AP/Tax scope | ❌ | Platform |
| 11 | Custom dashboards/reports | No reports API over MCP — P&L/Balance Sheet/Cash Flow not agent-readable | 🟡 agent can aggregate from `list` calls; costlier than a real endpoint | Platform |
| 12 | GST-branch auto-tagging from invoice GSTIN | Not evidenced in the schema | — unverified either side | Unverified |

**Not a gap vs. Mysa:** GSTR-2B/ITC reconciliation, e-invoicing, GST/TDS return
filing — Mysa's pages don't claim these either. (Clear and CashFlo do; see
`gap_report.md`.)

**Score:** of 11 real gaps, agent fully covers **2** (#2, #8), partially covers
**7** (#1, #4, #5, #6, #11, plus #3's 2-way leg), can't touch **2** (#7, #10).
Ceiling: our seat can *detect* at parity with Mysa but can't *enforce* — no
payment rail, no write access to block a transaction.

---

## 2. What our agent can do that Mysa can't

Tagged **proven** (shipped evidence) / **buildable** (tools exist, not yet built)
/ **structural** (true of the platform regardless of our code).

| Capability | Tag | Evidence |
|---|---|---|
| Audit the ledger's own data integrity, not just the incoming document | **Proven** | 3 tax-data bugs filed (N126–N128, `CURRENT_STATUS.md` §9); 2 of 3 fixed by the platform team, 1 still open |
| Verify a shipped fix actually landed | **Proven** | N127's fix was incomplete — `group_taxes[].tax_type` still holds product names post-fix (§9a) |
| Open-ended cross-entity questions ("MSME exposure + unclaimed ITC together") | **Buildable** | Spans `Party`, `Bill`, `GSTReturn` in one agent loop vs. a fixed dashboard |
| Catch duplicates hiding across the two AP representations | **Buildable** | `Invoice(direction=payable)` (165) and `Bill` (101) both exist; no single-entity check sees across them |
| Two jurisdictions, one system | **Structural** | Same agent serves Suryodaya (GST) and Keystone (US sales tax) via one locale flag |
| Auditable, replayable agent actions | **Structural, not yet used** | `AgentSession`/`AgentEscalation`/`endpoint.job_ledger.*` exist; `run_agent.py` doesn't call them yet |
| Same-day rule changes | **Buildable** | A playbook is a markdown file, not a vendor roadmap request |

---

## 3. Caveats

- Mysa capabilities are untested vendor claims; AgentSwitch capabilities are
  live-verified but the shared ledger drifts, and this snapshot may lag.
- "Agent?" verdicts for #1 (OCR intake) and #8 (auto-reconciliation) assume
  tools that appear in `tools/list` actually work for `finance_user` — not
  confirmed end to end.
- Tax-data trust rule still applies: use `items[].cgst/sgst/igst/cess_amount`
  only. `TaxJurisdiction` and the `Tax` master were fixed 2026-09-22;
  `group_taxes[].tax_type` and `CreditNote.taxes[]` were not (`CURRENT_STATUS.md`
  §7a/§9a).
