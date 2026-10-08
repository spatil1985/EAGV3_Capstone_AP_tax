"""UC-07 — School: exempt / taxable supply split.

Spec: docs/usecases/IN/uc-07-school-exempt-taxable-split.md.
Question: "Which of our income streams are actually taxable, and are we treating them correctly?"

Statute: Notification 12/2017-CT(R) entry 66 — services by an educational institution to its
students (pre-school to higher secondary), and services *to* it for student transport, catering,
security/cleaning and admissions/exams, are exempt. Printed books (HSN 4901) are nil-rated goods.
Stationery, uniforms, coaching by a non-institution, and hall hire are taxable.

Engine: scripts/uc/common/exempt_split.py. Classification is Item.tax_preference; the school
stream table only checks that the master matches the law. No school tenant exists, so live runs
use --vertical school against Suryodaya's data to exercise the engine.
"""

from aptax.playbooks.base import Dataset, Playbook, Rule
from scripts.uc.common.exempt_split import line_findings, master_findings, turnover_split

SCHOOL_STREAMS = [
    # (stream, expected treatment, code prefixes, keywords, basis)
    ("tuition", "exempt", ("9992",), ("tuition", "school fee", "term fee", "admission fee", "exam fee"),
     "12/2017-CT(R) entry 66(a)"),
    ("student transport", "exempt", (), ("school bus", "student transport", "bus fee"), "12/2017-CT(R) entry 66(b)(i)"),
    ("books", "exempt", ("4901",), ("textbook", "printed book"), "HSN 4901 nil rate (2/2017-CT(R))"),
    ("hostel / boarding", "review", (), ("hostel", "boarding"), "depends on whether it is part of the education"),
    ("stationery", "taxable", ("4820",), ("stationery", "notebook"), "HSN 4820 taxable"),
    ("uniforms", "taxable", ("61", "62"), ("uniform",), "HSN 61/62 taxable"),
    ("coaching", "taxable", (), ("coaching", "tuition class", "entrance prep"), "not an educational institution"),
    ("hall hire", "taxable", ("9972",), ("hall hire", "auditorium rent", "rent"), "renting is taxable"),
]


class SchoolSplit(Rule):
    id = "supply_classification"
    severity = 60

    def evaluate(self, data: Dataset, ctx):
        items = data.get("items", [])
        yield from master_findings(items, SCHOOL_STREAMS, ctx, "school")
        yield from line_findings(data.get("invoices", []), data.index("items", "id"), data, ctx)


class SchoolExemptSplit(Playbook):

    @property
    def rules(self):
        return [SchoolSplit()]

    def fetch(self, ctx, fetcher) -> Dataset:
        return Dataset(items=fetcher.list("Item"), invoices=fetcher.list("Invoice", direction="receivable"))

    def context(self, data, findings, ctx):
        split = turnover_split(data["invoices"], data.index("items", "id"))
        return {"items": len(data["items"]), "receivable invoices": len(data["invoices"]),
                "turnover split by month (Item.tax_preference)": dict(list(split.items())[-3:]),
                "basis": "Item.tax_preference (zero tax is not evidence of exemption)"}

    def summary(self, outcome, ctx):
        count = lambda rule: sum(1 for f in outcome.findings if f.rule == rule)  # noqa: E731
        return (f"Item master: {count('classification_conflict')} classification conflict(s), "
                f"{count('stream_treatment_mismatch')} stream(s) treated against the school rules. Sales: "
                f"{count('exempt_but_taxed')} exempt line(s) taxed, {count('taxable_but_untaxed')} taxable line(s) "
                f"untaxed, {count('item_tax_line_invalid')} invoice(s) with inconsistent tax lines.")
