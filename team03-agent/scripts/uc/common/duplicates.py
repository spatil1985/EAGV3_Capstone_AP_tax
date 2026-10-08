"""Duplicate-bill tiers shared by UC-05 (India) and US-07 (US).

Tier 1 exact        same vendor (GSTIN/TIN or id) + normalised supplier bill number + fiscal year
Tier 2 over_billed  bill_match says the PO was billed beyond the ordered quantity
Tier 3 suspicious   same vendor, same positive grand_total, dates ≤ 3 days apart, not two bills
                    from one recurring template; strong when the line items are identical

`paid_state` turns each pair into recovery (both paid) or prevention (hold the unpaid one).
"""

import re
from datetime import datetime
from decimal import Decimal
from itertools import combinations

from scripts.findings import Finding
from scripts.money import fmt, money
from scripts.uc.common.dates import day, fy_label
from scripts.uc.common.records import NOT_POSTED, party_of, ref

TIER_SEVERITY = {"exact": 95, "over_billed": 85, "suspicious_strong": 75, "suspicious_weak": 50}
WINDOW_DAYS = 3


def normalise(number) -> str:
    """Upper-case, drop spaces, '-' and '/', and leading zeros of every number run:
    'INV/0042' and 'inv-42' are the same supplier document."""
    text = re.sub(r"[\s\-/]", "", str(number or "")).upper()
    return re.sub(r"(?<!\d)0+(?=\d)", "", text)


def candidates(bills):
    return [b for b in bills if (b.get("status") or "").lower() not in NOT_POSTED - {"draft"}
            and (b.get("status") or "").lower() != "void"]


def lines_key(bill) -> tuple:
    return tuple(sorted((str(l.get("_item_id_display") or l.get("item_id") or l.get("description")),
                         str(money(l.get("qty"))), str(money(l.get("rate"))))
                        for l in bill.get("items") or []))


def is_paid(bill, paid_ids: set) -> bool:
    return (bill["id"] in paid_ids or money(bill.get("amount_paid")) > 0
            or (money(bill.get("balance_due")) <= 0 and money(bill.get("grand_total")) > 0))


def paid_state(a, b, paid_ids):
    pa, pb = is_paid(a, paid_ids), is_paid(b, paid_ids)
    return ("both_paid", "recover") if pa and pb else (("one_paid", "hold_unpaid") if pa or pb
                                                       else ("neither_paid", "hold_one"))


def paid_bill_ids(payments) -> set:
    ids = set()
    for p in payments:
        for b in p.get("bills") or []:
            ids.add(b.get("bill_id") or b.get("id"))
        for a in p.get("applied_allocations") or []:
            if a.get("target_entity") == "Bill":
                ids.add(a.get("target_id"))
    return ids


def vendor_key(bill, data):
    party = data.index("parties", "id").get(bill.get("vendor_id")) or {}
    return party.get("gst_no") or party.get("tin") or bill.get("vendor_id")


def exact_pairs(bills, data, ctx):
    groups: dict = {}
    for b in bills:
        if b.get("bill_number") and day(b.get("date")):
            key = (vendor_key(b, data), normalise(b["bill_number"]), fy_label(day(b["date"]), ctx.tax_regime))
            groups.setdefault(key, []).append(b)
    for key, group in groups.items():
        for a, b in combinations(sorted(group, key=lambda x: x.get("date") or ""), 2):
            yield a, b, "exact", {"key": list(map(str, key))}


def suspicious_pairs(bills):
    by_vendor: dict = {}
    for b in bills:
        if money(b.get("grand_total")) > 0 and day(b.get("date")):
            by_vendor.setdefault(b.get("vendor_id"), []).append(b)
    suppressed = 0
    out = []
    for group in by_vendor.values():
        for a, b in combinations(sorted(group, key=lambda x: (x.get("date"), x.get("id"))), 2):
            if money(a.get("grand_total")) != money(b.get("grand_total")):
                continue
            gap = abs((day(a["date"]) - day(b["date"])).days)
            if gap > WINDOW_DAYS:
                continue
            if a.get("recurring_bill_id") and a.get("recurring_bill_id") == b.get("recurring_bill_id"):
                suppressed += 1
                continue
            same = bool(a.get("items")) and lines_key(a) == lines_key(b)
            note = {"days_apart": gap, "same_line_items": same,
                    "same_purchase_order": bool(a.get("purchase_order_id"))
                    and a.get("purchase_order_id") == b.get("purchase_order_id")}
            created = [_ts(a.get("created_at")), _ts(b.get("created_at"))]
            if all(created) and abs((created[0] - created[1]).total_seconds()) <= 5:
                note["possible_double_submit"] = True
            out.append((a, b, "suspicious_strong" if same else "suspicious_weak", note))
    return out, suppressed


def _ts(value):
    try:
        return datetime.fromisoformat(str(value)) if value else None
    except ValueError:
        return None


def pair_finding(a, b, tier, note, data, ctx, paid_ids) -> Finding:
    # the later-entered bill is the one to hold
    first, second = sorted((a, b), key=lambda x: (x.get("created_at") or "", x.get("id")))
    state, action = paid_state(first, second, paid_ids)
    amount = money(second.get("grand_total"))
    vid, vname = party_of(second, data)
    r1, r2 = ref(first, "number"), ref(second, "number")
    what = {"exact": "same supplier bill number", "suspicious_strong": "same amount and items",
            "suspicious_weak": "same amount, different or missing line detail"}[tier]
    return Finding(
        finding_type="duplicate_payment", rule=f"duplicate_{tier}", severity=TIER_SEVERITY[tier],
        entity_type="Bill", entity_id=second["id"], entity_ref=r2, total_exposure=amount,
        currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
        summary=f"{r1} / {r2} ({vname}) — {fmt(amount, ctx.currency)} each, {what}, "
                f"{note.get('days_apart', '?')} day(s) apart. "
                + {"recover": "Both paid: recover one from the vendor.",
                   "hold_unpaid": "One is paid: hold the other.",
                   "hold_one": "Neither paid: hold one pending vendor confirmation."}[action],
        details={"tier": tier, "pair_entity_id": first["id"], "pair_entity_ref": r1, "paid_state": state,
                 "action": action, **note},
    )


def over_billed_finding(bill, match: dict, data, ctx) -> Finding | None:
    lines = ((match or {}).get("live") or {}).get("lines") or []
    over = [l for l in lines if money(l.get("billed_to_date_qty")) > money(l.get("ordered_qty")) > 0]
    if not over:
        return None
    extra = sum(((money(l["billed_to_date_qty"]) - money(l["ordered_qty"])) * money(l.get("bill_rate") or l.get("po_rate"))
                 for l in over), Decimal("0")).quantize(Decimal("0.01"))
    vid, vname = party_of(bill, data)
    number = ref(bill, "number")
    return Finding(
        finding_type="duplicate_payment", rule="duplicate_over_billed", severity=TIER_SEVERITY["over_billed"],
        entity_type="Bill", entity_id=bill["id"], entity_ref=number, total_exposure=extra,
        currency=ctx.currency, counterparty_id=vid, counterparty_name=vname,
        summary=f"{number} ({vname}) — its purchase order has been billed beyond the quantity ordered on "
                f"{len(over)} line(s); about {fmt(extra, ctx.currency)} billed twice.",
        details={"tier": "over_billed", "purchase_order_id": bill.get("purchase_order_id"),
                 "lines": [{k: l.get(k) for k in ("ordered_qty", "received_qty", "billed_qty", "billed_to_date_qty", "flags")}
                           for l in over]},
    )


def match_result(raw: dict) -> dict:
    """bill_match replies {"result": {...}} or the object itself."""
    return raw.get("result", raw) if isinstance(raw, dict) else {}
