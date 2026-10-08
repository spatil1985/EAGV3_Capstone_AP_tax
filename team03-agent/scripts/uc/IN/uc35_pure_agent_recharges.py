"""UC-35 — Recharged costs and the Rule 33 pure-agent test.

Spec: docs/usecases/IN/uc-35-agency-pure-agent-reimbursements.md.
Question: "When we pass client costs back to them, are we charging GST correctly on the recharge?"

Statute: s.15(2)(c) CGST Act — incidental costs charged to the client are part of the value (taxed at
our service rate); Rule 33 excludes them only for a pure agent (contract clause, no title, actual
amount, shown separately, in addition to our own service). A pure-agent cost is the client's: no ITC.

Rules:
  recharge_unlinked        an invoiced billable expense with no invoice carrying its expense_id, and
                           none matching customer + amount within 30 days (Invoice.expense_id is never
                           set on this tenant — candidate bug)
  reimbursement_undertaxed linked recharge failing the pure-agent test, charged below the service rate
  pure_agent_with_itc      linked recharge passing the test, yet credit claimed on the expense
  billable_not_recharged   billable, still unbilled after 60 days (revenue leakage)
  billable_flag_conflict   aggregate: status unbilled while is_billable is off
Pure-agent contracts live in config/overrides/pure_agent_contracts.yaml (not in the data model).
"""

from datetime import timedelta
from decimal import Decimal

import yaml

from aptax.config import CONFIG_DIR
from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.records import NOT_POSTED

OVERRIDES = CONFIG_DIR / "overrides" / "pure_agent_contracts.yaml"
STALE_DAYS = 60


def pure_agent_customers() -> set:
    try:
        raw = yaml.safe_load(OVERRIDES.read_text(encoding="utf-8")) or {}
    except OSError:
        return set()
    return {c.get("customer_id") for c in raw.get("customers") or [] if c.get("customer_id")}


def find_invoice(exp, invoices):
    linked = [i for i in invoices if i.get("expense_id") == exp["id"]]
    if linked:
        return linked[0], "expense_id"
    when, amount = day(exp.get("date")), money(exp.get("amount"))
    for inv in invoices:
        d = day(inv.get("date"))
        if (inv.get("party_id") == exp.get("customer_id") and d and when and 0 <= (d - when).days <= 30
                and any(money(l.get("amount") or l.get("taxable_amount")) == amount for l in inv.get("items") or [])):
            return inv, "customer+amount+date"
    return None, None


class Recharges(Rule):
    id = "recharge"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        invoices = [i for i in data.get("invoices", []) if (i.get("status") or "").lower() not in NOT_POSTED]
        contracts = data.get("pure_agent", set())
        rate = Decimal(str(ctx.constant("recharge_service_rate_pct")))
        conflicts = []
        for exp in data.get("expenses", []):
            status = (exp.get("status") or "").lower()
            label = exp.get("number") or exp["id"]
            amount, tax = money(exp.get("amount")), money(exp.get("tax_amount"))
            base = dict(entity_type="Expense", entity_id=exp["id"], entity_ref=label, currency=ctx.currency,
                        counterparty_id=exp.get("customer_id"), counterparty_name=exp.get("_customer_id_display"))
            if status == "unbilled" and not exp.get("is_billable"):
                conflicts.append(label)
            if exp.get("is_billable") and status == "unbilled":
                age = (ctx.as_of - day(exp["date"])).days if day(exp.get("date")) else 0
                if age > STALE_DAYS:
                    yield Finding(finding_type="recharge", rule="billable_not_recharged", severity=30,
                                  total_exposure=amount, **base,
                                  summary=f"Billable expense {label} ({fmt(amount, ctx.currency)}) is still unbilled "
                                          f"after {age} days: revenue not recovered.", details={"age_days": age})
            if not (exp.get("is_billable") and status == "invoiced"):
                continue
            inv, how = find_invoice(exp, invoices)
            if not inv:
                yield Finding(finding_type="recharge", rule="recharge_unlinked", severity=45, total_exposure=amount,
                              **base,
                              summary=f"Billable expense {label} ({exp.get('date')}, {fmt(amount, ctx.currency)}) is "
                                      f"marked invoiced, but no invoice links to it, so whether GST was charged on the "
                                      f"recharge can't be checked.",
                              details={"expense_id": exp["id"], "invoice_id": None})
                continue
            line = next((l for l in inv.get("items") or []
                         if money(l.get("amount") or l.get("taxable_amount")) == amount), None)
            line_tax = sum((money(line.get(f"{h}_amount")) for h in ("cgst", "sgst", "igst")), Decimal("0")) if line else Decimal("0")
            test = {"contract_clause": exp.get("customer_id") in contracts, "recovered_at_actual": line is not None,
                    "shown_separately": line is not None and len(inv.get("items") or []) > 1,
                    "no_credit_taken": exp.get("itc_eligibility") in (None, "", "ineligible") or tax == 0}
            if all(test.values()):
                continue
            if test["contract_clause"] and test["recovered_at_actual"] and test["shown_separately"]:
                yield Finding(finding_type="recharge", rule="pure_agent_with_itc", severity=55, total_exposure=tax,
                              **base,
                              summary=f"{label} is recharged as a pure agent on {inv.get('number')}, yet credit "
                                      f"({fmt(tax, ctx.currency)}) was claimed on it: a pure-agent cost is the client's.",
                              details={"invoice_id": inv["id"], "pure_agent_test": test, "linked_by": how})
                continue
            due = (amount * rate / 100).quantize(CENTS)
            if line_tax < due:
                yield Finding(finding_type="recharge", rule="reimbursement_undertaxed", severity=70,
                              total_exposure=due - line_tax, **base,
                              summary=f"{label} recharged on {inv.get('number')} fails the pure-agent test, so "
                                      f"{rate}% ({fmt(due, ctx.currency)}) was due on it; {fmt(line_tax, ctx.currency)} "
                                      f"was charged.",
                              details={"invoice_id": inv["id"], "pure_agent_test": test, "linked_by": how})
        if conflicts:
            yield Finding(finding_type=DATA_QUALITY, rule="billable_flag_conflict", status=DATA_QUALITY, severity=10,
                          entity_type="Expenses", entity_id="billable_flag_conflict",
                          entity_ref=f"{len(conflicts)} expenses", currency=ctx.currency,
                          summary=f"{len(conflicts)} expense(s) have status 'unbilled' while is_billable is off: the "
                                  f"flag and the status disagree.",
                          details={"count": len(conflicts), "expenses": conflicts[:50]})


class PureAgentRecharges(Playbook):

    @property
    def rules(self):
        return [Recharges()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(expenses=fetcher.list("Expense"), invoices=fetcher.list("Invoice", direction="receivable"),
                       pure_agent=pure_agent_customers())

    def context(self, data, findings, ctx):
        exps = data["expenses"]
        return {"billable expenses": sum(1 for e in exps if e.get("is_billable")),
                "… invoiced": sum(1 for e in exps if e.get("is_billable") and (e.get("status") or "") == "invoiced"),
                "invoices carrying expense_id": sum(1 for i in data["invoices"] if i.get("expense_id")),
                "pure-agent contracts on file": len(data["pure_agent"])}

    def summary(self, outcome, ctx):
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        under = sum((f.total_exposure for f in outcome.findings if f.rule == "reimbursement_undertaxed"), Decimal("0"))
        return (f"{n('recharge_unlinked')} invoiced recharge(s) can't be traced to an invoice (no invoice carries an "
                f"expense_id), so their GST can't be checked; {n('reimbursement_undertaxed')} under-taxed "
                f"({fmt(under, ctx.currency)}); {n('pure_agent_with_itc')} pure-agent cost(s) with credit claimed; "
                f"{n('billable_not_recharged')} billable cost(s) unbilled after {STALE_DAYS} days.")
