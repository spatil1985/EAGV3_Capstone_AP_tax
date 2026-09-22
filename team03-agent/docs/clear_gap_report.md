# Clear (ClearTax) — Detailed Competitor Analysis

Deep-dive companion to [`gap_report.md`](gap_report.md), which covers all six
competitors at a summary level. This document walks **every Clear product and
module we could evidence**, explains what each one does, and states what it
implies for the Team 03 Payables & Tax Agent.

**Date of research:** 2026-09-22
**Products:** Clear / ClearTax (`clear.in`, `cleartax.in`, `cleartax.com`), legal
entity **Defmacro Software Pvt Ltd**
**Why Clear:** it is our closest functional comparator — the only competitor in
our set whose core business is *exactly* the Core Challenge Prompt (tax
liability, unclaimed ITC, duplicate vendor payments) — and the only one with a
**regulatory** moat rather than a purely functional one.

**How this differs from [`razorpay_gap_report.md`](razorpay_gap_report.md):** we
have no Clear account. Nothing here is `[LIVE]`. That is the central limitation
of this document and §0 explains exactly what it costs us.

---

## 0. Evidence tiers — read this first

Following the precedent set by the RazorpayX analysis, every claim here is
tagged. Our tiers are different because our access is different.

| Tag | Meaning | Reliability |
|---|---|---|
| **[GOV]** | Verified on a government domain (`gst.gov.in`) | Strongest — independent of Clear's own claims |
| **[PRESS]** | Corroborated by two or more independent publications | Strong for events (acquisitions, launches), not for capability |
| **[VENDOR-V]** | Clear's own live page, fetched and **adversarially verified** — survived a 3-vote challenge | Moderate — proves the product exists and what it is called, **not** that it works well |
| **[REFUTED]** | Claim was tested and **failed** verification | Recorded so it is not re-imported later. See §7 |

**Method.** 28 sources fetched; 134 candidate claims extracted; 25 taken through
adversarial verification; **15 confirmed, 10 refuted**.

**The honest caveat, stated up front.** `[VENDOR-V]` is weaker than `[LIVE]` in
exactly the way the RazorpayX analysis warned about. Clear's marketing shows the
product as Clear wishes it were. Verification here tested whether *Clear actually
claims a thing and claims it consistently* — it could not test whether the thing
works, how deep it goes, or whether it is generally available. Every module below
should be treated as unverified for depth pending a demo or trial.

**And the RazorpayX lesson applies directly.** That analysis found a competitor
had *withdrawn* GST and advance-tax remittance. Nothing in vendor marketing would
ever tell us that. We should assume Clear's pages have the same blind spot.

---

## 1. What Clear actually is

Three businesses under one brand. Conflating them produces nonsense comparisons.

### 1.1 Consumer — ITR filing **[VENDOR-V]**

Free self-service income-tax e-filing, plus a paid CA-assisted ladder. AY 2026-27
tiers, branded by taxpayer profile:

| Tier | Audience | Price (list / discounted) |
|---|---|---|
| Basic | Salaried professionals | not captured |
| Premium | Traders and freelancers | not captured |
| Elite | Global wealth builders (badged "Investors Favourite") | ₹11,998 / ₹5,999 |
| Luxe | Year-round support | ₹29,998 / ₹14,999 |

Tiers differ genuinely, not just by price: income-type eligibility, filing SLA
(24hr vs 72hr priority), advisory minutes, Schedule FA / ESOP-RSU handling.

⚠️ **Tier names change every assessment year.** A SKU verified here was
previously branded "Premium Plus". Date every citation.

### 1.2 SMB — ClearOne **[VENDOR-V]**

Billing/invoicing for small business. Covers seven GST document types:
proforma/estimates, invoices, e-invoices, debit and credit notes, e-way bills,
bills of supply, delivery challans — plus export invoices and quotations on
sibling pages. Inventory management included.

**The notable part for us:** e-invoice and e-way-bill generation is embedded
directly in the SMB invoicing flow, one click from a GST invoice. IRP
connectivity is *not* reserved to the enterprise SKU.

⚠️ Two caveats the marketing obscures. The docs show e-way-bill generation
requires the user to enter **their own NIC/EWB portal credentials** — credential
passthrough, not a transparent GSP pipe. And one homepage line ("One click
e-invoice generation from E-way bill") is backwards versus post-March-2024 GST
sequencing, i.e. the copy is sloppy enough that it is not safe to read
implementation detail out of it.

No pricing published beyond a 30-day trial and "free until notified", so the
free-vs-paid boundary is unknown.

### 1.3 Enterprise — the three "clouds" **[VENDOR-V]**

**Clear Finance Cloud** (AP/AR/treasury), **Clear Compliance Cloud** (GST +
direct tax), **Clear Supply Chain Cloud**.

**These are packaging umbrellas, not exclusive bundles.** The same modules are
also sold standalone, and the boundaries overlap: AP appears under both Finance
and Supply Chain; GST/TDS under both Finance and Compliance. The global site
(`cleartax.com`) uses a different taxonomy again, leading with Compliance Cloud.

> **Practical instruction: benchmark Clear at module level, not cloud level.**
> Any comparison built on the cloud names will double-count.

---

## 2. Enterprise module inventory **[VENDOR-V]**

Verified item-by-item against live pages, 2026-09-22.

| Module | What it does |
|---|---|
| GST return filing | GSTR-1 → 9/9C, plus 4/6/7/8 and ITC-04, as ASP/GSP |
| E-invoicing | IRN generation, bulk from Tally or any ERP |
| E-way bill | Generation and management |
| TDS / direct tax | e-TDS return filing, certificate distribution, 26AS reconciliation, Clause 34/44 exceptions |
| Accounts payable | OCR ingestion, approval workflows, duplicate detection, payment tracking |
| Vendor management | Vendor KYC / GSTIN validation, vendor communication |
| **MaxITC** | 2A/2B reconciliation — see §3 |
| GSTN data pulls | 2 years of invoice history |
| Reporting | Smart reporting + CFO dashboard |
| Billing | Invoice generation |
| CimplyFive **[PRESS]** | Secretarial compliance — Companies Act 2013 / SEBI LODR, product "BLISS". All-cash acquisition 2022 |
| Employee ITR | Bulk consumer filing as an employee benefit |

### 2.1 Three confirmed gaps

Absent from **every** product menu checked:

- **No payroll product.**
- **No notices / litigation / assessment-management module.**
- **No corporate income-tax computation or return filing.** Clear's "direct tax"
  is effectively TDS/TCS plus employee ITR. No transfer pricing either.

### 2.2 And one gap they share with us

**Clear publishes no PO ↔ GRN ↔ invoice matching claim.** Worth stating plainly
because `gap_report.md` ranks the missing GRN entity as a High platform gap:
Clear does not solve it either. Mysa (3-way), CashFlo (6-way) and RazorpayX
(GRN import, `[LIVE]`) do. Clear does not.

---

## 3. MaxITC — the module closest to our mandate **[VENDOR-V]**

This is the one to study, because it targets half of our Core Challenge Prompt.

**What it is:** a separately branded, separately documented, separately sold
module for input-tax-credit maximisation. AI + fuzzy-logic **PAN-level matching**
against GSTR-2A/2B, with **scheduled automatic reconciliation**.

**Evidence it is a real module and not a marketing label:** it has its own
product page, its own API surface (`Trigger Max ITC Workflow`, `Get Max ITC
Results`) on `docs.cleartax.in`, and its own product-help documentation. BW
Disrupt reported a $15M investment specifically to build it **[PRESS]**.

**Do not restate its numbers.** Clear's own properties are mutually inconsistent:
"claim 100% ITC", "save on average 4% GST every time", "grow profits by 7%",
"impact profitability by up to 8%" (from a self-run 200-enterprise survey). No
footnote, no sample, no date, anywhere. Cite as positioning.

**What we should take from it:** Clear treats "what ITC is unclaimed" as
important enough to brand, document and sell *separately*. Our `gap_report.md`
§3.2 item 2 — unified liability + unclaimed ITC in one answer — aims at the same
target and should be scoped with that seriousness, not as a reporting nicety.

---

## 4. The regulatory moat — the strongest finding here

This is the only part of the Clear picture backed by evidence that is not
Clear's own.

### 4.1 Clear operates a private IRP **[GOV]**

`einvoice4.gst.gov.in` states it is **"operated by Clear, a GSTN authorized
IRP"** and publishes GSTN-issued certificates:

| Certificate | Date |
|---|---|
| Sandbox | 26 Sep 2022 |
| Production | 13 Jan 2023 |

Operator named as **Defmacro Software Pvt Ltd**. Portal live and unsuspended as
of Sept 2026.

**Only four private IRPs exist** — IRIS, Cygnet, ClearTax, E&Y — with NIC running
`einvoice1`/`einvoice2`. Six IRPs active in total. Independently corroborated by
a competitor-authored (IRIS) page on another `gst.gov.in` subdomain, 5 Mar 2023.

### 4.2 Clear is separately a GSP **[PRESS]**

One of roughly 62 empanelled GST Suvidha Providers. Corroborated by
contemporaneous trade press on the licence award plus multiple third-party GSP
compilations current to 2025. A targeted search for revocation returned nothing.

⚠️ The official `gstn.org.in` empanelled-GSP list could not be read directly
(returned page chrome only), so this rests on press plus compilations, not on a
primary government list.

### 4.3 What this means for us

`CURRENT_STATUS.md` §2 records AgentSwitch as `einvoicing: false` with nothing
implemented (ticket GST-28). `gap_report.md` §3.1 already ranks that **High**.
This section is the evidence for *why*:

> **IRP/GSP connectivity is the foundation of Clear's entire enterprise business,
> not a feature bullet. And it is a licence, not a feature — we cannot close it.**

The correct response is not to chase it. It is to design the agent to be
**correct without GSTN connectivity** rather than to pretend at it — which is
what `DESIGN.md`'s "escalate rather than assume" posture already implies.

Note for positioning: IRP status differentiates Clear from Zoho, Tally, CashFlo
and RazorpayX. It does **not** differentiate Clear from IRIS or Cygnet.

### 4.4 Security posture is weaker than it looks **[VENDOR-V]**

ISO 27001:2022 and SOC 2 Type II are claimed — but **self-attested** on the
global trust center with **no certificate number and no registrar published**.
The trust center is the `cleartax.com` global property, so certification scope
across Indian vs global entities and products is unverified. No data-residency
commitment was verified anywhere.

A more expansive security claim circulating about Clear was **[REFUTED] 0-3** —
see §7.

---

## 5. Money movement — Clear is an orchestrator, not a rail

The single most-corrected area in verification. Three separate claims asserting
Clear supplies credit itself were refuted. Two distinct mechanisms exist:

### 5.1 Enterprise supply-chain finance / invoice discounting **[VENDOR-V]**

Non-collateralised early payment to suppliers against a discount. Funding is
selectable from **three sources**:

1. **Buyer corporate treasury** — "improve yield on treasury funds, while
   enabling your supply chain with working capital"
2. **TReDS exchanges**
3. **Banks / NBFCs** — including unutilised bank limits

The discount rate is explained as the vendor's cost of early payment scaled by
tenor.

**But Clear is not the lender of record.** Its own invoice-financing FAQ states
the programme "is run by Clear Finance in partnership with our financing
partners, e.g., Bajaj Finance", with limits underwritten by the partner. No RBI
NBFC registration for Defmacro Software surfaced. Clear is **not** one of the
RBI-licensed TReDS operators (RXIL, M1xchange, Invoicemart, C2treds) — the TReDS
route hands off to an external exchange.

Entry into this space was the **2022 Xpedize acquisition** **[PRESS]**.

Scale figures on these pages (50+ enterprises, 36.1K+ vendors, $5.8B+ invoice
value, "$3Bn by FY24") are undated and unaudited, and the FY24 figure is a
**company target, not an outcome**.

### 5.2 SMB collection — ClearOne payment links **[VENDOR-V]**

Payment links generated with or without an invoice, shared via **WhatsApp or
Email**, with payment-status tracking and reminders.

**Collection via UPI and netbanking only — cards are not listed.**

⚠️ Three caveats material to any payments comparison:
- Clear is **not evidenced as an RBI-licensed payment aggregator**, so a
  third-party PA/PG almost certainly sits underneath. Partner undisclosed.
- "Free payment links" means free link *generation*, not zero transaction cost.
  MDR is not disclosed.
- This is **AR collection**, not AP payout. It does not compare to RazorpayX's
  payout rails at all.

### 5.3 What this means for us

`gap_report.md` §3.1 ranks "bulk payout execution tool" as a Medium platform gap.
**Clear is a weak benchmark for it.** RazorpayX, OPEN Money and Kodo/EnKash
operate actual rails; Clear orchestrates financing on top of someone else's.
When arguing that gap, cite them, not Clear.

Clear's genuine differentiator here is the **financing** layer — treasury-funded
early payment is something none of the others in our set offer.

---

## 6. Integrations, pricing and scale

### 6.1 Named ERP connectors **[VENDOR-V]** — the reliable part

SAP (ECC and S/4HANA add-on) · Oracle (Fusion Cloud / EBS / NetSuite) ·
Microsoft Dynamics 365 F&O and Business Central · Tally · Zoho · Busy ·
JD Edwards. Everything else ingests via **public API, SFTP or templates**.

Public developer documentation at `docs.cleartax.in`, with per-module API
surfaces including the MaxITC API. **REST, not MCP** — relevant because
`gap_report.md` lists "documented agent-callable API (MCP)" as our edge, and this
confirms it survives contact with the strongest competitor.

### 6.2 The integration counts are unusable

| Claimed | Where | Status |
|---|---|---|
| "500+ completed ERP integrations" | cleartax.in | **[REFUTED] 1-2** |
| "50+ ERPs, 50-member in-house integrations team" | cleartax.in | **[REFUTED] 0-3** |
| "2,000+ completed ERP integrations" | another Clear property | contradicts the above |
| "3000+ ERP/POS integrations" | cleartax.com/about-us | contradicts both |

Undated, unaudited, mutually contradictory. **Cite the named-connector list and
the ingestion modes; cite nothing numeric.** "Bulk invoicing within ANY ERP" is
universality marketing language, not a verified fact.

### 6.3 Enterprise pricing is entirely undisclosed

No rate card. No per-GSTIN / per-invoice / per-seat model. No bundle-vs-module
licensing structure — so even Clear's own "one platform" framing cannot be
verified as a single bundle. **And no source disclosed how enterprise customers
pay Clear** (invoice with net terms, NEFT/RTGS, card, mandate). That requires a
sales conversation.

The only published pricing is the B2C ladder in §1.1. Third-party review sites
(Techjockey, SoftwareSuggest, Trustpilot) carry recurring complaints about
ClearTax **pricing and renewal pricing**, implying non-trivial, negotiable list
prices.

### 6.4 Scale figures — do not restate as fact

Clear's own properties contradict each other on customer count:

| Figure | Source page |
|---|---|
| 4,000+ clients | India Compliance Cloud |
| 5,000+ enterprise customers | global about page |
| 10,000+ businesses | India site footer |
| 3,000+ enterprise customers | invoice-discounting page |

Different scopes (India product vs global company vs all businesses incl. SMB),
no as-of date on any of them. Also claimed: $500B+ B2B invoices digitised
annually, 5B+ e-invoices/yr, 1.5M+ consumers, 20,000+ CAs and tax experts.

No independent third party publishes an enterprise customer count — searches
surfaced only aggregators (Tracxn, Craft, Owler) and getLatka revenue estimates
in the ~$10.7–19.8M ARR range, itself unverified. An Entrackr report on FY25
revenue and loss surfaced in sourcing but was **not** elevated to a verified
finding; check it independently before use.

**Always write "Clear claims".**

---

## 7. [REFUTED] — do not reuse these

Recorded deliberately. Several appear in Clear's own marketing **and** in the
competitor blog posts (mysa.io, cashflo.io) that fed the v1 gap report research,
so they are likely to be re-imported by anyone repeating this work.

| Claim | Vote |
|---|---|
| "500+ completed ERP integrations" | 1-2 |
| "SAP/Tally + 50+ ERPs, 50-member in-house integrations team" | 0-3 |
| Security posture: SOC 2 + AWS + quarterly VAPT + 128-bit SSL + 2FA + IP whitelisting + 8-yr audit trails + 99.99% uptime | 0-3 |
| E-invoicing scale: 4,000+ businesses / 9,000+ GSTINs / 200M+ IRNs | 0-3 |
| Named enterprise logos (Flipkart, Swiggy, Ola, Blinkit, Udaan, Intel, Apollo, Patanjali, Jindal, SRF, BYJU'S) | 1-2 |
| ITR price points ₹1,299 / ₹2,999 / ₹3,999 | 0-3 |
| "Clear provides credit itself" | 1-2 |
| "Full AR+AP lifecycle, same scope as an AP and tax agent" | 0-3 |
| "Clear packages a separate Finance Cloud… intermediates money movement and credit" | 1-2 |

---

## 8. Consolidated scorecard

Mirroring the format in [`razorpay_gap_report.md`](razorpay_gap_report.md) §6.
Clear's column is `[VENDOR-V]` throughout — weaker than RazorpayX's `LIVE`.

| Capability | Clear | AgentSwitch | Verdict |
|---|---|---|---|
| GST return filing (1/3B/9/9C) | ✅ as ASP/GSP | ❌ read-only; GSTR-9 hard-501s | **Gap — but licence-bound** |
| E-invoicing (IRN/QR/IRP) | ✅ **operates IRP 4** [GOV] | ❌ not implemented (GST-28) | **Gap — structural, cannot be orchestrated around** |
| GSTR-2A/2B fetch + ITC reconciliation | ✅ MaxITC, own API | ⚠️ `ims_status` field only, no GSTN fetch | **Gap** |
| Duplicate invoice/payment detection | ✅ doc number + FY + vendor/buyer GSTIN | ❌ — our Core Challenge Prompt | **Gap — and see §9.1** |
| AP automation (OCR → approval → payment tracking) | ✅ | ❌ no OCR engine | **Gap** |
| Vendor KYC / GSTIN validation | ✅ | ❌ fields stored, never verified | **Gap** |
| TDS return filing + 26AS reconciliation | ✅ | ⚠️ fields + GL posting, no auto-deduction | Partial gap |
| PO ↔ GRN ↔ invoice matching | ❌ not claimed | ❌ no GRN entity | **Neither — market signal** |
| Payroll | ❌ absent | ❌ | **Neither** |
| Notices / litigation management | ❌ absent | ❌ | **Neither** |
| Corporate income tax computation / ITR | ❌ absent | ❌ | **Neither** |
| Supply-chain finance / early payment | ✅ orchestrated (treasury/TReDS/bank) | ❌ | Gap (out of our seat's scope) |
| Payout rails (lender/PA of record) | ❌ **not** lender or PA | ❌ records only | **Neither — cite RazorpayX for this gap, not Clear** |
| Composite/group tax taxonomy | not stated | ✅ one model covers GST + US + 1099 | **Our edge** |
| Dual jurisdiction (India **and** US) | ❌ India-focused | ✅ locale-driven | **Our edge** |
| Native agent/job/escalation framework | ❌ | ✅ full `Agent*` family | **Our edge** |
| Agent-action forensics / replay | ❌ | ✅ job ledger | **Our edge** |
| Documented agent-callable API | ⚠️ REST only (`docs.cleartax.in`) | ✅ MCP, 436 tools | **Our edge** |

**§2 of `gap_report.md` stands unchanged after a closer look at the strongest
competitor. That is the useful result of this exercise.**

---

## 9. What Team 03 should take from this

### 9.1 Fix `invoice_matcher.py` — Clear's key is better than ours

The single actionable finding.

**Clear keys duplicate detection on document number + FY + vendor/buyer GSTIN** —
a *document identity*. Our `scripts/invoice_matcher.py` keys on same-vendor +
identical amount within ±3 days — a *heuristic*.

Run live against the **Keystone (US)** instance on 2026-09-22, ours produced
**three false positives**: seven draft bills from four recurring templates, fired
2026-09-20 and again 2026-09-21, all Apex Metals Supply LLC, flagged purely
because the amounts repeat. `DESIGN.md` §"limitations" predicts exactly this
failure mode for flat recurring charges.

**Recommendation:** adopt a document-identity key (number + FY + party) as the
`exact` tier, and demote amount-proximity to a `suspicious` tier that must
*also* clear a recurring-template check (`recurring_bill_id` is present on
`Bill`). This directly strengthens `gap_report.md` §3.2 item 1, already ranked
first.

> **Provenance note:** that observation is from the Keystone/US instance
> (`class.agentswitch.theschoolofai.in`). `CURRENT_STATUS.md` covers
> Suryodaya/India only and does not describe that instance. The repeated
> same-amount generation across consecutive days is itself an **unfiled bug
> candidate**, pending a check of the templates' declared frequency.

### 9.2 Scope the ITC work like a product, not a report

See §3. Clear brands, documents and sells ITC maximisation separately. Our §3.2
item 2 targets the same thing.

### 9.3 Do not chase the licence

See §4.3. IRP/GSP is regulatory, not functional. Design for correctness without
GSTN connectivity.

### 9.4 Their gaps are our opening

No payroll, no notices/litigation, no corporate ITR — plus, like everyone in this
set, no native agent framework and no dual-jurisdiction support.

### 9.5 Apply the RazorpayX lesson to this document

The RazorpayX analysis found a competitor had **withdrawn** features its own
marketing still advertises. This entire document is built on marketing. **Assume
it has the same blind spot**, and downgrade anything here the moment we get real
access.

---

## 10. Still open on Clear

- Enterprise pricing/packaging model, and how enterprises actually pay Clear.
- The regulated rails behind ClearOne's UPI/netbanking collection and behind
  enterprise vendor payouts — which PA, bank or NBFC, and at what MDR.
- Whether notice management and corporate ITR are roadmap, partnership, or
  deliberately out of scope. Absence from every menu is suggestive, not
  conclusive.
- Real ERP integration depth — certified bidirectional posting with error
  handling, or batch push? Published counts are unreliable, so this needs a
  technical evaluation.
- **Head-to-head positioning against the rest of the set was not established.**
  No market-share, win-rate or analyst data was verified for any competitor. The
  only rigorous competitive datapoint is structural: Clear is one of four private
  IRPs and one of ~62 GSPs.
- Clear's **US/global** capability was not researched. Our Keystone seat runs
  sales & use tax, nexus, exemption certificates and Form 1099 — for which
  **Avalara and Vertex** are the right comparators, not Clear.
