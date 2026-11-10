"""The spend ledger's time rules on every store kind, by replay with a fake clock (no sleeping, no real time).

Coupling: the mutant scripts (tests/meter_mutants.py, tests/postgres_mutants.py) name tests and message texts in this
file; renaming a test or rewording an assertion message here means changing the mutant that expects it.

What the ledger is (read, not assumed): UTC calendar buckets, one per (agent, day) and per (agent, month), keyed by
``now().date()`` at charge time. It is NOT a rolling window: a charge 6 minutes after another lands in the same
bucket only if no UTC midnight lies between them. The memory store sums over days; the production ledger, the
postgres store, keeps two upsert counters (day and month) instead, so every scenario runs against every registered
store kind (postgres is skipped without HADAVIN_TEST_PG_DSN; in CI a missing DSN is a failure, see
``tests/contracts/kinds/store_postgres.py``).

Expected totals come from ``oracle`` in ``tests/meter_support.py``, which buckets each (time, usd) event by its own
UTC date and (year, month), never by the code under test. "No double count" means: each charge appears once in its
day total and once in its month total, and reading (``blocked``, ``spend_totals``) never changes a total.

Each scenario is written once, here. The memory-store mutants (``tests/meter_mutants.py``) reach these tests through
``tests/meter_memory_killers.py``; the postgres mutants run them through ``tests/postgres_mutants.py``.
"""

from __future__ import annotations

from datetime import date, datetime, timedelta
from decimal import Decimal

import pytest

from hadavin_sdk.models import now
from tests.meter_support import (
    AGENT,
    DAYS31,
    HOURS25,
    IST,
    START,
    STARTS,
    USD,
    WINDOWS,
    build_limits,
    event_times,
    make_limits,
    oracle,
    set_machine_clock,
    utc,
)


@pytest.mark.parametrize("start", STARTS, ids=lambda s: s.isoformat())
@pytest.mark.parametrize("name,window", WINDOWS)
def test_replay_over_6_minutes_25_hours_and_31_days_matches_the_oracle(
    name, window, start, store, monkeypatch
):
    events = [(t, USD) for t in event_times(start, window)]
    limits, _, clock = build_limits("1000", "1000", events[0][0], monkeypatch, store=store)
    for i, (t, usd) in enumerate(events):
        clock.set(t)
        assert limits.charge(AGENT, usd) == oracle(events[: i + 1], t), f"{name}: charge {i} at {t}"
    for t, _ in events:  # a later read, and reads change nothing
        clock.set(t)
        limits.blocked(AGENT)
        assert store.spend_totals(AGENT, t.date()) == oracle(events, t), f"{name}: read at {t}"
        assert store.spend_totals(AGENT, t.date()) == oracle(events, t), (
            f"{name}: second read at {t}"
        )


@pytest.mark.parametrize("start", STARTS, ids=lambda s: s.isoformat())
def test_reads_never_change_a_total(start, store, monkeypatch):
    events = [(t, USD) for t in event_times(start, DAYS31)]
    limits, _, clock = build_limits("1000", "1000", events[0][0], monkeypatch, store=store)
    for t, usd in events:
        clock.set(t)
        limits.charge(AGENT, usd)
    before = {t.date(): store.spend_totals(AGENT, t.date()) for t, _ in events}
    for t, _ in events:
        clock.set(t)
        for _ in range(3):
            limits.blocked(AGENT)
            store.spend_totals(AGENT, t.date())
    after = {t.date(): store.spend_totals(AGENT, t.date()) for t, _ in events}
    assert after == before, "reads changed a total"


def test_two_charges_on_one_day_add_up(store, monkeypatch):
    limits, _, clock = build_limits("1000", "1000", START, monkeypatch, store=store)
    first = limits.charge(AGENT, Decimal("0.30"))
    assert first == (Decimal("0.30"), Decimal("0.30")), (
        f"the first charge of a day was not booked once: {first}"
    )
    clock.advance(timedelta(minutes=6))
    day, month = limits.charge(AGENT, Decimal("0.70"))
    assert day == Decimal("1.00"), f"the day total of two charges on one day did not add up: {day}"
    assert month == Decimal("1.00"), f"the month total of two charges did not add up: {month}"
    assert store.spend_totals(AGENT, START.date()) == (Decimal("1.00"), Decimal("1.00")), (
        "the stored totals are not the sum of both charges"
    )


def test_a_charge_at_23_30_utc_is_booked_on_its_own_day(store, monkeypatch):
    t = utc(2026, 3, 10, 23, 30)
    limits, _, _ = build_limits("1000", "1000", t, monkeypatch, store=store)
    limits.charge(AGENT, USD)
    assert store.spend_totals(AGENT, date(2026, 3, 10)) == (USD, USD), (
        "a charge at 23:30 UTC is not on its own UTC day"
    )
    assert store.spend_totals(AGENT, date(2026, 3, 11)) == (Decimal(0), USD), (
        "a charge at 23:30 UTC leaked into the next day"
    )


def test_a_day_total_is_the_sum_of_its_own_charges_only_across_25_hours(store, monkeypatch):
    t0 = utc(2026, 3, 10, 0, 30)
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("0.30"))
    clock.set(t0 + HOURS25)  # 11 March 01:30
    limits.charge(AGENT, Decimal("0.70"))
    assert store.spend_totals(AGENT, t0.date()) == (Decimal("0.30"), Decimal("1.00"))
    assert store.spend_totals(AGENT, (t0 + HOURS25).date()) == (Decimal("0.70"), Decimal("1.00"))


def test_a_month_total_does_not_carry_over_31_days(store, monkeypatch):
    t0 = utc(2026, 1, 1, 0, 0)
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("0.40"))
    clock.set(t0 + DAYS31)  # 1 February 00:00
    limits.charge(AGENT, Decimal("0.60"))
    assert (t0 + DAYS31).date().isoformat() == "2026-02-01"
    assert store.spend_totals(AGENT, t0.date()) == (Decimal("0.40"), Decimal("0.40")), (
        "January's month total changed"
    )
    assert store.spend_totals(AGENT, (t0 + DAYS31).date()) == (Decimal("0.60"), Decimal("0.60")), (
        "January's spend carried into February's month total"
    )


def test_31_days_from_the_start_of_a_31_day_month_is_the_next_month_but_30_days_is_not(
    store, monkeypatch
):
    # 1 March + 30 d = 31 March (same month); + 31 d = 1 April (new month).
    t0 = utc(2026, 3, 1, 0, 0)
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    for t in (t0, t0 + timedelta(days=30), t0 + DAYS31):
        clock.set(t)
        limits.charge(AGENT, USD)
    assert store.spend_totals(AGENT, t0.date()) == (USD, 2 * USD)
    assert store.spend_totals(AGENT, (t0 + DAYS31).date()) == (USD, USD)


def test_the_same_month_of_another_year_is_a_different_month(store, monkeypatch):
    """One year plus one minute, and 24 months, after the first charge: March 2025, March 2026, March 2027. A month
    key without the year would add all three March totals together."""
    t0 = utc(2025, 3, 10, 12, 0)
    later = [utc(2026, 3, 10, 12, 1), utc(2027, 3, 10, 12, 0)]
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    assert limits.charge(AGENT, USD) == (USD, USD)
    for t in later:
        clock.set(t)
        got = limits.charge(AGENT, USD)
        assert got == (USD, USD), (
            f"a March of another year was added to the March of {t.year}: {got}"
        )
    for t in (t0, *later):
        assert store.spend_totals(AGENT, t.date()) == (USD, USD), (
            f"the March totals of other years leaked into {t.year}"
        )


def test_a_charge_on_a_past_date_is_booked_on_that_date(store, monkeypatch):
    """The store takes the date from the caller: nothing is read from the database server's own clock
    (``CURRENT_DATE``, ``NOW()``), which the fake clock cannot move. A date long past proves it."""
    t = utc(2001, 9, 9, 1, 46, 40)
    limits, _, _ = build_limits("1000", "1000", t, monkeypatch, store=store)
    assert limits.charge(AGENT, USD) == (USD, USD)
    assert store.spend_totals(AGENT, date(2001, 9, 9)) == (USD, USD), (
        "a charge on a past date is not on that date"
    )
    assert store.spend_totals(AGENT, date(2001, 9, 10)) == (Decimal(0), USD)


def test_a_charge_smaller_than_a_cent_is_neither_rounded_nor_lost(store, monkeypatch):
    """The ledger keeps exact decimals (numeric, no fixed scale): 0.0000001 is held as 0.0000001, not 0.00."""
    tiny = Decimal("0.0000001")
    limits, _, _ = build_limits("1000", "1000", START, monkeypatch, store=store)
    assert limits.charge(AGENT, tiny) == (tiny, tiny), "the first tiny charge was rounded"
    got = limits.charge(AGENT, tiny)
    assert got == (2 * tiny, 2 * tiny), f"tiny charges were rounded when added: {got}"
    assert store.spend_totals(AGENT, START.date()) == (2 * tiny, 2 * tiny), (
        "the stored total of tiny charges was rounded"
    )


def test_the_order_the_events_arrive_in_does_not_change_the_totals(store, monkeypatch):
    """A replay in any order (late arrivals, a clock that steps back) gives the same day and month totals."""
    t0 = utc(2026, 3, 30, 23, 0)
    events = [(t0 + timedelta(minutes=6 * k * 37), Decimal(k + 1) / 100) for k in range(60)]
    shuffled = [
        events[(k * 7) % 60] for k in range(60)
    ]  # 7 is coprime to 60: every event once, scrambled
    assert sorted(shuffled) == events and shuffled != events
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    for t, usd in shuffled:
        clock.set(t)
        limits.charge(AGENT, usd)
    for t, _ in events:
        assert store.spend_totals(AGENT, t.date()) == oracle(events, t), f"read at {t}"


def test_a_charge_every_6_minutes_for_two_days_blocks_and_frees_the_daily_budget_exactly(
    store, monkeypatch
):
    """240 charges of 0.01 fill a 2.40 daily budget exactly at 23:54; the next UTC day starts empty; month keeps both."""
    t0 = utc(2026, 3, 10, 0, 0)
    limits, _, clock = build_limits("2.40", "100", t0, monkeypatch, store=store)
    events = []
    for k in range(480):  # 2 days at one charge per 6 minutes
        t = t0 + timedelta(minutes=6 * k)
        clock.set(t)
        if t.hour == 0 and t.minute == 0:
            assert limits.blocked(AGENT) == [], f"a fresh day must start free at {t}"
        events.append((t, Decimal("0.01")))
        limits.charge(AGENT, Decimal("0.01"))
        daily_full = oracle(events, t)[0] >= Decimal("2.40")
        assert limits.blocked(AGENT) == (["daily_budget"] if daily_full else []), f"at {t}"
    assert store.spend_totals(AGENT, t0.date()) == (Decimal("2.40"), Decimal("4.80"))
    assert store.spend_totals(AGENT, (t0 + timedelta(days=1)).date()) == (
        Decimal("2.40"),
        Decimal("4.80"),
    )


def test_31_days_of_daily_charges_never_leak_across_the_month_boundary(store, monkeypatch):
    """One charge a day from 15 March for 31 days: March holds 17, April holds 14; both stay separate."""
    t0 = utc(2026, 3, 15, 8, 0)
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    events = [(t0 + timedelta(days=k), USD) for k in range(31)]
    for t, usd in events:
        clock.set(t)
        limits.charge(AGENT, usd)
    assert store.spend_totals(AGENT, utc(2026, 3, 31).date()) == (USD, 17 * USD)
    assert store.spend_totals(AGENT, utc(2026, 4, 1).date()) == (USD, 14 * USD)
    assert store.spend_totals(AGENT, utc(2026, 5, 1).date()) == (Decimal(0), Decimal(0))


# --- the budgets follow the buckets: rollover at the boundary --------------------------------------------------------


def test_the_daily_budget_frees_at_utc_midnight_and_is_not_a_rolling_25_hour_window(
    store, monkeypatch
):
    t = utc(2026, 3, 10, 0, 5)
    limits, _, clock = build_limits("1.00", "100", t, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("1.00"))
    clock.set(utc(2026, 3, 10, 23, 59, 59))
    assert limits.blocked(AGENT) == ["daily_budget"]  # 23 h 54 min later, the same UTC day
    clock.set(utc(2026, 3, 11, 0, 0))
    assert limits.blocked(AGENT) == [], "the next UTC day did not start free"
    clock.set(t + HOURS25)
    assert limits.blocked(AGENT) == []


def test_the_monthly_budget_stops_at_the_cap_and_frees_at_the_month_boundary(store, monkeypatch):
    t0 = utc(2026, 3, 1, 12, 0)
    limits, _, clock = build_limits("100", "2.00", t0, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("1.00"))
    clock.set(utc(2026, 3, 20, 12, 0))
    limits.charge(AGENT, Decimal("1.00"))
    for t in (utc(2026, 3, 20, 12, 0), utc(2026, 3, 31, 23, 59, 59, 999999)):
        clock.set(t)
        assert limits.blocked(AGENT) == ["monthly_budget"], f"not blocked at {t}"
    clock.set(utc(2026, 4, 1, 0, 0))  # the month total restarts; the day total was never full
    assert limits.blocked(AGENT) == [], "April started with March's month total"
    clock.set(utc(2026, 3, 31, 23, 59))  # reading an earlier instant again changes nothing
    assert limits.blocked(AGENT) == ["monthly_budget"]


def test_the_monthly_budget_frees_on_1_march_after_a_28_day_february(store, monkeypatch):
    t0 = utc(2026, 2, 1, 0, 0)
    limits, _, clock = build_limits("100", "1.00", t0, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("1.00"))
    for t, blocked in [
        (utc(2026, 2, 28, 23, 59, 59, 999999), ["monthly_budget"]),
        (utc(2026, 3, 1, 0, 0), []),  # 28 days after 1 February 00:00 (not 31)
    ]:
        clock.set(t)
        assert limits.blocked(AGENT) == blocked, f"at {t}"


def test_a_charge_at_exactly_the_cap_blocks_the_next_call_and_one_cent_under_does_not(
    store, monkeypatch
):
    limits, _, _ = build_limits("1.00", "100", START, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("0.99"))
    assert limits.blocked(AGENT) == []
    limits.charge(AGENT, Decimal("0.01"))
    assert limits.blocked(AGENT) == ["daily_budget"]


def test_the_daily_budget_is_read_for_today_not_yesterday(store, monkeypatch):
    t = utc(2026, 3, 10, 23, 54)
    limits, _, clock = build_limits("1.00", "100", t, monkeypatch, store=store)
    limits.charge(AGENT, Decimal("1.00"))
    assert limits.blocked(AGENT) == ["daily_budget"], "today's full budget was not read"
    clock.set(utc(2026, 3, 11, 0, 0, 0))
    assert limits.blocked(AGENT) == [], "yesterday's full budget was read as today's"


# --- agents are separate ledgers -----------------------------------------------------------------------------------


def test_one_agent_never_sees_another_agents_spend(store, monkeypatch):
    t = utc(2026, 3, 10, 12, 0)
    limits, _, _ = build_limits("1000", "1000", t, monkeypatch, store=store)
    limits.charge(AGENT, USD)
    assert store.spend_totals("someone-else", t.date()) == (Decimal(0), Decimal(0)), (
        "spend_totals showed this agent's spend to another agent"
    )
    store.add_spend("someone-else", t.date(), Decimal(7))
    assert store.spend_totals(AGENT, t.date()) == (USD, USD), "another agent's spend leaked in"
    assert store.spend_totals("someone-else", t.date()) == (Decimal(7), Decimal(7))


def test_a_charge_returns_only_its_own_agents_month_total(store, monkeypatch):
    t = utc(2026, 3, 10, 12, 0)
    limits, _, _ = build_limits("1000", "1000", t, monkeypatch, store=store)
    limits.charge(AGENT, USD)
    store.add_spend("someone-else", t.date(), Decimal(7))
    got = store.add_spend(AGENT, t.date(), USD)
    assert got == (2 * USD, 2 * USD), f"add_spend returned another agent's spend: {got}"
    got = store.add_spend(AGENT, (t + DAYS31).date(), USD)
    assert got == (USD, USD), f"a new month did not start empty: {got}"


def test_a_charge_returns_the_total_of_its_own_month_only(store, monkeypatch):
    """Charges on 31 January, 1 February and 2 February: the ones in February return a month total of February alone."""
    t0 = utc(2026, 1, 31, 12, 0)
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    unit = Decimal("0.10")
    want = [(unit, unit), (unit, unit), (unit, 2 * unit)]  # day, month: the month restarts on 1 Feb
    for k, t in enumerate([t0, t0 + timedelta(days=1), t0 + timedelta(days=2)]):
        clock.set(t)
        got = limits.charge(AGENT, unit)
        assert got == want[k], f"charge {k} at {t.date().isoformat()} returned {got}, not {want[k]}"


# --- the real now() and the instants on either side of midnight ---------------------------------------------------------


def test_the_real_now_is_aware_utc_and_books_23_00_utc_on_the_10th_on_a_machine_in_ist(
    store, monkeypatch
):
    """The real ``now()`` is aware UTC; a charge at 23:00 UTC on 10 March (04:30 on the 11th in IST) is booked on the
    10th, and the first instant of the 11th UTC (05:30 IST) on the 11th. Expected dates are written out by hand."""
    limits = make_limits(
        "1000", "1000", store
    )  # the real ``hadavin_sdk.limits.now``: nothing patched there
    unit = Decimal("0.25")
    set_machine_clock(monkeypatch, datetime(2026, 3, 11, 4, 30, tzinfo=IST))  # = 10 March 23:00 UTC
    got = now()
    assert got.tzinfo is not None and got.utcoffset() == timedelta(0), (
        f"now() is not aware UTC: {got!r}"
    )
    assert got == utc(2026, 3, 10, 23, 0), f"now() is the wrong instant: {got!r}"
    assert limits.charge(AGENT, unit) == (unit, unit)
    assert store.spend_totals(AGENT, date(2026, 3, 10)) == (unit, unit), (
        "23:00 UTC is not on the 10th"
    )
    assert store.spend_totals(AGENT, date(2026, 3, 11)) == (Decimal(0), unit), (
        "23:00 UTC landed on the 11th"
    )
    set_machine_clock(monkeypatch, datetime(2026, 3, 11, 5, 30, tzinfo=IST))  # = 11 March 00:00 UTC
    assert limits.charge(AGENT, unit) == (unit, 2 * unit)
    assert store.spend_totals(AGENT, date(2026, 3, 11)) == (unit, 2 * unit), (
        "00:00 UTC is not on the 11th"
    )


def test_one_microsecond_decides_the_day_and_a_leap_february_has_a_29th(store, monkeypatch):
    last = utc(2026, 3, 10, 23, 59, 59, 999999)
    leap = utc(2024, 2, 29, 23, 59, 59, 999999)
    limits, _, clock = build_limits("1000", "1000", last, monkeypatch, store=store)
    for t in (last, last + timedelta(microseconds=1), leap, leap + timedelta(microseconds=1)):
        clock.set(t)
        limits.charge(AGENT, USD)
    assert store.spend_totals(AGENT, utc(2026, 3, 10).date()) == (USD, 2 * USD), (
        "the 10th lost 23:59:59.999999"
    )
    assert store.spend_totals(AGENT, utc(2026, 3, 11).date()) == (USD, 2 * USD), (
        "00:00:00 is not the 11th"
    )
    assert store.spend_totals(AGENT, utc(2024, 2, 29).date()) == (USD, USD), (
        "29 Feb 2024 lost its charge"
    )
    assert store.spend_totals(AGENT, utc(2024, 3, 1).date()) == (USD, USD), (
        "1 March 2024 shared 29 Feb"
    )
