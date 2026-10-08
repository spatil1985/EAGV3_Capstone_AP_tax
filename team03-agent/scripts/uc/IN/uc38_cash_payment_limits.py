"""UC-38 — Cash payments above the s.40A(3) limit.

Spec: docs/usecases/IN/uc-38-cash-payment-limits.md.
Question: "Are we paying any vendor in cash above the limit, and losing the tax deduction for it?"

Statute (Income-tax Act 1961 numbering — confirm under the 2025 Act): s.40A(3) disallows in full an
expense paid to a person in a day otherwise than by account-payee cheque/draft or electronic mode above
₹10,000 (₹35,000 for goods-carriage hire); Rule 6DD exceptions. s.269ST (cash receipts) is Team 02's.

Rules:
  cash_payment_disallowed  cash paid to one vendor in one day above the limit (PaymentMade in cash,
                           expenses paid through a cash account); exposure = the day's total,
                           tax effect = total × company tax rate
  cash_payment_planned     an open bill set to be paid in cash with a balance above the limit
  cash_payment_wages       payroll-like accounts paid in cash: reported by count and amount only
"""

import re
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.records import NOT_POSTED

CASH_NAMES = re.compile(r"\bcash\b|petty", re.I)
TRANSPORT = re.compile(r"freight|carriage|transport|cartage|haulage", re.I)
WAGES = re.compile(r"wage|salar|payroll|\bPF\b|\bESI\b", re.I)


def cash_accounts(data) -> set:
    return {a.get("account_name") or a.get("name") for a in data.get("bank_accounts", [])
            if (a.get("account_type") or "").lower() == "cash"}


def cash_outflows(data):
    names = cash_accounts(data)
    for p in data.get("payments", []):
        if (p.get("payment_mode") or "").lower() == "cash" and (p.get("status") or "").lower() not in NOT_POSTED:
            yield "PaymentMade", p, p.get("vendor_id"), p.get("_vendor_id_display"), money(p.get("amount")), ""
    for e in data.get("expenses", []):
        through = str(e.get("paid_through_account") or e.get("paid_through") or "")
        if through and (through in names or CASH_NAMES.search(through)) and \
                (e.get("status") or "").lower() not in ("draft", "void", "cancelled"):
            yield ("Expense", e, e.get("vendor_id") or e.get("customer_id") or e.get("claimant_email"),
                   e.get("_vendor_id_display") or e.get("claimant_email"), money(e.get("amount")),
                   str(e.get("_account_id_display") or ""))


class CashLimits(Rule):
    id = "cash_limit"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        limit = money(ctx.constant("cash_payment_limit_inr"))
        transport_limit = money(ctx.constant("cash_payment_limit_transport_inr"))
        tax_rate = Decimal(str(ctx.constant("company_tax_rate_pct"))) / 100
        days: dict = {}
        wages = []
        for entity, doc, who, name, amount, account in cash_outflows(data):
            if WAGES.search(account):
                wages.append(amount)
                continue
            key = (who or doc["id"], str(doc.get("date"))[:10])
            row = days.setdefault(key, {"name": name, "docs": [], "total": Decimal("0"), "transport": True})
            row["docs"].append(f"{entity} {doc.get('number') or doc['id']}")
            row["total"] += amount
            row["transport"] = row["transport"] and bool(TRANSPORT.search(account))
        for (who, when), row in sorted(days.items(), key=lambda kv: -kv[1]["total"]):
            applied = transport_limit if row["transport"] else limit
            if row["total"] <= applied:
                continue
            effect = (row["total"] * tax_rate).quantize(CENTS)
            yield Finding(
                finding_type="cash_limit", rule="cash_payment_disallowed", severity=self.severity,
                entity_type="VendorDay", entity_id=f"{who}:{when}", entity_ref=f"{row['name']} {when}",
                total_exposure=row["total"], currency=ctx.currency, counterparty_id=who, counterparty_name=row["name"],
                summary=f"{fmt(row['total'], ctx.currency)} paid in cash to {row['name']} on {when}, above the "
                        f"{fmt(applied, ctx.currency)} limit: the expense is disallowed for income tax (s.40A(3)), "
                        f"costing about {fmt(effect, ctx.currency)} in tax.",
                details={"date": when, "daily_total": str(row["total"]), "limit_applied": str(applied),
                         "disallowed_amount": str(row["total"]), "tax_effect": str(effect), "documents": row["docs"]})
        for bill in data.get("bills", []):
            balance = money(bill.get("balance_due"))
            if ((bill.get("payment_gateway") or "").lower() == "cash" and balance > limit
                    and (bill.get("status") or "").lower() not in NOT_POSTED):
                yield Finding(
                    finding_type="cash_limit", rule="cash_payment_planned", severity=60, entity_type="Bill",
                    entity_id=bill["id"], entity_ref=bill.get("number"), total_exposure=balance, currency=ctx.currency,
                    counterparty_id=bill.get("vendor_id"), counterparty_name=bill.get("_vendor_id_display"),
                    summary=f"{bill.get('number')} ({bill.get('_vendor_id_display')}, {fmt(balance, ctx.currency)} due) is "
                            f"set to be paid in cash; above {fmt(limit, ctx.currency)} that disallows it. Pay by bank "
                            f"transfer.", details={"balance_due": str(balance)})
        if wages:
            total = sum(wages, Decimal("0"))
            yield Finding(
                finding_type="cash_limit", rule="cash_payment_wages", severity=40, entity_type="Expenses",
                entity_id="cash-wages", entity_ref=f"{len(wages)} payroll-like cash expenses", total_exposure=total,
                currency=ctx.currency,
                summary=f"{len(wages)} payroll-like expense(s) ({fmt(total, ctx.currency)}) were paid in cash. Reported "
                        f"by count only; payroll records are not read.", details={"count": len(wages)})


class CashPaymentLimits(Playbook):

    @property
    def rules(self):
        return [CashLimits()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(payments=fetcher.list("PaymentMade"), expenses=fetcher.list("Expense"),
                       bills=fetcher.list("Bill"), bank_accounts=fetcher.list("BankAccount"))

    def context(self, data, findings, ctx):
        outs = list(cash_outflows(data))
        return {"cash outflows": len(outs), "cash outflow total": str(sum((o[4] for o in outs), Decimal("0"))),
                "PaymentMade in cash": sum(1 for p in data["payments"] if (p.get("payment_mode") or "") == "cash"),
                "cash accounts": sorted(n for n in cash_accounts(data) if n)}

    def summary(self, outcome, ctx):
        dis = [f for f in outcome.findings if f.rule == "cash_payment_disallowed"]
        plan = [f for f in outcome.findings if f.rule == "cash_payment_planned"]
        total = sum((f.total_exposure for f in dis), Decimal("0"))
        planned = sum((f.total_exposure for f in plan), Decimal("0"))
        return (f"{len(dis)} cash payment(s) above the limit ({fmt(total, ctx.currency)}) will be disallowed for income "
                f"tax. {len(plan)} open bill(s) ({fmt(planned, ctx.currency)}) are set to be paid in cash: pay them by bank "
                f"transfer.")
