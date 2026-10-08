"""UC-28 — Documents entered or back-dated into a filed, locked or closed period (India).

Spec: docs/usecases/IN/uc-28-late-entered-documents.md.
Question: "Has anyone entered or back-dated a document into a month we've already filed or closed?"

Statute: a document dated in a period whose GSTR-1/3B is filed belongs in the next return or an
amendment (GSTR-1A; s.37(3), s.39(9)), with s.50 interest from the original due date on any tax
understated; amendments for an FY close on 30 November after it. Rule 47 (30 days to issue an invoice
for services) is the back-dating yardstick.

Rules (scripts/uc/common/period_integrity.py): entered_after_filing, entered_into_locked_period,
entered_into_closed_period, backdated_document. Control gaps (a filed month not locked until later)
are reported in the run context.
"""

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.uc.common.period_integrity import DOCS, control_gaps, integrity_findings, windows

BACKDATE_DAYS = 30      # Rule 47 CGST Rules


class LateEntries(Rule):
    id = "period_integrity"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        wins = windows(data.get("returns", []), data.get("locks", []), data.get("periods", []))
        docs = {e: data.get(e, []) for e in DOCS}
        yield from integrity_findings(docs, wins, ctx, backdate_days=BACKDATE_DAYS)


class LateEnteredDocuments(Playbook):

    @property
    def rules(self):
        return [LateEntries()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(returns=fetcher.list("GSTReturn"), locks=fetcher.list("TransactionLock"),
                       periods=fetcher.list("AccountingPeriod"),
                       **{e: fetcher.list(e) for e in DOCS})

    def context(self, data, findings, ctx):
        wins = windows(data["returns"], data["locks"], data["periods"])
        return {"closed windows": {k: sum(1 for w in wins if w["kind"] == k) for k in ("filed", "locked", "closed")},
                "documents scanned": {e: len(data[e]) for e in DOCS},
                "control gaps": control_gaps(wins)}

    def summary(self, outcome, ctx):
        n = len(outcome.findings)
        gaps = outcome.context["control gaps"]
        return ((f"{n} document(s) were entered into a filed, locked or closed period, or back-dated more than "
                 f"{BACKDATE_DAYS} days." if n else "No document has been entered into a filed, locked or closed period.")
                + (f" Control gap: {gaps[0]}." if gaps else ""))
