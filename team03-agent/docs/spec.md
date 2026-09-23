# spec.md — Multi-Vertical AP & Tax Agent (India)

**Team 03 · Seat 03 Payables & Tax · 2026-09-23**

Functional specification for extending the agent beyond a single manufacturing
company to five Indian organisation types: **school, manufacturing, clinic, retail,
agency**.

Each use case states **what it is, why it matters (statute + consequence), what
question it answers in the user's own words**, and — critically — **whether the data
to answer it actually exists**, verified against the live schema rather than assumed.

---

## 0. Method and grounding

| Source | What it gives us | Confidence |
|---|---|---|
| `GET /api/schemas` live, 2026-09-23 | Real field names, enums, types | **Verified** |
| [`mcp_tool_inventory_india.md`](mcp_tool_inventory_india.md) | 468 tools, 142 groups, `finance_user` scope | **Verified** |
| `CURRENT_STATUS.md` §7a/§9a | Which tax data is trustworthy | **Verified** |
| [`razorpay_gap_report.md`](razorpay_gap_report.md) | RazorpayX, one live account | **[LIVE]** / **[DEMO]** |
| [`clear_gap_report.md`](clear_gap_report.md) | Clear, adversarially verified marketing | **[VENDOR-V]** |
| [`gap_report_mysa.md`](gap_report_mysa.md) | Mysa, vendor pages | **[CLAIM]** |

**Two constraints carried forward from prior findings, both still binding:**

1. **Tax values must be computed from item-level fields** (`items[].cgst_amount`,
   `sgst_amount`, `igst_amount`, `cess_amount`). Document-level `taxes[]`, the
   `Tax`/`TaxJurisdiction` master and `group_taxes` are not trustworthy on this
   instance (`CURRENT_STATUS.md` §7a). Every computation below assumes item-level.
2. **`approvals` is now entitled.** `allowed_apps` reads
   `accounting, agent, crm, approvals` as of 2026-09-23 — F6 was granted, so
   `ApprovalRequest`/`ApprovalLog` are readable. Several use cases below depend on
   this and were previously blocked.

---

## 1. What the platform already supports (verified)

The schema is **considerably more multi-vertical than the current agent uses**. These
fields exist today and are unused by our playbooks:

| Field / tool | Enables | Which verticals |
|---|---|---|
| `Item.hsn_or_sac` | HSN (goods) / SAC (services) classification | All five |
| `Item.product_type` = `goods \| services` | Supply-type split | All five |
| `Item.tax_preference` = `taxable \| tax_exempt` | **Exempt-supply classification** | **School, clinic** |
| `Item.taxable`, `Item.tax_exemption_reason` | Per-item exemption with reason | School, clinic |
| `Item.intra_state_tax_rate`, `inter_state_tax_rate` | CGST+SGST vs IGST rate split | All five |
| `Bill/Invoice.gst_treatment` = `business_gst \| business_composition \| consumer \| overseas \| unregistered_business \| sez \| deemed_export` | Counterparty tax status | **Agency (export/SEZ), retail (B2C)** |
| `Bill/Invoice.itc_eligibility` = `input \| input_services \| capital_goods \| ineligible` | **Blocked-credit tagging (s.17(5))** | All five |
| `Bill/Invoice.is_reverse_charge` | **RCM** | Manufacturing (GTA), agency (import of services) |
| `place_of_supply`, `source_of_supply`, `destination_of_supply` | Place-of-supply determination | All five |
| `TaxExemption`, `ExemptionCertificate` | Exemption registry with expiry | School, clinic |
| `Item.is_manufactured`, `default_bom_id`, `routing_id`, `batch_tracked`, `serial_tracked` | BOM / production | **Manufacturing** |
| `Item.requires_incoming_inspection`, `sampling_plan` | Incoming QC | Manufacturing |
| `Item.shelf_life_days`, `batch_tracked` | Expiry management | **Clinic (pharmacy), retail** |
| `Item.mrp`, `selling_price`, `category_id`, `variants`, `is_published` | Retail catalogue | **Retail** |
| `endpoint.inventory.shipments`, `endpoint.make.orders` | Goods movement, production orders | Manufacturing, retail |
| `EWayBill.*` (6 tools incl. `generate`, `activate`) | Goods movement compliance | Manufacturing, retail |
| `Party.is_msme`, `msme_type`, `msme_no` | MSME counterparty status | All five |
| `ApprovalRequest`/`ApprovalLog` (now entitled) | Approval chains, SLA, audit | All five |

**Verdict: the data model is vertical-ready. The agent is not.** Our SKILL.md and
playbooks assume a single manufacturing company with fully taxable output. Nothing
reads `tax_preference`, `product_type`, `hsn_or_sac` or `is_reverse_charge`.

---

## 2. The tax reality that drives everything

Three statutory mechanics decide which verticals are easy and which are hard.

### 2.1 Exempt supply kills ITC — and that inverts our core question

Our Core Challenge Prompt asks *"what is unclaimed [ITC]?"* That question assumes
credit is claimable. For a **school** (Notification 12/2017-CT(R) entry 66, education
to students/faculty/staff) and largely for a **clinic** (entry 74, healthcare by a
clinical establishment), output is **exempt** — so input GST is **not** a credit, it
is a **cost**, and claiming it is an error to be reversed.

> **For two of five verticals, the correct answer to "what ITC is unclaimed?" is
> "none, and here is what you wrongly claimed and must reverse."** The agent must
> invert its own core question based on `Item.tax_preference` and the output mix.

### 2.2 Mixed supply forces apportionment (Rule 42 / 43)

Neither school nor clinic is *purely* exempt:

- **School:** tuition exempt; but coaching, uniforms, stationery, third-party
  transport and commercial hall hire are taxable.
- **Clinic:** consultation and procedures exempt; but **outpatient pharmacy sales are
  taxable**, room rent above ₹5,000/day (non-ICU, post-18-Jul-2022) is taxable at 5%,
  and cosmetic procedures are taxable unless reconstructive.

Mixed output ⇒ common input credit must be apportioned by the exempt:taxable turnover
ratio (**Rule 42** for inputs/services, **Rule 43** for capital goods), computed
monthly and trued-up annually.

**This is the single hardest and highest-value computation across the five verticals,
and none of RazorpayX, Mysa or Clear names it as a shipped feature.**

### 2.3 Rule 37 — AP behaviour creates a tax liability

If a supplier invoice is **not paid within 180 days**, ITC already taken must be
reversed with interest. This is a *payables* fact producing a *tax* consequence —
precisely the intersection Seat 03 owns, and it applies to **all five verticals**.

---

## 3. Competitive position, per vertical

Can we serve these organisations today, versus the three competitors?

| Vertical | RazorpayX | Clear | Mysa | **AgentSwitch + our agent** |
|---|---|---|---|---|
| **School** | ❌ Payouts + payroll only; no exemption logic | ⚠️ Strong GST/ITC engine, but no education-specific exemption or s.11/12 trust accounting | ❌ Assumes taxable AP | ⚠️ **Fields exist** (`tax_preference`, `TaxExemption`); apportionment must be built |
| **Manufacturing** | ⚠️ Payouts, TDS | ✅ Strongest — e-invoicing, IRP, 2A/2B | ✅ 3-way match, RCM, TDS | ✅ **Closest to parity** — BOM, routing, QC, e-way bill, PO↔Bill all present |
| **Clinic** | ❌ | ⚠️ Generic GST only | ❌ | ⚠️ Same as school + `batch_tracked`/`shelf_life_days` for pharmacy |
| **Retail** | ⚠️ Collections | ✅ ClearOne billing, e-invoice | ✅ AP side | ⚠️ Catalogue/MRP/variants present; **no composition-scheme mode**, no s.52 TCS |
| **Agency** | ✅ Vendor payouts | ✅ GST returns | ✅ AP + TDS | ✅ `gst_treatment` covers `overseas`/`sez`; **no LUT/refund tracking** |

**Where we can genuinely win:** school and clinic. Both hinge on exempt/mixed-supply
ITC logic that is *computable from data we already hold* and that no competitor in
our set advertises. Clear is closest (MaxITC) but targets reconciliation against
GSTR-2B, not exemption apportionment.

**Where we cannot compete today:** anything requiring money movement (RazorpayX) or
statutory filing/IRP (Clear). `CURRENT_STATUS.md` and `razorpay_gap_report.md` §3
both argue against chasing those.

---

## 4. Use case catalogue

Format per the brief: **what · why · the question it answers · data available ·
verdict**.

Verdicts: 🟢 **Buildable now** (data verified present) · 🟡 **Partial** (needs a
derivation or has a data caveat) · 🔴 **Blocked** (needs a platform change).

---

### 4.1 Cross-cutting — applies to all five verticals

#### UC-01 · Rule 37 — 180-day non-payment ITC reversal 🟢

**What:** find every purchase invoice where ITC was taken but the supplier remains
unpaid past 180 days from invoice date, and compute the reversal plus interest.

**Why:** Section 16(2) proviso + Rule 37. Reversal is mandatory with interest at 18%.
It is invisible in every AP screen because it is a *tax* consequence of an *AP*
fact — no ageing report flags it and no tax report knows about payment status.

**The question it answers:**
> *"Which unpaid bills are about to cost me my input credit, and how much?"*

**Data:** `Bill.date`, `Bill.balance_due`, `Bill.amount_paid`,
`Bill.itc_eligibility`, `items[].cgst/sgst/igst_amount`, `PaymentMade.bills[]`.

**Verdict:** 🟢 Buildable today with `Bill.list` + `PaymentMade.list`. **This is the
single highest-value cross-vertical use case and no competitor names it.**

---

#### UC-02 · Blocked credit (s.17(5)) audit 🟢

**What:** find bills where `itc_eligibility` is not `ineligible` but the item class
suggests it should be — motor vehicles, food and beverage, club membership, works
contract for immovable property, goods lost/written off.

**The question it answers:**
> *"Have we claimed credit on anything the law blocks?"*

**Data:** `Bill.itc_eligibility` (enum includes `ineligible`), `Item.hsn_or_sac`,
`Item.category_id`, `items[]`.

**Verdict:** 🟢 Buildable. HSN-prefix → blocked-category mapping is agent-side logic.

---

#### UC-03 · RCM self-invoicing exposure 🟢

**What:** identify inward supplies attracting reverse charge — goods transport
agency, legal services from advocates, director sitting fees, sponsorship, import of
services — and check whether the RCM flag is set and the liability discharged.

**Why:** s.9(3)/9(4) CGST. RCM liability is the *recipient's* — an unflagged RCM
supply is an undeclared liability, not merely a missing credit.

**The question it answers:**
> *"Which supplier bills make us liable to pay the tax ourselves, and have we?"*

**Data:** `Bill.is_reverse_charge`, `Party.gst_treatment` (incl.
`unregistered_business`, `overseas`), `Item.hsn_or_sac`.

**Verdict:** 🟢 Buildable. Flagging mismatches between supplier type and the RCM flag
is a pure cross-check.

---

#### UC-04 · MSME 45-day exposure 🟢

**What:** MSME suppliers approaching or past the 45-day statutory payment window.

**Why:** MSMED Act s.15/16 (penal interest at 3× RBI bank rate) **and** Income Tax
s.43B(h) — the expense is disallowed until actually paid, so a late payment costs
penal interest *and* tax.

**The question it answers:**
> *"Which small suppliers are we about to pay late, and what will it cost us?"*

**Data:** `Party.is_msme`, `msme_type`, `Bill.due_date`, `Bill.date`,
`Bill.balance_due`.

**Verdict:** 🟢 Buildable. (Already scoped as F8; unchanged.)

---

#### UC-05 · Duplicate vendor payment detection 🟡

**What:** the Core Challenge Prompt.

**The question it answers:**
> *"Is any vendor being paid twice?"*

**Data:** `Bill.bill_number`, `vendor_id`, `date`, `grand_total`,
`recurring_bill_id`, `PaymentMade.bills[]`.

**Verdict:** 🟡 **Rework required.** `scripts/invoice_matcher.py` keys on
same-vendor + identical amount within ±3 days, which produced **three false
positives** on Keystone against recurring templates. Adopt Clear's key —
**document number + financial year + counterparty GSTIN** — as the `exact` tier and
demote amount-proximity to `suspicious`, gated on a `recurring_bill_id` check.

---

#### UC-06 · Approval SLA and segregation-of-duties audit 🟢 *(newly unblocked)*

**What:** which payment approvals breached SLA, who approved outside policy, and
whether anyone approved their own request.

**Why:** `ApprovalPolicy.allow_self_approval` exists as a control; a real audit checks
whether it held. Newly possible — `approvals` was entitled on 2026-09-23.

**The question it answers:**
> *"Who approved what, was it within policy, and did anyone approve their own bill?"*

**Data:** `ApprovalRequest` (`current_level`, `total_levels`, `sla_deadline`,
`is_overdue`, `final_decision`, `steps`, `history`), `ApprovalLog` (`actor_id`,
`action`, `ip_address`, `timestamp`), `ApprovalPolicy`.

**Verdict:** 🟢 Buildable — **but `is_overdue` is known-unreliable on resolved
requests (filed as N1/N8: 8.6% error on US, 74% on India).** The agent must
recompute from `resolved_at` vs `sla_deadline`, not trust the stored flag. That
makes this a use case where our agent is *more correct than the platform*.

---

### 4.2 School

Legal frame: education services exempt (Notif. 12/2017 entry 66); coaching is **not**
exempt; most schools are s.12AA/12AB registered trusts.

#### UC-07 · Exempt vs taxable revenue split 🟡

**What:** classify every revenue stream — tuition, transport, hostel, uniforms,
books, stationery, coaching, hall hire — as exempt or taxable.

**Why:** everything downstream (registration threshold, apportionment ratio, return
filing) depends on this split being right. Schools routinely misclassify: books are
nil-rated, stationery is taxable; in-house transport to students is exempt,
third-party bus service is not.

**The question it answers:**
> *"Which of our income streams are actually taxable, and are we treating them
> correctly?"*

**Data:** `Item.tax_preference`, `Item.taxable`, `Item.tax_exemption_reason`,
`Item.hsn_or_sac`, `Item.product_type`, `Invoice(direction=receivable).items[]`.

**Verdict:** 🟡 Fields exist but are **unpopulated for a school** on this instance —
needs seeded data or a real tenant to validate against.

---

#### UC-08 · Rule 42 apportionment for a mixed-supply school 🔴

**What:** compute the monthly exempt:taxable turnover ratio and apportion common
input credit; true up annually.

**Why:** Rule 42. Claiming full ITC while making exempt supplies is one of the
commonest GST errors in the education sector, and it is recovered with interest and
penalty on assessment.

**The question it answers:**
> *"How much of our input credit are we actually entitled to keep?"*

**Data:** requires **exempt-supply turnover per period** — derivable by summing
`Invoice.items[]` where the linked `Item.tax_preference = tax_exempt`.

**Verdict:** 🔴 **Blocked as a platform capability, 🟡 computable by the agent.**
There is no apportionment engine and no exempt-turnover field; `itc_eligibility` is a
per-document enum, not a proportion. The agent can compute and *report* the ratio and
the reversal amount, but cannot post the reversal. **See GAP-1.**

---

#### UC-09 · Vendor TDS for a trust 🟢

**What:** TDS on contractor payments (194C), professional fees (194J), rent (194I).

**Why:** a school pays bus contractors, housekeeping, visiting faculty and landlords.
TDS default triggers interest plus 30% expense disallowance.

**The question it answers:**
> *"Are we deducting the right TDS on every vendor payment, under the right section?"*

**Data:** `Bill.tds_amount`, `tds_percentage`, `tds_section_code`, `tds_section`,
`Party` records.

**Verdict:** 🟢 Buildable as a **verification** layer — recompute
`tds_percentage × base` and flag disagreement. **Note N7: `tds_amount` is currently
corrupt on 9 India bills** (unrelated to base, driving negative `grand_total`), so
the agent must treat stored TDS as suspect and recompute. Auto-deduction by threshold
is GST-18, not ours to build.

---

### 4.3 Manufacturing

The best-supported vertical — this is what Suryodaya already is.

#### UC-10 · Job-work movement and ITC-04 🔴

**What:** track inputs/capital goods sent to a job worker and returned within
1 year / 3 years respectively.

**Why:** s.143 + Rule 45. Goods not returned in time are **deemed a supply** on the
date they were sent, with tax and interest.

**The question it answers:**
> *"What have we sent out for job work that hasn't come back, and when does it
> become a taxable supply?"*

**Data:** ❌ No `job_work` concept anywhere in the 468 tools or the schema.
`DeliveryChallan` exists and is the right document type, but has no job-work
subtype or return-tracking.

**Verdict:** 🔴 **Blocked.** See GAP-2.

---

#### UC-11 · Three-way match (PO ↔ GRN ↔ Bill) 🔴

**The question it answers:**
> *"Were the goods we're being billed for actually received?"*

**Verdict:** 🔴 **Structurally blocked — no GRN entity** (F1). Note N2: a working
`endpoint.accounting.bill_match` exists and computes PO↔Bill, but never persists to
`Bill.match_status`. So two-way is 🟡 (compute live per bill), three-way is 🔴.

---

#### UC-12 · E-way bill coverage audit 🟢

**What:** find outward movements above ₹50,000 with no valid, unexpired e-way bill.

**Why:** Rule 138. Goods in transit without a valid e-way bill are liable to
detention and a penalty of tax + 100%.

**The question it answers:**
> *"Is anything moving on the road right now without valid documentation?"*

**Data:** `EWayBill` (`eway_bill_number`, `expiry_date`, `status`, `distance_km`,
`transaction_type`, `transaction_id`), `Invoice`/`DeliveryChallan` totals.

**Verdict:** 🟢 Buildable as a **coverage and expiry audit**. Generation against the
NIC portal is GST-29 and out of scope.

---

#### UC-13 · 194Q / 206C(1H) threshold monitoring 🟡

**What:** track cumulative purchases per supplier past ₹50 lakh (TDS 194Q @0.1%) and
sales per customer past ₹50 lakh (TCS 206C(1H)).

**Why:** both are turnover-cumulative obligations that start mid-year. Missing the
crossover means under-deduction for the rest of the year.

**The question it answers:**
> *"Which suppliers or customers have we crossed the ₹50 lakh line with?"*

**Data:** `Bill.list(vendor_id)` / `Invoice.list(party_id)` aggregated by FY.

**Verdict:** 🟡 Buildable by aggregation; no native threshold tracking exists
(consistent with GST-18).

---

### 4.4 Clinic

The hardest vertical, and the most differentiated opportunity.

#### UC-14 · Healthcare exempt vs pharmacy taxable split 🟡

**What:** separate exempt clinical services from taxable pharmacy sales, taxable room
rent above ₹5,000/day, and taxable cosmetic procedures.

**Why:** a clinic is a textbook mixed supplier. The 18-Jul-2022 amendment made
non-ICU room rent above ₹5,000/day taxable at 5% **without ITC** — a rule many
clinics still miss.

**The question it answers:**
> *"Which parts of what we do are taxable, and are we charging GST on the right
> ones?"*

**Data:** `Item.tax_preference`, `product_type`, `hsn_or_sac`,
`Invoice.items[]`.

**Verdict:** 🟡 Fields support it; the ₹5,000/day room-rent rule needs a
rate-and-threshold rule the agent carries in a playbook, not in the platform.

---

#### UC-15 · Rule 42/43 apportionment for a clinic 🔴/🟡

Same mechanics as UC-08, higher stakes — pharmacy purchases are a large common input
pool.

**The question it answers:**
> *"Of all the GST we paid on purchases, how much can we actually keep?"*

**Verdict:** Same as UC-08. **See GAP-1.**

---

#### UC-16 · Drug expiry and batch exposure 🟢

**What:** pharmacy stock approaching expiry, and the ITC consequence of writing it
off.

**Why:** s.17(5)(h) — ITC on goods written off or destroyed is **blocked**. Expiry is
therefore both a stock loss and a credit reversal.

**The question it answers:**
> *"What stock is about to expire, and what credit do we lose when it does?"*

**Data:** `Item.shelf_life_days`, `Item.batch_tracked`, `Item.serial_tracked`,
`endpoint.inventory.shipments`.

**Verdict:** 🟢 Buildable — and a genuinely cross-domain answer (stock + tax) that no
competitor in our set offers.

---

### 4.5 Retail

#### UC-17 · Composition scheme eligibility and breach 🔴

**What:** for a small retailer under s.10 composition (1% for goods traders, turnover
≤ ₹1.5 crore): monitor the threshold and flag disqualifying activity — inter-state
outward supply, e-commerce sales, exempt services beyond the permitted limit.

**Why:** breaching composition retrospectively converts the taxpayer to regular from
the breach date, with tax recoverable at full rates on everything since.

**The question it answers:**
> *"Are we still eligible for the composition scheme, and are we about to fall out of
> it?"*

**Data:** `gst_treatment` includes `business_composition` — but **only as a
counterparty attribute**, not as a mode for the organisation itself. No composition
turnover tracking.

**Verdict:** 🔴 **Blocked.** See GAP-3.

---

#### UC-18 · HSN-wise rate-slab correctness 🟢

**What:** verify each item's applied rate against its HSN code and the correct slab
(0/5/12/18/28 + cess).

**Why:** retail carries a wide HSN spread. Under-charging is recovered from the
seller; over-charging is a s.171 anti-profiteering exposure.

**The question it answers:**
> *"Are we charging the right GST rate on every product we sell?"*

**Data:** `Item.hsn_or_sac`, `intra_state_tax_rate`, `inter_state_tax_rate`,
`items[].cgst_rate/sgst_rate/igst_rate`.

**Verdict:** 🟢 Buildable as a **consistency check** (same HSN charged at different
rates across invoices). An authoritative HSN→rate table would have to be carried in a
playbook.

---

#### UC-19 · Credit-note time-limit monitoring 🟢

**What:** s.34(2) — a GST credit note against a supply can only reduce liability if
issued by 30 November following the financial year.

**The question it answers:**
> *"Which returns can we still issue a tax-effective credit note for?"*

**Data:** `CreditNote.date`, `CreditNote.invoice_id`, `Invoice.date`.

**Verdict:** 🟢 Buildable. **Caveat: `CreditNote.taxes[]` is corrupt on this instance
(N128 open) — use item-level only.**

---

### 4.6 Agency (services — marketing, consulting, professional)

#### UC-20 · Export of services / LUT tracking 🟡

**What:** for zero-rated export of services (s.16 IGST Act), confirm each export
qualifies (place of supply outside India, payment in convertible foreign exchange)
and is covered by a valid LUT.

**Why:** exporting without a LUT means IGST must be paid and refunded — a working-
capital hit. And a "export" that fails the place-of-supply test is simply a domestic
supply with unpaid tax.

**The question it answers:**
> *"Are our export invoices genuinely zero-rated, and is our LUT still valid?"*

**Data:** `Invoice.gst_treatment` = `overseas` / `sez`, `place_of_supply`,
`destination_of_supply`, `Invoice.currency`, `exchange_rate`.

**Verdict:** 🟡 Classification data exists; **no LUT entity** — LUT validity would
have to live in `TaxExemption` (`exemption_reason` + `associated_with`) as a
workaround, or in agent memory.

---

#### UC-21 · Import of services — RCM 🟢

**What:** foreign vendor invoices (software subscriptions, overseas contractors,
OIDAR) attract RCM in the recipient's hands.

**The question it answers:**
> *"Which foreign supplier bills create a GST liability we have to pay ourselves?"*

**Data:** `Party.gst_treatment = overseas`, `Bill.is_reverse_charge`,
`Bill.currency_code`.

**Verdict:** 🟢 Buildable — flag `overseas` supplier bills where
`is_reverse_charge` is false. A common and expensive oversight for agencies.

---

#### UC-22 · Advance-receipt GST on services 🟡

**What:** for services, GST is payable on **receipt of advance**, not on invoice —
unlike goods.

**The question it answers:**
> *"Have we paid GST on client advances we're still holding?"*

**Data:** `PaymentReceived.unused_amount`, `advance_amount`, `RetainerInvoice`.

**Verdict:** 🟡 Data exists (`RetainerInvoice` is exactly the advance construct); the
goods-vs-services distinction must come from `Item.product_type`.

---

## 5. Platform gaps requiring change

Ordered by how many verticals they block.

| # | Gap | Blocks | Why it cannot be orchestrated around |
|---|---|---|---|
| **GAP-1** | **ITC apportionment (Rule 42/43)** — no exempt-turnover aggregate, no apportionment engine, no reversal posting | **School, clinic** (2 of 5) | The agent can *compute and report* the ratio, but `JournalEntry` is read-only for `finance_user`, so it cannot post the reversal. Reporting without posting leaves the books wrong |
| **GAP-2** | **Job work (s.143) / ITC-04** — no job-work document type or return tracking | Manufacturing | Deemed-supply timing cannot be tracked against a document type that does not exist |
| **GAP-3** | **Composition-scheme mode** — `business_composition` exists only as a counterparty attribute | Retail (small traders) | The org's own tax mode is not representable |
| **GAP-4** | **GRN entity** (already F1) | Manufacturing, retail | Three-way match needs a receipt document |
| **GAP-5** | **LUT / export-declaration registry** | Agency | No entity models an LUT and its validity period |
| **GAP-6** | **s.52 e-commerce TCS** | Retail (marketplace sellers) | No TCS-collected-by-operator concept |

**GAP-1 is the one to argue for.** It blocks two verticals outright, it is the
capability Clear monetises separately as MaxITC, and the computation is already
possible — only the *posting* is not.

---

## 6. Build order

Ranked by value per unit of work, given everything above.

**Phase 1 — cross-vertical, buildable today, no platform change**
1. **UC-01 Rule 37** (180-day reversal) — highest value, applies to all five, no
   competitor names it
2. **UC-05 duplicate detection, reworked** — the Core Challenge Prompt, with Clear's
   document-identity key replacing the amount heuristic that produced three false
   positives
3. **UC-04 MSME 45-day** — dual statutory cost, already scoped
4. **UC-03 / UC-21 RCM exposure** — cheap cross-check, expensive to get wrong

**Phase 2 — vertical differentiation**
5. **UC-14 / UC-07 exempt-supply classification** — the prerequisite for everything
   school and clinic
6. **UC-08 / UC-15 apportionment reporting** — compute and report even though we
   cannot post (GAP-1)
7. **UC-16 expiry → blocked credit** — clinic/retail, genuinely cross-domain
8. **UC-06 approval audit** — newly unblocked, and our recomputation is *more correct
   than the platform's own flag*

**Phase 3 — blocked pending platform**
GAP-1 through GAP-6, filed as feature requests per
[`agentswitch_submissions.md`](agentswitch_submissions.md) §D.

---

## 7. What this means for SKILL.md

The current charter assumes one manufacturing company with fully taxable output. To
serve five verticals it needs:

1. **An organisation-type dimension.** `GET /api/accounting/locale` gives country and
   tax regime but **not** business type. Derive it from the `Item` mix
   (`product_type`, `tax_preference`, `is_manufactured`) rather than hardcoding.
2. **An exempt-supply branch.** Before answering "what ITC is unclaimed", check
   whether output is exempt — if so, invert the question (§2.1).
3. **Playbook-carried statutory constants** — 180 days (Rule 37), 45 days (MSME),
   ₹50 lakh (194Q/206C), ₹5,000/day (room rent), ₹50,000 (e-way bill), 1yr/3yr (job
   work), 30 Nov (s.34/s.16(4)). These are rules, not data, and belong in playbooks
   where they can be updated same-day.
4. **A standing distrust rule for stored tax values.** Recompute from item-level
   fields; treat `tds_amount`, document-level `taxes[]` and `is_overdue` as suspect
   until verified (N7, N128, N1/N8).

---

## 8. Honest limitations

- **No non-manufacturing tenant exists to test against.** Both instances are
  precision-engineering companies. Every school/clinic/retail/agency use case is
  specified against *schema capability*, not observed data. The fields exist; whether
  they behave correctly when populated for an exempt supplier is **untested**.
- **Competitor positions carry their original evidence tiers** — RazorpayX [LIVE],
  Clear [VENDOR-V], Mysa [CLAIM]. None was re-verified for vertical fit specifically.
- **Tax positions here are engineering specifications, not tax advice.** Rates,
  thresholds and exemption entries change; each should be confirmed against the
  current notification before a filing decision relies on it.
- **The agent still cannot post anything to the ledger.** `JournalEntry` is read-only
  for `finance_user`, so every computation above ends in a report or an escalation,
  never a correcting entry.
