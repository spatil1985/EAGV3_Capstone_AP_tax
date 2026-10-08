# playbooks/ — one manifest per use case

Each `.md` file is a playbook manifest: YAML front matter (what the router and the capability
registry read) followed by the SOP text the agent loads with `load_playbook`. India manifests are
in [`IN/`](IN/), US manifests in [`US/`](US/). `load_manifests()` reads both folders.

- **Code:** `compute: module:Class` points at `scripts/uc/IN/…` or `scripts/uc/US/…`; logic shared
  by more than one use case is in [`../scripts/uc/common/`](../scripts/uc/common/).
- **Statutory numbers:** [`constants.yaml`](constants.yaml), effective-dated where the law changed;
  values with `verified: null` still need a person to check the source.
- **Facts not in the data model** (pure-agent contracts, non-resident documents, certificates we
  issue, approval limits): [`../config/overrides/`](../config/overrides/).
- **Checks:** LLM-generated, ungraded offline checks for each live playbook are in
  [`../tests_generated/`](../tests_generated/README.md). Graded tests stay hand-written in `tests/`.
- **Run one:** `py -3 -m aptax run --tenant in --playbook uc-05` (dry-run; `routes` shows why a
  playbook would or wouldn't run).

**66 manifests:** 56 live, 5 blocked, 5 spec only. Blocked and spec-only manifests carry no code; the router answers them through `explain_use_case`.

## India (GST) — Suryodaya

| Use case | Title | Capability | Status | Triggers | Code |
|---|---|---|---|---|---|
| [UC-01](IN/uc-01-rule-37-itc-reversal.md) | Rule 37 180-day ITC reversal | `rule37` | ✅ live | on_request · scheduled/daily | `scripts/uc/IN/uc01_rule37_itc_reversal.py` |
| [UC-02](IN/uc-02-blocked-credit-audit.md) | Blocked credit audit (s.17(5)) | `blocked_credit` | ✅ live | on_request · scheduled/weekly | `scripts/uc/IN/uc02_blocked_credit.py` |
| [UC-03](IN/uc-03-rcm-self-invoicing.md) | Reverse-charge self-invoicing on notified services | `rcm` | ✅ live | on_request · scheduled/weekly | `scripts/uc/IN/uc03_rcm_self_invoicing.py` |
| [UC-04](IN/uc-04-msme-45-day-exposure.md) | MSME 45-day payment exposure | `msme` | ✅ live | on_request · scheduled/daily | `scripts/uc/IN/uc04_msme_45_day.py` |
| [UC-05](IN/uc-05-duplicate-vendor-payment.md) | Duplicate vendor payment | `duplicates` | ✅ live | event · on_request · scheduled/daily | `scripts/uc/IN/uc05_duplicate_vendor_payment.py` |
| [UC-06](IN/uc-06-approval-sla-audit.md) | Approval SLA and segregation of duties | `approvals` | ✅ live | on_request · scheduled/weekly | `scripts/uc/IN/uc06_approval_sla.py` |
| [UC-07](IN/uc-07-school-exempt-taxable-split.md) | School: exempt / taxable supply split | `school_exempt_split` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc07_school_exempt_split.py` |
| [UC-08](IN/uc-08-rule-42-apportionment-school.md) | School: Rule 42 ITC apportionment | `apportionment_school` | 🔴 blocked — F18 / N273 (no ITC apportionment or reversal posting; JournalEntry is read-only) and N426 T4.1; no school tenant | on_request · scheduled/monthly | — |
| [UC-09](IN/uc-09-vendor-tds-verification.md) | Vendor TDS verification | `tds` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc09_vendor_tds.py` |
| [UC-10](IN/uc-10-job-work-itc04.md) | Job work return deadline (s.143, ITC-04) | `job_work` | ✅ live | on_request · scheduled/monthly | `scripts/uc/IN/uc10_job_work.py` |
| [UC-11](IN/uc-11-three-way-match.md) | Three-way match (PO, receipt, bill) | `three_way` | ✅ live | event · on_request · scheduled/daily | `scripts/uc/IN/uc11_three_way_match.py` |
| [UC-12](IN/uc-12-eway-bill.md) | E-way bill coverage and expiry audit | `eway` | ✅ live | on_request · scheduled/daily | `scripts/uc/IN/uc12_eway_bill.py` |
| [UC-13](IN/uc-13-194q-206c-thresholds.md) | 194Q goods-purchase TDS thresholds (buy and sell side) | `tds_194q` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc13_194q_thresholds.py` |
| [UC-14](IN/uc-14-clinic-exempt-taxable-split.md) | Clinic: exempt / taxable supply split | `clinic_exempt_split` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc14_clinic_exempt_split.py` |
| [UC-15](IN/uc-15-rule-42-43-apportionment-clinic.md) | Clinic: Rule 42/43 ITC apportionment | `apportionment_clinic` | 🔴 blocked — F18 / N273 (no apportionment engine or reversal posting; JournalEntry is read-only) and N426 T4.1; no clinic tenant | on_request · scheduled/monthly | — |
| [UC-16](IN/uc-16-drug-expiry-blocked-credit.md) | Stock expiry and blocked credit on write-off | `expiry` | ✅ live | on_request · scheduled/daily | `scripts/uc/IN/uc16_expiry_blocked_credit.py` |
| [UC-17](IN/uc-17-composition-scheme.md) | Composition scheme eligibility and breach | `composition` | 🔴 blocked — N426 T4.3 / F20 — no company tax profile (registration type, preceding-FY turnover) | event · on_request · scheduled/monthly | — |
| [UC-18](IN/uc-18-hsn-rate-consistency.md) | HSN rate consistency | `hsn_rate` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc18_hsn_rate_consistency.py` |
| [UC-19](IN/uc-19-credit-note-time-limit.md) | Credit-note s.34(2) time limit | `credit_note_window` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc19_credit_note_window.py` |
| [UC-20](IN/uc-20-export-lut-tracking.md) | Export / SEZ zero-rating and LUT cover | `export_lut` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc20_export_lut.py` |
| [UC-21](IN/uc-21-import-of-services-rcm.md) | Import of services under reverse charge | `rcm_import` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc21_import_of_services_rcm.py` |
| [UC-22](IN/uc-22-advance-receipt-gst.md) | GST on advances received | `advances` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc22_advance_receipt_gst.py` |
| [UC-23](IN/uc-23-period-gst-liability.md) | Period GST liability (GSTR-3B) | `tax_liability` | ✅ live | on_request · scheduled/monthly | `scripts/uc/IN/uc23_period_gst_liability.py` |
| [UC-24](IN/uc-24-unclaimed-itc-ims-2b.md) | Unclaimed and at-risk input credit (IMS, GSTR-2B) | `itc_unclaimed` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc24_itc_entitlement.py` |
| [UC-25](IN/uc-25-vendor-credit-debit-notes-itc.md) | Inward credit notes and the credit they reduce | `vendor_notes` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc25_vendor_notes_itc.py` |
| [UC-26](IN/uc-26-gstr1-readiness.md) | GSTR-1 readiness | `gstr1` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc26_gstr1_readiness.py` |
| [UC-27](IN/uc-27-return-filing-timeliness.md) | GST return filing timeliness | `filing_calendar` | ✅ live | on_request · scheduled/daily | `scripts/uc/IN/uc27_return_filing_timeliness.py` |
| [UC-28](IN/uc-28-late-entered-documents.md) | Late-entered documents in filed or closed periods | `period_integrity` | ✅ live | event · on_request · scheduled/daily | `scripts/uc/IN/uc28_late_entered_documents.py` |
| [UC-29](IN/uc-29-turnover-based-obligations.md) | Turnover-based GST obligations | `turnover` | ✅ live | on_request · scheduled/monthly | `scripts/uc/IN/uc29_turnover_obligations.py` |
| [UC-30](IN/uc-30-multiple-registrations.md) | Multiple registrations, branch transfers and ISD | `registrations` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc30_multiple_registrations.py` |
| [UC-31](IN/uc-31-annual-return-reconciliation.md) | Annual return reconciliation (GSTR-9 / 9C) | `annual_return` | 🔴 blocked — GST-39 (GSTR-9 endpoint returns HTTP 501, platform-documented — don't file); GSTR-2B lines not exposed (N426 T1.3) | on_request · scheduled/monthly | — |
| [UC-32](IN/uc-32-itc-refund-zero-rated-inverted.md) | ITC refund on zero-rated supplies and inverted duty (Rule 89) | `refund` | ✅ live | on_request · scheduled/monthly | `scripts/uc/IN/uc32_itc_refund.py` |
| [UC-33](IN/uc-33-expense-claims-itc.md) | GST credit on expense claims | `expense_credit` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc33_expense_claims_itc.py` |
| [UC-34](IN/uc-34-school-exempt-inward-services.md) | School: GST charged on exempt inward services | `school_inward` | ⚪ spec only | event · on_request · scheduled/monthly | — |
| [UC-35](IN/uc-35-agency-pure-agent-reimbursements.md) | Recharged costs and the pure-agent test (Rule 33) | `recharges` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc35_pure_agent_recharges.py` |
| [UC-36](IN/uc-36-ecommerce-tcs-s52.md) | Retail: e-commerce TCS (s.52) and s.9(5) | `marketplace_in` | 🔴 blocked — F22 (not filed): no sales-channel / operator field on Invoice and no TCS credit (GSTR-8) record — GAP-6 | on_request · scheduled/monthly | — |
| [UC-37](IN/uc-37-non-resident-payments-tds-195.md) | Payments to non-residents (s.195 TDS, Form 15CA/CB) | `nonresident_tds` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc37_nonresident_payments.py` |
| [UC-38](IN/uc-38-cash-payment-limits.md) | Cash payments above the s.40A(3) limit | `cash_limit` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc38_cash_payment_limits.py` |
| [UC-39](IN/uc-39-tds-deductor-setup.md) | TDS deductor setup and section coverage | `tds_setup` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/IN/uc39_tds_deductor_setup.py` |
| [UC-40](IN/uc-40-vendor-master-audit.md) | Vendor master audit | `vendor_master` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/IN/uc40_vendor_master_audit.py` |
| [UC-41](IN/uc-41-unapplied-vendor-credits.md) | Unapplied vendor credits and advances | `vendor_balance` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/IN/uc41_unapplied_vendor_credits.py` |
| [UC-42](IN/uc-42-payment-run-prioritisation.md) | Payment-run prioritisation | `payment_run` | ✅ live | on_request · scheduled/weekly | `scripts/uc/IN/uc42_payment_run.py` |
| [UC-43](IN/uc-43-bank-to-payables-reconciliation.md) | Bank-to-payables reconciliation | `bank_recon` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/IN/uc43_bank_to_payables.py` |
| [UC-44](IN/uc-44-approval-threshold-splitting.md) | Approval-threshold splitting | `threshold_split` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/IN/uc44_approval_threshold_splitting.py` |

## US (sales & use tax) — Keystone

| Use case | Title | Capability | Status | Triggers | Code |
|---|---|---|---|---|---|
| [US-01](US/us-01-period-sales-use-tax-liability.md) | Period sales and use tax liability | `tax_liability_us` | ✅ live | on_request · scheduled/monthly | `scripts/uc/US/us01_period_sales_use_tax.py` |
| [US-02](US/us-02-consumer-use-tax-on-purchases.md) | Consumer use tax on purchases | `use_tax` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/US/us02_consumer_use_tax.py` |
| [US-03](US/us-03-economic-nexus-monitoring.md) | Economic nexus monitoring | `nexus` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/US/us03_economic_nexus.py` |
| [US-04](US/us-04-exemption-certificate-coverage.md) | Exemption certificate coverage | `exemption_certs` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/US/us04_exemption_certificates.py` |
| [US-05](US/us-05-sourcing-and-rate-correctness.md) | Sourcing and rate correctness | `rates` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/US/us05_sourcing_and_rate.py` |
| [US-06](US/us-06-form-1099-readiness.md) | Form 1099 readiness and backup withholding | `form_1099` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/US/us06_form_1099_readiness.py` |
| [US-07](US/us-07-duplicate-vendor-payment.md) | Duplicate vendor payment (US) | `duplicates_us` | ✅ live | event · on_request · scheduled/daily | `scripts/uc/US/us07_duplicate_vendor_payment.py` |
| [US-08](US/us-08-approval-sla-audit.md) | Approval SLA and segregation of duties (US) | `approvals_us` | ✅ live | on_request · scheduled/weekly | `scripts/uc/US/us08_approval_sla.py` |
| [US-09](US/us-09-three-way-match.md) | Three-way match (US) | `three_way_us` | ✅ live | event · on_request · scheduled/daily | `scripts/uc/US/us09_three_way_match.py` |
| [US-10](US/us-10-credit-memo-refund-window.md) | Sales tax on credit memos and refund windows | `credit_memo_window` | ⚪ spec only | event · on_request · scheduled/monthly | — |
| [US-11](US/us-11-sales-tax-on-exempt-purchases.md) | Sales tax paid on exempt purchases | `exempt_purchases` | ✅ live | event · on_request · scheduled/monthly | `scripts/uc/US/us11_tax_on_exempt_purchases.py` |
| [US-12](US/us-12-marketplace-facilitator-sales.md) | Retail: marketplace facilitator sales | `marketplace_us` | ⚪ spec only | event · on_request · scheduled/monthly | — |
| [US-13](US/us-13-taxability-services-digital-holidays.md) | Taxability by state — services, digital, medical, shipping, holidays | `taxability` | ⚪ spec only | event · on_request · scheduled/monthly | — |
| [US-14](US/us-14-sales-tax-filing-calendar.md) | State sales-tax filing calendar | `filing_calendar_us` | ✅ live | on_request · scheduled/daily | `scripts/uc/US/us14_filing_calendar.py` |
| [US-15](US/us-15-late-entered-documents.md) | Late-entered documents (US) | `period_integrity_us` | ✅ live | event · on_request · scheduled/daily | `scripts/uc/US/us15_late_entered_documents.py` |
| [US-16](US/us-16-vendor-master-audit.md) | Vendor master audit (US) | `vendor_master_us` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/US/us16_vendor_master_audit.py` |
| [US-17](US/us-17-unapplied-vendor-credits.md) | Unapplied vendor credits (US) | `vendor_balance_us` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/US/us17_unapplied_vendor_credits.py` |
| [US-18](US/us-18-payment-run-prioritisation.md) | Payment-run prioritisation (US) | `payment_run_us` | ✅ live | on_request · scheduled/weekly | `scripts/uc/US/us18_payment_run.py` |
| [US-19](US/us-19-bank-to-payables-reconciliation.md) | Bank-to-payables reconciliation (US) | `bank_recon_us` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/US/us19_bank_to_payables.py` |
| [US-20](US/us-20-approval-threshold-splitting.md) | Approval-threshold splitting (US) | `threshold_split_us` | ✅ live | event · on_request · scheduled/weekly | `scripts/uc/US/us20_approval_threshold_splitting.py` |
| [US-21](US/us-21-unclaimed-property-escheat.md) | Unclaimed property (escheat) | `escheat` | ✅ live | on_request · scheduled/monthly | `scripts/uc/US/us21_unclaimed_property.py` |
| [US-22](US/us-22-foreign-vendor-withholding.md) | Foreign vendors: Chapter 3 withholding and Form 1042-S | `foreign_withholding` | ⚪ spec only | event · on_request · scheduled/monthly | — |

`duplicate_audit.md` and `tax_audit.md` are legacy SOPs with no manifest, superseded by UC-05 /
US-07 and UC-23 / US-01.
