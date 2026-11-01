"""Read-only shared configuration and an effect barrier (a stop gate every port goes through).

ACCIDENT-PROOFING, NOT A SANDBOX. ``freeze`` returns a deep copy whose dicts, lists and sets refuse every mutation
through Python's normal interface, so a caller cannot edit a policy or a directory by accident (or by a careless
helper). Code that deliberately calls ``dict.__setitem__(d, ...)`` on a frozen dict still reaches the C slot; a
root of trust that must resist a hostile in-process caller lives in a signed document outside the process.
``copy.deepcopy`` of a frozen value returns a plain, editable copy BY DESIGN (that is how a change is prepared).

``ConfigHolder`` keeps the policy and the directory in ONE immutable ``ConfigView`` replaced as a whole, so a reader
that takes ``holder.view()`` never sees a new policy with an old directory. ``holder.lock`` serialises config
changes and decisions; never hold it across I/O.

``StopGate`` is the in-process effect barrier. It is NOT ``hadavin_sdk.models.KillSwitch`` (the store-backed, durable
switch). Given a store, ``engage`` writes the durable switch FIRST and ``blocked()`` also reads it, so a second
process or a second gate instance sees the same state. Every outbound effect runs inside ``with gate.effect():`` which
(under a short condition lock, never held during the effect) refuses when the gate is engaged and otherwise counts the
effect as in flight; ``engage`` sets the flag and then waits, with a timeout, for the in-flight effects to finish before
it sweeps. A port that only calls ``blocked()`` before acting has a check-then-act race: use ``effect()``.
Cross-process safety of a particular effect (a conditional write in the target system) is the effect's own job.

Synchronous primitives (``threading``). Async callers run the blocking calls with ``asyncio.to_thread``.
Lock order: ``holder.lock`` before any store or audit lock; ``StopGate`` takes no ``holder.lock``.
"""

from __future__ import annotations

import re
import threading
from collections.abc import Callable, Iterable
from contextlib import contextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol

_LEAF = (str, int, float, bool, type(None), bytes, frozenset)


def _refuse(self: object, *a: object, **k: object) -> None:
    raise TypeError("read-only configuration: change it only through the holder's swap")


class FrozenDict(dict):
    __slots__ = ("_sealed",)

    def __init__(self, data: Any = ()) -> None:
        if getattr(self, "_sealed", False):
            _refuse(self)  # `d.__init__(...)` on a built value is an in-place edit
        dict.__init__(self, data)
        object.__setattr__(self, "_sealed", True)

    __setitem__ = __delitem__ = update = pop = popitem = clear = setdefault = __ior__ = _refuse  # type: ignore[assignment]

    def __reduce__(self) -> tuple[Any, ...]:
        return (FrozenDict, (dict(self),))

    def __deepcopy__(self, memo: dict) -> Any:
        return thaw(self)


class FrozenList(list):
    __slots__ = ("_sealed",)

    def __init__(self, data: Any = ()) -> None:
        if getattr(self, "_sealed", False):
            _refuse(self)
        list.__init__(self, data)
        object.__setattr__(self, "_sealed", True)

    __setitem__ = __delitem__ = append = extend = insert = remove = pop = clear = _refuse  # type: ignore[assignment]
    sort = reverse = __iadd__ = __imul__ = _refuse  # type: ignore[assignment]

    def __reduce__(self) -> tuple[Any, ...]:
        return (FrozenList, (list(self),))

    def __deepcopy__(self, memo: dict) -> Any:
        return thaw(self)


def freeze(o: Any) -> Any:
    """A deep frozen copy; nothing in the result is shared with ``o``. dict -> FrozenDict, list/tuple -> FrozenList,
    set -> frozenset. Any other mutable or unknown type raises ``TypeError`` (it could be edited in place)."""
    if isinstance(o, dict):
        d = FrozenDict.__new__(FrozenDict)
        dict.__init__(d, {k: freeze(v) for k, v in o.items()})
        object.__setattr__(d, "_sealed", True)
        return d
    if isinstance(o, (list, tuple)):
        lst = FrozenList.__new__(FrozenList)
        list.__init__(lst, [freeze(v) for v in o])
        object.__setattr__(lst, "_sealed", True)
        return lst
    if isinstance(o, (set, frozenset)):
        return frozenset(freeze(v) for v in o)
    if isinstance(o, _LEAF):
        return o
    raise TypeError(f"cannot freeze a {type(o).__name__}: only JSON-shaped values and sets")


def thaw(o: Any) -> Any:
    """A deep plain (mutable) copy of a frozen or plain structure."""
    if isinstance(o, dict):
        return {k: thaw(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [thaw(v) for v in o]
    if isinstance(o, (set, frozenset)):
        return {thaw(v) for v in o}
    return o


@dataclass(frozen=True)
class ConfigView:
    """One immutable policy + directory pair; ``version`` counts swaps."""

    pol: Any
    directory: Any
    version: int = 0


class ConfigHolder:
    def __init__(self, pol: dict, directory: dict | None = None) -> None:
        self._view = ConfigView(freeze(pol), None if directory is None else freeze(directory))
        self.lock = threading.RLock()

    def view(self) -> ConfigView:
        return self._view  # one attribute read: the pair is consistent

    @property
    def pol(self) -> Any:
        return self._view.pol

    @property
    def directory(self) -> Any:
        return self._view.directory

    def swap(self, pol: dict, directory: dict) -> ConfigView:
        """Replace policy and directory together. Freezing happens before the lock is taken."""
        new_pol, new_dir = freeze(pol), freeze(directory)
        with self.lock:
            self._view = ConfigView(new_pol, new_dir, self._view.version + 1)
            return self._view


class KillSwitchStore(Protocol):
    """The durable switch (``hadavin_sdk.store`` implements these two methods)."""

    def get_kill_switch(self) -> Any: ...
    def set_kill_switch(self, ks: Any) -> None: ...


class EffectBlocked(RuntimeError):
    """The stop gate is engaged: no outbound effect may start."""


@dataclass
class EngageResult:
    results: list[tuple[str, str]] = field(default_factory=list)
    complete: bool = (
        True  # False: the wait for in-flight effects timed out, or the sweep was interrupted
    )
    in_flight_at_timeout: int = 0


_LABEL = re.compile(r"[A-Za-z0-9_.:@-]{1,60}")


def _label(who: object) -> str:
    return who if isinstance(who, str) and _LABEL.fullmatch(who) else "?"


class StopGate:
    def __init__(self, store: KillSwitchStore | None = None) -> None:
        self._store = store
        self._cond = threading.Condition()
        self._on = False
        self._inflight = 0
        self.last: EngageResult | None = None

    @property
    def engaged(self) -> bool:
        return self._on

    def blocked(self) -> bool:
        """True if this gate is engaged or the durable switch is on (the store is read each call)."""
        if self._on:
            return True
        return bool(self._store is not None and self._store.get_kill_switch().on)

    @contextmanager
    def effect(self):
        """Wrap every outbound effect. Refuses (``EffectBlocked``) when blocked; otherwise counts it in flight."""
        if self._store is not None and self._store.get_kill_switch().on:
            raise EffectBlocked("durable kill switch is on")
        with self._cond:
            if self._on:
                raise EffectBlocked("stop gate engaged")
            self._inflight += 1
        try:
            yield
        finally:
            with self._cond:
                self._inflight -= 1
                self._cond.notify_all()

    def engage(
        self,
        items: Callable[[], Iterable[str]],
        undo: Callable[[str], str],
        *,
        by: str,
        timeout: float | None = 30.0,
    ) -> EngageResult:
        """Durable switch first, then the flag (no new effect starts), then wait up to ``timeout`` seconds for effects in
        flight, then ``undo`` each item. One failing undo is reported and never stops the rest; an interrupt
        (KeyboardInterrupt) records the item and re-raises with the partial result in ``self.last``."""
        if self._store is not None:
            from hadavin_sdk.models import KillSwitch  # the durable model (name kept there)

            self._store.set_kill_switch(KillSwitch(on=True, by=_label(by)))
        res = EngageResult()
        self.last = res
        with self._cond:
            self._on = True
            drained = self._cond.wait_for(lambda: self._inflight == 0, timeout=timeout)
            res.in_flight_at_timeout = 0 if drained else self._inflight
        if not drained:
            res.complete = False
            return res
        for item in list(items()):
            try:
                res.results.append((item, undo(item)))
            except Exception as e:  # noqa: BLE001 - per-item choke point
                res.results.append((item, f"error:{type(e).__name__}"))
            except BaseException:
                res.results.append((item, "interrupted"))
                res.complete = False
                raise
        return res

    def restore(self, on: bool) -> None:
        """Set the in-process flag from persisted state (a restart). No store write, no sweep."""
        with self._cond:
            self._on = bool(on)

    def release(self, by: str) -> None:
        if self._store is not None:
            from hadavin_sdk.models import KillSwitch

            self._store.set_kill_switch(KillSwitch(on=False, by=_label(by)))
        with self._cond:
            self._on = False
