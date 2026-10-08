"""US-15 — Documents entered or back-dated into a period already reported (US).

Spec: docs/usecases/US/us-15-late-entered-documents.md (UC-28 for the US tenant).
Question: "Has anyone entered or back-dated a document into a month we've already reported?"

A sale belongs on the sales-tax return for the period it occurred in (accrual basis); entered after
that return was due, it needs an amended return with interest. Keystone has no return records, no
transaction locks and no closed periods, so the windows are:
  - the US-14 calendar: the return for the document's period was due before the document was created
    (entered_into_reported_period — "probably filed"; the row says so);
  - closed AccountingPeriods and TransactionLocks, if any appear (shared engine, UC-28);
  - back-dating more than 30 days, whatever the period status (backdated_document).
Rows are aggregated per document type and month (147 invoices back-entered in one day would otherwise
be 147 rows).
"""

from datetime import date, datetime
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import add_months, day, period_of
from scripts.uc.common.period_integrity import DOCS, windows

BACKDATE_DAYS = 30


def ts(v):
    try:
        return datetime.fromisoformat(str(v).replace("Z", "+00:00")).replace(tzinfo=None) if v else None
    except ValueError:
        return None


def return_due(period: str, ctx, state: str = "OH") -> date:
    first = date(int(period[:4]), int(period[5:7]), 1)
    nxt = add_months(first, 1)
    return date(nxt.year, nxt.month, int(ctx.constant("sales_tax_return_due_day").get(state, 20)))


class LateEntries(Rule):
    id = "period_integrity"
    severity = 65

    def evaluate(self, data: Dataset, ctx):
        wins = windows((), data.get("locks", []), data.get("periods", []))
        home = str(((data.get("org") or [{}])[0]).get("state") or "OH").upper()
        groups: dict = {}
        for entity in DOCS:
            amount_field = DOCS[entity][1]
            for doc in data.get(entity, []):
                if (doc.get("status") or "").lower() in ("draft", "void", "cancelled"):
                    continue
                when, created = day(doc.get("date")), ts(doc.get("created_at"))
                if not when or not created:
                    continue
                period = period_of(when)
                due = return_due(period, ctx, home)
                closed = next((w for w in wins if (w["from"] is None or when >= w["from"]) and when <= w["to"]
                               and w["closed_at"] and created > w["closed_at"]), None)
                if closed:
                    rule = "entered_into_closed_period" if closed["kind"] == "closed" else "entered_into_locked_period"
                elif entity in ("Invoice", "CreditNote") and created.date() > due:
                    rule = "entered_into_reported_period"
                elif (created.date() - when).days > BACKDATE_DAYS:
                    rule = "backdated_document"
                else:
                    continue
                g = groups.setdefault((rule, entity, period), {"count": 0, "amount": Decimal("0"), "tax": Decimal("0"),
                                                               "created": set(), "due": due, "refs": []})
                g["count"] += 1
                g["amount"] += money(doc.get("net_total") or doc.get("amount"))
                g["tax"] += money(doc.get(amount_field))
                g["created"].add(str(created.date()))
                g["refs"].append(doc.get("number"))
        for (rule, entity, period), g in sorted(groups.items()):
            created = ", ".join(sorted(g["created"])[:3])
            text = {"entered_into_reported_period":
                        f"dated {period} were entered on {created}, after that month's return was due ({g['due']}): if the "
                        f"return was filed on time, this tax ({fmt(g['tax'], ctx.currency)}) was not on it — amend it",
                    "entered_into_closed_period": f"dated {period} were entered after the period was closed ({created})",
                    "entered_into_locked_period": f"dated {period} were entered after the period was locked ({created})",
                    "backdated_document": f"dated {period} were entered more than {BACKDATE_DAYS} days later ({created})"}[rule]
            yield Finding(
                finding_type="period_integrity", rule=rule, severity=75 if rule == "entered_into_reported_period" else 50,
                entity_type=entity, entity_id=f"{entity}:{period}:{rule}", entity_ref=f"{g['count']} {entity} {period}",
                total_exposure=g["tax"], currency=ctx.currency,
                summary=f"{g['count']} {entity.lower()}(s) ({fmt(g['amount'], ctx.currency)}) {text}.",
                details={"period": period, "count": g["count"], "amount": str(g["amount"]), "tax": str(g["tax"]),
                         "return_due": str(g["due"]), "created_on": sorted(g["created"]), "documents": g["refs"][:30],
                         "filing_evidence": "none on the platform (US-14)"})


class LateEnteredDocumentsUS(Playbook):

    @property
    def rules(self):
        return [LateEntries()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(locks=fetcher.list("TransactionLock"), periods=fetcher.list("AccountingPeriod"),
                       org=fetcher.list("OrgProfile"), **{e: fetcher.list(e) for e in DOCS})

    def context(self, data, findings, ctx):
        return {"transaction locks": len(data["locks"]),
                "closed accounting periods": sum(1 for p in data["periods"] if (p.get("status") or "") == "closed"),
                "documents scanned": {e: len(data[e]) for e in DOCS}}

    def summary(self, outcome, ctx):
        rep = [f for f in outcome.findings if f.rule == "entered_into_reported_period"]
        n = sum(f.details["count"] for f in rep)
        tax = sum((f.total_exposure for f in rep), Decimal("0"))
        back = sum(f.details["count"] for f in outcome.findings if f.rule == "backdated_document")
        c = outcome.context
        return ((f"{n} invoice(s) carrying {fmt(tax, ctx.currency)} of tax were entered after their month's return was "
                 f"due: if those returns were filed on time, they need amending. " if rep else "")
                + f"{back} other document(s) were back-dated more than {BACKDATE_DAYS} days. "
                + (f"No period is locked or closed ({c['closed accounting periods']} closed, {c['transaction locks']} locks), "
                   f"so nothing stopped it." if not c["transaction locks"] and not c["closed accounting periods"] else ""))
