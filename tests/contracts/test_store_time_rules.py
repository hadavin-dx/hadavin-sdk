"""T2 on every store kind: the spend ledger's time rules by replay with a fake clock (no sleeping, no real time).

``tests/test_t2_ledger_replay.py`` proves the rules on the memory store. The production ledger is the postgres store,
which keeps its day and month totals a different way (two upsert counters, not a sum over days), so the same replay
runs here against every registered store kind (postgres is skipped without HADAVIN_TEST_PG_DSN, like the rest of the
store contract). Expected totals come from the oracle in the T2 file (each event bucketed by its own UTC date), never
from the code under test.
"""

from __future__ import annotations

from datetime import timedelta
from decimal import Decimal

import pytest

from tests.meter_support import AGENT, build_limits, utc
from tests.test_t2_ledger_replay import STARTS, WINDOWS, event_times, oracle

USD = Decimal("0.10")


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
