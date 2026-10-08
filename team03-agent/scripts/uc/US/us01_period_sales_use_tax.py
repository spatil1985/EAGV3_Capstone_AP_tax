"""US-01 — Period sales and use tax liability by jurisdiction.

Spec: docs/usecases/US/us-01-period-sales-use-tax-liability.md.
Question: "What is our sales and use tax liability this period, by jurisdiction?"

Period: the calendar year to date (the jurisdictions file quarterly; the run context also gives the
last completed month). Tax source is invoice `taxes[]` (US README rule 1); item-level GST fields are
never read.

1. Sales tax by jurisdiction = Σ non-exempt taxes[].amount on invoices (not draft/void) in the window.
2. Use tax = Σ Bill.use_tax_accrued in the window.
3. Oracle: GET /api/accounting/reports/sales-tax-liability for the same window — per-jurisdiction
   tax_billed must agree to the cent, and invoice counts.
Rules: tax_liability (one context row per jurisdiction, citable), use_tax_accrued, stored_value_mismatch
(amount or count disagrees with the report; the Stark County count gap is known — spec §6).
"""

from datetime import date
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import CONTEXT, DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day

REPORT = "/api/accounting/reports/sales-tax-liability"


def window(ctx) -> tuple[date, date]:
    return date(ctx.as_of.year, 1, 1), ctx.as_of


def compute(data, ctx) -> dict:
    start, end = window(ctx)
    by: dict = {}
    taxable = exempt = Decimal("0")
    for inv in data.get("invoices", []):
        d = day(inv.get("date"))
        if (inv.get("direction", "receivable") != "receivable" or not d or not (start <= d <= end)
                or (inv.get("status") or "").lower() in ("draft", "void", "cancelled")):
            continue
        rows = inv.get("taxes") or []
        if any(not r.get("is_exempt") for r in rows):
            taxable += money(inv.get("net_total"))
        if any(r.get("is_exempt") for r in rows):
            exempt += money(inv.get("net_total"))
        for r in rows:
            j = by.setdefault(r.get("jurisdiction_id"), {"name": r.get("jurisdiction_name") or r.get("tax_type"),
                                                         "state": r.get("state_code"), "rate": r.get("rate"),
                                                         "tax": Decimal("0"), "invoices": set()})
            if not r.get("is_exempt"):
                j["tax"] += money(r.get("amount"))
                j["invoices"].add(inv["id"])
    use = sum((money(b.get("use_tax_accrued")) for b in data.get("bills", [])
               if day(b.get("date")) and start <= day(b["date"]) <= end
               and (b.get("status") or "").lower() not in ("draft", "void")), Decimal("0"))
    return {"by": by, "taxable": taxable, "exempt": exempt, "use": use}


class SalesUseLiability(Rule):
    id = "tax_liability"
    severity = 40

    def evaluate(self, data: Dataset, ctx):
        r = compute(data, ctx)
        start, end = window(ctx)
        oracle = {j.get("jurisdiction_id"): j for j in (data.get("report") or {}).get("jurisdictions") or []}
        for jid, j in sorted(r["by"].items(), key=lambda kv: -kv[1]["tax"]):
            o = oracle.get(jid) or {}
            amount_ok = abs(money(o.get("tax_billed")) - j["tax"]) <= Decimal("0.01")
            count_ok = int(o.get("invoice_count") or 0) == len(j["invoices"])
            yield Finding(
                finding_type="tax_liability", rule="tax_liability", severity=20, status=CONTEXT,
                entity_type="TaxJurisdiction", entity_id=jid, entity_ref=j["name"], total_exposure=j["tax"],
                currency=ctx.currency,
                summary=f"{j['name']} ({j['rate']}%): {fmt(j['tax'], ctx.currency)} sales tax on {len(j['invoices'])} "
                        f"invoice(s), {start} … {end}; the platform report says {fmt(money(o.get('tax_billed')), ctx.currency)}"
                        f" on {o.get('invoice_count', 0)}.",
                details={"state_code": j["state"], "rate": j["rate"], "invoice_count": len(j["invoices"]),
                         "oracle_amount": str(money(o.get("tax_billed"))), "oracle_count": o.get("invoice_count"),
                         "reconciled": amount_ok, "count_matches": count_ok})
            if not amount_ok or not count_ok:
                yield Finding(
                    finding_type=DATA_QUALITY, rule="stored_value_mismatch", status=DATA_QUALITY,
                    severity=50 if not amount_ok else 15, entity_type="TaxJurisdiction", entity_id=f"{jid}:oracle",
                    entity_ref=j["name"], currency=ctx.currency,
                    summary=f"{j['name']}: " + (f"the liability report's amount {fmt(money(o.get('tax_billed')), ctx.currency)} "
                                                 f"≠ ours {fmt(j['tax'], ctx.currency)}" if not amount_ok else
                                                 f"amounts agree, but the report counts {o.get('invoice_count')} invoices "
                                                 f"against our {len(j['invoices'])} (exempt rows filed against this "
                                                 f"jurisdiction)") + ".",
                    details={"oracle": o, "ours": {"tax": str(j["tax"]), "invoices": len(j["invoices"])}})
        yield Finding(
            finding_type="tax_liability", rule="use_tax_accrued", severity=30 if r["use"] == 0 else 40, status=CONTEXT,
            entity_type="Bills", entity_id="use_tax", entity_ref="use tax accrued", total_exposure=r["use"],
            currency=ctx.currency,
            summary=f"Use tax accrued on purchases {start} … {end}: {fmt(r['use'], ctx.currency)}"
                    + (" — see US-02 for purchases where use tax may be owed." if r["use"] == 0 else "."),
            details={"bills_with_use_tax": sum(1 for b in data.get("bills", []) if money(b.get("use_tax_accrued")))})


class PeriodSalesUseTax(Playbook):

    @property
    def rules(self):
        return [SalesUseLiability()]

    def fetch(self, ctx, fetcher) -> Dataset:
        start, end = window(ctx)
        report = fetcher.rest_get(REPORT, {"from_date": str(start), "to_date": str(end), "basis": "accrual"})
        return Dataset(invoices=fetcher.list("Invoice"), bills=fetcher.list("Bill"),
                       jurisdictions=fetcher.list("TaxJurisdiction"), report=report)

    def context(self, data, findings, ctx):
        r = compute(data, ctx)
        rep = data.get("report") or {}
        start, end = window(ctx)
        return {"window": f"{start} … {end}", "total sales tax": str(sum((j["tax"] for j in r["by"].values()), Decimal("0"))),
                "report total": str(money(rep.get("total_tax_billed"))), "taxable sales": str(r["taxable"]),
                "report taxable sales": str(money(rep.get("taxable_sales"))), "exempt sales": str(r["exempt"]),
                "report exempt sales": str(money(rep.get("exempt_sales"))), "use tax accrued": str(r["use"]),
                "filing frequency": sorted({j.get("filing_frequency") for j in data["jurisdictions"]} - {None})}

    def summary(self, outcome, ctx):
        c = outcome.context
        n = sum(1 for f in outcome.findings if f.rule == "tax_liability")
        agrees = money(c["total sales tax"]) == money(c["report total"])
        gaps = [f.entity_ref for f in outcome.findings if f.rule == "stored_value_mismatch"]
        return (f"{c['window']}: sales tax liability {fmt(money(c['total sales tax']), ctx.currency)} across {n} "
                f"jurisdiction(s), {'matching' if agrees else 'NOT matching'} the platform's liability report"
                f"{' to the cent' if agrees else ' (' + fmt(money(c['report total']), ctx.currency) + ')'}"
                + (f"; count gaps on {', '.join(gaps)}" if gaps else "")
                + f". Use tax accrued: {fmt(money(c['use tax accrued']), ctx.currency)}.")
