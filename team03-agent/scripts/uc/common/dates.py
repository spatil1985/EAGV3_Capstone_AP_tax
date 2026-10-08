"""Dates, periods and financial years.

Platform dates arrive as 'YYYY-MM-DD', ISO datetimes, None or (rarely) junk. `day()`
never raises: a malformed date becomes None, so one bad record can't abort a run (the
UC-12 validation found that failure mode).
"""

from calendar import monthrange
from datetime import date


def day(value) -> date | None:
    if not value:
        return None
    if isinstance(value, date):
        return value
    try:
        return date.fromisoformat(str(value)[:10])
    except ValueError:
        return None


def days_between(start, end) -> int | None:
    a, b = day(start), day(end)
    return (b - a).days if a and b else None


def month_bounds(period: str) -> tuple[date, date]:
    """'2026-09' → (2026-09-01, 2026-09-30)."""
    year, month = (int(x) for x in period.split("-")[:2])
    return date(year, month, 1), date(year, month, monthrange(year, month)[1])


def period_of(value) -> str | None:
    d = day(value)
    return d.strftime("%Y-%m") if d else None


def previous_period(as_of: date) -> str:
    """The last complete month before `as_of` — the period a return is filed for."""
    year, month = (as_of.year, as_of.month - 1) if as_of.month > 1 else (as_of.year - 1, 12)
    return f"{year:04d}-{month:02d}"


def in_period(value, period: str) -> bool:
    return period_of(value) == period


def fy_start(on: date, regime: str) -> date:
    """India: financial year April–March. US: calendar year."""
    if regime == "gst":
        return date(on.year if on.month >= 4 else on.year - 1, 4, 1)
    return date(on.year, 1, 1)


def fy_label(on: date, regime: str) -> str:
    start = fy_start(on, regime)
    return f"FY {start.year}-{str(start.year + 1)[2:]}" if regime == "gst" else f"CY {start.year}"


def add_months(d: date, months: int) -> date:
    m = d.month - 1 + months
    year, month = d.year + m // 12, m % 12 + 1
    return date(year, month, min(d.day, monthrange(year, month)[1]))
