"""UC-10 — Job work: s.143 return deadline and ITC-04.

Spec: docs/usecases/IN/uc-10-job-work-itc04.md.
Question: "What have we sent out for job work that hasn't come back, and when does it become a
taxable supply?"

Statute: s.143 CGST Act — inputs sent to a job worker must come back within 1 year (capital
goods 3 years); otherwise the original despatch is a deemed supply on the day it was sent, with
interest. ITC-04 reports the movements.

Rules:
  s143_deemed_supply   a delivered job_work challan older than the limit with no return found
  s143_due_soon        within the warning window of the limit, no return found
A draft challan has not moved goods, so its clock has not started (spec §6: all 19 live job-work
challans are draft → 0 findings is the right answer today).

Returns are not modelled on the platform (N426 T4.5). A return is *inferred* from a later bill
from the same party for the same item, and labelled `return_inferred`, never confirmed.
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day
from scripts.uc.common.records import party_of


def _job_work(data):
    return [c for c in data.get("challans", []) if c.get("challan_type") == "job_work"]


def return_inferred(challan, data) -> bool:
    party = challan.get("customer_id") or challan.get("party_id")
    sent = day(challan.get("date"))
    items = {l.get("item_id") for l in challan.get("items") or [] if l.get("item_id")}
    for bill in data.get("bills", []):
        if bill.get("vendor_id") == party and (day(bill.get("date")) or sent) > sent:
            if not items or items & {l.get("item_id") for l in bill.get("items") or []}:
                return True
    return False


def limit_days(challan, data, ctx) -> tuple[int, str]:
    # No field marks capital goods (spec §10); inputs is the safe, shorter clock.
    return int(ctx.constant("job_work_return_days_inputs")), "inputs_assumed"


class JobWorkDeadline(Rule):
    id = "job_work"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        warn = int(ctx.constant("job_work_warning_days"))
        rate = Decimal(str(ctx.constant("gst_interest_rate_pct"))) / 100
        for ch in _job_work(data):
            sent = day(ch.get("date"))
            if (ch.get("status") or "").lower() != "delivered" or not sent:
                continue
            limit, goods_class = limit_days(ch, data, ctx)
            deadline = sent + timedelta(days=limit)
            age = (ctx.as_of - sent).days
            if age <= limit - warn:
                continue
            returned = return_inferred(ch, data)
            if returned:
                continue
            value = money(ch.get("net_total") or ch.get("grand_total"))
            items = data.index("items", "id")
            rates = [money((items.get(l.get("item_id")) or {}).get("intra_state_tax_rate")) for l in ch.get("items") or []]
            tax = (value * (max(rates) if rates else Decimal("0")) / 100).quantize(CENTS)
            pid, pname = party_of(ch, data)
            late = age > limit
            interest = (tax * rate * age / 365).quantize(CENTS) if late else Decimal("0.00")
            yield Finding(
                finding_type="job_work", rule="s143_deemed_supply" if late else "s143_due_soon",
                severity=80 if late else 45, entity_type="DeliveryChallan", entity_id=ch["id"],
                entity_ref=ch.get("number"), total_exposure=tax + interest, interest_amount=interest,
                currency=ctx.currency, counterparty_id=pid, counterparty_name=pname,
                summary=(f"{ch.get('number')} sent to {pname} on {sent} for job work has not come back after "
                         f"{age} days: it is now a deemed supply ({fmt(value, ctx.currency)} value, about "
                         f"{fmt(tax, ctx.currency)} tax plus {fmt(interest, ctx.currency)} interest)."
                         if late else
                         f"{ch.get('number')} sent to {pname} on {sent} must come back by {deadline} "
                         f"({(deadline - ctx.as_of).days} days), or it becomes a deemed supply."),
                details={"sent_date": str(sent), "deadline": str(deadline), "age_days": age,
                         "goods_class": goods_class, "return_state": "none_found",
                         "deemed_supply_value": str(value), "estimated_tax": str(tax),
                         "tax_basis": "item intra_state_tax_rate (estimate)"},
            )


class JobWorkItc04(Playbook):

    @property
    def rules(self):
        return [JobWorkDeadline()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(challans=fetcher.list("DeliveryChallan", challan_type="job_work"),
                       bills=fetcher.list("Bill"), items=fetcher.list("Item"))

    def context(self, data, findings, ctx):
        jw = _job_work(data)
        return {"job-work challans": len(jw),
                "… delivered (clock running)": sum(1 for c in jw if (c.get("status") or "") == "delivered"),
                "… draft (not sent, no clock)": sum(1 for c in jw if (c.get("status") or "") == "draft"),
                "returns": "inferred from later bills only; the platform has no return link (N426 T4.5)"}

    def summary(self, outcome, ctx):
        late = sum(1 for f in outcome.findings if f.rule == "s143_deemed_supply")
        soon = sum(1 for f in outcome.findings if f.rule == "s143_due_soon")
        c = outcome.context
        if not outcome.findings:
            return (f"{c['job-work challans']} job-work challan(s): {c['… delivered (clock running)']} delivered, "
                    f"{c['… draft (not sent, no clock)']} draft. Nothing is out past or near its return deadline.")
        return f"{late} job-work despatch(es) are now deemed supplies; {soon} more are due back within the warning window."
