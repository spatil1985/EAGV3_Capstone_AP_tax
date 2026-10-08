"""US-21 — Unclaimed property (escheat) held for vendors.

Spec: docs/usecases/US/us-21-unclaimed-property-escheat.md.
Question: "Do we hold money owed to vendors that nobody has claimed, and must we report it to a state?"

Statute: state unclaimed property laws (RUUPA 2016 model; Ohio R.C. Chapter 169) — money owed to someone
else and unclaimed past the dormancy period must be reported and remitted, after due-diligence notices.
Owner state priority: last known address, else the holder's state (Texas v. New Jersey, 1965).

An outstanding payment is a PaymentMade that never cleared the bank (US-19 matching), past a 60-day grace.
A payment outside the bank feed's window is "unknown", not outstanding (spec §6).
Rules:
  escheat_due_diligence        within 120 days of dormancy: send owner notices
  escheat_reportable           past dormancy: report and remit with the state's next report
  escheat_owner_state_unknown  outstanding item with no vendor address (holder state used)
Vendor credits owed to us are not unclaimed property (US-17).
"""

from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.bank_recon import recon
from scripts.uc.common.dates import add_months, day


def owner_state(payment, data) -> str | None:
    party = data.index("parties", "id").get(payment.get("vendor_id")) or {}
    for a in party.get("addresses") or []:
        if a.get("state"):
            return str(a["state"]).upper()[:2]
    return None


def outstanding(data, ctx):
    r = recon(data, ctx)
    start, end = r["window"]
    grace = int(ctx.constant("escheat_clearing_grace_days"))
    uncleared = {p["id"] for p in r["missing"]}
    out, unknown = [], 0
    for p in data.get("payments", []):
        d = day(p.get("date"))
        if not d or (p.get("status") or "").lower() in ("void", "draft", "cancelled") or (ctx.as_of - d).days < grace:
            continue
        if start is None or not (start <= d <= end):
            unknown += 1
        elif p["id"] in uncleared:
            out.append(p)
    return out, unknown


class Escheat(Rule):
    id = "unclaimed_property"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        dormancy = ctx.constant("escheat_dormancy_years")
        notice = int(ctx.constant("escheat_due_diligence_days"))
        holder = str(((data.get("org") or [{}])[0]).get("state") or "").upper()
        items, _ = outstanding(data, ctx)
        for p in items:
            state = owner_state(p, data)
            used = state or holder
            years = int(dormancy.get(used, dormancy.get("default", 3)))
            dormant_on = add_months(day(p["date"]), 12 * years)
            amount = money(p.get("amount"))
            base = dict(entity_type="PaymentMade", entity_id=p["id"], entity_ref=p.get("number"), total_exposure=amount,
                        currency=ctx.currency, counterparty_id=p.get("vendor_id"), counterparty_name=p.get("_vendor_id_display"))
            det = {"payment_id": p["id"], "owner_state": used, "dormant_on": str(dormant_on), "amount": str(amount),
                   "payment_mode": p.get("payment_mode")}
            if not state:
                yield Finding(finding_type="unclaimed_property", rule="escheat_owner_state_unknown", severity=40, **base,
                              summary=f"{p.get('number')} ({fmt(amount, ctx.currency)}) never cleared and the vendor has no "
                                      f"address; the holder's state ({holder}) would take it.", details=det)
            if dormant_on <= ctx.as_of:
                yield Finding(finding_type="unclaimed_property", rule="escheat_reportable", severity=80, **base,
                              summary=f"{p.get('number')} ({fmt(amount, ctx.currency)} to {p.get('_vendor_id_display')}) "
                                      f"has been outstanding since {p['date']} and was presumed abandoned on {dormant_on}: "
                                      f"report and remit it to {used}.", details=det)
            elif dormant_on <= ctx.as_of + timedelta(days=notice):
                yield Finding(finding_type="unclaimed_property", rule="escheat_due_diligence", severity=60, **base,
                              summary=f"{p.get('number')} ({fmt(amount, ctx.currency)}) becomes dormant on {dormant_on}: "
                                      f"send the owner due-diligence notice now.", details=det)


class UnclaimedProperty(Playbook):

    @property
    def rules(self):
        return [Escheat()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(payments=fetcher.list("PaymentMade"), bank_transactions=fetcher.list("BankTransaction"),
                       parties=fetcher.list("Party"), org=fetcher.list("OrgProfile"), bills=[])

    def context(self, data, findings, ctx):
        items, unknown = outstanding(data, ctx)
        oldest = min((day(p.get("date")) for p in data["payments"] if day(p.get("date"))), default=None)
        return {"payments": len(data["payments"]),
                "by mode": {m: sum(1 for p in data["payments"] if p.get("payment_mode") == m)
                            for m in sorted({p.get("payment_mode") for p in data["payments"]} - {None})},
                "outstanding (never cleared, inside the bank window)": len(items),
                "outstanding total": str(sum((money(p.get("amount")) for p in items), Decimal("0"))),
                "clearing unknown (outside the bank feed)": unknown, "oldest payment": str(oldest) if oldest else None}

    def summary(self, outcome, ctx):
        c = outcome.context
        rep = [f for f in outcome.findings if f.rule == "escheat_reportable"]
        dd = [f for f in outcome.findings if f.rule == "escheat_due_diligence"]
        if not rep and not dd:
            return (f"No unclaimed property to report: {c['outstanding (never cleared, inside the bank window)']} payment(s) "
                    f"({fmt(money(c['outstanding total']), ctx.currency)}) never cleared, but none is near dormancy (oldest "
                    f"payment {c['oldest payment']}, dormancy ≥ 3 years). {c['clearing unknown (outside the bank feed)']} "
                    f"payment(s) fall outside the bank feed, so their clearing is unknown.")
        return f"{len(rep)} item(s) are reportable now and {len(dd)} need due-diligence notices."
