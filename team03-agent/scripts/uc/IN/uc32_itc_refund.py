"""UC-32 — Refund of accumulated input credit (Rule 89): zero-rated supplies and inverted duty.

Spec: docs/usecases/IN/uc-32-itc-refund-zero-rated-inverted.md.
Question: "We have credit piling up because we export or because our inputs are taxed higher than our
sales. How much can we get refunded, and by when?"

Statute: s.54(3) CGST Act; Rule 89(4) zero-rated refund = zero-rated turnover × net ITC ÷ adjusted
total turnover (net ITC = inputs + input services, no capital goods); Rule 89(5) inverted duty (net
ITC = inputs only, Notification 14/2022-CT); s.54(1) 2-year window from the relevant date.

Period: the FY to date (ATT and net ITC from live documents dated in it).
Rules:
  refund_eligible_zero_rated  zero-tax SEZ/export/deemed-export turnover under LUT → Rule 89(4) amount
  refund_eligible_inverted    an output rate below the inputs' rate → Rule 89(5) amount
  lut_unverified              the zero-rated refund rests on an LUT whose validity can't be proved (UC-20)
  refund_window_closing       the 2-year window for the earliest zero-rated invoice is < 90 days away
Net ITC uses each bill's trusted tax, else its stored total_tax (labelled) — the same rule as UC-24.
"""

import re
from datetime import timedelta
from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day, fy_label, fy_start
from scripts.uc.common.records import NOT_POSTED
from scripts.uc.common.tax import doc_tax

ZERO_RATED = {"sez", "overseas", "deemed_export"}
LUT = re.compile(r"\bLUT\b|letter of undertaking", re.I)
REFUND_WINDOW_DAYS = 730      # s.54(1): 2 years


def in_fy(doc, ctx) -> bool:
    d = day(doc.get("date"))
    return bool(d) and fy_start(ctx.as_of, "gst") <= d <= ctx.as_of and \
        (doc.get("status") or "").lower() not in NOT_POSTED


def figures(data, ctx) -> dict:
    sales = [i for i in data.get("invoices", []) if i.get("direction") == "receivable" and in_fy(i, ctx)]
    att = sum((money(i.get("taxable_value")) for i in sales), Decimal("0"))
    zero = [i for i in sales if (i.get("gst_treatment") or "").lower() in ZERO_RATED
            and money(i.get("total_tax")) == 0]
    zr_turnover = sum((money(i.get("taxable_value")) for i in zero), Decimal("0"))
    credit = {"input": Decimal("0"), "input_services": Decimal("0"), "capital_goods": Decimal("0")}
    stored_used = 0
    for b in data.get("bills", []):
        if not in_fy(b, ctx) or (b.get("ims_status") or "").lower() in ("reject", "rejected"):
            continue
        kind = b.get("itc_eligibility")
        if kind not in credit:
            continue
        tax = doc_tax(b)
        if tax is None:
            stored_used += 1
        credit[kind] += tax["total"] if tax else money(b.get("total_tax"))
    out_rates = {Decimal(str(t.get("rate"))) * (2 if re.search(r"CGST|SGST", str(t.get("tax_type")), re.I) else 1)
                 for i in sales for t in i.get("taxes") or [] if t.get("rate") not in (None, "")}
    in_rates = {money(l.get("tax_percentage")) for b in data.get("bills", []) if in_fy(b, ctx)
                for l in b.get("items") or [] if money(l.get("tax_percentage")) > 0}
    return {"att": att, "zero": zero, "zr_turnover": zr_turnover, "credit": credit, "stored_used": stored_used,
            "out_rates": out_rates, "in_rates": in_rates}


class Refund(Rule):
    id = "itc_refund"
    severity = 55

    def evaluate(self, data: Dataset, ctx):
        f = figures(data, ctx)
        label = fy_label(ctx.as_of, "gst")
        net = f["credit"]["input"] + f["credit"]["input_services"]
        if f["zr_turnover"] > 0 and f["att"] > 0:
            refund = min((f["zr_turnover"] * net / f["att"]).quantize(CENTS), net)
            luts = [e for e in data.get("exemptions", []) if LUT.search(str(e.get("exemption_reason") or ""))]
            yield Finding(
                finding_type="itc_refund", rule="refund_eligible_zero_rated", severity=self.severity,
                entity_type="FiscalYear", entity_id=f"89-4:{label}", entity_ref=label, total_exposure=refund,
                currency=ctx.currency,
                summary=f"About {fmt(refund, ctx.currency)} of {label} credit is refundable on zero-rated supplies "
                        f"under LUT (Rule 89(4): {fmt(f['zr_turnover'], ctx.currency)} × {fmt(net, ctx.currency)} ÷ "
                        f"{fmt(f['att'], ctx.currency)}), once the LUT is confirmed valid.",
                details={"period": label, "zero_rated_turnover": str(f["zr_turnover"]),
                         "adjusted_total_turnover": str(f["att"]), "net_itc": str(net),
                         "capital_goods_excluded": str(f["credit"]["capital_goods"]), "refund_amount": str(refund),
                         "bills_on_stored_total_tax": f["stored_used"]})
            yield Finding(
                finding_type="itc_refund", rule="lut_unverified", severity=40, entity_type="TaxExemption",
                entity_id=(luts[0].get("id") if luts else "none"), entity_ref="LUT", currency=ctx.currency,
                summary="The refund assumes the zero-rated supplies were made under a valid LUT; "
                        + ("an LUT record exists but has no dates or ARN (UC-20)." if luts else "no LUT record exists."),
                details={"lut_records": len(luts)})
            earliest = min(day(i["date"]) for i in f["zero"])
            closes = earliest + timedelta(days=REFUND_WINDOW_DAYS)
            if (closes - ctx.as_of).days <= 90:
                yield Finding(
                    finding_type="itc_refund", rule="refund_window_closing", severity=70, entity_type="FiscalYear",
                    entity_id=f"window:{label}", entity_ref=label, total_exposure=refund, currency=ctx.currency,
                    summary=f"The 2-year refund window (s.54(1)) for zero-rated supplies from {earliest} closes on "
                            f"{closes}.", details={"relevant_date": str(earliest), "window_closes": str(closes)})
        if f["out_rates"] and f["in_rates"] and max(f["in_rates"]) > min(f["out_rates"]):
            yield Finding(
                finding_type="itc_refund", rule="refund_eligible_inverted", severity=self.severity,
                entity_type="FiscalYear", entity_id=f"89-5:{label}", entity_ref=label, currency=ctx.currency,
                summary=f"Some inputs are taxed at {max(f['in_rates'])}%, above the {min(f['out_rates'])}% output rate: "
                        f"an inverted-duty refund (Rule 89(5), inputs only) may be available. Compute per product.",
                details={"input_rates": sorted(map(str, f["in_rates"])), "output_rates": sorted(map(str, f["out_rates"]))})


class ItcRefund(Playbook):

    @property
    def rules(self):
        return [Refund()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice", direction="receivable"), bills=fetcher.list("Bill"),
                       exemptions=fetcher.list("TaxExemption"))

    def context(self, data, findings, ctx):
        f = figures(data, ctx)
        return {"period": fy_label(ctx.as_of, "gst"), "zero-rated invoices (zero tax)": len(f["zero"]),
                "zero-rated turnover": str(f["zr_turnover"]), "adjusted total turnover": str(f["att"]),
                "credit by eligibility": {k: str(v) for k, v in f["credit"].items()},
                "output rates": sorted(map(str, f["out_rates"])), "input rates": sorted(map(str, f["in_rates"]))}

    def summary(self, outcome, ctx):
        zr = next((f for f in outcome.findings if f.rule == "refund_eligible_zero_rated"), None)
        inv = any(f.rule == "refund_eligible_inverted" for f in outcome.findings)
        return ((zr.summary if zr else "No zero-rated supplies under LUT this FY, so no Rule 89(4) refund.")
                + (" An inverted-duty position may exist." if inv else " No inverted-duty position exists."))
