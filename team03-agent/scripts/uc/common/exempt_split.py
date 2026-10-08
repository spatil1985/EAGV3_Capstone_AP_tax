"""Exempt / taxable supply split shared by UC-07 (school) and UC-14 (clinic).

Classification comes from `Item.tax_preference`, never from whether tax was charged: on this
instance "zero tax" does not mean "exempt" (UC-07 §6 — every invoice before 2026-09 is zero-tax).

Stage 1 (item master):  classification_conflict — HSN goods typed services (or SAC typed goods),
                        tax_exempt with taxable=1 (or taxable with taxable=0), exempt with no reason.
Stage 1b (vertical):    stream_treatment_mismatch — the item maps to a revenue stream whose
                        statutory treatment (a per-vertical table) differs from tax_preference.
Stage 2 (sales lines):  exempt_but_taxed, taxable_but_untaxed (not SEZ/export/deemed export).
Aggregate:              E (exempt), T (taxable), F = E + T by month — UC-08/UC-15's input.
"""

from decimal import Decimal

from scripts.findings import DATA_QUALITY, Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import period_of, previous_period
from scripts.uc.common.lines import line_taxes, line_value
from scripts.uc.common.records import NOT_POSTED, party_of
from scripts.uc.common.tax import line_tax

ZERO_RATED = {"sez", "overseas", "deemed_export"}


def code_kind(code: str) -> str | None:
    code = str(code or "").strip()
    return None if not code else ("services" if code.startswith("99") else "goods")


def item_conflicts(item: dict) -> list[str]:
    out = []
    kind, typed = code_kind(item.get("hsn_or_sac") or item.get("hsn_sac")), item.get("product_type")
    if kind and typed and kind != typed:
        out.append(f"code {item.get('hsn_or_sac')} is {kind} but product_type is {typed}")
    pref, flag = item.get("tax_preference"), item.get("taxable")
    if pref == "tax_exempt" and flag in (1, True):
        out.append("tax_exempt but taxable=1")
    if pref == "taxable" and flag in (0, False):
        out.append("taxable but taxable=0")
    if pref == "tax_exempt" and not item.get("tax_exemption_reason"):
        out.append("tax_exempt with no exemption reason")
    return out


def stream_of(item: dict, streams) -> tuple | None:
    """streams: [(name, expected 'exempt'|'taxable'|'review', code prefixes, keywords, basis)]."""
    code = str(item.get("hsn_or_sac") or item.get("hsn_sac") or "")
    text = f"{item.get('name') or ''} {item.get('description') or ''}".lower()
    for name, expected, prefixes, words, basis in streams:
        if (code and any(code.startswith(p) for p in prefixes)) or any(w in text for w in words):
            return name, expected, basis
    return None


def master_findings(items, streams, ctx, vertical: str):
    for item in items:
        problems = item_conflicts(item)
        if problems:
            yield Finding(finding_type="supply_classification", rule="classification_conflict", severity=40,
                          entity_type="Item", entity_id=item["id"], entity_ref=item.get("name"),
                          currency=ctx.currency,
                          summary=f"Item {item.get('name')}: {'; '.join(problems)}. Fix the master before "
                                  f"sales on it are classified.",
                          details={"problems": problems, "tax_preference": item.get("tax_preference"),
                                   "hsn_or_sac": item.get("hsn_or_sac")})
        hit = stream_of(item, streams)
        if hit and hit[1] in ("exempt", "taxable"):
            name, expected, basis = hit
            actual = "exempt" if item.get("tax_preference") == "tax_exempt" else "taxable"
            if item.get("tax_preference") and actual != expected:
                yield Finding(finding_type="supply_classification", rule="stream_treatment_mismatch", severity=60,
                              entity_type="Item", entity_id=item["id"], entity_ref=item.get("name"),
                              currency=ctx.currency,
                              summary=f"Item {item.get('name')} is a {vertical} '{name}' supply, which is {expected} "
                                      f"({basis}), but the master marks it {actual}.",
                              details={"stream": name, "expected": expected, "basis": basis,
                                       "tax_preference": item.get("tax_preference")})


def sales_lines(invoices):
    for inv in invoices:
        if inv.get("direction", "receivable") != "receivable" or (inv.get("status") or "").lower() in NOT_POSTED:
            continue
        shares = line_taxes(inv)
        for i, line in enumerate(inv.get("items") or []):
            tax = shares[i][1] if shares is not None else sum(line_tax(line).values(), Decimal("0"))
            yield inv, i, line, tax, shares is not None


def line_findings(invoices, items_by_id, data, ctx, since: str | None = None):
    """Sales-line checks for invoices dated in or after period `since` (default: the previous
    month), so a monthly run reviews the period being filed rather than re-reporting history."""
    since = since or previous_period(ctx.as_of)
    recent = [inv for inv in invoices if (period_of(inv.get("date")) or "") >= since]
    for inv, i, line, tax, trusted in sales_lines(recent):
        item = items_by_id.get(line.get("item_id"))
        if not item or not item.get("tax_preference"):
            continue
        treatment = (inv.get("gst_treatment") or "").lower()
        rule = None
        if item["tax_preference"] == "tax_exempt" and tax > 0:
            rule, sev, what = "exempt_but_taxed", 70, f"is marked tax-exempt but was charged {fmt(tax, ctx.currency)} GST"
        elif item["tax_preference"] == "taxable" and tax == 0 and treatment not in ZERO_RATED and line_value(line) > 0:
            rule, sev, what = "taxable_but_untaxed", 50, "is taxable but no GST was charged"
        if not rule:
            continue
        pid, pname = party_of(inv, data)
        yield Finding(finding_type="supply_classification", rule=rule, severity=sev, entity_type="Invoice",
                      entity_id=inv["id"], entity_ref=inv.get("number"), total_exposure=tax if tax > 0 else Decimal("0"),
                      currency=ctx.currency, counterparty_id=pid, counterparty_name=pname,
                      summary=f"{inv.get('number')} line {i + 1} — {item.get('name')} {what}"
                              + ("" if trusted else "; the invoice's tax fields are also internally inconsistent")
                              + ".",
                      details={"line_index": i, "item_id": item["id"], "item_name": item.get("name"),
                               "tax_preference": item["tax_preference"], "tax_charged": str(tax),
                               "taxable_amount": str(line_value(line)), "gst_treatment": treatment,
                               "tax_source_trusted": trusted})
    for inv in recent:
        if inv.get("direction", "receivable") == "receivable" and (inv.get("status") or "").lower() not in NOT_POSTED \
                and line_taxes(inv) is None:
            yield Finding(finding_type=DATA_QUALITY, rule="item_tax_line_invalid", entity_type="Invoice",
                          entity_id=inv["id"], entity_ref=inv.get("number"), status=DATA_QUALITY, severity=10,
                          currency=ctx.currency,
                          summary=f"{inv.get('number')}: tax lines are internally inconsistent; tax figures on it "
                                  f"are excluded from totals.",
                          details={"blocks": "exempt-split tax charged"})


def turnover_split(invoices, items_by_id) -> dict:
    out: dict = {}
    for inv, _, line, _, _ in sales_lines(invoices):
        item = items_by_id.get(line.get("item_id"))
        pref = (item or {}).get("tax_preference")
        bucket = "E" if pref == "tax_exempt" else ("T" if pref == "taxable" else "unclassified")
        row = out.setdefault(period_of(inv.get("date")) or "undated", {"E": Decimal("0"), "T": Decimal("0"),
                                                                       "unclassified": Decimal("0")})
        row[bucket] += line_value(line)
    return {p: {"exempt_E": str(r["E"]), "taxable_T": str(r["T"]), "total_F": str(r["E"] + r["T"]),
                "unclassified": str(r["unclassified"])} for p, r in sorted(out.items())}


def exempt_share(split: dict, period: str) -> Decimal | None:
    row = split.get(period)
    if not row or money(row["total_F"]) == 0:
        return None
    return money(row["exempt_E"]) / money(row["total_F"])
