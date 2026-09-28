# UC-07 — School: Exempt vs Taxable Revenue Split

**Workstream B · Owner: Geetha · Verdict: 🟡 Partial (fields exist; no school tenant)**
**Status: draft · live evidence 2026-09-28 · reference template: [UC-01](uc-01-rule-37-itc-reversal.md)**

> **Write this first in WS-B.** UC-08 cannot be specified until this spec defines how
> exempt turnover is derived, and UC-14 reuses its classification engine.

---

## 1. Question

> *"Which of our income streams are actually taxable, and are we treating them
> correctly?"*

(Verbatim from `spec.md` UC-07.)

---

## 2. Statutory basis

- **Notification 12/2017-Central Tax (Rate), entry 66** — services by an educational
  institution to its students, faculty and staff are **exempt**. Entry 66(b) also
  exempts certain services *to* an institution (transport of students, catering,
  security, housekeeping) up to higher secondary level.
- **Books** — printed books (HSN 4901) are **nil-rated** under the goods rate
  notification. **Stationery, uniforms** and similar goods are taxable at their HSN rate.
- **Coaching / private tuition** outside a recognised curriculum is **not** an
  "educational institution" service and is taxable (SAC 9992).
- **Why it matters:** the split feeds three things. (a) The s.22 registration threshold
  counts *aggregate* turnover, including exempt supplies. (b) Rule 42's E/F ratio
  (UC-08). (c) GSTR-1/3B exempt-supply reporting.
- **Consequence if wrong:** GST not charged on a taxable stream is recoverable from the
  school with interest (s.50) and penalty (s.73/74). GST charged on an exempt stream is
  collected without authority and must be deposited anyway (s.76).

---

## 3. Trigger

- **Monthly**, before the GSTR-1/3B cut-off: classify that month's outward invoices.
- **On document event:** a new `Item` created with `product_type`/`tax_preference`
  that contradicts its HSN/SAC (§5 step 2). Catching misclassification at master level
  prevents every future invoice from inheriting it.
- **Period:** calendar month (return period). The FY aggregate feeds UC-08's annual
  true-up.

---

## 4. Input contract

| Tool | Arguments | Notes |
|---|---|---|
| `Item.list` | `{"limit": 1000}` | 103 live. The classification master |
| `Invoice.list` | `{"direction": "receivable", "limit": 1000}` | 320 receivable live. `direction` is a valid flat filter |
| `TaxExemption.list` | `{"limit": 100}` | 8 live. Exemption reasons exist but carry no notification reference |

**`Item` fields** (confirmed live): `id`, `name`, `hsn_or_sac`, `product_type`
(`goods|services`), `tax_preference` (`taxable|tax_exempt`), `taxable` (0/1),
`tax_exemption_reason`, `intra_state_tax_rate`, `inter_state_tax_rate`.

**`Invoice.items[]` fields:** `item_id`, `hsn_or_sac`, `tax_percentage`,
`taxable_amount`, `cgst_amount`, `sgst_amount`, `igst_amount`, `cess_amount`,
`_item_id_display`.

---

## 5. Algorithm

**Stage 1 — master-level consistency (per `Item`)**
1. Derive the expected supply type from the code: `hsn_or_sac` starting `99` → services
   (SAC); anything else non-empty → goods (HSN).
2. Flag `classification_conflict` where:
   - HSN (goods chapter) but `product_type = services`, or SAC but `product_type = goods`;
   - `tax_preference = tax_exempt` but `taxable = 1`, or `taxable` but `taxable = 0`;
   - `tax_preference = tax_exempt` with empty `tax_exemption_reason`.
3. For a school tenant, map each item to a revenue stream (tuition, transport, hostel,
   books, stationery, uniforms, coaching, hall hire) with a playbook table keyed on
   SAC/HSN. Compare that stream's statutory treatment against `tax_preference`.

**Stage 2 — transaction-level (per receivable invoice line)**
4. Join each line to its `Item` by `item_id`. The line's **classification is the
   item's `tax_preference`**, *not* whether tax was charged (see §6).
5. Apply Rule 0 (README) to the line's tax fields.
6. Flag:
   - `exempt_but_taxed`: item is `tax_exempt` and the line carries tax > 0;
   - `taxable_but_untaxed`: item is `taxable`, the line has tax = 0, and the
     customer's `gst_treatment` is not `sez`/`overseas`/`deemed_export` (those are
     zero-rated, not exempt).
7. Aggregate `taxable_amount` by (month, classification) → **E (exempt)**, **T
   (taxable)**, **F = E + T**. This is the handoff to UC-08.

### Worked example (real data, 2026-09-28 — a manufacturing tenant, used because no school exists)

> **INV-2026-00254** (`289df9d7-d856-499e-b751-91db971fcdd4`), 2026-09-22, customer
> Shubhangi Joshi, `draft`.
> Line 1: item *Pipe Wrench 138mm (Pair)* (`28dafc21-9c58-464e-869a-a88fe9fa4d30`).
> Item master: `tax_preference = tax_exempt`, `product_type = services`, HSN `82055900`.
>
> ```
> Stage 1: HSN 8205 is a goods chapter, product_type = services      → classification_conflict
>          tax_exempt with empty tax_exemption_reason                 → classification_conflict
> Stage 2: item tax_exempt; line tax = 26419.44 + 14677.46 + 26419.44 = 67516.34 > 0
>                                                                     → exempt_but_taxed
>          Rule 0: CGST and IGST on the same line, CGST ≠ SGST         → data_quality (line invalid)
> ```
>
> Output: *"INV-2026-00254 line 1 — Pipe Wrench is marked tax-exempt but was charged
> ₹67,516.34 GST; the tax fields are also internally inconsistent. Fix the item master
> before this invoice is issued."*

---

## 6. Known-bad data

- **"Zero tax" does not mean "exempt" on this instance.** 438 of 592 receivable lines
  carry zero tax with `taxable_amount > 0`. Every invoice before 2026-09 is zero-tax,
  across items of both preferences. A split derived from tax charged would call eleven
  months of normal manufacturing sales "exempt". **Classification comes from
  `Item.tax_preference` only.**
- **The item master is itself unreliable** (§11): 15 goods-HSN items are typed
  `services`, 12 items are `tax_exempt` with `taxable=1`, and 0 of 15 exempt items state
  a reason. For a real school tenant, Stage 1 must be clean before Stage 2 results mean
  anything.
- **Rule 0** — only 6 of 153 taxed invoice lines are arithmetically consistent.

---

## 7. Output contract

Per-line `finding_type: "supply_classification"`, `rule ∈ {exempt_but_taxed,
taxable_but_untaxed, classification_conflict}`, with fields `entity_type`,
`entity_id`, `entity_ref`, `item_id`, `item_name`, `tax_preference`,
`tax_charged`, `status`, `summary` (same shape conventions as UC-01 §7).

Plus one **period aggregate** per month, which UC-08 consumes:

```json
{
  "finding_type": "turnover_split",
  "period": "2026-09",
  "exempt_turnover_E": 23296704.45,
  "taxable_turnover_T": 61710848.59,
  "total_turnover_F": 85007553.04,
  "lines_classified": 592,
  "lines_unclassifiable": 1,
  "basis": "Item.tax_preference",
  "currency": "INR"
}
```

---

## 8. Limits

- Never edits `Item` master data. It flags; a human fixes.
- Does not decide statutory classification for a novel stream. The playbook table maps
  known streams, and anything unmapped is `classification_conflict: unmapped` for a CA
  to rule on.
- Not tax advice (README statutory caveats).

---

## 9. Validation

1. **Positive control:** INV-2026-00254 must produce `exempt_but_taxed` and a Rule 0
   `data_quality` row.
2. **Aggregate reconciliation:** E + T for 2026-09 must equal the sum of
   `taxable_amount` on all September receivable lines: ₹8,50,07,553.04 live.
3. **Oracle for "should this line carry tax":** `POST /api/accounting/tax/compute`
   with `{"amount": taxable_amount, "rate": tax_percentage}`. The oracle returns
   `taxes: []` for rate 0 (verified during B4).
4. **School validation is not possible on live data.** Seed a sandbox school (F2) or
   hand-construct a 10-invoice fixture covering all eight streams.

---

## 10. Open questions

- **Student transport:** `spec.md` says "third-party bus service is not" exempt. Entry
  66(b)(i) exempts transport services *provided to* a school (up to higher secondary).
  The contractor's supply to the school is exempt; what is taxable is less clear. Needs
  a CA ruling before the playbook table is written.
- **Composite vs mixed supply:** is a school's "annual fee" covering tuition + uniform +
  books one composite supply (principal supply = exempt education) or a mixed supply
  (highest rate applies)? This changes the split materially.
- **Where the classification should live:** item master only, or per-invoice-line
  override? The platform has no line-level override, so a single item cannot be exempt
  to students and taxable to outsiders (hall hire).

---

## 11. Live evidence — actual calls, 2026-09-28

**Postman folder:** `UC-07 School exempt-taxable split`.

**Call 1 — `Item.list {"limit":1000}`** → 103 items.

| Measure | Live value |
|---|---|
| `tax_preference`: taxable / tax_exempt / blank | 81 / **15** / 7 |
| `product_type`: goods / services / blank | 79 / 22 / 2 |
| Items with `tax_exemption_reason` populated | **0** |
| Goods-chapter HSN typed `services` | **15** |
| `tax_exempt` but `taxable = 1` | **12** |
| `taxable` but `taxable = 0` | 6 |

**Call 2 — `Invoice.list {"direction":"receivable","limit":1000}`** → 320 invoices,
592 lines, dated 2025-09-19 … 2026-09-24.

| Classified by `Item.tax_preference` | Lines | `taxable_amount` |
|---|---|---|
| tax_exempt | 49 | ₹2,32,96,704.45 |
| taxable | 542 | ₹19,32,20,044.89 |
| unlinked | 1 | ₹1,000.00 |

Zero-tax lines: **438 / 592**. Every month before 2026-09 is 100% zero-tax. That is why
"tax = 0" cannot be the exempt test.

**Call 3 — `Invoice.get {"id":"289df9d7-d856-499e-b751-91db971fcdd4"}`** (INV-2026-00254)
```json
{"number":"INV-2026-00254","date":"2026-09-22","status":"draft","grand_total":1452906.3,
 "items":[{"item_id":"28dafc21-9c58-464e-869a-a88fe9fa4d30","tax_percentage":5,
           "taxable_amount":293549.28,"cgst_amount":26419.44,"sgst_amount":14677.46,"igst_amount":26419.44},
          {"item_id":"eef9fead-4587-4fa3-8524-5f7f7a664740","tax_percentage":12,
           "taxable_amount":799231.84,"cgst_amount":143861.73,"sgst_amount":95907.82,"igst_amount":0}]}
```
**What it proves:** a `tax_exempt` item is being charged GST, and the tax lines are
internally impossible. Both checks this spec defines fire on a real document.

**Call 4 — `TaxExemption.list`** → 8 rows (e.g. *"Job-work movement — not a supply"*,
*"Export under LUT"*, *"Scrap sold to an unregistered buyer"*). None cites a
notification entry. None is education- or health-related.
