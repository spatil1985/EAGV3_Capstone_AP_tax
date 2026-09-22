# AgentSwitch MCP Tool Inventory — India (Suryodaya) — live snapshot

Captured 2026-09-23 against `https://agentswitch.theschoolofai.in` via the real MCP handshake (`initialize` -> `notifications/initialized` -> `tools/list`).

- Account: `team03@theschoolofai.in` (Team 03), role `finance_user`, roles `finance_user, user, agent_user, sales_viewer`
- `allowed_apps`: `accounting, agent, crm, approvals`
- Company: `5cbe5a55-af74-4363-a436-f5350593114c` (Suryodaya Precision Works Pvt. Ltd.)
- Locale: IN / gst

**Total tools visible to this account/role: 468**, grouped into **142** entity/endpoint groups below.

Tools are scoped per-caller — this is not the platform's full tool catalog, only what this role + app entitlements + row scope permit. See the companion [US/Keystone inventory](mcp_tool_inventory_us.md) for comparison.


---

## Group index

- [Account](#account) (2)
- [AccountantPreferences](#accountantpreferences) (2)
- [AccountingLocale](#accountinglocale) (2)
- [AccountingPeriod](#accountingperiod) (2)
- [AccountPlan](#accountplan) (2)
- [AcctDocument](#acctdocument) (4)
- [Activity](#activity) (2)
- [AddressBook](#addressbook) (5)
- [AddressBookEntry](#addressbookentry) (5)
- [AgentEscalation](#agentescalation) (4)
- [AgentFloorConfig](#agentfloorconfig) (2)
- [AgentJob](#agentjob) (2)
- [AgentJobStep](#agentjobstep) (2)
- [AgentLedgerSeal](#agentledgerseal) (2)
- [AgentMemory](#agentmemory) (4)
- [AgentMessage](#agentmessage) (2)
- [AgentPersona](#agentpersona) (3)
- [AgentPrivacyEvent](#agentprivacyevent) (2)
- [AgentProvider](#agentprovider) (2)
- [AgentRetentionRule](#agentretentionrule) (2)
- [AgentRunbook](#agentrunbook) (2)
- [AgentRunbookRun](#agentrunbookrun) (2)
- [AgentSeat](#agentseat) (2)
- [AgentSession](#agentsession) (8)
- [AgentSkill](#agentskill) (2)
- [AgentTask](#agenttask) (9)
- [AgentTodo](#agenttodo) (4)
- [AgentToolPolicy](#agenttoolpolicy) (2)
- [ApprovalDelegation](#approvaldelegation) (4)
- [ApprovalLog](#approvallog) (2)
- [ApprovalRequest](#approvalrequest) (9)
- [BankAccount](#bankaccount) (4)
- [BankRule](#bankrule) (2)
- [BankTransaction](#banktransaction) (5)
- [Bill](#bill) (11)
- [BillIntakeEvent](#billintakeevent) (2)
- [BillPreferences](#billpreferences) (2)
- [Branding](#branding) (2)
- [Budget](#budget) (2)
- [BugReport](#bugreport) (3)
- [CallNoteDraft](#callnotedraft) (2)
- [CampaignAudience](#campaignaudience) (2)
- [Company](#company) (2)
- [ContactGroup](#contactgroup) (5)
- [ContactGroupMember](#contactgroupmember) (5)
- [CreditNote](#creditnote) (8)
- [CreditNotePreferences](#creditnotepreferences) (2)
- [CRMPreferences](#crmpreferences) (2)
- [CurrencyConfig](#currencyconfig) (2)
- [CustomerVendorPreferences](#customervendorpreferences) (2)
- [Deal](#deal) (2)
- [DeliveryChallan](#deliverychallan) (9)
- [DeliveryChallanPreferences](#deliverychallanpreferences) (2)
- [DigitalSignaturePreferences](#digitalsignaturepreferences) (2)
- [DirectTaxPreferences](#directtaxpreferences) (2)
- [EInvoicingPreferences](#einvoicingpreferences) (2)
- [EmailNotification](#emailnotification) (2)
- [endpoint.accounting](#endpoint-accounting) (7)
- [endpoint.agent](#endpoint-agent) (2)
- [endpoint.agent_governance](#endpoint-agent-governance) (7)
- [endpoint.approvals](#endpoint-approvals) (6)
- [endpoint.calendar](#endpoint-calendar) (1)
- [endpoint.contracts](#endpoint-contracts) (1)
- [endpoint.crm](#endpoint-crm) (5)
- [endpoint.email](#endpoint-email) (1)
- [endpoint.inventory](#endpoint-inventory) (1)
- [endpoint.job_ledger](#endpoint-job-ledger) (4)
- [endpoint.make](#endpoint-make) (1)
- [endpoint.mission_control](#endpoint-mission-control) (4)
- [endpoint.people_directory](#endpoint-people-directory) (1)
- [endpoint.public](#endpoint-public) (4)
- [endpoint.storefront](#endpoint-storefront) (10)
- [EstimatePreferences](#estimatepreferences) (2)
- [EWayBill](#ewaybill) (6)
- [EWayBillPreferences](#ewaybillpreferences) (2)
- [ExchangeRate](#exchangerate) (2)
- [ExemptionCertificate](#exemptioncertificate) (2)
- [Expense](#expense) (6)
- [ExpensePreferences](#expensepreferences) (2)
- [FileAttachment](#fileattachment) (4)
- [GeneralPreferences](#generalpreferences) (2)
- [GLEntry](#glentry) (2)
- [Goal](#goal) (2)
- [GSTReturn](#gstreturn) (2)
- [Invoice](#invoice) (11)
- [InvoicePreferences](#invoicepreferences) (2)
- [Item](#item) (4)
- [ItemPreferences](#itempreferences) (2)
- [JournalEntry](#journalentry) (2)
- [Lead](#lead) (2)
- [LedgerRetentionEvent](#ledgerretentionevent) (2)
- [LedgerRetentionPolicy](#ledgerretentionpolicy) (2)
- [Location](#location) (2)
- [MSMEPreferences](#msmepreferences) (2)
- [Note](#note) (2)
- [Notification](#notification) (2)
- [NumberSeries](#numberseries) (2)
- [OnlinePaymentPreferences](#onlinepaymentpreferences) (2)
- [OrgProfile](#orgprofile) (2)
- [Party](#party) (4)
- [PartyRelationship](#partyrelationship) (4)
- [Payment](#payment) (2)
- [PaymentMade](#paymentmade) (6)
- [PaymentMadePreferences](#paymentmadepreferences) (2)
- [PaymentReceived](#paymentreceived) (6)
- [PaymentReceivedPreferences](#paymentreceivedpreferences) (2)
- [PaymentReminder](#paymentreminder) (2)
- [PDFTemplate](#pdftemplate) (2)
- [Pipeline](#pipeline) (2)
- [Plugin](#plugin) (2)
- [PortalPreferences](#portalpreferences) (2)
- [PrivacyAuditEvent](#privacyauditevent) (2)
- [PrivacyRequest](#privacyrequest) (4)
- [ProjectPreferences](#projectpreferences) (2)
- [PurchaseOrder](#purchaseorder) (10)
- [PurchaseOrderPreferences](#purchaseorderpreferences) (2)
- [PurchaseRequisition](#purchaserequisition) (12)
- [PurchaseRfq](#purchaserfq) (7)
- [Quotation](#quotation) (4)
- [RecurringBill](#recurringbill) (4)
- [RecurringExpense](#recurringexpense) (4)
- [RecurringInvoice](#recurringinvoice) (4)
- [RecurringInvoicePreferences](#recurringinvoicepreferences) (2)
- [ReportingTag](#reportingtag) (2)
- [RetainerInvoice](#retainerinvoice) (8)
- [SalesOrder](#salesorder) (5)
- [SalesOrderPreferences](#salesorderpreferences) (2)
- [SupplierQuotation](#supplierquotation) (6)
- [Tax](#tax) (2)
- [TaxExemption](#taxexemption) (2)
- [TaxGroup](#taxgroup) (2)
- [TaxJurisdiction](#taxjurisdiction) (2)
- [TaxNexus](#taxnexus) (2)
- [TaxRateServiceConfig](#taxrateserviceconfig) (2)
- [TimesheetPreferences](#timesheetpreferences) (2)
- [tools](#tools) (2)
- [TransactionLock](#transactionlock) (2)
- [UserCompany](#usercompany) (2)
- [UserPreference](#userpreference) (5)
- [VendorCredit](#vendorcredit) (8)
- [VendorCreditPreferences](#vendorcreditpreferences) (2)
- [VendorPortalPreferences](#vendorportalpreferences) (2)

---

## Account

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Account.get` | Get a single Account record by ID | READ | read |
| `Account.list` | List Account records with optional filters | READ | read |

## AccountantPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AccountantPreferences.get` | Get a single AccountantPreferences record by ID | READ | read |
| `AccountantPreferences.list` | List AccountantPreferences records with optional filters | READ | read |

## AccountingLocale

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AccountingLocale.get` | Get a single AccountingLocale record by ID | READ | read |
| `AccountingLocale.list` | List AccountingLocale records with optional filters | READ | read |

## AccountingPeriod

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AccountingPeriod.get` | Get a single AccountingPeriod record by ID | READ | read |
| `AccountingPeriod.list` | List AccountingPeriod records with optional filters | READ | read |

## AccountPlan

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AccountPlan.get` | Get a single AccountPlan record by ID | READ | read |
| `AccountPlan.list` | List AccountPlan records with optional filters | READ | read |

## AcctDocument

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AcctDocument.create` | Create a new AcctDocument record | WRITE | create |
| `AcctDocument.get` | Get a single AcctDocument record by ID | READ | read |
| `AcctDocument.list` | List AcctDocument records with optional filters | READ | read |
| `AcctDocument.update` | Update an existing AcctDocument record | WRITE | write |

## Activity

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Activity.get` | Get a single Activity record by ID | READ | read |
| `Activity.list` | List Activity records with optional filters | READ | read |

## AddressBook

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AddressBook.create` | Create a new AddressBook record | WRITE | create |
| `AddressBook.delete` | Delete a AddressBook record by ID | DESTRUCTIVE | delete |
| `AddressBook.get` | Get a single AddressBook record by ID | READ | read |
| `AddressBook.list` | List AddressBook records with optional filters | READ | read |
| `AddressBook.update` | Update an existing AddressBook record | WRITE | write |

## AddressBookEntry

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AddressBookEntry.create` | Create a new AddressBookEntry record | WRITE | create |
| `AddressBookEntry.delete` | Delete a AddressBookEntry record by ID | DESTRUCTIVE | delete |
| `AddressBookEntry.get` | Get a single AddressBookEntry record by ID | READ | read |
| `AddressBookEntry.list` | List AddressBookEntry records with optional filters | READ | read |
| `AddressBookEntry.update` | Update an existing AddressBookEntry record | WRITE | write |

## AgentEscalation

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentEscalation.create` | Create a new AgentEscalation record | WRITE | create |
| `AgentEscalation.get` | Get a single AgentEscalation record by ID | READ | read |
| `AgentEscalation.list` | List AgentEscalation records with optional filters | READ | read |
| `AgentEscalation.update` | Update an existing AgentEscalation record | WRITE | write |

## AgentFloorConfig

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentFloorConfig.get` | Get a single AgentFloorConfig record by ID | READ | read |
| `AgentFloorConfig.list` | List AgentFloorConfig records with optional filters | READ | read |

## AgentJob

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentJob.get` | Get a single AgentJob record by ID | READ | read |
| `AgentJob.list` | List AgentJob records with optional filters | READ | read |

## AgentJobStep

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentJobStep.get` | Get a single AgentJobStep record by ID | READ | read |
| `AgentJobStep.list` | List AgentJobStep records with optional filters | READ | read |

## AgentLedgerSeal

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentLedgerSeal.get` | Get a single AgentLedgerSeal record by ID | READ | read |
| `AgentLedgerSeal.list` | List AgentLedgerSeal records with optional filters | READ | read |

## AgentMemory

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentMemory.create` | Create a new AgentMemory record | WRITE | create |
| `AgentMemory.get` | Get a single AgentMemory record by ID | READ | read |
| `AgentMemory.list` | List AgentMemory records with optional filters | READ | read |
| `AgentMemory.update` | Update an existing AgentMemory record | WRITE | write |

## AgentMessage

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentMessage.get` | Get a single AgentMessage record by ID | READ | read |
| `AgentMessage.list` | List AgentMessage records with optional filters | READ | read |

## AgentPersona

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentPersona.daily_limits` | Tokens and USD spend each agent persona you can see has used today against its daily limits (tokens_used_today / daily_token_budget, spen... | READ | ['AgentPersona.read'] |
| `AgentPersona.get` | Get a single AgentPersona record by ID | READ | read |
| `AgentPersona.list` | List AgentPersona records with optional filters | READ | read |

## AgentPrivacyEvent

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentPrivacyEvent.get` | Get a single AgentPrivacyEvent record by ID | READ | read |
| `AgentPrivacyEvent.list` | List AgentPrivacyEvent records with optional filters | READ | read |

## AgentProvider

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentProvider.get` | Get a single AgentProvider record by ID | READ | read |
| `AgentProvider.list` | List AgentProvider records with optional filters | READ | read |

## AgentRetentionRule

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentRetentionRule.get` | Get a single AgentRetentionRule record by ID | READ | read |
| `AgentRetentionRule.list` | List AgentRetentionRule records with optional filters | READ | read |

## AgentRunbook

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentRunbook.get` | Get a single AgentRunbook record by ID | READ | read |
| `AgentRunbook.list` | List AgentRunbook records with optional filters | READ | read |

## AgentRunbookRun

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentRunbookRun.get` | Get a single AgentRunbookRun record by ID | READ | read |
| `AgentRunbookRun.list` | List AgentRunbookRun records with optional filters | READ | read |

## AgentSeat

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentSeat.get` | Get a single AgentSeat record by ID | READ | read |
| `AgentSeat.list` | List AgentSeat records with optional filters | READ | read |

## AgentSession

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentSession.close.active.closed` | Transition AgentSession from 'active' to 'closed' | WRITE | submit |
| `AgentSession.close.idle.closed` | Transition AgentSession from 'idle' to 'closed' | WRITE | submit |
| `AgentSession.create` | Create a new AgentSession record | WRITE | create |
| `AgentSession.get` | Get a single AgentSession record by ID | READ | read |
| `AgentSession.list` | List AgentSession records with optional filters | READ | read |
| `AgentSession.pause` | Transition AgentSession from 'active' to 'idle' | WRITE | submit |
| `AgentSession.resume` | Transition AgentSession from 'idle' to 'active' | WRITE | submit |
| `AgentSession.update` | Update an existing AgentSession record | WRITE | write |

## AgentSkill

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentSkill.get` | Get a single AgentSkill record by ID | READ | read |
| `AgentSkill.list` | List AgentSkill records with optional filters | READ | read |

## AgentTask

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentTask.complete` | Transition AgentTask from 'active' to 'completed' | WRITE | submit |
| `AgentTask.create` | Create a new AgentTask record | WRITE | create |
| `AgentTask.fail` | Transition AgentTask from 'active' to 'failed' | WRITE | submit |
| `AgentTask.get` | Get a single AgentTask record by ID | READ | read |
| `AgentTask.list` | List AgentTask records with optional filters | READ | read |
| `AgentTask.pause` | Transition AgentTask from 'active' to 'paused' | WRITE | submit |
| `AgentTask.resume` | Transition AgentTask from 'paused' to 'active' | WRITE | submit |
| `AgentTask.run_now` | Run an agent task immediately. | WRITE | ['AgentTask.submit'] |
| `AgentTask.update` | Update an existing AgentTask record | WRITE | write |

## AgentTodo

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentTodo.create` | Create a new AgentTodo record | WRITE | create |
| `AgentTodo.get` | Get a single AgentTodo record by ID | READ | read |
| `AgentTodo.list` | List AgentTodo records with optional filters | READ | read |
| `AgentTodo.update` | Update an existing AgentTodo record | WRITE | write |

## AgentToolPolicy

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `AgentToolPolicy.get` | Get a single AgentToolPolicy record by ID | READ | read |
| `AgentToolPolicy.list` | List AgentToolPolicy records with optional filters | READ | read |

## ApprovalDelegation

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ApprovalDelegation.create` | Create a new ApprovalDelegation record | WRITE | create |
| `ApprovalDelegation.get` | Get a single ApprovalDelegation record by ID | READ | read |
| `ApprovalDelegation.list` | List ApprovalDelegation records with optional filters | READ | read |
| `ApprovalDelegation.update` | Update an existing ApprovalDelegation record | WRITE | write |

## ApprovalLog

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ApprovalLog.get` | Get a single ApprovalLog record by ID | READ | read |
| `ApprovalLog.list` | List ApprovalLog records with optional filters | READ | read |

## ApprovalRequest

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ApprovalRequest.create` | Create a new ApprovalRequest record | WRITE | create |
| `ApprovalRequest.get` | Get a single ApprovalRequest record by ID | READ | read |
| `ApprovalRequest.list` | List ApprovalRequest records with optional filters | READ | read |
| `ApprovalRequest.recall.in_review.recalled` | Transition ApprovalRequest from 'in_review' to 'recalled' | WRITE | submit |
| `ApprovalRequest.recall.pending.recalled` | Transition ApprovalRequest from 'pending' to 'recalled' | WRITE | submit |
| `ApprovalRequest.resubmit.recalled.pending` | Transition ApprovalRequest from 'recalled' to 'pending' | WRITE | submit |
| `ApprovalRequest.resubmit.rejected.pending` | Transition ApprovalRequest from 'rejected' to 'pending' | WRITE | submit |
| `ApprovalRequest.submit_for_approval` | Transition ApprovalRequest from 'draft' to 'pending' | WRITE | submit |
| `ApprovalRequest.update` | Update an existing ApprovalRequest record | WRITE | write |

## BankAccount

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `BankAccount.create` | Create a new BankAccount record | WRITE | create |
| `BankAccount.get` | Get a single BankAccount record by ID | READ | read |
| `BankAccount.list` | List BankAccount records with optional filters | READ | read |
| `BankAccount.update` | Update an existing BankAccount record | WRITE | write |

## BankRule

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `BankRule.get` | Get a single BankRule record by ID | READ | read |
| `BankRule.list` | List BankRule records with optional filters | READ | read |

## BankTransaction

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `BankTransaction.create` | Create a new BankTransaction record | WRITE | create |
| `BankTransaction.get` | Get a single BankTransaction record by ID | READ | read |
| `BankTransaction.list` | List BankTransaction records with optional filters | READ | read |
| `BankTransaction.match_voucher` | Match a bank transaction to the voucher it settles. | WRITE | ['BankTransaction.write'] |
| `BankTransaction.update` | Update an existing BankTransaction record | WRITE | write |

## Bill

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Bill.approval.submit` | Submit a Bill for approval (approval_status -> pending_approval). | WRITE | ['Bill.submit'] |
| `Bill.create` | Create a new Bill record | WRITE | create |
| `Bill.get` | Get a single Bill record by ID | READ | read |
| `Bill.list` | List Bill records with optional filters | READ | read |
| `Bill.open` | Transition Bill from 'draft' to 'open' | POSTING | submit |
| `Bill.record_full_payment.open.paid` | Transition Bill from 'open' to 'paid' | WRITE | submit |
| `Bill.record_full_payment.overdue.paid` | Transition Bill from 'overdue' to 'paid' | WRITE | submit |
| `Bill.record_full_payment.partially_paid.paid` | Transition Bill from 'partially_paid' to 'paid' | WRITE | submit |
| `Bill.record_partial_payment` | Transition Bill from 'open' to 'partially_paid' | WRITE | submit |
| `Bill.submit` | Transition Bill from 'draft' to 'open' | POSTING | submit |
| `Bill.update` | Update an existing Bill record | WRITE | write |

## BillIntakeEvent

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `BillIntakeEvent.get` | Get a single BillIntakeEvent record by ID | READ | read |
| `BillIntakeEvent.list` | List BillIntakeEvent records with optional filters | READ | read |

## BillPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `BillPreferences.get` | Get a single BillPreferences record by ID | READ | read |
| `BillPreferences.list` | List BillPreferences records with optional filters | READ | read |

## Branding

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Branding.get` | Get a single Branding record by ID | READ | read |
| `Branding.list` | List Branding records with optional filters | READ | read |

## Budget

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Budget.get` | Get a single Budget record by ID | READ | read |
| `Budget.list` | List Budget records with optional filters | READ | read |

## BugReport

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `BugReport.create` | Create a new BugReport record | WRITE | create |
| `BugReport.get` | Get a single BugReport record by ID | READ | read |
| `BugReport.list` | List BugReport records with optional filters | READ | read |

## CallNoteDraft

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CallNoteDraft.get` | Get a single CallNoteDraft record by ID | READ | read |
| `CallNoteDraft.list` | List CallNoteDraft records with optional filters | READ | read |

## CampaignAudience

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CampaignAudience.get` | Get a single CampaignAudience record by ID | READ | read |
| `CampaignAudience.list` | List CampaignAudience records with optional filters | READ | read |

## Company

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Company.get` | Get a single Company record by ID | READ | read |
| `Company.list` | List Company records with optional filters | READ | read |

## ContactGroup

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ContactGroup.create` | Create a new ContactGroup record | WRITE | create |
| `ContactGroup.delete` | Delete a ContactGroup record by ID | DESTRUCTIVE | delete |
| `ContactGroup.get` | Get a single ContactGroup record by ID | READ | read |
| `ContactGroup.list` | List ContactGroup records with optional filters | READ | read |
| `ContactGroup.update` | Update an existing ContactGroup record | WRITE | write |

## ContactGroupMember

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ContactGroupMember.create` | Create a new ContactGroupMember record | WRITE | create |
| `ContactGroupMember.delete` | Delete a ContactGroupMember record by ID | DESTRUCTIVE | delete |
| `ContactGroupMember.get` | Get a single ContactGroupMember record by ID | READ | read |
| `ContactGroupMember.list` | List ContactGroupMember records with optional filters | READ | read |
| `ContactGroupMember.update` | Update an existing ContactGroupMember record | WRITE | write |

## CreditNote

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CreditNote.apply_to_invoice` | Apply part or all of an open credit note to an invoice. | WRITE | ['CreditNote.write', 'Invoice.write'] |
| `CreditNote.approval.submit` | Submit a CreditNote for approval (approval_status -> pending_approval). | WRITE | ['CreditNote.submit'] |
| `CreditNote.close` | Transition CreditNote from 'open' to 'closed' | POSTING | submit |
| `CreditNote.create` | Create a new CreditNote record | WRITE | create |
| `CreditNote.get` | Get a single CreditNote record by ID | READ | read |
| `CreditNote.list` | List CreditNote records with optional filters | READ | read |
| `CreditNote.open` | Transition CreditNote from 'draft' to 'open' | POSTING | submit |
| `CreditNote.update` | Update an existing CreditNote record | WRITE | write |

## CreditNotePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CreditNotePreferences.get` | Get a single CreditNotePreferences record by ID | READ | read |
| `CreditNotePreferences.list` | List CreditNotePreferences records with optional filters | READ | read |

## CRMPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CRMPreferences.get` | Get a single CRMPreferences record by ID | READ | read |
| `CRMPreferences.list` | List CRMPreferences records with optional filters | READ | read |

## CurrencyConfig

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CurrencyConfig.get` | Get a single CurrencyConfig record by ID | READ | read |
| `CurrencyConfig.list` | List CurrencyConfig records with optional filters | READ | read |

## CustomerVendorPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `CustomerVendorPreferences.get` | Get a single CustomerVendorPreferences record by ID | READ | read |
| `CustomerVendorPreferences.list` | List CustomerVendorPreferences records with optional filters | READ | read |

## Deal

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Deal.get` | Get a single Deal record by ID | READ | read |
| `Deal.list` | List Deal records with optional filters | READ | read |

## DeliveryChallan

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `DeliveryChallan.convert_to_invoice` | Transition DeliveryChallan from 'delivered' to 'invoiced' | WRITE | submit |
| `DeliveryChallan.create` | Create a new DeliveryChallan record | WRITE | create |
| `DeliveryChallan.get` | Get a single DeliveryChallan record by ID | READ | read |
| `DeliveryChallan.list` | List DeliveryChallan records with optional filters | READ | read |
| `DeliveryChallan.make.Invoice` | Create a Invoice from a DeliveryChallan through its document chain; optional fields override the mapped values. | WRITE | ['DeliveryChallan.read', 'Invoice.create'] |
| `DeliveryChallan.mark_delivered` | Transition DeliveryChallan from 'draft' to 'delivered' | WRITE | submit |
| `DeliveryChallan.mark_returned.delivered.returned` | Transition DeliveryChallan from 'delivered' to 'returned' | WRITE | submit |
| `DeliveryChallan.mark_returned.invoiced.returned` | Transition DeliveryChallan from 'invoiced' to 'returned' | WRITE | submit |
| `DeliveryChallan.update` | Update an existing DeliveryChallan record | WRITE | write |

## DeliveryChallanPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `DeliveryChallanPreferences.get` | Get a single DeliveryChallanPreferences record by ID | READ | read |
| `DeliveryChallanPreferences.list` | List DeliveryChallanPreferences records with optional filters | READ | read |

## DigitalSignaturePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `DigitalSignaturePreferences.get` | Get a single DigitalSignaturePreferences record by ID | READ | read |
| `DigitalSignaturePreferences.list` | List DigitalSignaturePreferences records with optional filters | READ | read |

## DirectTaxPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `DirectTaxPreferences.get` | Get a single DirectTaxPreferences record by ID | READ | read |
| `DirectTaxPreferences.list` | List DirectTaxPreferences records with optional filters | READ | read |

## EInvoicingPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `EInvoicingPreferences.get` | Get a single EInvoicingPreferences record by ID | READ | read |
| `EInvoicingPreferences.list` | List EInvoicingPreferences records with optional filters | READ | read |

## EmailNotification

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `EmailNotification.get` | Get a single EmailNotification record by ID | READ | read |
| `EmailNotification.list` | List EmailNotification records with optional filters | READ | read |

## endpoint.accounting

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.accounting.bill_intake.accept` | accounting-OP3. Creates one DRAFT Bill from a reviewed document. Never submits, never posts, never pays. | WRITE | Bill.create |
| `endpoint.accounting.bill_intake.extract` | accounting-OP3. Reads the stored document's text layer and proposes candidate Bill fields, each with a confidence, the rule that produced... | WRITE | AcctDocument.write |
| `endpoint.accounting.bill_intake.queue` | accounting-OP3. Read-only review queue for OCR-assisted bill intake: documents waiting for a person, the candidate fields the reader prop... | READ | AcctDocument.read |
| `endpoint.accounting.bill_intake.reject` | accounting-OP3. Records that a document is not a payable, with a required reason. Writes no Bill. | WRITE | AcctDocument.write |
| `endpoint.accounting.bill_match` | C-048. Read-only three-way match of one Bill (or payable Invoice) against its purchase order and receipt: per line the PO rate, billed ra... | WRITE | Bill.read |
| `endpoint.accounting.cash_flow_scenario_sources` | Read-only, active-tenant cash-flow scenario source packet. It returns canonical receivable, payable, and confirmed-order obligations with... | READ | Invoice.read |
| `endpoint.accounting.supplier_quotation.convert_to_po` | C-038. Convert the selected supplier quotation to a Purchase Order with the quoted vendor and per-line rates; mark the quote selected, re... | WRITE | SupplierQuotation.write |

## endpoint.agent

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.agent.skill.export` | POST /api/agent/skill/export | WRITE | AgentSkill.read |
| `endpoint.agent.tasks.run` | Launch one of your own scheduled agent tasks now (body: task_id). Owner-only; a task owned by another user is refused. | WRITE | AgentTask.submit |

## endpoint.agent_governance

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.agent_governance.escalations` | GET /api/agent-governance/escalations | READ | AgentEscalation.read |
| `endpoint.agent_governance.escalations.assignees` | GET /api/agent-governance/escalations/assignees | READ | AgentEscalation.create |
| `endpoint.agent_governance.escalations.raise` | POST /api/agent-governance/escalations/raise | WRITE | AgentEscalation.create |
| `endpoint.agent_governance.escalations.update` | POST /api/agent-governance/escalations/update | WRITE | AgentEscalation.write |
| `endpoint.agent_governance.privacy` | GET /api/agent-governance/privacy | READ | AgentSession.read |
| `endpoint.agent_governance.privacy.forget.preview` | POST /api/agent-governance/privacy/forget/preview | WRITE | AgentPrivacyEvent.read |
| `endpoint.agent_governance.skill_sandbox` | POST /api/agent-governance/skill-sandbox | WRITE | AgentSkill.read |

## endpoint.approvals

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.approvals.analytics` | Get approval analytics and KPIs | READ | ApprovalRequest.read |
| `endpoint.approvals.check_sla` | Run SLA compliance check on all active requests | WRITE | ApprovalRequest.write |
| `endpoint.approvals.my_queue` | The approval requests waiting on the authenticated caller | READ | ApprovalRequest.read |
| `endpoint.approvals.process_decision` | Process an approve/reject decision for an approval step | WRITE | ApprovalRequest.submit |
| `endpoint.approvals.risk_analysis` | Read-only conflict-of-interest, delegation and coverage analysis for approval configuration | READ | ApprovalRequest.read |
| `endpoint.approvals.workload` | Read-only named approver workload, SLA evidence and qualified forecast | READ | ApprovalRequest.read |

## endpoint.calendar

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.calendar.birthdays` | GET /api/calendar/birthdays | READ | Party.read |

## endpoint.contracts

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.contracts.attribute_spend` | Attribute one Bill or Invoice to the Contract it is spend under, or detach it | WRITE | Bill.write |

## endpoint.crm

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.crm.account_plans` | GET /api/crm/account-plans | READ | AccountPlan.read |
| `endpoint.crm.call_note_sources` | GET /api/crm/call-note-sources | READ | Activity.read |
| `endpoint.crm.call_notes` | GET /api/crm/call-notes | READ | CallNoteDraft.read |
| `endpoint.crm.campaign_audiences` | GET /api/crm/campaign-audiences | READ | CampaignAudience.read |
| `endpoint.crm.campaign_audiences.preview` | POST /api/crm/campaign-audiences/preview | WRITE | CampaignAudience.read |

## endpoint.email

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.email.public.subscriber_lists` | GET /api/email/public/subscriber-lists | READ | public |

## endpoint.inventory

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.inventory.shipments` | C-097. The Shipments list: DeliveryChallans and despatch StockEntries in one set of columns (sales order, customer, lines, e-way bill, in... | READ | DeliveryChallan.read |

## endpoint.job_ledger

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.job_ledger.forensics` | GET /api/job-ledger/forensics | READ | AgentLedgerSeal.read |
| `endpoint.job_ledger.replay` | POST /api/job-ledger/replay | POSTING | AgentJobStep.read |
| `endpoint.job_ledger.retention.preview` | POST /api/job-ledger/retention/preview | POSTING | LedgerRetentionEvent.read |
| `endpoint.job_ledger.verify` | POST /api/job-ledger/verify | POSTING | AgentLedgerSeal.read |

## endpoint.make

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.make.orders` | Orders: one row per open Sales Order line — customer, item, quantity, promised and projected dates, stage, top blocker and owner. Read-on... | READ | SalesOrder.read |

## endpoint.mission_control

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.mission_control.incident_timeline` | GET /api/mission-control/incident-timeline | READ | AgentJob.read |
| `endpoint.mission_control.incidents` | GET /api/mission-control/incidents | READ | AgentJob.read |
| `endpoint.mission_control.runbooks` | GET /api/mission-control/runbooks | READ | AgentRunbook.read |
| `endpoint.mission_control.staffing_forecast` | POST /api/mission-control/staffing-forecast | WRITE | AgentJob.read |

## endpoint.people_directory

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.people_directory` | N146. A names-only people directory any member may read: employee id, name and department, and NOTHING else (no salary, bank, statutory i... | READ | Party.read |

## endpoint.public

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.public.collective.book` | POST /api/public/collective/book | WRITE | public |
| `endpoint.public.collective.claim` | POST /api/public/collective/claim | WRITE | public |
| `endpoint.public.collective.meta` | GET /api/public/collective/meta | READ | public |
| `endpoint.public.collective.waitlist` | POST /api/public/collective/waitlist | WRITE | public |

## endpoint.storefront

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `endpoint.storefront.account.orders` | GET /api/storefront/account/orders | READ | public |
| `endpoint.storefront.categories` | GET /api/storefront/categories | READ | public |
| `endpoint.storefront.checkout` | POST /api/storefront/checkout | WRITE | public |
| `endpoint.storefront.locale` | GET /api/storefront/locale | READ | public |
| `endpoint.storefront.notify_me` | POST /api/storefront/notify-me | WRITE | public |
| `endpoint.storefront.order` | GET /api/storefront/order | READ | public |
| `endpoint.storefront.order.claim` | POST /api/storefront/order/claim | WRITE | public |
| `endpoint.storefront.payment.verify` | POST /api/storefront/payment/verify | WRITE | public |
| `endpoint.storefront.products` | GET /api/storefront/products | READ | public |
| `endpoint.storefront.shipping_methods` | GET /api/storefront/shipping-methods | READ | public |

## EstimatePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `EstimatePreferences.get` | Get a single EstimatePreferences record by ID | READ | read |
| `EstimatePreferences.list` | List EstimatePreferences records with optional filters | READ | read |

## EWayBill

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `EWayBill.activate` | Transition EWayBill from 'generated' to 'active' | WRITE | submit |
| `EWayBill.create` | Create a new EWayBill record | WRITE | create |
| `EWayBill.generate` | Transition EWayBill from 'not_generated' to 'generated' | WRITE | submit |
| `EWayBill.get` | Get a single EWayBill record by ID | READ | read |
| `EWayBill.list` | List EWayBill records with optional filters | READ | read |
| `EWayBill.update` | Update an existing EWayBill record | WRITE | write |

## EWayBillPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `EWayBillPreferences.get` | Get a single EWayBillPreferences record by ID | READ | read |
| `EWayBillPreferences.list` | List EWayBillPreferences records with optional filters | READ | read |

## ExchangeRate

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ExchangeRate.get` | Get a single ExchangeRate record by ID | READ | read |
| `ExchangeRate.list` | List ExchangeRate records with optional filters | READ | read |

## ExemptionCertificate

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ExemptionCertificate.get` | Get a single ExemptionCertificate record by ID | READ | read |
| `ExemptionCertificate.list` | List ExemptionCertificate records with optional filters | READ | read |

## Expense

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Expense.approval.submit` | Submit a Expense for approval (approval_status -> pending_approval). | WRITE | ['Expense.submit'] |
| `Expense.create` | Create a new Expense record | WRITE | create |
| `Expense.get` | Get a single Expense record by ID | READ | read |
| `Expense.list` | List Expense records with optional filters | READ | read |
| `Expense.make.Invoice` | Create a Invoice from a Expense through its document chain; optional fields override the mapped values. | WRITE | ['Expense.read', 'Invoice.create'] |
| `Expense.update` | Update an existing Expense record | WRITE | write |

## ExpensePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ExpensePreferences.get` | Get a single ExpensePreferences record by ID | READ | read |
| `ExpensePreferences.list` | List ExpensePreferences records with optional filters | READ | read |

## FileAttachment

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `FileAttachment.create` | Create a new FileAttachment record | WRITE | create |
| `FileAttachment.get` | Get a single FileAttachment record by ID | READ | read |
| `FileAttachment.list` | List FileAttachment records with optional filters | READ | read |
| `FileAttachment.update` | Update an existing FileAttachment record | WRITE | write |

## GeneralPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `GeneralPreferences.get` | Get a single GeneralPreferences record by ID | READ | read |
| `GeneralPreferences.list` | List GeneralPreferences records with optional filters | READ | read |

## GLEntry

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `GLEntry.get` | Get a single GLEntry record by ID | READ | read |
| `GLEntry.list` | List GLEntry records with optional filters | READ | read |

## Goal

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Goal.get` | Get a single Goal record by ID | READ | read |
| `Goal.list` | List Goal records with optional filters | READ | read |

## GSTReturn

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `GSTReturn.get` | Get a single GSTReturn record by ID | READ | read |
| `GSTReturn.list` | List GSTReturn records with optional filters | READ | read |

## Invoice

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Invoice.approval.submit` | Submit a Invoice for approval (approval_status -> pending_approval). | WRITE | ['Invoice.submit'] |
| `Invoice.cancel.draft.cancelled` | Transition Invoice from 'draft' to 'cancelled' | DESTRUCTIVE | submit |
| `Invoice.create` | Create a new Invoice record | WRITE | create |
| `Invoice.get` | Get a single Invoice record by ID | READ | read |
| `Invoice.list` | List Invoice records with optional filters | READ | read |
| `Invoice.record_full_payment.overdue.paid` | Transition Invoice from 'overdue' to 'paid' | WRITE | submit |
| `Invoice.record_full_payment.partially_paid.paid` | Transition Invoice from 'partially_paid' to 'paid' | WRITE | submit |
| `Invoice.record_full_payment.sent.paid` | Transition Invoice from 'sent' to 'paid' | WRITE | submit |
| `Invoice.record_partial_payment` | Transition Invoice from 'sent' to 'partially_paid' | WRITE | submit |
| `Invoice.send` | Transition Invoice from 'draft' to 'sent' | WRITE | submit |
| `Invoice.update` | Update an existing Invoice record | WRITE | write |

## InvoicePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `InvoicePreferences.get` | Get a single InvoicePreferences record by ID | READ | read |
| `InvoicePreferences.list` | List InvoicePreferences records with optional filters | READ | read |

## Item

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Item.create` | Create a new Item record | WRITE | create |
| `Item.get` | Get a single Item record by ID | READ | read |
| `Item.list` | List Item records with optional filters | READ | read |
| `Item.update` | Update an existing Item record | WRITE | write |

## ItemPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ItemPreferences.get` | Get a single ItemPreferences record by ID | READ | read |
| `ItemPreferences.list` | List ItemPreferences records with optional filters | READ | read |

## JournalEntry

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `JournalEntry.get` | Get a single JournalEntry record by ID | READ | read |
| `JournalEntry.list` | List JournalEntry records with optional filters | READ | read |

## Lead

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Lead.get` | Get a single Lead record by ID | READ | read |
| `Lead.list` | List Lead records with optional filters | READ | read |

## LedgerRetentionEvent

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `LedgerRetentionEvent.get` | Get a single LedgerRetentionEvent record by ID | READ | read |
| `LedgerRetentionEvent.list` | List LedgerRetentionEvent records with optional filters | READ | read |

## LedgerRetentionPolicy

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `LedgerRetentionPolicy.get` | Get a single LedgerRetentionPolicy record by ID | READ | read |
| `LedgerRetentionPolicy.list` | List LedgerRetentionPolicy records with optional filters | READ | read |

## Location

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Location.get` | Get a single Location record by ID | READ | read |
| `Location.list` | List Location records with optional filters | READ | read |

## MSMEPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `MSMEPreferences.get` | Get a single MSMEPreferences record by ID | READ | read |
| `MSMEPreferences.list` | List MSMEPreferences records with optional filters | READ | read |

## Note

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Note.get` | Get a single Note record by ID | READ | read |
| `Note.list` | List Note records with optional filters | READ | read |

## Notification

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Notification.get` | Get a single Notification record by ID | READ | read |
| `Notification.list` | List Notification records with optional filters | READ | read |

## NumberSeries

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `NumberSeries.get` | Get a single NumberSeries record by ID | READ | read |
| `NumberSeries.list` | List NumberSeries records with optional filters | READ | read |

## OnlinePaymentPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `OnlinePaymentPreferences.get` | Get a single OnlinePaymentPreferences record by ID | READ | read |
| `OnlinePaymentPreferences.list` | List OnlinePaymentPreferences records with optional filters | READ | read |

## OrgProfile

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `OrgProfile.get` | Get a single OrgProfile record by ID | READ | read |
| `OrgProfile.list` | List OrgProfile records with optional filters | READ | read |

## Party

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Party.create` | Create a new Party record | WRITE | create |
| `Party.get` | Get a single Party record by ID | READ | read |
| `Party.list` | List Party records with optional filters | READ | read |
| `Party.update` | Update an existing Party record | WRITE | write |

## PartyRelationship

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PartyRelationship.create` | Create a new PartyRelationship record | WRITE | create |
| `PartyRelationship.get` | Get a single PartyRelationship record by ID | READ | read |
| `PartyRelationship.list` | List PartyRelationship records with optional filters | READ | read |
| `PartyRelationship.update` | Update an existing PartyRelationship record | WRITE | write |

## Payment

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Payment.get` | Get a single Payment record by ID | READ | read |
| `Payment.list` | List Payment records with optional filters | READ | read |

## PaymentMade

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PaymentMade.cancel` | Transition PaymentMade from 'draft' to 'cancelled' | DESTRUCTIVE | submit |
| `PaymentMade.create` | Create a new PaymentMade record | WRITE | create |
| `PaymentMade.get` | Get a single PaymentMade record by ID | READ | read |
| `PaymentMade.list` | List PaymentMade records with optional filters | READ | read |
| `PaymentMade.mark_paid` | Transition PaymentMade from 'draft' to 'paid' | POSTING | submit |
| `PaymentMade.update` | Update an existing PaymentMade record | WRITE | write |

## PaymentMadePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PaymentMadePreferences.get` | Get a single PaymentMadePreferences record by ID | READ | read |
| `PaymentMadePreferences.list` | List PaymentMadePreferences records with optional filters | READ | read |

## PaymentReceived

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PaymentReceived.cancel` | Transition PaymentReceived from 'draft' to 'cancelled' | DESTRUCTIVE | submit |
| `PaymentReceived.create` | Create a new PaymentReceived record | WRITE | create |
| `PaymentReceived.get` | Get a single PaymentReceived record by ID | READ | read |
| `PaymentReceived.list` | List PaymentReceived records with optional filters | READ | read |
| `PaymentReceived.mark_received` | Transition PaymentReceived from 'draft' to 'paid' | POSTING | submit |
| `PaymentReceived.update` | Update an existing PaymentReceived record | WRITE | write |

## PaymentReceivedPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PaymentReceivedPreferences.get` | Get a single PaymentReceivedPreferences record by ID | READ | read |
| `PaymentReceivedPreferences.list` | List PaymentReceivedPreferences records with optional filters | READ | read |

## PaymentReminder

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PaymentReminder.get` | Get a single PaymentReminder record by ID | READ | read |
| `PaymentReminder.list` | List PaymentReminder records with optional filters | READ | read |

## PDFTemplate

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PDFTemplate.get` | Get a single PDFTemplate record by ID | READ | read |
| `PDFTemplate.list` | List PDFTemplate records with optional filters | READ | read |

## Pipeline

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Pipeline.get` | Get a single Pipeline record by ID | READ | read |
| `Pipeline.list` | List Pipeline records with optional filters | READ | read |

## Plugin

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Plugin.get` | Get a single Plugin record by ID | READ | read |
| `Plugin.list` | List Plugin records with optional filters | READ | read |

## PortalPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PortalPreferences.get` | Get a single PortalPreferences record by ID | READ | read |
| `PortalPreferences.list` | List PortalPreferences records with optional filters | READ | read |

## PrivacyAuditEvent

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PrivacyAuditEvent.get` | Get a single PrivacyAuditEvent record by ID | READ | read |
| `PrivacyAuditEvent.list` | List PrivacyAuditEvent records with optional filters | READ | read |

## PrivacyRequest

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PrivacyRequest.create` | Create a new PrivacyRequest record | WRITE | create |
| `PrivacyRequest.get` | Get a single PrivacyRequest record by ID | READ | read |
| `PrivacyRequest.list` | List PrivacyRequest records with optional filters | READ | read |
| `PrivacyRequest.update` | Update an existing PrivacyRequest record | WRITE | write |

## ProjectPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ProjectPreferences.get` | Get a single ProjectPreferences record by ID | READ | read |
| `ProjectPreferences.list` | List ProjectPreferences records with optional filters | READ | read |

## PurchaseOrder

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PurchaseOrder.approval.submit` | Submit a PurchaseOrder for approval (approval_status -> pending_approval). | WRITE | ['PurchaseOrder.submit'] |
| `PurchaseOrder.cancel.draft.cancelled` | Transition PurchaseOrder from 'draft' to 'cancelled' | DESTRUCTIVE | submit |
| `PurchaseOrder.confirm` | Transition PurchaseOrder from 'draft' to 'open' | WRITE | submit |
| `PurchaseOrder.convert_to_bill` | Create a draft Bill from a purchase order. | WRITE | ['Bill.create', 'PurchaseOrder.read'] |
| `PurchaseOrder.create` | Create a new PurchaseOrder record | WRITE | create |
| `PurchaseOrder.get` | Get a single PurchaseOrder record by ID | READ | read |
| `PurchaseOrder.list` | List PurchaseOrder records with optional filters | READ | read |
| `PurchaseOrder.make.Bill` | Create a Bill from a PurchaseOrder through its document chain; optional fields override the mapped values. | WRITE | ['PurchaseOrder.read', 'Bill.create'] |
| `PurchaseOrder.mark_billed` | Transition PurchaseOrder from 'open' to 'billed' | WRITE | submit |
| `PurchaseOrder.update` | Update an existing PurchaseOrder record | WRITE | write |

## PurchaseOrderPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PurchaseOrderPreferences.get` | Get a single PurchaseOrderPreferences record by ID | READ | read |
| `PurchaseOrderPreferences.list` | List PurchaseOrderPreferences records with optional filters | READ | read |

## PurchaseRequisition

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PurchaseRequisition.approval.submit` | Submit a PurchaseRequisition for approval (approval_status -> pending_approval). | WRITE | ['PurchaseRequisition.submit'] |
| `PurchaseRequisition.approve` | Transition PurchaseRequisition from 'submitted' to 'approved' | WRITE | submit |
| `PurchaseRequisition.cancel.draft.cancelled` | Transition PurchaseRequisition from 'draft' to 'cancelled' | DESTRUCTIVE | submit |
| `PurchaseRequisition.convert_to_po` | Transition PurchaseRequisition from 'approved' to 'ordered' | WRITE | submit |
| `PurchaseRequisition.create` | Create a new PurchaseRequisition record | WRITE | create |
| `PurchaseRequisition.get` | Get a single PurchaseRequisition record by ID | READ | read |
| `PurchaseRequisition.list` | List PurchaseRequisition records with optional filters | READ | read |
| `PurchaseRequisition.make.PurchaseOrder` | Create a PurchaseOrder from a PurchaseRequisition through its document chain; optional fields override the mapped values. | WRITE | ['PurchaseRequisition.read', 'PurchaseOrder.create'] |
| `PurchaseRequisition.reject` | Transition PurchaseRequisition from 'submitted' to 'rejected' | WRITE | submit |
| `PurchaseRequisition.revise` | Transition PurchaseRequisition from 'rejected' to 'draft' | WRITE | submit |
| `PurchaseRequisition.submit_for_approval` | Transition PurchaseRequisition from 'draft' to 'submitted' | WRITE | submit |
| `PurchaseRequisition.update` | Update an existing PurchaseRequisition record | WRITE | write |

## PurchaseRfq

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `PurchaseRfq.cancel.draft.cancelled` | Transition PurchaseRfq from 'draft' to 'cancelled' | DESTRUCTIVE | submit |
| `PurchaseRfq.close` | Transition PurchaseRfq from 'sent' to 'closed' | WRITE | submit |
| `PurchaseRfq.create` | Create a new PurchaseRfq record | WRITE | create |
| `PurchaseRfq.get` | Get a single PurchaseRfq record by ID | READ | read |
| `PurchaseRfq.list` | List PurchaseRfq records with optional filters | READ | read |
| `PurchaseRfq.send_to_suppliers` | Transition PurchaseRfq from 'draft' to 'sent' | WRITE | submit |
| `PurchaseRfq.update` | Update an existing PurchaseRfq record | WRITE | write |

## Quotation

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Quotation.get` | Get a single Quotation record by ID | READ | read |
| `Quotation.list` | List Quotation records with optional filters | READ | read |
| `Quotation.make.Invoice` | Create a Invoice from a Quotation through its document chain; optional fields override the mapped values. | WRITE | ['Quotation.read', 'Invoice.create'] |
| `Quotation.update` | Update an existing Quotation record | WRITE | write |

## RecurringBill

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `RecurringBill.create` | Create a new RecurringBill record | WRITE | create |
| `RecurringBill.get` | Get a single RecurringBill record by ID | READ | read |
| `RecurringBill.list` | List RecurringBill records with optional filters | READ | read |
| `RecurringBill.update` | Update an existing RecurringBill record | WRITE | write |

## RecurringExpense

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `RecurringExpense.create` | Create a new RecurringExpense record | WRITE | create |
| `RecurringExpense.get` | Get a single RecurringExpense record by ID | READ | read |
| `RecurringExpense.list` | List RecurringExpense records with optional filters | READ | read |
| `RecurringExpense.update` | Update an existing RecurringExpense record | WRITE | write |

## RecurringInvoice

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `RecurringInvoice.create` | Create a new RecurringInvoice record | WRITE | create |
| `RecurringInvoice.get` | Get a single RecurringInvoice record by ID | READ | read |
| `RecurringInvoice.list` | List RecurringInvoice records with optional filters | READ | read |
| `RecurringInvoice.update` | Update an existing RecurringInvoice record | WRITE | write |

## RecurringInvoicePreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `RecurringInvoicePreferences.get` | Get a single RecurringInvoicePreferences record by ID | READ | read |
| `RecurringInvoicePreferences.list` | List RecurringInvoicePreferences records with optional filters | READ | read |

## ReportingTag

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `ReportingTag.get` | Get a single ReportingTag record by ID | READ | read |
| `ReportingTag.list` | List ReportingTag records with optional filters | READ | read |

## RetainerInvoice

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `RetainerInvoice.close` | Transition RetainerInvoice from 'paid' to 'closed' | WRITE | submit |
| `RetainerInvoice.create` | Create a new RetainerInvoice record | WRITE | create |
| `RetainerInvoice.get` | Get a single RetainerInvoice record by ID | READ | read |
| `RetainerInvoice.list` | List RetainerInvoice records with optional filters | READ | read |
| `RetainerInvoice.record_payment.draft.paid` | Transition RetainerInvoice from 'draft' to 'paid' | WRITE | submit |
| `RetainerInvoice.record_payment.sent.paid` | Transition RetainerInvoice from 'sent' to 'paid' | WRITE | submit |
| `RetainerInvoice.send` | Transition RetainerInvoice from 'draft' to 'sent' | WRITE | submit |
| `RetainerInvoice.update` | Update an existing RetainerInvoice record | WRITE | write |

## SalesOrder

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `SalesOrder.get` | Get a single SalesOrder record by ID | READ | read |
| `SalesOrder.list` | List SalesOrder records with optional filters | READ | read |
| `SalesOrder.make.DeliveryChallan` | Create a DeliveryChallan from a SalesOrder through its document chain; optional fields override the mapped values. | WRITE | ['SalesOrder.read', 'DeliveryChallan.create'] |
| `SalesOrder.make.Invoice` | Create a Invoice from a SalesOrder through its document chain; optional fields override the mapped values. | WRITE | ['SalesOrder.read', 'Invoice.create'] |
| `SalesOrder.update` | Update an existing SalesOrder record | WRITE | write |

## SalesOrderPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `SalesOrderPreferences.get` | Get a single SalesOrderPreferences record by ID | READ | read |
| `SalesOrderPreferences.list` | List SalesOrderPreferences records with optional filters | READ | read |

## SupplierQuotation

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `SupplierQuotation.create` | Create a new SupplierQuotation record | WRITE | create |
| `SupplierQuotation.get` | Get a single SupplierQuotation record by ID | READ | read |
| `SupplierQuotation.list` | List SupplierQuotation records with optional filters | READ | read |
| `SupplierQuotation.reject` | Transition SupplierQuotation from 'received' to 'rejected' | WRITE | submit |
| `SupplierQuotation.select` | Transition SupplierQuotation from 'received' to 'selected' | WRITE | submit |
| `SupplierQuotation.update` | Update an existing SupplierQuotation record | WRITE | write |

## Tax

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `Tax.get` | Get a single Tax record by ID | READ | read |
| `Tax.list` | List Tax records with optional filters | READ | read |

## TaxExemption

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TaxExemption.get` | Get a single TaxExemption record by ID | READ | read |
| `TaxExemption.list` | List TaxExemption records with optional filters | READ | read |

## TaxGroup

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TaxGroup.get` | Get a single TaxGroup record by ID | READ | read |
| `TaxGroup.list` | List TaxGroup records with optional filters | READ | read |

## TaxJurisdiction

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TaxJurisdiction.get` | Get a single TaxJurisdiction record by ID | READ | read |
| `TaxJurisdiction.list` | List TaxJurisdiction records with optional filters | READ | read |

## TaxNexus

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TaxNexus.get` | Get a single TaxNexus record by ID | READ | read |
| `TaxNexus.list` | List TaxNexus records with optional filters | READ | read |

## TaxRateServiceConfig

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TaxRateServiceConfig.get` | Get a single TaxRateServiceConfig record by ID | READ | read |
| `TaxRateServiceConfig.list` | List TaxRateServiceConfig records with optional filters | READ | read |

## TimesheetPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TimesheetPreferences.get` | Get a single TimesheetPreferences record by ID | READ | read |
| `TimesheetPreferences.list` | List TimesheetPreferences records with optional filters | READ | read |

## tools

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `tools.describe` | Return the full input schema (and description) for tool names you already know, so you can call them without fetching the whole catalogue... | READ | read |
| `tools.search` | Search the tools available to you for a business object or verb, e.g. 'purchase order', 'WO complete', 'stock availability'. Returns the ... | READ | read |

## TransactionLock

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `TransactionLock.get` | Get a single TransactionLock record by ID | READ | read |
| `TransactionLock.list` | List TransactionLock records with optional filters | READ | read |

## UserCompany

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `UserCompany.get` | Get a single UserCompany record by ID | READ | read |
| `UserCompany.list` | List UserCompany records with optional filters | READ | read |

## UserPreference

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `UserPreference.create` | Create a new UserPreference record | WRITE | create |
| `UserPreference.delete` | Delete a UserPreference record by ID | DESTRUCTIVE | delete |
| `UserPreference.get` | Get a single UserPreference record by ID | READ | read |
| `UserPreference.list` | List UserPreference records with optional filters | READ | read |
| `UserPreference.update` | Update an existing UserPreference record | WRITE | write |

## VendorCredit

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `VendorCredit.apply_to_bill` | Apply part or all of an open vendor credit to a bill. | WRITE | ['VendorCredit.write', 'Bill.write'] |
| `VendorCredit.approval.submit` | Submit a VendorCredit for approval (approval_status -> pending_approval). | WRITE | ['VendorCredit.submit'] |
| `VendorCredit.close` | Transition VendorCredit from 'open' to 'closed' | POSTING | submit |
| `VendorCredit.create` | Create a new VendorCredit record | WRITE | create |
| `VendorCredit.get` | Get a single VendorCredit record by ID | READ | read |
| `VendorCredit.list` | List VendorCredit records with optional filters | READ | read |
| `VendorCredit.open` | Transition VendorCredit from 'draft' to 'open' | POSTING | submit |
| `VendorCredit.update` | Update an existing VendorCredit record | WRITE | write |

## VendorCreditPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `VendorCreditPreferences.get` | Get a single VendorCreditPreferences record by ID | READ | read |
| `VendorCreditPreferences.list` | List VendorCreditPreferences records with optional filters | READ | read |

## VendorPortalPreferences

| Tool | Description | Risk | Permission |
|---|---|---|---|
| `VendorPortalPreferences.get` | Get a single VendorPortalPreferences record by ID | READ | read |
| `VendorPortalPreferences.list` | List VendorPortalPreferences records with optional filters | READ | read |
