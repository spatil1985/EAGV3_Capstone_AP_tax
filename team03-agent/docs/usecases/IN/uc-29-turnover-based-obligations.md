# UC-29 — Turnover-Based Obligations (Aggregate Turnover Thresholds)

**Domains: all five (decisive for small school, clinic, retail and agency tenants) · Category: compliance calendar · Verdict: 🟢 Buildable — live finding (e-invoicing obligation not met)**
**Status: draft · live evidence 2026-10-04 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

Many GST and income-tax obligations switch on at a turnover line, so this use case decides **which other
use cases apply** to a tenant. It feeds [UC-13](uc-13-194q-206c-thresholds.md),
[UC-17](uc-17-composition-scheme.md), [UC-26](uc-26-gstr1-readiness.md),
[UC-27](uc-27-return-filing-timeliness.md) and [UC-31](uc-31-annual-return-reconciliation.md).

---

## 1. Question

> *"Given our turnover, which GST obligations apply to us this year, and are we meeting them?"*

---

## 2. Statutory basis

**Aggregate annual turnover (AATO)** is the value of all supplies made under one PAN across India, in the
previous FY:
- **included:** taxable, exempt, export and inter-state supplies;
- **excluded:** the taxes themselves, and inward supplies taxed under reverse charge.

It is measured at PAN level (s.2(6)).

| Obligation | Line | Basis |
|---|---|---|
| Registration | Aggregate turnover above ₹40 lakh (goods) / ₹20 lakh (services), lower in special-category states. A person making **only exempt supplies need not register** | s.22, s.23(1)(a), Notif. 10/2019-CT |
| Composition eligibility | ≤ ₹1.5 crore | s.10 ([UC-17](uc-17-composition-scheme.md)) |
| Quarterly filing (QRMP) | ≤ ₹5 crore | Rule 61A |
| **E-invoicing (IRN)** | AATO **above ₹5 crore** in any FY from 2017-18. An invoice without an IRN is **not a valid tax invoice** (Rule 48(5)), so the buyer's credit is at risk | Rule 48(4), Notif. 13/2020-CT as amended by 10/2023-CT (from 1 August 2023) |
| IRN reporting window | *Our understanding (caveat):* AATO ≥ ₹10 crore must report to the IRP within 30 days of the invoice date, from 1 April 2025 | GSTN advisory |
| HSN digits on invoices | ≤ ₹5 crore: 4 digits (B2B); above ₹5 crore: **6 digits** | Notif. 78/2020-CT |
| Annual return GSTR-9 | Optional at ≤ ₹2 crore (notified each year); mandatory above | s.44, Rule 80 |
| Reconciliation GSTR-9C | Self-certified, AATO above ₹5 crore | Rule 80(3) |
| Income tax: s.194Q buyer | Buyer's **total turnover above ₹10 crore** in the preceding FY. Only then does UC-13's ₹50 lakh per-vendor test apply | s.194Q |

---

## 3. Trigger

- **Scheduled on 1 April each year.** The new FY's obligations are fixed by the previous FY's turnover.
- **Scheduled monthly**, to project the current FY's run-rate toward next year's lines.
- **On request**, and once on tenant onboarding, where it sets the playbook routing.

---

## 4. Input contract

| Tool | Fields |
|---|---|
| `Invoice.list {"limit":1000}` | `direction=receivable`, `status`, `date`, `taxable_value`, `gst_treatment` |
| `CreditNote.list` | Reductions in turnover |
| `OrgProfile.list` | `gstin`, `pan`, `industry`, `enable_e_invoicing`, `msme_type` |
| `EInvoicingPreferences.list` | `enabled`, `auto_generate_irn`, `sandbox_mode` |
| `Location.list` | Other GSTINs under the same PAN, which are aggregated ([UC-30](uc-30-multiple-registrations.md)) |
| `GET /api/accounting/locale` | `features.einvoicing`, `not_yet_supported.einvoicing` (GST-28), `gst_filing_frequency` |

---

## 5. Algorithm

1. **Turnover per FY:** live receivable `taxable_value` (exempt and zero-rated included, taxes excluded),
   minus credit notes, summed across every GSTIN under the PAN. If the ledger doesn't cover the whole FY,
   the figure is a **floor** and says so.
2. **Obligation matrix:** compare the previous FY's turnover with each line in §2 and emit one row per
   obligation: `applies` / `does_not_apply` / `undeterminable`.
3. **Compliance checks** for each obligation that applies:
   - **e-invoicing:** `EInvoicingPreferences.enabled = 1` and invoices carry an IRN. Otherwise
     `einvoice_required_not_generated` for each B2B, SEZ or export invoice in the current FY.
   - **HSN:** digit count on live outward lines ≥ 6 (or ≥ 4).
   - **Filing cadence:** quarterly filing at AATO above ₹5 crore → `qrmp_ineligible`.
   - **GSTR-9C:** due for the previous FY → pass to UC-31.
4. **Run-rate projection:** current-FY turnover so far ÷ months elapsed × 12. If a line will be crossed next
   year, emit `threshold_will_cross` with the month expected.
5. **Exempt-only rule:** for school and clinic tenants with only exempt supplies, registration is optional.
   The first taxable stream (uniforms, coaching, pharmacy) puts the full aggregate, exempt included,
   against the ₹20 lakh / ₹40 lakh line.

### Worked example (REAL, 2026-10-04)

> **FY 2025-26 turnover:** live receivable taxable value **₹6,70,65,518.43**, from invoices dated
> 2025-09-19 onward. The ledger covers only part of the year, so this is a floor. **AATO > ₹5 crore** →
> e-invoicing, 6-digit HSN and GSTR-9C apply; QRMP does not.
>
> **E-invoicing:**
> - `OrgProfile.enable_e_invoicing = 1`, but `EInvoicingPreferences.enabled = 0` (sandbox mode);
> - the locale lists e-invoicing as `not_yet_supported` (GST-28);
> - no IRN field exists on `Invoice`;
> - FY 2026-27 B2B and SEZ invoices: **108, ₹7,55,23,313.00**.
>
> **Others:**
> - HSN: all live outward lines carry 8 digits ✓.
> - Filing: monthly ✓.
> - s.194Q gate: FY 2025-26 turnover is at least ₹6.71 crore. That is *undeterminable* against the
>   ₹10 crore line until the full-year figure is known, so UC-13 must not assume 194Q applies.
>
> Output: *"FY 2025-26 turnover is at least ₹6.71 crore, so e-invoicing is mandatory. 108 B2B invoices this
> year (₹7.55 crore) carry no IRN and are not valid tax invoices for your buyers' credit. AgentSwitch
> cannot generate IRNs today (GST-28)."*

---

## 6. Known-bad data

- **E-invoicing settings contradict each other:** `OrgProfile.enable_e_invoicing = 1` vs
  `EInvoicingPreferences.enabled = 0`. Report as `data_quality`. The platform's own `not_yet_supported`
  entry means the missing IRN is **a documented gap, not a bug to file**. The compliance exposure is real
  all the same.
- Turnover from invoices only. Supplies recorded elsewhere (stock transfers, [UC-30](uc-30-multiple-registrations.md))
  are missing, which is another reason to call the figure a floor.

---

## 7. Output contract

`finding_type: "turnover_obligation"`, `rule ∈ {obligation_applies, einvoice_required_not_generated,
hsn_digits_short, qrmp_ineligible, threshold_will_cross, registration_required, data_quality}`. The
obligation matrix is a context table; each failed check is a finding, with `total_exposure` = tax on the
affected invoices.

---

## 8. Limits

- Never enables e-invoicing or generates an IRN. The platform can't (GST-28).
- Turnover is the GST measure. Income-tax "turnover" for s.194Q may differ (e.g. sales vs gross receipts),
  and the row says so.
- PAN-level aggregation needs every GSTIN's data. The platform has a single company ledger
  (consolidation is not supported).

---

## 9. Validation

1. **Live:** recompute FY totals from `Invoice.list`; check the 108-invoice count by month (April 23,
   May 26, June 26, July 27, August 6).
2. **Line fixtures:** ₹5,00,00,000 → e-invoicing does not apply; ₹5,00,00,001 → applies.
3. **Exempt-only fixture:** a school with ₹30 lakh exempt and ₹0 taxable → registration optional; add
   ₹1 of taxable → required.

---

## 10. Open questions

- What is Suryodaya's real full-year FY 2025-26 turnover? The ledger starts in September 2025. Ask the
  instructors, or treat the floor as decisive since it already exceeds ₹5 crore.
- Should e-invoice exposure be escalated per invoice, or once as a digest (G8)? Recommend a digest.

---

## 11. Live evidence — actual calls, 2026-10-04

- `OrgProfile.list` → `497428a7-29f6-4fcd-8e65-412f02a09ede`:
  - `industry: manufacturing`, `gstin 27AASCS7781M1ZQ`, `pan AASCS7781M`;
  - `enable_e_invoicing: 1`, `enable_tds: 1`, `tan: null`, `msme_type: small`.
- `EInvoicingPreferences.list` → `enabled: 0`, `auto_generate_irn: 0`, `sandbox_mode: 1`.
- `Invoice.list {"limit":1000}` → live receivable taxable by FY:
  - FY 2025-26: ₹6,70,65,518.43 (first invoice 2025-09-19);
  - FY 2026-27 to date: ₹6,44,70,617.02.
  Outward HSN digit counts on live lines: 8 digits on all.
