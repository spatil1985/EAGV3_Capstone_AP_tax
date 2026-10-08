"""UC-18 — HSN rate consistency on outward supplies.

Spec: docs/usecases/IN/uc-18-hsn-rate-consistency.md.
Question: "Are we charging the right GST rate on every product we sell?"

There is no authoritative HSN → rate table on the platform (tax/compute takes the rate on trust,
`rate_source_authoritative: false`; requested as N426 T3.4), so this is a consistency check:

  hsn_rate_inconsistent   one HSN charged at more than one rate across sale lines
  rate_not_a_slab         a line rate that is not a GST slab on the invoice date (effective-dated:
                          12% and 28% left the schedule on 22 Sep 2025; a "9%" is usually a CGST
                          half stored as the full rate)
  rate_drift_from_master  a line rate that differs from its item's master rate (when the master
                          carries one)

Rate per line: the effective rate (tax ÷ taxable) when the line passes Rule 0 and carries tax;
otherwise `tax_percentage`. Every finding says which basis it used.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import money
from scripts.uc.common.dates import day
from scripts.uc.common.lines import line_value
from scripts.uc.common.tax import line_is_valid, line_tax

DEAD = {"void", "cancelled"}


def line_rate(line) -> tuple[Decimal | None, str]:
    tax = sum(line_tax(line).values(), Decimal("0"))
    base = line_value(line)
    if tax > 0 and base > 0 and line_is_valid(line):
        return (tax / base * 100).quantize(Decimal("0.01")), "effective"
    if line.get("tax_percentage") in (None, ""):
        return None, "none"
    return money(line.get("tax_percentage")), "tax_percentage"


def sale_lines(invoices):
    for inv in invoices:
        if inv.get("direction", "receivable") != "receivable" or (inv.get("status") or "").lower() in DEAD:
            continue
        for i, line in enumerate(inv.get("items") or []):
            code = str(line.get("hsn_or_sac") or "").strip()
            rate, basis = line_rate(line)
            if code and rate is not None:
                yield inv, i, line, code, rate, basis


def _num(r: Decimal) -> str:
    return f"{r.normalize():f}"


def _fmt_rate(r: Decimal) -> str:
    return f"{_num(r)}%"


class InconsistentHsn(Rule):
    id = "hsn_rate_inconsistent"
    severity = 55

    def evaluate(self, data: Dataset, ctx):
        groups: dict = {}
        for inv, i, line, code, rate, basis in sale_lines(data.get("invoices", [])):
            groups.setdefault(code, {}).setdefault(rate, []).append((inv.get("number"), basis))
        for code, rates in sorted(groups.items()):
            if len(rates) < 2:
                continue
            seen = {_fmt_rate(r): {"lines": len(v), "example": v[0][0],
                                   "basis": sorted({b for _, b in v})} for r, v in sorted(rates.items())}
            lines = sum(len(v) for v in rates.values())
            yield Finding(
                finding_type="rate_check", rule=self.id, severity=self.severity, entity_type="HSN",
                entity_id=code, entity_ref=code, currency=ctx.currency,
                summary=f"HSN {code} is charged at {len(rates)} different rates across {lines} sale lines "
                        f"({' / '.join(seen)}). At most one is correct. Fix the item master.",
                details={"hsn": code, "rates_seen": seen})


class NotASlab(Rule):
    id = "rate_not_a_slab"
    severity = 45

    def evaluate(self, data, ctx):
        for inv, i, line, code, rate, basis in sale_lines(data.get("invoices", [])):
            on = day(inv.get("date")) or ctx.as_of
            slabs = {Decimal(str(s)) for s in ctx.rule("gst_rate_slabs_pct", on)}
            if rate in slabs:
                continue
            half = rate * 2 in slabs
            yield Finding(
                finding_type="rate_check", rule=self.id, severity=self.severity, entity_type="Invoice",
                entity_id=inv["id"], entity_ref=inv.get("number"), currency=ctx.currency,
                summary=f"{inv.get('number')} line {i + 1} (HSN {code}) is charged at {_fmt_rate(rate)}, not a GST slab "
                        f"on {on}" + (f"; it looks like the CGST half of {_fmt_rate(rate * 2)}" if half else "") + ".",
                details={"hsn": code, "rate": _num(rate), "basis": basis, "invoice_date": str(on),
                         "slabs_in_force": sorted((_num(s) for s in slabs), key=Decimal),
                         "likely_half_of": _num(rate * 2) if half else None})


class MasterDrift(Rule):
    id = "rate_drift_from_master"
    severity = 40

    def evaluate(self, data, ctx):
        items = data.index("items", "id")
        for inv, i, line, code, rate, basis in sale_lines(data.get("invoices", [])):
            master = items.get(line.get("item_id")) or {}
            ref_rate = master.get("intra_state_tax_rate") or master.get("inter_state_tax_rate")
            if ref_rate in (None, "", 0) or rate == 0:
                continue
            if money(ref_rate) != rate:
                yield Finding(
                    finding_type="rate_check", rule=self.id, severity=self.severity, entity_type="Invoice",
                    entity_id=inv["id"], entity_ref=inv.get("number"), currency=ctx.currency,
                    summary=f"{inv.get('number')} line {i + 1} ({master.get('name')}) is charged {_fmt_rate(rate)}; "
                            f"the item master says {_fmt_rate(money(ref_rate))}.",
                    details={"hsn": code, "rate": str(rate), "master_rate": str(money(ref_rate)), "basis": basis})


class HsnRateConsistency(Playbook):

    @property
    def rules(self):
        return [InconsistentHsn(), NotASlab(), MasterDrift()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(invoices=fetcher.list("Invoice", direction="receivable"), items=fetcher.list("Item"))

    def context(self, data, findings, ctx):
        lines = list(sale_lines(data["invoices"]))
        return {"sale lines with an HSN and a rate": len(lines),
                "… rate basis": {b: sum(1 for *_, basis in lines if basis == b) for b in ("effective", "tax_percentage")},
                "distinct HSNs": len({code for _, _, _, code, _, _ in lines}),
                "authoritative rate table": "none on the platform (N426 T3.4)"}

    def summary(self, outcome, ctx):
        n = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"{n('hsn_rate_inconsistent')} HSN(s) are charged at more than one rate; {n('rate_not_a_slab')} "
                f"line(s) use a rate that is not a GST slab; {n('rate_drift_from_master')} line(s) differ from the "
                f"item master. This is a consistency check: the platform has no authoritative rate table.")
