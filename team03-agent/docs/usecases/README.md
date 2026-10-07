# Use cases — Payables & Tax Agent on AgentSwitch (India and US, five domains)

**Team 03 · Seat 03 · catalogue updated 2026-10-04**

This folder holds every AP and tax use case the agent can serve on AgentSwitch, for both tenants and all
five domains. Each is one specification file. Every use case is either:
- **specified** here;
- recorded as an **extension** of an existing spec (§5);
- **catalogued as blocked** before any data exists (§6);
- or **excluded with a reason** (§7).

| Folder | Tenant | Regime | Specs |
|---|---|---|---|
| [`IN/`](IN/README.md) | Suryodaya Precision Works Pvt. Ltd. | `gst` (India) | **UC-01 … UC-44** (UC-01–22 from [`spec.md`](../planning/spec.md); UC-23–44 added 2026-10-04) |
| [`US/`](US/README.md) | Keystone Precision Works LLC | `sales_use_tax` (US) | **US-01 … US-22** (US-11–22 added 2026-10-04) |

**How the two folders relate.** A use case is written once per jurisdiction where it applies.
Regime-agnostic checks get a short US file that records only what differs. The IN→US mapping is in
[`US/README.md`](US/README.md#mapping-from-the-india-use-cases). In the agent, a manifest declares
`tax_regimes: [gst]`, `[sales_use_tax]` or `[all]`, and the router picks by the tenant's locale
([`agent_design.md` §4.12](../planning/agent_design.md)).

**Feasibility per use case:** achievable?, MCP tools present?, already requested?, sample question, mode
and playbook, grouped by similar use cases, are in
[`../planning/usecase_feasibility.md`](../planning/usecase_feasibility.md).

**Design labels:** where a spec cites **G1–G14** (e.g. "watcher transitions (G4)"), the label is defined
in [`../planning/agent_design.md` §2c](../planning/agent_design.md#2c-design-additions-cited-by-the-use-case-specs-g1g14-new-2026-10-04).

**Verdicts:**
- 🟢 buildable now, data verified;
- 🟡 partial (a derivation, a data caveat, or one leg blocked);
- 🔴 blocked by the platform;
- ⚪ spec only (the fields exist, but no tenant of that domain or kind exists).

---

## 1. Totals

| | 🟢 | 🟡 | 🔴 | ⚪ | Total |
|---|---|---|---|---|---|
| India | 20 | 18 | 5 | 1 | **44** |
| US | 15 | 3 | 0 | 4 | **22** |
| **All** | **35** | **21** | **5** | **5** | **66** |

**Playbooks: about 46.** Several specs run the same algorithm with a regime or vertical strategy, and
share one playbook (§4). Both live tenants are manufacturers (`OrgProfile.industry = manufacturing`), so
school, clinic, retail and agency checks route as `spec` until such a tenant exists.

---

## 2. Coverage: domain × jurisdiction

| Domain | India | US |
|---|---|---|
| **All five** (cross-cutting) | UC-01 Rule 37 · 02 blocked credit · 03 RCM · 04 MSME · 05 duplicates · 06 approval SLA · 09 TDS · 13 194Q · 19 credit-note window · 21 import RCM · **23 liability · 24 unclaimed credit** · 25 vendor credit notes · 26 GSTR-1 · 27 filing timeliness · 28 late-entered documents · 29 turnover thresholds · 31 annual return · 33 expense credit · 38 cash limits · 39 TDS setup · 40 vendor master · 41 unapplied credits · 42 payment run · 43 bank reconciliation · 44 threshold splitting | US-01 **liability** · 02 use tax · 03 nexus · 04 exemption certificates · 05 rates · 06 1099 · 07 duplicates · 08 approval SLA · 09 three-way · 10 credit memos · **11 tax overpaid (unclaimed)** · 14 filing calendar · 15 late-entered documents · 16 vendor master · 17 unapplied credits · 18 payment run · 19 bank reconciliation · 20 threshold splitting · 21 unclaimed property |
| **Manufacturing** | UC-10 job work · 11 three-way match · 12 e-way bill · 30 multiple registrations · 32 inverted-duty / SEZ refund | US-11 manufacturing exemption · US-09 three-way · US-22 foreign royalties |
| **School** | UC-07 exempt split · 08 Rule 42 · **34 exempt inward services** | US-11 nonprofit/government purchases · US-04 exempt buyers · US-13 school sales |
| **Clinic** | UC-14 exempt split · 15 Rule 42/43 · 16 expiry | US-11 Rx/medical purchases · US-13 Rx/OTC/devices · US-06 medical payments (§5) |
| **Retail** | UC-16 expiry · 17 composition · 18 HSN rates · **36 e-commerce TCS** · 38 cash · 26 B2C tables | **US-12 marketplace** · US-13 holidays/shipping · US-04 resale certificates · US-11 resale purchases |
| **Agency** | UC-20 export/LUT · 21 import RCM · 22 advances · 32 export refund · **35 pure agent** · **37 s.195** | US-13 services/digital · US-06 freelancers (1099-NEC) · **US-22 foreign freelancers (1042-S)** |

**The Core Challenge, per jurisdiction:**

| Question | India | US |
|---|---|---|
| What is our tax liability this period? | UC-23 | US-01 |
| What is unclaimed? | UC-24 (credit), UC-32 (refund) | US-11 (overpaid tax) |
| Is any vendor being paid twice? | UC-05 + UC-43 | US-07 + US-19 |

---

## 3. Full catalogue

Category key:
- **CT** core tax
- **IT** input tax / purchase taxability
- **OT** output tax
- **CC** compliance calendar
- **MV** movement and documents
- **WH** withholding / income tax
- **AP** payables control
- **RG** registrations

### India

| ID | Use case | Domains | Cat. | Verdict | Playbook |
|---|---|---|---|---|---|
| [UC-01](IN/uc-01-rule-37-itc-reversal.md) | Rule 37 180-day credit reversal | all | IT | 🟢 | rule37 |
| [UC-02](IN/uc-02-blocked-credit-audit.md) | Blocked credit s.17(5) | all | IT | 🟢 | blocked-credit |
| [UC-03](IN/uc-03-rcm-self-invoicing.md) | RCM self-invoicing | all | IT | 🟢 | rcm |
| [UC-04](IN/uc-04-msme-45-day-exposure.md) | MSME 45-day exposure | all | AP | 🟢 | msme |
| [UC-05](IN/uc-05-duplicate-vendor-payment.md) | Duplicate vendor payment | all | AP | 🟡 | duplicates |
| [UC-06](IN/uc-06-approval-sla-audit.md) | Approval SLA and SoD | all | AP | 🟢 | approval-sla |
| [UC-07](IN/uc-07-school-exempt-taxable-split.md) | School exempt/taxable split | school | OT | 🟡 | exempt-split |
| [UC-08](IN/uc-08-rule-42-apportionment-school.md) | Rule 42 apportionment, school | school | IT | 🔴 (compute 🟢) | apportionment |
| [UC-09](IN/uc-09-vendor-tds-verification.md) | Vendor TDS verification | all | WH | 🟢 | tds |
| [UC-10](IN/uc-10-job-work-itc04.md) | Job work / ITC-04 | mfg | MV | 🟡 | job-work |
| [UC-11](IN/uc-11-three-way-match.md) | Three-way match | mfg, retail | MV | 🟡 | three-way |
| [UC-12](IN/uc-12-eway-bill-coverage.md) | E-way bill coverage | mfg, retail | MV | 🟢 | eway |
| [UC-13](IN/uc-13-194q-206c-thresholds.md) | 194Q / 206C(1H) thresholds | all | WH | 🟡 | tds |
| [UC-14](IN/uc-14-clinic-exempt-taxable-split.md) | Clinic exempt/taxable split | clinic | OT | 🟡 | exempt-split |
| [UC-15](IN/uc-15-rule-42-43-apportionment-clinic.md) | Rule 42/43 apportionment, clinic | clinic | IT | 🔴 (compute 🟢) | apportionment |
| [UC-16](IN/uc-16-drug-expiry-blocked-credit.md) | Expiry → blocked credit | clinic, retail | IT | 🟡 | expiry |
| [UC-17](IN/uc-17-composition-scheme.md) | Composition scheme | retail | RG | 🔴 (sub-check 🟢) | composition |
| [UC-18](IN/uc-18-hsn-rate-consistency.md) | HSN rate consistency | retail, all | OT | 🟢 | hsn-rate |
| [UC-19](IN/uc-19-credit-note-time-limit.md) | Credit-note s.34(2) window | all | OT | 🟢 | credit-note-window |
| [UC-20](IN/uc-20-export-lut-tracking.md) | Export / LUT | agency | OT | 🟡 | export-lut |
| [UC-21](IN/uc-21-import-of-services-rcm.md) | Import of services RCM | agency, all | IT | 🟡 | rcm |
| [UC-22](IN/uc-22-advance-receipt-gst.md) | Advance-receipt GST | agency | OT | 🟡 | advances |
| [UC-23](IN/uc-23-period-gst-liability.md) | **Period GST liability (GSTR-3B)** | all | CT | 🟡 | period-liability |
| [UC-24](IN/uc-24-unclaimed-itc-ims-2b.md) | **Unclaimed / at-risk credit (IMS, GSTR-2B, s.16(4))** | all | CT | 🟡 | itc-entitlement |
| [UC-25](IN/uc-25-vendor-credit-debit-notes-itc.md) | Inward credit/debit notes | all | IT | 🟢 | vendor-notes |
| [UC-26](IN/uc-26-gstr1-readiness.md) | GSTR-1 readiness and tax head | all | OT | 🟡 | gstr1 |
| [UC-27](IN/uc-27-return-filing-timeliness.md) | Return filing timeliness | all | CC | 🟢 | filing-calendar |
| [UC-28](IN/uc-28-late-entered-documents.md) | Late-entered documents | all | CC | 🟢 | period-integrity |
| [UC-29](IN/uc-29-turnover-based-obligations.md) | Turnover-based obligations | all | CC | 🟢 | turnover |
| [UC-30](IN/uc-30-multiple-registrations.md) | Multiple registrations, transfers, ISD | mfg, retail | RG | 🟡 | registrations |
| [UC-31](IN/uc-31-annual-return-reconciliation.md) | Annual return GSTR-9/9C | all | CC | 🔴 (compute 🟡) | annual-return |
| [UC-32](IN/uc-32-itc-refund-zero-rated-inverted.md) | Credit refund, Rule 89(4)/(5) | agency, mfg, retail | IT | 🟡 | refund |
| [UC-33](IN/uc-33-expense-claims-itc.md) | Expense claims GST credit | all | IT | 🟢 | expense-credit |
| [UC-34](IN/uc-34-school-exempt-inward-services.md) | School: exempt inward services | school | IT | ⚪ | school-inward |
| [UC-35](IN/uc-35-agency-pure-agent-reimbursements.md) | Agency: pure-agent recharges | agency | OT | 🟡 | recharges |
| [UC-36](IN/uc-36-ecommerce-tcs-s52.md) | Retail: e-commerce TCS s.52 / s.9(5) | retail | OT | 🔴 F22 | marketplace |
| [UC-37](IN/uc-37-non-resident-payments-tds-195.md) | Non-resident payments s.195 | agency, mfg | WH | 🟡 | tds |
| [UC-38](IN/uc-38-cash-payment-limits.md) | Cash payments s.40A(3) | all | WH | 🟢 | cash-limit |
| [UC-39](IN/uc-39-tds-deductor-setup.md) | TDS deductor setup and sections | all | WH | 🟢 | tds |
| [UC-40](IN/uc-40-vendor-master-audit.md) | Vendor master audit | all | AP | 🟢 | vendor-master |
| [UC-41](IN/uc-41-unapplied-vendor-credits.md) | Unapplied vendor credits | all | AP | 🟢 | vendor-balance |
| [UC-42](IN/uc-42-payment-run-prioritisation.md) | Payment run prioritisation | all | AP | 🟢 | payment-run |
| [UC-43](IN/uc-43-bank-to-payables-reconciliation.md) | Bank-to-payables reconciliation | all | AP | 🟢 | bank-recon |
| [UC-44](IN/uc-44-approval-threshold-splitting.md) | Approval threshold splitting | all | AP | 🟡 | threshold-split |

### US

| ID | Use case | Domains | Cat. | Verdict | Playbook |
|---|---|---|---|---|---|
| [US-01](US/us-01-period-sales-use-tax-liability.md) | **Period sales and use tax liability** | all | CT | 🟢 | period-liability |
| [US-02](US/us-02-consumer-use-tax-on-purchases.md) | Consumer use tax on untaxed purchases | all | IT | 🟡 | purchase-taxability |
| [US-03](US/us-03-economic-nexus-monitoring.md) | Economic nexus | all | CC | 🟢 | nexus |
| [US-04](US/us-04-exemption-certificate-coverage.md) | Exemption certificate coverage | all, retail, school | OT | 🟢 | exemption-certs |
| [US-05](US/us-05-sourcing-and-rate-correctness.md) | Sourcing and rate correctness | all | OT | 🟡 | rates |
| [US-06](US/us-06-form-1099-readiness.md) | Form 1099 and backup withholding | all, agency | WH | 🟢 | payee-withholding |
| [US-07](US/us-07-duplicate-vendor-payment.md) | Duplicate vendor payment | all | AP | 🟢 | duplicates |
| [US-08](US/us-08-approval-sla-audit.md) | Approval SLA and SoD | all | AP | 🟢 | approval-sla |
| [US-09](US/us-09-three-way-match.md) | Three-way match | mfg, retail | MV | 🟢 | three-way |
| [US-10](US/us-10-credit-memo-refund-window.md) | Credit memos and refund windows | all | OT | ⚪ | credit-note-window |
| [US-11](US/us-11-sales-tax-on-exempt-purchases.md) | **Tax paid on exempt purchases (unclaimed)** | mfg, school, clinic, retail | CT/IT | 🟢 | purchase-taxability |
| [US-12](US/us-12-marketplace-facilitator-sales.md) | Marketplace facilitator sales | retail | OT | ⚪ | marketplace |
| [US-13](US/us-13-taxability-services-digital-holidays.md) | Taxability: services, digital, medical, holidays | agency, clinic, retail, school | OT | ⚪ (🟢 goods) | taxability |
| [US-14](US/us-14-sales-tax-filing-calendar.md) | Filing calendar and timeliness | all | CC | 🟡 | filing-calendar |
| [US-15](US/us-15-late-entered-documents.md) | Late-entered documents | all | CC | 🟢 | period-integrity |
| [US-16](US/us-16-vendor-master-audit.md) | Vendor master audit (TIN, W-9) | all | AP | 🟢 | vendor-master |
| [US-17](US/us-17-unapplied-vendor-credits.md) | Unapplied vendor credits | all | AP | 🟢 | vendor-balance |
| [US-18](US/us-18-payment-run-prioritisation.md) | Payment run prioritisation | all | AP | 🟢 | payment-run |
| [US-19](US/us-19-bank-to-payables-reconciliation.md) | Bank-to-payables reconciliation | all | AP | 🟢 | bank-recon |
| [US-20](US/us-20-approval-threshold-splitting.md) | Approval threshold splitting | all | AP | 🟢 | threshold-split |
| [US-21](US/us-21-unclaimed-property-escheat.md) | Unclaimed property (escheat) | all | AP | 🟢 | escheat |
| [US-22](US/us-22-foreign-vendor-withholding.md) | Foreign vendors: Chapter 3 / 1042-S | agency, mfg | WH | ⚪ | payee-withholding |

---

## 4. Playbook grouping

A playbook is the code that answers a use case: manifest + fetch + pure rules. Specs share a playbook
when the **algorithm is the same** and only a regime table or vertical rule set differs:

| Shared playbook | Specs |
|---|---|
| period-liability | UC-23 + US-01 |
| purchase-taxability | US-02 + US-11 |
| duplicates | UC-05 + US-07 |
| approval-sla | UC-06 + US-08 |
| three-way | UC-11 + US-09 |
| rcm | UC-03 + UC-21 |
| exempt-split | UC-07 + UC-14 |
| apportionment | UC-08 + UC-15 |
| tds | UC-09 + UC-13 + UC-37 + UC-39, one section table |
| payee-withholding | US-06 + US-22 |
| filing-calendar | UC-27 + US-14 |
| period-integrity | UC-28 + US-15 |
| marketplace | UC-36 + US-12 |
| vendor-master | UC-40 + US-16 |
| vendor-balance | UC-41 + US-17 |
| payment-run | UC-42 + US-18 |
| bank-recon | UC-43 + US-19 |
| threshold-split | UC-44 + US-20 |
| credit-note-window | UC-19 + US-10 (optional) |

66 specs − 20 shared = **46 playbooks** (45 if UC-19 and US-10 share).

---

## 5. Extensions to existing specs

These are real use cases that belong inside an existing spec's rules or table rather than in a new file.
They are recorded here for the team member who next edits each spec.

| Extend | Add | Domains | Live hint (2026-10-04) |
|---|---|---|---|
| UC-01 | Re-availment of reversed credit after late payment (UC-01 §10) | all | Needs stored reversal state |
| UC-03 | Lookup-table rows (*our understanding, caveat*): **rent of commercial property from an unregistered person** (Notif. 09/2024-CT(R), from 10 Oct 2024); **security services** by a non-body-corporate (Notif. 29/2018-CT(R)); renting of motor vehicles | school, clinic, retail, agency | 7 rent expenses with no GST treatment ("Monthly rent for HQ office") |
| UC-04 | **MSME Form-1** half-yearly return of dues past 45 days (MCA order 2019; 30 Apr / 31 Oct); **MSMED s.23**: interest under s.16 is not deductible | all | 6 "MSME Interest (Section 16)" expenses, ₹2,60,427.54 |
| UC-13 | **s.206C(1) TCS on scrap sales**; the s.194Q buyer-turnover gate (> ₹10 Cr, from UC-29) | mfg | `TaxExemption` row "Scrap sold to an unregistered buyer" |
| UC-16 | Other s.17(5)(h) events: theft, destruction, free samples, gifts | retail, mfg, clinic | Needs stock adjustments (§6) |
| UC-18 | Inward rate check: vendor overcharge is pure cost for exempt-output schools and clinics | school, clinic | — |
| UC-19 | s.15(3)(b): post-sale discount credit notes must be pre-agreed and linked to invoices | retail, all | — |
| US-02 | Extend to `Expense` | all | 78 expenses, $0 tax: Microsoft 365, equipment leases, repairs |
| US-04 | Nonprofit, government, manufacturing and Rx certificate reasons | school, clinic, mfg | `exemption_reason` options include all four |
| US-06 | 1099-MISC box 6 medical payments, reportable even to corporations; *our understanding (caveat):* Pennsylvania withholding on non-employee compensation to non-residents | clinic, all | — |

---

## 6. Catalogued but not specified: blocked before any data exists

| Use case | Jurisdiction / domains | What blocks it |
|---|---|---|
| Capital goods disposal: credit payback (s.18(6)) | IN · mfg, clinic | `Asset` exists in the schema (`bill_id`, `disposal_value`, status) but isn't exposed to `finance_user`. Request `Asset.list` |
| Supplier GSTIN cancelled or suspended → credit at risk | IN · all | No GSTN verification API (UC-40 §10) |
| Stock written off, lost or stolen → credit reversal | IN · retail, mfg | `StockEntry` / `Batch` / `StockLedger` not readable (UC-16) |
| Use tax on inventory withdrawn for own use | US · retail, mfg | Same stock access gap |

---

## 7. Considered and excluded

| Area | Why it isn't an AP & Tax use case here |
|---|---|
| Payroll taxes: TDS on salary (s.192), PF/ESI/PT, US payroll | `SalarySlip` is prohibited for Seat 03 |
| Tax review of contracts | `Contract` is prohibited |
| *Filing* returns, generating IRNs, paying challans | No filing, IRP or challan integration (GST-28, GST-39, GST-18). The agent detects and reports: UC-27/29/31/39, US-14 |
| Customs duty and IGST on imported goods | No Bill of Entry entity |
| Income-tax provision, deferred tax (Ind AS 12 / ASC 740), advance tax, MAT | GL / tax provision (Team 01), not payables |
| Meals and entertainment deductibility (IRC §274) | Income-tax provision. 8 US meal expenses exist, but there's no AP obligation |
| Ohio CAT, gross receipts and property taxes | Business taxes outside AP |
| Equalisation levy on online advertising | *Our understanding:* abolished from 1 April 2025 (noted in UC-37) |
| s.206AB / s.206CCA higher rates for non-filers | *Our understanding:* omitted from 1 April 2025 |
| Receivable-side compliance: s.269ST cash receipts, customer credit balances | Team 02 (receivables) |
| School trust accounting (s.11/12AB) | GL, not AP |
| Anti-profiteering (s.171) | Authority-driven; not checkable from ledger data |

---

## 8. Platform changes that would unblock more

Feed [`../submissions/requested_tools.md`](../submissions/requested_tools.md):

| Request | Unblocks |
|---|---|
| Read `ApprovalPolicy` | UC-06, UC-44 |
| GSTR-2B / IMS line data | UC-24, UC-31 |
| Read `Asset`, `StockEntry`, `Batch` | §6 rows, UC-16 |
| `SalesTaxReturn` record, or `TaxNexus.next_filing_due` populated | US-14, US-15 |
| `Invoice.sales_channel` + marketplace settlement import | UC-36, US-12 (F22) |
| Despatch location / receiving GSTIN on documents | UC-30 |
| Certificates issued *to* vendors; W-8 on `Party`; LUT validity dates | US-11, US-22, UC-20, UC-32 |
| GSTIN verification endpoint | UC-40, §6 |
| `Invoice.expense_id` set by "bill to customer" | UC-35 |

**Vertical routing:** `OrgProfile.industry` (`education`, `healthcare`, `retail`, `consulting`,
`manufacturing`, …) states the vertical directly. Recommend routing on it, with the `Item`-mix
inference (spec.md §7.1) as a cross-check.
