"""Reverse-charge (RCM) helpers shared by UC-03 (domestic notified services) and UC-21
(import of services): the notified-service table, the bill's GST treatment, and the
liability a recipient must self-assess.
"""

from decimal import Decimal

from scripts.money import CENTS, money
from scripts.uc.common.lines import line_value

# (supplier type, SAC prefixes, rate constant, notification). Spec UC-03 §5a.
NOTIFIED_SERVICES = [
    ("gta", ("9965", "996791"), "rcm_rate_gta_pct", "13/2017-CT(R) entry 1"),
    ("legal", ("9982",), "rcm_rate_services_pct", "13/2017-CT(R) entry 2"),
    ("sponsorship", ("998397",), "rcm_rate_services_pct", "13/2017-CT(R) entry 4"),
]
DIRECTOR_WORDS = ("sitting fee", "director fee", "director's fee", "directors fee")


def treatment(bill: dict, party: dict | None) -> str:
    return (bill.get("gst_treatment") or (party or {}).get("gst_treatment") or "").lower()


def notified_type(bill: dict, party: dict | None):
    """(supplier_type, basis, rate_constant, notification) or None."""
    for line in bill.get("items") or []:
        code = str(line.get("hsn_or_sac") or "")
        for kind, prefixes, rate, notif in NOTIFIED_SERVICES:
            if any(code.startswith(p) for p in prefixes):
                return kind, f"hsn_or_sac={code}", rate, notif
        text = f"{line.get('description') or ''} {line.get('_item_id_display') or ''}".lower()
        if any(w in text for w in DIRECTOR_WORDS):
            return "director", "line text", "rcm_rate_services_pct", "13/2017-CT(R) entry 6"
    return None


def is_service_bill(bill: dict) -> bool:
    lines = bill.get("items") or []
    return bool(lines) and all(str(l.get("hsn_or_sac") or "").startswith("99") for l in lines)


def taxable_base(bill: dict) -> Decimal:
    base = sum((line_value(l) for l in bill.get("items") or []), Decimal("0"))
    return base if base > 0 else money(bill.get("taxable_value") or bill.get("net_total"))


def derived_liability(bill: dict, rate_pct) -> Decimal:
    return (taxable_base(bill) * Decimal(str(rate_pct)) / 100).quantize(CENTS)
