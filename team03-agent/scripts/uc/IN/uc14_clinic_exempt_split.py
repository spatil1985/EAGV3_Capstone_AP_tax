"""UC-14 — Clinic: exempt / taxable supply split.

Spec: docs/usecases/IN/uc-14-clinic-exempt-taxable-split.md.
Question: "Which parts of what we do are taxable, and are we charging GST on the right ones?"

Statute: Notification 12/2017-CT(R) entry 74 — health care by a clinical establishment is exempt.
Room rent above ₹5,000/day (non-ICU) is taxable at 5% without ITC from 18 July 2022. OP pharmacy
is a supply of goods at the HSN rate; in-patient medicine is part of the exempt composite supply.
Cosmetic procedures are taxable unless reconstructive.

Engine: scripts/uc/common/exempt_split.py (as UC-07), with the clinic stream table, plus:
  room_rent_tax_wrong   a ward/room line above ₹5,000 per day not charged exactly 5%
No clinic tenant exists; live runs use --vertical clinic against Suryodaya's data.
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import Finding
from scripts.money import CENTS, fmt, money
from scripts.uc.common.exempt_split import line_findings, master_findings, sales_lines, turnover_split

CLINIC_STREAMS = [
    ("consultation / procedure", "exempt", ("9993",), ("consultation", "opd fee", "procedure", "surgery"),
     "12/2017-CT(R) entry 74"),
    ("cosmetic procedure", "taxable", (), ("cosmetic", "aesthetic", "hair transplant", "botox"),
     "not health care unless reconstructive"),
    ("ICU room", "exempt", (), ("icu", "iccu", "nicu", "ccu"), "ICU rooms exempt at any rate"),
    ("room rent", "review", (), ("ward", "room rent", "deluxe room", "private room"),
     "taxable 5% only above ₹5,000/day (rate-dependent)"),
    ("pharmacy", "review", ("3004",), ("tablet", "capsule", "syrup", "injection"),
     "OP sale taxable, IP composite exempt; no patient-type field"),
]
ROOM_WORDS = ("ward", "room rent", "deluxe room", "private room")
ICU_WORDS = ("icu", "iccu", "nicu", "ccu")


class ClinicSplit(Rule):
    id = "supply_classification"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        yield from master_findings(data.get("items", []), CLINIC_STREAMS, ctx, "clinic")
        yield from line_findings(data.get("invoices", []), data.index("items", "id"), data, ctx)


class RoomRent(Rule):
    id = "room_rent_tax_wrong"
    severity = 65

    def evaluate(self, data, ctx):
        threshold = money(ctx.constant("clinic_room_rent_threshold_inr"))
        rate = Decimal(str(ctx.constant("clinic_room_rent_rate_pct")))
        items = data.index("items", "id")
        for inv, i, line, tax, _ in sales_lines(data.get("invoices", [])):
            text = f"{line.get('description') or ''} {(items.get(line.get('item_id')) or {}).get('name') or ''}".lower()
            if not any(w in text for w in ROOM_WORDS) or any(w in text for w in ICU_WORDS):
                continue
            per_day = money(line.get("rate"))
            if per_day <= threshold:
                continue
            base = money(line.get("taxable_amount") or line.get("amount"))
            expected = (base * rate / 100).quantize(CENTS)
            if abs(tax - expected) <= 1:
                continue
            yield Finding(
                finding_type="supply_classification", rule=self.id, severity=self.severity, entity_type="Invoice",
                entity_id=inv["id"], entity_ref=inv.get("number"), total_exposure=abs(expected - tax),
                currency=ctx.currency,
                summary=f"{inv.get('number')} line {i + 1} — room at {fmt(per_day, ctx.currency)}/day is above "
                        f"{fmt(threshold, ctx.currency)}, so 5% ({fmt(expected, ctx.currency)}) is due; "
                        f"{fmt(tax, ctx.currency)} was charged.",
                details={"line_index": i, "per_day": str(per_day), "expected_tax": str(expected),
                         "tax_charged": str(tax), "itc": "none allowed on this supply"})


class ClinicExemptSplit(Playbook):

    @property
    def rules(self):
        return [ClinicSplit(), RoomRent()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(items=fetcher.list("Item"), invoices=fetcher.list("Invoice", direction="receivable"))

    def context(self, data, findings, ctx):
        split = turnover_split(data["invoices"], data.index("items", "id"))
        return {"items": len(data["items"]), "receivable invoices": len(data["invoices"]),
                "turnover split by month (Item.tax_preference)": dict(list(split.items())[-3:]),
                "pharmacy IP/OP": "no patient-type field: pharmacy lines are treated as OP (taxable)"}

    def summary(self, outcome, ctx):
        count = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"Item master: {count('classification_conflict')} conflict(s), {count('stream_treatment_mismatch')} "
                f"stream(s) against the clinic rules. Sales: {count('exempt_but_taxed')} exempt line(s) taxed, "
                f"{count('taxable_but_untaxed')} taxable line(s) untaxed, {count('room_rent_tax_wrong')} room-rent "
                f"line(s) not at 5%.")
