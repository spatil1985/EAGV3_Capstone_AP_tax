# assignment.md — Use-case spec ownership (Team 03, Seat 03)

**2026-09-23 · companion to [`spec.md`](spec.md)**

[`spec.md`](spec.md) catalogues 22 use cases across five verticals at *functional*
depth — what each one is, why it matters, and whether the data exists. It does not go
deep enough to implement from. This document splits those 22 into three workstreams,
assigns each to one person, and defines what "a detailed spec" has to contain so that
three people writing separately produce work that fits together.

**Nothing here changes the content of `spec.md`.** Verdicts (🟢/🟡/🔴), gap numbers and
phase ordering are carried over unchanged.

---

## 1. How the 22 were grouped

The grouping axis is **the data spine each question reads**, not the vertical it
serves. Verticals cut across each other (a clinic is also a retailer; a school is also
an agency buyer), but the *fields* a use case touches do not. Grouping by spine means
two people rarely need to reason about the same fields at the same time, and each
person builds one mental model instead of five.

| Workstream | Spine — the records it reads | The shape of every question in it |
|---|---|---|
| **WS-A · Inward obligations** | `Bill`, `PaymentMade`, `Party`, `ApprovalRequest`/`Log` | *A payables fact has created a statutory liability or a control failure* |
| **WS-B · ITC entitlement** | `Item` classification + the exempt:taxable output mix | *Of the GST we paid, how much may we actually keep?* |
| **WS-C · Outward supply & movement** | `Invoice`, `CreditNote`, `DeliveryChallan`, `EWayBill`, org tax mode | *Is what we sent out — goods or documents — correctly classified and covered?* |

A second, deliberate property of this split: **WS-A is almost entirely 🟢 buildable,
WS-C is where most of the 🔴 blocks live, and WS-B holds the single hardest
computation.** Each person therefore owns a different kind of difficulty — delivery
pressure, platform-gap argumentation, and statutory complexity respectively — rather
than one person absorbing all three.

---

## 2. Assignment at a glance

| WS | Owner | Use cases | Count | Verdicts | Platform gaps owned |
|---|---|---|---|---|---|
| **A** | **Sudip** | UC-01, UC-03, UC-04, UC-05, UC-06, UC-09, UC-13, UC-21 | 8 | 6🟢 2🟡 | none — owns the two shared contracts instead (§7) |
| **B** | **Geetha** | UC-02, UC-07, UC-08, UC-14, UC-15, UC-16 | 6 | 2🟢 2🟡 2🔴 | **GAP-1** → filed as **F18** |
| **C** | **Sandip** | UC-10, UC-11, UC-12, UC-17, UC-18, UC-19, UC-20, UC-22 | 8 | 3🟢 2🟡 3🔴 | **GAP-2/3/5/6** → filed as **F19–F22**; **GAP-4** → already **F1** |

All six gaps are now filed as feature requests
([`agentswitch_submissions.md`](agentswitch_submissions.md) §D.2). **Owning a gap here
means owning the technical argument behind it, not the filing** — if triage comes back
with questions on F18, Geetha answers them; on F19–F22, Sandip does.

**Why Sudip takes WS-A:** it contains the two use cases where prior work already exists
under his name — UC-05 is a rework of `scripts/invoice_matcher.py`, and UC-06 depends
on the `is_overdue` defects filed as N1/N8. Reassigning either would mean re-deriving
findings that are already understood.

**Why Geetha and Sandip take B and C as listed:** no basis to prefer one over the
other — swap freely if either has relevant domain exposure. The split between B and C
matters; who takes which does not.

---

## 3. What "a detailed spec" must contain

One file per use case, `docs/specs/uc-NN-short-name.md`. Same ten sections in the same
order in all 22, so they can be read and reviewed interchangeably.

| § | Section | What it must contain — and the bar to clear |
|---|---|---|
| 1 | **Question** | The user's own words, verbatim from `spec.md`. Do not rephrase into system language |
| 2 | **Statutory basis** | Exact section / rule / notification number **and the consequence** (interest rate, penalty, disallowance). "Rule 37" is not enough; "Rule 37 — reversal with interest at 18% p.a. from the date of availment" is |
| 3 | **Trigger** | When the agent runs this — on request, on a schedule, or on a document event. State the period it computes over |
| 4 | **Input contract** | Exact MCP tool or REST path, exact field names, filters, pagination limits. Every field must be one you have confirmed in `/api/schemas` or [`mcp_tool_inventory_india.md`](mcp_tool_inventory_india.md) — cite where you confirmed it |
| 5 | **Algorithm** | Numbered steps, deterministic, with a **worked example using real numbers pulled from the live instance**. Where the data does not exist (school/clinic), a constructed example with the values stated as constructed |
| 6 | **Known-bad data** | Which stored fields this use case must *not* trust, naming the bug: N7 `tds_amount`, N128 `CreditNote.taxes[]`, N1/N8 `is_overdue`, §7a document-level `taxes[]`. State the recomputation used instead |
| 7 | **Output contract** | The exact shape the agent returns: row schema, sort order, what makes a row a "finding" vs. context, and the one-sentence summary a human reads first |
| 8 | **Limits** | What this must never claim or do. Every spec ends in a report or escalation — **nothing posts to the ledger** (`JournalEntry` is read-only for `finance_user`) |
| 9 | **Validation** | How we know the answer is right with no real tenant to test against. Name the oracle: a platform endpoint, a hand-computed case, or a control group |
| 10 | **Open questions** | What you could not resolve. An empty section here is a warning sign, not a good sign |

**Definition of done:** another team member can implement the use case from the spec
without asking the author a question. That is the review test — each spec is read by
the other two people, and the reviewer's job is to try to implement it mentally and
report the first place they get stuck.

For 🔴 use cases, sections 4–5 describe what *would* be needed and section 10 carries
the gap argument — those specs feed the feature requests in
[`agentswitch_submissions.md`](agentswitch_submissions.md) §D, so they must be strong
enough to file.

---

## 4. WS-A · Sudip — Inward obligations

*Every question here starts from a supplier bill or a payment against one.*

| UC | Title | Verdict | The thing this spec must nail |
|---|---|---|---|
| **UC-01** | Rule 37 — 180-day non-payment ITC reversal | 🟢 | The reversal **row schema** (§7) — UC-08 and UC-16 emit the same row type. Get it right here, the others inherit it |
| UC-03 | RCM self-invoicing exposure | 🟢 | The supplier-type → RCM-expected mapping (GTA, advocate, director, sponsorship, import). This is a lookup table, and it belongs in the spec |
| UC-04 | MSME 45-day exposure | 🟢 | Dual consequence — penal interest **and** s.43B(h) disallowance. Already scoped as F8; the spec must add the computation, not restate the gap |
| UC-05 | Duplicate vendor payment detection | 🟡 | The three-tier key: `exact` (doc number + FY + GSTIN), `suspicious` (amount proximity), and the `recurring_bill_id` gate that suppresses the three known false positives |
| UC-06 | Approval SLA & segregation-of-duties audit | 🟢 | Recomputation of `is_overdue` from `resolved_at` vs `sla_deadline`. **Never read the stored flag** — it is wrong on 74% of India resolved requests |
| UC-09 | Vendor TDS verification (194C/194J/194I) | 🟢 | Verification only, not deduction. Recompute `tds_percentage × base`; treat stored `tds_amount` as suspect (N7) |
| UC-13 | 194Q / 206C(1H) ₹50 lakh thresholds | 🟡 | FY-cumulative aggregation and the mid-year crossover point — the obligation starts on the transaction that crosses, not at year end |
| UC-21 | Import of services — RCM | 🟢 | Pairs with UC-03; same check, `overseas` counterparty. Write them together, ship them as one playbook |

**Sequence:** UC-01 → UC-05 → UC-04 → UC-03 + UC-21 (together) → UC-06 → UC-09 → UC-13.
The first four are the whole of `spec.md` §6 Phase 1.

⚠️ **This workstream is the delivery critical path.** If it falls behind, UC-09 and
UC-13 are the two that can move — neither is Phase 1, and both are self-contained
aggregations that need no context from the rest of WS-A.

---

## 5. WS-B · Geetha — ITC entitlement (exempt & mixed supply)

*Every question here is a variation on: we paid GST on inputs — how much of it is
actually ours to keep?*

This is the workstream `spec.md` §3 identifies as **where we can genuinely win.** No
competitor in the comparison set (RazorpayX, Clear, Mysa) advertises exemption
apportionment. It is also the workstream that requires inverting the agent's own core
question (§2.1) — for a school or clinic, the right answer to *"what ITC is
unclaimed?"* is *"none, and here is what you wrongly claimed."*

| UC | Title | Verdict | The thing this spec must nail |
|---|---|---|---|
| **UC-07** | School — exempt vs taxable revenue split | 🟡 | **Write this first.** It is the prerequisite for UC-08, and its classification logic is reused by UC-14. Books nil-rated vs stationery taxable; in-house transport exempt vs third-party not |
| **UC-14** | Clinic — healthcare exempt vs pharmacy taxable | 🟡 | Same engine as UC-07, different rule set. Plus the ₹5,000/day non-ICU room-rent rule (post-18-Jul-2022, 5% **without ITC**) |
| **UC-08** | Rule 42 apportionment — school | 🔴 compute-only | The monthly ratio, the annual true-up, and the honest statement that we report but cannot post |
| **UC-15** | Rule 42/43 apportionment — clinic | 🔴 compute-only | Same mechanics, larger common-input pool. If it is genuinely identical to UC-08, say so and write one spec with a clinic section rather than duplicating |
| UC-02 | Blocked credit (s.17(5)) audit | 🟢 | The HSN-prefix → blocked-category mapping table. Motor vehicles, F&B, club membership, works contract, goods written off |
| UC-16 | Drug expiry → blocked credit under s.17(5)(h) | 🟢 | The cross-domain link: expiry is a stock event **and** a credit reversal. Reuses UC-02's blocking logic and UC-01's reversal row |

**Sequence:** UC-07 → UC-14 → UC-02 → UC-16 → UC-08 → UC-15.
Classification before apportionment: UC-08 cannot be specified until UC-07 defines how
exempt turnover is derived.

**You own GAP-1, now filed as F18** — the argument that ITC apportionment needs
platform support. It blocks two of five verticals, it is what Clear monetises
separately as MaxITC, and the computation is already possible — only the posting is
not. [`agentswitch_submissions.md`](agentswitch_submissions.md) calls F18 the
strongest feature ask in the document and says to file it **alone**, not batched.
Your UC-08 and UC-15 specs are the evidence behind that ask, so they need to be
strong enough for triage to read directly.

⚠️ **Data reality:** these fields exist but are **unpopulated** — no school or clinic
tenant exists on either instance. Every spec in WS-B is written against schema
capability, and §9 (validation) must say plainly what is untested rather than implying
it was checked.

---

## 6. WS-C · Sandip — Outward supply, movement & organisation tax mode

*Every question here is about what left the building — goods, an invoice, or a
declaration — and whether it was correctly classified and covered.*

| UC | Title | Verdict | The thing this spec must nail |
|---|---|---|---|
| UC-12 | E-way bill coverage & expiry audit | 🟢 | **Start here** — it is the one 🟢 with live data behind it. Coverage and expiry only; generation against the NIC portal is GST-29 and out of scope |
| UC-18 | HSN-wise rate-slab correctness | 🟢 | Frame as a **consistency** check (same HSN charged differently across invoices), because we hold no authoritative HSN→rate table. Say where that table would have to come from |
| UC-19 | Credit-note s.34(2) time limit | 🟢 | The 30-November-following-FY cutoff. **`CreditNote.taxes[]` is corrupt (N128) — item-level only** |
| UC-20 | Export of services / LUT tracking | 🟡 | Two independent tests: place of supply outside India, **and** payment in convertible foreign exchange. An "export" failing either is a domestic supply with unpaid tax |
| UC-22 | Advance-receipt GST on services | 🟡 | The goods-vs-services divergence — GST on an advance is payable for services, not goods. The distinction comes from `Item.product_type` |
| UC-11 | Three-way match (PO ↔ GRN ↔ Bill) | 🔴 | Split the verdict precisely: two-way is 🟡 (live compute via `endpoint.accounting.bill_match`, which N2 shows never persists), three-way is 🔴 for want of a GRN |
| UC-10 | Job work (s.143) / ITC-04 | 🔴 | Deemed-supply timing at 1 year / 3 years. `DeliveryChallan` is the right document type but has no job-work subtype or return tracking |
| UC-17 | Composition-scheme eligibility & breach | 🔴 | The core defect: `business_composition` exists only as a *counterparty* attribute — the organisation's own tax mode is not representable |

**Sequence:** UC-12 → UC-19 → UC-18 → UC-20 → UC-22 → UC-11 → UC-10 → UC-17.
Buildable first, blocked last — so that if time runs out, what is lost is gap
argumentation rather than shippable capability.

**You own five of the six platform gaps** — GAP-2 job work (**F19**), GAP-3
composition mode (**F20**), GAP-4 GRN (**F1**, filed earlier), GAP-5 LUT registry
(**F21**), GAP-6 s.52 e-commerce TCS (**F22**). All are filed; your specs are what
backs them if triage pushes back.

GAP-6/F22 has no use case of its own in `spec.md` — it needs one, scoped alongside
UC-17 and UC-18 for retail. That is the one genuinely new piece of scoping in this
workstream.

---

## 7. Shared contracts — where the three workstreams must agree

Three things are used by more than one person. Each has **one owner**, and the other
two consume rather than redefine.

| Contract | Owner | Consumed by | Why it must be shared |
|---|---|---|---|
| **ITC reversal row schema** | Sudip (defined in UC-01) | Geetha (UC-08, UC-15, UC-16) | Rule 37, Rule 42/43 and s.17(5)(h) all produce "credit to be reversed" findings. Three different row shapes for one concept would make the output unreadable |
| **Statutory constants table** | Sudip | Everyone | 180 days · 45 days · ₹50 lakh · ₹5,000/day · ₹50,000 · 1yr/3yr · 30 November. These are **rules, not data** — one playbook file, updatable same-day, never hardcoded in a spec |
| **Place-of-supply determination** | Sandip (defined in UC-20) | Sudip (UC-03, UC-21) | Inward RCM and outward export both turn on the same determination. One logic, two directions |

---

## 8. Rules that bind all three of us

Carried from [`spec.md`](spec.md) §0 and §7. Any spec that violates one of these gets
sent back in review.

1. **Compute tax from item-level fields.** `items[].cgst_amount`, `sgst_amount`,
   `igst_amount`, `cess_amount`. Document-level `taxes[]`, the `Tax`/`TaxJurisdiction`
   master and `group_taxes` are **not trustworthy on this instance**
   (`CURRENT_STATUS.md` §7a).
2. **Treat these stored values as suspect and recompute:** `tds_amount` (N7),
   `CreditNote.taxes[]` (N128), `is_overdue` on resolved requests (N1/N8),
   `Bill.match_status` (N2 — always null).
3. **Nothing posts to the ledger.** `JournalEntry` is read-only for `finance_user`.
   Every use case ends in a report or an escalation. Say so in §8 of each spec rather
   than leaving it implied.
4. **Cite where you confirmed each field** — a `/api/schemas` pull or
   [`mcp_tool_inventory_india.md`](mcp_tool_inventory_india.md). A field name that
   turns out not to exist invalidates the spec that depends on it.
5. **Tax positions are engineering specifications, not tax advice.** Rates, thresholds
   and exemption entries change. Each spec names the notification it relies on so it
   can be rechecked.

---

## 9. What is not assigned here

- **Dates.** Sequencing within each workstream is given; calendar deadlines are not.
  Add them once the milestone date is fixed.
- **Implementation.** This covers specs only. Who builds what is a separate decision,
  and deliberately so — the spec review (§3) is the point at which we find out whether
  a use case is as buildable as `spec.md` claims.
- **The competitor gaps** (F9–F17 in
  [`agentswitch_submissions.md`](agentswitch_submissions.md) §D.1). They argue *"a
  rival ships this and we don't"*, are product requests rather than use cases, and
  none has a `spec.md` entry. Distinct from §D.2's F18–F22, which are the six gaps
  owned above and argue *"Indian tax law requires this and the data model cannot
  represent it"*.
- **Filing and triage follow-up.** The submissions document owns that. This document
  only says who can answer a technical question about each gap.
