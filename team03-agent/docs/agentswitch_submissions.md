# AgentSwitch — Bug Reports & Feature Requests (Team 03, Seat 03 Payables & Tax)

Consolidated, submission-ready list of everything we've found on the AgentSwitch
platform: confirmed defects, plus feature gaps from two sources — comparison against
real competitor products, and the multi-vertical requirements in
[`spec.md`](spec.md) (school, manufacturing, clinic, retail, agency under Indian tax
law).

**Submission channel:** `POST /api/bug-report` (per the brief, §Week 4 Milestone 2 —
100 points per *verified* bug). Body fields: `description` (required), `page`,
`agent_seat`, `job_id`. `reporter` and `app_version` are server-stamped and are
deliberately not settable by the reporter.

**Scoring note:** the brief's bug bar asks for reproducible steps, expected vs.
actual, **job ID**, and entity IDs. Everything below has steps, expected/actual and
entity IDs. **None has a `job_id`**, because all were found by direct REST/MCP
inspection rather than an agent run. Wiring `run_agent.py` to create an
`AgentSession`/`AgentTask` would let future findings carry one.

**Do not submit §3.** Those items are already self-documented by the platform in the
locale endpoint's `not_yet_supported` list and would likely be rejected as known.

---

## Status summary

**Verified against `GET /api/bug-report/mine`, 2026-09-23:** 25 reports on the India
account, 0 on Keystone. Every report was **fingerprinted by description content**,
not by assumed order — an earlier revision of this table mapped the 09-23 batch by
position and got one item wrong.

> ⚠️ **Correction (supersedes the previous revision).** This document previously
> listed **B7 as unfiled and "file it first."** That was wrong.
> **B7's defect is already reported — as N6.** N6 (filed 23 Sep,
> `5d6a7f61-fed9-4ad7-b430-31b52595f15c`) describes the same scheduler defect
> (`next_bill_date` never advancing), covers the India instance, *and* explicitly
> names Keystone. **Filing B7 separately would create a duplicate** — precisely the
> mistake §B exists to prevent.
>
> Only **B8, B9 and B5** remain genuinely unfiled. See §C.

> 📋 **What this document can and cannot see.** `GET /api/bug-report/mine` is
> authoritative for *what we submitted*. The class bug board is **not machine-
> readable** — its rows load dynamically, so a fetch returns only the template.
> Board IDs and statuses below were transcribed from screenshots and may lag.
> **N1–N8 were filed on 23 Sep and will have been triaged onto the board with new
> board IDs that are not recorded here yet.**

---

### A · FILED (21 filings → 13 distinct issues)

**Defects**

| # | Title | Instance | Filed | Board | Status |
|---|---|---|---|---|---|
| B1 | US tax jurisdictions on the India company | India | 21 Sep | **N126** | ✅ **Fixed, live on server** |
| B2 | `is_group=false` with `group_taxes` children | India | 21 Sep | **N127** | ✅ **Fixed, live on server** |
| B3 | Tax Summary renders product names as tax heads | India | 21 Sep | merged **N127** | ✅ **Fixed** |
| B4 | Tax lines storable that the calculator can't produce | India | 21 Sep | **N128** | 🔴 Open (Medium) |
| B6 | N127's fix is incomplete — `group_taxes[].tax_type` | India | 22 Sep | pending | ⏳ Awaiting triage |
| N1 | `is_overdue` wrong on resolved requests (8.6%) | US | 23 Sep | pending | ⏳ Awaiting triage |
| N2 | 3-way match computed but never persisted to Bill | US | 23 Sep | pending | ⏳ Awaiting triage |
| N3 | `bill_match` metadata contradicts its description | US | 23 Sep | pending | ⏳ Awaiting triage |
| N4 | Economic-nexus YTD counters stuck at zero | US | 23 Sep | pending | ⏳ Awaiting triage |
| N5 | Tool names in `ApprovalRequest.steps[]`/`history[]` | India | 23 Sep | pending | ⏳ Awaiting triage |
| N6 | Recurring-bill duplication + expired template firing | India | 23 Sep | pending | ⏳ Awaiting triage |
| N7 | TDS independent of base → negative `grand_total` | India | 23 Sep | pending | ⏳ Awaiting triage |
| N8 | `is_overdue` false negatives 74%, bulk-resolve cluster | India | 23 Sep | pending | ⏳ Awaiting triage |

*"Instance" = the company the defect is **about**. Every one of the 28 filings sits
on the **India** account's `bug-report/mine` — the Keystone-company findings
(N1–N4) were filed from there too, which is why the Keystone account reads 0.*

**Feature requests** — F1–F8 filed 22 Sep, collapsed into one board card. F18 filed
separately 23 Sep, **on its own** per its own priority recommendation (see §5) —
not yet triaged onto the board.

| # | Title | Filed | Board |
|---|---|---|---|
| F1–F8 | GRN · sandbox · reports over MCP · bank validation · CA access · approvals entitlement · batch payment-run · MSME 45-day | 22 Sep | **N173** ⚪ Low · *Carbon upgrade* · not scheduled |
| F18 | ITC apportionment, Rule 42/43 (blocks School + Clinic verticals) | 23 Sep, `a9f1888f…` | pending — not yet triaged |

---

### B · DUPLICATES — already on the platform twice, do not re-file

| Platform id | Filed | Duplicate of |
|---|---|---|
| `8399b310-96df-4a5d-b02a-66ea5aab4bc1` | 21 Sep 05:51 | B1 (`2a655790…`, already N126) |
| `c8024248-b974-4b1e-81fd-c90cbe9c5286` | 21 Sep 05:54 | B2 (`5c8b16e3…`, already N127) |
| `ca9ec4bf-d7c3-4a60-b24c-2c0c21fc4daf` | 21 Sep 05:59 | B3 (`84955e11…`, merged N127) |
| `b98e4e6f-7c43-4d61-bbf5-b59c29b1653e` | 22 Sep 05:05 | B4 (`834f1301…`, already N128) |

Each was filed once via the API and again by hand ten to twenty minutes later.
Nothing to undo — but worth telling the instructor so triage doesn't process them
twice.

**Merge risk, not duplicates:** **N1 and N8** are the same defect class on different
instances, filed two minutes apart. Expect one board card. Both are still worth
having — N1 carries the `check_sla` oracle proving the live logic is *correct*
before showing where it breaks; N8 carries the volume (74%) and the bulk-resolve
timestamp cluster pointing at a root cause.

---

### C · NOT FILED — the complete list

**Three items. Everything else in this document is already on the platform.**

| # | Title | Instance | Severity | Status / re-verification 2026-09-23 |
|---|---|---|---|---|
| **B8** | INR-denominated bills + India GST fields on the USD company | US | **Medium** | ✅ **Not filed** — 0 content matches across all 25 reports. 🔺 **Now 13 INR bills**, was 10 — growing, because the N6 scheduler defect keeps generating them |
| **B9** | Locale feature flags contradict MCP tool exposure | US | **Low-Med** | ✅ **Not filed.** Still reproduces exactly: `eway_bill=false` → **8** EWayBill tools (was 6); `form_1099=true` → **0** tools; 490 tools visible |
| **B5** | Journal voucher renders ₹0.00 with no line items | India | Medium | ✅ Not filed — ❗**needs reproduction** against a concrete `JournalEntry.id` first. Do not file until `JournalEntry.get` confirms whether `lines` is populated |

#### Reclassified — do NOT file

| # | Why not |
|---|---|
| ~~**B7**~~ Recurring bills regenerate daily | **Already reported as N6** (`5d6a7f61…`, 23 Sep). N6 covers the same `next_bill_date` defect, on India, and explicitly names Keystone. Filing B7 would duplicate it. If the board wants the US instance called out separately, **add it as a comment on N6's card** rather than as a new report |

**File B8 first** of the remaining three. It is verified-still-live, actively
worsening, and pairs naturally with the already-fixed B1/N126 — the same
wrong-jurisdiction seed-data defect in the opposite direction, which gives triage an
obvious precedent to attach it to.

---

### D · NEW — gaps identified but not yet written up

**Two sources, kept separate because they argue differently:**

- **D.1 — competitor gaps (F9–F17).** "A competitor ships this and we don't."
- **D.2 — multi-vertical gaps (F18–F22).** From [`spec.md`](spec.md): "Indian tax
  law requires this and we cannot represent it." These are **statutory**, not
  competitive — the argument is compliance exposure, not feature parity, which is a
  stronger case to make to a platform team.

---

#### D.1 · Competitor gaps

From `razorpay_gap_report.md`, `clear_gap_report.md` and `gap_report_mysa.md`,
cross-checked against F1–F8. **None of these is covered by an existing request.**
Numbered F9+ to continue the series; full write-ups not yet drafted.

| # | Gap | Priority | Who has it | Note |
|---|---|---|---|---|
| **F9** | **OCR / AI invoice extraction** | **HIGH** | All six — Mysa #1 ("99% accuracy"), Clear ("OCR ingestion"), RazorpayX | **Biggest omission in the whole list.** AgentSwitch has no OCR engine; this is the entry point to the entire AP automation pipeline |
| **F10** | **Payment initiation / execution rail** | **HIGH** | Mysa (#2 of its own top-5), RazorpayX **[LIVE]** | F7 covers only batch *identity* and explicitly notes we "cannot execute payments at all" — the underlying gap was observed but never filed |
| F11 | Vendor identity validation (PAN / GSTIN / Udyam registry) | Medium | Mysa #4, Clear | Distinct from F4, which is **bank-account** validation only |
| F12 | ERP / Tally connectors | Medium | RazorpayX **[LIVE]** Tally Payouts, Clear (8 named), Mysa | `gap_report_mysa.md` calls this "category, not a gap" — worth a deliberate decision rather than silent omission |
| F13 | Bill intake via email / Slack / WhatsApp | Low | Mysa #10 | |
| F14 | Historical cashflow analytics | Low | RazorpayX **[LIVE]** Insights | F3 is reports-over-MCP; this is backward-looking trend analytics. Ours is forward *simulation* only |
| F15 | Payout lifecycle / stage tracking | Low | RazorpayX **[LIVE]** | Only meaningful once F10 exists |
| F16 | Spend caps / budget controls on approvals | Medium | Mysa #6 | ⚠️ **Verify before filing** — `ApprovalPolicy.condition_field/operator/value` may already express these. Exactly the trap F6 fell into |
| F17 | Supply-chain finance / early-payment discounting | Low | Clear §5.1 | Clear's genuine differentiator; out of Seat 03 scope |

**Not a platform request — belongs in our own code backlog.** `clear_gap_report.md`
§9.1: Clear keys duplicate detection on *document number + FY + vendor/buyer GSTIN*
(a document identity), while `scripts/invoice_matcher.py` uses amount-proximity
within ±3 days (a heuristic) — which **already produced three false positives** on
Keystone against recurring templates. Fix the matcher; don't file it.

---

#### D.2 · Multi-vertical statutory gaps (from `spec.md`)

`spec.md` specifies the agent across five Indian organisation types — school,
manufacturing, clinic, retail, agency — and identifies six platform gaps. **One is
already filed (GAP-4 = F1, the GRN entity), so five are new.**

These are worth filing separately from D.1 because the argument is different: each
blocks a *statutory obligation* that the platform's data model cannot represent, not
a feature a rival happens to ship.

| # | Gap (spec.md ref) | Priority | Verticals blocked | Why it cannot be orchestrated around |
|---|---|---|---|---|
| **F18** ✅ **FILED** `a9f1888f…` (23 Sep) | **ITC apportionment, Rule 42/43** (GAP-1) | **HIGH** | **School, clinic** (2 of 5) | No exempt-turnover aggregate and no apportionment engine. `itc_eligibility` is a per-document enum, not a proportion. The agent can compute and *report* the ratio, but **`JournalEntry` is read-only for `finance_user`**, so it cannot post the reversal — reporting without posting leaves the books wrong. **This is the capability Clear monetises separately as MaxITC** |
| **F19** | **Job work, s.143 / ITC-04** (GAP-2) | Medium | Manufacturing | No `job_work` concept anywhere in the 468 tools or the schema. `DeliveryChallan` is the right document type but has no job-work subtype or return-tracking. Goods not returned in 1 year (inputs) / 3 years (capital goods) become a **deemed supply** — timing that cannot be tracked against a document type that does not exist |
| **F20** | **Composition-scheme mode, s.10** (GAP-3) | Medium | Retail (small traders) | `business_composition` exists only as a *counterparty* attribute on `gst_treatment`. The organisation's **own** tax mode is not representable, so threshold monitoring and breach detection are impossible |
| **F21** | **LUT / export-declaration registry** (GAP-5) | Low-Med | Agency | No entity models a Letter of Undertaking or its validity period. Exporting services without a valid LUT means IGST must be paid and reclaimed. Closest workaround is abusing `TaxExemption.exemption_reason` |
| **F22** | **s.52 e-commerce TCS** (GAP-6) | Low | Retail (marketplace sellers) | No TCS-collected-by-operator concept; a marketplace seller cannot reconcile operator-collected TCS against their own returns |

**F18 is the strongest feature ask in this entire document, and it is now filed** —
`a9f1888f-dd7d-4884-b5dc-c5f17fd944a9`, 23 Sep 2026 16:02, filed on its own rather
than batched with F19–F22, per §5's own recommendation. It blocks two of five
verticals outright, the computation is *already possible* from data we hold — only
the posting is not — and it is the one capability in `spec.md` §3 that no competitor
in our set (RazorpayX, Clear, Mysa) names as shipped. Full submitted text is in §4
below.

**Buildable today — agent backlog, not submissions.** `spec.md` identifies fourteen
use cases needing **no platform change**, notably UC-01 (Rule 37 — ITC reversal when
a supplier goes unpaid past 180 days), UC-03/UC-21 (RCM exposure), UC-16 (expiry →
blocked credit under s.17(5)(h)) and UC-06 (approval audit). **Do not file these** —
they are ours to build. UC-01 in particular is the highest-value cross-vertical
capability found and no competitor names it.

---

**Already covered, do not re-file:** GRN→F1 *(= spec.md GAP-4)* · sandbox→F2 ·
reports→F3 · bank validation→F4 · CA access→F5 · approvals→F6 · batch run→F7 ·
MSME→F8 *(= spec.md UC-04)*.
**Already in §3 (platform self-documented):** e-invoicing GST-28 · GSTN fetch
GST-39 · TDS automation GST-18 *(covers spec.md UC-09/UC-13's filing half)*.

---

### What the fixes tell us

**N126** — fixed by commit `c3986d40e`: *"the India company now uses Indian GST
states and union territories · existing records are corrected when the next release
goes out."*

**N127** — fixed by two commits. `92682d0a3` fixes the data at source, and
`4c812eb0f` *"makes the Tax Summary show an unclassifiable row as Unclassified and
leave it out of the total."* **That is precisely the fix this report recommended** —
that the report should refuse to present a row it cannot classify as a tax head,
rather than summing it into output tax.

**The blast radius was far larger than we found.** The fix note records
**8,535 tool-named values across 85 fields, in both apps**, all corrected in a
rehearsal on copies of live data. We identified the pattern in roughly three fields
on two entities. The report triggered a sweep ~28× wider than our own sample.

**N127 shares a root cause with pre-existing bug N116** (*"the demo data wrote
product names into unrelated records"*). So the data half overlapped a known issue;
the report-layer half — Tax Summary presenting and totalling unclassifiable rows —
appears to be our distinct contribution, and is what the second commit addresses.

### Scoring lesson — features are not bugs

All five feature requests (F1–F5) were collapsed into **one** board card, **N173**,
tagged *Carbon upgrade* — which the board defines as *"separate product features
being added (not defects)"* — at **Low** severity and **not scheduled**.

The bounty is 100 points per **verified bug**. Feature requests appear to earn
nothing toward it. Five carefully argued requests produced one unscheduled Low card.

**Implication: to move the score, file defects, not feature requests.** The nine new
gaps in §D should be raised for product value, not bounty value. Time is better
spent on the schema-invariant sweep that produced N126–N128 and, now, N1–N8.

**Evidence so far:** 13 distinct defects filed → 3 board cards, 2 already fixed in
production. 8 feature requests filed → 1 unscheduled Low card.

---

## 1. Bugs — filed

### B1 · US tax jurisdictions on an India-locale company **[FILED `2a655790…`]**

**Severity:** High · **Area:** Tax / Settings

All 100 `TaxJurisdiction` rows on Suryodaya (India) have `country="US"` with
US-only `jurisdiction_level` values (special_district 33, county 25, city 22,
state 20) and 18 with `has_nexus=true` — while `GET /api/accounting/locale` reports
`features.sales_tax_jurisdictions=false` and `sales_tax_nexus=false` for India.
Indian GST has no county/special-district jurisdiction or nexus-sourcing concept.

Sample `c6fc62d8-180d-4dde-bc9e-01b36cce2f5f`: `name="Depth Gauge 301mm (Kg)"`,
`country="US"`, `city="Thane"` (an Indian city), `county="File Set 9004"`,
`state_code="VP3433/9004"`, `sourcing="origin"`, and `liability_account_id`
pointing at **"Unsecured Loans"** — a loan account as a tax liability account.

**Impact:** `Tax.jurisdiction_id` links to these, so if the GST computation path
reads `TaxJurisdiction`, Indian GST routes through US nexus logic.

---

### B2 · `is_group=false` with `group_taxes` children **[FILED `5c8b16e3…`]**

**Severity:** Medium · **Area:** Tax / Settings

67 of 100 `Tax` rows have `is_group=false` yet carry `group_taxes` children (16 are
correctly flagged, 17 have no children). Visible in the UI: Tax "V-Block Pair 5131"
shows "Is Group: No" while a GROUP TAXES section below lists a component.

Related: `group_taxes[].tax_type` is unconstrained free text — **0 of 88** populated
values match the `Tax.tax_type` enum, while the *parent* `Tax.tax_type` correctly
enforces it on the same records.

**Impact:** no consumer can decide whether to expand a composite tax; the flag and
the data disagree on two-thirds of the tax master.

---

### B3 · Tax Summary renders product names as tax heads **[FILED `84955e11…`]**

**Severity:** High · **Area:** Reports / Tax

The Tax Summary report (01-04-2026 → 21-09-2026) lists rows labelled
"Hex Key Set 7355", "V-Block Pair 7359", "Drill Chuck 7357" etc. under OUTPUT TAX
(SALES), and includes their amounts in the Total of ₹1,08,80,907.12. The report
groups by `CreditNote.taxes[].tax_type`, declared `"type": "text"`. Each row maps
to the paisa to one credit note.

The six rows total ₹4,991.76, while those documents' own `total_tax` sums to
₹62,402.95 — the report counts amounts the documents themselves exclude.

> **Note:** consider asking for this to be split against B4, or reference B4 as the
> data-layer half. Filed as one report before the split was identified.

---

### N1 · `ApprovalRequest.is_overdue` is wrong on resolved requests, in both directions **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** High · **Area:** Approvals (Bill/PurchaseOrder/Invoice approval workflow)

```
ENVIRONMENT
Company: Keystone Precision Works LLC (c1e47d8d-b849-4187-9a32-4103d3dece4a)
Role: finance_user. allowed_apps now includes "approvals" (this was blocked at F6
time — worth noting the entitlement gap from F6 appears resolved on this account).

SUMMARY
is_overdue is computed correctly for currently-open requests -- verified against the
platform's own oracle, endpoint.approvals.check_sla (dry_run=true, non-mutating):
it independently re-evaluated all 29 active requests and its "breached" list matched
the stored is_overdue=true flag on all 27 of them exactly, 0 mismatches. So the
live SLA logic itself is right.

The defect is that this correct computation is never re-applied, or is applied
incorrectly, once a request resolves. Comparing resolved_at against sla_deadline for
every request with status in (approved/rejected/recalled) that carries both
timestamps (93 of 122 total requests):

  8 of 93 (8.6%) have an is_overdue flag that contradicts resolved_at vs
  sla_deadline:

  FALSE NEGATIVE -- resolved AFTER the deadline (genuinely late) but is_overdue=0:
    6d40c70c-49c5-4306-a3aa-4491391501ae  APR-2026-00121  Invoice INV-2026-00125
      sla_deadline=2026-07-07T10:00:00  resolved_at=2026-07-14T15:20:00  (7d late)
    68c8012a-cc7a-464f-a710-08e63d44f5dd  APR-2026-00120  Invoice INV-2026-00130
      sla_deadline=2026-07-13T09:00:00  resolved_at=2026-07-16T13:30:00  (3d late)
    96f182c3-7972-449d-91fc-bc04dac8b9b7  APR-2026-00116  Invoice INV-2026-00135
      sla_deadline=2026-07-22T09:30:00  resolved_at=2026-07-22T12:00:00  (2.5h late)
    c307731d-9a5d-4e77-b927-767682519240  APR-2026-00111  PurchaseOrder PO-2026-00002
      sla_deadline=2026-08-19T08:15:00  resolved_at=2026-08-23T04:03:00  (~4d late)

  FALSE POSITIVE -- resolved BEFORE the deadline (on time) but is_overdue=1:
    14106018-9de9-4203-8593-6e71422f0b46  APR-2026-00107  PurchaseOrder PO-2026-00040
      sla_deadline=2026-09-17T16:45:54  resolved_at=2026-09-16T16:45:54  (1d early)
    2dc082aa-3ce8-4e8a-ad15-116ece6a8168  APR-2026-00095  Contract CTR-2026-00001
      sla_deadline=2026-09-18T16:45:01  resolved_at=2026-09-16T16:45:01  (2d early)
    b41479c3-c611-4d3c-b570-13e7525292b0  APR-2026-00052  PurchaseOrder PO-2026-00014
      sla_deadline=2026-09-17T16:44:58  resolved_at=2026-09-16T16:44:58  (1d early)
    c40f9c59-ce22-4774-bd12-7ac4408da005  APR-2026-00046  PurchaseOrder PO-2025-00007
      sla_deadline=2026-09-17T16:44:58  resolved_at=2026-09-16T16:44:58  (1d early)

6 of the 8 are on core AP documents (3 PurchaseOrder, 3 Invoice); 1 is a Contract.

REPRODUCTION
1. tools/call ApprovalRequest.list {"limit": 200} -- 122 records.
2. tools/call endpoint.approvals.check_sla {"dry_run": true} -- 29 checked, 27
   breached; compare request_id set against ApprovalRequest.is_overdue=true among
   the 29 still-open records: exact match, 0 discrepancies (proves the live logic
   is correct).
3. For every resolved request (status in approved/rejected/recalled) with both
   sla_deadline and resolved_at populated, compare resolved_at > sla_deadline
   against the stored is_overdue flag: 8 of 93 disagree (listed above).

EXPECTED
When a request resolves, is_overdue should be finalized to whether resolution beat
the SLA deadline (same logic the dry-run check already gets right for open requests)
and then stop changing.

ACTUAL
is_overdue on a resolved request does not reliably reflect resolved_at vs
sla_deadline. It appears to freeze at some earlier value rather than being
finalized on resolution -- explaining both directions of error (a request that was
overdue *before* being approved keeps a stale true even after an on-time-relative-
to-that-earlier-check resolution, and vice versa). Root cause not confirmed --
this is the observable symptom.

IMPACT
Any SLA/compliance dashboard, report, or agent that trusts the stored is_overdue
field on closed approvals -- e.g. "how many PO approvals breached SLA this
quarter" -- undercounts real breaches (the 4 false negatives) and overcounts on two
Invoice approvals and overstates blame on two PurchaseOrder approvers (the false
positives). This directly affects AP: PurchaseOrder and Invoice approval SLA
compliance is exactly the kind of metric Seat 03 (Payables & Tax) would be asked to
report on or act on (e.g. escalate approvers with real SLA breaches).

ENTITY IDS
Company: c1e47d8d-b849-4187-9a32-4103d3dece4a
ApprovalRequest ids: see the 8 listed above.
No job_id -- found by direct REST/MCP inspection, cross-verified against the
platform's own endpoint.approvals.check_sla oracle.
```

---

### N2 · 3-way match result is computed correctly but never persisted to the Bill **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** Medium · **Area:** Accounts Payable / PO↔Bill matching

```
ENVIRONMENT
Company: Keystone Precision Works LLC (c1e47d8d-b849-4187-9a32-4103d3dece4a)

SUMMARY
endpoint.accounting.bill_match ("C-048") computes a real three-way match (PO rate
vs billed rate, ordered/received/billed-to-date quantities, tolerance status) for
any Bill with a purchase_order_id, and it works -- no errors, sensible output. But
its own response distinguishes a "live" (just-computed) result from a
"recorded_status" (what's persisted on the Bill), and recorded_status is null on
every single bill tested.

This means Bill.match_status and Bill.match_detail -- real schema fields, present
in every Bill record's _readonly_fields (i.e. the platform itself treats them as
system-computed, not user-editable) -- are permanently empty. Nothing that reads
the Bill directly (a list view, a report, another tool) can see match status; only
a caller who separately invokes this specific endpoint per-bill ever sees it, and
even then the result is never written back.

REPRODUCTION
1. tools/call Bill.list {"limit": 200} -- 91 bills, 81 carry purchase_order_id.
2. Note Bill.match_status / Bill.match_detail are null on all 91 (also visible
   directly on Bill.list, no compute needed).
3. tools/call endpoint.accounting.bill_match {"bill_id": <id>} for all 81 PO-linked
   bills. Every call succeeds (isError=false) and returns a populated "live" object
   (e.g. status="within_tolerance", real ordered/billed quantities and rates).
4. Every one of the 81 responses carries "recorded_status": null.

Sample: BILL-2026-00081 (6d7e27f8-e0e3-4bc5-af60-f5e2e9d6ea74), PO
db9baf58-dc1b-4dd6-9c37-4aeace5afa85 -- live.status="within_tolerance",
recorded_status=null. Same pattern on all 81/81 sampled.

EXPECTED
Either the compute endpoint should write live.status/live back onto
Bill.match_status/match_detail (matching what the read-only-field declaration
implies the platform intends), or Bill.list/Bill.get should expose a live-computed
value instead of a permanently-null stored one.

ACTUAL
match_status/match_detail read null everywhere, with no code path found that ever
sets them, despite a working, callable compute existing.

IMPACT
The "2-way/3-way match" capability the earlier gap report rated as a theoretical,
partial capability ("PO<->Bill matching is possible") turns out to have a working
compute endpoint underneath -- which makes this a sharper finding: the capability
isn't missing, it's built but disconnected from the document it's supposed to
annotate. Any consumer that reasonably expects Bill.match_status to reflect match
state (approval routing, a vendor-bill list screen, a report) sees nothing, 100%
of the time, regardless of whether the underlying match is clean or has a real
variance.

ENTITY IDS
Company: c1e47d8d-b849-4187-9a32-4103d3dece4a
Sample bill: 6d7e27f8-e0e3-4bc5-af60-f5e2e9d6ea74 (BILL-2026-00081)
Affects: all 81 of 81 PO-linked Bills sampled.
No job_id -- found by direct REST/MCP inspection.
```

---

### N3 · `bill_match` tool metadata contradicts its own description (read-only vs WRITE) **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** Low · **Area:** API / MCP tool metadata · **Related to N2**

```
SUMMARY
endpoint.accounting.bill_match's description opens with "Read-only three-way match
of one Bill..." -- but the tool's own annotations and _meta disagree with that:

  "annotations": {"readOnlyHint": false, "destructiveHint": false,
                   "idempotentHint": false}
  "_meta.agentswitch": {"permission": "Bill.read", "risk": "WRITE"}

A read permission (Bill.read) paired with a WRITE risk classification, on a tool
whose own prose says "read-only," is an internal contradiction in the tool's
self-description -- the three signals (description text, readOnlyHint, risk tag)
don't agree with each other.

REPRODUCTION
1. tools/list -> find "endpoint.accounting.bill_match".
2. Compare description ("Read-only three-way match...") against
   annotations.readOnlyHint (false) and _meta.agentswitch.risk ("WRITE").

EXPECTED
A tool documented as read-only should carry readOnlyHint=true and a READ risk tag,
consistent with its stated behavior (and with what N2 independently confirms: the
call never writes anything, since recorded_status stays null after every call).

ACTUAL
The metadata says WRITE/not-read-only while the description and observed behavior
(N2) are both consistent with read-only.

IMPACT
Low direct impact (the call is in fact safe to invoke, per N2), but any
orchestrator or agent that gates tool calls by risk/readOnlyHint rather than
parsing free-text descriptions would apply unnecessary write-confirmation friction
to what is actually a lookup -- or, in the opposite failure mode, an agent that
trusts the description text alone and skips a write-safety check could be caught
out on some other tool with the same mismatch pattern that turns out to actually
write. Worth a metadata sweep for the same description-vs-annotation disagreement
on other endpoint.* tools.

ENTITY IDS
N/A -- tool-definition-level finding, not a data record.
```

---

### N4 · Economic-nexus YTD sales/transaction counters are stuck at zero on active, registered nexus **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** Medium · **Area:** Tax / Sales & Use Tax (US)

```
ENVIRONMENT
Company: Keystone Precision Works LLC (c1e47d8d-b849-4187-9a32-4103d3dece4a),
US locale, tax_regime "sales_use_tax".

SUMMARY
TaxNexus.list returns 4 records (IL, MI, PA, OH). 3 of 4 are is_registered=1 /
status="active" with real state registration numbers, "effective_from": "2023-09-17"
-- i.e. the platform's own data says this company has been legally required to
collect and remit sales tax in Michigan, Pennsylvania and Ohio for roughly three
years. Yet every one of the 4 records shows:

  "ytd_sales_amount": 0.0
  "ytd_transaction_count": 0.0

despite the company having 127 receivable Invoices and (per a related finding
already on file, B8) USD 226,488.27 of recorded output tax. Nothing is
incrementing these counters from actual invoice activity.

The Illinois record is the sharpest internal contradiction: it is the one nexus
still in "monitoring" (not yet registered) status, and its own free-text note says
"Approaching the economic threshold — watched, not collected" -- a qualitative
claim that directly contradicts its own quantitative field, ytd_sales_amount=0.0.
You cannot be "approaching" a $100,000 / 200-transaction threshold while your
tracked year-to-date sales are recorded as exactly zero.

REPRODUCTION
1. tools/call TaxNexus.list {"limit": 200} -- 4 records.
2. For each: is_registered, status, economic_threshold_amount (100000.0 on all 4),
   economic_threshold_transactions (200.0 on all 4), ytd_sales_amount (0.0 on all
   4), ytd_transaction_count (0.0 on all 4).
3. Illinois record (4a70d682-f7b6-45f3-a15b-663404a8d6fa): status="monitoring",
   notes="Approaching the economic threshold — watched, not collected.",
   ytd_sales_amount=0.0 -- the note and the field disagree.
4. Cross-check against real invoicing activity: Invoice.list shows 127
   receivable invoices exist for this company (see B8 in agentswitch_submissions.md
   for the output-tax total).

EXPECTED
ytd_sales_amount / ytd_transaction_count should reflect actual invoiced sales
attributable to each nexus state over the year, so a state genuinely approaching
its economic threshold is flagged before the legal registration obligation is
missed. A "monitoring" nexus's own note text should be consistent with its own
numeric fields.

ACTUAL
The counters are inert -- 0.0 on all 4 nexus regardless of registration status or
real invoicing volume -- and the IL note text asserts a threshold-approach
condition its own field contradicts.

IMPACT
This is the mechanism that is supposed to catch a company crossing into a new
state's economic-nexus tax obligation. If it never updates, an agent or user
relying on TaxNexus to answer "are we approaching a new filing obligation
anywhere?" gets a uniformly reassuring "no" regardless of actual sales
distribution by state -- a real compliance-risk blind spot, and adjacent to (but
distinct from) the already-documented tax_rate_service gap (which covers rate
lookup/filing, not economic-threshold monitoring).

ENTITY IDS
Company: c1e47d8d-b849-4187-9a32-4103d3dece4a
TaxNexus: 4a70d682-f7b6-45f3-a15b-663404a8d6fa (IL, monitoring),
          61066fea-7c8c-4568-877f-47641211889d (MI, active),
          9d87f28e-facb-4265-91ce-e01fff5e02ee (PA, active),
          f39e96bb-1f7f-46dd-8992-65bd6568478b (OH, active)
No job_id -- found by direct REST/MCP inspection.
```

---

### Instance 2: Suryodaya (India) -- N5-N8

Added 2026-09-23, once `.env` carried separate India (`AGENTSWITCH_*`) and US
(`US_AGENTSWITCH_*`) credentials. Same method as N1–N4, run against
`https://agentswitch.theschoolofai.in`, company `5cbe5a55-af74-4363-a436-f5350593114c`
(Suryodaya Precision Works Pvt. Ltd.), 468 tools visible (identical tool count/role
scope to Keystone — see `mcp_tool_inventory_india.md`).

---

### N5 · Tool/product-name + non-integer corruption in `ApprovalRequest.steps[]`/`history[]` — a third location for the N126/N127 defect class **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** High · **Area:** Approvals / data integrity

```
ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)

SUMMARY
The already-fixed-twice defect class behind N126 (US tax jurisdictions on the India
company) and N127 (tool names in Tax records) -- where the demo-data seeder's
tool/product-name generator leaks into fields that are supposed to hold structured
data -- is present in a THIRD location that the N127 fix's "8,535 values across 85
fields" sweep evidently did not reach: ApprovalRequest.steps[] and .history[].

On ApprovalRequest APR-2026-00100 (id a7b92cf9-4681-44d2-8db3-6cc1c9347ffb),
steps[0] reads:
  "approver_id": "Punch Set 945"        <- should be a UUID
  "approver_role": "Angle Plate 945"    <- should be a role like "admin"/"finance_manager"
  "delegated_from_name": "Hex Key Set 945"
  "level": 262.43                       <- an approval level should be a small integer
  "order": 578.07                       <- likewise

On APR-2026-00070 (id ec853b5f-4fe9-41ff-a120-0b9b6ad3ce5a):
  "total_levels": 447.22                <- a count of approval levels, not a decimal
  steps[0].level: 447.22                <- same bogus value echoed into the step
  history[].actor_name: "Bench Vice 915" <- should be a person's name

REPRODUCTION
1. tools/call ApprovalRequest.list {"limit": 200} on the Suryodaya instance.
2. Inspect any record's steps[]/history[] arrays: approver_id, approver_role,
   delegated_from_name and actor_name hold tool/product names
   ("Punch Set 945", "Angle Plate 945", "Hex Key Set 945", "Bench Vice 915" are four
   distinct samples from two different records); level/order/total_levels hold
   decimal values in the hundreds instead of small integers.
3. Cross-reference against the product-name pattern already documented for N127
   (CURRENT_STATUS.md, Root cause section): the "<Tool Name> <4-digit number>"
   shape matches exactly.

EXPECTED
approver_id should be a Party/User id, approver_role a role enum value,
delegated_from_name/actor_name a person's name, and level/order/total_levels small
positive integers (1, 2, 3, ...).

ACTUAL
These fields hold the same class of seed-data garbage already fixed on Tax records
by N127's commits 92682d0a3/4c812eb0f -- confirming that fix's own field list (85
fields) did not include the Approvals domain's nested arrays.

IMPACT
Any approval-routing logic, audit trail, or agent that trusts steps[].approver_role
to route a decision, or level/order to sequence approval stages, is reading
unusable data. Given N127's fix note said the sweep ran "in both apps" and still
missed this, a full-schema, all-nested-array sweep (not just the fields already
found) looks warranted rather than another one-off fix.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
ApprovalRequest: a7b92cf9-4681-44d2-8db3-6cc1c9347ffb (APR-2026-00100),
                 ec853b5f-4fe9-41ff-a120-0b9b6ad3ce5a (APR-2026-00070)
No job_id -- found by direct REST/MCP inspection.
```

---

### N6 · Recurring-bill duplicate-generation defect (same class as B7) also reproduces on Suryodaya, plus an *expired* template still firing **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** High · **Area:** Accounts Payable / Recurring Bills

```
ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)

SUMMARY
B7 (the Keystone/US write-up in agentswitch_submissions.md -- never filed under its
own name; THIS report, N6, is the filed record of that defect) described RecurringBill
templates that never advance next_bill_date/last_generated_date and so regenerate a
duplicate Bill every day. The same signature is present on Suryodaya: every one of the 3 distinct
recurring_bill_id values referenced by the 110 fetched India Bills produced exactly
one new Bill per day on 2026-09-20, -21 and -22 (3 consecutive days = 3 duplicates
each, 9 duplicate bills total). This means the defect is a platform-wide scheduler
bug, not specific to the Keystone instance.

A NEW symptom not seen in the original B7 writeup: one of the three templates
(82510285-23fd-43c5-b2b5-42aed0bf0a97) has RecurringBill.status = "expired" and is
STILL generating bills daily -- the scheduler does not exclude expired templates.

REPRODUCTION
1. tools/call RecurringBill.list {"limit": 100} -- 100 templates exist; only 3 are
   referenced by any bill in the fetched 110-bill page.
2. tools/call Bill.list {"limit": 200} -- group by recurring_bill_id.
3. All three groups show the identical pattern:

   82510285-23fd-43c5-b2b5-42aed0bf0a97  (freq=weekly, status="expired")
     next_bill_date=2026-08-04 (past)  last_generated_date=2026-08-03 (never advanced)
     BILL-2026-00104  2026-09-20   BILL-2026-00107  2026-09-21   BILL-2026-00110  2026-09-22

   20fbba9d-a30f-43e5-8820-f97461ae307c  (freq=weekly, status="active")
     next_bill_date=2026-01-11 (8+ months past)  last_generated_date=2025-11-25
     BILL-2026-00103  2026-09-20   BILL-2026-00106  2026-09-21   BILL-2026-00109  2026-09-22
     Note: frequency is "weekly" yet it fired on 3 consecutive DAYS, not once a week.

   a593bc2f-b66c-48aa-8e7d-5c31b468d215  (freq=daily, status="active")
     next_bill_date=2026-08-21 (past)  last_generated_date=2026-08-02 (never advanced)
     BILL-2026-00102  2026-09-20   BILL-2026-00105  2026-09-21   BILL-2026-00108  2026-09-22

EXPECTED
One Bill per template per billing period, next_bill_date/last_generated_date
advanced after each generation, and an "expired" template excluded from the
generation loop entirely.

ACTUAL
All three fire once per day regardless of their own stated frequency
(weekly/weekly/daily all produced a daily bill), dates never advance, and expired
status does not stop generation.

IMPACT
Same class of impact as B7: unbounded duplicate draft payables against real
vendors, compounding daily. Confirms this is a platform-wide recurring-document
scheduler defect rather than an environment-specific one, which raises its
priority -- fixing it once should resolve both B7 and N6. See N7 below: on this
instance the duplicated bills also carry a second, compounding tax defect.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
RecurringBill: 82510285-23fd-43c5-b2b5-42aed0bf0a97 (expired, still firing),
               20fbba9d-a30f-43e5-8820-f97461ae307c, a593bc2f-b66c-48aa-8e7d-5c31b468d215
Bills: BILL-2026-00102 through BILL-2026-00110 (odd/even per template, see above)
No job_id -- found by direct REST/MCP inspection.
```

---

### N7 · TDS deducted independent of the taxable base, producing negative Bill `grand_total`/`balance_due` **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** High · **Area:** Accounts Payable / Tax (TDS) · **Compounds N6**

```
ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)

SUMMARY
All 9 bills generated by the 3 broken recurring templates in N6 carry a tds_amount
that bears no arithmetic relationship to the bill's own net_total/taxable_amount,
and because nothing else on the bill offsets it, the result is a NEGATIVE
grand_total and balance_due -- i.e. a vendor "bill" the platform's own books say is
actually owed FROM the vendor, which is not a real accounts-payable state.

Group 1 (82510285... template): net_total=0.0 (single line item has rate=0,
  amount=0.0), tds_amount=20,546.99, tds_percentage=null -- TDS deducted from a
  bill with nothing to deduct a percentage OF. grand_total=-20,547.00.
  (BILL-2026-00104/107/110, all 3 duplicates identical)

Group 2 (20fbba9d... template): net_total=0.0, tds_amount=203,954.62,
  tds_percentage=null. grand_total=-203,955.00.
  (BILL-2026-00103/106/109, all 3 duplicates identical)

Group 3 (a593bc2f... template): net_total=39.36, tds_percentage=15.0,
  tds_amount=11,196.65 -- 15% of 39.36 is 5.90, not 11,196.65 (the stored amount is
  ~1,898x the correct figure). grand_total=-11,155.00.
  (BILL-2026-00102/105/108, all 3 duplicates identical)

balance_due matches grand_total exactly on all 9 (balance_due = grand_total -
amount_paid - credits_applied reconciles cleanly), so the defect is upstream in how
tds_amount is computed/stored, not in a separate balance calculation.

REPRODUCTION
1. tools/call Bill.get {"id": "6584b054-a047-4acd-b544-829876d5a6bc"}  (BILL-2026-00104)
   -> net_total=0.0, tds_amount=20546.99, grand_total=-20547.0
2. tools/call Bill.get {"id": "5ac8b6a7-82bc-4993-a3b2-ad423bb475fd"}  (BILL-2026-00108)
   -> net_total=39.36, tds_percentage=15.0, tds_amount=11196.65 (expected ~5.90)
3. Repeat for the other 7 bills listed above -- the pattern is identical within
   each recurring-template group (as expected, since N6 means they're duplicates).

EXPECTED
tds_amount should be tds_percentage% of the taxable base (or 0 when the base is 0),
and grand_total should never go negative on a normal vendor bill purely from a TDS
deduction -- TDS reduces what's owed, it should not flip a bill into an amount owed
BY the vendor.

ACTUAL
tds_amount is a large, arbitrary figure unrelated to tds_percentage x net_total
(or present even when net_total is 0), driving grand_total/balance_due negative on
9 of 110 bills sampled -- all 9 being the N6 duplicates.

IMPACT
Negative payables corrupt AP aging, cash-outflow forecasting and TDS liability
reporting (the "unified tax liability" workflow the team's own gap report proposed
building depends on tds_amount being trustworthy). Because these 9 bills are also
N6 duplicates, fixing the recurring-bill scheduler (N6) would stop new instances,
but the underlying TDS-computation defect is independent and would still affect any
other bill with a similarly small/zero net_total.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
Bills: 6584b054-a047-4acd-b544-829876d5a6bc (BILL-2026-00104),
       c8b99c7a-25d2-458f-81f5-e639b1d363cd (BILL-2026-00107),
       3a1fd3f3-beee-41f2-a90d-c26341d26a2f (BILL-2026-00110),
       5ac8b6a7-82bc-4993-a3b2-ad423bb475fd (BILL-2026-00108), and the remaining 5
       duplicates listed in N6.
No job_id -- found by direct REST/MCP inspection.
```

---

### N8 · `ApprovalRequest.is_overdue` false-negative rate is far worse on India (74%), clustered on one suspicious bulk-resolution timestamp **[FILED 23 Sep 2026 -- awaiting board triage]**

**Severity:** High · **Area:** Approvals / AP workflow · **Same defect class as N1, higher severity**

```
ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)

SUMMARY
N1 found an 8.6% is_overdue error rate on Keystone. The identical check on
Suryodaya (resolved_at vs sla_deadline, for every resolved/cancelled/recalled
request carrying both timestamps) finds a much higher and much more one-sided
error rate: 14 of 19 checkable requests (74%) show is_overdue=0 despite having
resolved AFTER their SLA deadline -- in several cases by MONTHS (one sla_deadline
of 2025-12-21 shows resolved_at of 2026-09-12, nearly 9 months late, still flagged
not-overdue). Unlike N1, every one of these 14 is a false negative -- none is a
false positive in this sample.

11 of the 14 mismatched requests share the exact same resolved_at timestamp to the
millisecond: 2026-09-12T17:19:16.0xx-3xx. Different documents (Bill, Invoice,
PurchaseOrder, Contract, SalesOrder, LeaveApplication, Expense), different
sla_deadlines spanning 2025-04 through 2026-08, all "resolved" within a ~0.8-second
window on the same day. This strongly suggests a single bulk-resolve or data-backfill
operation that stamped resolved_at on a batch of stale requests without recomputing
is_overdue against each one's own sla_deadline.

REPRODUCTION
1. tools/call ApprovalRequest.list {"limit": 200} -- 171 records.
2. Filter to status in (approved, rejected, recalled, cancelled) with both
   sla_deadline and resolved_at populated -- 19 records.
3. Compare resolved_at > sla_deadline against stored is_overdue: 14 of 19 disagree,
   all in the false-negative direction. Sample:
     APR-2026-00097 (Expense, eb30f02e-...): sla=2026-08-18, resolved=2026-09-12
       17:19:16.340594, is_overdue=0
     APR-2026-00095 (LeaveApplication, ce16ca87-...): sla=2025-12-21, resolved=
       2026-09-12 17:19:16.327217, is_overdue=0  (~9 months late)
     APR-2026-00080 (PurchaseOrder, 09674d0d-...): sla=2025-08-12, resolved=
       2026-09-12 17:19:16.195113, is_overdue=0  (~13 months late)
     APR-2026-00078 (Invoice, 82b3a48a-...): sla=2026-08-24, resolved=2026-09-12
       17:19:16.177546, is_overdue=0
     APR-2026-00015 (Bill, ed438f37-...): sla=2026-06-04, resolved=2026-09-12
       17:19:15.596284, is_overdue=0

EXPECTED
is_overdue should reflect resolved_at vs sla_deadline at the time of resolution
(same expectation as N1), regardless of whether the resolution happened via normal
workflow or a bulk operation.

ACTUAL
74% of checkable resolved requests on this instance carry a stale/wrong flag, and
the clustering around one exact timestamp points to a specific bulk-resolution
event as the likely mechanism, rather than a per-request logic error alone (which
is what N1's Keystone sample, with mismatches spread across different times and in
both directions, looks more like).

IMPACT
Same as N1, at much higher volume here: an SLA-compliance report on Suryodaya's
approval history would show near-total compliance while the real figure -- based on
the platform's own timestamps -- is that most checkable late approvals were never
flagged. Directly relevant to AP: 2 of the 14 (APR-2026-00015 on a Bill,
APR-2026-00078 on an Invoice) are payables/receivables documents.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
ApprovalRequest ids (14 total): eb30f02e-7c04-4d67-adb8-bb861d167e22,
  ce16ca87-cd01-4f9c-a064-83dcb839b3a5, 09674d0d-3ab7-4e41-9f11-2d610f72396d,
  82b3a48a-b96c-45d8-82ff-0bbc5c886661, ec853b5f-4fe9-41ff-a120-0b9b6ad3ce5a,
  f0132f05-fb86-4e81-94f9-4a5880f986ac, f1492e4c-4a31-4645-be59-a70afea96edc,
  9720c05f-14a7-4158-94e1-857fdeb0eab9, 72629af0-297f-4768-8932-d7d1e922566c,
  76c033c2-5923-4fc1-8a7d-831b2edd6401, ed438f37-fde0-4ebb-949b-97b08baab068,
  99bd8cdd-eda7-4a46-9f87-843f49407b1e, a2cfbe9f-ee38-4436-9457-baa4e70986b3,
  94b14c54-f70a-47e2-9c53-23d35f7cc728
No job_id -- found by direct REST/MCP inspection.
```

---

---

### Notes on method / what was ruled out (N1-N8 verification pass)

To avoid inflating the list above, several avenues were checked on each instance
and found clean (not worth reporting as a defect).

**Keystone/US pass -- also checked and found clean:**

- Bill arithmetic (`grand_total = net_total + total_tax + shipping + adjustment +
  round_off`, `balance_due = grand_total - amount_paid - credits_applied`,
  `sum(items[].amount) == net_total`) reconciles on all 91 bills, 0 exceptions.
- `Bill.status` vs `balance_due` is fully consistent (67 paid bills all have
  balance_due=0; all open/draft bills have balance_due>0 or are legitimately
  unbilled drafts).
- No duplicate `PaymentMade` against the same bill; no overpayments found among 67
  payments.
- No duplicate `Bill.number`; no `Party` records sharing a tax id or bank account
  number (within the fetched pages).
- `ApprovalRequest.current_level`/`total_levels`/`escalation_count` are internally
  consistent (no `current_level > total_levels`, no `escalated` status with a zero
  escalation count).
- The 3-way match's quantity/price tolerance fields were all "within_tolerance"
  across the 81 PO-linked bills sampled — plausibly clean seed data rather than a
  masking bug, but flagged here for transparency since it couldn't be positively
  ruled out (no bill in this dataset has a genuine price/qty variance to serve as a
  positive control, the way B7's "Quarterly pest control" template served as a
  control group for the recurring-bill defect).

**India/Suryodaya pass -- also checked and found clean:**

- `PurchaseOrder`↔`Bill` 3-way match (`endpoint.accounting.bill_match`, same tool as
  N2/N3): confirmed present and callable on Suryodaya too, not separately re-probed
  in depth this pass -- worth a follow-up session.
- No duplicate `PaymentMade` against the same Bill (0 of 134 payments).
- `Bill.balance_due` reconciles against `grand_total - amount_paid - credits_applied`
  on all 110 bills, including the 9 negative-total bills in N7 -- confirming N7's
  defect is upstream of the balance calculation, not in it.
- `RecurringInvoice` (100 templates exist) was checked for the same runaway pattern
  as N6/B7: no `Invoice(direction=payable)` in the fetched 165-record page
  references a `recurring_invoice_id` at all, so no evidence either way this pass.

---

## 2. Bugs — ready to submit

### B4 · Tax lines can be stored that the platform's own calculator cannot produce

**Severity:** High · **Area:** Tax / Data integrity · **Split from B3**

```
Documents can store tax lines that the platform's own tax calculator would never
produce. Nothing validates taxes[] on write.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c),
India locale, tax_regime "gst".

SUMMARY
This is NOT a calculation bug. POST /api/accounting/tax/compute is correct, and that
was verified first. The defect is that stored CreditNote.taxes[] rows contradict what
that endpoint returns for the same inputs, meaning they were written without ever
being validated against it.

THE CALCULATOR IS CORRECT (control tests)
  POST /api/accounting/tax/compute {"amount": 100000, "rate": 18}
    -> total_tax 18000.0, taxes[{tax_type "IGST", rate 18.0, amount 18000.0}]
  POST /api/accounting/tax/compute {"amount": 288886.74, "rate": 18}
    -> total_tax 51999.61
  POST /api/accounting/tax/compute {"amount": 100000, "rate": 0}
    -> total_tax 0, taxes[]        <- a 0% rate correctly yields NO tax row at all
The calculator also emits a valid Tax.tax_type enum value ("IGST").

WHAT IS ACTUALLY STORED
  CN-2026-00022  08749498-9898-423a-a4ab-6bac6b679c7d
    taxable_value 288886.74, taxes[{rate 18, amount 975.17}]
    The calculator returns 51999.61 for this exact base and rate.
  CN-2026-00023  f7aa6705-2703-4403-ba36-926197945859
    taxes[{rate 0, amount 1381.05}]
    A 0% rate carrying tax. The calculator returns an empty taxes[] for rate 0, so
    this row is not something the compute path can emit.
  CN-2026-00020
    taxable_value 3469.53, taxes[{rate 5, amount 1635.97}]
    5% of 3469.53 is 173.48. The stored amount exceeds rate x base by ~9x.

Additionally taxes[].tax_type holds product names ("V-Block Pair 7363") rather than a
tax head, whereas the calculator emits "IGST". The field is declared "type": "text",
so nothing constrains it despite the canonical Tax.tax_type enum existing.

REPRODUCTION
1. POST /api/accounting/tax/compute {"amount": 288886.74, "rate": 18} -> 51999.61
2. tools/call CreditNote.get {"id": "08749498-9898-423a-a4ab-6bac6b679c7d"} -> 975.17
3. POST /api/accounting/tax/compute {"amount": 100000, "rate": 0} -> taxes[]
   then inspect f7aa6705-2703-4403-ba36-926197945859 -> rate 0, amount 1381.05

EXPECTED
A stored tax line should be reconcilable against the platform's own calculator:
amount follows from rate and base, a 0% line carries no tax, tax_type is a recognised
head. Violating writes should be rejected or flagged.

ACTUAL
Arbitrary rate/amount combinations persist, including amounts exceeding the taxable
base and 0% lines carrying tax. These flow into compliance reporting.

IMPACT
Every consumer of taxes[] is affected, not just one report. Because
/api/accounting/tax/compute already implements correct behaviour, it can serve as the
validation oracle on write.

ENTITY IDS
CreditNote: 08749498-9898-423a-a4ab-6bac6b679c7d, f7aa6705-2703-4403-ba36-926197945859
Company: 5cbe5a55-af74-4363-a436-f5350593114c
No job_id — found by direct REST/MCP inspection.
```

---

### B6 · N127's fix is incomplete — `group_taxes[].tax_type` still holds tool names

**Severity:** Medium · **Area:** Tax / Settings · **Follow-up to N127**

```
The fix shipped for N127 corrected the parent Tax records but did not reach the
nested group_taxes child rows, which still hold tool names.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c),
India locale. Re-verified 2026-09-22, after N127 was marked "Live on server".

WHAT THE FIX DID CORRECT (confirmed working)
  Tax.tax_name          was "Scriber 5169"  ->  now "Tax — Machining", "Tax — Inspection"
  Tax.is_group          was 67 of 100 contradicting their group_taxes children
                        ->  now 0 of 100 contradictory
  TaxJurisdiction       was 100 rows all country="US" on an India company
                        ->  now total = 0, correctly empty for a GST regime

WHAT IT MISSED
  group_taxes[].tax_type is still 0 of 88 valid against the Tax.tax_type enum
  (IGST / CGST / SGST / UTGST / CESS / TDS / TCS / SALES_TAX / USE_TAX / EXCISE /
  WITHHOLDING_1099 / other). Current values include:
      "Angle Plate 5091", "Scriber 5162", "Punch Set 5158", "Punch Set 5130",
      "Punch Set 5115", "Surface Plate 5107", "Pipe Wrench 5134", "Pipe Wrench 5112"

  So a Tax record now reads sensibly at the top level -- tax_name "Tax — Machining",
  tax_type "SALES_TAX", is_group true -- while its component rows underneath are
  still named after hand tools.

REPRODUCTION
1. POST /api/mcp -> tools/call Tax.list {"limit": 100}
2. Read Tax.tax_name on any row: corrected.
3. Read group_taxes[].tax_type on the same row: still a tool name.
4. Compare every populated group_taxes[].tax_type against the Tax.tax_type enum
   published in /api/schemas: 0 of 88 match.

WHY IT WAS MISSED (probable)
The N127 fix note reports "8,535 tool-named values found in 85 fields, all corrected
in a rehearsal on copies of the live data." This nested child field appears not to
have been among those 85 fields, or the sweep did not descend into child tables.
Worth checking whether other "children"-typed fields were skipped for the same
reason -- Invoice.taxes, Bill.taxes, CreditNote.taxes and Party.roles are all the
same shape, and CreditNote.taxes[].tax_type is confirmed still corrupt (see N128).

EXPECTED
group_taxes[].tax_type should hold a recognised tax head, like the parent
Tax.tax_type field already does on the same record.

ACTUAL
It holds product names, unchanged since before the fix.

IMPACT
Composite-tax expansion (GST 18% -> CGST 9% + SGST 9%) still cannot be driven off
the tax master: the component rows carry no usable classification. The parent-level
fix makes this harder to notice, because the record now looks correct until you
open its children.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
Affects every Tax row with group_taxes children (88 populated child values sampled
across 100 Tax records).
No job_id -- found by direct REST/MCP inspection.
```

---

### B5 · Journal voucher renders ₹0.00 with no lines despite non-zero Total Debit

**Severity:** Medium · **Area:** Accountant / Manual Journals · **Needs reproduction**

Observed in the UI inventory (`UI.MD` SCR-041): the Manual Journals **list** shows a
non-zero `Total Debit`, but opening the journal renders a voucher with no line items
and subtotal/total ₹0.00. `JournalEntry.lines` is a real schema field, so the data
should be present.

**Before submitting:** reproduce against a specific `JournalEntry.id` and confirm via
`tools/call JournalEntry.get` whether `lines` is populated in the API response. If
populated → UI rendering bug (strong). If empty while `total_debit` is non-zero →
data-integrity bug (stronger). Capture the id either way.

---

### B7 · Recurring bills regenerate **every day** — `next_bill_date` never advances

**Severity:** High · **Area:** Accounts Payable / Recurring Bills · **Instance: Keystone (US)** · **Verified 2026-09-22**

> **File this one first.** It is the strongest candidate we have: a live,
> self-demonstrating duplicate-payables generator, and it is *literally* the
> Core Challenge Prompt ("is any vendor being paid twice?") occurring for real
> on the platform. It also has a clean internal control group (see below).

```
Active monthly RecurringBill templates generate a new draft Bill on EVERY run,
not once per month. next_bill_date never advances and last_generated_date is
never stamped, so the scheduler re-fires the same template indefinitely.

ENVIRONMENT
Company: Keystone Precision Works LLC (c1e47d8d-b849-4187-9a32-4103d3dece4a)
Instance: https://class.agentswitch.theschoolofai.in  (US locale, us_gaap,
sales_use_tax, base_currency USD)
Vendor: Apex Metals Supply LLC (bfb5a381-ec65-46bb-a7c8-60f0fbadf205)

SUMMARY
RecurringBill.list returns 4 active templates, all frequency "monthly",
all start_date 2026-04-01. Three have repeat_every 1.0 and a next_bill_date of
2026-08-01 -- a date in the PAST. Those three have each produced one Bill per
day on 2026-09-20, 2026-09-21 and 2026-09-22 and are still producing them.

THE CONTROL GROUP (this is what makes it conclusive)
The fourth template is identical in every respect except that its next_bill_date
is in the FUTURE, and it fired exactly once:

  5d45e8e8-a423-486e-858e-aeb8a20f0c94  "Quarterly pest control"
    frequency monthly, repeat_every 3.0, next_bill_date 2026-10-01 (future)
    -> 1 bill total:  BILL-2026-00085  2026-09-20  4,500.00  draft

Same company, same vendor, same start_date, same active status. The only
differing variable is whether next_bill_date is in the past. That isolates the
defect to the scheduler's date-advance step.

REPRODUCTION
1. tools/call RecurringBill.list {"limit": 100}
   -> 4 templates; note next_bill_date and last_generated_date on each.
2. tools/call Bill.list {"limit": 100}  (page through; total was 91 on 09-22)
3. Group the returned bills by recurring_bill_id.

ACTUAL -- one bill per template per DAY:

  4493ae01-2a36-41d3-ae59-5d8ddd94e0ce  "Monthly internet & bandwidth"
    next_bill_date 2026-08-01, last_generated_date null
      BILL-2026-00082  2026-09-20   8,500.00  draft
      BILL-2026-00086  2026-09-21   8,500.00  draft
      BILL-2026-00089  2026-09-22   8,500.00  draft

  d6e80764-c95e-459d-9c2c-aaa53b7c7bad  "Office cleaning services"
    next_bill_date 2026-08-01, last_generated_date null
      BILL-2026-00083  2026-09-20  18,000.00  draft
      BILL-2026-00087  2026-09-21  18,000.00  draft
      BILL-2026-00090  2026-09-22  18,000.00  draft

  95155c69-5fc6-4c2b-92a8-10e16076d689  "SaaS - CRM & helpdesk"
    next_bill_date 2026-08-01, last_generated_date null
      BILL-2026-00084  2026-09-20  12,000.00  draft
      BILL-2026-00088  2026-09-21  12,000.00  draft  (id a72bfc54-e6ab-46fd-97d9-f4728ddf3a15)
      BILL-2026-00091  2026-09-22  12,000.00  draft

EXPECTED
One Bill per template per month. After generating, the scheduler should advance
next_bill_date by (frequency x repeat_every) and stamp last_generated_date.

TWO SYMPTOMS, LIKELY ONE ROOT CAUSE
  (a) next_bill_date is not advanced after generation, so a past due-date stays
      permanently due and re-fires on every scheduler pass.
  (b) last_generated_date is null on all four templates despite 10 bills having
      been generated from them -- so even a "have I already run today?" guard
      has nothing to read.

IMPACT
Unbounded growth of duplicate draft payables against a single vendor. Three new
duplicates per day, accumulating since at least 2026-09-20. Any AP process or
agent that approves drafts in bulk would pay this vendor three times over for
the same month of services. This is a duplicate-payment defect, which is the
exact failure class Seat 03 exists to detect.

NOTE ON SEVERITY
Currently contained only because every generated bill is stuck in status
"draft". If anything advances drafts automatically, this becomes a live
double-payment incident rather than a data-hygiene one.
```

**Why this is not already covered:** `not_yet_supported` names GST-18/28/29/32/39,
`period_close`, `depreciation_posting` and `inventory_costing`. Recurring-bill
scheduling appears nowhere in that list, and nothing in §3 covers it.

---

### B8 · India seed data on the US company — INR bills and GST fields on a USD/sales-tax entity

**Severity:** Medium · **Area:** Data integrity / Locale · **Instance: Keystone (US)** · **Verified 2026-09-22**

```
Bills on the US company are denominated in INR and carry the full India GST
field set, contradicting the company's own locale.

ENVIRONMENT
Company: Keystone Precision Works LLC (c1e47d8d-b849-4187-9a32-4103d3dece4a)
Instance: https://class.agentswitch.theschoolofai.in
GET /api/accounting/locale -> locale.country "US", accounting_standard
"us_gaap", tax_regime "sales_use_tax", base_currency "USD", currency_symbol "$",
features.gst_returns false.

ACTUAL
Of 91 Bills, 10 carry currency_code "INR" on a company whose base_currency is
USD. All 10 belong to vendor Apex Metals Supply LLC
(bfb5a381-ec65-46bb-a7c8-60f0fbadf205) and all are recurring-generated (see B7):

  BILL-2026-00082 .. BILL-2026-00091   currency_code "INR"

Sample: BILL-2026-00088 (a72bfc54-e6ab-46fd-97d9-f4728ddf3a15) returns
  currency_code   "INR"        <- company base_currency is USD
  gst_treatment   null         <- India-only field, present on a US document
  place_of_supply null         <- India-only
  source_of_supply / destination_of_supply  null   <- India-only
  gst_no          null         <- India-only
  ims_status      "pending"    <- India GST IMS, meaningless under sales_use_tax
  itc_eligibility "input"      <- India Input Tax Credit, no US equivalent
  is_reverse_charge 0          <- India RCM
  tds_amount / tds_section / tds_percentage / tcs_*  null  <- India TDS/TCS
  items[].cgst_amount / sgst_amount / igst_amount / utgst_amount / cess_amount
                               <- India GST components on every line item
  use_tax_accrued null         <- the ONE field that is actually relevant to
                                  this locale, and it is the one left unset

EXPECTED
Either (a) documents on a US company should be created in the company's base
currency unless a deliberate multi-currency workflow set otherwise, and (b) the
India-only GST/TDS field group should not be populated or surfaced under
tax_regime "sales_use_tax" -- or, if the schema is intentionally shared across
jurisdictions, the locale-irrelevant fields should be consistently null/absent
rather than carrying India semantics (ims_status "pending", itc_eligibility
"input") on a US document.

WHY THIS MATTERS BEYOND COSMETICS
An agent that follows the platform's own locale contract -- read
/api/accounting/locale, branch on tax_regime -- computes US sales tax for this
company. But the purchase-side tax signal is entirely in India GST fields that
are all zero, while the genuinely relevant field (use_tax_accrued) is null on
all 91 bills. The result is a US company with USD 226,488.27 of output tax
across 127 receivable invoices and no representable input-tax position at all.

RELATED
Compare filed report 2a655790-2b05-4528-ade1-cff6d9c5ce15 (B1), which is the
mirror image on the India instance: 100 TaxJurisdiction rows of US sales-tax
data sitting on Suryodaya. Same class of defect -- seed data landing on the
wrong-jurisdiction company -- in both directions.
```

---

### B9 · Locale feature flags contradict MCP tool exposure in three places

**Severity:** Low-Medium · **Area:** Locale / API surface · **Instance: Keystone (US)** · **Verified 2026-09-22**

```
GET /api/accounting/locale advertises a feature set that does not match the
tools actually exposed to the caller.

ENVIRONMENT
Company: Keystone Precision Works LLC (c1e47d8d-b849-4187-9a32-4103d3dece4a)
Instance: https://class.agentswitch.theschoolofai.in
Role: finance_user; roles [finance_user, user, agent_user, sales_viewer]
MCP tools/list returned 447 tools on 2026-09-22.

METHOD
Cross-check each locale.features flag against the presence of matching tools in
tools/list.

THREE MISMATCHES

  features.gst_returns = false
    but exposed: GSTReturn.get, GSTReturn.list
    (read-only, so low impact -- but the flag says the capability is off)

  features.eway_bill = false
    but exposed: EWayBill.activate, EWayBill.create, EWayBill.generate,
                 EWayBill.get, EWayBill.list, EWayBill.update   (6 tools)
    This is the material one: WRITE and GENERATE tools for an India-only
    statutory document are callable on a US company whose locale declares the
    feature disabled. An agent enumerating tools/list has no way to know these
    should not be used here.

  features.form_1099 = true
    but exposed: nothing. No Form1099 entity, no 1099-named tool anywhere in
    the 447. The flag advertises a US compliance capability with no API behind
    it.

CORRECTLY ALIGNED (control cases -- the flags are not uniformly wrong)
  features.einvoicing             = false -> 0 matching tools   consistent
  features.sales_tax_nexus        = true  -> TaxNexus.get/list   consistent
  features.exemption_certificates = true  -> ExemptionCertificate.get/list,
                                             TaxExemption.get/list  consistent
  features.sales_tax_jurisdictions= true  -> TaxJurisdiction.get/list consistent

EXPECTED
locale.features should gate tool exposure, or at minimum agree with it. A flag
of false should mean the corresponding tools are not offered (the platform
already does exactly this for prohibited entities -- SalarySlip, Contract and
EsignDocument are absent from tools/list rather than returning 403). A flag of
true should mean an API exists.

IMPACT
locale.features is the platform's own documented contract for how an agent
adapts to jurisdiction -- our SKILL.md Hard Rule 2 depends on it. If the flags
do not predict tool availability, a locale-driven agent must probe tools/list
instead, which makes the endpoint advisory rather than authoritative.
```

---

### Not fileable — tool-count delta between instances

`tools/list` returned **436** on Suryodaya (per `../CURRENT_STATUS.md` §4,
2026-09-20) and **446–447** on Keystone (2026-09-22, count drifted by one within
the same session). A diff would be interesting — a US company exposing India-only
tools is exactly what B9 documents.

**We cannot produce that diff.** The team credentials authenticate against
Keystone only; the Suryodaya login returns `HTTP 401 Invalid credentials`, and
`CURRENT_STATUS.md` records the India tool names in prose rather than storing the
raw `tools/list` response. Two different counts taken on two different days from
two different companies is not evidence of anything. **Do not file this** —
B9 already captures the defensible part with direct flag-vs-tool evidence.

---

## 3. Do NOT submit — already self-documented by the platform

These appear in `GET /api/accounting/locale` → `not_yet_supported`, with the
platform's own ticket ids. Re-filing risks rejection as already-known.

| Ticket | Item |
|---|---|
| GST-28 | E-invoicing (IRN / signed QR / IRP) not implemented despite a full settings page |
| GST-29 | E-way bill generation — no NIC portal integration, no Part A/B, no threshold auto-generate |
| GST-32 | No GSTR-1 amendment tables; back-dated invoice into a filed period accepted silently |
| GST-39 | GSTR-9 annual return returns HTTP 501 |
| GST-18 | TDS/TCS — no auto-deduction by section/threshold, no challan tracking, no 26Q/27Q |
| — | Depreciation posting produces zero GL rows |
| — | Inventory costing method setting read by no code path |
| — | Multi-entity consolidation absent |

---

## 4. Feature requests

Derived from the competitor analysis in [`gap_report.md`](gap_report.md) and
[`razorpay_gap_report.md`](razorpay_gap_report.md). These are gaps, not defects —
submit separately from bugs, since the bug bounty is for defects.

**Each entry states how we proved the gap exists here and how we proved a
competitor has it.** That matters: while preparing this list, two items we assumed
were missing turned out to exist (see F6, and the note under F2). Asserting an
absence without checking is how a feature request gets dismissed.

**Evidence tiers for competitor claims** — **[LIVE]** = seen in a real logged-in
account · **[DEMO]** = seen in the vendor's marketing video · **[CLAIM]** = vendor
text only, untested.

---

### F1 · Goods Receipt Note entity — enable 3-way matching · **HIGH**

**What's missing:** any record of goods being *received*.

**Why it matters, in plain terms.** Three documents should agree before a supplier
gets paid: the purchase order (what we ordered), the goods receipt note (what
actually arrived at the loading dock), and the invoice (what we're being billed
for). Checking all three is called *three-way matching*, and it's the single most
important control in accounts payable.

Concrete example: you order 100 steel plates at ₹500 each. Only 60 arrive. The
supplier invoices you for all 100 — ₹50,000 instead of ₹30,000. With a GRN you
catch it automatically: the receipt says 60, the invoice says 100, payment is
blocked. Without a GRN the only defence is someone remembering what turned up at
the dock weeks ago. This is also how invoice fraud works — bill for goods never
delivered and hope nobody checks.

**How we verified it's missing in AgentSwitch:**
1. Pulled all 425 entity names from `GET /api/schemas`.
2. Searched them case-insensitively for `receipt|grn|goods`. Only two matched, both
   unrelated: `EsignConsentReceipt`, `FormConsentReceipt`.
3. Checked all 436 MCP tools from `tools/list` — no GRN tool of any kind.
4. Confirmed `Bill.purchase_order_id` exists, so PO↔Bill (two-way) matching *is*
   possible — the missing leg is specifically the receipt.

**Who has it, and how we know:** **RazorpayX [LIVE]** — screenshot of Vendor
Payments → Import showing three tabs: `Purchase Orders | Items | GRNs`. Also
claimed by Mysa (3-way), CashFlo (6-way) and Kodo/EnKash (2-/3-way) **[CLAIM]**.

**The ask:** a `GoodsReceiptNote` entity with line-level quantities, links to
`PurchaseOrder` and `Bill`, and a matching tool exposed over MCP.

**Why it's top priority:** this is the only gap in this list our agent
*categorically cannot work around*. Every other item can be partially bridged by
orchestrating existing tools. You cannot match against a document type that does
not exist.

---

### F2 · A sandbox, or a dry-run flag on write tools · **HIGH**

**What's missing:** anywhere safe to test a write.

**Why it matters, in plain terms.** Our agent's job includes changing records —
flagging a duplicate bill, putting a payment on hold, submitting something for
approval. Right now the only place to try that is the real ledger, which Teams 01
and 02 are also using. There is no "practice mode." If our duplicate-detection
logic has a bug and flags 40 legitimate bills, that happens to live data that two
other teams are working in, and there's no undo.

Analogy: it's like being asked to test a new autopilot by flying the actual plane
with passengers aboard.

**How we verified it's missing in AgentSwitch:**
1. Searched all 425 entities for `Demo|Sandbox|Test`. Found `DemoPlay`,
   `DemoPlayRun`, `DemoPlayStep` (domain `demo`) — a scripted demo-walkthrough
   feature, not a data sandbox.
2. Searched all 436 tools for `sandbox|demo|test`. Found exactly one:
   `endpoint.agent_governance.skill_sandbox` — a sandbox for testing *agent skills*,
   not for testing *transactions*.
3. No write tool in the 436 accepts a dry-run or validate-only parameter.

**Honest note:** a skill sandbox does exist, so the platform isn't ignorant of the
problem — it just doesn't extend to ledger writes.

**Who has it, and how we know:** **RazorpayX [LIVE]** — the account runs with a
"Test balance", an "Add test balance" action, and the banner *"These are test
payouts and do not affect the actual balance. They are used only for the purpose of
integrating events."*

**The ask:** either a resettable per-team sandbox company, or (cheaper) a
`dry_run: true` parameter on write tools that validates and returns what *would*
change without persisting.

---

### F3 · Expose reports over MCP · **MEDIUM**

**What's missing:** an agent cannot read the financial statements.

**Why it matters, in plain terms.** Our agent is asked "what is our tax liability
this period?" A human answers that by opening a report. Our agent can't open any
report — it has to re-derive the numbers from thousands of raw ledger rows. That's
slower, and worse, it means the agent's answer can silently disagree with what the
finance team sees on screen, with no way to reconcile the two.

**How we verified it's missing in AgentSwitch:**
1. The reports **do** exist over REST — confirmed in `openapi.json` (729 paths):
   `/api/accounting/reports/{profit-and-loss,balance-sheet,trial-balance,cash-flow,
   ap-aging,ar-aging,sales-tax-liability}`, plus `/api/reports` which accepts
   `trial_balance, profit_and_loss, balance_sheet, receivables, payables,
   stock_balance, gst_r1`.
2. Searched all 436 MCP tool names — **no** `Report.*` tool and no
   `endpoint.accounting.reports.*` entry. The capability exists; it simply isn't
   reachable from the agent interface.

**Who has it, and how we know:** **RazorpayX [LIVE]** — a Reports screen generating
Account Statement, Payouts, Vendor Payments, Purchase Orders, Vendor Advances,
Vendor Invoices V2 and Fund Account Validation. (Not an MCP comparison — RazorpayX
has no published MCP server — but it shows reports treated as a first-class,
exportable surface.)

**The ask:** expose the existing report endpoints as MCP tools. This should be
cheap — the computation already exists and is already permission-checked.

---

### F4 · Bank account validation (penny-drop) · **MEDIUM**

**What's missing:** nothing checks that a vendor's bank account is real or theirs.

**Why it matters, in plain terms.** One of the most common frauds in accounts
payable is *bank detail substitution*: someone emails finance pretending to be a
supplier, says "we've changed banks, here's our new account," and the next payment
goes to the fraudster. A penny-drop check defends against this — the system deposits
₹1 and reads back the account holder's registered name. If the account says
"Acme Traders" and the vendor is "Bosch Rexroth India", the payment is stopped.

This sits squarely in our seat's remit: we're the Payables agent, and "is this
vendor legitimate?" is our question to ask.

**How we verified it's missing in AgentSwitch:**
1. Confirmed the fields exist on `Party`: `vendor_bank_account_number`,
   `vendor_bank_name`, `vendor_bank_code`, `beneficiary_name`. They are stored.
2. Searched all 436 tools for `valid|verify|penny`. Only two matched, both
   unrelated: `endpoint.job_ledger.verify` (agent audit) and
   `endpoint.storefront.payment.verify` (e-commerce checkout).
3. Note `/api/accounting/tax/validate-address` exists — so the platform does do
   external validation for *addresses*, just not bank accounts.

**Who has it, and how we know:** **RazorpayX [LIVE]** — "Fund Account Validation
report" appears in the Reports type dropdown, which implies account verification is
performed and its results are reportable.

**The ask:** a validation tool for vendor bank details, plus a flag on `Party`
recording verification status and date.

---

### F5 · Scoped external-accountant (CA) access · **MEDIUM**

**What's missing:** a way to give an outside accountant reports without giving them
the whole system.

**Why it matters, in plain terms.** Indian SMEs run their compliance through a
chartered accountant who is not an employee. That CA needs the trial balance and
GST data every month. Today the realistic options are: share a login (the CA can
then see and change everything, and the audit trail shows your name for their
actions), or export files by hand every month. A read-only, reports-only guest role
solves both.

**How we verified it's missing in AgentSwitch:**
1. Collected the roles appearing across entity permission blocks in
   `/api/schemas`: `admin`, `finance_admin`, `finance_user`, `accountant`,
   `auditor`, `hr_admin`, `hr_user`, `operations_user`, `sales_user`,
   `support_user`, `project_user`, `employee`, `viewer`, `student`, `instructor`.
   `accountant` and `auditor` exist but are **internal** roles on the company, not
   a scoped external grant.
2. Found no share/invite mechanism scoped to reports among the 436 tools.

**Caveat — lower confidence than F1–F4.** We verified no *role* exists for this; we
did not exhaustively rule out a sharing feature in the UI. Worth a quick check
before submitting.

**Who has it, and how we know:** **RazorpayX [LIVE]** — the Reports screen states
*"Let Your CA Download These Reports — CA can download reports without troubling
you! No access to your RazorpayX account except"* reports. Clear also targets CAs
as a primary segment **[CLAIM]**.

---

### F6 · Enable the `approvals` app for Seat 03 · **MEDIUM** *(rewritten — this is not a missing feature)*

> ✅ **Half-resolved, 23 Sep.** `allowed_apps` on the Keystone account now includes
> `approvals` — the entitlement half of this ask has been granted (recorded in N1's
> own filed text, which is how we found out; no board card or fix note references
> F6). The second half is **still open**: no `Approval*` entity tool appears in
> `tools/list`, so the data is reachable over REST but not over MCP. N1, N5 and N8
> were all found through that newly-opened REST access.

**⚠️ Correction:** an earlier draft of this document asked AgentSwitch to *build*
multi-level approvals. That was wrong, and checking before submitting avoided an
embarrassing request. **The approval engine already exists and is more capable than
anything we observed in a competitor.** We simply cannot reach it.

**What actually exists.** Six entities in the `approvals` domain:

| Entity | Notable fields |
|---|---|
| `ApprovalPolicy` | `routing_type`, `approval_type`, `levels`, `conditions`, `condition_field/operator/value`, `max_escalation_levels`, `sla_enabled`, `default_sla_hours`, `escalation_enabled`, `allow_self_approval`, `require_comments_on_reject` |
| `ApprovalRequest` | `current_level`, `total_levels`, `current_approver`, `final_decision`, `sla_deadline`, `is_overdue`, `escalation_count`, `steps`, `history` |
| `ApprovalLog` | `action`, `actor_id`, `actor_name`, `level`, `step_index`, `comments`, `previous_status`, `new_status`, `ip_address`, `timestamp` |
| `ApprovalGroup` | `quorum_type`, `quorum_count`, `role_filter`, `members` |
| `ApprovalDelegation` | (delegated approval authority) |
| `ApprovalSLAConfig` | (SLA configuration) |

That is conditional routing, multi-level escalation, SLA deadlines, quorum-based
group approval, delegation, and a full per-action audit log with IP addresses.
RazorpayX's demo showed a single named level ("Finance L2") — **AgentSwitch's
design is richer.**

**Why we can't use it — and how we verified that:**
1. `ApprovalRequest` permissions explicitly grant our role:
   `"finance_user": ["read","create","write","submit"]`.
2. But `GET /api/ApprovalRequest?limit=1` → **HTTP 403**
   `{"detail":"App 'approvals' is not enabled for your account"}`. Same for
   `ApprovalPolicy`, `ApprovalLog`, `ApprovalGroup`.
3. `GET /api/auth/me` shows `allowed_apps: ["accounting", "agent", "crm"]` —
   `approvals` is absent. So it's an **app entitlement**, not a role permission,
   blocking us.
4. No `Approval*` entity tool appears in our 436. All we get is the fire-and-forget
   `Bill.approval.submit` / `Invoice.approval.submit` — we can *push* a document
   into approval but cannot see who must approve it, what's pending, or what was
   decided.

**In plain terms:** we can put a suspicious duplicate bill into the approval queue,
but we're then blind. We can't tell you who it's waiting on, whether it's breached
its SLA, or whether it was approved or rejected and why — even though the platform
records all of that.

**The ask:** add `approvals` to Seat 03's `allowed_apps`, and expose
`ApprovalRequest` and `ApprovalLog` as read-only MCP tools. Nothing needs building.

---

### F7 · Batch / payment-run identity · **LOW**

**What's missing:** payments can only be made one at a time.

**Why it matters, in plain terms.** Finance teams don't pay 200 suppliers
individually — they do a weekly "payment run", approve it once, and release it as a
batch. If something goes wrong, they reverse the batch. Without a batch concept you
get 200 unrelated records with no shared identity, nothing to approve as a unit,
and nothing to reverse as a unit.

**How we verified it's missing in AgentSwitch:** `PaymentMade` has no batch/run
field (fields include `payment_number`, `bills`, `invoices`,
`applied_allocations`, `total_applied` — all single-payment scoped), and no batch
tool exists among the 436.

**Who has it, and how we know:** **RazorpayX [LIVE]** — a dedicated Bulk Payouts
screen: *"A batch is the group of payouts uploaded in bulk. Once a batch is created,
they will show up here."*

**Priority note:** LOW for our seat specifically, since AgentSwitch cannot execute
payments at all (see the main gap report) — batching matters more once there's
something to batch.

---

### F8 · MSME 45-day statutory payment tracking · **MEDIUM**

**What's missing:** nothing warns when an MSME vendor is about to be paid late.

**Why it matters, in plain terms.** Under India's MSME Development Act, payments to
registered micro/small enterprises must be made within 45 days. Miss it and the
buyer owes compound penal interest at three times the RBI bank rate — and, since
the 2023 amendment to Section 43B(h) of the Income Tax Act, the expense is
disallowed as a deduction until actually paid. So a late MSME payment costs money
twice: penal interest, plus a higher tax bill.

Concrete example: a ₹10,00,000 bill from a small vendor sits unpaid for 60 days.
That's 15 days overdue, penal interest accrues, and the ₹10,00,000 can't be claimed
as an expense in that year's return. Nobody notices because no screen shows it.

**How we verified it's missing in AgentSwitch:**
1. The vendor-side data exists: `Party.is_msme`, `Party.msme_type`
   (`micro/small/medium`), `Party.msme_no`.
2. The locale confirms the feature is meant to be in scope for India:
   `features.msme_45_day = true`.
3. But `MSMEPreferences` holds only `udyam_registration_number`,
   `enterprise_type`, `date_of_registration`, `display_on_invoices`,
   `display_on_purchase_orders` — i.e. **our own company's** MSME registration and
   whether to print it on documents. Nothing about tracking *vendor* payment
   deadlines.
4. No tool among the 436 computes or surfaces MSME ageing.

**Who has it, and how we know:** **OPEN Money [CLAIM]** — "MSME 45-day payment
tracking" stated explicitly. **Kodo/EnKash [CLAIM]** — "MSME payment rule
compliance."

**Good news — our agent can bridge this today.** Joining `Party.list(is_msme=true)`
against `Bill.list` due dates gives the exposure report, with no platform change
required. This is a strong candidate for demonstrating agent value over the stock
UI, and only needs platform support if it should become a native alert.

---

### F18 · ITC apportionment under Rule 42/43 · **HIGH** · **[FILED `a9f1888f…`, 23 Sep]**

**What's missing:** three things, in order of how hard each is to fix.
1. No field or aggregate anywhere that sums "exempt-supply turnover this period" vs
   "taxable-supply turnover this period" for a company. `itc_eligibility` on
   `Bill`/`Invoice` is a per-document enum (`input`/`input_services`/
   `capital_goods`/`ineligible`), not a proportion, and nothing aggregates it into a
   period ratio.
2. No apportionment engine applying the Rule 42 (inputs/services) or Rule 43
   (capital goods) exempt:taxable ratio to common input credit.
3. No write path to post the reversal even once an agent computes it by hand —
   `JournalEntry` is read-only for `finance_user`, and there is no dedicated
   ITC-reversal entity/tool.

**Why it matters, in plain terms — worked example.** A GST-registered school has
two kinds of income in a month: tuition fees ₹8,00,000 (GST-**exempt** — education
is an exempt supply) and coaching/uniforms/hall-rental ₹2,00,000 (taxable). Exempt
share = 80%, taxable share = 20%. The school also pays ₹90,000 of GST on common
inputs that serve both activities — electricity, stationery, security, a shared
accountant, software. Under Rule 42, only the taxable-proportion share of that input
GST is claimable: ₹90,000 × 20% = ₹18,000. The remaining ₹90,000 × 80% = ₹72,000
must be reversed, with interest. If nobody computes this ratio, the school claims
the full ₹90,000 and that ₹72,000 becomes a liability GST assessment catches later —
one of the commonest GST errors in the education sector (`spec.md` UC-08). A clinic
hits the identical mechanics with a larger common-input pool (rent, staff,
equipment), since pharmacy sales are taxable but consultations/procedures are
exempt (UC-15).

**How we verified it's missing:**
1. `itc_eligibility` confirmed to be a fixed enum on `Bill`/`Invoice`, not a
   computed proportion or aggregate.
2. No apportionment-related entity or field (`ExemptTurnover`, `ApportionmentRatio`,
   `Rule42`, or similar) found anywhere in the schema.
3. No MCP tool computes or exposes an exempt:taxable turnover ratio.
4. `JournalEntry` permissions confirmed read-only for `finance_user` (`list`/`get`
   only, no `create`/`update`) — so even a correctly-computed reversal has nowhere
   to post.

**Who has it, and how we know:** **Clear [CLAIM]** sells this capability separately
as a paid product ("MaxITC") rather than bundling it — evidence it is both hard to
build and independently monetizable, not a corner case. RazorpayX and Mysa do not
claim it either; none of the three competitors in our set is confirmed to ship this
as a standard feature.

**The ask:**
1. A period-level exempt-turnover / taxable-turnover aggregate per company
   (derivable today by summing `Invoice.items[]` joined to `Item.tax_preference`,
   so this is mostly a rollup, not new source data).
2. A Rule 42 (inputs/services) and Rule 43 (capital goods) apportionment
   computation over that aggregate and the period's common-input GST.
3. A write path for the resulting reversal — either `finance_user` write access to
   `JournalEntry` scoped to this posting, or a dedicated `ITCReversal` entity/tool
   an agent can call.

**Why it's top priority.** Blocks 2 of 5 verticals (school, clinic) outright — not
a nice-to-have, a hard wall for those business types. Half of the capability is
already agent-buildable today (the compute/report half, over existing read-only
data, the same shape as N7's TDS-recompute verification and F8's MSME bridge
above); only the write half is a structural platform blocker no orchestration can
route around.

---

## 5. Suggested submission order

**Everything in §A is already filed. Only three defects remain (§C).**

1. **B8 (INR bills on the USD company)** — verified still live and worsening (13,
   was 10). Pairs with the already-fixed B1/N126 as the same wrong-jurisdiction
   seed-data defect in the opposite direction, which gives triage a precedent.
2. **B9 (feature flags vs tool exposure)** — weaker, but carries four
   correctly-aligned control cases, so it cannot be dismissed as a misunderstanding
   of how the flags work.
3. **B5** — only after reproducing against a concrete `JournalEntry.id`.
4. ~~**F18 (ITC apportionment, Rule 42/43)**~~ — ✅ **Filed** `a9f1888f…`, 23 Sep,
   **on its own, not in a batch**, exactly as recommended here: the one item whose
   argument is statutory rather than competitive, blocking two of five verticals,
   with the computation already working and only the *posting* missing. Full text
   in §4 above.
5. **F9 (OCR) and F10 (payment execution)** — the two significant omissions from the
   original feature list. Write up and file together; both are High, both are
   capabilities every competitor in the set has.
6. **F19–F22** (job work · composition mode · LUT registry · s.52 TCS) as one
   vertical-expansion batch, citing `spec.md`. Each names the statute it blocks.
7. **F16 (spend caps)** — **verify first** against `ApprovalPolicy.condition_*`
   before writing it up. F6 was originally wrong in exactly this way.
8. The remaining D.1 items as a single batch, referencing the competitor evidence in
   `razorpay_gap_report.md`, `clear_gap_report.md` and `gap_report_mysa.md`.
   Given N173's outcome, expect one low-priority card — file them for product value,
   not for score.

**Do not file `spec.md`'s buildable use cases.** UC-01 (Rule 37), UC-03/UC-21 (RCM),
UC-16 (expiry → blocked credit) and UC-06 (approval audit) need no platform change.
They are agent backlog. Filing them as requests would misrepresent work we can
already do.

**Do not file B7** — see §C. Its defect is already on the board as N6.

**Before the next filing round, re-read the board.** Its rows are not
machine-readable from here, so board IDs and statuses in this document are
transcribed by hand and lag reality. N1–N8's board IDs are not yet recorded.

**A note on method, worth repeating to whoever reviews this:** F6 was originally
written as "please build multi-level approvals." Verifying before submitting
revealed the engine already exists, with conditional routing, SLA escalation,
quorum groups and delegation — richer than the competitor feature we were citing as
the gap. Two of the eight items changed materially once checked. Any feature
request in this list that gets challenged should be re-verified rather than
defended.

**Before submitting anything further, confirm with the instructor** whether
`/api/bug-report` is the channel that earns bounty credit, or whether submissions
should also land on the class bug board — the two are not connected as far as we can
tell, and our three filed reports (`status: new`, `delivery: local`) have not
appeared on the board.
