"""Exact and fuzzy invoice matching for duplicate-payment detection.

Deterministic grouping/matching logic lives here rather than in the agent's
context window, per `SKILL.md` Hard Rule 3. Called by
`playbooks/duplicate_audit.md`.
"""

from datetime import datetime, timedelta

DATE_FORMAT = "%Y-%m-%d"
SUSPICIOUS_WINDOW_DAYS = 3


def _parse_date(value: str) -> datetime:
    return datetime.strptime(value, DATE_FORMAT)


def find_duplicate_invoices(invoices: list) -> list:
    """Group invoices by vendor_id and flag exact/suspicious duplicate pairs.

    Returns a list of dicts:
      {"vendor_id", "original_id", "duplicate_id", "amount", "match_type"}
    """
    by_vendor: dict = {}
    for inv in invoices:
        by_vendor.setdefault(inv["vendor_id"], []).append(inv)

    duplicates = []
    for vendor_id, vendor_invoices in by_vendor.items():
        vendor_invoices = sorted(vendor_invoices, key=lambda i: i["date"])
        seen: list = []

        for inv in vendor_invoices:
            match = _match_against_seen(inv, seen)
            if match:
                duplicates.append(
                    {
                        "vendor_id": vendor_id,
                        "original_id": match["id"],
                        "duplicate_id": inv["id"],
                        "amount": inv["amount"],
                        "match_type": match["match_type"],
                    }
                )
            seen.append(inv)

    return duplicates


def _match_against_seen(candidate: dict, seen: list) -> dict | None:
    for prior in seen:
        if prior["invoice_number"] == candidate["invoice_number"]:
            return {"id": prior["id"], "match_type": "exact"}

        if prior["amount"] == candidate["amount"]:
            delta = abs(_parse_date(candidate["date"]) - _parse_date(prior["date"]))
            if delta <= timedelta(days=SUSPICIOUS_WINDOW_DAYS):
                return {"id": prior["id"], "match_type": "suspicious"}

    return None
