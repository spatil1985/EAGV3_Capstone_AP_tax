# Submission Tracker — Identified vs. Filed

Single source of truth for every bug/feature the team has identified, cross-checked
against the **live** `BugReport.list` (`GET /api/bug-report/mine`) — not the class
board (not machine-readable from here; board IDs/statuses are hand-transcribed and
may lag) and not any other doc's summary table, which have been wrong before (see
`agentswitch_submissions.md`'s own correction notes on B7/B8/B9).

**Last verified:** 2026-09-23, via `BugReport.list {"limit": 200}` on the India
account (the only account that can file — Keystone login returns 401 on
`/api/bug-report`). **27 reports** exist on the platform: 15 distinct bugs (4 filed
twice), 8 feature requests (1 board card). Full write-ups for every filed item live
in [`agentswitch_submissions.md`](agentswitch_submissions.md); this document tracks
**status only** — refresh it by re-running `BugReport.list` and diffing against the
tables below, not by re-reading prose.

**To refresh:** log in (`scripts/agentswitch_client.py`), `tools/call BugReport.list
{"limit": 200}`, fingerprint each returned `description` against the "Fingerprint"
column below (exact match on the opening sentence is enough — descriptions run
3,000–4,000 characters and don't change between filings of the same item).

---

## Legend

✅ Filed · 🔴 Not filed · ⛔ Filed but should not have been (duplicate) · ➖ Filed but N/A to bounty (feature)
Board: 🟢 Fixed/live · 🟡 Open/awaiting triage · ⚪ Low, not scheduled · — no board card yet recorded

---

## 1. Bugs — identified vs. filed (15 distinct)

| # | Title | Instance | Identified | Filed? | Platform ID | Filed date | Board | Board status |
|---|---|---|---|---|---|---|---|---|
| B1 | US tax jurisdictions on the India company | India | 21 Sep | ✅ | `2a655790…` | 21 Sep 05:41 | N126 | 🟢 Fixed |
| B2 | `is_group=false` with `group_taxes` children | India | 21 Sep | ✅ | `5c8b16e3…` | 21 Sep 05:41 | N127 | 🟢 Fixed |
| B3 | Tax Summary renders product names as tax heads | India | 21 Sep | ✅ | `84955e11…` | 21 Sep 05:41 | N127 (merged) | 🟢 Fixed |
| B4 | Tax lines storable that the calculator can't produce | India | 21 Sep | ✅ | `834f1301…` | 21 Sep 06:01 | N128 | 🟡 Open |
| B5 | Journal voucher renders ₹0.00 with no lines | India | — | 🔴 | — | — | — | Blocked: needs repro against a concrete `JournalEntry.id` first |
| B6 | N127's fix incomplete — `group_taxes[].tax_type` still corrupt | India | 22 Sep | ✅ | `f9e0c388…` | 22 Sep 05:07 | pending | 🟡 Awaiting triage |
| B7 | Recurring bills regenerate daily (Keystone) | US | 22 Sep | ⛔ **do not file** | — | — | — | Same defect as N6 — filing separately would duplicate it |
| B8 | INR bills + India GST fields on the USD company | US | 22 Sep | ✅ | `5e64a8bc…` | **23 Sep 10:10** | pending | 🟡 Awaiting triage |
| B9 | Locale feature flags contradict tool exposure | US | 22 Sep | ✅ | `70a47383…` | **23 Sep 10:14** | pending | 🟡 Awaiting triage |
| N1 | `ApprovalRequest.is_overdue` wrong on resolved requests (8.6%) | US | 23 Sep | ✅ | `4e8018f7…` | 23 Sep 04:19 | pending | 🟡 Awaiting triage |
| N2 | 3-way match computed but never persisted to the Bill | US | 23 Sep | ✅ | `9fa79e97…` | 23 Sep 04:20 | pending | 🟡 Awaiting triage |
| N3 | `bill_match` tool metadata contradicts its own description | US | 23 Sep | ✅ | `941f6088…` | 23 Sep 04:20 | pending | 🟡 Awaiting triage |
| N4 | Economic-nexus YTD counters stuck at zero | US | 23 Sep | ✅ | `1ef3d577…` | 23 Sep 04:20 | pending | 🟡 Awaiting triage |
| N5 | Tool/product names in `ApprovalRequest.steps[]`/`history[]` | India | 23 Sep | ✅ | `35f7a945…` | 23 Sep 04:20 | pending | 🟡 Awaiting triage |
| N6 | Recurring-bill duplication (India; also covers Keystone/B7) | India + US | 23 Sep | ✅ | `5d6a7f61…` | 23 Sep 04:21 | pending | 🟡 Awaiting triage |
| N7 | TDS deducted independent of base → negative `grand_total` | India | 23 Sep | ✅ | `5664be37…` | 23 Sep 04:21 | pending | 🟡 Awaiting triage |
| N8 | `is_overdue` false-negative rate 74% on India | India | 23 Sep | ✅ | `6ea1df82…` | 23 Sep 04:21 | pending | 🟡 Awaiting triage |

**Duplicate filings (4, on top of the above — same content filed twice, no extra board cards):**

| Duplicate of | Platform ID | Filed |
|---|---|---|
| B1 | `8399b310…` | 21 Sep 05:51 |
| B2 | `c8024248…` | 21 Sep 05:54 |
| B3 | `ca9ec4bf…` | 21 Sep 05:59 |
| B4 | `b98e4e6f…` | 22 Sep 05:05 |

**Bugs filed: 13/15 eligible (B5 blocked, B7 correctly excluded). 2 of 13 already fixed (B1, B2/B3).**

---

## 2. Feature requests — filed batch (F1–F8)

All 8 filed 22 Sep, all collapsed into **one** board card. Feature requests are not
bounty-eligible (100 pts/bug is for defects only) — tracked here for completeness,
not score.

| # | Title | Priority | Filed | Platform ID | Board |
|---|---|---|---|---|---|
| F1 | Goods Receipt Note entity (3-way matching) | High | ✅ 22 Sep 04:37 | `03bc068c…` | N173 ⚪ Low, not scheduled |
| F2 | Sandbox / dry-run flag on write tools | High | ✅ 22 Sep 04:37 | `b21745e1…` | N173 |
| F3 | Expose reports over MCP | Medium | ✅ 22 Sep 04:38 | `ea21ee35…` | N173 |
| F4 | Bank account validation (penny-drop) | Medium | ✅ 22 Sep 04:38 | `a0caffaa…` | N173 |
| F5 | Scoped external-accountant (CA) access | Medium | ✅ 22 Sep 04:38 | `df0dae41…` | N173 |
| F6 | Enable `approvals` app for Seat 03 | Medium | ✅ 22 Sep 04:39 | `3cbfdc17…` | N173 — **half-resolved 23 Sep**: `allowed_apps` now grants `approvals`; `Approval*` MCP tools still missing |
| F7 | Batch / payment-run identity | Low | ✅ 22 Sep 04:40 | `d90a94ad…` | N173 |
| F8 | MSME 45-day statutory payment tracking | Medium | ✅ 22 Sep 04:40 | `b3737f0e…` | N173 |

---

## 3. Feature requests — identified, **not yet written up or filed**

From competitor analysis (D.1) and `spec.md`'s multi-vertical requirements (D.2).
Not on the platform in any form — no `BugReport` record matches any of these.

### D.1 — competitor gaps (F9–F17)

| # | Title | Priority | Filed? |
|---|---|---|---|
| F9 | OCR / AI invoice extraction | **High** | 🔴 Not filed |
| F10 | Payment initiation / execution rail | **High** | 🔴 Not filed |
| F11 | Vendor identity validation (PAN/GSTIN/Udyam) | Medium | 🔴 Not filed |
| F12 | ERP / Tally connectors | Medium | 🔴 Not filed |
| F13 | Bill intake via email/Slack/WhatsApp | Low | 🔴 Not filed |
| F14 | Historical cashflow analytics | Low | 🔴 Not filed |
| F15 | Payout lifecycle/stage tracking | Low | 🔴 Not filed |
| F16 | Spend caps / budget controls on approvals | Medium | 🔴 Not filed — **verify against `ApprovalPolicy.condition_*` first** (F6 was wrong this way once already) |
| F17 | Supply-chain finance / early-payment discounting | Low | 🔴 Not filed |

### D.2 — multi-vertical statutory gaps (F18–F22, from `spec.md`)

| # | Title | Priority | Verticals blocked | Filed? |
|---|---|---|---|---|
| **F18** | **ITC apportionment, Rule 42/43** | **High** | School, clinic | 🔴 Not filed — **strongest unfiled item in this document; file on its own, not batched** |
| F19 | Job work, s.143 / ITC-04 | Medium | Manufacturing | 🔴 Not filed |
| F20 | Composition-scheme mode, s.10 | Medium | Retail | 🔴 Not filed |
| F21 | LUT / export-declaration registry | Low-Med | Agency | 🔴 Not filed |
| F22 | s.52 e-commerce TCS | Low | Retail (marketplace) | 🔴 Not filed |

---

## 4. Explicitly do-not-file

| Item | Why |
|---|---|
| B7 (recurring bills, Keystone) | Duplicate of N6 — already filed and covers both instances |
| Tool-count delta between instances (436 vs 446–447 vs 468 over time) | Not defensible as a standalone finding; B9 already captures the defensible part with direct flag-vs-tool evidence |
| `spec.md` buildable use cases (UC-01 Rule 37, UC-03/UC-21 RCM, UC-16 blocked credit, UC-06 approval audit) | No platform change needed — these are agent backlog, not platform requests. Filing them would misrepresent work the team can already do |

---

## Summary counts

| Category | Identified | Filed | Not filed | Fixed |
|---|---|---|---|---|
| Bugs (distinct) | 17 (incl. B7, B5) | 13 | 2 (B5 blocked, B7 excluded) | 2 (B1, B2/B3) |
| Duplicate bug filings | — | 4 | — | — |
| Feature requests (F1–F8) | 8 | 8 | 0 | — (1 unscheduled card) |
| Feature requests (F9–F22) | 14 | 0 | 14 | — |
| **Total platform filings** | | **27** | | |

**Biggest gaps between "identified" and "filed": F9–F22 (14 feature requests fully
written up in `agentswitch_submissions.md` §D but never submitted) and F18
specifically, which the team's own analysis calls its strongest unfiled ask.**
