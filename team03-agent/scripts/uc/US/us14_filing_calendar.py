"""US-14 — State sales-tax filing calendar and timeliness.

Spec: docs/usecases/US/us-14-sales-tax-filing-calendar.md.
Question: "Which state returns are due when, are we ready to file them, and what do we lose if we're late?"

Each registered state's periods come from its filing frequency (TaxNexus, cross-checked with the
TaxJurisdiction rows); the due day and timely-filing discount per state are rulebook values. There is
no return or payment record on the platform, so a past-due period can't be shown filed or unfiled.

Rules:
  filing_due                           a period due within 7 days, with its liability and the discount at stake
  filing_unverifiable                  aggregate per state: past-due periods with no filing evidence
  next_filing_due_missing              (data_quality) TaxNexus.next_filing_due null on a registered state
  frequency_conflict                   TaxNexus frequency ≠ that state's TaxJurisdiction frequencies
  registered_state_without_jurisdiction  registered with no active jurisdiction rows
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import add_months, day, month_bounds

MONTHS = {"monthly": 1, "quarterly": 3, "semi_annual": 6, "semiannual": 6, "annual": 12}
DUE_SOON = 7


def periods(n, ctx, start: date):
    step = MONTHS.get((n.get("filing_frequency") or "").lower(), 1)
    first = date(start.year, ((start.month - 1) // step) * step + 1, 1)
    p = first
    while True:
        end = month_bounds(f"{add_months(p, step - 1):%Y-%m}")[1]
        due_day = int(ctx.constant("sales_tax_return_due_day").get(n["state_code"], 20))
        nxt = add_months(p, step)
        due = date(nxt.year, nxt.month, due_day)
        yield p, end, due
        if due > ctx.as_of:
            return
        p = nxt


def liability(data, state, start, end) -> Decimal:
    total = Decimal("0")
    for inv in data.get("invoices", []):
        d = day(inv.get("date"))
        if not d or not (start <= d <= end) or (inv.get("status") or "").lower() in ("draft", "void", "cancelled"):
            continue
        total += sum((money(r.get("amount")) for r in inv.get("taxes") or []
                      if not r.get("is_exempt") and str(r.get("state_code") or "").upper() == state), Decimal("0"))
    return total


class FilingCalendar(Rule):
    id = "filing_calendar"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        ledger_start = min((day(i.get("date")) for i in data.get("invoices", []) if day(i.get("date"))), default=ctx.as_of)
        discounts = ctx.constant("sales_tax_timely_discount_pct")
        for n in data.get("nexus", []):
            state = str(n.get("state_code")).upper()
            if not n.get("is_registered"):
                continue
            base = dict(entity_type="TaxNexus", entity_id=n["id"], entity_ref=state, currency=ctx.currency)
            juris = [j for j in data.get("jurisdictions", []) if str(j.get("state_code")).upper() == state
                     and (j.get("status") or "active") == "active"]
            if not juris:
                yield Finding(finding_type="filing_calendar", rule="registered_state_without_jurisdiction", severity=55,
                              **base, summary=f"{state} is registered but has no active tax jurisdiction configured.",
                              details={})
            freqs = {(j.get("filing_frequency") or "").lower() for j in juris} - {""}
            if freqs and (n.get("filing_frequency") or "").lower() not in freqs:
                yield Finding(finding_type="filing_calendar", rule="frequency_conflict", severity=45, **base,
                              summary=f"{state}: nexus says {n.get('filing_frequency')} filing, its jurisdictions say "
                                      f"{sorted(freqs)}.", details={})
            if not n.get("next_filing_due"):
                yield Finding(finding_type=DATA_QUALITY, rule="next_filing_due_missing", status=DATA_QUALITY,
                              severity=15, **base,
                              summary=f"{state}: next_filing_due is empty, so the platform's own calendar drives nothing.",
                              details={"field": "next_filing_due"})
            start = max(day(n.get("registered_on")) or ledger_start, ledger_start)
            past = []
            for p_start, p_end, due in periods(n, ctx, start):
                tax = liability(data, state, p_start, p_end)
                discount = (tax * Decimal(str(discounts.get(state, 0))) / 100).quantize(CENTS)
                label = f"{p_start:%Y-%m}" + (f"…{p_end:%Y-%m}" if p_start.month != p_end.month else "")
                if due < ctx.as_of:
                    past.append(f"{label} (due {due}, {fmt(tax, ctx.currency)})")
                elif (due - ctx.as_of).days <= DUE_SOON:
                    yield Finding(finding_type="filing_calendar", rule="filing_due", severity=70, total_exposure=tax,
                                  **base,
                                  summary=f"{state} return for {label} is due {due} ({(due - ctx.as_of).days} days): "
                                          f"{fmt(tax, ctx.currency)} liability; filing on time keeps a "
                                          f"{fmt(discount, ctx.currency)} discount.",
                                  details={"state": state, "period": label, "due_date": str(due), "liability": str(tax),
                                           "discount_at_stake": str(discount)})
            if past:
                yield Finding(finding_type="filing_calendar", rule="filing_unverifiable", severity=50, **base,
                              summary=f"{state}: {len(past)} past-due period(s) and AgentSwitch holds no record of any "
                                      f"filed return or payment — confirm they were filed: {', '.join(past[-3:])}.",
                              details={"state": state, "periods": past})


class SalesTaxFilingCalendar(Playbook):

    @property
    def rules(self):
        return [FilingCalendar()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(nexus=fetcher.list("TaxNexus"), jurisdictions=fetcher.list("TaxJurisdiction"),
                       invoices=fetcher.list("Invoice"))

    def context(self, data, findings, ctx):
        upcoming = {}
        ledger_start = min((day(i.get("date")) for i in data["invoices"] if day(i.get("date"))), default=ctx.as_of)
        for n in data["nexus"]:
            if n.get("is_registered"):
                *_, last = periods(n, ctx, max(day(n.get("registered_on")) or ledger_start, ledger_start))
                upcoming[n["state_code"]] = f"{last[0]:%Y-%m}…{last[1]:%Y-%m} due {last[2]}"
        return {"next returns": upcoming, "filing records": "none on the platform (return / payment record not requested)"}

    def summary(self, outcome, ctx):
        due = [f for f in outcome.findings if f.rule == "filing_due"]
        unver = [f.entity_ref for f in outcome.findings if f.rule == "filing_unverifiable"]
        nxt = "; ".join(f"{s} {v}" for s, v in outcome.context["next returns"].items())
        return ((f"{len(due)} return(s) due within {DUE_SOON} days. " if due else "")
                + f"Next returns: {nxt}. "
                + (f"AgentSwitch holds no record of filed returns for {', '.join(unver)}: confirm past filings."
                   if unver else ""))
