"""UC-24 — Unclaimed and at-risk input credit (IMS, GSTR-2B, s.16(4)).

Spec: docs/usecases/IN/uc-24-unclaimed-itc-ims-2b.md.
Question: "Which input credit can we still claim, which have we claimed that we shouldn't have, and
what will we lose if we wait?"

Statute: s.16(2)(aa) + Rule 36(4) — credit only for documents in GSTR-2B; IMS (Oct 2024) lets the
recipient accept/reject/keep pending before 2B is generated on the 14th (no action = deemed
accepted); s.16(4) — credit of an FY can't be taken after 30 November following it.

Rules (population: posted bills, ITC-eligible, tax > 0, tax source per document):
  itc_on_rejected_document     IMS-rejected but still marked eligible: don't claim / reverse
  itc_awaiting_ims_action      aggregate per period: pending documents whose 2B is not generated yet
  itc_supplier_not_identified  aggregate: no supplier GSTIN on the bill or the vendor
  itc_lapsing                  aggregate per FY whose s.16(4) date is < 90 days away
  itc_not_in_2b                aggregate per period: book credit vs the GSTR-2B row's total (the
                               platform has no 2B lines, so this is totals only — and says so)
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import add_months, day, fy_label, fy_start, period_of
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tax import doc_tax

WARN_DAYS = 90


def population(data):
    for bill in data.get("bills", []):
        if (bill.get("status") or "").lower() in NOT_POSTED or bill.get("itc_eligibility") == "ineligible":
            continue
        tax = doc_tax(bill)
        if tax and tax["total"] > 0:
            yield bill, tax


def claim_cutoff(d: date, ctx) -> date:
    end = fy_start(d, "gst").year + 1
    month, dd = (int(x) for x in str(ctx.rule("itc_claim_cutoff_month_day", date(end, 4, 1))).split("-"))
    return date(end, month, dd)


def twob_date(period: str, ctx) -> date:
    first = date(int(period[:4]), int(period[5:7]), 1)
    nxt = add_months(first, 1)
    return date(nxt.year, nxt.month, int(ctx.constant("gstr2b_generation_day")))


def _aggregate(rule, entity_id, ref_, bills, ctx, severity, summary, **details):
    total = sum((t["total"] for _, t in bills), Decimal("0"))
    return Finding(finding_type="itc_entitlement", rule=rule, severity=severity, entity_type="Bills",
                   entity_id=entity_id, entity_ref=ref_, total_exposure=total, currency=ctx.currency,
                   summary=summary.format(n=len(bills), tax=fmt(total, ctx.currency)),
                   details={"bills": [ref(b, "number") for b, _ in bills][:50], "count": len(bills), **details})


class ItcEntitlement(Rule):
    id = "itc_entitlement"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        parties = data.index("parties", "id")
        pop = list(population(data))
        pending: dict = {}
        unidentified, lapsing = [], {}
        for bill, tax in pop:
            ims = (bill.get("ims_status") or "").lower()
            if ims in ("reject", "rejected"):
                vid, vname = party_of(bill, data)
                yield Finding(
                    finding_type="itc_entitlement", rule="itc_on_rejected_document", severity=80, entity_type="Bill",
                    entity_id=bill["id"], entity_ref=ref(bill, "number"), reversal_base_amount=tax["total"],
                    total_exposure=tax["total"], currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                    summary=f"{ref(bill, 'number')} ({vname}) was rejected in IMS but is still marked ITC-eligible: "
                            f"{fmt(tax['total'], ctx.currency)} must not be claimed (reverse it with 18% interest if "
                            f"it was).",
                    details={"ims_status": ims, "itc_eligibility": bill.get("itc_eligibility")})
            elif ims == "pending" and period_of(bill.get("date")):
                period = period_of(bill["date"])
                if ctx.as_of < twob_date(period, ctx):
                    pending.setdefault(period, []).append((bill, tax))
            if not bill.get("gst_no") and not (parties.get(bill.get("vendor_id")) or {}).get("gst_no"):
                unidentified.append((bill, tax))
            d = day(bill.get("date"))
            if d and 0 <= (claim_cutoff(d, ctx) - ctx.as_of).days <= WARN_DAYS and ims not in ("reject", "rejected"):
                lapsing.setdefault((fy_label(d, "gst"), claim_cutoff(d, ctx)), []).append((bill, tax))
        for period, bills in sorted(pending.items()):
            gen = twob_date(period, ctx)
            yield _aggregate("itc_awaiting_ims_action", f"ims:{period}", f"IMS {period}", bills, ctx, 50,
                             "{n} " + f"{period} supplier document(s) carrying " + "{tax}" + f" of credit are pending "
                             f"in IMS; action them before GSTR-2B is generated on {gen}, or they are deemed accepted.",
                             period=period, gstr2b_on=str(gen))
        if unidentified:
            yield _aggregate("itc_supplier_not_identified", "no-gstin", "no supplier GSTIN", unidentified, ctx, 40,
                             "{n} credit-bearing bill(s) ({tax}) have no supplier GSTIN on the bill or the vendor, so "
                             "they can't be matched to GSTR-2B (Rule 46 particulars missing — UC-40).")
        for (label, cut), bills in sorted(lapsing.items()):
            yield _aggregate("itc_lapsing", f"lapse:{label}", label, bills, ctx, 75,
                             "{n} " + f"{label} document(s) carrying " + "{tax}" + f" of credit lapse on {cut} "
                             f"({(cut - ctx.as_of).days} days) under s.16(4) if not claimed.",
                             fy=label, cutoff=str(cut))
        for row in data.get("returns", []):
            if row.get("return_type") != "GSTR-2B":
                continue
            rp = str(row.get("return_period") or "")
            period = f"{rp[3:]}-{rp[:2]}" if len(rp) == 7 else None
            books = [(b, t) for b, t in pop if period_of(b.get("date")) == period]
            twob_tax = sum((money(row.get(f"{h}_amount")) for h in ("igst", "cgst", "sgst", "cess")), Decimal("0"))
            book_tax = sum((t["total"] for _, t in books), Decimal("0"))
            if abs(twob_tax - book_tax) > 1:
                yield _aggregate("itc_not_in_2b", f"2b:{period}", f"GSTR-2B {rp}", books, ctx, 45,
                                 f"{period}: book credit {fmt(book_tax, ctx.currency)} on " + "{n}" + f" bill(s) vs "
                                 f"GSTR-2B total {fmt(twob_tax, ctx.currency)}. 2B carries no lines on the platform, so "
                                 f"the difference can't be traced to documents (totals only).",
                                 gstr2b_tax=str(twob_tax), book_tax=str(book_tax),
                                 gstr2b_filing_status=row.get("filing_status"))


class ItcEntitlementAudit(Playbook):

    @property
    def rules(self):
        return [ItcEntitlement()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), parties=fetcher.list("Party"), returns=fetcher.list("GSTReturn"))

    def context(self, data, findings, ctx):
        pop = list(population(data))
        by: dict = {}
        for b, t in pop:
            k = (b.get("ims_status") or "blank").lower()
            by.setdefault(k, [0, Decimal("0")])
            by[k][0] += 1
            by[k][1] += t["total"]
        return {"credit-bearing bills": len(pop), "by IMS status": {k: f"{n} bills, {v}" for k, (n, v) in by.items()},
                "claimed per document": "not recorded on the platform; see UC-23 for the period claim"}

    def summary(self, outcome, ctx):
        def total(rule):
            return sum((f.total_exposure for f in outcome.findings if f.rule == rule), Decimal("0"))
        rejected = [f for f in outcome.findings if f.rule == "itc_on_rejected_document"]
        pend = [f for f in outcome.findings if f.rule == "itc_awaiting_ims_action"]
        unid = next((f for f in outcome.findings if f.rule == "itc_supplier_not_identified"), None)
        lapse = [f for f in outcome.findings if f.rule == "itc_lapsing"]
        return (f"{fmt(total('itc_on_rejected_document'), ctx.currency)} of credit sits on {len(rejected)} IMS-rejected "
                f"bill(s) still marked eligible: do not claim it. "
                + (f"{fmt(total('itc_awaiting_ims_action'), ctx.currency)} is pending IMS action before GSTR-2B. "
                   if pend else "Nothing is pending IMS action before the next GSTR-2B. ")
                + (f"{unid.details['count']} credit-bearing bill(s) have no supplier GSTIN. " if unid else "")
                + (f"{fmt(total('itc_lapsing'), ctx.currency)} lapses under s.16(4) within {WARN_DAYS} days."
                   if lapse else "No credit lapses under s.16(4) within 90 days."))
