# US-06 — Form 1099 Readiness & Backup Withholding

**US · Proposed owner: Sudip · Verdict: 🟢 Buildable — the platform's 1099 report is the oracle**
**IN counterpart:** UC-09 (TDS — tax on vendor payments) · **live evidence 2026-10-03**

---

## 1. Question

> *"Which vendors will need a 1099 for this year, and do we have what we need to file
> it — or should we be withholding?"*

## 2. Statutory basis

- **Information reporting.** A business must file **Form 1099-NEC** for nonemployee
  compensation (IRC §6041A) and **1099-MISC** for rents and other payments
  (§6041) to non-corporate payees above the threshold. *Our understanding: the
  threshold is **$2,000** for payments after 31 Dec 2025 (OBBBA 2025), indexed after
  2026. The platform's report uses $2,000 for 2026 (US README caveat).*
  Payments to corporations are generally excluded.
- **Backup withholding** (IRC §3406). If a reportable payee has not provided a
  taxpayer identification number (TIN), the payer must withhold **24%** of reportable
  payments and remit it.
- **Consequence:** penalties per missing or incorrect information return (§6721/6722),
  and the payer becomes liable for backup withholding it should have taken.

## 3. Trigger

- **Event:** before paying a vendor flagged `is_1099_vendor` with no TIN (backup
  withholding check).
- **Monthly**, and **in December**, for year-end readiness.
- **Period:** calendar year (`tax_year`).

## 4. Input contract

| Source | Fields |
|---|---|
| **Oracle** `GET /api/cpa/reports/1099-summary?year=2026` | per vendor: `us_tax_classification`, `tin_on_file`, `w9_on_file`, `form_type`, `box`, `backup_withholding`, `total_paid`, `reportable_amount`, `meets_threshold`, `needs_w9`; plus `excluded_corporations`, `missing_w9`, `limitations` |
| `Party.list {"limit":1000}` | `is_1099_vendor`, `us_tax_classification`, `tin_type`, `tin` (redacted), `w9_on_file`, `w9_received_date`, `form_1099_type`, `form_1099_box`, `backup_withholding` |
| `PaymentMade.list {"limit":1000}` | `vendor_id`, `date`, `amount`, `status`, to recompute totals |

## 5. Algorithm

1. **Reportable vendors** = report rows with `meets_threshold: true`. Recompute
   `total_paid` from `PaymentMade` (calendar year, not void) and emit
   `stored_value_mismatch` on disagreement.
2. For each reportable vendor:
   - `needs_w9` or `w9_on_file: false` → **`w9_missing`** (collect before January);
   - `tin_on_file: false` → **`tin_missing`**, and if payments continue →
     **`backup_withholding_required`**, with exposure = 24% of reportable payments
     since the TIN went missing;
   - no `form_1099_box` → `box_unmapped`.
3. **Classification gaps:** vendors paid at least the threshold with
   `us_tax_classification` empty → `classification_missing`. A corporation (including
   an LLC taxed as a C-corp) is correctly excluded.
4. **Approaching:** non-corporate vendors at 80% or more of the threshold → context
   rows, so a W-9 is requested before the threshold is crossed.

### Worked example (REAL — 2026 to date)

| Vendor | Classification | Paid | Box | W-9 | TIN | Finding |
|---|---|---|---|---|---|---|
| Tuscarawas Machining Services LLC | LLC (partnership) | $18,450.00 | NEC-1 | ✓ 2025-01-02 | ✓ | ready |
| **Canton Industrial Consulting** | sole proprietor | $7,800.00 | NEC-1 | **✗** | ✓ | **`w9_missing`** |
| Apex Metals Supply LLC | LLC taxed as C-corp | $204,551.28 | — | — | — | correctly excluded |

> Output: *"2 vendors will receive a 2026 Form 1099-NEC ($26,250.00). Canton Industrial
> Consulting ($7,800.00) has no W-9 on file — request one now. No backup withholding
> is required: both have a TIN on file."*

## 6. Known-bad data

- `Party.tin` reads empty because it is redacted for our role (`_redacted_fields`).
  Use the report's `tin_on_file` and `tin_masked`.
- `not_yet_supported.form_1099_filing` says "No W-9 capture, no TIN matching, no box
  mapping". **Partly out of date:** `Party` has W-9 and box fields and the report reads
  them. TIN matching (IRS TIN-match) and e-file remain absent. Those are
  platform-documented gaps, not bugs.

## 7. Output contract

`finding_type: "form_1099"`, `rule ∈ {w9_missing, tin_missing,
backup_withholding_required, box_unmapped, classification_missing,
stored_value_mismatch}`, `entity_type: "Party"`, `total_exposure` = backup withholding
due (0 for documentation findings), `details: {tax_year, reportable_amount, box,
form_type}`.

## 8. Limits

- Does not withhold, file or e-file. It reports and escalates.
- Does not validate TINs against the IRS (platform-documented gap).

## 9. Validation

1. Oracle: the report's `reportable_count` (2) and `total_reportable` must equal the
   recompute from `PaymentMade`.
2. Fixture: a sole proprietor paid $2,500 with no TIN → `backup_withholding_required`,
   $600.00 (24%).
3. Boundary: $1,999.99 → context only; $2,000.00 → reportable.

## 10. Open questions

- Confirm the 2026 threshold and the indexing for 2027 before the December run.
- State 1099 filing (e.g. Ohio's combined federal/state programme): in scope?

## 11. Live evidence — actual calls, 2026-10-03

- `GET /api/cpa/reports/1099-summary?year=2026` → `general_threshold: 2000.0`,
  `thresholds_by_box: {"MISC-1": 2000.0, "NEC-1": 2000.0}`, 2 vendors:
  Tuscarawas `fa216869-f6c7-446a-8c79-f9c2c3b61194` (`meets_threshold: true`,
  `needs_w9: false`), Canton Industrial Consulting `607bdecf-e87d-4dfe-9c91-f2e3a12e1b0a`
  (`w9_on_file: false`, `needs_w9: true`, `total_paid: 7800.0`).
- `Party.list` → 4 parties `is_1099_vendor: true`; 3 with `w9_on_file`; 0 with
  `backup_withholding`.
- `PaymentMade.list` → 8 vendors paid in 2026, classified: 3 sole proprietors,
  2 C-corps, 1 S-corp, 1 LLC/C-corp, 1 LLC/partnership.
