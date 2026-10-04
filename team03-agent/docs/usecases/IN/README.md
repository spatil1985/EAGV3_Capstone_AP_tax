# Use-case specs — index and shared rules

**Team 03 · Seat 03 Payables & Tax · live evidence pulled 2026-09-28**

One file per use case from [`../spec.md`](../../planning/spec.md), written to the ten-section
template in [`../assignment.md`](../../planning/assignment.md) §3, with [`uc-01`](uc-01-rule-37-itc-reversal.md)
as the reference. Each file adds **§11 Live evidence**: the actual MCP/REST calls made
against the live instance, trimmed real responses, and what they prove.

**Live snapshot used throughout:** Suryodaya Precision Works Pvt. Ltd.
(`5cbe5a55-af74-4363-a436-f5350593114c`), India, signed in as `team03@theschoolofai.in`
(`finance_user`), 2026-09-28. Record counts at pull time: 227 Bill · 485 Invoice (320
receivable) · 195 Party · 134 PaymentMade · 215 PaymentReceived · 172 ApprovalRequest ·
331 ApprovalLog · 25 CreditNote · 103 Item · 100 EWayBill · 100 DeliveryChallan · 100
RetainerInvoice · 100 RecurringBill · 232 PurchaseOrder · 8 TaxExemption. MCP exposes
**494 tools** to this account.

**Reproducing the calls.** Each spec's §11 gives the exact MCP/REST call and its
arguments. The per-use-case Postman collection was planned but not built. Use the
generic collection's `tools/call` request in
[`postman/`](../../../postman/README.md), with the tool name and arguments from §11.

---

## Index

Verdict column: `spec.md`'s original verdict → the verdict the live data supports. A
changed verdict is explained in that file's §11.

| UC | Title | Verdict | Headline from live data |
|---|---|---|---|
| [01](uc-01-rule-37-itc-reversal.md) | Rule 37 — 180-day ITC reversal | 🟢 → 🟢 *(no case until 5 Dec 2026)* | Ledger starts 2026-06-07; oldest bill is 113 days. First crossing is BILL-2026-00001 on **2026-12-05**, carrying **₹1,02,672** ITC in `taxes[]` *(corrected 30 Sep — was "₹0")* |
| [02](uc-02-blocked-credit-audit.md) | Blocked credit s.17(5) | 🟢 → 🟢 | 0 of 250 bill lines in a blocked HSN/SAC; 54 lines (22%) have no HSN at all, so they cannot be classified |
| [03](uc-03-rcm-self-invoicing.md) | RCM self-invoicing | 🟢 → 🟢 | 5 GTA bills (SAC 996511) from Chakan Transport Lines, RCM flag off — but the GTA **charges 18% forward-charge GST** (₹29,736 in `taxes[]`), so **no undeclared RCM** *(corrected 30 Sep — was "₹8,260 undeclared")*. No live positive control |
| [04](uc-04-msme-45-day-exposure.md) | MSME 45-day | 🟢 → 🟢 | **7 real breaches**, worst 68 days over (₹5,85,162). `msme_no` blank on all 8 MSME parties |
| [05](uc-05-duplicate-vendor-payment.md) | Duplicate vendor payment | 🟡 → 🟡 | Amount heuristic: 218 pairs, 208 suppressed by the `recurring_bill_id` gate, **10 remain**. Exact tier usable on only **18/227** bills |
| [06](uc-06-approval-sla-audit.md) | Approval SLA & SoD audit | 🟢 → 🟢 | N8 records were re-stamped since filing; now 5/19 resolved wrong, 3/55 open wrong. `ApprovalPolicy` still **403** |
| [07](uc-07-school-exempt-taxable-split.md) | School exempt/taxable split | 🟡 → 🟡 | **Tax-exempt items are being charged GST** (INV-2026-00254). 15 items with goods HSN typed `services` |
| [08](uc-08-rule-42-apportionment-school.md) | Rule 42 apportionment — school | 🔴 → 🔴 *(compute 🟢)* | Real Sep-2026 ratio **27.41%**, C2 ₹14,80,485.54 → D1 **₹4,05,733.76** *(corrected 30 Sep — was ₹55,491.28 → ₹15,207.64)*. Exempt comes from `Item.tax_preference`, not zero-tax lines |
| [09](uc-09-vendor-tds-verification.md) | Vendor TDS verification | 🟢 → 🟢 | **N7 has grown 9 → 101 bills.** 101/101 stored `tds_amount` wrong; ₹52.57 lakh of phantom TDS; negative payables on all 101 |
| [10](uc-10-job-work-itc04.md) | Job work / ITC-04 | 🔴 → 🟡 | **`challan_type=job_work` exists** (19 challans). spec.md and F19 say it doesn't. Return tracking is what's missing |
| [11](uc-11-three-way-match.md) | Three-way match | 🔴 → 🟡 | **A receipt leg exists.** `bill_match` on all 101 PO bills: 9 exceed tolerance, **8 billed with 0 received**. `recorded_status` null ×101 |
| [12](uc-12-eway-bill-coverage.md) | E-way bill coverage | 🟢 → 🟢 | **80/80 "active/generated" e-way bills have no EWB number.** 67 past expiry. 226/280 goods invoices >₹50k unlinked |
| [13](uc-13-194q-206c-thresholds.md) | 194Q / 206C(1H) | 🟡 → 🟡 | No vendor past ₹50 lakh (top ₹35.2 lakh). Receive side: ₹7.08 Cr from Bharat EV, **0 TDS deducted**. 206C(1H) likely omitted |
| [14](uc-14-clinic-exempt-taxable-split.md) | Clinic exempt/taxable split | 🟡 → 🟡 | No clinic tenant. Engine shared with UC-07; room-rent rule is playbook-only |
| [15](uc-15-rule-42-43-apportionment-clinic.md) | Rule 42/43 — clinic | 🔴 → 🔴 *(compute 🟢)* | Same engine as UC-08; adds Rule 43 capital-goods leg (9 `capital_goods` bills exist) |
| [16](uc-16-drug-expiry-blocked-credit.md) | Expiry → blocked credit | 🟢 → 🟡 | 29 shelf-life items, **only 8 batch-tracked**; no `Batch`/`StockEntry` list tool over MCP |
| [17](uc-17-composition-scheme.md) | Composition scheme | 🔴 → 🔴 | `Company` has no tax-mode field. Buildable sub-check: **4 "composition" vendor bills carry ₹13,500.98 GST** marked ITC-eligible *(corrected 30 Sep — was ₹8,079.46)* |
| [18](uc-18-hsn-rate-consistency.md) | HSN rate consistency | 🟢 → 🟢 | 5 HSNs charged at 2–5 different rates; HSN 73269099 at 0/5/9/12/18%. Tax oracle has **no HSN input** |
| [19](uc-19-credit-note-time-limit.md) | Credit-note s.34(2) limit | 🟢 → 🟢 | 25/25 CNs within window. **125 FY25-26 invoices; window closes 2026-11-30 (63 days).** 12 CNs link to payable invoices |
| [20](uc-20-export-lut-tracking.md) | Export / LUT | 🟡 → 🟡 | 15 zero-tax SEZ invoices. An LUT row exists in `TaxExemption` but has **no validity dates and no party link** |
| [21](uc-21-import-of-services-rcm.md) | Import of services RCM | 🟢 → 🟡 | 12 bills tagged `overseas`, **all INR from Indian vendors**. No genuine overseas vendor in the data |
| [22](uc-22-advance-receipt-gst.md) | Advance-receipt GST | 🟡 → 🟡 | `RetainerInvoice` has **no tax fields**. Real case: RET-2026-00002, ₹6,00,000 advance held, unapplied |

### Added 2026-10-04: UC-23 … UC-44, from the full catalogue

These come from the catalogue in [`../README.md`](../README.md), and have no `spec.md` entry. They use the
same eleven sections, with live evidence pulled on **2026-10-04**. Record counts on that date:
- 281 Bill · 487 Invoice · 230 Party · 134 PaymentMade · 100 VendorCredit · 120 Expense;
- 62 BankTransaction · 9 TransactionLock · 26 AccountingPeriod · 6 Location · 5 GSTReturn.

| UC | Title | Verdict | Headline from live data |
|---|---|---|---|
| [23](uc-23-period-gst-liability.md) | Period GST liability and credit utilisation (GSTR-3B) | 🟡 | August cash payable **₹5,72,073.68**. July triggers Rule 86B. Return rows don't reconcile (July filed ₹2.49 Cr vs ledger ₹1.35 Cr) |
| [24](uc-24-unclaimed-itc-ims-2b.md) | Unclaimed and at-risk credit (IMS / GSTR-2B / s.16(4)) | 🟡 | **10 IMS-rejected bills still credit-eligible (₹41,226.79)**. ₹18.70 lakh pending IMS action. No GSTR-2B line data |
| [25](uc-25-vendor-credit-debit-notes-itc.md) | Inward credit and debit notes: credit adjustment | 🟢 | ₹63,956.20 of credit to reduce for 20 supplier credit notes. 21 credits carry GST from suppliers who can't charge it |
| [26](uc-26-gstr1-readiness.md) | GSTR-1 readiness: classification and tax head | 🟡 | **12 inter-state invoices charged CGST+SGST instead of IGST (₹45,152.62)**. Split: 208 B2B, 27 B2CS, 15 SEZ |
| [27](uc-27-return-filing-timeliness.md) | Return filing timeliness, late fee and interest | 🟢 | **August GSTR-1 23 days late, GSTR-3B 14 days**: ₹1,850 late fee + ₹3,949.66 interest so far. E-way bills blocked if September GSTR-3B is missed |
| [28](uc-28-late-entered-documents.md) | Documents entered late into filed or locked periods | 🟢 | 0 breaches. But July was filed 8 Aug and locked only 12 Sep, a 35-day unprotected window |
| [29](uc-29-turnover-based-obligations.md) | Turnover-based obligations (AATO) | 🟢 | Turnover of at least ₹6.71 Cr → **e-invoicing mandatory. 108 B2B/SEZ invoices (₹7.55 Cr) carry no IRN** (GST-28) |
| [30](uc-30-multiple-registrations.md) | Multiple registrations: transfers and ISD | 🟡 | **No location GSTIN belongs to the company's PAN.** Transfer and ISD checks are blocked |
| [31](uc-31-annual-return-reconciliation.md) | Annual return reconciliation (GSTR-9/9C) | 🔴 (compute 🟡) | FY 2025-26 due 31 Dec 2026. FY credit is absent from the ledger. The March `total_income` looks cumulative |
| [32](uc-32-itc-refund-zero-rated-inverted.md) | Refund of accumulated credit (Rule 89(4)/(5)) | 🟡 | SEZ supplies under LUT → **indicative refund ₹37,758.92**. No inverted duty |
| [33](uc-33-expense-claims-itc.md) | Expense claims: GST credit eligibility | 🟢 | **18 personal expenses claim ₹7.74 lakh of credit.** 56 expenses carry tax above 40% of the amount |
| [34](uc-34-school-exempt-inward-services.md) | School: GST on exempt inward services (entry 66(b)) | ⚪ spec | No education tenant |
| [35](uc-35-agency-pure-agent-reimbursements.md) | Agency: recharges and the pure-agent test (Rule 33) | 🟡 | 15 invoiced billable expenses; **0 invoices carry `expense_id`** |
| [36](uc-36-ecommerce-tcs-s52.md) | Retail: e-commerce TCS (s.52) and s.9(5) | 🔴 F22 | No sales channel or TCS-credit record |
| [37](uc-37-non-resident-payments-tds-195.md) | Non-resident payments: s.195 TDS, 15CA/CB | 🟡 | 38 "overseas" documents are all INR from Indian vendors |
| [38](uc-38-cash-payment-limits.md) | Cash payments: s.40A(3) | 🟢 | **13 cash payments above ₹10,000 (₹7,02,867.40).** 4 open bills set to cash |
| [39](uc-39-tds-deductor-setup.md) | TDS deductor setup and section coverage | 🟢 | **TDS on, TAN null.** 0 of 9 valid section codes. ₹2.60 lakh MSME interest without 194A |
| [40](uc-40-vendor-master-audit.md) | Vendor master data audit | 🟢 | **0 of 88 vendors have a GSTIN, PAN or bank details.** 76 aren't typed as vendors |
| [41](uc-41-unapplied-vendor-credits.md) | Unapplied vendor credits before payment | 🟢 | **₹4,91,099.27 applicable now** across 7 vendors |
| [42](uc-42-payment-run-prioritisation.md) | Payment run prioritisation | 🟢 | 100 open bills (₹1.41 Cr); 52 overdue; 55 MSME bills (₹84.0 lakh) |
| [43](uc-43-bank-to-payables-reconciliation.md) | Bank-to-payables reconciliation | 🟢 | **₹56.21 lakh of vendor debits have no AP payment**; 77 AP payments aren't in the bank |
| [44](uc-44-approval-threshold-splitting.md) | Approval threshold splitting | 🟡 | 2 candidate groups at an assumed ₹1 lakh threshold. `ApprovalPolicy` 403 |

### New observations from the 2026-10-04 pull: candidates for the bug board

None of these is filed. Each is verified in the named spec's §11, and none is on the platform's
`not_yet_supported` list.

| # | Observation | Spec |
|---|---|---|
| 1 | `GSTReturn` figures don't reconcile to the ledger (August GSTR-1: ₹2.63 Cr / 161 vs ₹46.4 lakh / 14 invoices); `net_tax_payable` null on all | UC-23, UC-26 |
| 2 | `VendorCredit.taxes[].tax_type` holds product names: N128's pattern on a third entity | UC-25 |
| 3 | 14 bank debits `matched` with no voucher type or id (on Keystone the same field is populated) | UC-43 |
| 4 | Location GSTINs carry PANs other than the company's; the primary location GSTIN ≠ `OrgProfile.gstin` | UC-30 |
| 5 | 100 `TaxNexus` and 100 `ExemptionCertificate` rows (US constructs) on the India tenant, the class of N126 | UC-36 |
| 6 | `OrgProfile.enable_e_invoicing = 1` vs `EInvoicingPreferences.enabled = 0` | UC-29 |
| 7 | `tds_section_code` seeded strings on every TDS-bearing bill; the rates (12/15/5%) match no section | UC-39 |
| 8 | March 2026 `AccountingPeriod.total_income` equals the full-year invoice turnover | UC-31 |
| 9 | `Invoice.expense_id` never set, although 15 expenses are `invoiced` | UC-35 |
| 10 | 56 of 120 expenses carry tax above 40% of the amount | UC-33 |
| 11 | 12 inter-state invoices taxed as intra-state | UC-26 |

E-invoicing (GST-28), GSTR-9 (GST-39), amendments (GST-32) and TDS challans (GST-18) are
platform-documented gaps. They are **not** to be filed.

---

## Shared rules — every spec applies these

Rules 1–5 are carried from [`../assignment.md`](../../planning/assignment.md) §8. **Rule 0 is new,
forced by the 2026-09-28 data, and overrides the old wording of Rule 1.**

> **Correction 2026-09-30 — pick the tax source per document, not per rule.** The
> 2026-09-28 rules below assumed item-level tax is the only candidate source. It
> is not. On **Bill and Invoice**, document-level `taxes[]` carries a clean
> CGST/SGST/IGST split that **reconciles to `total_tax` on 401/401 manually created
> invoices and 63/64 bills whose lines carry no tax**. On those documents item-level
> tax is simply empty, so an item-only rule reads their ITC and output tax as ₹0.
> N128's `taxes[]` corruption is on **CreditNote**; it does not generalise.
>
> ```
> tax_source(doc) :=
>     "taxes[]"   if abs(Σ taxes[].amount − doc.total_tax) <= 1 and every taxes[].tax_type is non-blank
>     "items[]"   elif abs(Σ item tax − doc.total_tax) <= 1 and every taxed line passes line_is_valid
>     "none"      otherwise → data_quality row; exclude from totals
> ```
>
> Recurring-generated invoices (69) are the reverse case: `items[]` sums to
> `total_tax`, but the lines are impossible and `taxes[]` has blank types. They fall to
> "none" (see [`../bugs_to_file_2026-09-30.md`](../../submissions/bugs_to_file_2026-09-30.md) N10).
> Rule 1 below is superseded for Bill and Invoice, and still holds for CreditNote.
> Figures corrected under this rule are marked *Correction 2026-09-30* in UC-01, UC-03,
> UC-04, UC-08 and UC-17.

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

As [`../assignment.md`](../../planning/assignment.md) §7. The **reversal row schema** is defined in
[UC-01 §7](uc-01-rule-37-itc-reversal.md), and UC-08, UC-15 and UC-16 emit it unchanged.

Two more row types appear, both first defined in these specs:

| `finding_type` | Defined in | Used by |
|---|---|---|
| `itc_reversal` | UC-01 §7 | UC-08, UC-15, UC-16, UC-17 |
| `data_quality` | this README, Rule 0 | every spec |
| `rcm_undeclared_liability` | UC-03 §7 | UC-21, UC-22 |

**UC-23 … UC-44** each define one `finding_type`, named in that spec's §7. Where credit is reversed or
reduced, they reuse the UC-01 reversal fields (`reversal_base_amount`, `interest_amount`,
`total_exposure`): UC-24, UC-25, UC-33. Every one emits `data_quality` rows for records it can't trust.

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
