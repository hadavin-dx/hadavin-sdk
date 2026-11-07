"""Harness for the money-meter tests T1 and T2: a fake clock for ``hadavin_sdk.limits.now`` and a Limits built over
a MemoryStore with a stub registry. No network, no model call, no real time.

The code under test is the real ``Limits`` (``charge`` = spend after, ``blocked`` = check before) and the real
``MemoryStore`` spend ledger (``add_spend`` / ``spend_totals``). Nothing here is a second meter.
"""

from __future__ import annotations

import threading
from collections.abc import Callable
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from hadavin_sdk.limits import Limits
from hadavin_sdk.registry import Budget
from hadavin_sdk.store.memory import MemoryStore

AGENT = "meter-agent"
CALLERS = 50
W = Decimal("1.00")  # worst-case cost of one call
START = datetime(2026, 3, 10, 12, 0, tzinfo=UTC)
HUGE = "100000"  # the monthly budget, out of the way
WAIT_S = 10.0  # a bound on every wait: a broken schedule fails, it never hangs


class NoAudit:
    """Limits.blocked and Limits.charge never write audit; stop and reset (not used here) would."""


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


def build_limits(
    daily: str, monthly: str, start: datetime, monkeypatch: pytest.MonkeyPatch
) -> tuple[Limits, MemoryStore, FakeClock]:
    clock = FakeClock(start)
    monkeypatch.setattr("hadavin_sdk.limits.now", clock)
    store = MemoryStore()
    agent = SimpleNamespace(budget_usd=Budget(daily=Decimal(daily), monthly=Decimal(monthly)))
    registry = SimpleNamespace(agents={AGENT: agent})
    return Limits(store, NoAudit(), registry), store, clock  # type: ignore[arg-type]


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
