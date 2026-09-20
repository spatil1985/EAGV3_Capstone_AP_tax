# UI.MD — Current Product UI & Functional Inventory

> Purpose: This document captures the **current-state UI and evidenced functionality** of the product for use by Claude Code or another coding/review agent.  
> Scope emphasis: **Accounting, Accounts Payable, tax/compliance, payments, ledger/accounting controls, reporting, and related master data.**  
> Important: Treat anything marked **Not evidenced / Not visible / Suggested** as unconfirmed. Do not infer implementation beyond what the screenshots showed.

---

# 1. Product Structure

## 1.1 Primary functional areas observed

- Dashboard / Company Overview
- All Contacts / Business Partner master
- Accounting
  - Sales
  - Purchases
  - Documents
  - Banking
  - Compliance
  - Accountant
  - Reports
  - Settings
- Platform
  - Agent
  - Mission Control
  - Job Ledger
  - Agent Skills

This document focuses on the accounting/AP/tax side rather than global platform navigation.

---

# 2. Functional Architecture Summary

The product currently appears to support the following business flow:

```text
Business Partner / Vendor Master
    ↓
Supplier / Customer Tax Attributes
    ↓
Purchase Requisition / Purchase Order
    ↓
Supplier Document Intake
    ↓
Draft Bill
    ↓
Supplier Bill
    ↓
GST / Tax Calculation
    ↓
General Ledger Posting
    ↓
Payment / Allocation
    ↓
Reconciliation
    ↓
GST Return / IMS / Tax Payment / Annual Return
```

Supporting controls and configuration:

```text
Locations / GSTIN
Currencies / Exchange Rates
Taxes / Group Taxes
Reporting Tags / Dimensions
Transaction Locking
Period Close
Budgets
Cash-flow Scenarios
Reports
```

---

# 3. Screen Inventory

---

## SCR-001 — Company Overview / Dashboard

**Module:** Dashboard  
**Workspace:** Executive Workspace  
**Domain relevance:** Finance overview, AP monitoring, collections

### Purpose

High-level landing page for business and financial monitoring.

### Visible finance capabilities

- Recorded collections
- Overdue customer invoices
- Overdue supplier bills
- Collections trend over time
- Reporting-period filter
- Drill-down into Accounting workspace

### AP relevance

- Shows count of overdue supplier bills
- Provides high-level payable health indicator

### Tax relevance

- No explicit tax KPI visible on this screen

### Notes

This screen is a summary/monitoring dashboard, not a transaction-entry screen.

---

## SCR-002 — Customers / Contacts List

**Module:** All Contacts  
**Domain relevance:** Business partner master

### Purpose

Centralized list of customer/contact records.

### Visible fields / actions

- Total records
- Individuals count
- Organizations count
- Customer/contact name
- Associated organization
- Search
- Add new contact/customer
- Open record detail

### AP / tax relevance

Indirect. More useful as evidence of a unified party master.

### Not visible at list level

- GSTIN
- PAN
- Tax treatment
- Bank account
- MSME
- W-9 / 1099 data

---

## SCR-003 — Customer / Business Partner Detail

**Module:** All Contacts  
**Domain relevance:** Party master, AP-adjacent vendor attributes, tax/compliance

### Purpose

Maintain business partner identity, tax, compliance, portal, and payment attributes.

### Core fields

- Company
- Name
- Type
- Email
- Phone
- Communication preferences
- Created date
- Updated date

### Tax / compliance fields

- GST No
- PAN
- Tax
- Taxable
- TIN
- W9 On File
- W9 Signed Name
- Is 1099 Vendor
- Backup Withholding
- Privacy State

### AP / vendor fields

- Is MSME
- MSME No
- Vendor Bank Account Number
- Beneficiary Name
- Opening Balance
- Portal Enabled / Is Portal Enabled

### Roles

- Role
- Since
- Active
- Example observed: `prospect`

### Key architectural observation

The record appears to be a **unified business partner model**, because a "Customer" record can still contain vendor banking, MSME, W-9, 1099, and withholding fields.

---

## SCR-004 — New Customer / Business Partner

**Module:** All Contacts  
**Domain relevance:** Business partner onboarding

### Purpose

Create a new person or organization.

### Fields

- Name — required
- Type
- Email
- Phone

### Roles section

- Role
- Since date
- Add Row
- Multiple roles supported

### Contacts section

- Contact type
- Contact value
- Add Row

### Addresses section

- Label
- Address
- City
- State
- PIN
- Add Row

### Tags section

- Tag
- Add Row

### Important observation

Initial creation form does **not** visibly expose the richer finance/tax fields from the detail screen.

Potential implication:
- finance/tax enrichment may occur later via edit, role-specific onboarding, or another workflow.

---

## SCR-005 — Accounting Dashboard

**Module:** Accounting → Dashboard  
**Domain relevance:** AP operations, cash, spend, accounting overview

### Purpose

Consolidated accounting dashboard.

### Payables summary

- Total unpaid bills
- Current payables
- Overdue payables
- New bill action

### Receivables summary

- Total unpaid invoices
- Current
- Overdue

### Cash Flow

- Monthly incoming
- Monthly outgoing
- Cash as on today
- Financial-year selector

### Income and Expense

- Accrual / Cash toggle
- Total income
- Total expense
- Net result

### Top Expenses

- Expense category breakdown

### Recent Bills

- Bill number
- Vendor
- Amount
- Status
- View All

### Bank & Credit Cards

- Account name
- Institution
- Balance
- Link state such as `unlinked`

### AP modules visible in navigation

- Vendors
- Expenses
- Recurring Expenses
- Purchase Requisitions
- Purchase Orders
- Bills
- Recurring Bills
- Payments Made
- Vendor Credits

### Tax

No direct tax KPI visible on the dashboard.

---

## SCR-006 — Supplier Bill Detail

**Module:** Accounting → Purchases → Bills  
**Domain relevance:** Accounts Payable, GST, supplier liability

### Purpose

View and manage an individual supplier bill.

### Header / status

- Bill number
- Status, example: `Open`
- Bill template selector
- Void
- Edit
- Email
- Share
- PDF / Print

### Bill details

- Vendor / party
- Bill date
- Due date
- Bill-to
- Ship-to
- Line items
- Rate
- Amount
- Notes
- Bank details

### Tax behavior observed

Example:

```text
Subtotal
CGST @ 9%
SGST @ 9%
Total
```

This is direct evidence of transaction-level GST calculation.

### Payment / liability

- Grand Total
- Balance Due
- Payments section
- "No payments recorded" when unpaid

### Activity

- Created
- Updated

### Evidenced

- Supplier bill lifecycle
- Vendor linkage
- Due-date tracking
- GST calculation
- Outstanding balance tracking
- Payment association
- Void/edit/share/print

### Not yet evidenced

- TDS deduction
- IGST
- HSN/SAC
- reverse charge
- 2-way/3-way matching
- PO matching
- GRN matching
- approval workflow

---

## SCR-007 — Sales Invoices List

**Module:** Accounting → Sales → Invoices  
**Domain relevance:** AR / output tax reference

### Purpose

List and monitor customer invoices.

### KPIs

- Total Outstanding
- Not Yet Due
- Overdue
- Total Invoices

### Columns

- Number
- Party
- Status
- Date
- Due Date
- Grand Total

### Actions

- Search
- Filter/options
- New invoice
- Pagination

### Relevance to AP/tax study

Useful mainly as AR counterpart and output-tax reference.

---

## SCR-008 — Tax Invoice Detail

**Module:** Accounting → Sales → Invoices  
**Domain relevance:** Output tax, tax invoice generation

### Purpose

Create/review/send a customer tax invoice.

### Fields / document content

- Invoice number
- Status, example: `Draft`
- Document type: `Tax Invoice`
- Seller GSTIN
- Bill To
- Ship To
- Invoice date
- Payment terms
- Due date
- Line items
- Rate
- Amount
- Tax lines
- Total
- Bank details

### Actions

- Send
- Edit
- Email
- Share
- PDF / Print
- Template selector

### Tax observation

Multiple tax amounts are shown, but labels are generic `Tax` on this screenshot.

### Important evaluation point

Compare transaction tax transparency:
- supplier bill shows clear `CGST` and `SGST`
- this tax invoice shows generic tax labels

---

## SCR-009 — Sales Orders List

**Module:** Accounting → Sales → Sales Orders  
**Domain relevance:** Order-to-cash upstream document

### Purpose

Track customer sales orders.

### KPIs

- Total
- Open
- Fulfilled

### Columns

- Number
- Party
- Status
- Date
- Grand Total
- Approval Status
- Payment Terms

### Statuses observed

- Confirmed
- Draft

### Notes

Tax breakdown is not visible at list level.

---

## SCR-010 — Recurring Invoices

**Module:** Accounting → Sales → Recurring Invoices

### Purpose

Maintain recurring invoice schedules.

### Columns

- Profile Name
- Customer
- Status
- Frequency
- Next Invoice Date
- Amount

### Frequencies observed

- Weekly
- Monthly
- Quarterly
- Yearly

### Statuses observed

- Stopped
- Expired

### Tax behavior

Not visible at this level.

---

## SCR-011 — Delivery Challans List

**Module:** Accounting → Sales → Delivery Challans  
**Domain relevance:** Goods movement / fulfillment

### Columns

- Number
- Customer
- Status
- Date
- Grand Total

### Statuses observed

- Draft
- Delivered

### Actions

- Search
- New

---

## SCR-012 — Delivery Challan Detail

**Module:** Accounting → Sales → Delivery Challans  
**Domain relevance:** Fulfillment, GST, place of supply

### Purpose

Document delivery of goods against a sales order.

### Header / actions

- Challan number
- Status: Delivered
- Mark Returned
- Edit
- Create Invoice
- Share
- PDF / Print

### Important fields

- Bill To
- Ship To
- Challan date
- P.O.# / sales-order reference
- Place of Supply
- Item lines
- Rate
- Amount
- CGST
- SGST
- Total
- Notes
- Bank details

### Key capabilities

- Explicit linkage to sales order
- Place of Supply displayed
- GST on delivery document
- Return handling
- Create invoice from delivery challan

### Document flow evidenced

```text
Sales Order → Delivery Challan → Invoice
```

---

## SCR-013 — Payments Received List

**Module:** Accounting → Sales → Payments Received  
**Domain relevance:** AR cash receipts

### Columns

- Number
- Customer
- Status
- Date
- Amount
- Payment Mode
- Unused Amount

### Payment modes observed

- cheque
- bank_transfer
- upi
- online

### Key accounting capability

`Unused Amount` indicates support for unapplied/excess receipts.

---

## SCR-014 — Payment Receipt Detail

**Module:** Accounting → Sales → Payments Received

### Purpose

View a customer payment receipt.

### Fields

- Receipt number
- Status: Paid
- Payment date
- Party
- Amount
- Reference
- Bank details

### Actions

- Void
- Edit
- Share
- PDF / Print

### Activity

- Created
- Updated
- Marked as Paid

### Relevance

Good model for evaluating the AP-side payment equivalent.

---

## SCR-015 — Retainer Invoice Detail

**Module:** Accounting → Sales → Retainer Invoices  
**Domain relevance:** Customer advance / prepayment

### Purpose

Request and track customer advance funds.

### Important fields

- Retainer invoice number
- Status: Sent
- Customer
- Date
- Due date
- Terms
- Reference / PO number
- Grand total

### Key actions

- Apply available funds
- Record Payment
- Edit
- Share
- PDF / Print

### Important capability

Supports customer advance / unapplied-fund model.

---

## SCR-016 — Vendors List

**Module:** Accounting → Purchases → Vendors  
**Domain relevance:** AP vendor master

### Columns

- Name
- Company Name
- Email
- GST Treatment
- Phone

### Actions

- Search
- Filter/options
- New vendor
- Pagination

### Key tax capability

Dedicated `GST Treatment` field exists at vendor-list level.

---

## SCR-017 — Vendor Detail

**Module:** Accounting → Purchases → Vendors  
**Domain relevance:** Supplier master, tax, compliance, banking

### Purpose

View supplier identity and finance/tax attributes.

### Core fields

- Company
- Name
- Type
- Email
- Phone
- Communication preferences

### AP / tax fields

- GST No
- PAN
- Tax
- Taxable
- Opening Balance
- Is MSME
- MSME No
- Vendor Bank Account Number
- Beneficiary Name
- TIN
- W9 On File
- W9 Signed Name
- Portal Enabled

### Key architectural observation

Vendor and customer detail appear to share the same business-partner data model.

---

## SCR-018 — Payments Made List

**Module:** Accounting → Purchases → Payments Made  
**Domain relevance:** AP settlement

### Columns

- Number
- Vendor
- Status
- Date
- Amount
- Payment Mode
- Unused Amount

### Status observed

- Paid

### Payment modes observed

- bank_transfer
- cheque

### Important capability

Unused amount exists on vendor payments as well.

Potential use:
- vendor advance
- overpayment
- unapplied payment

---

## SCR-019 — General Ledger List

**Module:** Accounting → Accountant → General Ledger  
**Domain relevance:** Core accounting, AP/tax posting

### Columns

- Account
- Posting Date
- Debit
- Credit
- Remarks
- Created At

### Accounts observed

- Salaries Payable
- Input CGST
- Salaries & Wages
- Term Loan - ICICI (Machinery)
- Round Off
- EPF Payable
- Staff Welfare

### Key tax capability

Separate GL account for `Input CGST`.

### Important behavior

Posting date is distinct from created timestamp.

---

## SCR-020 — General Ledger Entry Detail

**Module:** Accounting → General Ledger

### Fields

- Account
- Customer / party
- Debit
- Credit
- Voucher Type
- Voucher
- Posting Date
- Company
- Remarks
- Is Cancelled
- Created date

### Key capabilities

- Voucher linkage
- Party linkage
- Cancellation state
- Source metadata

### Notable UI issue

Field label `Customer` may be generic even for vendor/expense contexts.

---

## SCR-021 — Transaction Locking

**Module:** Accounting → Accountant → Transaction Locking  
**Domain relevance:** Period protection / accounting controls

### Purpose

Prevent modifications to transactions before a lock date.

### Lock groups

#### Sales
Includes:
- Invoices
- Quotations
- Sales Orders
- Credit Notes
- Payments Received

#### Purchases
Includes:
- Bills
- Purchase Orders
- Vendor Credits
- Expenses
- Payments Made

#### Banking
Includes:
- Bank Transactions
- Categorization
- Reconciliation

#### Accountant
Includes:
- Journal Entries
- Chart of Accounts modifications

### Actions

- Lock All Modules
- Unlock per module
- Configure date

### Explicit business rule

When locked, attempts to create, edit, or delete transactions dated on or before the lock date are rejected.

---

## SCR-022 — Period Close

**Module:** Accounting → Accountant → Period Close  
**Domain relevance:** Month-end / year-end controls

### Purpose

Close accounting periods and block ledger postings.

### Features

- Fiscal year
- Monthly periods
- Period date range
- Status: open / closed
- Closed by
- Close action
- Reopen action
- Prior year / current year / next year navigation
- Year-end indicator

### Explicit control

Ledger refuses postings on or before the books-closed date.

### Important

This is engine-level enforcement, not just UI state.

---

## SCR-023 — Budgets

**Module:** Accounting → Accountant → Budgets

### Columns

- Name
- Fiscal Year
- Budget Type
- Status

### Budget types observed

- monthly
- quarterly
- yearly

### Statuses

- Active
- Inactive

### Not yet evidenced

- budget vs actual
- procurement budget enforcement
- PO / requisition budget check
- department / cost center budget dimensions

---

## SCR-024 — Cash-flow Scenarios

**Module:** Accounting → Reports → Cash-flow scenarios  
**Domain relevance:** Treasury / AP timing / working capital

### Purpose

Non-posting timing simulation over current obligations.

### Explicit warning

Scenario assumptions do not create, change, post, or pay any financial record.

### Inputs

- Customer receipt delay (days)
- Payable payment timing (days)

### Output

Grouped by:
- due date
- currency

Each item shows:
- inflow
- outflow
- canonical source reference

### Action

- Refetch before comparison

### Key capability

AP timing can be simulated independently of actual bill due dates or postings.

---

## SCR-025 — Reports Catalogue

**Module:** Accounting → Reports

### Report categories

- Business Overview
- Sales
- Receivables
- Payables
- Purchases
- Taxes
- Banking
- Accountant
- Budgets

### Business Overview reports shown

- Profit and Loss
- Balance Sheet
- Cash Flow Statement

### Important

Dedicated Payables and Taxes report categories exist.

---

## SCR-026 — Taxes List

**Module:** Accounting → Settings → Taxes  
**Domain relevance:** Tax master

### Columns

- Tax Name
- Tax Type
- Tax Percentage
- Status

### Tax types observed

- SALES_TAX
- USE_TAX
- TDS
- CGST
- UTGST
- TCS
- other

### Statuses

- Active
- Inactive

### Key behavior

Tax percentages are configurable.

---

## SCR-027 — New Tax

**Module:** Accounting → Settings → Taxes

### Fields

- Tax Name — required
- Tax Type
- Percentage — required
- Is Group Tax
- Status

### Group Tax section

- Tax Name
- Type
- %
- Add Row

### Key capability

Supports **composite/group taxes**.

Potential use:

```text
GST 18%
  - CGST 9%
  - SGST 9%
```

This exact composition was not shown, but the group mechanism is evidenced.

---

## SCR-028 — Currencies

**Module:** Accounting → Settings → Currencies  
**Domain relevance:** Multi-currency accounting

### Columns

- Currency Code
- Currency Symbol
- Currency Name
- Exchange Rate
- Is Base

### Currencies observed

- JPY
- EUR
- USD
- INR

### Base currency

INR with exchange rate `1`.

### Key capability

Manual/configurable exchange-rate master exists.

### Not yet evidenced

- automatic FX feed
- effective dates
- historical FX rates
- transaction-date rate selection
- realized FX gain/loss logic

---

## SCR-029 — Locations

**Module:** Accounting → Settings → Locations  
**Domain relevance:** GST registration / legal entity location

### Columns

- Name
- City
- State
- GSTIN
- Is Primary

### Example location types

- Sales Office
- Forward Stock Point
- Warehouse
- Registered Office

### Key tax capability

GSTIN can be maintained per location.

### Important model

```text
Company
  → Location
      → City
      → State
      → GSTIN
      → Primary flag
```

---

## SCR-030 — Reporting Tags

**Module:** Accounting → Settings → Reporting Tags  
**Domain relevance:** Accounting dimensions / analytical classification

### Columns

- Tag Name
- Is Mandatory
- Applies To

### Example tags

- Shift
- Capex vs Revenue
- Customer Programme
- Cost Centre

### Applies-to values observed

- expenses
- journals
- bills
- invoices
- all

### Key capability

Custom accounting/reporting dimensions can be:
- transaction-specific
- mandatory or optional

---

## SCR-031 — Payments List

**Module:** Accounting → Accountant → Payments  
**Domain relevance:** Unified payment engine

### Columns

- Number
- Status
- Type
- Amount
- Mode
- Created At

### Payment types observed

- pay
- receive
- internal_transfer

### Statuses observed

- Draft
- Submitted
- Cancelled
- Reconciled

### Payment modes observed

- bank_transfer
- upi
- cash
- card
- online
- other

### Key architectural conclusion

This appears to be a centralized payment engine supporting:
- incoming payments
- outgoing payments
- internal transfers

---

## SCR-032 — Payment Detail

**Module:** Accounting → Payments

### Fields

- Payment number
- Status
- Type
- Customer / party
- Company
- Date
- Amount
- Mode
- Reference
- Deposit To
- Bank Charges
- Exchange Rate
- Notes
- Created date
- Updated date

### Summary

- Total Amount
- Allocated
- Unallocated

### Key capability

Allocation model is explicit.

Example:

```text
Total Amount: 80,855.61
Allocated: 0
Unallocated: 80,855.61
```

This is strong evidence for:
- unapplied cash
- partial allocation
- advance / prepayment handling

Multi-document allocation UI is still not directly shown.

---

## SCR-033 — GST Filing / Returns

**Module:** Accounting → Compliance → GST Filing  
**Tab:** Returns

### Period selection

- Month
- Year

### GSTR-3B

- Summary Return
- Status: Unfiled
- Generate action

### GSTR-1

- Sales Return
- Status: Unfiled
- Generate action

### GSTR-2A

- Auto-drafted
- Fetch supplier-filed data from GSTN
- Fetch from GSTN action

### GSTR-2B

- ITC Statement
- Fetch ITC eligibility statement from GSTN
- Fetch from GSTN action

### Return history

- Dedicated history area

### Key capability

GST return preparation plus GSTN data retrieval.

### Not yet evidenced

- direct filing/submission
- ARN
- amendment flow
- filing error handling

---

## SCR-034 — GST Filing / IMS Dashboard

**Module:** Accounting → Compliance → GST Filing  
**Tab:** IMS Dashboard  
**Domain relevance:** ITC reconciliation / supplier invoice review

### Summary cards

- Accepted
- Rejected
- Pending

### Columns

- Vendor
- GSTIN
- Invoice #
- Taxable
- Tax
- Status
- Action

### Actions

- Accept
- Reject

### Key capability

Supplier invoice-level tax review workflow.

### Important AP linkage

This directly links:
- vendor
- supplier bill
- taxable amount
- tax amount
- ITC review status

---

## SCR-035 — GST Filing / GST Payments

**Module:** Accounting → Compliance → GST Filing  
**Tab:** GST Payments

### Fields

- Challan Number
- Amount
- Payment Date
- Bank Account

### Actions

- Record Payment
- Save Payment
- Cancel

### Lower section

GST payment history area.

### Key capability

Dedicated GST liability-payment recording.

---

## SCR-036 — GST Filing / Annual Returns

**Module:** Accounting → Compliance → GST Filing  
**Tab:** Annual Returns

### Functionality

- Annual Return (GSTR-9)
- Fiscal-year selector
- Generate Summary

### Key capability

Annual GST summary generation.

### Not yet evidenced

- direct GSTR-9 filing
- GSTR-9C
- book-to-return reconciliation

---

## SCR-037 — e-Way Bills List

**Module:** Accounting → Compliance → e-Way Bills  
**Domain relevance:** Goods movement compliance

### Columns

- E-Way Bill Number
- Transaction Type
- Generation Date
- Total
- Status
- Expiry Date

### Transaction types observed

- bill
- invoice
- delivery_challan

### Statuses observed

- Not Generated
- Generated
- Active

### Key capability

Tracks e-Way Bill status and validity against source transactions.

---

## SCR-038 — New e-Way Bill

**Module:** Accounting → Compliance → e-Way Bills

### Fields

- Transaction Type
- E-Way Bill #
- Customer GSTIN
- Vehicle Number
- Distance (km)
- Transporter ID
- Related Transaction
- Total Value
- Generation Date
- Expiry Date

### Key capability

Captures logistics and compliance fields required for e-Way Bill tracking.

### Not yet evidenced

- NIC API generation
- cancellation
- extension
- Part A / Part B workflow
- vehicle update workflow

---

## SCR-039 — Bill Intake Review

**Module:** Accounting → Documents → Bill Intake Review  
**Domain relevance:** AP automation / document ingestion

### Purpose

Read supplier documents, extract bill fields, show confidence, require human confirmation, and then create a draft bill.

### Actions

- Refresh queue
- Add a document
- Review this document

### Filters / states

- Waiting for review
- Could not be read
- Not read yet
- Accepted
- Rejected
- All

### Per-document metadata

- State
- Lowest confidence
- Fields needing review

### Explicit safety behavior

Bill intake:
- creates draft bill only
- never submits
- never posts to ledger
- never pays

### Explicit limitation

This deployment has **no OCR engine**.

Meaning:
- scanned photos/images are unreadable
- machine-readable documents may still be parsed

### Key capability

Human-in-the-loop AP document extraction.

### Key evaluation areas

- OCR
- AI extraction
- vendor auto-match
- duplicate detection
- PO match
- GST validation
- confidence scoring
- straight-through processing

---

## SCR-040 — Manual Journals List

**Module:** Accounting → Accountant → Manual Journals

### Columns

- Number
- Status
- Date
- Narration
- Total Debit

### Status observed

- Submitted

### Key capability

Formal journal voucher register.

### Interesting observation

Narrations include source references, suggesting some journals may originate from operational modules.

---

## SCR-041 — Manual Journal Detail

**Module:** Accounting → Manual Journals

### Visible details

- Journal number
- Status: Submitted
- Entry date
- Journal Voucher document
- Created date

### Important inconsistency observed

The list shows a non-zero `Total Debit`, but the rendered journal voucher detail shows:

- no line items
- subtotal ₹0.00
- total ₹0.00

### Evaluation point

Journal detail should be checked for:
- debit line visibility
- credit line visibility
- balancing
- source document
- dimensions
- reversal
- tax adjustment metadata

---

# 4. Current AP Capability Map

## 4.1 Vendor / Business Partner

- Unified business-partner model
- Vendor records
- GSTIN
- PAN
- Taxable flag
- MSME flag and number
- Vendor bank account
- Beneficiary name
- TIN
- W-9
- 1099 vendor flag
- Backup withholding
- Opening balance
- Portal flag

## 4.2 Procure-to-Pay

- Purchase Requisitions
- Purchase Orders
- Bills
- Recurring Bills
- Expenses
- Recurring Expenses
- Payments Made
- Vendor Credits

## 4.3 Supplier Invoice Intake

- Document upload
- Machine-readable extraction
- Confidence scoring
- Human review
- Accept/reject
- Draft bill creation
- No automatic posting/payment
- No OCR in current deployment

## 4.4 Bill Processing

- Vendor
- Bill date
- Due date
- Line items
- Tax calculation
- Outstanding balance
- Payment association
- Edit
- Void
- PDF/Print
- Activity timestamps

## 4.5 Payments

- Unified payment engine
- pay / receive / internal_transfer
- multiple payment modes
- reference
- account association
- bank charges
- exchange rate
- allocated amount
- unallocated amount
- reconciliation status

---

# 5. Current Tax Capability Map

## 5.1 Tax Master

- Tax Name
- Tax Type
- Percentage
- Status
- Group Tax
- Multiple child tax components

## 5.2 Tax Types Observed

- CGST
- UTGST
- TDS
- TCS
- SALES_TAX
- USE_TAX
- other

## 5.3 Party Tax Data

- GSTIN
- PAN
- Taxable
- TIN
- W-9
- 1099
- Backup Withholding
- MSME

## 5.4 Organization / Registration Data

- Multiple locations
- State
- City
- GSTIN per location
- Primary location

## 5.5 Transaction Tax

- CGST
- SGST
- tax-inclusive total
- tax invoice
- place of supply
- input-tax GL posting

## 5.6 GST Compliance

- GSTR-1 generation
- GSTR-3B generation
- GSTR-2A fetch from GSTN
- GSTR-2B fetch from GSTN
- IMS dashboard
- accept / reject supplier invoice
- GST payment recording
- GSTR-9 generation

## 5.7 e-Way Bill

- transaction linkage
- GSTIN
- vehicle number
- transporter ID
- distance
- total value
- generation date
- expiry date
- statuses

---

# 6. Financial Control Capabilities

- General Ledger
- Voucher linkage
- Posting date
- Created timestamp
- Debit / Credit
- Input CGST GL account
- Cancellation flag
- Manual Journals
- Transaction Locking
- Period Close
- Reopen
- Ledger-level close enforcement
- Budgets
- Reporting Tags
- Cost Centre style dimensions
- Currency master
- Exchange-rate field
- Cash-flow scenarios

---

# 7. Explicitly Observed Limitations / Weaknesses

These are **not assumptions**; they are either explicit in the UI or visible as gaps in the shown screens.

## 7.1 Bill Intake

- No OCR engine in the current deployment
- Scanned images/photos cannot be read

## 7.2 Manual Journal Detail

- Rendered journal voucher does not expose debit/credit lines in the shown screen
- Rendered total shows ₹0.00 while the list shows a non-zero Total Debit

## 7.3 Tax Invoice Presentation

- Tax lines on one AR tax invoice are shown generically as `Tax`
- Supplier bill screen shows clearer CGST/SGST labels

## 7.4 Tax Configuration

Not visible:
- effective dates
- jurisdiction rules
- thresholds
- tax applicability logic
- HSN/SAC mapping
- automatic tax determination

## 7.5 AP Matching / Controls

Not yet evidenced:
- 2-way match
- 3-way match
- GRN matching
- duplicate invoice detection
- payment batch/run
- supplier statement reconciliation
- payment approval workflow

## 7.6 GST Compliance

Not yet evidenced:
- direct GST return submission
- ARN
- amendment filing
- bulk IMS action
- automated mismatch scoring
- GST liability-to-payment reconciliation

## 7.7 e-Way Bill

Not yet evidenced:
- NIC API generation
- cancellation
- extension
- vehicle update
- Part A / Part B workflow

---

# 8. Recommended Evaluation Model for Claude Code

For each screen or capability, classify into one of the following:

## 8.1 Status

- `Implemented`
- `Implemented - Partial`
- `Visible but behavior unconfirmed`
- `Not evidenced`
- `Explicitly unavailable`

## 8.2 Evaluation dimensions

For each capability, evaluate:

1. **Functional completeness**
2. **Workflow depth**
3. **Automation**
4. **Validation**
5. **Accounting integration**
6. **Tax integration**
7. **Auditability**
8. **Configurability**
9. **Exception handling**
10. **Reporting / traceability**
11. **API / external-system integration**
12. **User experience**

## 8.3 Example assessment format

```markdown
### Capability: Supplier Invoice Intake

Status: Implemented - Partial

Current:
- Supplier document upload
- machine-readable extraction
- confidence scoring
- human review
- accept/reject
- draft bill creation

Limitations:
- no OCR
- no duplicate detection shown
- no PO matching shown
- no GST validation shown

Market comparison questions:
- Does competitor support OCR?
- Does competitor auto-detect vendor?
- Does competitor perform 2-way/3-way matching?
- Does competitor support straight-through posting?
- Does competitor flag duplicate invoice number / amount / supplier?
```

---

# 9. Suggested Capability IDs for GAP Analysis

## AP

- `AP-MDM-001` Vendor Master
- `AP-MDM-002` Vendor Bank Details
- `AP-MDM-003` MSME Classification
- `AP-INTAKE-001` Supplier Document Upload
- `AP-INTAKE-002` Field Extraction
- `AP-INTAKE-003` Confidence Scoring
- `AP-INTAKE-004` Human Review
- `AP-BILL-001` Supplier Bill Creation
- `AP-BILL-002` Due Date Tracking
- `AP-BILL-003` Outstanding Balance
- `AP-PAY-001` Vendor Payments
- `AP-PAY-002` Allocated / Unallocated Payments
- `AP-PAY-003` Payment Reconciliation
- `AP-CTRL-001` Transaction Locking
- `AP-CTRL-002` Period Close

## Tax

- `TAX-MDM-001` Tax Master
- `TAX-MDM-002` Group Tax
- `TAX-MDM-003` GSTIN / PAN
- `TAX-LOC-001` Location GSTIN
- `TAX-TXN-001` CGST
- `TAX-TXN-002` SGST
- `TAX-TXN-003` Place of Supply
- `TAX-GL-001` Input GST GL Posting
- `TAX-GST-001` GSTR-1
- `TAX-GST-002` GSTR-3B
- `TAX-GST-003` GSTR-2A
- `TAX-GST-004` GSTR-2B
- `TAX-GST-005` IMS Review
- `TAX-GST-006` GST Payments
- `TAX-GST-007` GSTR-9
- `TAX-EWB-001` e-Way Bill Creation
- `TAX-EWB-002` e-Way Bill Validity

## Accounting / Platform

- `ACC-GL-001` General Ledger
- `ACC-GL-002` Voucher Linkage
- `ACC-JRN-001` Manual Journals
- `ACC-CUR-001` Currency Master
- `ACC-DIM-001` Reporting Tags
- `ACC-BUD-001` Budgets
- `ACC-CF-001` Cash-flow Scenarios
- `ACC-REP-001` Financial Statements

---

# 10. Claude Code Instructions

When evaluating or extending this UI:

1. **Do not invent behavior not evidenced here.**
2. Treat screenshots as current-state product behavior.
3. Distinguish:
   - master-data capability
   - transaction capability
   - accounting-posting capability
   - compliance capability
4. Preserve relationships between source documents and downstream accounting.
5. Preserve auditability and period controls when proposing changes.
6. For AP automation, prioritize:
   - intake
   - matching
   - validation
   - approval
   - payment allocation
   - reconciliation
7. For tax, distinguish:
   - tax configuration
   - tax determination
   - tax calculation
   - tax accounting
   - tax reconciliation
   - filing/compliance
8. For every suggested enhancement, specify:
   - impacted screen
   - data model
   - workflow
   - validations
   - accounting impact
   - tax impact
   - audit requirements
9. Flag any inconsistency between UI labels and actual business role semantics.
10. Use the capability IDs above when creating GAP matrices or implementation tasks.

---

# 11. Recommended Next Evaluation Areas

Highest-value screens/features to inspect or compare next:

- Purchase Requisition detail
- Purchase Order detail
- Bill create/edit form
- Vendor Credit detail
- Payment Made detail
- Bank reconciliation
- Bill-to-PO matching
- Goods receipt / GRN if available
- GST return generated detail
- IMS mismatch detail
- e-Way Bill generated detail
- Currency Adjustments
- Chart of Accounts
- Tax report category
- Payables report category
- Bank account / reconciliation workflow
- Approval configuration

---

# 12. Current-State Summary

The product currently demonstrates a broad accounting stack with:

- unified business partner master
- vendor and customer records
- AP and AR transactions
- supplier bill intake
- GST transaction calculation
- tax master configuration
- location-level GSTIN
- multi-currency support
- payment allocation
- reconciliation states
- general ledger
- manual journals
- transaction locking
- period close
- budgets
- cash-flow simulation
- GST returns
- GSTN data fetch
- IMS review
- GST payments
- GSTR-9
- e-Way Bills
- configurable reporting dimensions

The most important areas for market GAP evaluation are likely to be:

- OCR and intelligent document processing
- duplicate invoice detection
- PO/GRN matching
- approval workflows
- supplier onboarding depth
- payment orchestration/batch execution
- tax determination logic
- GST mismatch automation
- direct statutory filing
- e-Way Bill API lifecycle
- audit detail and source traceability
