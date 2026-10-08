"""UC-02 — Blocked credit audit, s.17(5) CGST Act.

Spec: docs/usecases/IN/uc-02-blocked-credit-audit.md.
Question: "Have we claimed credit on anything the law blocks?"

Rules:
  section_17_5                  a line on an ITC-claiming bill whose HSN/SAC prefix or text
                                matches a blocked category. Exposure = the line's share of the
                                bill's trusted tax. Always flagged for human confirmation:
                                the exceptions (further supply, obligatory under law, plant and
                                machinery) are not determinable from ledger fields.
  itc_possibly_under_claimed    a bill marked `ineligible` whose lines are ordinary inputs
                                (no blocked match): credit may have been given up (spec §11.4).
  missing_required_field        (data_quality) an ITC-claiming bill with lines that have no
                                HSN/SAC, so the blocked-category table can't see them (§11.3).
"""

from decimal import Decimal

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.lines import hsn, line_taxes, line_text
from scripts.uc.common.records import NOT_POSTED, party_of, ref
from scripts.uc.common.tax import doc_tax, untrusted_tax

CLAIMING = {"input", "input_services", "capital_goods"}

# (category, s.17(5) clause, HSN/SAC prefixes, keywords). Prefixes are spec §4/§11;
# keywords catch services the HSN alone under-determines.
BLOCKED = [
    ("motor_vehicle", "(a)/(aa)", ("8703", "8711"), ("car ", "motor car", "vehicle purchase", "two-wheeler")),
    ("food_beverage_catering", "(b)", ("2106", "2201", "2202", "9963"),
     ("canteen", "catering", "food", "lunch", "dinner", "restaurant", "hotel stay", "beverage")),
    ("club_membership", "(b)", ("9996", "9997"), ("club", "membership", "gym", "fitness", "health spa")),
    ("works_contract_immovable_property", "(c)/(d)", ("9954",),
     ("civil work", "construction", "renovation", "building work")),
    ("gifts_personal", "(g)/(h)", (), ("gift", "diwali hamper", "personal use")),
]


def blocked_category(code: str, text: str):
    for category, clause, prefixes, words in BLOCKED:
        if code and any(code.startswith(p) for p in prefixes):
            return category, clause, f"HSN/SAC {code}"
        hit = next((w for w in words if w in text), None)
        if hit:
            return category, clause, f"text '{hit.strip()}'"
    return None


def _items(data):
    return data.index("items", "id")


def _claiming(bill):
    return (bill.get("itc_eligibility") in CLAIMING
            and (bill.get("status") or "").lower() not in NOT_POSTED)


class BlockedCredit(Rule):
    id = "section_17_5"
    severity = 70

    def evaluate(self, data: Dataset, ctx):
        items = _items(data)
        for bill in data.get("bills", []):
            if not _claiming(bill):
                continue
            matches = [(i, l, blocked_category(hsn(l, items), line_text(l, items)))
                       for i, l in enumerate(bill.get("items") or [])]
            matches = [(i, l, m) for i, l, m in matches if m]
            if not matches:
                continue
            shares = line_taxes(bill)
            if shares is None:
                yield untrusted_tax(bill, "Bill", blocks="UC-02 ITC at risk", currency=ctx.currency)
                continue
            vid, vname = party_of(bill, data)
            number = ref(bill, "bill_number", "number")
            for i, line, (category, clause, why) in matches:
                at_risk = shares[i][1]
                yield Finding(
                    finding_type="blocked_credit_suspected", rule=self.id, severity=self.severity,
                    entity_type="Bill", entity_id=bill["id"], entity_ref=number,
                    total_exposure=at_risk, reversal_base_amount=at_risk, currency=ctx.currency,
                    counterparty_id=vid, counterparty_name=vname,
                    summary=f"{number} ({vname}) — {fmt(at_risk, ctx.currency)} ITC claimed on "
                            f"{category.replace('_', ' ')} ({why}), blocked under s.17(5){clause} unless "
                            f"an exception applies.",
                    details={"blocked_category": category, "clause": f"s.17(5){clause}", "matched_on": why,
                             "line_index": i, "line_item_id": line.get("item_id"),
                             "line_item_name": line.get("_item_id_display") or line.get("description"),
                             "hsn_or_sac": hsn(line, items), "exception_test_required": True,
                             "exception_test_note": "Confirm no further-supply, obligatory-under-law or "
                                                    "plant-and-machinery exception before reversing."},
                )


class UnderClaimed(Rule):
    id = "itc_possibly_under_claimed"
    severity = 30

    def evaluate(self, data, ctx):
        items = _items(data)
        for bill in data.get("bills", []):
            if bill.get("itc_eligibility") != "ineligible" or (bill.get("status") or "").lower() in NOT_POSTED:
                continue
            lines = bill.get("items") or []
            if not lines or any(blocked_category(hsn(l, items), line_text(l, items)) for l in lines):
                continue
            tax = doc_tax(bill)
            amount = tax["total"] if tax else money(bill.get("total_tax"))
            if amount <= 0:
                continue
            vid, vname = party_of(bill, data)
            number = ref(bill, "bill_number", "number")
            codes = sorted({hsn(l, items) or "blank" for l in lines})
            yield Finding(
                finding_type="itc_possibly_under_claimed", rule=self.id, severity=self.severity,
                entity_type="Bill", entity_id=bill["id"], entity_ref=number, total_exposure=amount,
                currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
                summary=f"{number} ({vname}) is marked ineligible, but its lines ({', '.join(codes)}) are "
                        f"ordinary inputs with no blocked category: {fmt(amount, ctx.currency)} of credit "
                        f"may have been given up. The reason is not recorded.",
                details={"hsn_codes": codes, "tax_source": tax["source"] if tax else "unsourced"},
            )


class BlankHsn(Rule):
    id = "missing_required_field"
    severity = 5

    def evaluate(self, data, ctx):
        items = _items(data)
        for bill in data.get("bills", []):
            if not _claiming(bill):
                continue
            blank = [i for i, l in enumerate(bill.get("items") or []) if not hsn(l, items)]
            if blank:
                number = ref(bill, "bill_number", "number")
                yield Finding(
                    finding_type=DATA_QUALITY, rule=self.id, entity_type="Bill", entity_id=bill["id"],
                    entity_ref=number, status=DATA_QUALITY, severity=self.severity, currency=ctx.currency,
                    summary=f"{number}: {len(blank)} line(s) have no HSN/SAC, so the blocked-category "
                            f"check can't classify them.",
                    details={"field": "items[].hsn_or_sac", "lines": blank, "blocks": "UC-02 classification"},
                )


class BlockedCreditAudit(Playbook):

    @property
    def rules(self):
        return [BlockedCredit(), UnderClaimed(), BlankHsn()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(bills=fetcher.list("Bill"), items=fetcher.list("Item"))

    def context(self, data, findings, ctx):
        items = _items(data)
        claiming = [b for b in data["bills"] if _claiming(b)]
        lines = [l for b in claiming for l in b.get("items") or []]
        return {"bills claiming ITC": len(claiming), "lines": len(lines),
                "lines classifiable (HSN/SAC present)": sum(1 for l in lines if hsn(l, items)),
                "bills marked ineligible": sum(1 for b in data["bills"] if b.get("itc_eligibility") == "ineligible")}

    def summary(self, outcome, ctx):
        blocked = [f for f in outcome.findings if f.rule == "section_17_5"]
        under = [f for f in outcome.findings if f.rule == "itc_possibly_under_claimed"]
        blank = sum(len(f.details.get("lines", [])) for f in outcome.findings if f.rule == "missing_required_field")
        total = sum((f.total_exposure for f in blocked), Decimal("0"))
        cats = sorted({f.details["blocked_category"] for f in blocked})
        head = (f"{len({f.entity_id for f in blocked})} bill(s) claim ITC on suspected blocked categories; "
                f"{fmt(total, ctx.currency)} at risk ({', '.join(cats)})." if blocked
                else "No ITC claimed on a blocked category among classifiable lines.")
        return (head + (f" {len(under)} ineligible bill(s) look like ordinary inputs (credit possibly "
                        f"under-claimed)." if under else "")
                + (f" {blank} line(s) have no HSN/SAC and could not be checked." if blank else ""))
