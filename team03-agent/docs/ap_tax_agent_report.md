# AP & Tax Agent Report — Payables, GST, TDS (Seat 03)

**Team 03 · Suryodaya Precision Works (India) · 2026-09-22**

`gap_report.md` and `gap_report_mysa.md` compare AgentSwitch against other
products. This report looks only at **our agent**: for each of payables, GST and
TDS, what the platform lets it see and do, what checks it should run, what it
cannot do, and how far our code is from that today.

## How to read the evidence tags

| Tag | Meaning |
|---|---|
| **Verified** | Observed in the live Suryodaya instance (`CURRENT_STATUS.md`, `screen_api_mapping.md`) |
| **Inferred** | Read from the schema or `tools/list`, not exercised end to end |
| **Statutory** | Indian tax law or regulation, from general knowledge. **Not verified for FY 2026-27. Confirm current rates, thresholds and section numbers before coding them** |
| **Code** | What is in this repo today |

The API page originally linked (`tax_rate_service`) is the US Avalara/TaxJar
path. It is out of scope for India and was not readable without credentials.

---

## 0. Where we actually are (read this first)

The agent does not run yet, and its tax logic was written against the brief's
simplified example, not the real schema.

| Item | State | Evidence |
|---|---|---|
| `run_agent.py::call_llm` | `raise NotImplementedError`. No LLM is wired, so no end-to-end run has happened | Code |
| `SKILL.md` allowed entities | Lists `TaxLine`, `Vendor`, `Payment` (Payment is read-only for us). None of `TaxLine`/`Vendor` exist. Real: `Bill`, `Party`, `Tax`/`GSTReturn`, `PaymentMade` | Code vs Verified |
| `tax_math.py` | Reads `type`, `tax_amount`, `is_itc_eligible`, `is_claimed`. None exist on real records. Would return zeros on live data | Code vs Verified |
| `tax_audit.md` step 2 | Calls `TaxLine.list(...)`, a tool that does not exist | Code vs Verified |
| `duplicate_audit.md` step 4 | Uses `hold_payment` and `AgentMessage.create`; neither exists | Code vs Verified |
| `invoice_matcher.py` | Groups on `vendor_id` (real `Invoice` uses `party_id` + `direction`) and uses `invoice_number`/`amount`/`date` names that need mapping | Code vs Verified |
| Tests | 9 unit tests, all against the fake field names, so they pass while the code fails on real data | Code |
| TDS | **Zero code.** No script, playbook or test mentions TDS, though it is in the mission | Code |

Two domain errors sit inside `tax_math.py` itself, beyond the field names:

1. **`net_liability = max(0, output - itc)` discards carried-forward credit.**
   Under GST, ITC in excess of output tax is not "zero liability"; it stays in the
   electronic credit ledger. Statutory. The agent would report ₹0 and lose the
   excess.
2. **A single netted number ignores credit-utilisation rules.** IGST credit is
   used before CGST/SGST, and CGST credit cannot pay SGST liability, or the
   reverse. Statutory. Netting all heads together can overstate credit
   available. `GSTReturn` already carries `igst/cgst/sgst/cess_amount` separately,
   so the data supports doing it per head.

Also: `output_tax` counts only sales invoices. It ignores `CreditNote` (25 exist)
and `VendorCredit`, which reduce output tax and ITC respectively.

---

## 1. Payables

### 1.1 What the platform gives us

| Capability | Tool / field | Tag |
|---|---|---|
| Read vendor bills | `Bill.{list,get}`: `vendor_id`, `date`, `due_date`, `grand_total`, `balance_due`, `status` (BillFlow state), `approval_status`, `ims_status`, `itc_eligibility` | Verified |
| Read payable invoices | `Invoice.list(direction=payable)`: 165 records, `party_id`, `outstanding`. **A second AP representation next to `Bill` (101)**; relationship unexplained | Verified |
| Vendors | `Party.list(contact_type="vendor")`: GSTIN, PAN, `is_msme`/`msme_no`, bank account, beneficiary | Verified |
| Payments made | `PaymentMade.{list,get,create,update,mark_paid,cancel}`, with `bills`/`applied_allocations` | Verified |
| Bill lifecycle | `Bill.open`, `.submit`, `.approval.submit`, `.record_partial_payment`, `.record_full_payment.*`; `VendorCredit.{open,close}` | Verified |
| Purchase orders | `PurchaseOrder.{list,get}`, `PurchaseOrder.make.Bill` | Inferred |
| Escalate / flag | `AgentEscalation.{create,update}`, `AgentTodo.create`, `Notification.create`. **No `AgentMessage.create`** | Verified |
| Hold a payment | **No `hold_payment` field.** Closest: `Bill.approval.submit` (to `pending_approval`) plus an escalation. No confirmed tool to block `PaymentMade.create` | Verified |

### 1.2 Checks the agent should run

| # | Check | Data needed | Status |
|---|---|---|---|
| P1 | **Duplicate bill/payment**: exact (same vendor + invoice no.), near (same vendor + amount within window), and normalised invoice-number variants (`INV-001` vs `INV001`, leading zeros) | `Bill`, `Invoice(payable)`, `PaymentMade` | Partly built; must be rebuilt on real fields |
| P2 | **Cross-representation duplicates**: same bill present as both a `Bill` and an `Invoice(direction=payable)` | both entities | Not built. Needs the open question in `CURRENT_STATUS.md` §8 answered first |
| P3 | **Paid-twice**: one bill with multiple `PaymentMade` allocations summing past `grand_total` | `PaymentMade.applied_allocations` vs `Bill.grand_total` | Not built |
| P4 | **Overdue and ageing** | `Bill.due_date`, `balance_due` | Not built. Trivial |
| P5 | **MSME 45-day**: `Party.is_msme` bills unpaid past 45 days from acceptance/date. The locale flag `msme_45_day=true` says the platform has *something*; unclear whether it alerts | `Party`, `Bill`, `PaymentMade` | Not built. Verify what the flag does first |
| P6 | **Vendor master hygiene**: missing/malformed GSTIN or PAN, GSTIN state code vs PAN mismatch, two vendors sharing a bank account | `Party` | Not built. Format-only; no registry lookup |
| P7 | **2-way match** (PO ↔ Bill). **3-way is impossible**: no GRN entity | `PurchaseOrder`, `Bill` | Not built |
| P8 | **Bill total integrity**: sum of item taxes vs `total_tax`, `grand_total` vs items | `Bill.items[]` | Not built |

Consider P3 and P8 first. They need no external data, and the seeded ledger has
shown it contains inconsistencies (§4).

### 1.3 Limits

The agent can **flag and escalate**, not **stop** a payment. `finance_user` is
read-mostly and no tool blocks `PaymentMade.create`. "Held for review" is
therefore advisory. Say so in the agent's output rather than implying a hold
exists.

---

## 2. GST

### 2.1 What the platform gives us

| Capability | Tool / field | Tag |
|---|---|---|
| Period returns | `GSTReturn.{list,get}`: `return_type` GSTR-1/3B/2A/2B/9, `taxable_amount`, `igst/cgst/sgst/utgst/cess_amount`, `net_tax_payable`, `filing_status`, `filed_date`. **5 exist for Suryodaya.** Read-only for us | Verified |
| **Item-level tax** | `items[].cgst_amount/rate`, `sgst_*`, `igst_*`, `cess_*` on `Invoice` and `Bill`. **The only coherent tax source** (see §4) | Verified |
| ITC eligibility | `Bill.itc_eligibility` = `input` / `input_services` / `capital_goods` / `ineligible` | Verified |
| IMS status | `Bill.ims_status` = `pending` / `accept` / `reject` | Verified |
| Reverse charge | `Bill.is_reverse_charge` | Verified |
| Place of supply | `place_of_supply` on `Invoice` / `Bill` | Verified |
| e-Way bill | `EWayBill.{list,get,create,update,generate,activate}`; no NIC integration (GST-29) | Verified |
| Locale flags | `gst_returns`, `gst_ims`, `eway_bill` on; `einvoicing` **off** | Verified |
| **Not available to us** | GSTN fetch (2A/2B), return generate/file (`finance_admin`-only or unbuilt), GSTR-9 (HTTP 501, GST-39), e-invoicing/IRN (GST-28), GST amendments (GST-32), GST payment/challan entity | Verified |

### 2.2 Checks the agent should run

| # | Check | Data needed | Status |
|---|---|---|---|
| G1 | **Output tax per head** for a period, from `items[]` on receivable `Invoice`, less `CreditNote` | item-level fields | Rebuild `tax_math.py` |
| G2 | **Eligible ITC per head** from `Bill.items[]` where `itc_eligibility != ineligible`, less `VendorCredit` | item-level fields | Rebuild |
| G3 | **Net payable per head with correct utilisation order**, and **carry-forward** shown separately, never floored to zero | G1, G2 | Rebuild. Replaces the current `max(0, …)` |
| G4 | **Reconcile computed figures against `GSTReturn.net_tax_payable`** for the same period, and report the delta | `GSTReturn` | Not built. High-value: exposes whether the return matches the books |
| G5 | **Unclaimed ITC**: eligible `Bill`s with `ims_status` not `accept`, i.e. credit at risk. There is **no `is_claimed` flag**; `ims_status` is the closest proxy, so state that assumption | `Bill` | Rebuild; document the proxy |
| G6 | **IMS pre-screen**: recommend accept/reject on `pending` bills (vendor GSTIN valid? duplicate? matches a PO? amount sane?). Write-back via `Bill.update(ims_status=…)` is **unconfirmed** | `Bill`, `Party`, `PurchaseOrder` | Not built |
| G7 | **RCM completeness**: bills from unregistered vendors or RCM-category services without `is_reverse_charge` | `Bill`, `Party` | Not built |
| G8 | **Blocked credit / ineligible mix**: ITC claimed on categories that are statutorily blocked (s.17(5)) | `Bill.itc_eligibility` + item categories | Not built. Statutory list needs confirming |
| G9 | **180-day rule**: ITC reversal exposure where the vendor bill is unpaid past 180 days (Statutory, Rule 37) | `Bill.date`, `PaymentMade` | Not built. Verify current rule |
| G10 | **ITC claim window**: bills approaching or past the s.16(4) cut-off (Statutory) | `Bill.date` | Not built |
| G11 | **Place-of-supply consistency**: IGST charged where CGST+SGST expected (and reverse) from vendor vs company state | `Bill`, `Party`, company state | Not built |
| G12 | **Back-dated documents into filed periods** (platform silently accepts these, GST-32) | `Invoice`/`Bill.date` vs `GSTReturn.filed_date` | Not built. The platform won't catch this, so the agent could |

### 2.3 Limits

Read and analyse only. The agent cannot fetch 2B from GSTN, generate or file a
return, or issue an IRN. The answer to "what is unclaimed" is **"computed from
books and IMS status, not confirmed against GSTN"**, and the agent must say so.

---

## 3. TDS

**This is our largest hole: zero code, and the platform only stores the data.**

### 3.1 What the platform gives us

| Capability | Tool / field | Tag |
|---|---|---|
| TDS on a bill | `Bill.tds_name`, `tds_percentage`, `tds_amount`, `tds_section_code`, `tds_section` | Verified |
| TDS on an invoice | `Invoice.tds_amount` | Verified |
| TDS/TCS in totals | Now flow into `grand_total` and post their own GL legs | Verified |
| Locale flag | `tds_tcs` on | Verified |
| Tax type | `Tax.tax_type` includes `TDS`, `TCS` | Verified |
| Vendor PAN | `Party` PAN field | Verified |
| **Not available** | Auto-deduction by section/threshold; 26Q/27Q filing; challan tracking (GST-18) | Verified |

### 3.2 Checks the agent should run

| # | Check | Data needed | Status |
|---|---|---|---|
| T1 | **Missing TDS**: bill for a TDS-liable nature (contractor, professional, rent, commission) with no `tds_section` or `tds_amount = 0` | `Bill`, `Party` | Not built |
| T2 | **Wrong rate**: `tds_percentage` vs the statutory rate for the section and payee type, with the higher rate where PAN is missing or invalid (Statutory) | `Bill`, `Party.pan` | Not built. **Rates must come from a reviewed table, not the model's memory** |
| T3 | **Threshold logic**: single-payment and annual-aggregate thresholds per section, tracked per vendor across bills (Statutory) | all `Bill`s per vendor per FY | Not built. Needs per-vendor running totals in `scripts/` |
| T4 | **Amount arithmetic**: `tds_amount` = base × `tds_percentage`, and the base (excluding GST if shown separately) is right | `Bill` | Not built. Deterministic, easy |
| T5 | **TDS liability by section by month** (what should be deposited), from posted bills/payments | `Bill`, `PaymentMade` | Not built |
| T6 | **Deposit tracking**: TDS deducted but no evidence of deposit. **No challan entity exists**, so this is only detectable via GL payable balances (`GLEntry` on the TDS payable account) | `GLEntry`, `Account` | Not built. Feasibility unconfirmed |
| T7 | **Section misclassification**: same vendor billed under different sections across bills | `Bill` | Not built |

### 3.3 Two things to verify before writing any TDS code

- **Statute renumbering.** The Income-tax Act, 2025 is understood to apply from
  1 April 2026 and to replace the 1961 Act's section numbers, while vendors and
  even Mysa's own pages still say "194C". Which numbering the platform's
  `tds_section_code` values follow is unknown. Read real `Bill` records first.
- **Rate/threshold table ownership.** Put the table in one reviewed file
  (`scripts/tds_rules.py`) with a source and effective date per row. Hard Rule 3
  applies: the model must never supply a rate from memory.

---

## 4. Data-trust rules (already learned the hard way)

From `CURRENT_STATUS.md` §7a and the three filed bugs (§9). These bind every
check above:

| Do | Do not |
|---|---|
| Use **item-level** `cgst/sgst/igst/cess_amount` | Use document-level `taxes[]`. `tax_type` there is free text holding product names (0 of 68 valid); rows are incoherent |
| Use `GSTReturn` amounts as the *filing-side* comparator | Use the `Tax` / `TaxJurisdiction` master. All 100 jurisdictions on the India company are US data |
| Expand composite GST from `items[]` rates | Rely on `group_taxes`. 67 of 100 parents contradict `is_group` and 0 of 88 child types are valid |

Practical consequence: **G4 (books vs `GSTReturn`) is the best integrity
signal available.** If item-level totals and the filed return disagree, that
finding is worth more than any single-record check.

Seeder data also means numbers can look wrong for reasons unrelated to real-world
tax. Report a discrepancy as "inconsistent in this instance", and file it via
`BugReport.create`, rather than presenting it as a compliance failure.

---

## 5. Mapping to the Core Challenge Prompt

> "What is our tax liability this period, what is unclaimed, and is any vendor
> being paid twice?"

| Question | Answered by | Ready? |
|---|---|---|
| Tax liability this period | G1 + G2 + G3, reconciled by G4; TDS payable via T5 | No. `tax_math.py` is wrong-schema and wrong-model |
| What is unclaimed | G5 (+ G6, G9, G10 for context) | No. Proxy via `ims_status` undocumented in code |
| Paid twice | P1, P3 (+ P2) | Partly. Logic exists, on fake fields |

---

## 6. Backlog, in order

| # | Task | Why now | Unblocks |
|---|---|---|---|
| 1 | **Wire `call_llm`** and run once end to end against Suryodaya | Nothing has been proven on real data | Everything |
| 2 | **Rewrite `SKILL.md` entities and both playbooks** to real tools (`Bill`, `Party`, `GSTReturn`, `AgentEscalation`, `Bill.approval.submit`) | Documented in `CURRENT_STATUS.md` §7, still unapplied | 3, 4 |
| 3 | **Rebuild `tax_math.py`** on item-level fields: per-head, credit-note-aware, carry-forward, no floor. Update tests to real record shapes | Current code returns wrong or zero answers | Q1 and Q2 of the challenge prompt |
| 4 | **Rebuild `invoice_matcher.py`** on `Bill` + `Invoice(payable)`; add normalised invoice numbers and paid-twice (P3) | Direct challenge-prompt item | Q3 |
| 5 | **G4 reconciliation** against `GSTReturn` | Best cross-check; cheap once 3 exists | Trust in 3 |
| 6 | **Resolve the `Invoice(payable)` vs `Bill` question** with side-by-side samples | Duplicate logic depends on it | P2 |
| 7 | **Build `scripts/tds_rules.py` and T1–T4** | Zero TDS coverage today | TDS story |
| 8 | **MSME (P5), ageing (P4), 180-day (G9)** | Simple date joins; check what `msme_45_day` flag does first | Extra coverage |
| 9 | **Wire `AgentSession`/`AgentTask`/`AgentEscalation`** | Makes actions auditable and gradable | `job_id` question |

## 7. Open questions

1. What does the locale flag `msme_45_day=true` actually do on this instance?
2. Are `Bill` and `Invoice(direction=payable)` the same documents, or different flows?
3. Does `Bill.update(ims_status=…)` work for `finance_user`, or is it flow-gated?
4. Which section numbering do `tds_section_code` values use?
5. Is there any TDS-payable GL account we can read to detect unremitted TDS (T6)?
6. How is the run tied to a gradable `job_id`?

## Caveats

- Nothing here was exercised live this session: no credentials are available in
  this environment. Platform statements come from earlier verified snapshots,
  which the shared ledger has since drifted from.
- All **Statutory** items are from general knowledge and were not checked
  against current law or FY 2026-27 amendments. Treat them as a checklist of
  what to verify, not as rules to implement.
- Check IDs (P/G/T) are proposals for our own backlog, not platform features.
