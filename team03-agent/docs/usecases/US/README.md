# US use cases — Keystone Precision Works LLC (sales & use tax)

**Team 03 · Seat 03 Payables & Tax · live evidence pulled 2026-10-03**

US counterparts of the India use cases in [`../IN/`](../IN/README.md). They use the
same ten-section template ([`../../assignment.md`](../../planning/assignment.md) §3) plus
**§11 Live evidence**, and the same finding row (IN UC-01 §7).

**Tenant at pull time.** Keystone Precision Works LLC
(`c1e47d8d-b849-4187-9a32-4103d3dece4a`), `https://class.agentswitch.theschoolofai.in`,
signed in as `finance_user`. Locale: country `US`, `tax_regime: sales_use_tax`,
`us_gaap`, USD, fiscal year = calendar 2026, timezone America/New_York. Feature flags:
`sales_tax_jurisdictions`, `sales_tax_nexus`, `exemption_certificates` and `form_1099`
on; every GST flag off.

Records: 101 Bill · 158 Invoice (all receivable) · 120 Party · 67 PaymentMade ·
85 PurchaseOrder · 4 RecurringBill · 4 TaxNexus (IL, MI, PA, OH) · 4 TaxJurisdiction ·
1 ExemptionCertificate · 123 ApprovalRequest · 602 ApprovalLog · **0** CreditNote ·
**0** Tax · **0** TaxExemption.

---

## Index

| US | Title | IN counterpart | Verdict | Headline from live data |
|---|---|---|---|---|
| [01](us-01-period-sales-use-tax-liability.md) | Period sales & use tax liability | period liability (harness plan §6.1) | 🟢 | Our recompute matches the platform's liability report **to the cent** in all 4 jurisdictions (YTD $226,488.27). Use tax accrued: $0 (→ US-02) |
| [02](us-02-consumer-use-tax-on-purchases.md) | Consumer use tax on untaxed purchases | UC-03, UC-21 (self-assessed tax) | 🟡 | 81 bills, $588,555.24, **no vendor tax and no use tax on any**. $260,985 is outside "production material" → up to **$16,964.03** use tax, subject to classification |
| [03](us-03-economic-nexus-monitoring.md) | Economic nexus threshold monitoring | UC-13 (cumulative thresholds) | 🟢 | Platform YTD counters now equal our recompute (**N4 appears fixed**). No sales outside the 3 registered states |
| [04](us-04-exemption-certificate-coverage.md) | Exemption certificate coverage | UC-07, UC-20 (exempt / zero-rated) | 🟢 | 31 exempt invoices ($570,195.62), **31/31 covered** by a valid resale certificate valid to 2029-04-01 |
| [05](us-05-sourcing-and-rate-correctness.md) | Sales tax sourcing & rate correctness | UC-18 (rate correctness) | 🟡 | Arithmetic exact on every line. But **36 OH invoices charge Stark County tax ($7,919.93) to customers outside Stark County**, while jurisdictions are configured `sourcing: destination` |
| [06](us-06-form-1099-readiness.md) | Form 1099 readiness & backup withholding | UC-09 (TDS) | 🟢 | 2 reportable vendors at the 2026 **$2,000** threshold; **1 needs a W-9** (Canton Industrial Consulting, $7,800) |
| [07](us-07-duplicate-vendor-payment.md) | Duplicate vendor payment | UC-05 (same check) | 🟢 | 0 suspicious pairs. 15 groups of identical bills are fortnightly standing orders with distinct POs. Recurring runaway bills are now void/draft |
| [08](us-08-approval-sla-audit.md) | Approval SLA & segregation-of-duties audit | UC-06 (same check) | 🟢 | **0/93** resolved requests with a wrong `is_overdue` (filed N1 had 8, so it **appears fixed**); 0 self-approvals |
| [09](us-09-three-way-match.md) | Three-way match | UC-11 (same check) | 🟢 | 81/81 PO bills within tolerance; `recorded_status` **now persisted** (filed N2 had null ×81, so it **appears fixed**) |
| [10](us-10-credit-memo-refund-window.md) | Sales tax on credit memos & refund windows | UC-19 (credit-note time limit) | ⚪ spec | No CreditNote exists on the tenant; the liability report shows `credited_sales: 0` |

### Added 2026-10-04: US-11 … US-22, from the full catalogue

From the catalogue in [`../README.md`](../README.md); live evidence pulled 2026-10-04.

| US | Title | IN counterpart | Verdict | Headline from live data |
|---|---|---|---|---|
| [11](us-11-sales-tax-on-exempt-purchases.md) | Sales tax paid on exempt purchases (refunds) | UC-34, UC-32 | 🟢 | 0 bills or expenses carry vendor tax, so nothing to refund. US-02 found the opposite problem |
| [12](us-12-marketplace-facilitator-sales.md) | Marketplace facilitator sales | UC-36 | ⚪ spec | No sales channel on `Invoice`; Keystone sells direct |
| [13](us-13-taxability-services-digital-holidays.md) | Taxability by state: services, digital, medical, shipping, holidays | UC-18 | ⚪ spec / 🟢 goods | All 28 items are goods (taxable in OH/MI/PA), `tax_code` null; no services sold |
| [14](us-14-sales-tax-filing-calendar.md) | Filing calendar and timeliness | UC-27 | 🟡 | MI/PA Q3 due 2026-10-20, OH September due 2026-10-23. **No filing record exists**; `next_filing_due` null on 4 of 4 |
| [15](us-15-late-entered-documents.md) | Documents entered late into past periods | UC-28 | 🟢 | **147 invoices ($220,089.85 tax) entered 2026-09-16 for January–August.** 0 periods ever closed |
| [16](us-16-vendor-master-audit.md) | Vendor master audit (TIN, W-9, 1099 flags) | UC-40 | 🟢 | `tin` empty in list output on 8 of 8; 1 W-9 missing; Hartville set to box MISC-1 (Rents) |
| [17](us-17-unapplied-vendor-credits.md) | Unapplied vendor credits and advances | UC-41 | 🟢 | 0 vendor credits, 0 advances → 0 findings |
| [18](us-18-payment-run-prioritisation.md) | Payment run prioritisation | UC-42 | 🟢 | 14 open ($115,392.56); **13 overdue**, the oldest 141 days |
| [19](us-19-bank-to-payables-reconciliation.md) | Bank-to-payables reconciliation | UC-43 | 🟢 | **6 of 9 payments in the bank window ($45,825) have no matching debit**; 1 unidentified $3,000 debit |
| [20](us-20-approval-threshold-splitting.md) | Approval threshold splitting | UC-44 | 🟢 | Threshold **inferred at $10,000** from two policy bands; 0 candidates (standing orders excluded) |
| [21](us-21-unclaimed-property-escheat.md) | Unclaimed property (escheat) on vendor payments | — | 🟢 | 0 candidates: all payments are bank transfers in 2026; earliest dormancy 2029 |
| [22](us-22-foreign-vendor-withholding.md) | Foreign vendors: Chapter 3 withholding, Form 1042-S | UC-37 | ⚪ spec | All 8 vendors are in Ohio; the INR bills are the B8 defect, not foreign vendors |

---

## Mapping from the India use cases

| IN | Title | US | Why |
|---|---|---|---|
| UC-01 | Rule 37 180-day ITC reversal | — | No input tax credit in US sales tax |
| UC-02 | Blocked credit s.17(5) | (US-02) | No credit to block. The nearest US question is whether a purchase owes use tax |
| UC-03 | RCM self-invoicing | **US-02** | Both are tax the *buyer* self-assesses |
| UC-04 | MSME 45-day | — | No federal private-sector prompt-payment statute. The Prompt Payment Act binds federal agencies only |
| UC-05 | Duplicate payment | **US-07** | Regime-agnostic |
| UC-06 | Approval SLA audit | **US-08** | Regime-agnostic |
| UC-07 | School exempt/taxable split | **US-04** | US exemptions are certificate-driven per customer, not per item |
| UC-08 | Rule 42 apportionment | — | No input credit to apportion |
| UC-09 | TDS verification | **US-06** | The US analogue is 1099 information reporting plus backup withholding |
| UC-10 | Job work ITC-04 | — | No deemed-supply rule |
| UC-11 | Three-way match | **US-09** | Regime-agnostic |
| UC-12 | E-way bill | — | No US equivalent. Note filed B9: Keystone still exposes 8 `EWayBill.*` tools with `eway_bill=false` |
| UC-13 | 194Q / 206C(1H) thresholds | **US-03** | Both monitor a cumulative sales threshold that starts an obligation |
| UC-14 | Clinic exempt/taxable split | (US-04) | Healthcare exemptions are certificate- or item-based; no clinic tenant |
| UC-15 | Rule 42/43 clinic | — | No input credit |
| UC-16 | Expiry → blocked credit | — | A write-off has no sales-tax credit consequence |
| UC-17 | Composition scheme | — | No US equivalent |
| UC-18 | HSN rate consistency | **US-05** | Rate by jurisdiction instead of by product code |
| UC-19 | Credit-note time limit | **US-10** | State refund windows instead of s.34(2) |
| UC-20 | Export / LUT | (US-04) | Resale and export exemptions both rest on documentation (certificates) |
| UC-21 | Import of services RCM | **US-02** | Use tax on untaxed purchases |
| UC-22 | Advance-receipt GST | — | Sales tax generally attaches at sale or delivery, and ASC 606 is platform-documented as unsupported |
| *(period liability)* | | **US-01** | harness_plan.md §6.1, US column |
| UC-23 | Period GST liability (GSTR-3B) | **US-01** | Same question; one playbook, two regime strategies |
| UC-24 | Unclaimed credit (IMS / GSTR-2B) | **US-11** | No credit in US sales tax; the US "unclaimed" money is tax overpaid on exempt purchases |
| UC-25 | Inward credit and debit notes (credit effect) | — | No input credit to reduce. The cash side is US-17 |
| UC-26 | GSTR-1 readiness | (US-05, US-13) | No outward statement; rate and taxability correctness cover the same risk |
| UC-27 | Return filing timeliness | **US-14** | State filing calendar instead of GSTR-1/3B |
| UC-28 | Late-entered documents | **US-15** | Regime-agnostic; on Keystone no period is closed and no return is recorded |
| UC-29 | Turnover-based obligations | (US-03) | Economic-nexus thresholds are the US turnover lines |
| UC-30 | Multiple registrations | — | A state sales-tax permit is not a distinct-person regime; no ISD analogue |
| UC-31 | Annual return (GSTR-9/9C) | — | Most states have no annual sales-tax reconciliation return |
| UC-32 | Credit refunds (Rule 89) | **US-11** | Refund of overpaid tax instead of accumulated credit |
| UC-33 | Expense claims, GST credit | (US-02) | US-02 extends to `Expense` for use tax (no credit to block) |
| UC-34 | School exempt inward services | **US-11** | Nonprofit/government purchase exemption |
| UC-35 | Pure-agent recharges | (US-13) | Taxability of recharged services and pass-through costs by state |
| UC-36 | E-commerce TCS | **US-12** | Marketplace facilitator laws |
| UC-37 | Non-resident payments (s.195) | **US-22** | Chapter 3 withholding and Form 1042-S |
| UC-38 | Cash payment limits (s.40A(3)) | — | No US payer-side cash-deduction limit (Form 8300 concerns cash *received*) |
| UC-39 | TDS deductor setup | (US-06) | 1099 and backup-withholding setup |
| UC-40 | Vendor master audit | **US-16** | TIN / W-9 instead of GSTIN / PAN |
| UC-41 | Unapplied vendor credits | **US-17** | Regime-agnostic |
| UC-42 | Payment run prioritisation | **US-18** | Terms, discounts and backup withholding instead of MSME/Rule 37 |
| UC-43 | Bank-to-payables reconciliation | **US-19** | Regime-agnostic |
| UC-44 | Approval threshold splitting | **US-20** | Regime-agnostic; the threshold is inferable on Keystone |
| — | | **US-21** | Unclaimed property has no India analogue for vendor payables |

---

## Shared US rules

1. **Tax source on invoices is `taxes[]`.** Each row carries `state_code`,
   `jurisdiction_id`, `jurisdiction_level`, `rate`, `amount` and `is_exempt`. Item-level
   `cgst/sgst/igst` fields exist on US documents (filed B8), but they are GST
   leftovers and are never read.
2. **The customer's state comes from `Party.addresses[].state`.** Invoices have no
   `shipping_address`, `billing_address` or `place_of_supply` (0/158 populated).
3. **Rates are hand-entered.** Every jurisdiction has `rate_source: manual`, and the
   platform says so (`not_yet_supported.tax_rate_service`: "no call has ever been made
   against a live Avalara or TaxJar endpoint"). Specs check consistency against the
   configured jurisdictions, never "the correct rate", and must not file the absence
   of a rate service as a bug.
4. **The platform's own reports are the oracles:**
   `GET /api/accounting/reports/sales-tax-liability?from_date&to_date&basis` (US-01)
   and `GET /api/cpa/reports/1099-summary?year` (US-06). Neither is an MCP tool yet
   (`../../submissions/requested_tools.md` T1).
5. **Platform-documented US gaps are not bugs.** `not_yet_supported` lists
   `tax_rate_service`, `form_1099_filing` ("no W-9 capture, no TIN matching, no box
   mapping, no e-file"), `asc_606`, `cash_basis` (except the liability report's
   `basis=cash`) and `us_payroll`. *Observed:* `Party` now carries `tin`, `w9_on_file`,
   `form_1099_box` and `backup_withholding`, and the 1099 report reads them. Part of
   the "no W-9 capture" note looks out of date.
6. **Nothing posts.** Same as IN: report, escalate, never write.

## Status of our filed US reports, observed 2026-10-03

Tallied with the class bug board on 2026-10-03; the board status is authoritative.
The full Team 3 mapping is in
[`../../agentswitch_submissions.md` §A](../../submissions/agentswitch_submissions.md#a--filed--tallied-with-the-class-bug-board-2026-10-03).

| Filed | Board | Board status | Observed on Keystone, 3 Oct |
|---|---|---|---|
| **N1** `is_overdue` on resolved requests | N224 (merged with N8) | Live in Release 7 | 0/93 wrong. Cited records corrected (e.g. APR-2026-00121 `is_overdue 1`) |
| **N2** match never persisted | N242 | Fixed, ships next release | `recorded_status` populated on 81/81 |
| **N3** `bill_match` metadata | N243 | Live in Release 7 | not re-checked |
| **N4** nexus YTD stuck at 0 | N225 | Fixed, ships next release | MI $713,601.20 / 28, PA $1,077,985.76 / 28, OH $2,400,857.51 / 102: all equal our recompute |
| **B7 → N6** recurring runaway | N220 | Live in Release 7 | `next_bill_date` advances (2026-11-01); 15 of 20 generated bills voided; `last_generated_date` **still null** on all 4 templates. Worth a comment on N220 |
| **B8** INR bills on USD company | N223 | Fixed, ships next release | 15 of 16 voided, 1 draft |
| **B9** flags vs tools | N227 | Fixed, ships next release | not re-checked |

New US bugs from these use cases, verified and not on the board: **N14–N16**
([`../../agentswitch_submissions.md` §C.1](../../submissions/agentswitch_submissions.md#c1--new-bugs-to-file--verified-2026-10-03)).
US-06's W-9 finding is already on the board as **N398** (team07).

## Statutory caveats (flagged, not asserted)

- **1099 threshold.** Our understanding is that payments made after 31 Dec 2025 use a
  **$2,000** threshold for 1099-NEC/MISC (One Big Beautiful Bill Act, 2025), indexed
  after 2026. The platform's 1099 report already uses $2,000 for 2026. Applies to US-06.
- **Illinois nexus.** Our understanding is that Illinois dropped the 200-transaction
  test from 1 January 2026, leaving $100,000 of sales. Applies to US-03.
- **Ohio sourcing.** Ohio's sourcing rule for delivered intrastate sales
  (R.C. 5739.033) decides whether US-05's 36 invoices are mis-charged or the
  `sourcing: destination` configuration is wrong. Applies to US-05.
- **Ohio manufacturing exemption** (R.C. 5739.02(B)(42)(g)) and the taxability of
  janitorial and exterminating services decide US-02's exposure. Applies to US-02.
