# Use-case specs — index and shared rules

**Team 03 · Seat 03 Payables & Tax · live evidence pulled 2026-09-28**

One file per use case from [`../spec.md`](../spec.md), written to the ten-section
template in [`../assignment.md`](../assignment.md) §3, with [`uc-01`](uc-01-rule-37-itc-reversal.md)
as the reference. Each file adds **§11 Live evidence**: the actual MCP/REST calls made
against the live instance, trimmed real responses, and what they prove.

**Live snapshot used throughout:** Suryodaya Precision Works Pvt. Ltd.
(`5cbe5a55-af74-4363-a436-f5350593114c`), India, signed in as `team03@theschoolofai.in`
(`finance_user`), 2026-09-28. Record counts at pull time: 227 Bill · 485 Invoice (320
receivable) · 195 Party · 134 PaymentMade · 215 PaymentReceived · 172 ApprovalRequest ·
331 ApprovalLog · 25 CreditNote · 103 Item · 100 EWayBill · 100 DeliveryChallan · 100
RetainerInvoice · 100 RecurringBill · 232 PurchaseOrder · 8 TaxExemption. MCP exposes
**494 tools** to this account.

**Every call in these specs is reproducible from Postman:**
[`../../postman/AgentSwitch-UseCases.postman_collection.json`](../../postman/AgentSwitch-UseCases.postman_collection.json),
one folder per use case. Setup is in [`../../postman/README.md`](../../postman/README.md).

---

## Index

Verdict column: `spec.md`'s original verdict → the verdict the live data supports. A
changed verdict is explained in that file's §11.

| UC | Title | Owner | Verdict | Headline from live data |
|---|---|---|---|---|
| [01](uc-01-rule-37-itc-reversal.md) | Rule 37 — 180-day ITC reversal | Sudip | 🟢 → 🟢 *(no case until 5 Dec 2026)* | Ledger starts 2026-06-07; oldest bill is 113 days. First crossing is BILL-2026-00001 on **2026-12-05**, and it carries **₹0** item-level ITC |
| [02](uc-02-blocked-credit-audit.md) | Blocked credit s.17(5) | Geetha | 🟢 → 🟢 | 0 of 250 bill lines in a blocked HSN/SAC; 54 lines (22%) have no HSN at all, so they cannot be classified |
| [03](uc-03-rcm-self-invoicing.md) | RCM self-invoicing | Sudip | 🟢 → 🟢 | **Real case:** 5 GTA bills (SAC 996511) from Chakan Transport Lines, RCM flag off, **₹8,260** RCM at 5% undeclared |
| [04](uc-04-msme-45-day-exposure.md) | MSME 45-day | Sudip | 🟢 → 🟢 | **7 real breaches**, worst 68 days over (₹5,85,162). `msme_no` blank on all 8 MSME parties |
| [05](uc-05-duplicate-vendor-payment.md) | Duplicate vendor payment | Sudip | 🟡 → 🟡 | Amount heuristic: 218 pairs, 208 suppressed by the `recurring_bill_id` gate, **10 remain**. Exact tier usable on only **18/227** bills |
| [06](uc-06-approval-sla-audit.md) | Approval SLA & SoD audit | Sudip | 🟢 → 🟢 | N8 records were re-stamped since filing; now 5/19 resolved wrong, 3/55 open wrong. `ApprovalPolicy` still **403** |
| [07](uc-07-school-exempt-taxable-split.md) | School exempt/taxable split | Geetha | 🟡 → 🟡 | **Tax-exempt items are being charged GST** (INV-2026-00254). 15 items with goods HSN typed `services` |
| [08](uc-08-rule-42-apportionment-school.md) | Rule 42 apportionment — school | Geetha | 🔴 → 🔴 *(compute 🟢)* | Real Sep-2026 ratio **27.41%**, C2 ₹55,491.28 → D1 **₹15,207.64**. Zero-tax ≠ exempt: 438/592 lines are zero-tax |
| [09](uc-09-vendor-tds-verification.md) | Vendor TDS verification | Sudip | 🟢 → 🟢 | **N7 has grown 9 → 101 bills.** 101/101 stored `tds_amount` wrong; ₹52.57 lakh of phantom TDS; negative payables on all 101 |
| [10](uc-10-job-work-itc04.md) | Job work / ITC-04 | Sandip | 🔴 → 🟡 | **`challan_type=job_work` exists** (19 challans). spec.md and F19 say it doesn't. Return tracking is what's missing |
| [11](uc-11-three-way-match.md) | Three-way match | Sandip | 🔴 → 🟡 | **A receipt leg exists.** `bill_match` on all 101 PO bills: 9 exceed tolerance, **8 billed with 0 received**. `recorded_status` null ×101 |
| [12](uc-12-eway-bill-coverage.md) | E-way bill coverage | Sandip | 🟢 → 🟢 | **80/80 "active/generated" e-way bills have no EWB number.** 67 past expiry. 226/280 goods invoices >₹50k unlinked |
| [13](uc-13-194q-206c-thresholds.md) | 194Q / 206C(1H) | Sudip | 🟡 → 🟡 | No vendor past ₹50 lakh (top ₹35.2 lakh). Receive side: ₹7.08 Cr from Bharat EV, **0 TDS deducted**. 206C(1H) likely omitted |
| [14](uc-14-clinic-exempt-taxable-split.md) | Clinic exempt/taxable split | Geetha | 🟡 → 🟡 | No clinic tenant. Engine shared with UC-07; room-rent rule is playbook-only |
| [15](uc-15-rule-42-43-apportionment-clinic.md) | Rule 42/43 — clinic | Geetha | 🔴 → 🔴 *(compute 🟢)* | Same engine as UC-08; adds Rule 43 capital-goods leg (9 `capital_goods` bills exist) |
| [16](uc-16-drug-expiry-blocked-credit.md) | Expiry → blocked credit | Geetha | 🟢 → 🟡 | 29 shelf-life items, **only 8 batch-tracked**; no `Batch`/`StockEntry` list tool over MCP |
| [17](uc-17-composition-scheme.md) | Composition scheme | Sandip | 🔴 → 🔴 | `Company` has no tax-mode field. Buildable sub-check: **4 "composition" vendor bills carry ₹8,079.46 GST** marked ITC-eligible |
| [18](uc-18-hsn-rate-consistency.md) | HSN rate consistency | Sandip | 🟢 → 🟢 | 5 HSNs charged at 2–5 different rates; HSN 73269099 at 0/5/9/12/18%. Tax oracle has **no HSN input** |
| [19](uc-19-credit-note-time-limit.md) | Credit-note s.34(2) limit | Sandip | 🟢 → 🟢 | 25/25 CNs within window. **125 FY25-26 invoices; window closes 2026-11-30 (63 days).** 12 CNs link to payable invoices |
| [20](uc-20-export-lut-tracking.md) | Export / LUT | Sandip | 🟡 → 🟡 | 15 zero-tax SEZ invoices. An LUT row exists in `TaxExemption` but has **no validity dates and no party link** |
| [21](uc-21-import-of-services-rcm.md) | Import of services RCM | Sudip | 🟢 → 🟡 | 12 bills tagged `overseas`, **all INR from Indian vendors**. No genuine overseas vendor in the data |
| [22](uc-22-advance-receipt-gst.md) | Advance-receipt GST | Sandip | 🟡 → 🟡 | `RetainerInvoice` has **no tax fields**. Real case: RET-2026-00002, ₹6,00,000 advance held, unapplied |

---

## Shared rules — every spec applies these

Rules 1–5 are carried from [`../assignment.md`](../assignment.md) §8. **Rule 0 is new,
forced by the 2026-09-28 data, and overrides the old wording of Rule 1.**

### Rule 0 — item-level tax is *not* automatically trustworthy (new)

The team rule has been "compute tax from `items[].cgst/sgst/igst/cess_amount`, never
document-level `taxes[]`." The live data no longer supports the first half:

| Entity | Lines with tax | CGST **and** IGST on same line | CGST ≠ SGST | ≠ rate × taxable | **Internally consistent** |
|---|---|---|---|---|---|
| Invoice | 153 | 93 | 127 | 106 | **6 (4%)** |
| Bill | 96 | 29 | 33 | 21 | **59 (61%)** |

Example — INV-2026-00254 line 1: `tax_percentage 5`, taxable ₹2,93,549.28, CGST
₹26,419.44 + SGST ₹14,677.46 + IGST ₹26,419.44. Intra- and inter-state tax together,
unequal halves, and 23% effective on a 5% line.

**So every spec gates each line before using it:**

```
line_is_valid(l) :=
    not ((l.cgst_amount > 0 or l.sgst_amount > 0) and l.igst_amount > 0)   # one supply type only
    and abs(l.cgst_amount - l.sgst_amount) <= 0.05                         # halves agree
    and (l.tax_percentage in (null, 0)
         or abs(l.cgst_amount + l.sgst_amount + l.igst_amount
                - l.taxable_amount * l.tax_percentage / 100) <= 1.00)      # arithmetic holds
```

A valid line's item-level amounts are used as-is. An invalid line is **not silently
recomputed**. It is emitted as a `data_quality` finding alongside the use case's own
findings, and excluded from monetary totals, with the exclusion stated in the summary.
Where a recomputed figure is needed, the oracle is `POST /api/accounting/tax/compute`
(verified correct: `{"amount":100000,"rate":18}` → `total_tax 18000.0`).

### Rules 1–5 (unchanged in substance)

1. **Never use document-level `taxes[]`, the `Tax`/`TaxJurisdiction` master or
   `group_taxes`** (`CURRENT_STATUS.md` §7a; N127/N128). Subject to Rule 0, use
   item-level.
2. **Treat these stored values as suspect and recompute:** `tds_amount` (N7 — now 101
   bills), `CreditNote.taxes[]` (N128), `is_overdue` on resolved requests (N1/N8),
   `Bill.match_status` (N2 — null on 101/101).
3. **Nothing posts to the ledger.** `JournalEntry` is read-only for `finance_user`.
   Output is a report row or an `AgentEscalation`.
4. **Cite where you confirmed each field.** In these specs, every field was read from a
   live record or from the tool's `inputSchema` in `tools/list` on 2026-09-28.
5. **Tax positions are engineering specifications, not tax advice.** See the statutory
   caveats below.

### Rule 6 — MCP list filters are flat, single-valued and strictly typed (new)

Found by live calls. UC-01 to UC-04 were drafted with `Bill.list(filters={...})`, and
**that syntax does not exist.** `Bill.list`'s `inputSchema` exposes each field as a
top-level argument:

| What the drafts wrote | What the server accepts | Server response to the draft form |
|---|---|---|
| `filters={"itc_eligibility": ["input","input_services"]}` | `{"itc_eligibility": "input"}` — **one** enum value per call | `-32602 "/itc_eligibility must be string"` |
| `filters={"is_reverse_charge": 1}` | `{"is_reverse_charge": true}` — **boolean**, although records return `0`/`1` | `-32602 "/is_reverse_charge must be boolean"` |
| `filters={"vendor_id": [...ids...]}` | `{"vendor_id": "<one id>"}` | (same class of error) |

`limit` max is **1000**, default 20. There are no range operators (`date >= x`,
`balance_due > 0`), so those filters are always client-side. At current volumes
(≤485 rows per entity) a single `limit: 1000` call returns everything; specs page anyway
and stop when a page returns fewer than `limit` rows.

### Statutory caveats that apply across specs

These are flagged for confirmation, not asserted. Each affected spec repeats the one it
relies on in its §10.

- **Income-tax renumbering.** The specs cite the Income-tax Act 1961 section numbers
  used throughout `spec.md` (43B(h), 194C/194I/194J, 194Q, 206C(1H)). Our understanding
  is that the **Income-tax Act 2025 applies from 1 April 2026** and renumbers these.
  Obligations are unchanged in substance, but citations must be confirmed before any
  output is shown to a user. Affects UC-04, UC-09, UC-13.
- **GST rate structure.** Our understanding is that GST rates were rationalised to
  **5% / 18% / 40%** from 22 September 2025, removing the 12% and 28% slabs for most
  goods. `spec.md` UC-18 still lists 0/5/12/18/28. Affects UC-03 (GTA forward-charge
  rate), UC-18.
- **s.206C(1H) TCS.** Our understanding is that it was **omitted from 1 April 2025**
  (Finance Act 2025). `spec.md` UC-13 treats it as live. Affects UC-13.
- **s.129 e-way bill penalty.** Our understanding is that it has been **200% of tax
  payable** since 1 January 2022, not "tax + 100%" as `spec.md` UC-12 says. Affects
  UC-12.

---

## Shared contracts

As [`../assignment.md`](../assignment.md) §7. The **reversal row schema** is defined in
[UC-01 §7](uc-01-rule-37-itc-reversal.md), and UC-08, UC-15 and UC-16 emit it unchanged.

Two more row types appear, both first defined in these specs:

| `finding_type` | Defined in | Used by |
|---|---|---|
| `itc_reversal` | UC-01 §7 | UC-08, UC-15, UC-16, UC-17 |
| `data_quality` | this README, Rule 0 | every spec |
| `rcm_undeclared_liability` | UC-03 §7 | UC-21, UC-22 |

`data_quality` row, fixed fields:

```json
{
  "finding_type": "data_quality",
  "rule": "item_tax_line_invalid | stored_value_mismatch | classification_conflict | missing_required_field",
  "entity_type": "Invoice",
  "entity_id": "289df9d7-d856-499e-b751-91db971fcdd4",
  "entity_ref": "INV-2026-00254",
  "field": "items[0].igst_amount",
  "observed": "cgst 26419.44 + sgst 14677.46 + igst 26419.44 on one line",
  "expected": "either cgst=sgst with igst=0, or igst only; sum = 5% of 293549.28 = 14677.46",
  "blocks": "UC-07 exempt-split; UC-08 turnover",
  "status": "finding",
  "summary": "INV-2026-00254 line 1 carries intra- and inter-state tax together; excluded from totals."
}
```

---

## What the live data changed about `spec.md` and our filings

These are corrections, not new ideas. Most need action outside this folder.

| # | `spec.md` / filing says | Live data shows | Suggested action |
|---|---|---|---|
| 1 | UC-10 / **F19**: `DeliveryChallan` has no job-work subtype | `challan_type=job_work` on 19 challans | Rewrite F19 as "no return tracking", not "no subtype" |
| 2 | UC-11 / **F1 (GAP-4)**: no GRN, three-way match structurally blocked | `bill_match` computes `received_qty` from receipts; 8 bills billed with 0 received | Downgrade F1's claim; three-way is 🟡 |
| 3 | Rule 1: item-level tax is the trustworthy source | 4% of invoice lines internally consistent | Rule 0 above. **Candidate new bug report** |
| 4 | **N7**: TDS corrupt on 9 bills | 101 bills, every recurring-template bill | Update N7 on the board; it is growing daily |
| 5 | **N8**: 14/19 false negatives | Same record ids now carry different `sla_deadline`s; 5/19 wrong, mostly false positives | Tell triage the data changed under the report |
| 6 | **F6** second half: no `Approval*` MCP tools | `ApprovalRequest.list/get`, `ApprovalLog.list/get` now in `tools/list` | Mark F6 fully delivered — except `ApprovalPolicy` (403) |
| 7 | UC-12: 80 e-way bills "active/generated" | None has an `eway_bill_number` | **Candidate new bug report** |
