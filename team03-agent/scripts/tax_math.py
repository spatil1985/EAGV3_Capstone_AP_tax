"""Deterministic arithmetic for tax reconciliation.

LLMs are prone to arithmetic drift/hallucination when aggregating many currency
rows, so all summation logic for tax liability lives here, not in the agent's
context window. Called by `playbooks/tax_audit.md`.
"""


def compute_tax_reconciliation(records: list, locale: str = "IN") -> dict:
    output_tax = 0.0
    input_tax_credit = 0.0
    unclaimed_credit = 0.0

    for item in records:
        amount = float(item.get("tax_amount", 0.0))
        doc_type = item.get("type")

        if doc_type == "sales_invoice":
            output_tax += amount
        elif doc_type == "purchase_bill":
            if item.get("is_itc_eligible") and item.get("is_claimed"):
                input_tax_credit += amount
            elif item.get("is_itc_eligible") and not item.get("is_claimed"):
                unclaimed_credit += amount

    net_liability = max(0.0, output_tax - input_tax_credit)

    return {
        "output_tax_total": round(output_tax, 2),
        "claimed_itc_total": round(input_tax_credit, 2),
        "unclaimed_itc_total": round(unclaimed_credit, 2),
        "net_liability": round(net_liability, 2),
        "locale": locale,
    }
