"""Harness for the money-meter tests T1 and T2: a fake clock for ``hadavin_sdk.limits.now`` and a Limits built over
a MemoryStore with a stub registry. No network, no model call, no real time.

The code under test is the real ``Limits`` (``charge`` = spend after, ``blocked`` = check before) and the real
``MemoryStore`` spend ledger (``add_spend`` / ``spend_totals``). Nothing here is a second meter.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, date, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from types import SimpleNamespace
from typing import Self, cast

import pytest

from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.limits import Limits
from hadavin_sdk.models import AuditEvent
from hadavin_sdk.registry import Budget, Registry
from hadavin_sdk.store.memory import MemoryStore
from hadavin_sdk.store.protocol import Store

AGENT = "meter-agent"
CALLERS = 50
W = Decimal("1.00")  # worst-case cost of one call
START = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
HUGE = "100000"  # the monthly budget, out of the way
WAIT_S = 10.0  # a bound on every wait: a broken schedule fails, it never hangs


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
    """The real Limits over ``store`` and a one-agent stub registry (only ``agents[AGENT].budget_usd`` is read)."""
    agent = SimpleNamespace(budget_usd=Budget(daily=Decimal(daily), monthly=Decimal(monthly)))
    registry = cast(Registry, SimpleNamespace(agents={AGENT: agent}))
    return Limits(store, cast(AuditSink, NoAudit()), registry)


def build_limits(
    daily: str,
    monthly: str,
    start: datetime,
    monkeypatch: pytest.MonkeyPatch,
    store: Store | None = None,
) -> tuple[Limits, Store, FakeClock]:
    """``store`` is any Store kind (the contract suite passes each registered one); the default is a MemoryStore."""
    clock = FakeClock(start)
    monkeypatch.setattr("hadavin_sdk.limits.now", clock)
    store = MemoryStore() if store is None else store
    return make_limits(daily, monthly, store), store, clock


def admit_check_then_charge(limits: Limits) -> bool:
    """The way agent_loop uses the meter: ask ``blocked``, make the call, ``charge`` the cost."""
    return not limits.blocked(AGENT)


class Schedule:
    """Forces the worst interleaving: no caller charges until every caller has been through the check."""

    def __init__(self, n: int) -> None:
        self.n, self.decided = n, 0
        self.cond = threading.Condition()

    def decided_and_wait(self) -> None:
        with self.cond:
            self.decided += 1
            self.cond.notify_all()
            self.cond.wait_for(lambda: self.decided >= self.n, timeout=WAIT_S)


def run_parallel(limits: Limits, admit: Callable[[Limits], bool], n: int = CALLERS) -> int:
    """n threads: admit? -> (decide) -> provider call -> charge W. Returns how many were admitted."""
    sched = Schedule(n)
    start = threading.Barrier(n, timeout=WAIT_S)
    admitted: list[bool] = []
    lock = threading.Lock()

    def caller() -> None:
        start.wait()
        ok = admit(limits)
        sched.decided_and_wait()  # the stub provider answers only after every check is done
        if ok:
            limits.charge(AGENT, W)
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


# --- the real ``now()`` over a fake machine clock, and scenarios shared by the memory and every-store tests -------------

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


def check_real_now_buckets_by_utc_date_on_a_machine_in_ist(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The real ``now()`` is aware UTC; a charge at 23:00 UTC on 10 March (04:30 on the 11th in IST) is booked on the
    10th, and the first instant of the 11th UTC (05:30 IST) on the 11th. Expected dates are written out by hand."""
    from hadavin_sdk.models import now

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


def check_a_charge_returns_the_total_of_its_own_month_only(
    store: Store, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Charges on 31 January and 1 February: the one on 1 February returns a month total of that month alone."""
    t0 = utc(2026, 1, 31, 12, 0)
    limits, _, clock = build_limits("1000", "1000", t0, monkeypatch, store=store)
    unit = Decimal("0.10")
    for k, t in enumerate(
        [t0, t0 + timedelta(days=1), t0 + timedelta(days=2)]
    ):  # 31 Jan, 1 Feb, 2 Feb
        clock.set(t)
        got = limits.charge(AGENT, unit)
        want = [(unit, unit), (unit, unit), (unit, 2 * unit)][
            k
        ]  # day, month: the month restarts on 1 Feb
        assert got == want, f"charge {k} at {t.date().isoformat()} returned {got}, not {want}"
