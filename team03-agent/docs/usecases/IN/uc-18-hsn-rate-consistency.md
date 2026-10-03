# UC-18 — HSN-Wise Rate-Slab Correctness

**Workstream C · Verdict: 🟢 Buildable as a consistency check**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

---

## 1. Question

> *"Are we charging the right GST rate on every product we sell?"*

(Verbatim from `spec.md` UC-18.)

---

## 2. Statutory basis

- **Rate notifications under s.9(1) CGST / s.5(1) IGST** fix the rate per HSN.
- ⚠️ **Rate structure.** `spec.md` lists slabs 0/5/12/18/28. **Our understanding is
  that GST was rationalised to 5% / 18% (plus 40% for demerit goods) from 22 September
  2025, removing the 12% and 28% slabs for most goods** (README caveat). If so, every
  12% line dated after 22 Sep 2025 is presumptively wrong. **Confirm against the current
  rate schedule before encoding it.**
- **Under-charging** → the shortfall is recoverable from the *seller*, not the buyer,
  with s.50 interest.
- **Over-charging** → s.171 anti-profiteering exposure (**our understanding is that
  new applications under s.171 are not accepted from 1 April 2025 — confirm**). Tax
  collected in excess must be paid to the government regardless (s.76).

---

## 3. Trigger

- **On item-master change:** a changed `intra_state_tax_rate`/`inter_state_tax_rate`
  or HSN.
- **Monthly before GSTR-1:** consistency sweep over the month's outward lines.
- **Period:** month; FY for the "same HSN, different rate" comparison.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Invoice.list` | `{"direction": "receivable", "limit": 1000}` | Outward lines |
| `Item.list` | `{"limit": 1000}` | Master rate per item |
| `POST /api/accounting/tax/compute` | `{"amount": x, "rate": r}` | Arithmetic oracle. **Takes no HSN.** Response: `rate_source: "manual"`, `rate_source_authoritative: false` |

**Line fields:** `hsn_or_sac`, `tax_percentage`, `taxable_amount`, `cgst_amount`,
`sgst_amount`, `igst_amount`, `item_id`.

---

## 5. Algorithm

1. **Rule 0** (README) on every line. Invalid lines are excluded from rate analysis and
   reported as `data_quality`.
2. **Effective rate** per valid line = `(cgst + sgst + igst) ÷ taxable × 100`, rounded
   to 0.01. Use the effective rate, not `tax_percentage`, because the two disagree on
   live data (§6).
3. **Consistency (the core check):** group valid lines by `hsn_or_sac`. Any HSN with
   more than one effective rate → `hsn_rate_inconsistent`, listing each rate and its
   invoices. This needs no rate table.
4. **Master drift:** line effective rate ≠ the item's master rate → `rate_drift_from_master`.
5. **Slab validity:** effective rate not in the current slab set (per the confirmed
   schedule: {0, 5, 18, 40} + cess, or the older set) → `rate_not_a_slab`.
6. **Authoritative check (only when a table exists):** HSN → rate from a
   playbook-carried table. Mismatch → `rate_wrong_for_hsn`.

### Worked example (REAL — HSN 73269099)

> HSN **73269099** (other articles of iron or steel) appears on **20** receivable lines
> at **five** different `tax_percentage` values:
>
> | `tax_percentage` | Lines | Example invoice |
> |---|---|---|
> | 0% | 2 | INV-2026-00221 |
> | 5% | 1 | INV-2026-00192 |
> | 9% | 7 | INV-2026-00253 |
> | 12% | 5 | INV-2026-00244 |
> | 18% | 5 | INV-2026-00233 |
>
> ```
> step 3 → hsn_rate_inconsistent (5 distinct rates for one HSN)
> step 5 → 9% is not a slab (probably a CGST half of 18% stored as the full rate)
>          12% is not a slab post-22-Sep-2025 (if the rationalisation is confirmed)
> ```
>
> Output: *"HSN 73269099 is charged at five different rates across 20 invoice lines
> (0/5/9/12/18%). At most one is correct. Fix the item master."*

---

## 6. Known-bad data

- **`tax_percentage` does not equal the effective rate** on many lines. INV-2026-00254
  line 2 has `tax_percentage 12` and effective 30%. Analyse effective rates from valid
  lines only.
- **Rule 0 excludes most lines:** only 6 of 153 taxed invoice lines are internally
  consistent. On live data, step 3 mostly runs on `tax_percentage` rather than effective
  rate, and the output must say which basis it used.
- **"9%" is likely a CGST-only half** stored as the line rate, which is itself a
  data-quality finding.
- **Item master rates are empty** (`intra_state_tax_rate`/`inter_state_tax_rate` blank
  on sampled items), so step 4 has nothing to compare against.

---

## 7. Output contract

`finding_type: "rate_check"`, `rule ∈ {hsn_rate_inconsistent, rate_drift_from_master,
rate_not_a_slab, rate_wrong_for_hsn}`, with `hsn`, `rates_seen` (map rate → line
count → example invoice), `basis: "effective | tax_percentage"`, `status`, `summary`.

---

## 8. Limits

- **No authoritative HSN → rate source exists on the platform.** The tax oracle takes
  a rate, not an HSN, and self-reports as non-authoritative. Step 6 depends on a
  playbook table the team would maintain.
- Never edits rates. Not tax advice.

---

## 9. Validation

1. **Live counts must reproduce:** 15 HSNs on receivable lines; **5** with more than one
   rate (§11).
2. **Oracle for arithmetic:** `tax/compute {"amount":100000,"rate":18}` →
   `total_tax 18000.0` (verified live).
3. **Fixture:** one HSN at 18% on three invoices and 12% on one → one
   `hsn_rate_inconsistent` row naming the odd invoice.

---

## 10. Open questions

- **Confirm the post-22-Sep-2025 slab set** before `rate_not_a_slab` ships. Getting
  this wrong would flag every line in the ledger.
- **Who maintains the HSN → rate table?** It changes with every Council meeting. It is
  a playbook file with an owner and a "last verified" date, or it is not built.
- **Is "9%" really a CGST half?** One `Invoice.get` on a 9% line with a Rule 0-valid
  split would settle it.

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-18 HSN rate consistency`.

**Call 1 — `Invoice.list {"direction":"receivable","limit":1000}`** → 15 distinct HSNs
on receivable lines; **5 carry more than one `tax_percentage`**:

| HSN | Lines | Rates seen (count) |
|---|---|---|
| 82055900 | 25 | 0% ×19 · 9% ×3 · 12% ×2 · 18% ×1 |
| **73269099** | 20 | 0% ×2 · 5% ×1 · 9% ×7 · 12% ×5 · 18% ×5 |
| 84669390 | 19 | 0% ×12 · 9% ×2 · 12% ×5 |
| 82041100 | 4 | 0% ×2 · 5% ×1 · 12% ×1 |
| 84831099 | 2 | 0% ×1 · 9% ×1 |

**Call 2 — `POST /api/accounting/tax/compute {"amount":100000,"rate":18}`**
```json
{"tax_regime":"gst","taxable_amount":100000.0,"total_tax":18000.0,"grand_total":118000.0,
 "rate_source":"manual","rate_source_status":"manual","rate_source_authoritative":false,
 "taxes":[{"tax_type":"IGST","rate":18.0,"amount":18000.0,"is_exempt":false}],
 "supply_type":"inter_state","place_of_supply":""}
```
**What it proves:** the oracle is right on arithmetic, but it takes the rate on trust.
`rate_source_authoritative: false` is the platform itself saying it has no rate table.
