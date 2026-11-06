"""Helpers for the meter tests: a store wrapper that records calls and raises on demand, a fake clock and run maker."""

from collections import defaultdict
from datetime import UTC, datetime, timedelta

from hadavin_sdk.meter import Caps, Meter
from hadavin_sdk.models import Run
from hadavin_sdk.store.memory import MemoryStore

NO_CAPS = Caps(day=None, month=None, run=None)


class ScriptedStore:
    """Wraps a real `MemoryStore`. `raises[method]` is a list of exceptions raised by the next calls of that method
    (one per call, before the real method runs); `after[method]` is the same but raised AFTER the real method ran
    (a committed write whose answer was lost). `calls` lists (method, args) of every call."""

    def __init__(self, inner=None):
        self._inner = inner or MemoryStore()
        self.raises: dict[str, list[BaseException]] = defaultdict(list)
        self.after: dict[str, list[BaseException]] = defaultdict(list)
        self.calls: list[tuple[str, tuple]] = []

    def count(self, method):
        return sum(1 for m, _ in self.calls if m == method)

    def __getattr__(self, name):
        attr = getattr(self._inner, name)
        if name.startswith("_") or not callable(attr):
            return attr

        def call(*args, **kwargs):
            self.calls.append((name, args))
            if self.raises[name]:
                raise self.raises[name].pop(0)
            result = attr(*args, **kwargs)
            if self.after[name]:
                raise self.after[name].pop(0)
            return result

        return call


class FakeMono:
    def __init__(self):
        self.t = 1000.0

    def __call__(self):
        return self.t


def make_run(store, agent="ag"):
    run = Run(agent_id=agent, principal_id="p", trigger_kind="event", trigger_ref="t")
    store.create_run(run)
    return run


def utc(y, m, d, hh=0, mm=0, ss=0):
    return datetime(y, m, d, hh, mm, ss, tzinfo=UTC)


def fixed_clock(stamp):
    return lambda: stamp


class StepClock:
    """A wall clock for `MemoryStore(clock=...)` that moves only when told."""

    def __init__(self):
        self.stamp = datetime.now(UTC)

    def __call__(self):
        return self.stamp

    def advance(self, seconds):
        self.stamp = self.stamp + timedelta(seconds=seconds)


def new_meter(store=None, **kw):
    store = store or ScriptedStore()
    return store, Meter(store, **kw)
