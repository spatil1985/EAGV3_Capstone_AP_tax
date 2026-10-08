"""US purchase-side taxability shared by US-02 (use tax owed) and US-11 (sales tax paid on exempt
purchases).

A playbook table classifies each bill line by its description (CPA confirmation needed — US README
caveats); the use-tax rate is the combined rate of the configured jurisdictions in the company's
state (place of use), e.g. OH 5.75% + Stark County 0.75% = 6.5%.
"""

import re
from decimal import Decimal

from scripts.money import money

# (class, pattern, note). First match wins; anything else is "unclassified".
LINE_CLASSES = [
    ("exempt_manufacturing", r"production material|raw material|consumed in manufactur",
     "used directly in manufacturing (Ohio R.C. 5739.02(B)(42)(g))"),
    ("exempt_resale", r"for resale|resale stock", "purchased for resale"),
    ("non_taxable_service", r"freight|shipping|carrier|haulage", "transport by a common carrier"),
    ("non_taxable_service", r"consult|internal audit|iso 9001|advisory", "professional consulting"),
    ("non_taxable_service", r"internet|fibre|fiber|broadband", "internet access"),
    ("taxable_service", r"housekeeping|janitorial|cleaning", "building maintenance / janitorial (taxable in Ohio)"),
    ("taxable_service", r"pest|extermin", "exterminating (taxable in Ohio)"),
    ("taxable_service", r"users\b.*plan|software|saas|subscription", "automatic data processing for business use"),
    ("taxable_goods", r"sign|banner|furniture|office supplies", "tangible goods for own use"),
]


def classify(line) -> tuple[str, str]:
    text = f"{line.get('description') or ''} {line.get('_item_id_display') or ''}".lower()
    for cls, pattern, note in LINE_CLASSES:
        if re.search(pattern, text):
            return cls, note
    return "unclassified", "needs classification"


def line_amount(line) -> Decimal:
    return money(line.get("amount") if line.get("amount") not in (None, "") else line.get("taxable_amount"))


def place_of_use_rate(data) -> tuple[Decimal, list]:
    org = (data.get("org") or [{}])[0]
    state = str(org.get("state") or "").upper()
    rows = [j for j in data.get("jurisdictions", []) if str(j.get("state_code") or "").upper() == state
            and (j.get("status") or "active") == "active"]
    return sum((money(j.get("rate_percentage")) for j in rows), Decimal("0")), [j.get("name") for j in rows]


def untaxed(bill) -> bool:
    return money(bill.get("total_tax")) == 0 and not bill.get("taxes")
