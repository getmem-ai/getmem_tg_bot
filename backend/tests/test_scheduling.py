"""Unit tests for timezone-aware schedule maths (no DB)."""

import datetime as dt

from app.core.scheduling import compute_next_run, parse_times, valid_timezone

UTC = dt.timezone.utc


def test_parse_times_filters_and_sorts() -> None:
    assert parse_times(["20:30", "08:00", "08:00", "bad", "25:00", "9:5"]) == [
        (8, 0),
        (9, 5),
        (20, 30),
    ]


def test_daily_same_day_when_time_still_ahead() -> None:
    # 06:00 UTC; daily 08:00 in Berlin (UTC+2 in June) = 06:00 UTC -> not strictly
    # after, so it rolls to tomorrow.
    after = dt.datetime(2026, 6, 14, 6, 0, tzinfo=UTC)
    nxt = compute_next_run(
        timezone="Europe/Berlin", frequency="daily", times=["08:00"], weekdays=[], after=after
    )
    assert nxt == dt.datetime(2026, 6, 15, 6, 0, tzinfo=UTC)


def test_daily_picks_earliest_future_time() -> None:
    # 06:30 UTC = 08:30 Berlin; times 08:00 & 20:00 -> next is 20:00 Berlin today.
    after = dt.datetime(2026, 6, 14, 6, 30, tzinfo=UTC)
    nxt = compute_next_run(
        timezone="Europe/Berlin",
        frequency="daily",
        times=["08:00", "20:00"],
        weekdays=[],
        after=after,
    )
    assert nxt == dt.datetime(2026, 6, 14, 18, 0, tzinfo=UTC)  # 20:00 CEST = 18:00 UTC


def test_weekly_lands_on_chosen_weekday() -> None:
    # 2026-06-14 is a Sunday. Weekly Monday(0) 09:00 UTC -> 2026-06-15 09:00.
    after = dt.datetime(2026, 6, 14, 6, 0, tzinfo=UTC)
    nxt = compute_next_run(
        timezone="UTC", frequency="weekly", times=["09:00"], weekdays=[0], after=after
    )
    assert nxt == dt.datetime(2026, 6, 15, 9, 0, tzinfo=UTC)


def test_returns_none_when_unfireable() -> None:
    after = dt.datetime(2026, 6, 14, 6, 0, tzinfo=UTC)
    assert (
        compute_next_run(
            timezone="UTC", frequency="daily", times=[], weekdays=[], after=after
        )
        is None
    )
    assert (
        compute_next_run(
            timezone="UTC", frequency="weekly", times=["09:00"], weekdays=[], after=after
        )
        is None
    )


def test_valid_timezone() -> None:
    assert valid_timezone("Europe/Moscow")
    assert valid_timezone("UTC")
    assert not valid_timezone("Mars/Olympus")
