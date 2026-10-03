# Bugs to file — 2026-09-30

**Source:** a sweep of the 22 use-case specs in [`usecases/IN/`](usecases/IN/) against
[`agentswitch_submissions.md`](agentswitch_submissions.md), with every candidate
re-verified on live Suryodaya data on 2026-09-30.
**Duplicate check:** against `GET /api/bug-report/mine` — **27 reports** on the
India account on 2026-09-30. Each candidate below states which filed report it is
closest to and why it is not a duplicate.

> **We cannot see other teams' filings.** The class board is not machine-readable.
> A defect below may already be reported by Team 01 or 02. Skim the board for
> "RecurringInvoice", "credit note" and "tax_id" before filing.

---

## Summary

| | # | Title | Severity | Closest filed | Confidence it is new |
|---|---|---|---|---|---|
| **File** | **N9** | Expired `RecurringInvoice` templates generate customer invoices — 69 invoices, ₹11.19 Cr | High | N6 (RecurringBill) | High — different entity, receivable side |
| **File** | **N10** | Every recurring-generated invoice carries impossible GST (69/69); no manual invoice does (0/416) | High | N7, N128 | High — different entity, field and producer |
| **File** | **N11** | Credit notes worth up to 52× the invoice they credit; "customer" credit notes against purchase invoices | Medium-High | N128 (same CN records, different defect) | Medium-High |
| **File** | **N12** | Tax foreign keys hold GSTIN strings: `items[].tax_id` resolves to a Tax record 0/189 times | Medium | N127 / N5 / B6 (seed-leak class) | Medium — may be merged into the N127 card |
| **File with care** | **N13** | E-way bills stay `active` after expiry; "active/generated" with no EWB number or vehicle | Medium | GST-29 (platform-known) | Medium — frame as lifecycle, not NIC integration |
| Append | → N6 | Now 36 templates / 153 bills (filed: 3 / 9) | | | |
| Append | → N7 | Now 124 bills, −₹63.69 lakh (filed: 9) | | | |
| Append | → N8 | **Evidence re-stamped — as filed, it no longer reproduces** | | | |
| Append | → N1/N8 | Open request flagged overdue with both deadlines in the future | | | |
| Append | → N128 | Bill `taxes[]` / line tax / `total_tax` disagree on 26 bills | | | |
| ~~Re-file~~ | F18 | **Correction 3 Oct: it is on the board as N273 (To do). Do not re-file.** | Feature | | |

**Order:** N9 and N10 together (they cite each other), then N11, N12, N13.

---

## Ruled out — checked, and not bugs

| Candidate | Why it was dropped |
|---|---|
| Header `total_tax` ≠ Σ line tax on 401/485 invoices and 64/254 bills | **By design.** Document-level `taxes[]` carries a clean CGST/SGST/IGST split that reconciles to `total_tax` on 401/401 invoices and 63/64 bills. Lines simply don't carry the split. *(This also overturns a rule in our own specs — see "Corrections to our specs" below.)* |
| `bill_match`: 8 bills billed with 0 received (UC-11) | The engine working correctly on odd seed data |
| `DeliveryChallan` job-work subtype "missing" (F19) | It exists (`challan_type=job_work`). Our filing was wrong |
| `ApprovalPolicy` → 403 | Entitlement (F6), not a defect |
| E-way bill validity arithmetic | 0/100 mismatches — correct |
| `RetainerInvoice.balance` | Consistent: it means *unapplied advance*. One retainer marked `paid` at 50% is too thin to file |
| `Bill.gst_treatment=overseas` on Indian vendors | Valid enum values that contradict the Party. That's seed data with no validation, and too weak on its own |
| Open-request `is_overdue` driven by past `due_date` (44 of 47) | Explained by the separate `due_date` field; only one case is unexplained (→ N1/N8 append) |

---

## N9 · Expired recurring-invoice templates generate customer invoices — one customer billed 12× for one weekly profile

**Severity:** High · **Area:** Accounts Receivable / Recurring Invoices · **`page`:** `Accounting:Home` · **Sibling of N6**

```
Expired RecurringInvoice templates generate new customer invoices, many times per
day, and never advance last_invoice_date. 69 invoices, Rs 11.19 crore of draft
receivables, came from 30 templates -- 29 of them expired.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)
Verified 2026-09-30.

SUMMARY
N6 reported the RecurringBill scheduler (payables) regenerating bills and firing
expired templates. The receivable-side scheduler, RecurringInvoice, has the same
defect, and on customer-facing documents:

  - 69 Invoices carry a recurring_invoice_id, from 30 distinct templates.
  - 29 of those 30 templates have status "expired"; 65 of the 69 invoices are
    dated AFTER their template's own end_date.
  - The generator ran at least SEVEN times on 2026-09-17 alone -- invoices
    created at 13:11 (x30), 13:22 (x14), 13:35 (x10), 13:48 (x4), 14:21 (x3),
    14:39 (x1), 15:02 (x1) -- then once a day 2026-09-18 .. 09-22.
  - last_invoice_date is not advanced: on 14 of the 30 templates it is still
    earlier than the first invoice they generated.

Worst case -- template 37203233-df70-483d-8aa7-9234a647f913
"Recurring invoice -- Quality", customer Shubhangi Joshi:
  frequency weekly, status expired, end_date 2026-05-12,
  next_invoice_date 2026-05-12, last_invoice_date 2026-03-10
  -> 12 identical invoices, each Rs 14,52,906.30, total Rs 1,74,34,875.60:
     INV-2026-00201, 00223, 00235, 00241, 00245, 00247, 00248 (all 2026-09-17),
     00249 (09-18), 00250 (09-19), 00251 (09-20), 00252 (09-21), 00254 (09-22)

REPRODUCTION
1. tools/call RecurringInvoice.list {"limit": 1000}
2. tools/call Invoice.list {"limit": 1000}; group by recurring_invoice_id.
3. For each group, compare invoice dates with the template's status, end_date
   and last_invoice_date, and invoice created_at timestamps with each other.

EXPECTED
An expired template (or one past end_date) generates nothing. An active weekly
template generates one invoice per week, advances next_invoice_date and stamps
last_invoice_date. The generator runs once per schedule tick.

ACTUAL
Expired templates fire; one template produced 7 invoices in one afternoon; dates
never advance.

IMPACT
Duplicate invoices to real customers -- the receivable mirror of N6's duplicate
payables. If issued, a customer is billed 12 times for one weekly profile, and
output GST is overstated on every copy (see N10: these same 69 invoices also
carry corrupt tax). Currently contained because create_as_draft = 1 on these
templates; anything that bulk-issues drafts turns it into over-billing.

RELATED
N6 (5d6a7f61-...) -- same scheduler class on RecurringBill. Filed separately
because the entity, the direction (receivable vs payable) and the customer-facing
impact differ; merge if triage finds one root cause.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
RecurringInvoice: 37203233-df70-483d-8aa7-9234a647f913 (12 invoices, expired),
  10ea4475-6865-49cb-8711-26bb5d71b97c (5, expired, end 2025-12-30),
  4d21bb91-add7-4b0e-b302-238bb008d364 (5, expired, end 2026-05-05),
  8a1f9dc2-8803-4b5e-9e05-fe54d80616f1 (4, expired, end 2025-10-16)
Invoices: INV-2026-00241 (00945d7a-6f97-4677-a45f-603021437779),
  INV-2026-00254 (289df9d7-d856-499e-b751-91db971fcdd4), and the 10 others above.
No job_id -- found by direct REST/MCP inspection.
```

---

## N10 · Every recurring-generated invoice carries impossible GST — exempt items taxed, CGST+SGST+IGST on one line

**Severity:** High · **Area:** Tax / Accounts Receivable · **`page`:** `Accounting:Home` · **Sibling of N7; distinct from N128**

```
Invoices created by the RecurringInvoice generator carry GST that cannot be
correct: tax-exempt items are taxed, intra- and inter-state tax sit on the same
line, and effective rates run from 9% to 59.7%. All 69 generated invoices are
affected; none of the 416 non-generated invoices is.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c),
India, tax_regime "gst". Verified 2026-09-30.

SUMMARY
The defect tracks the producer exactly:
                                   generated (69)   not generated (416)
  items[] with impossible tax           69                  0
  items[] sum == total_tax              69                  n/a (lines carry no tax)
  taxes[] sum == total_tax               0                401 of 401 taxed
Manually created invoices store their GST split in taxes[] and it reconciles.
Generated invoices store it in items[] instead, and it is wrong.

Three impossibilities, all on generated invoices:
 1. Tax-exempt items charged GST. 49 lines whose Item.tax_preference is
    "tax_exempt" carry Rs 58,07,510.72 of GST.
 2. CGST/SGST and IGST on the same line (93 lines), and CGST != SGST (127 lines).
 3. Amounts unrelated to the stated rate: total_tax / net_total ranges 9%-59.7%.

Worked case -- INV-2026-00241 (00945d7a-6f97-4677-a45f-603021437779), template
37203233 (see N9):
  line 1  Pipe Wrench 138mm (Pair)  item tax_preference = tax_exempt
          tax_percentage 5, taxable 2,93,549.28
          cgst 26,419.44 + sgst 14,677.46 + igst 26,419.44 = 67,516.34  (23.0%)
  line 2  Lathe Dog 106mm (Box)      tax_percentage 12, taxable 7,99,231.84
          cgst 1,43,861.73 + sgst 95,907.82 = 2,39,769.55              (30.0%)
  total_tax 3,60,124.76 on net_total 10,92,781.12 = 33.0%
  taxes[] = three rows with blank tax_type (1,623.81 / 858.07 / 1,465.67),
            summing to 3,947.55 -- not total_tax

THE PLATFORM AGREES
RecurringInvoice e93b9d46-8cee-461b-96db-350347614b9c now records
  last_error = "Taxes do not match the computed tax: expected 0.00 on
               1393029.15 at 0%, got 1074.86."   (last_error_at 2026-09-29)
-- the generator's own check rejects the tax it produces. The 69 invoices written
before that check remain.

Root-cause pointer: the template lines carry tax_id values like
"32CKDPB8823W4ZI" -- GSTIN strings, not Tax ids (see N12). The generator cannot
resolve a tax master from them.

REPRODUCTION
1. tools/call Invoice.list {"limit": 1000}
2. Split by recurring_invoice_id present/absent.
3. For each line: flag (cgst|sgst)>0 AND igst>0; |cgst-sgst|>0.05; and
   |cgst+sgst+igst - taxable_amount x tax_percentage/100| > 1.
4. Join items[].item_id to Item.list; flag tax_exempt items with tax > 0.
5. Oracle: POST /api/accounting/tax/compute {"amount": 293549.28, "rate": 5}
   -> 14,677.46 (stored: 67,516.34).

EXPECTED
Generated invoices carry the same tax structure as manual ones (taxes[] split
reconciling to total_tax), exempt items carry no tax, and each line's tax equals
rate x taxable_amount under one supply type.

ACTUAL
69/69 generated invoices carry impossible item-level tax and a taxes[] that does
not reconcile.

IMPACT
Output GST on these drafts is overstated by multiples (a GSTR-1 built from them
over-declares), and tax is charged on supplies the item master marks exempt. N128
covers CreditNote.taxes[] not being validated on write. This is a different entity
(Invoice), a different field (items[] amounts), and a single producer (the
recurring generator) with a 69/0 split.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
Invoices: INV-2026-00241 (00945d7a-6f97-4677-a45f-603021437779),
  INV-2026-00253 (6434bc7a-5b64-4a4b-a7a1-90aea26a8a97),
  INV-2026-00254 (289df9d7-d856-499e-b751-91db971fcdd4)
Item (tax_exempt, taxed): 28dafc21-9c58-464e-869a-a88fe9fa4d30
RecurringInvoice with last_error: e93b9d46-8cee-461b-96db-350347614b9c
No job_id -- found by direct REST/MCP inspection.
```

---

## N11 · Credit notes worth up to 52× the invoice they credit; customer credit notes raised against purchase invoices

**Severity:** Medium-High · **Area:** Accounts Receivable / Credit Notes · **`page`:** `Accounting:Home`

```
Credit notes are accepted for many times the value of the invoice they reverse,
and "customer" credit notes are raised against the company's own purchase
invoices. Nothing checks either.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)
Verified 2026-09-30. 25 CreditNotes; all 25 carry invoice_id.

SUMMARY
1. Credit exceeding the original. 7 of 25 credit notes credit at least 2x the
   original invoice's grand_total:
     CN-2026-00023  Rs 19,83,965.94  vs INV-2026-00009   Rs 37,580     52.8x
     CN-2026-00022  Rs  2,89,862.00  vs INV-2026-00175   Rs 13,951     20.8x
     CN-2026-00012  Rs  7,58,925.63  vs PINV-2026-00018  Rs 40,120     18.9x
     CN-2026-00010  Rs     34,654.00 vs INV-2026-00180   Rs  5,361      6.5x
     CN-2026-00014  Rs     74,910.00 vs INV-2026-00063   Rs 24,634      3.0x
     CN-2026-00021  Rs  9,29,299.13  vs PINV-2025-00027  Rs 3,15,915    2.9x
     CN-2026-00011  Rs  1,74,223.66  vs INV-2026-00069   Rs 63,067      2.8x
   PINV-2026-00018 (Rs 40,120) is credited twice: CN-2026-00008 (Rs 40,120) and
   CN-2026-00012 (Rs 7,58,925.63) -- Rs 7,99,045.63 of credit on a Rs 40,120 document.

2. Wrong direction. 12 of 25 CreditNotes reference PAYABLE invoices (PINV-*),
   with the vendor stored as customer_id -- e.g. CN-2026-00025 -> PINV-2025-00042,
   customer "Chakan MIDC Utilities". A credit note we issue is a sales-side
   document; a reduction on a purchase is a debit note from us or a credit
   note from the vendor.

3. Internally inconsistent. On 14 of 25, net_total != taxable_value -- e.g.
   CN-2026-00023 net_total 32,126.46, taxable_value 19,70,472.94;
   CN-2026-00022 net_total 0.00, taxable_value 2,88,886.74.

REPRODUCTION
1. tools/call CreditNote.list {"limit": 1000}
2. tools/call Invoice.list {"limit": 1000}  (both directions)
3. Join CreditNote.invoice_id -> Invoice.id; compare grand_totals, the invoice's
   direction, and CreditNote.net_total vs taxable_value.

EXPECTED
Sum of credit notes against an invoice <= that invoice's value (s.34 CGST: a credit
note reduces a supply that was made). A sales credit note references a
receivable invoice. net_total and taxable_value agree.

ACTUAL
Credits up to 52.8x the original; 12 credit notes point at purchase invoices;
14 are internally inconsistent. All are status open or draft.

IMPACT
CN-2026-00023 alone gives a customer an open credit balance of Rs 19,83,965.94
against a Rs 37,580 sale, and it reduces output tax accordingly. N128 (filed)
cites CN-2026-00022/00023 for a different defect: their taxes[] rows disagree
with the tax calculator. This report is about the documents' VALUE and DIRECTION,
which N128 does not cover.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
CreditNote: f7aa6705-2703-4403-ba36-926197945859 (CN-2026-00023),
  08749498-9898-423a-a4ab-6bac6b679c7d (CN-2026-00022),
  3e04530c-c9b3-48c5-bb68-49137694e395 (CN-2026-00012),
  17db0596-c771-456f-81c3-081ce5b0e6c6 (CN-2026-00008),
  d21b5977-9c25-45bc-8b5a-8218bed31e7c (CN-2026-00025)
Invoices: 230ab5c0-855e-4c3d-b578-27aedf9afaf1 (INV-2026-00009),
  62015dff-2155-489a-8911-cbc39f2a4d2c (PINV-2026-00018)
No job_id -- found by direct REST/MCP inspection.
```

---

## N12 · Tax foreign keys hold GSTIN strings — `items[].tax_id` never resolves to a Tax record

**Severity:** Medium · **Area:** Tax / Data integrity · **`page`:** `Accounting:Home` · **Seed-leak class (N126/N127/N5/B6)**

```
items[].tax_id on Bills and RecurringInvoice templates holds GSTIN-shaped strings
instead of Tax record ids. Not one value resolves to a Tax row. tds_section_code
likewise holds reference codes, not TDS sections.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)
Verified 2026-09-30.

SUMMARY
  Bill.items[].tax_id                populated 87   resolve to Tax.id 0
  RecurringInvoice.items[].tax_id    populated 102  resolve to Tax.id 0
  Values: "33EOYPD8129H4ZF", "32CKDPB8823W4ZI", "27VBLPQ1536K8ZI" ...
          -- the shape of a GSTIN (2-digit state + PAN + 3). None matches a
          Party.gst_no either, so it is not even a real counterparty GSTIN.
  Bill.tds_section_code              populated 128  valid TDS section 0
  Values: "S8306/9691", "AP8953/9654", "PS8313/9639" -- the same shape as the
          seeded reference_number field. tds_section is null on all 128.

REPRODUCTION
1. tools/call Tax.list {"limit": 1000}  -> 100 ids (UUIDs)
2. tools/call Bill.list {"limit": 1000}; collect items[].tax_id -> 87 values,
   0 in the Tax id set.
3. tools/call RecurringInvoice.list {"limit": 1000}; same -> 102 values, 0 resolve.
4. Bill.tds_section_code: 128 values, all matching ^[A-Z]+\d+/\d+$; none a section
   (194C/194J/...).

EXPECTED
tax_id is a foreign key to Tax (resolvable, or null). tds_section_code holds a TDS
section.

ACTUAL
Both hold seed-generator strings of the wrong type.

IMPACT
Any tax computation that follows items[].tax_id to the tax master finds nothing.
N10 shows the recurring-invoice generator producing impossible tax from template
lines carrying exactly these values. TDS reporting cannot be grouped by section.
Like N5 and B6, this is a location the N127 sweep ("8,535 values across 85
fields") appears not to have reached -- a foreign-key field rather than a text
field.

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
Bills: 81dc6d87-3874-4936-9331-6582b391a59f (BILL-2026-00254, tax_id 33EOYPD8129H4ZF),
  6b9b6e96-3cbc-4324-8c22-2a173d49807b (BILL-2026-00249),
  47c8c3fe-af6f-4784-8c09-9762b246adde (BILL-2026-00248)
RecurringInvoice: 37203233-df70-483d-8aa7-9234a647f913 (tax_id 32CKDPB8823W4ZI)
No job_id -- found by direct REST/MCP inspection.
```

---

## N13 · E-way bills stay `active` after expiry, and "active/generated" bills have no EWB number or vehicle

**Severity:** Medium · **Area:** Compliance / E-way bill · **`page`:** `Accounting:Home` · ⚠️ **Adjacent to GST-29 — read the note before filing**

> **Why this might be rejected, and how to pre-empt it.** GST-29 (platform-known)
> says e-way bill *generation* has no NIC integration. Triage may read "no EWB
> number" as that. The text below leads with the part GST-29 cannot explain:
> **status never transitions on expiry.** That is local lifecycle logic, and needs
> no NIC. If you want the safest version, file only the expiry half.

```
EWayBill.status does not transition on expiry: 68 e-way bills whose expiry_date
has passed are still "active" or "generated". Separately, all 80 "active"/
"generated" e-way bills have no eway_bill_number, and 52 "active" ones have no
vehicle_number.

ENVIRONMENT
Company: Suryodaya Precision Works Pvt. Ltd. (5cbe5a55-af74-4363-a436-f5350593114c)
Verified 2026-09-30. 100 EWayBills: active 52, generated 28, not_generated 20.

SUMMARY
1. No expiry transition (independent of GST-29). 68 of 80 active/generated
   EWBs have expiry_date < today. Oldest: EWB-2026-00028
   (ce6ab7df-cb47-42fb-95a9-e65063f1e534), generated 2026-07-26, expired
   2026-07-28, still status "active" 64 days later.
2. Status without substance. "generated"/"active" should mean the NIC portal
   issued an EWB number. eway_bill_number is null on 80 of 80 such records, and
   vehicle_number (Part-B) is null on all 52 "active" ones. A movement with no
   Part-B is not valid for transit under Rule 138.
The validity arithmetic itself is right (expiry = generation + ceil(km/200) days
on 100/100), so the dates are trustworthy -- only the status is not.

REPRODUCTION
1. tools/call EWayBill.list {"limit": 1000}
2. Filter status in (active, generated): 80. Of these, count expiry_date < today
   (68), eway_bill_number null (80), and -- for active -- vehicle_number null (52).

EXPECTED
An EWB past expiry_date moves to "expired". "generated"/"active" implies an EWB
number exists; "active" implies Part-B (vehicle) is filled.

ACTUAL
Expired EWBs remain "active"; "active"/"generated" carry neither number nor vehicle.

IMPACT
Any "what is on the road with valid documentation?" query -- or agent -- that
trusts status reports 80 valid e-way bills where there are none. Goods moving
under an expired or number-less EWB are liable to detention and penalty (s.129).

ENTITY IDS
Company: 5cbe5a55-af74-4363-a436-f5350593114c
EWayBill: ce6ab7df-cb47-42fb-95a9-e65063f1e534 (EWB-2026-00028, active, expired 2026-07-28),
  810045ab-7e3c-4005-9165-6f20f3811ecf (EWB-2026-00090, active, expired 2026-08-06),
  1a2139b4-60bd-4047-9cdb-de460e73cd2b (EWB-2026-00091, generated, expired 2026-09-01)
No job_id -- found by direct REST/MCP inspection.
```

---

## Evidence to append to filed reports (not new filings)

Post these as comments on the existing board cards, or as a short follow-up that
names the original id. **Do not refile.**

**→ N6 (`5d6a7f61…`) — scale update.** Filed with 3 templates / 9 bills. On
2026-09-30: **36 templates, 153 bills** carry a `recurring_bill_id`, newest dated
2026-09-29. **15 bills generated since 23 Sep came from templates with status
`expired`.** Still accruing daily.

**→ N7 (`5664be37…`) — scale update.** Filed with 9 bills. On 2026-09-30: **124
bills** have non-zero `tds_amount`, **all 124 have negative `grand_total`** (sum
−₹63,69,104), and all 124 are recurring-generated (0 non-recurring). Every
`tds_section` is null.

**→ N8 (`6ea1df82…`) — ⚠️ the evidence has changed under the report.** N8 cites
APR-2026-00080 with `sla_deadline 2025-08-12`. On 2026-09-30 the same record reads
`2026-09-15T18:00:00`, and all 14 N8 ids moved the same way. **Triage following N8's
steps will not reproduce 14/19 false negatives.** Today it's 5/19 mismatches (4 false
positive, 1 false negative). Tell triage the deadlines were rewritten after filing,
which is itself worth their attention.

**→ N1 / N8 — the open-request path.** N1 stated the open-request logic is correct
(on Keystone). On India, APR-2026-00036 (`3e2d7c9e-0b07-43c3-acd1-b1d65ac4800b`, a
**Bill** approval for BILL-2026-00018) is `pending` with `is_overdue = 1` and
`escalation_count = 17`, while both `due_date` and `sla_deadline` are 2026-11-11 —
six weeks in the future. `check_sla {"dry_run": true}` does not list it as breached.
Also: APR-2026-00050 (`f0132f05…`, cancelled) has `resolved_at = 2026-11-05`, a
resolution date in the future.

**→ N128 (`834f1301…`) — Bills too.** 37 bills have internally inconsistent line tax
(CGST and IGST together, unequal halves, amount ≠ rate × base), and on **26 of them**
`taxes[]` does not reconcile to `total_tax` either. Example: BILL-2026-00019
(`be59dc55…`), `total_tax` 7,828.60, `taxes[]` = 1,613.11 (blank `tax_type`) +
IGST 1,136.41 + CESS 1,136.41 = 3,885.93. Same class as N128 ("nothing validates tax
on write"), on a second entity.

~~**F18 — re-file (feature, no bounty).**~~ **Correction 2026-10-03: do not re-file.**
F18 is on the class bug board as **N273** (To do, backlog), attributed to Team 3 by its
F-series numbering. It is absent from `GET /api/bug-report/mine` and its recorded id
returns 404, but the board has it, so re-filing would create a duplicate.

---

## Corrections to our specs (found during this sweep)

Checking the header-vs-line "bug" showed that one of our own rules is wrong on this
data. That rule is "never use document-level `taxes[]`; item-level only".

- **On Bill and Invoice, `taxes[]` is the reliable source:** it reconciles to
  `total_tax` on 401/401 manual invoices and 63/64 header-taxed bills. Item-level
  tax is empty there. Item-level is populated mainly on *generated* invoices (N10)
  and 37 bills, and is wrong on both.
- **N128's `taxes[]` corruption is on CreditNote.** It does not generalise to Bill or
  Invoice.

Figures in the use-case specs that change as a result are corrected in place, each
marked *"Correction 2026-09-30"*: UC-01 (BILL-2026-00001 carries ₹1,02,672 of ITC,
not ₹0), UC-03 (the Chakan Transport GTA bills charge 18% forward-charge GST, so they
are not undeclared RCM), UC-04, UC-08 (September C2 is ₹14,80,485.54, so D1 is
₹4,05,733.76) and UC-17 (composition-tagged bills carry ₹13,500.98), plus the
README's Rule 0/1.
