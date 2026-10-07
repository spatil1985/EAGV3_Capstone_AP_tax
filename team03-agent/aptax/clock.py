"""Tenant-local time (governor day windows, default as-of dates, schedules).

`zoneinfo` needs the IANA database, which Windows does not ship (and `tzdata` is not a
dependency). Without it, India falls back to fixed IST (+05:30, no DST) and the US to
Eastern time with the federal DST rule: second Sunday of March 02:00 to first Sunday
of November 02:00 local.
"""

from datetime import UTC, date, datetime, timedelta, timezone

from aptax.config import TENANT_TIMEZONES

IST = timezone(timedelta(hours=5, minutes=30), "IST")


def _first_sunday_from(day: datetime) -> datetime:
    return day + timedelta(days=(6 - day.weekday()) % 7)


def us_eastern(now_utc: datetime) -> timezone:
    year = now_utc.year
    dst_start = _first_sunday_from(datetime(year, 3, 8, 7, tzinfo=UTC))    # 02:00 EST = 07:00 UTC
    dst_end = _first_sunday_from(datetime(year, 11, 1, 6, tzinfo=UTC))     # 02:00 EDT = 06:00 UTC
    if dst_start <= now_utc < dst_end:
        return timezone(timedelta(hours=-4), "EDT")
    return timezone(timedelta(hours=-5), "EST")


def tenant_tz(tenant: str, now_utc: datetime | None = None):
    try:
        from zoneinfo import ZoneInfo
        return ZoneInfo(TENANT_TIMEZONES[tenant])
    except Exception:  # noqa: BLE001 — no IANA database on this machine
        return IST if tenant == "in" else us_eastern(now_utc or datetime.now(UTC))


def tenant_now(tenant: str) -> datetime:
    now = datetime.now(UTC)
    return now.astimezone(tenant_tz(tenant, now))


def tenant_today(tenant: str) -> date:
    return tenant_now(tenant).date()
