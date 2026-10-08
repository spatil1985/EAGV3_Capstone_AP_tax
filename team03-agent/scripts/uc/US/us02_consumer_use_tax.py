"""US-02 — Consumer use tax on purchases where no sales tax was charged.

Spec: docs/usecases/US/us-02-consumer-use-tax-on-purchases.md.
Question: "Which purchases did nobody charge us sales tax on, where we owe use tax ourselves?"

Statute: use tax complements sales tax — a buyer who isn't charged sales tax on a taxable purchase
owes use tax at the rate where the item is used (Ohio R.C. 5741.02, same combined rate). Exemptions
(manufacturing, resale) decide most of it.

Rules (lines classified by scripts/uc/common/us_purchase_tax.py):
  use_tax_due            per bill: taxable lines × the combined place-of-use rate, on bills with no vendor
                         tax and no use tax accrued
  use_tax_unclassified   aggregate: lines that need classification, reported as a range, not as due
  stored_value_mismatch  use_tax_accrued set but different from the computed figure
Window: the calendar year to date. INR bills (B8 residue) are excluded.
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.records import ref
from scripts.uc.common.us_purchase_tax import classify, line_amount, place_of_use_rate, untaxed


def in_scope(data, ctx):
    start = date(ctx.as_of.year, 1, 1)
    for b in data.get("bills", []):
        d = day(b.get("date"))
        if (d and start <= d <= ctx.as_of and (b.get("status") or "").lower() not in ("draft", "void")
                and (b.get("currency_code") or "USD").upper() == "USD" and untaxed(b)):
            yield b


class UseTax(Rule):
    id = "use_tax"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        rate, where = place_of_use_rate(data)
        unclassified = Decimal("0")
        unclassified_bills = set()
        for bill in in_scope(data, ctx):
            taxable, classes = Decimal("0"), {}
            for line in bill.get("items") or []:
                cls, note = classify(line)
                amount = line_amount(line)
                classes[cls] = classes.get(cls, Decimal("0")) + amount
                if cls in ("taxable_goods", "taxable_service"):
                    taxable += amount
                elif cls == "unclassified":
                    unclassified += amount
                    unclassified_bills.add(bill["id"])
            due = (taxable * rate / 100).quantize(CENTS)
            accrued = money(bill.get("use_tax_accrued"))
            number = ref(bill, "number")
            if accrued and abs(accrued - due) > Decimal("0.01"):
                yield Finding(finding_type=DATA_QUALITY, rule="stored_value_mismatch", status=DATA_QUALITY, severity=40,
                              entity_type="Bill", entity_id=bill["id"], entity_ref=number, currency=ctx.currency,
                              summary=f"{number}: use tax accrued {fmt(accrued, ctx.currency)} ≠ computed "
                                      f"{fmt(due, ctx.currency)}.", details={"accrued": str(accrued), "computed": str(due)})
            elif due > 0 and not accrued:
                yield Finding(
                    finding_type="use_tax", rule="use_tax_due", severity=self.severity, entity_type="Bill",
                    entity_id=bill["id"], entity_ref=number, total_exposure=due, currency=ctx.currency,
                    counterparty_id=bill.get("vendor_id"), counterparty_name=bill.get("_vendor_id_display"),
                    summary=f"{number} ({bill.get('_vendor_id_display')}): {fmt(taxable, ctx.currency)} of taxable "
                            f"purchases with no sales tax charged and no use tax accrued: {fmt(due, ctx.currency)} use tax "
                            f"at {rate}% ({', '.join(where)}).",
                    details={"taxable_base": str(taxable), "rate": str(rate), "place_of_use": where,
                             "line_classes": {k: str(v) for k, v in classes.items()}})
        if unclassified:
            ceiling = (unclassified * rate / 100).quantize(CENTS)
            yield Finding(
                finding_type="use_tax", rule="use_tax_unclassified", severity=45, entity_type="Bills",
                entity_id="unclassified", entity_ref=f"{len(unclassified_bills)} bills", total_exposure=ceiling,
                currency=ctx.currency,
                summary=f"{fmt(unclassified, ctx.currency)} of untaxed purchases on {len(unclassified_bills)} bill(s) needs "
                        f"classification; if all of it were taxable, use tax would be {fmt(ceiling, ctx.currency)} at {rate}%.",
                details={"unclassified_base": str(unclassified), "rate": str(rate), "count": len(unclassified_bills)})


class ConsumerUseTax(Playbook):

    @property
    def rules(self):
        return [UseTax()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), jurisdictions=fetcher.list("TaxJurisdiction"),
                       org=fetcher.list("OrgProfile"))

    def context(self, data, findings, ctx):
        bills = list(in_scope(data, ctx))
        by: dict = {}
        for b in bills:
            for line in b.get("items") or []:
                cls = classify(line)[0]
                by[cls] = by.get(cls, Decimal("0")) + line_amount(line)
        rate, where = place_of_use_rate(data)
        return {"untaxed USD bills this year": len(bills),
                "net value": str(sum((money(b.get("net_total")) for b in bills), Decimal("0"))),
                "by line class": {k: str(v) for k, v in sorted(by.items())},
                "place-of-use rate": f"{rate}% ({', '.join(where)})"}

    def summary(self, outcome, ctx):
        c = outcome.context
        due = sum((f.total_exposure for f in outcome.findings if f.rule == "use_tax_due"), Decimal("0"))
        unc = next((f for f in outcome.findings if f.rule == "use_tax_unclassified"), None)
        return (f"{fmt(money(c['net value']), ctx.currency)} of this year's purchases carried no sales tax and no use tax "
                f"was accrued. Use tax due on clearly taxable lines: {fmt(due, ctx.currency)}. "
                + (f"Another {fmt(money(unc.details['unclassified_base']), ctx.currency)} needs classification (up to "
                   f"{fmt(unc.total_exposure, ctx.currency)})." if unc else ""))
