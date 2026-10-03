# UC-17 — Composition Scheme Eligibility and Breach

**Workstream C · Verdict: 🔴 Blocked (confirmed live) — with a 🟢 buildable sub-check found in the data**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**
**Backs:** F20 / GAP-3

---

## 1. Question

> *"Are we still eligible for the composition scheme, and are we about to fall out of
> it?"*

(Verbatim from `spec.md` UC-17.)

---

## 2. Statutory basis

- **Section 10, CGST Act — composition levy.** Aggregate turnover in the preceding FY
  up to **₹1.5 crore** (₹75 lakh in special-category states). Tax at **1%** (0.5% CGST
  + 0.5% SGST) for manufacturers and traders, 5% for restaurants. Services under
  **s.10(2A)**: 6% up to ₹50 lakh.
- **Disqualifying activities (s.10(2)):** inter-state outward supply; supply of
  non-taxable goods; supply through an e-commerce operator required to collect TCS
  (partly relaxed for intra-state goods from 1 October 2023 — **confirm current
  position**); manufacturing notified goods (ice cream, pan masala, tobacco).
- **s.10(4)** — a composition dealer **cannot collect tax** from the recipient **and
  cannot claim ITC**. Its invoice is a *bill of supply*.
- **Consequence of breach:** the taxpayer becomes a regular taxpayer from the day the
  condition fails. Tax at full rates plus interest is recoverable on everything since,
  and penalty under s.10(5) applies if they were never eligible.
- **The recipient's side (the buildable sub-check):** GST shown on a bill from a
  composition supplier is not tax the recipient can credit. Composition tax is paid by
  the supplier on its own turnover, not charged on. **ITC claimed on such a bill is
  wrong.**

---

## 3. Trigger

- **Main check (org as composition dealer):** monthly turnover run-rate against ₹1.5
  crore, and every outward invoice for a disqualifying attribute. **Blocked**, see §4.
- **Sub-check (counterparty as composition dealer):** document event on every bill
  whose `gst_treatment = business_composition`.

---

## 4. Input contract

**Main check — what would be needed, and what exists:**

| Need | Live status |
|---|---|
| The organisation's own tax mode (regular / composition) | ❌ **`Company` has no such field.** Live `Company` fields: `id`, `name`, `country`, `default_currency`, `fiscal_year_start`, `active_domains`, `party_id`, `agent_daily_llm_budget_usd`, erasure fields. No GSTIN, no registration type, no tax mode |
| Locale-level regime | `GET /api/accounting/locale` → `tax_regime: "gst"` only. No composition variant |
| Preceding-FY aggregate turnover | derivable from `Invoice.list`, but the ledger starts 2025-09-19 (receivable) |
| Inter-state outward flag | `Invoice.place_of_supply` vs own state — derivable |

**Sub-check — all present:**

| Tool | Arguments |
|---|---|
| `Bill.list` | `{"gst_treatment": "business_composition", "limit": 1000}` |
| `Party.get` | `{"id": vendor_id}` — does the Party agree the vendor is composition? |

---

## 5. Algorithm

**Main check (specified for when GAP-3 is closed)**
1. If `org.tax_mode = composition`: FY-to-date Σ receivable `taxable_amount`, projected
   to year-end at the current run-rate. `composition_threshold_approaching` at 80% of
   the limit, `composition_breached` above it.
2. Any outward invoice with `place_of_supply ≠ own state` → `composition_disqualified`
   (inter-state supply) from that invoice's date.
3. Any outward invoice carrying GST (tax > 0) → `composition_collecting_tax` (s.10(4)).

**Sub-check (buildable now)**
4. For each bill with `gst_treatment = business_composition`:
   - item-level tax > 0 → **`composition_vendor_charged_gst`**: the vendor cannot
     charge it, and we cannot credit it.
   - `itc_eligibility ≠ ineligible` → **`itc_on_composition_bill`**: emit a UC-01 §7
     reversal row, `rule: "s10_4_composition"`, base = the bill's item-level tax.
   - `Party.gst_treatment ≠ business_composition` → `classification_conflict`: the
     bill and the party disagree.

### Worked example (REAL — BILL-2026-00019)

> **BILL-2026-00019** (`be59dc55-57bd-4145-9f3c-42f8ee66bc8e`), vendor **Bosch Rexroth
> India**, `gst_treatment: business_composition`, `itc_eligibility: input`,
> `is_reverse_charge: 0`, item-level tax **₹4,419.37**, `grand_total ₹24,702.78`.
>
> ```
> tax > 0 on a composition bill        → composition_vendor_charged_gst
> itc_eligibility = input              → itc_on_composition_bill → reverse ₹4,419.37
> Party(Bosch Rexroth India).gst_treatment = business_gst (not composition)
>                                      → classification_conflict — which is right?
> ```
>
> Output: *"BILL-2026-00019 (Bosch Rexroth India) is tagged as from a composition
> dealer yet charges ₹4,419.37 GST, marked ITC-eligible. Either the tag is wrong (Bosch
> Rexroth is not plausibly a composition dealer) or the credit must be reversed. Fix
> the bill's treatment."*

---

## 6. Known-bad data

- **The four `business_composition` bills are all from large companies** (Bosch Rexroth
  India, Bharat EV Motors, Tata Ficosa, Shreeji Powder Coating), and **no `Party` has
  `gst_treatment = business_composition`** (0 of 195). The tag is almost certainly wrong
  on the bills. The sub-check therefore mostly produces `classification_conflict`,
  which is the correct, honest output.
- **Two of the four also have `is_reverse_charge = 1`.** RCM on a bill from a
  composition supplier makes no sense for goods. A third conflict for UC-03.
- **`Party.gst_treatment` is blank on 139 of 195 parties.** The party side of the
  cross-check is usually silent.

---

## 7. Output contract

`finding_type: "composition"`, `rule ∈ {composition_vendor_charged_gst,
itc_on_composition_bill, classification_conflict, composition_threshold_approaching,
composition_breached, composition_disqualified, composition_collecting_tax}`. The ITC
rule additionally emits a UC-01 §7 reversal row.

---

## 8. Limits

- **Main check cannot run.** The organisation's tax mode is not representable (GAP-3 /
  F20), so the agent cannot know whether the question even applies.
- Never re-tags a bill. It reports the conflict.

---

## 9. Validation

1. **Sub-check live positive controls:** all 4 `business_composition` bills (§11) must
   produce findings; total GST ₹13,500.98 by `total_tax` (₹8,079.46 item-level — see
   §11 correction).
2. **Main check:** fixture only. Composition org at ₹1.2 Cr run-rate →
   `approaching`; one inter-state invoice → `disqualified` from its date.

---

## 10. Open questions

- **F20 evidence:** the live `Company` field list is the cleanest possible proof for
  F20. Quote it in the triage response.
- **E-commerce relaxation** for composition dealers (intra-state goods through an ECO
  from Oct 2023) — confirm scope before encoding it as a disqualifier.
- **Are the 4 mis-tagged bills a seeder artefact** (N127 class) or user error? Either
  way, they are worth one line in the next bug batch.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-17 Composition scheme`.

**Call 1 — `Company.list {"limit":5}`**
```json
{"data":[{"id":"5cbe5a55-af74-4363-a436-f5350593114c","name":"Suryodaya Precision Works Pvt. Ltd.",
  "country":"India","default_currency":"INR","fiscal_year_start":"2026-04-01",
  "active_domains":[{"domain":"core"},{"domain":"accounting"}, "…"],
  "party_id":null,"agent_daily_llm_budget_usd":8.0}]}
```
No tax-mode, GSTIN or registration-type field exists. **GAP-3 confirmed.**

**Call 2 — `GET /api/accounting/locale`** → `"tax_regime":"gst"`,
`"gst_filing_frequency":"monthly"`. No composition variant.

**Call 3 — `Bill.list {"gst_treatment":"business_composition","limit":1000}`** → 4 bills:

| Bill | Vendor | Item-level GST | **`total_tax`** *(30 Sep)* | `itc_eligibility` | RCM |
|---|---|---|---|---|---|
| BILL-2026-00019 `be59dc55…` | Bosch Rexroth India | ₹4,419.37 | ₹7,828.60 | input | 0 |
| BILL-2026-00077 `2be5ebc8…` | Bharat EV Motors Ltd | ₹2,069.90 | ₹2,587.37 | input_services | 0 |
| BILL-2026-00072 `89be310f…` | Shreeji Powder Coating | ₹1,434.70 | ₹2,608.54 | input | **1** |
| BILL-2026-00022 `2cfe5989…` | Tata Ficosa Automotive Systems | ₹155.49 | ₹476.47 | capital_goods | **1** |
| **Total** | | ₹8,079.46 | **₹13,500.98** | all ITC-eligible | |

> **Correction 2026-09-30.** The GST these bills carry is their `total_tax`,
> ₹13,500.98. The item-level column understates it. None of the three sources agrees
> on three of the four bills. BILL-2026-00019: lines ₹4,419.37, `taxes[]` ₹3,885.93
> (one blank-typed row plus IGST and CESS of equal amount), `total_tax` ₹7,828.60.
> Report `total_tax` as the exposure and emit a `data_quality` row for the
> disagreement. This inconsistency is evidence for N128 (see
> `../../submissions/bugs_to_file_2026-09-30.md`).

**Call 4 — `Party.list {"limit":1000}`** → `gst_treatment`: blank 139 · consumer 40 ·
business_gst 15 · sez 1 · **business_composition 0**.

**What the live data changed:** the main use case stays 🔴, now proven by the live
`Company` schema rather than asserted. The data also surfaced a buildable recipient-side
check that `spec.md` did not have.
