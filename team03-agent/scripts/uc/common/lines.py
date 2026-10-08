"""Per-line tax and classification for documents whose tax may live on the lines or in taxes[].

`line_taxes(doc)` returns [(line, tax)] where tax is the line's share of the document's
trusted tax: the line's own amounts when the document's source is items[], or a share of
taxes[] pro rata to the line's taxable amount when the source is taxes[]. Returns None when
the document's tax can't be sourced (the caller emits the data_quality row).
"""

from decimal import Decimal

from scripts.money import CENTS, money
from scripts.uc.common.tax import doc_tax, line_tax


def line_value(line: dict) -> Decimal:
    return money(line.get("taxable_amount") if line.get("taxable_amount") not in (None, "") else line.get("amount"))


def line_taxes(doc: dict) -> list[tuple[dict, Decimal]] | None:
    tax = doc_tax(doc)
    if tax is None:
        return None
    lines = doc.get("items") or []
    if tax["source"] == "items[]":
        return [(l, sum(line_tax(l).values(), Decimal("0"))) for l in lines]
    base = sum((line_value(l) for l in lines), Decimal("0"))
    if base <= 0:
        return [(l, (tax["total"] / len(lines)).quantize(CENTS)) for l in lines] if lines else []
    return [(l, (tax["total"] * line_value(l) / base).quantize(CENTS)) for l in lines]


def hsn(line: dict, items_by_id: dict | None = None) -> str:
    code = str(line.get("hsn_or_sac") or "").strip()
    if not code and items_by_id and line.get("item_id") in items_by_id:
        master = items_by_id[line["item_id"]]
        code = str(master.get("hsn_or_sac") or master.get("hsn_sac") or "").strip()
    return code


def line_text(line: dict, items_by_id: dict | None = None) -> str:
    parts = [line.get("description"), line.get("_item_id_display"), line.get("name")]
    if items_by_id and line.get("item_id") in items_by_id:
        m = items_by_id[line["item_id"]]
        parts += [m.get("name"), m.get("description")]
    return " ".join(str(p) for p in parts if p).lower()
