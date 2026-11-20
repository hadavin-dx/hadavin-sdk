"""The booking day of the Postgres money tests. `hadavin_reserve_spend` refuses a day more than `max_day_skew` days away
from the database's UTC date (review B3), so a test that reserves through it cannot use a fixed old date: it names
today's UTC date (or yesterday or tomorrow, inside the window) through these helpers."""

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta


def today_utc() -> date:
    return datetime.now(UTC).date()


def yesterday_utc() -> date:
    return today_utc() - timedelta(days=1)


def tomorrow_utc() -> date:
    return today_utc() + timedelta(days=1)
