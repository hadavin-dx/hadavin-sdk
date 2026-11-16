"""Harness for the money-meter tests T1 (the cap) and T2 (the ledger's time rules): a fake clock for
``hadavin_sdk.limits.now``, a Limits built over any store kind, a money oracle, and a parallel-caller schedule.
No network, no model call, no real time.

The code under test is the real ``Limits`` (``charge`` = spend after, ``blocked`` = check before) and the real spend
ledger of each store kind (``add_spend`` / ``spend_totals``). Nothing here is a second meter.

Plan: handover/PARALLEL-PLAN-2026-11-10.md, rows A21a (these tests) and A21b (the 50-parallel run on the Meter).
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import SimpleNamespace
from typing import Self, cast

import pytest

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.registry import AgentRecord, Budget, Registry
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import Store

AGENT = "meter-agent"
CALLERS = 50
W = Decimal("1.00")  # worst-case cost of one call
START = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
HUGE = "100000"  # the monthly budget, out of the way
WAIT_S = 10.0  # a bound on every wait: a broken schedule fails, it never hangs
USD = Decimal("0.10")  # a small charge for the time-rule replays


class NoAudit:
    """An audit sink for code that must not write audit: Limits.blocked and Limits.charge never do (stop and reset,
    not used here, would). Every method fails the test that reaches it, so a stray audit write cannot go unseen."""

    def write_intent(self, event: AuditEvent) -> str:
        raise AssertionError("the meter wrote an audit intent event")

    def write_outcome(self, event: AuditEvent) -> str | None:
        raise AssertionError("the meter wrote an audit outcome event")

    def reconcile(self) -> int:
        raise AssertionError("the meter reconciled the audit outbox")

    def verify_object(self, key: str) -> bool:
        raise AssertionError("the meter verified an audit object")

    def events(self, run_id: str | None = None) -> list[AuditEvent]:
        raise AssertionError("the meter read audit events")


@dataclass
class FakeClock:
    """Stands in for ``hadavin_sdk.limits.now`` and can be set or advanced. The small ``Clock`` classes in
    tests/test_cuj.py and tests/test_s6_approvals.py only return a fixed time; the meter tests move time, so this
    one has ``set`` and ``advance`` (a superset)."""

    t: datetime

    def __call__(self) -> datetime:
        return self.t

    def set(self, t: datetime) -> None:
        self.t = t

    def advance(self, delta: timedelta) -> None:
        self.t += delta


def utc(*args: int) -> datetime:
    return datetime(*args, tzinfo=UTC)


def make_limits(daily: str, monthly: str, store: Store) -> Limits:
    """The real Limits over ``store``. ``Limits`` reads one thing from the registry, ``agents[AGENT].budget_usd``.
    A real ``Registry`` is built only by ``registry.load`` from a whole config folder (config file, principals,
    chains, contracts, prompt files), which has nothing to do with money, so the registry here is a minimal
    stand-in that holds one real ``AgentRecord``; the ``cast`` says exactly that and nothing else is faked."""
    agent = AgentRecord(
        id=AGENT,
        status="live",
        data_class="internal",
        model_route="unused",
        prompt_file="unused",
        scope_allowed=[],
        max_steps=1,
        budget_usd=Budget(daily=Decimal(daily), monthly=Decimal(monthly)),
    )
    registry = cast(Registry, SimpleNamespace(agents={AGENT: agent}))
    audit: AuditSink = NoAudit()
    return Limits(store, audit, registry)


def build_limits(
    daily: str,
    monthly: str,
    start: datetime,
    monkeypatch: pytest.MonkeyPatch,
    store: Store | None = None,
) -> tuple[Limits, Store, FakeClock]:
    """``store`` is any Store kind (the contract suite passes each registered one); the default is a MemoryStore.
    The clock is fake: the Postgres server's own ``NOW()`` is never asked (the store takes the date from the
    caller), and a test pins that by charging on a date long past."""
    clock = FakeClock(start)
    monkeypatch.setattr("hadavin_sdk.limits.now", clock)
    store = MemoryStore() if store is None else store
    return make_limits(daily, monthly, store), store, clock


# --- the parallel schedule: a caller is a (reserve, settle) pair ----------------------------------------------------

Reserve = Callable[[], bool]  # before the provider call: may this call go ahead? True = admitted
Settle = Callable[[], None]  # after the provider answered: book the real cost of an admitted call


def check_then_charge(limits: Limits) -> tuple[Reserve, Settle]:
    """The way agent_loop uses the meter today: reserve = ask ``blocked``; settle = ``charge`` the cost W."""

    def reserve() -> bool:
        return not limits.blocked(AGENT)

    def settle() -> None:
        limits.charge(AGENT, W)

    return reserve, settle


class Schedule:
    """Forces the worst interleaving: no caller settles until every caller has been through ``reserve``."""

    def __init__(self, n: int) -> None:
        self.n, self.decided = n, 0
        self.cond = threading.Condition()

    def decided_and_wait(self) -> None:
        with self.cond:
            self.decided += 1
            self.cond.notify_all()
            self.cond.wait_for(lambda: self.decided >= self.n, timeout=WAIT_S)


def run_parallel(reserve: Reserve, settle: Settle, n: int = CALLERS) -> int:
    """n threads: reserve? -> (every caller has decided) -> stub provider call -> settle. Returns how many were
    admitted. ``run_parallel`` itself never charges: a meter that books at reserve time (a choke-point fix) is
    therefore not charged twice, and a meter that books only at settle time shows its race."""
    sched = Schedule(n)
    start = threading.Barrier(n, timeout=WAIT_S)
    admitted: list[bool] = []
    lock = threading.Lock()

    def caller() -> None:
        start.wait()
        ok = reserve()
        sched.decided_and_wait()  # the stub provider answers only after every check is done
        if ok:
            settle()
        with lock:
            admitted.append(ok)

    threads = [threading.Thread(target=caller) for _ in range(n)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(WAIT_S * 2)
        assert not t.is_alive(), "a caller hung: the schedule is broken"
    assert len(admitted) == n
    return sum(admitted)


# --- the real ``now()`` over a fake machine clock ---------------------------------------------------------------------

IST = timezone(timedelta(hours=5, minutes=30))  # a machine whose local zone is NOT UTC


class MachineClock(datetime):
    """Stands in for ``datetime`` inside ``hadavin_sdk.models`` so the REAL ``now()`` runs: like the real
    ``datetime.now``, ``now(tz)`` gives the instant in ``tz`` and ``now()`` gives the machine's local wall clock
    (naive, in ``local``). No real time is read."""

    instant: datetime = START
    local: tzinfo = IST

    @classmethod
    def now(cls, tz: tzinfo | None = None) -> Self:
        if tz is None:
            return cls.fromisoformat(
                cls.instant.astimezone(cls.local).replace(tzinfo=None).isoformat()
            )
        return cls.fromisoformat(cls.instant.astimezone(tz).isoformat())


def set_machine_clock(monkeypatch: pytest.MonkeyPatch, instant: datetime) -> None:
    monkeypatch.setattr(MachineClock, "instant", instant)
    monkeypatch.setattr("hadavin_sdk.models.datetime", MachineClock)


# --- the money oracle and the time-rule scenarios (T2) ------------------------------------------------------------------

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
    """(day total, month total) of the events, bucketed by their own UTC date and (year, month). Never the code
    under test."""
    here = now.astimezone(UTC)  # an aware time in any zone is bucketed by its UTC calendar date
    utc_events = [(t.astimezone(UTC), u) for t, u in events]
    day = sum((u for t, u in utc_events if t.date() == here.date()), Decimal(0))
    month = sum(
        (u for t, u in utc_events if (t.year, t.month) == (here.year, here.month)), Decimal(0)
    )
    return day, month


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
