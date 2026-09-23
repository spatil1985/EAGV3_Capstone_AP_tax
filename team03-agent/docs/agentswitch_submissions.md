# AgentSwitch — Bug Reports & Feature Requests (Team 03, Seat 03 Payables & Tax)

Consolidated, submission-ready list of everything we've found on the AgentSwitch
platform: confirmed defects, and feature gaps identified by comparing against real
competitor products.

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

**Verified against `GET /api/bug-report/mine` on both instances, 2026-09-23:**
**25 reports on India, 0 on Keystone.**

> 🚨 **B7, B8 and B9 have never been filed — on either instance.** They are written
> up in §2 below and were assumed filed, but neither account holds them. Worse,
> **N6's text opens with *"B7 (filed against Keystone/US only)…"* — that reference
> is wrong** and points triage at a report that does not exist. Either file B7 or
> correct N6. See §C.

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

*"Instance" = the company the defect is **about**. Every one of the 25 filings sits
on the **India** account's `bug-report/mine` — the Keystone-company findings
(N1–N4) were filed from there too, which is why the Keystone account reads 0.*

**Feature requests** — all eight filed 22 Sep, **collapsed into one board card**

| # | Title | Board |
|---|---|---|
| F1–F8 | GRN · sandbox · reports over MCP · bank validation · CA access · approvals entitlement · batch payment-run · MSME 45-day | **N173** ⚪ Low · *Carbon upgrade* · not scheduled |

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

### C · YET TO FILE — written up, verified, ready

Re-verified against live data 2026-09-23. **B7 and B8 have got worse since they
were written.**

| # | Title | Instance | Severity | Re-verification |
|---|---|---|---|---|
| **B7** | Recurring bills regenerate every day | US | **High** | 🔺 **Now 4 days** (20–23 Sep), was 3. Control template `5d45e8e8` (future `next_bill_date`) still fired exactly **once** — 3×4 vs 1×1 |
| **B8** | INR bills + GST fields on the USD company | US | Medium | 🔺 **Now 13 INR bills**, was 10 — growing because B7 keeps generating them |
| **B9** | Locale flags contradict MCP tool exposure | US | Low-Med | Still exact: `eway_bill=false` → **8** EWayBill tools (was 6); `form_1099=true` → 0 tools; 490 tools visible |
| B5 | Journal voucher ₹0.00 with no lines | India | Medium | ❗ Still needs reproduction against a concrete `JournalEntry.id` before filing |

**File B7 first.** It is the strongest item we hold: a live, self-demonstrating
duplicate-payables generator with a clean internal control group, still accruing,
and it *is* the Core Challenge Prompt ("is any vendor being paid twice?") happening
for real on the platform.

---

### D · NEW — competitor gaps identified but not yet written up

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

**Already covered, do not re-file:** GRN→F1 · sandbox→F2 · reports→F3 · bank
validation→F4 · CA access→F5 · approvals→F6 · batch run→F7 · MSME→F8.
**Already in §3 (platform self-documented):** e-invoicing GST-28 · GSTN fetch
GST-39 · TDS automation GST-18.

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

## 5. Suggested submission order

**Everything in §A is already filed. This order covers §C and §D only.**

1. **B7 (recurring bills regenerate daily)** — file today. It carries a control
   group, the "Quarterly pest control" template, identical in every respect except
   a future `next_bill_date`, which has fired **once** while its three siblings have
   now fired on **four** consecutive days. That isolates the defect to a single
   step and makes it hard to dismiss. It is live, still accruing, and it *is* the
   Core Challenge Prompt happening for real on the platform.
2. **Fix the B7 reference in N6** (or file B7 first so the reference becomes true).
   N6 is already on the board saying *"B7 (filed against Keystone/US only)"* — but
   B7 was never filed on either instance, so that cross-reference currently points
   nowhere.
3. **B8 (India seed data on the US company)** — pairs naturally with the fixed B1,
   the same defect in the opposite direction, and is now at 13 bills and growing
   because B7 keeps generating them. Cross-reference both.
4. **B9 (feature flags vs tool exposure)** — weakest of the three, but it carries
   four correctly-aligned control cases, so it cannot be waved away as a
   misunderstanding of how the flags work.
5. **B5** once reproduced with a concrete `JournalEntry.id`.
6. **F9 (OCR) and F10 (payment execution)** — the two significant omissions from
   the original feature list. Write up and file together; both are High, both are
   capabilities every competitor in the set has.
7. **F16 (spend caps)** — **verify first** against `ApprovalPolicy.condition_*`
   before writing it up. F6 was originally wrong in exactly this way.
8. The remaining §D items as a single batch, referencing the competitor evidence in
   `razorpay_gap_report.md`, `clear_gap_report.md` and `gap_report_mysa.md`.
   Given N173's outcome, expect one low-priority card — file them for product value,
   not for score.

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
