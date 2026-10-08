"""Three-way match (PO ↔ receipt ↔ bill) shared by UC-11 (India) and US-09 (US).

The engine is the platform's `endpoint.accounting.bill_match` (read-only in practice — N3 tags it
WRITE; N2 shows it never persists). `Bill.match_status` is quarantined (N2): always call the
endpoint, never read the stored field.
"""

from decimal import Decimal

from aptax.agentswitch.fetch import FetchError
from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.duplicates import match_result
from scripts.uc.common.records import NOT_POSTED, party_of, ref

MATCH_TOOL = "endpoint.accounting.bill_match"
SEVERITY = {"billed_not_received": 85, "over_billed": 75, "price_variance": 55}


def po_bills(bills):
    return [b for b in bills if b.get("purchase_order_id")
            and (b.get("status") or "").lower() not in NOT_POSTED - {"draft"}]


def fetch_matches(fetcher, bills) -> tuple[dict, int]:
    out, failed = {}, 0
    for bill in po_bills(bills):
        try:
            out[bill["id"]] = match_result(fetcher.call(MATCH_TOOL, {"bill_id": bill["id"]}))
        except FetchError:
            failed += 1
    return out, failed


def classify(match: dict) -> tuple[str | None, list]:
    live = (match or {}).get("live") or {}
    lines = live.get("lines") or []
    # received_qty None means bill_match had no receipt basis (two-way match), not "0 received"
    not_received = [l for l in lines if l.get("received_qty") is not None
                    and money(l.get("received_qty")) == 0 and money(l.get("billed_qty")) > 0]
    if live.get("receipt_problem") or not_received:
        return "billed_not_received", not_received or lines
    over = [l for l in lines if "qty_over_ordered" in (l.get("flags") or [])
            or money(l.get("billed_to_date_qty")) > money(l.get("ordered_qty")) > 0]
    if over:
        return "over_billed", over
    tol = money(live.get("price_tolerance_pct") or 0)
    priced = [l for l in lines if abs(money(l.get("price_variance_pct"))) > tol]
    if priced:
        return "price_variance", priced
    return None, []


def finding(bill, match, data, ctx, *, cross_flags=()) -> Finding | None:
    rule, lines = classify(match)
    if not rule:
        return None
    live = match.get("live") or {}
    vid, vname = party_of(bill, data)
    number = ref(bill, "number", "bill_number")
    amount = money(bill.get("balance_due") or bill.get("grand_total"))
    if rule == "over_billed":
        amount = sum(((money(l.get("billed_to_date_qty")) - money(l.get("ordered_qty")))
                      * money(l.get("bill_rate") or l.get("po_rate")) for l in lines), Decimal("0")).quantize(Decimal("0.01"))
    first = lines[0] if lines else {}
    text = {
        "billed_not_received": f"billed for {money(first.get('billed_qty'))} unit(s), "
                               f"{money(first.get('received_qty'))} received against the PO"
                               + (f" ({live.get('receipt_problem')})" if live.get("receipt_problem") else "")
                               + ". Hold payment and ITC until receipt is confirmed",
        "over_billed": f"the PO has been billed beyond the ordered quantity on {len(lines)} line(s), "
                       f"about {fmt(amount, ctx.currency)} over",
        "price_variance": f"bill rate differs from the PO rate beyond the {live.get('price_tolerance_pct')}% "
                          f"tolerance on {len(lines)} line(s)",
    }[rule]
    return Finding(
        finding_type="three_way_match", rule=rule, severity=SEVERITY[rule], entity_type="Bill",
        entity_id=bill["id"], entity_ref=number, total_exposure=amount, currency=ctx.currency,
        counterparty_id=vid, counterparty_name=vname, summary=f"{number} ({vname}) — {text}.",
        details={"purchase_order_id": bill.get("purchase_order_id"), "match_status": live.get("status"),
                 "receipt_problem": live.get("receipt_problem"), "stock_entry_id": live.get("stock_entry_id"),
                 "lines": [{k: l.get(k) for k in ("ordered_qty", "received_qty", "billed_qty", "billed_to_date_qty",
                                                  "po_rate", "bill_rate", "price_variance_pct", "flags")} for l in lines],
                 "cross_flags": list(cross_flags),
                 "action": "hold_payment" if rule == "billed_not_received" else "review"},
    )
