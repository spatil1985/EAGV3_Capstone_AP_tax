"""US-19 — Bank-to-payables reconciliation (US instance of UC-43).

Spec: docs/usecases/US/us-19-bank-to-payables-reconciliation.md.
Question: "Does every vendor payment in the bank match a payment in our books, and the other way round?"

Same engine as UC-43 (scripts/uc/common/bank_recon.py). On Keystone the platform's voucher links
(PaymentMade / Expense / JournalEntry) are populated and trusted; bank debits carry no payee, so the
payee key can't run, and a debit without a voucher or payee is an unidentified debit. The feed covers
only part of the year — the summary states the window.
"""

from scripts.uc.IN.uc43_bank_to_payables import BankToPayables


class BankToPayablesUS(BankToPayables):
    """UC-43's playbook unchanged; kept as its own class so the US manifest and SOP stand alone."""
