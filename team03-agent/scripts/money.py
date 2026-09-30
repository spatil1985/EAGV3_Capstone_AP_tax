"""Money helpers: Decimal, ROUND_HALF_UP to 2 dp, locale-aware display.

harness_plan.md §5 makes this the shared money contract — no floats in amounts.
"""

from decimal import ROUND_HALF_UP, Decimal, InvalidOperation

CENTS = Decimal("0.01")
SYMBOLS = {"INR": "₹", "USD": "$"}


def money(value) -> Decimal:
    """Platform amounts arrive as float, int, str or None; normalise to 2 dp."""
    if value is None or value == "":
        return Decimal("0.00")
    try:
        return Decimal(str(value)).quantize(CENTS, rounding=ROUND_HALF_UP)
    except InvalidOperation as exc:
        raise ValueError(f"not an amount: {value!r}") from exc


def fmt(amount: Decimal, currency: str = "INR") -> str:
    """₹1,24,267.28 for INR (lakh grouping), $124,267.28 otherwise."""
    amount = money(amount)
    sign = "-" if amount < 0 else ""
    whole, _, paise = f"{abs(amount):.2f}".partition(".")
    if currency == "INR" and len(whole) > 3:
        head, tail = whole[:-3], whole[-3:]
        groups = []
        while len(head) > 2:
            groups.insert(0, head[-2:])
            head = head[:-2]
        if head:
            groups.insert(0, head)
        whole = ",".join(groups + [tail])
    elif currency != "INR":
        whole = f"{int(whole):,}"
    return f"{sign}{SYMBOLS.get(currency, currency + ' ')}{whole}.{paise}"
