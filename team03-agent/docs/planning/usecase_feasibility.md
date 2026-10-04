# usecase_feasibility.md — Every use case: achievable? tools? requested? mode? playbook?

**Team 03 · Seat 03 · 2026-10-04** · one row per use case in [`../usecases/`](../usecases/README.md): 44 India + 22 US = **66**, grouped into 13 families of similar use cases.

**How each column was checked:**

| Column | Source |
|---|---|
| **Achievable?** | Each spec's verdict, from live data pulled 2026-10-04 |
| **MCP tools** | The read tools each spec's §4 names, checked against the live `tools/list` (India 508 tools, US 500). "+ REST" marks an oracle that exists only as a REST endpoint |
| **Gap → already requested?** | [`requested_tools.md`](../submissions/requested_tools.md) (filed as board **N426**), [`agentswitch_submissions.md`](../submissions/agentswitch_submissions.md) (F1–F8 = **N173**, F18 = **N273**), and [`submission_tracker.md`](../submissions/submission_tracker.md) (F19–F22 **not filed**) |
| **Modes** | Each spec's §3 Trigger. **R** = on_request, **E** = on_event (what fires it), **S** = scheduled (cadence) |
| **Playbook · category** | Catalogue §3–§4. Specs with the same playbook name share one playbook |

**Achievable:**
- ✅ yes, now;
- 🟡 partly (a derivation, a data caveat, or one leg blocked);
- 🔴 blocked by the platform;
- ⚪ spec only (no tenant or data of that kind yet).

---

## Summary

| | Count |
|---|---|
| ✅ Achievable now | **35** |
| 🟡 Partly | **21** |
| 🔴 Blocked by the platform | **5** (UC-08, UC-15, UC-17, UC-31, UC-36) |
| ⚪ Spec only (no tenant or data) | **5** (UC-34, US-10, US-12, US-13, US-22) |
| **MCP read tools present** | **63 of 66**. The 3 that miss a tool (UC-06, UC-44: `ApprovalPolicy.list`; UC-16: `Batch.list`, `StockEntry.list`) are **already requested** (N426: T2.1, T2.2, T2.3) |
| Modes | **All 66** answer on request and run on a schedule. **47** also react to an event |
| Playbooks | **~46**: 66 specs, with 20 sharing a playbook |

**Not yet requested** (the full list is at the end):
- the 1099 summary report as an MCP tool;
- a sales channel on `Invoice` (F22);
- a sales-tax return record;
- the receiving GSTIN on documents;
- certificates issued to vendors;
- W-8 fields;
- `Notification.create`;
- a structured approval choice on escalations.

---

## Cross-cutting needs (every use case relies on these)

| Need | Today | Requested? |
|---|---|---|
| Watch for changes (on_event) | ✅ Works with `sort_by=updated_at`; there is no `updated_since` filter | `updated_since`, ranges: **T3.1 ✅ (N426)** |
| Escalate a finding | ✅ `AgentEscalation.create` (needs an `AgentSession` first) | Structured reason + entity links: **T3.5 ✅ (N426)** |
| To-do for finance | ✅ `AgentTodo.create` | — |
| Notify / alert | ❌ `Notification.create` not exposed (workaround: `AgentTodo`) | ❌ **not requested** |
| Human approval choice (hold / ignore) | ❌ No structured resolution field on `AgentEscalation` | ❌ **not requested** |
| Hold a bill | ❌ No `Bill.hold`; interim `Bill.approval.submit` (exists) | **T3.3 ✅ (N426)** |
| Try a write safely | Only `endpoint.approvals.check_sla` has `dry_run` | **T3.2 ✅ (N426)**, F2 ✅ (N173) |
| Reports over MCP (AP ageing, sales-tax liability, GSTR-1) | REST only | **T1.1 ✅ (N426)**, **F3 ✅ (N173)** |

---

## A · Liability and returns

*Compute what we owe for a period, and get each return right and on time.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-23](../usecases/IN/uc-23-period-gst-liability.md) Period GST liability (GSTR-3B) | "How much GST do we owe for this month, under each head, and how much of it must be paid in cash?" | 🟡 Computable; return rows don't reconcile | ✅ (+ REST oracle `indirect-tax/reconcile`) | Oracle as MCP: **T1.4 ✅ (N426)**. Return mismatch: candidate bug, **not filed** | R · S monthly (15th, 19th) | period-liability · core tax |
| [US-01](../usecases/US/us-01-period-sales-use-tax-liability.md) Period sales & use tax liability | "What is our sales and use tax liability this period, by jurisdiction?" | ✅ Matches the platform report to the cent | ✅ (+ REST liability report) | Report as MCP: **F3 ✅ (N173)** | R · S monthly | period-liability · core tax |
| [UC-26](../usecases/IN/uc-26-gstr1-readiness.md) GSTR-1 readiness | "Is every sale this month going into the right part of GSTR-1, with the right kind of GST?" | 🟡 Checks run (12 wrong-head invoices); GSTR-1 rows don't reconcile | ✅ | GSTR-1 report as MCP: **F3 ✅ (N173)** | R · E new invoice / credit note · S monthly (8th, 10th) | gstr1 · output tax |
| [UC-27](../usecases/IN/uc-27-return-filing-timeliness.md) Return filing timeliness | "Which GST returns are due or overdue, and what is lateness costing us?" | ✅ August returns overdue now | ✅ | — (challans: GST-18, platform-documented) | R · S daily + T−5/T−1 reminders | filing-calendar · compliance calendar |
| [US-14](../usecases/US/us-14-sales-tax-filing-calendar.md) Filing calendar and timeliness | "Which state returns are due when, are we ready to file them, and what do we lose if we're late?" | 🟡 Calendar ✅; filing can't be verified | ✅ | Return record / `next_filing_due`: ❌ **not requested** | R · S daily reminders, monthly | filing-calendar · compliance calendar |
| [UC-31](../usecases/IN/uc-31-annual-return-reconciliation.md) Annual return GSTR-9/9C | "Will our annual return agree with our monthly returns and our books, and what do we have to fix before it's due?" | 🔴 Filing blocked (HTTP 501); a draft is computable | ✅ (GSTR-9 endpoint 501) | GST-39 platform-documented, **don't file**. GSTR-2B lines: **T1.3 ✅ (N426)** | R · S Oct–Dec | annual-return · compliance calendar |

## B · Input credit (India)

*Which GST credit we may keep, must reverse, or are about to lose.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-24](../usecases/IN/uc-24-unclaimed-itc-ims-2b.md) Unclaimed / at-risk credit | "Which input credit can we still claim, which have we claimed that we shouldn't have, and what will we lose if we wait?" | 🟡 IMS checks ✅ (10 rejected bills still eligible); GSTR-2B line match blocked | ✅ | `reconcile_2b` / `ims_action`: **T1.3 ✅ (N426)** | R · E IMS status change · S monthly (12th, 15th), Aug–Nov | itc-entitlement · core tax |
| [UC-01](../usecases/IN/uc-01-rule-37-itc-reversal.md) Rule 37 180-day reversal | "Which unpaid bills are about to cost me my input credit, and how much?" | ✅ First live case 5 Dec 2026 | ✅ | — (posting the reversal: **T4.1 ✅ (N426)**) | R · S daily | rule37 · input tax |
| [UC-25](../usecases/IN/uc-25-vendor-credit-debit-notes-itc.md) Inward credit/debit notes | "Our suppliers have given us credit notes. Have we reduced our input credit for them, and are any of them wrong?" | ✅ | ✅ | — (`VendorCredit.taxes[]` corruption: candidate bug, **not filed**) | R · E new vendor credit · S monthly | vendor-notes · input tax |
| [UC-02](../usecases/IN/uc-02-blocked-credit-audit.md) Blocked credit s.17(5) | "Have we claimed credit on anything the law blocks?" | ✅ | ✅ | — (HSN rate source **T3.4 ✅ (N426)**, optional) | R · S weekly | blocked-credit · input tax |
| [UC-33](../usecases/IN/uc-33-expense-claims-itc.md) Expense claims: GST credit | "Are we claiming GST credit on expense claims where the law says we can't?" | ✅ 18 personal expenses claim credit | ✅ | — | R · E new expense · S monthly | expense-credit · input tax |
| [UC-16](../usecases/IN/uc-16-drug-expiry-blocked-credit.md) Expiry → blocked credit | "What stock is about to expire, and what credit do we lose when it does?" | 🟡 No batch or stock access | ❌ `Batch.list`, `StockEntry.list` | **T2.2 + T2.3 ✅ (N426)** | R · E write-off · S daily | expiry · input tax |

## C · Exempt and mixed supply (school, clinic)

*Exempt output turns input GST into a cost, and forces apportionment.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-07](../usecases/IN/uc-07-school-exempt-taxable-split.md) School exempt/taxable split | "Which of our income streams are actually taxable, and are we treating them correctly?" | 🟡 Runs on manufacturing data; no school tenant | ✅ (+ REST `tax/compute`) | `Tax.compute` as MCP: **T1.2 ✅ (N426)** | R · E item change · S monthly | exempt-split · output tax |
| [UC-14](../usecases/IN/uc-14-clinic-exempt-taxable-split.md) Clinic exempt/taxable split | "Which parts of what we do are taxable, and are we charging GST on the right ones?" | 🟡 Engine ready; no clinic tenant | ✅ (+ REST `tax/compute`) | **T1.2 ✅ (N426)** | R · E item change, discharge · S monthly | exempt-split · output tax |
| [UC-08](../usecases/IN/uc-08-rule-42-apportionment-school.md) Rule 42 apportionment, school | "How much of our input credit are we actually entitled to keep?" | 🔴 Report only: compute ✅, posting blocked | ✅ | Posting: **F18 ✅ (N273)** + **T4.1 ✅ (N426)** | R · S monthly + annual true-up | apportionment · input tax |
| [UC-15](../usecases/IN/uc-15-rule-42-43-apportionment-clinic.md) Rule 42/43, clinic | "Of all the GST we paid on purchases, how much can we actually keep?" | 🔴 Report only, as UC-08 | ✅ | **F18 ✅ (N273)** + **T4.1 ✅ (N426)** | R · S monthly + annual | apportionment · input tax |
| [UC-34](../usecases/IN/uc-34-school-exempt-inward-services.md) School: exempt inward services | "Are our bus, canteen, security, cleaning and exam vendors charging us GST they shouldn't?" | ⚪ No school tenant | ✅ | — | R · E new bill · S monthly | school-inward · input tax |

## D · Self-assessed and purchase-side tax

*Tax the buyer must pay itself (RCM, use tax), or overpaid to a vendor.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-03](../usecases/IN/uc-03-rcm-self-invoicing.md) RCM self-invoicing | "Which supplier bills make us liable to pay the tax ourselves, and have we?" | ✅ | ✅ | — | R · S weekly | rcm · input tax |
| [UC-21](../usecases/IN/uc-21-import-of-services-rcm.md) Import of services RCM | "Which foreign supplier bills create a GST liability we have to pay ourselves?" | 🟡 No genuine overseas vendor | ✅ | — (vendor validation **T4.2 ✅ (N426)**, optional) | R · E bill before approval · S monthly | rcm · input tax |
| [US-02](../usecases/US/us-02-consumer-use-tax-on-purchases.md) Consumer use tax | "Which purchases did nobody charge us sales tax on, where we owe use tax ourselves?" | 🟡 Taxability needs classification | ✅ | — | R · E bill with no vendor tax · S monthly | purchase-taxability · input tax |
| [US-11](../usecases/US/us-11-sales-tax-on-exempt-purchases.md) Tax paid on exempt purchases | "Have we paid sales tax to vendors on purchases that should have been tax-free, and can we still get it back?" | ✅ 0 cases today | ✅ | Certificates issued *to* vendors: ❌ **not requested** | R · E taxed bill · S monthly + annual | purchase-taxability · core tax |

## E · Outward taxability, rates and exemptions

*Charging the right tax, at the right rate, on what we sell.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-18](../usecases/IN/uc-18-hsn-rate-consistency.md) HSN rate consistency | "Are we charging the right GST rate on every product we sell?" | ✅ As a consistency check (no authoritative rate table) | ✅ (+ REST `tax/compute`) | HSN rate lookup: **T3.4 ✅ (N426)** | R · E item change · S monthly | hsn-rate · output tax |
| [US-05](../usecases/US/us-05-sourcing-and-rate-correctness.md) Sourcing and rate | "Are we charging each customer the right state and local rate for where the sale is sourced?" | 🟡 36 Ohio invoices need a sourcing ruling | ✅ | — (rate service: platform-documented gap) | R · E new invoice · S monthly | rates · output tax |
| [US-13](../usecases/US/us-13-taxability-services-digital-holidays.md) Taxability by state | "Is each thing we sell actually taxable in the customer's state on that date — and are we charging accordingly?" | ⚪ Spec for services; ✅ goods | ✅ | — (`Item.tax_code` empty is data, not a request) | R · E invoice, item change · S monthly + holiday calendar | taxability · output tax |
| [US-04](../usecases/US/us-04-exemption-certificate-coverage.md) Exemption certificates | "For every sale we didn't charge tax on, do we hold a valid exemption certificate?" | ✅ | ✅ | — | R · E exempt invoice · S monthly (90-day expiry) | exemption-certs · output tax |
| [UC-20](../usecases/IN/uc-20-export-lut-tracking.md) Export / LUT | "Are our export invoices genuinely zero-rated, and is our LUT still valid?" | 🟡 LUT has no dates | ✅ | LUT registry: **T4.4 ✅ (N426)**; F21 not filed separately | R · E zero-rated invoice · S 1 April | export-lut · output tax |
| [UC-35](../usecases/IN/uc-35-agency-pure-agent-reimbursements.md) Agency pure-agent recharges | "When we pass client costs back to them, are we charging GST correctly on the recharge?" | 🟡 Expense→invoice link empty | ✅ | `Invoice.expense_id` never set: ❌ **not reported** (candidate bug) | R · E invoice / expense invoiced · S monthly | recharges · output tax |

## F · Credit notes, advances and refunds

*Time windows on adjustments, advances and recoveries.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-19](../usecases/IN/uc-19-credit-note-time-limit.md) Credit-note s.34(2) window | "Which returns can we still issue a tax-effective credit note for?" | ✅ Window closes 30 Nov 2026 | ✅ | — | R · E new credit note · S monthly Aug–Nov | credit-note-window · output tax |
| [US-10](../usecases/US/us-10-credit-memo-refund-window.md) Credit memo refund window | "For returns and price adjustments, did we refund the sales tax correctly, and are we still inside the window to recover tax we remitted?" | ⚪ 0 credit notes on the tenant | ✅ | — | R · E credit memo · S monthly | credit-note-window · output tax |
| [UC-22](../usecases/IN/uc-22-advance-receipt-gst.md) Advance-receipt GST | "Have we paid GST on client advances we're still holding?" | 🟡 `RetainerInvoice` has no tax fields | ✅ | Tax fields / receipt voucher: **T4.6 ✅ (N426)** | R · E retainer paid / advance received · S monthly | advances · output tax |
| [UC-32](../usecases/IN/uc-32-itc-refund-zero-rated-inverted.md) Credit refund (Rule 89) | "We have credit piling up because we export or because our inputs are taxed higher than our sales. How much can we get refunded, and by when?" | 🟡 Compute ✅ (₹37,758.92); LUT validity unproven | ✅ | LUT: **T4.4 ✅ (N426)**; refund filing out of scope | R · S monthly + window warning | refund · input tax |

## G · Thresholds, registrations and sales channels

*Obligations switched on by turnover, state presence or the channel a sale goes through.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-29](../usecases/IN/uc-29-turnover-based-obligations.md) Turnover-based obligations | "Given our turnover, which GST obligations apply to us this year, and are we meeting them?" | ✅ Live: e-invoicing obligation unmet | ✅ | IRN: GST-28 platform-documented, **don't file**. Company tax profile: **T4.3 ✅ (N426)** | R · S 1 April + monthly | turnover · compliance calendar |
| [US-03](../usecases/US/us-03-economic-nexus-monitoring.md) Economic nexus | "Are we approaching a new state's sales tax registration obligation anywhere?" | ✅ | ✅ | — (N4 appears fixed) | R · E invoice to an unregistered state · S monthly | nexus · compliance calendar |
| [UC-17](../usecases/IN/uc-17-composition-scheme.md) Composition scheme | "Are we still eligible for the composition scheme, and are we about to fall out of it?" | 🔴 Main check blocked; sub-check ✅ | ✅ | Organisation's own tax mode: **T4.3 ✅ (N426)**; F20 not filed separately | R · E bill from a composition vendor · S monthly | composition · registrations |
| [UC-30](../usecases/IN/uc-30-multiple-registrations.md) Multiple registrations, transfers, ISD | "We're registered in several states. Are our branches dealing with each other the way GST requires?" | 🟡 Data checks ✅ (PAN mismatch); transfers and ISD blocked | ✅ | Receiving GSTIN / despatch location on documents: ❌ **not requested** | R · E location / challan change · S monthly | registrations · registrations |
| [UC-36](../usecases/IN/uc-36-ecommerce-tcs-s52.md) Retail: e-commerce TCS (s.52) | "Do our marketplace sales, and the tax the marketplace collected on them, agree with what we report — and have we claimed that collected tax back?" | 🔴 No sales channel in the data model | ✅ (the tools exist; the field doesn't) | **F22 ❌ not filed** | R · S monthly | marketplace · output tax |
| [US-12](../usecases/US/us-12-marketplace-facilitator-sales.md) Marketplace facilitator sales | "For sales we make through marketplaces, is the marketplace collecting the tax, and are we keeping those sales out of our own returns and nexus totals correctly?" | ⚪ No sales channel | ✅ | Sales channel: ❌ **not requested** (file with F22) | R · E marketplace invoice · S monthly | marketplace · output tax |

## H · Withholding and income-tax limits

*Tax we must deduct before paying, or that disallows the expense if we get it wrong.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-09](../usecases/IN/uc-09-vendor-tds-verification.md) Vendor TDS verification | "Are we deducting the right TDS on every vendor payment, under the right section?" | ✅ | ✅ (+ REST `tax/compute`) | Hold for wrong TDS: **T3.3 ✅ (N426)** | R · E bill approved · S monthly (before 7th) | tds · withholding |
| [UC-39](../usecases/IN/uc-39-tds-deductor-setup.md) TDS deductor setup and sections | "Are we set up to deduct TDS at all, and are we deducting under every section that applies to what we pay?" | ✅ Live: TDS on, no TAN | ✅ | — (challans / 26Q: GST-18 platform-documented) | R · E new bill / expense · S monthly + quarterly | tds · withholding |
| [UC-13](../usecases/IN/uc-13-194q-206c-thresholds.md) 194Q / 206C(1H) | "Which suppliers or customers have we crossed the ₹50 lakh line with?" | 🟡 Buyer-turnover gate unknown | ✅ | Company turnover: **T4.3 ✅ (N426)** | R · E new bill · S monthly | tds · withholding |
| [UC-37](../usecases/IN/uc-37-non-resident-payments-tds-195.md) Non-resident payments s.195 | "Before we pay a foreign vendor, have we deducted the right tax and got the remittance paperwork done?" | 🟡 No genuine non-resident vendor | ✅ | — | R · E bill / payment to a non-resident · S monthly | tds · withholding |
| [UC-38](../usecases/IN/uc-38-cash-payment-limits.md) Cash payments s.40A(3) | "Are we paying any vendor in cash above the limit, and losing the tax deduction for it?" | ✅ 13 live findings | ✅ | — | R · E cash payment, cash-mode bill approved · S monthly | cash-limit · withholding |
| [US-06](../usecases/US/us-06-form-1099-readiness.md) 1099 and backup withholding | "Which vendors will need a 1099 for this year, and do we have what we need to file it — or should we be withholding?" | ✅ | ✅ (+ REST 1099 summary) | 1099 summary as MCP: ❌ **not requested** (F3 lists other reports) | R · E paying a vendor with no TIN · S monthly + December | payee-withholding · withholding |
| [US-22](../usecases/US/us-22-foreign-vendor-withholding.md) Foreign vendors: Chapter 3 / 1042-S | "Before we pay a foreign vendor, have we withheld the right US tax and collected the right form?" | ⚪ No foreign vendor | ✅ | W-8 fields on `Party`: ❌ **not requested** | R · E bill to a foreign vendor · S monthly + by 15 March | payee-withholding · withholding |

## I · Duplicates and matching

*Are we paying for something twice, or for something we never received?*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-05](../usecases/IN/uc-05-duplicate-vendor-payment.md) Duplicate vendor payment | "Is any vendor being paid twice?" | 🟡 Exact key usable on few bills (no supplier invoice number) | ✅ | Hold: **T3.3 ✅ (N426)**; `updated_since`: **T3.1 ✅ (N426)** | R · E new bill · S daily | duplicates · AP control |
| [US-07](../usecases/US/us-07-duplicate-vendor-payment.md) Duplicate vendor payment | "Is any vendor being paid twice?" | ✅ 0 findings; standing orders suppressed | ✅ | Hold: **T3.3 ✅ (N426)** | R · E new bill · S daily | duplicates · AP control |
| [UC-11](../usecases/IN/uc-11-three-way-match.md) Three-way match | "Were the goods we're being billed for actually received?" | 🟡 Two-way ✅ via `bill_match`; receipts not readable | ✅ | Inventory receipts: **T2.2 ✅ (N426)**, F1 ✅ (N173) | R · E bill with a PO · S daily | three-way · movement |
| [US-09](../usecases/US/us-09-three-way-match.md) Three-way match | "Were the goods we're being billed for actually received?" | ✅ (N2 appears fixed) | ✅ | — | R · E bill with a PO · S daily | three-way · movement |
| [UC-43](../usecases/IN/uc-43-bank-to-payables-reconciliation.md) Bank-to-payables reconciliation | "Does every vendor payment in the bank match a payment in our books, and the other way round?" | ✅ Live: ₹56.2 lakh unmatched | ✅ | — (`matched` without a voucher: candidate bug, **not filed**) | R · E bank debit · S weekly + month-end | bank-recon · AP control |
| [US-19](../usecases/US/us-19-bank-to-payables-reconciliation.md) Bank-to-payables reconciliation | "Does every vendor payment in the bank match a payment in our books, and the other way round?" | ✅ 6 of 9 payments unmatched | ✅ | — | R · E bank debit · S weekly | bank-recon · AP control |

## J · Vendor and payment controls

*Paying the right vendor the right amount at the right time, with the record to prove it.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-04](../usecases/IN/uc-04-msme-45-day-exposure.md) MSME 45-day exposure | "Which small suppliers are we about to pay late, and what will it cost us?" | ✅ 7 live breaches | ✅ | Udyam check: **T4.2 ✅ (N426)**; MSME tracking **F8 ✅ (N173)** | R · S daily | msme · AP control |
| [UC-40](../usecases/IN/uc-40-vendor-master-audit.md) Vendor master audit | "Are our vendor records complete and trustworthy enough to pay against, claim credit on and deduct tax for?" | ✅ Live: no vendor has a GSTIN, PAN or bank details | ✅ | GSTIN/PAN/Udyam validation: **T4.2 ✅ (N426)**; bank validation **F4 ✅ (N173)** | R · E vendor change, payment · S weekly | vendor-master · AP control |
| [US-16](../usecases/US/us-16-vendor-master-audit.md) Vendor master audit | "Are our vendor records (TIN, W-9, 1099 settings) complete enough to pay and report on?" | ✅ | ✅ | — (no IRS TIN matching on the platform) | R · E vendor change, payment · S weekly | vendor-master · AP control |
| [UC-41](../usecases/IN/uc-41-unapplied-vendor-credits.md) Unapplied vendor credits | "Are we about to pay vendors in full while they owe us money from credit notes or advances?" | ✅ Live: ₹4.91 lakh applicable now | ✅ | — (`VendorCredit.apply_to_bill` exists; the agent doesn't write) | R · E bill approved, new vendor credit · S weekly | vendor-balance · AP control |
| [US-17](../usecases/US/us-17-unapplied-vendor-credits.md) Unapplied vendor credits | "Are we about to pay vendors in full while they owe us money from credits?" | ✅ 0 cases | ✅ | — | R · E bill approved, new vendor credit · S weekly | vendor-balance · AP control |
| [UC-42](../usecases/IN/uc-42-payment-run-prioritisation.md) Payment run prioritisation | "We can't pay everything this week. Which bills should we pay first to avoid penalties and lost credit, and which should we hold?" | ✅ | ✅ | AP ageing as MCP: **T1.1 ✅ (N426)**, optional | R · E MSME bill at day 40, bill at day 170 · S weekly | payment-run · AP control |
| [US-18](../usecases/US/us-18-payment-run-prioritisation.md) Payment run prioritisation | "Which bills should we pay first this week, and which should we hold or withhold on?" | ✅ | ✅ | — | R · S weekly | payment-run · AP control |
| [US-21](../usecases/US/us-21-unclaimed-property-escheat.md) Unclaimed property (escheat) | "Do we hold money owed to vendors that nobody has claimed, and must we report it to a state?" | ✅ 0 cases | ✅ | Returned-payment status: ❌ **not requested** (minor) | R · S monthly + annual | escheat · AP control |

## K · Approvals and segregation of duties

*Is the approval control actually working?*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-06](../usecases/IN/uc-06-approval-sla-audit.md) Approval SLA and SoD | "Who approved what, was it within policy, and did anyone approve their own bill?" | ✅ (policy check partial) | ❌ `ApprovalPolicy.list` | **T2.1 ✅ (N426)** | R · S weekly | approval-sla · AP control |
| [US-08](../usecases/US/us-08-approval-sla-audit.md) Approval SLA and SoD | "Who approved what, was it within policy, and did anyone approve their own bill?" | ✅ | ✅ (policy unreadable, as UC-06) | **T2.1 ✅ (N426)** | R · S weekly | approval-sla · AP control |
| [UC-44](../usecases/IN/uc-44-approval-threshold-splitting.md) Approval threshold splitting | "Is anyone splitting purchases into smaller bills so each one stays under the approval limit?" | 🟡 Threshold from config | ❌ `ApprovalPolicy.list` | **T2.1 ✅ (N426)** | R · E new bill · S weekly | threshold-split · AP control |
| [US-20](../usecases/US/us-20-approval-threshold-splitting.md) Approval threshold splitting | "Is anyone splitting purchases to stay under the approval limit?" | ✅ Threshold inferred at $10,000 | ✅ | **T2.1 ✅ (N426)** would confirm the limit | R · E new bill · S weekly | threshold-split · AP control |

## L · Period integrity

*Has anything been entered into a month we've already reported or closed?*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-28](../usecases/IN/uc-28-late-entered-documents.md) Late-entered documents | "Has anyone entered or back-dated a document into a month we've already filed or closed?" | ✅ 0 breaches | ✅ | Amendments: GST-32 platform-documented, **don't file** | R · E document dated in a closed period · S daily | period-integrity · compliance calendar |
| [US-15](../usecases/US/us-15-late-entered-documents.md) Late-entered documents | "Has anyone entered or back-dated a document into a month we've already reported?" | ✅ Live: 147 invoices back-entered | ✅ | Return record: ❌ **not requested** (as US-14) | R · E back-dated document · S daily | period-integrity · compliance calendar |

## M · Goods movement (manufacturing)

*Documents that must accompany or track goods.*

| Use case | Sample question | Achievable? | MCP tools | Gap → already requested? | Modes | Playbook · category |
|---|---|---|---|---|---|---|
| [UC-12](../usecases/IN/uc-12-eway-bill-coverage.md) E-way bill coverage | "Is anything moving on the road right now without valid documentation?" | ✅ Built in the harness | ✅ | — (e-way bill generation: GST-29 platform-documented) | R · E invoice / challan despatched · S several times daily | eway · movement |
| [UC-10](../usecases/IN/uc-10-job-work-itc04.md) Job work / ITC-04 | "What have we sent out for job work that hasn't come back, and when does it become a taxable supply?" | 🟡 Return tracking missing | ✅ | Return tracking: **T4.5 ✅ (N426)**; F19 not filed separately | R · S monthly + 30 Sep / 31 Mar | job-work · movement |

---

## Not yet requested — candidates to file

| # | Ask | Unblocks |
|---|---|---|
| 1 | `Invoice.sales_channel` / marketplace id, plus marketplace settlement import (**F22**, India and US together) | UC-36, US-12 |
| 2 | Sales-tax return / payment record, or populate `TaxNexus.next_filing_due` | US-14, US-15 |
| 3 | 1099 summary report (`/api/cpa/reports/1099-summary`) as an MCP tool | US-06 |
| 4 | Receiving GSTIN / despatch location on documents | UC-30 |
| 5 | Exemption certificates issued **to** vendors; W-8 fields on `Party` | US-11, US-22 |
| 6 | `Notification.create`, and a structured choice field on `AgentEscalation` resolution | All scheduled and event alerts; the hold-approval flow |
| 7 | Read access to `Asset` (capital-goods disposal, s.18(6); catalogue §6) | New use case, not yet specified |

**F19, F20, F21** are marked "not filed" in the tracker, but their tool shapes are already inside **N426**
(T4.5, T4.3, T4.4). Filing them again risks a duplicate (agentswitch_submissions §B). Recommend
commenting on N426 instead.

**Candidate bug reports** surfaced by these specs are listed in
[`../usecases/IN/README.md`](../usecases/IN/README.md) ("New observations from the 2026-10-04 pull").

## Platform-documented gaps — do not file

GST-28 e-invoicing (UC-29) · GST-39 GSTR-9 (UC-31) · GST-32 amendments (UC-28) · GST-18 TDS
returns/challans (UC-27, UC-39) · GST-29 e-way bill generation (UC-12) · `tax_rate_service` (US-05,
US-13) · `consolidation` (UC-30) · `form_1099_filing` (US-06).
