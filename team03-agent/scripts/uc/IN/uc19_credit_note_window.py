"""UC-19 — Credit-note s.34(2) time limit.

Spec: docs/usecases/IN/uc-19-credit-note-time-limit.md.
Question: "Which returns can we still issue a tax-effective credit note for?"

Statute: s.34(2) CGST Act — a credit note reduces output tax only if declared by 30 November
after the end of the FY of the original supply (or the annual-return date, if earlier). After
that the GST on it is lost.

Rules:
  credit_note_out_of_window  an existing credit note dated after its original invoice's cutoff
  window_closing             aggregate: an FY whose cutoff is ≤ 90 days away, with the count and
                             value of receivable invoices still eligible
  classification_conflict    a credit note linked to a *payable* invoice (PINV): that needs a
                             debit note from us or a credit note from the vendor (12 live in §11)
CreditNote.taxes[] is stripped at fetch (N128); its tax comes from item lines.
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day, fy_label, fy_start
from scripts.uc.common.records import party_of


def cutoff(original: date, ctx) -> date:
    fy_end_year = fy_start(original, "gst").year + 1
    month_day = ctx.rule("credit_note_cutoff_month_day", date(fy_end_year, 4, 1))
    month, d = (int(x) for x in str(month_day).split("-"))
    return date(fy_end_year, month, d)


class CreditNoteWindow(Rule):
    id = "credit_note_window"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        invoices = data.index("invoices", "id")
        for cn in data.get("credit_notes", []):
            if (cn.get("status") or "").lower() in ("void", "cancelled", "draft"):
                continue
            original = invoices.get(cn.get("invoice_id"))
            pid, pname = party_of(cn, data)
            if original and original.get("direction") == "payable":
                yield Finding(
                    finding_type="credit_note_window", rule="classification_conflict", severity=40,
                    entity_type="CreditNote", entity_id=cn["id"], entity_ref=cn.get("number"),
                    total_exposure=money(cn.get("total_tax")), currency=ctx.currency,
                    counterparty_id=pid, counterparty_name=pname,
                    summary=f"{cn.get('number')} is a credit note we issued against purchase invoice "
                            f"{original.get('number')}; a purchase adjustment needs our debit note or the "
                            f"vendor's credit note.",
                    details={"original": original.get("number"), "original_direction": "payable"})
                continue
            when, orig_day = day(cn.get("date")), day((original or {}).get("date"))
            if not (when and orig_day):
                continue
            limit = cutoff(orig_day, ctx)
            if when > limit:
                yield Finding(
                    finding_type="credit_note_window", rule="credit_note_out_of_window", severity=self.severity,
                    entity_type="CreditNote", entity_id=cn["id"], entity_ref=cn.get("number"),
                    total_exposure=money(cn.get("total_tax")), currency=ctx.currency,
                    counterparty_id=pid, counterparty_name=pname,
                    summary=f"{cn.get('number')} ({cn.get('date')}) reduces {original.get('number')} "
                            f"({original.get('date')}) after the s.34(2) cutoff {limit}: its GST "
                            f"({fmt(money(cn.get('total_tax')), ctx.currency)}) can't be reduced from output tax.",
                    details={"original": original.get("number"), "original_date": original.get("date"),
                             "cutoff": str(limit), "days_late": (when - limit).days})


class WindowClosing(Rule):
    id = "window_closing"
    severity = 50

    def evaluate(self, data, ctx):
        warn = int(ctx.constant("credit_note_window_warning_days"))
        by_fy: dict = {}
        for inv in data.get("invoices", []):
            d = day(inv.get("date"))
            if (inv.get("direction") != "receivable" or not d
                    or (inv.get("status") or "").lower() in ("void", "cancelled", "draft")):
                continue
            limit = cutoff(d, ctx)
            if 0 <= (limit - ctx.as_of).days <= warn:
                by_fy.setdefault((fy_label(d, "gst"), limit), []).append(inv)
        in_window = sum(1 for cn in data.get("credit_notes", []) if cn.get("invoice_id"))
        for (label, limit), invs in sorted(by_fy.items()):
            value = sum((money(i.get("grand_total")) for i in invs), Decimal("0"))
            left = (limit - ctx.as_of).days
            yield Finding(
                finding_type="credit_note_window", rule=self.id, severity=self.severity, entity_type="FiscalYear",
                entity_id=label, entity_ref=label, total_exposure=value, currency=ctx.currency,
                summary=f"{left} days left to issue tax-effective credit notes against {len(invs)} {label} "
                        f"invoice(s) ({fmt(value, ctx.currency)}); the window closes on {limit}.",
                details={"fy": label, "cutoff": str(limit), "days_left": left, "eligible_invoice_count": len(invs),
                         "existing_credit_notes": in_window})


class CreditNoteTimeLimit(Playbook):

    @property
    def rules(self):
        return [CreditNoteWindow(), WindowClosing()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(credit_notes=fetcher.list("CreditNote"), invoices=fetcher.list("Invoice"))

    def context(self, data, findings, ctx):
        return {"credit notes": len(data["credit_notes"]),
                "receivable invoices": sum(1 for i in data["invoices"] if i.get("direction") == "receivable"),
                "CreditNote.taxes[]": "stripped at fetch (N128)"}

    def summary(self, outcome, ctx):
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        closing = [f.summary for f in outcome.findings if f.rule == "window_closing"]
        return ((" ".join(closing) + " ") if closing else "No FY credit-note window closes within 90 days. ") + \
            (f"{n('credit_note_out_of_window')} credit note(s) issued after their window; "
             f"{n('classification_conflict')} credit note(s) issued against purchase invoices.")
