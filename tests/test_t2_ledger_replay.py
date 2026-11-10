"""T2: ledger replay on the spend ledger (``MemoryStore.add_spend`` / ``spend_totals`` through ``Limits``) with a fake
clock, over windows of 6 minutes, 25 hours and 31 days (STANDING ORDERS 6d, plan v4 T2).

What the ledger is (read, not assumed): UTC calendar buckets, one per (agent, day) and per (agent, month), keyed by
``now().date()`` at charge time. It is NOT a rolling window: a charge 6 minutes after another lands in the same
bucket only if no UTC midnight lies between them. The expected totals below come from a separate oracle that
buckets each (time, usd) event by its own UTC date and (year, month), never by the code under test.

"No double count" means: each charge appears once in its day total and once in its month total; reading
(``blocked``, ``spend_totals``) never changes a total; replaying the same event list into a fresh ledger gives the
same totals.
"""

from __future__ import annotations

from datetime import UTC, datetime, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.store.memory import MemoryStore
from tests.meter_support import (
    AGENT,
    build_limits,
    check_a_charge_returns_the_total_of_its_own_month_only,
    check_real_now_buckets_by_utc_date_on_a_machine_in_ist,
    utc,
)

USD = Decimal("0.10")
MINUTES6 = timedelta(minutes=6)
HOURS25 = timedelta(hours=25)
DAYS31 = timedelta(days=31)

# Start points chosen so each window length is tried inside a bucket, just before a boundary and exactly on one.
STARTS = [
    utc(2026, 3, 10, 12, 0),  # mid-day, mid-month
    utc(2026, 3, 10, 23, 57),  # 6 min window crosses UTC midnight
    utc(2026, 3, 10, 23, 59, 59),  # last second of the day
    utc(2026, 3, 10, 0, 0),  # first instant of the day
    utc(2026, 3, 31, 23, 57),  # crosses a month end
    utc(2026, 12, 31, 23, 57),  # crosses a year end
    utc(2026, 2, 28, 23, 30),  # February, 25 h reaches 1 March
    utc(2024, 2, 28, 23, 30),  # leap year: 29 February exists
    utc(2026, 1, 1, 0, 0),  # 31 days lands on exactly 1 February 00:00
    utc(2024, 2, 29, 23, 57),  # the leap day itself: 6 minutes reach 1 March
    utc(2026, 4, 30, 23, 57),  # a 30-day month end: 6 minutes reach 1 May
    utc(2026, 1, 31, 23, 57),  # 6 minutes reach 1 February
    utc(
        2026, 2, 1, 0, 0
    ),  # 31 days over a 28-day month lands on 4 March (no 1 March bucket in between)
    utc(2026, 2, 20, 8, 0),  # 31 days from a short month land on 23 March
    utc(
        2026, 3, 10, 23, 59, 59, 999999
    ),  # one microsecond before midnight: every later event is the 11th
]
WINDOWS = [("6min", MINUTES6), ("25h", HOURS25), ("31d", DAYS31)]


def oracle(events: list[tuple[datetime, Decimal]], now: datetime) -> tuple[Decimal, Decimal]:
    """(day total, month total) of the events, bucketed by their own UTC date and (year, month)."""
    here = now.astimezone(UTC)  # an aware time in any zone is bucketed by its UTC calendar date
    utc_events = [(t.astimezone(UTC), u) for t, u in events]
    day = sum((u for t, u in utc_events if t.date() == here.date()), Decimal(0))
    month = sum(
        (u for t, u in utc_events if (t.year, t.month) == (here.year, here.month)), Decimal(0)
    )
    return day, month


def replay(events, monkeypatch, daily="1000", monthly="1000"):
    limits, store, clock = build_limits(daily, monthly, events[0][0], monkeypatch)
    returned = []
    for t, usd in events:
        clock.set(t)
        returned.append(limits.charge(AGENT, usd))
    return limits, store, clock, returned


def event_times(start: datetime, window: timedelta) -> list[datetime]:
    """Five instants: the start, the window midpoint, and one second before, exactly at and one second after the window end."""
    tick = timedelta(seconds=1)
    return [
        start,
        start + window / 2,
        start + window - tick,
        start + window,
        start + window + tick,
    ]


@pytest.mark.parametrize("start", STARTS, ids=lambda s: s.isoformat())
@pytest.mark.parametrize("name,window", WINDOWS)
def test_every_charge_lands_in_its_own_day_and_month_exactly_once(name, window, start, monkeypatch):
    events = [(t, USD) for t in event_times(start, window)]
    _, store, clock, returned = replay(events, monkeypatch)
    for i, (t, _) in enumerate(events):
        # the totals the charge returned: only events up to and including this one, as of that moment
        assert returned[i] == oracle(events[: i + 1], t), f"{name}: charge {i} at {t}"
        # and what a later read shows for that same day and month
        clock.set(t)
        assert store.spend_totals(AGENT, t.date()) == oracle(events, t), f"{name}: read at {t}"


@pytest.mark.parametrize("start", STARTS, ids=lambda s: s.isoformat())
@pytest.mark.parametrize("name,window", WINDOWS)
def test_reads_never_change_a_total_and_a_replay_gives_the_same_totals(
    name, window, start, monkeypatch
):
    events = [(t, USD) for t in event_times(start, window)]
    limits, store, clock, _ = replay(events, monkeypatch)
    before = {t.date(): store.spend_totals(AGENT, t.date()) for t, _ in events}
    for t, _ in events:
        clock.set(t)
        for _ in range(3):
            limits.blocked(AGENT)
            store.spend_totals(AGENT, t.date())
    assert {t.date(): store.spend_totals(AGENT, t.date()) for t, _ in events} == before
    _, store2, _, _ = replay(events, monkeypatch)
    assert {t.date(): store2.spend_totals(AGENT, t.date()) for t, _ in events} == before


def test_a_day_total_is_the_sum_of_its_own_charges_only_across_25_hours(monkeypatch):
    t0 = utc(2026, 3, 10, 0, 30)
    events = [(t0, Decimal("0.30")), (t0 + HOURS25, Decimal("0.70"))]  # 11 March 01:30
    _, store, _, _ = replay(events, monkeypatch)
    assert store.spend_totals(AGENT, t0.date()) == (Decimal("0.30"), Decimal("1.00"))
    assert store.spend_totals(AGENT, (t0 + HOURS25).date()) == (Decimal("0.70"), Decimal("1.00"))


def test_a_month_total_does_not_carry_over_31_days(monkeypatch):
    t0 = utc(2026, 1, 1, 0, 0)
    events = [(t0, Decimal("0.40")), (t0 + DAYS31, Decimal("0.60"))]  # 1 February 00:00
    _, store, _, _ = replay(events, monkeypatch)
    assert (t0 + DAYS31).date().isoformat() == "2026-02-01"
    assert store.spend_totals(AGENT, t0.date()) == (Decimal("0.40"), Decimal("0.40")), (
        "January's month total changed"
    )
    assert store.spend_totals(AGENT, (t0 + DAYS31).date()) == (Decimal("0.60"), Decimal("0.60")), (
        "January's spend carried into February's month total"
    )


def test_31_days_from_a_31_day_month_start_is_the_next_month_but_31_days_inside_march_is_not(
    monkeypatch,
):
    # 1 March + 30 d = 31 March (same month); + 31 d = 1 April (new month).
    t0 = utc(2026, 3, 1, 0, 0)
    events = [(t0, USD), (t0 + timedelta(days=30), USD), (t0 + DAYS31, USD)]
    _, store, _, _ = replay(events, monkeypatch)
    assert store.spend_totals(AGENT, t0.date()) == (USD, 2 * USD)
    assert store.spend_totals(AGENT, events[2][0].date()) == (USD, USD)


# --- the budgets follow the buckets: rollover at the boundary --------------------------------------------------------


def test_the_daily_budget_stops_at_the_cap_and_frees_at_utc_midnight(monkeypatch):
    t = utc(2026, 3, 10, 23, 54)
    limits, _, clock, _ = replay([(t, Decimal("1.00"))], monkeypatch, daily="1.00", monthly="100")
    assert limits.blocked(AGENT) == ["daily_budget"]
    clock.set(utc(2026, 3, 10, 23, 59, 59))
    assert limits.blocked(AGENT) == [
        "daily_budget"
    ]  # 6 minutes after the charge, still the same day
    clock.set(utc(2026, 3, 11, 0, 0, 0))
    assert limits.blocked(AGENT) == []  # the next day: a fresh bucket, the month still has room


def test_the_daily_budget_is_not_a_rolling_25_hour_window(monkeypatch):
    t = utc(2026, 3, 10, 0, 5)
    limits, _, clock, _ = replay([(t, Decimal("1.00"))], monkeypatch, daily="1.00", monthly="100")
    clock.set(t + timedelta(hours=23, minutes=54))  # 23:59 the same day
    assert limits.blocked(AGENT) == ["daily_budget"]
    clock.set(t + HOURS25)  # 11 March 01:05
    assert limits.blocked(AGENT) == []


def test_the_monthly_budget_stops_at_the_cap_and_frees_at_the_month_boundary(monkeypatch):
    events = [(utc(2026, 3, 1, 12, 0), Decimal("1.00")), (utc(2026, 3, 20, 12, 0), Decimal("1.00"))]
    limits, _, clock, _ = replay(events, monkeypatch, daily="100", monthly="2.00")
    clock.set(utc(2026, 3, 31, 23, 59, 59))
    assert limits.blocked(AGENT) == ["monthly_budget"]
    clock.set(utc(2026, 4, 1, 0, 0, 0))  # 31 days after 1 March 00:00
    assert limits.blocked(AGENT) == []


def test_a_charge_at_exactly_the_cap_blocks_the_next_call_and_one_cent_under_does_not(monkeypatch):
    t = utc(2026, 3, 10, 12, 0)
    limits, _, _, _ = replay([(t, Decimal("0.99"))], monkeypatch, daily="1.00", monthly="100")
    assert limits.blocked(AGENT) == []
    limits.charge(AGENT, Decimal("0.01"))
    assert limits.blocked(AGENT) == ["daily_budget"]


def test_one_agent_never_sees_another_agents_spend(monkeypatch):
    t = utc(2026, 3, 10, 12, 0)
    _, store, _, _ = replay([(t, USD)], monkeypatch)
    assert store.spend_totals("someone-else", t.date()) == (Decimal(0), Decimal(0)), (
        "spend_totals showed this agent's spend to another agent"
    )


def test_a_charge_returns_only_its_own_agents_month_total(monkeypatch):
    t = utc(2026, 3, 10, 12, 0)
    _, store, _, _ = replay([(t, USD)], monkeypatch)
    store.add_spend("someone-else", t.date(), Decimal(7))
    got = store.add_spend(AGENT, t.date(), USD)
    assert got == (2 * USD, 2 * USD), f"add_spend returned another agent's spend: {got}"
    got = store.add_spend(AGENT, (t + DAYS31).date(), USD)
    assert got == (USD, USD), f"a new month did not start empty: {got}"


def test_a_charge_returns_the_total_of_its_own_month_only(monkeypatch):
    check_a_charge_returns_the_total_of_its_own_month_only(MemoryStore(), monkeypatch)


def test_the_real_now_is_aware_utc_and_books_23_00_utc_on_the_10th_on_a_machine_in_ist(monkeypatch):
    check_real_now_buckets_by_utc_date_on_a_machine_in_ist(MemoryStore(), monkeypatch)


def test_one_microsecond_decides_the_day_and_a_leap_february_has_a_29th(monkeypatch):
    last = utc(2026, 3, 10, 23, 59, 59, 999999)
    first = last + timedelta(microseconds=1)
    leap = [(utc(2024, 2, 29, 23, 59, 59, 999999), USD), (utc(2024, 3, 1, 0, 0), USD)]
    events = [(last, USD), (first, USD), *leap]
    assert first == utc(2026, 3, 11, 0, 0) and leap[0][0] + timedelta(microseconds=1) == utc(
        2024, 3, 1
    )
    _, store, _, _ = replay(events, monkeypatch)
    assert store.spend_totals(AGENT, last.date()) == (USD, 2 * USD), "23:59:59.999999 left the 10th"
    assert store.spend_totals(AGENT, first.date()) == (USD, 2 * USD), "00:00:00 is not the 11th"
    assert store.spend_totals(AGENT, leap[0][0].date()) == (USD, USD), "29 Feb 2024 lost its charge"
    assert store.spend_totals(AGENT, leap[1][0].date()) == (USD, USD), "1 March 2024 shared 29 Feb"
