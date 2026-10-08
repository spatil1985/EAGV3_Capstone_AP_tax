"""Per-document tax source (docs/usecases/IN/README.md, "Correction 2026-09-30" and Rule 0).

    tax_source(doc) :=
        "taxes[]"  if |Σ taxes[].amount − total_tax| ≤ 1 and every taxes[].tax_type is non-blank
        "items[]"  elif |Σ item tax − total_tax| ≤ 1 and every taxed line passes line_is_valid
        "none"     otherwise → a data_quality row; the document is excluded from totals

`doc_tax(doc)` returns the head split {cgst, sgst, igst, cess, total} from whichever source
the document passes, or None. CreditNote `taxes[]` is stripped at fetch (N128), so credit
notes fall through to their item lines automatically.
"""

import re
from decimal import Decimal

from scripts.findings import DATA_QUALITY, Finding
from scripts.money import money

HEADS = ("cgst", "sgst", "igst", "cess")
TOLERANCE = Decimal("1.00")
HALF_TOLERANCE = Decimal("0.05")
_HEAD = re.compile(r"\b(IGST|CGST|SGST|UTGST|CESS)\b", re.I)


def line_tax(line: dict) -> dict:
    t = {h: money(line.get(f"{h}_amount")) for h in HEADS}
    t["sgst"] += money(line.get("utgst_amount"))     # UTGST stands in for SGST in a UT
    return t


def line_is_valid(line: dict) -> bool:
    t = line_tax(line)
    if (t["cgst"] > 0 or t["sgst"] > 0) and t["igst"] > 0:
        return False                                  # intra- and inter-state on one line
    if abs(t["cgst"] - t["sgst"]) > HALF_TOLERANCE:
        return False                                  # halves disagree
    rate = line.get("tax_percentage")
    if rate not in (None, 0, ""):
        expected = money(line.get("taxable_amount")) * Decimal(str(rate)) / 100
        if abs(t["cgst"] + t["sgst"] + t["igst"] - expected) > TOLERANCE:
            return False
    return True


def _taxes_split(doc: dict) -> dict | None:
    rows = doc.get("taxes") or []
    if not rows or any(not str(r.get("tax_type") or "").strip() for r in rows):
        return None
    split = {h: Decimal("0.00") for h in HEADS}
    for r in rows:
        m = _HEAD.search(str(r.get("tax_type")))
        if not m:
            return None
        head = m.group(1).lower()
        split["sgst" if head == "utgst" else head] += money(r.get("amount"))
    return split


def _items_split(doc: dict) -> dict | None:
    split = {h: Decimal("0.00") for h in HEADS}
    for line in doc.get("items") or []:
        t = line_tax(line)
        if any(t.values()) and not line_is_valid(line):
            return None
        for h in HEADS:
            split[h] += t[h]
    return split


def tax_source(doc: dict) -> str:
    total = money(doc.get("total_tax"))
    split = _taxes_split(doc)
    if split is not None and abs(sum(split.values()) - total) <= TOLERANCE:
        return "taxes[]"
    split = _items_split(doc)
    if split is not None and abs(sum(split.values()) - total) <= TOLERANCE:
        return "items[]"
    return "none"


def doc_tax(doc: dict) -> dict | None:
    """{cgst, sgst, igst, cess, total, source} or None when no source can be trusted."""
    source = tax_source(doc)
    if source == "none":
        return None
    split = _taxes_split(doc) if source == "taxes[]" else _items_split(doc)
    return {**split, "total": sum(split.values(), Decimal("0.00")), "source": source}


def clean_heads(doc: dict) -> dict | None:
    """Head split from the rows that survived quarantine (VendorCredit keeps only real GST heads,
    UC-25 §6), else valid item lines. Unlike doc_tax it doesn't require the total to reconcile,
    because the product-named rows were removed from it."""
    split = _taxes_split(doc)
    if split is None:
        split = _items_split(doc)
    if split is None:
        return None
    return {**split, "total": sum(split.values(), Decimal("0.00"))}


def untrusted_tax(doc: dict, entity_type: str, *, blocks: str, currency: str = "INR") -> Finding:
    """The shared data_quality row for a document whose tax can't be sourced."""
    item_sum = sum((sum(line_tax(l).values()) for l in doc.get("items") or []), Decimal("0"))
    tax_sum = sum((money(r.get("amount")) for r in doc.get("taxes") or []), Decimal("0"))
    number = doc.get("number") or doc.get("bill_number") or doc.get("invoice_number") or doc.get("id")
    return Finding(
        finding_type=DATA_QUALITY, rule="stored_value_mismatch", entity_type=entity_type,
        entity_id=doc["id"], entity_ref=number, currency=currency, status=DATA_QUALITY, severity=10,
        summary=f"{number}: neither taxes[] ({tax_sum}) nor valid item lines ({item_sum}) reconcile "
                f"to total_tax {money(doc.get('total_tax'))}; excluded from totals.",
        details={"field": "total_tax", "observed": {"taxes[]": str(tax_sum), "items[]": str(item_sum)},
                 "expected": str(money(doc.get("total_tax"))), "blocks": blocks},
    )
