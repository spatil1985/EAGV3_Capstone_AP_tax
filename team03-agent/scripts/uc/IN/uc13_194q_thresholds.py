"""UC-13 — s.194Q TDS on purchase of goods (buy side) and its mirror on our sales (sell side).

Spec: docs/usecases/IN/uc-13-194q-206c-thresholds.md.
Question: "Which suppliers or customers have we crossed the ₹50 lakh line with?"

Statute: s.194Q Income-tax Act 1961 — a buyer with preceding-FY turnover > ₹10 crore deducts
0.1% on goods purchases from one seller above ₹50 lakh in the FY (base excludes GST, CBDT
Circular 13/2021). s.206C(1H) is understood omitted from 1 April 2025, so the sell side is
built as the mirror: what our customers should deduct from us (a 26AS reconciliation break,
not our liability).

Rules:
  194q_not_deducted            buy side: a bill at or after the crossing point with no TDS
  194q_approaching             buy side: FY goods base ≥ 80% of the threshold, not yet crossed
  194q_customer_not_deducting  sell side: customer past the threshold, receipts show less TDS
                               than 0.1% of the excess

Goods = lines whose HSN does not start 99; blank HSN counts as goods (conservative) and the
number of blank lines is reported. Bases come from line taxable_amount, never grand_total (N7).
The buyer-turnover gate (₹10 crore) is not in the data: findings are "subject to turnover".
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.dates import day, fy_label, fy_start
from scripts.uc.common.lines import line_value
from scripts.uc.common.records import NOT_POSTED
from scripts.uc.common.tds import stored


def goods_base(doc) -> tuple[Decimal, int]:
    total, blank = Decimal("0"), 0
    for line in doc.get("items") or []:
        code = str(line.get("hsn_or_sac") or "")
        if code.startswith("99"):
            continue
        blank += 0 if code else 1
        total += line_value(line)
    return total, blank


def fy_docs(docs, ctx, party_key):
    start = fy_start(ctx.as_of, ctx.tax_regime)
    out: dict = {}
    for d in docs:
        when = day(d.get("date"))
        if when and start <= when <= ctx.as_of and (d.get("status") or "").lower() not in NOT_POSTED:
            out.setdefault(d.get(party_key), []).append(d)
    return {k: sorted(v, key=lambda x: (x.get("date"), x.get("id"))) for k, v in out.items()}


def _name(docs, key):
    return next((d.get(key) for d in docs if d.get(key)), None)


class BuySide(Rule):
    id = "194q_buy"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        threshold = money(ctx.constant("tds_194q_threshold_inr"))
        rate = Decimal(str(ctx.constant("tds_194q_rate_pct"))) / 100
        near = threshold * Decimal(str(ctx.constant("tds_194q_approaching_pct"))) / 100
        for vendor, bills in fy_docs(data.get("bills", []), ctx, "vendor_id").items():
            running = Decimal("0")
            crossed = None
            for bill in bills:
                base, _ = goods_base(bill)
                before, running = running, running + base
                if running <= threshold or base <= 0:
                    continue
                crossed = crossed or bill
                expected = ((running - max(before, threshold)) * rate).quantize(CENTS)
                if stored(bill)[0] <= 0:
                    yield Finding(
                        finding_type="tds_threshold", rule="194q_not_deducted", severity=self.severity,
                        entity_type="Bill", entity_id=bill["id"], entity_ref=bill.get("number"),
                        total_exposure=expected, currency=ctx.currency, counterparty_id=vendor,
                        counterparty_name=bill.get("_vendor_id_display"),
                        summary=f"{bill.get('number')} ({bill.get('_vendor_id_display')}) — FY goods purchases "
                                f"from this vendor are {fmt(running, ctx.currency)}, past the "
                                f"{fmt(threshold, ctx.currency)} 194Q line; {fmt(expected, ctx.currency)} TDS "
                                f"(0.1%) was not deducted. Subject to our turnover exceeding ₹10 crore.",
                        details={"side": "buy", "fy": fy_label(ctx.as_of, ctx.tax_regime),
                                 "cumulative_goods_base": str(running), "threshold": str(threshold),
                                 "crossed_on_document": crossed.get("number"), "expected_tds": str(expected),
                                 "recorded_tds": "0.00", "turnover_gate": "not in data"})
            if near <= running <= threshold:
                yield Finding(
                    finding_type="tds_threshold", rule="194q_approaching", severity=35, entity_type="Party",
                    entity_id=vendor, entity_ref=_name(bills, "_vendor_id_display"), currency=ctx.currency,
                    counterparty_id=vendor, counterparty_name=_name(bills, "_vendor_id_display"),
                    summary=f"{_name(bills, '_vendor_id_display')}: FY goods purchases {fmt(running, ctx.currency)}, "
                            f"{fmt(threshold - running, ctx.currency)} short of the 194Q line. Set up TDS before "
                            f"the next bill.",
                    details={"side": "buy", "cumulative_goods_base": str(running), "threshold": str(threshold)})


class SellSide(Rule):
    id = "194q_sell"
    severity = 45

    def evaluate(self, data, ctx):
        threshold = money(ctx.constant("tds_194q_threshold_inr"))
        rate = Decimal(str(ctx.constant("tds_194q_rate_pct"))) / 100
        start = fy_start(ctx.as_of, ctx.tax_regime)
        sales = [i for i in data.get("invoices", []) if i.get("direction", "receivable") == "receivable"]
        for customer, invoices in fy_docs(sales, ctx, "party_id").items():
            base = sum((goods_base(i)[0] for i in invoices), Decimal("0"))
            if base <= threshold:
                continue
            expected = ((base - threshold) * rate).quantize(CENTS)
            receipts = [r for r in data.get("receipts", []) if r.get("customer_id") == customer
                        and (day(r.get("date")) or start) >= start]
            recorded = sum((money(r.get("withholding_tax_amount")) or abs(money(r.get("tax_deducted")))
                            for r in receipts), Decimal("0"))
            if recorded >= expected:
                continue
            name = _name(invoices, "_party_id_display")
            yield Finding(
                finding_type="tds_threshold", rule="194q_customer_not_deducting", severity=self.severity,
                entity_type="Party", entity_id=customer, entity_ref=name, total_exposure=expected - recorded,
                currency=ctx.currency, counterparty_id=customer, counterparty_name=name,
                summary=f"{name} has bought {fmt(base, ctx.currency)} of goods from us this FY (past the ₹50 lakh "
                        f"194Q line), so about {fmt(expected, ctx.currency)} TDS should show on its payments; "
                        f"{fmt(recorded, ctx.currency)} is recorded on {len(receipts)} receipt(s). Expect a 26AS "
                        f"mismatch; confirm with the customer.",
                details={"side": "sell", "fy": fy_label(ctx.as_of, ctx.tax_regime), "cumulative_goods_base": str(base),
                         "threshold": str(threshold), "expected_tds": str(expected), "recorded_tds": str(recorded),
                         "invoices": len(invoices), "receipts": len(receipts),
                         "caveat": "applies only if the customer's own turnover exceeds ₹10 crore"})


class Thresholds194Q(Playbook):

    @property
    def rules(self):
        return [BuySide(), SellSide()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), invoices=fetcher.list("Invoice", direction="receivable"),
                       receipts=fetcher.list("PaymentReceived"))

    def context(self, data, findings, ctx):
        vendors = fy_docs(data["bills"], ctx, "vendor_id")
        top = sorted(((sum((goods_base(b)[0] for b in bs), Decimal("0")), _name(bs, "_vendor_id_display"))
                      for bs in vendors.values()), reverse=True)[:3]
        blank = sum(goods_base(b)[1] for bs in vendors.values() for b in bs)
        return {"FY": fy_label(ctx.as_of, ctx.tax_regime), "vendors with FY bills": len(vendors),
                "largest FY goods bases (buy side)": [f"{n}: {v}" for v, n in top],
                "blank-HSN bill lines counted as goods": blank,
                "buyer turnover > ₹10 crore": "not in data (N426 T4.3)"}

    def summary(self, outcome, ctx):
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"Buy side: {n('194q_not_deducted')} bill(s) past the ₹50 lakh line without TDS, "
                f"{n('194q_approaching')} vendor(s) approaching it. Sell side: {n('194q_customer_not_deducting')} "
                f"customer(s) past the line with no matching TDS on their payments (26AS check).")
