"""Pure timezone-aware schedule maths — no DB, no I/O (easy to unit-test).

A scheduled task fires at one or more times-of-day, either every day or on
chosen weekdays, interpreted in the *user's* timezone. ``compute_next_run``
returns the next fire instant in UTC so the scheduler can store/poll it cheaply.
DST transitions are handled by ``zoneinfo`` (we build aware local datetimes and
convert to UTC).
"""

from __future__ import annotations

import datetime as dt
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError


def zone(timezone: str) -> ZoneInfo:
    """Resolve an IANA name to a ZoneInfo, falling back to UTC."""
    try:
        return ZoneInfo(timezone or "UTC")
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return ZoneInfo("UTC")


def valid_timezone(timezone: str) -> bool:
    try:
        ZoneInfo(timezone)
        return True
    except (ZoneInfoNotFoundError, ValueError, KeyError):
        return False


def parse_times(times: list[str]) -> list[tuple[int, int]]:
    """Parse ["08:00", "20:30"] → sorted unique [(8, 0), (20, 30)]."""
    out: set[tuple[int, int]] = set()
    for t in times or []:
        try:
            hh, mm = str(t).split(":")
            h, m = int(hh), int(mm)
        except (ValueError, AttributeError):
            continue
        if 0 <= h < 24 and 0 <= m < 60:
            out.add((h, m))
    return sorted(out)


def compute_next_run(
    *,
    timezone: str,
    frequency: str,
    times: list[str],
    weekdays: list[int],
    after: dt.datetime,
    interval_days: int | None = None,
    anchor: dt.date | None = None,
) -> dt.datetime | None:
    """Next UTC fire instant strictly after ``after`` (UTC), or None if the
    schedule can never fire.

    Frequencies: ``daily`` (every day), ``weekly`` (chosen weekdays), ``interval``
    (every ``interval_days`` days counted from ``anchor``), ``as_needed`` (never
    fires → None). ``after`` and the result are UTC-aware.
    """
    if frequency == "as_needed":
        return None
    tods = parse_times(times)
    if not tods:
        return None
    tz = zone(timezone)
    if after.tzinfo is None:
        after = after.replace(tzinfo=dt.timezone.utc)
    local_after = after.astimezone(tz)

    weekly = frequency == "weekly"
    wd = {w for w in (weekdays or []) if 0 <= w <= 6} if weekly else None
    if weekly and not wd:
        return None

    interval = frequency == "interval"
    n = max(1, interval_days or 1)
    anchor_date = anchor or local_after.date()
    # Cover any weekday/interval + time combination within one full cycle.
    horizon = max(8, n + 1)

    for offset in range(0, horizon):
        day = (local_after + dt.timedelta(days=offset)).date()
        if weekly and day.weekday() not in wd:  # type: ignore[operator]
            continue
        if interval and (day - anchor_date).days % n != 0:
            continue
        for h, m in tods:
            cand = dt.datetime(day.year, day.month, day.day, h, m, tzinfo=tz)
            if cand > local_after:
                return cand.astimezone(dt.timezone.utc)
    return None
