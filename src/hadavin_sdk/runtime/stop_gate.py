"""StopGate: the in-process effect barrier in front of the durable, audited stop (``hadavin_sdk.limits.Limits``).

Three names, one concept: ``models.KillSwitch`` is the DURABLE row; ``Limits.stop(by)`` / ``Limits.reset(by)`` are the audited
way to write it (the CLI uses them); ``StopGate`` is the in-process counterpart that makes a running process stop starting
effects and waits for the ones in flight. A gate over a durable switch takes the ``Limits`` object and delegates to it, so there is
ONE write path and the audit invariant is the same everywhere: ``engage`` flips the process flag FIRST (it cannot fail), then
calls ``Limits.stop`` (switch first, then audit through the outbox); if the store is down the gate stays engaged and the result
says ``durable=False`` with the error. ``release`` calls ``Limits.reset`` (audit intent first); if that fails the switch AND the gate
stay on and the error propagates.

Every outbound effect runs inside ``with gate.effect():`` (async code: ``async with gate.aeffect():``). The check and the count of
the effect in flight happen under one short condition lock that is NOT held during the effect, so a stop cannot slip between a
check and an act, and ``engage`` waits (with a timeout) for the effects already started. A port that only calls ``blocked()`` before
acting has a check-then-act race. The durable switch is read on every ``effect()`` (optionally cached for ``cache_ttl`` seconds)
and an unreadable store is treated as ENGAGED (fail closed). Cross-process safety of one particular effect (a conditional write in
the target system) is the effect's own job.

Local flag and store can drift: after an operator runs ``limits reset`` the gate that was engaged stays blocked until its own
``release()`` (a process never un-stops itself from outside). ``engaged`` is the PROCESS FLAG only (no store read); ``durable_on()``
is the durable switch (a store read, unreadable means on); ``blocked()`` is either. With ``cache_ttl > 0`` a cached "off" can hide an
operator's stop for up to ``cache_ttl`` seconds (the stale-allow window); this gate's own engage and release clear the cache. The
durable switch is one global row (``models.KillSwitch``): a per-tenant stop needs a schema change and is a tracked item
(``docs/promoted-controls.md``), not offered here. The audit rows of a gate flip carry ``source="gate"``.

``release`` versus ``engage``: every engage bumps a generation counter; ``release`` remembers it before the slow ``Limits.reset`` and
refuses to clear the flag if an engage happened meanwhile (it re-writes the stop and raises ``StopGateBusy``), so a late release can
never undo a newer engage.

Concurrency: a second ``engage`` while one sweep runs returns at once (``already_sweeping=True``) and runs no undo, so no item is undone
twice; ``release`` during a sweep raises ``StopGateBusy``. ``engage`` inside an ``effect()`` (or ``aengage`` inside an ``aeffect()``)
of the SAME thread or task does not wait for itself: the open-effect count is a ``ContextVar``, which ``asyncio.to_thread`` copies into
the worker. An effect opened by ANOTHER task is waited for, as it should be. Lock order: this gate takes only its own condition lock; the caller's config lock (``ConfigHolder.lock``) is never taken here.
Synchronous primitives; ``aengage`` / ``aeffect`` are the asyncio variants (``to_thread`` for the blocking parts).
"""

from __future__ import annotations

import asyncio
import contextvars
import re
import threading
import time
from collections.abc import Callable, Iterable
from contextlib import asynccontextmanager, contextmanager
from dataclasses import dataclass, field
from typing import Any, Protocol

from hadavin_sdk.models import AuditEvent

_OWN: contextvars.ContextVar[dict[int, int] | None] = contextvars.ContextVar(
    "stop_gate_own", default=None
)


class LimitsLike(Protocol):
    """The surface of ``hadavin_sdk.limits.Limits`` the gate uses."""

    audit: Any

    def stop(self, by: str, source: str = "cli") -> None: ...
    def reset(self, by: str, source: str = "cli") -> None: ...
    def is_stopped(self) -> bool: ...


class EffectBlocked(RuntimeError):
    """The gate is engaged (or the durable switch is on or unreadable): no outbound effect may start."""


class StopGateBusy(RuntimeError):
    """``release`` was called while a sweep is running."""


@dataclass
class EngageResult:
    results: list[tuple[str, str]] = field(default_factory=list)
    complete: bool = (
        True  # False: the wait for in-flight effects timed out, or the sweep was interrupted
    )
    in_flight_at_timeout: int = 0
    # True: ``Limits.stop`` returned. False: it raised (the gate is engaged anyway); the switch may still be on if the failure came after
    # the switch write (the audit step), so read ``durable_on()``. None: another engage owns the sweep and this call wrote nothing.
    durable: bool | None = True
    store_error: str | None = None
    already_sweeping: bool = False  # another engage owns the sweep; nothing was undone here


_LABEL = re.compile(r"[A-Za-z0-9_.:@ -]{1,60}")


def _label(who: object) -> str:
    return who if isinstance(who, str) and _LABEL.fullmatch(who) else "?"


class StopGate:
    def __init__(self, limits: LimitsLike | None = None, *, cache_ttl: float = 0.0) -> None:
        self._limits = limits
        self._cond = threading.Condition()
        self._on = False
        self._inflight = 0
        self._sweeping = False
        self._gen = 0  # bumped by every engage; release refuses to clear the flag if it moved
        self._cache_ttl = max(0.0, float(cache_ttl))
        self._cached: tuple[float, bool] | None = None
        self._last: EngageResult | None = None

    # ---- state -------------------------------------------------------------------------------------------------------------
    @property
    def engaged(self) -> bool:
        """The process flag only (no store read). ``blocked()`` also reads the durable switch."""
        return self._on

    @property
    def last(self) -> EngageResult | None:
        with self._cond:
            return self._last

    def durable_on(self) -> bool:
        """The durable switch (a store read; failure means ENGAGED). False without a ``Limits``."""
        if self._limits is None:
            return False
        now = time.monotonic()
        c = self._cached
        if self._cache_ttl and c is not None and now - c[0] < self._cache_ttl:
            return c[1]
        try:
            on = bool(self._limits.is_stopped())
        except Exception:  # noqa: BLE001 - an unreadable store fails closed
            on = True
        self._cached = (now, on)
        return on

    def blocked(self) -> bool:
        return self._on or self.durable_on()

    def restore(self, on: bool) -> None:
        """Set the in-process flag from persisted state (a restart). No store write, no sweep."""
        with self._cond:
            self._on = bool(on)

    # ---- effects -----------------------------------------------------------------------------------------------------------
    def _enter(self) -> None:
        with self._cond:
            if self._on:
                raise EffectBlocked("stop gate engaged")
            self._inflight += 1
        self._own(+1)

    def _own(self, delta: int = 0) -> int:
        """Effects the CURRENT thread or task has open on this gate (a ContextVar, copied into ``to_thread`` workers)."""
        m = _OWN.get() or {}
        n = m.get(id(self), 0) + delta
        if delta:
            m = {**m, id(self): n} if n > 0 else {k: v for k, v in m.items() if k != id(self)}
            _OWN.set(m)
        return n

    def _leave(self) -> None:
        self._own(-1)
        with self._cond:
            self._inflight -= 1
            self._cond.notify_all()

    @contextmanager
    def effect(self):
        """Wrap every outbound effect. Refuses (``EffectBlocked``) when blocked; otherwise counts it in flight."""
        if self.durable_on():
            raise EffectBlocked("durable kill switch is on or unreadable")
        self._enter()
        try:
            yield
        finally:
            self._leave()

    @asynccontextmanager
    async def aeffect(self):
        """asyncio variant of ``effect()``: the store read runs in a thread; the count is a short non-blocking critical section."""
        if self._limits is not None and await asyncio.to_thread(self.durable_on):
            raise EffectBlocked("durable kill switch is on or unreadable")
        with self._cond:
            if self._on:
                raise EffectBlocked("stop gate engaged")
            self._inflight += 1
        self._own(+1)
        try:
            yield
        finally:
            self._leave()

    # ---- engage / release ----------------------------------------------------------------------------------------------------
    def engage(
        self,
        items: Callable[[], Iterable[str]],
        undo: Callable[[str], str],
        *,
        by: str,
        timeout: float | None = 30.0,
    ) -> EngageResult:
        """Flag first (no new effect starts), then the durable switch (audited by ``Limits.stop``), then wait up to ``timeout``
        seconds for effects in flight, then ``undo`` each item. ``undo`` must be idempotent. One failing undo is reported and never
        stops the rest; an interrupt records the item and re-raises with the partial result in ``last``. If the effects in flight do not
        drain within ``timeout`` the sweep is NOT run (``complete=False``, nothing undone): call ``engage`` again (it is idempotent)."""
        with self._cond:
            self._on = True
            self._gen += 1
            self._cached = None
            if self._sweeping:
                return EngageResult(already_sweeping=True, durable=None)
            self._sweeping = True
        res = EngageResult()
        with self._cond:
            self._last = res
        try:
            if self._limits is not None:
                try:
                    self._limits.stop(_label(by), source="gate")
                except Exception as e:  # noqa: BLE001 - the process is already stopped; report that the durable write failed
                    res.durable, res.store_error = False, f"{type(e).__name__}: {e}"[:200]
                    self._audit_stop_failed(by, type(e).__name__)
            own = self._own()  # effects THIS thread or task has open do not block its own engage
            with self._cond:
                drained = self._cond.wait_for(lambda: self._inflight - own <= 0, timeout=timeout)
                res.in_flight_at_timeout = 0 if drained else self._inflight - own
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
        finally:
            with self._cond:
                self._sweeping = False

    def _audit_stop_failed(self, by: str, error: str) -> None:
        """``Limits.stop`` raised, so it may have written no audit row: record the emergency stop here (best effort, never raises)."""
        event = AuditEvent(
            run_id="-", domain="limits", operation="stop", principal=_label(by), source="gate",
            result="on", error_code=f"durable_write_failed:{error}"[:60],
        )  # fmt: skip
        try:
            self._limits.audit.write_outcome(event)  # type: ignore[union-attr]
        except Exception:  # noqa: BLE001, S110 - the process is stopped either way
            pass

    def release(self, by: str) -> None:
        """Audit first (``Limits.reset`` writes the intent, then the switch). If that fails the switch and the gate stay ON and the
        error propagates. Not allowed while a sweep runs. If an ``engage`` ran while the reset was in flight, the flag is NOT cleared,
        the stop is written again and ``StopGateBusy`` is raised: a release never undoes a newer engage."""
        with self._cond:
            if self._sweeping:
                raise StopGateBusy("a sweep is running")
            gen = self._gen
        if self._limits is not None:
            self._limits.reset(_label(by), source="gate")
        with self._cond:
            self._cached = None
            again = self._gen != gen
            if not again:
                self._on = False
        if again:
            if self._limits is not None:
                try:
                    self._limits.stop(_label(by), source="gate")
                except Exception as e:  # noqa: BLE001 - the gate is engaged either way
                    self._audit_stop_failed(by, type(e).__name__)
            raise StopGateBusy("an engage ran during the release: the stop stays on")

    async def aengage(
        self,
        items: Callable[[], Iterable[str]],
        undo: Callable[[str], str],
        *,
        by: str,
        timeout: float | None = 30.0,
    ) -> EngageResult:
        """asyncio variant: runs ``engage`` in a worker thread, so the event loop keeps running the async effects it waits for."""
        return await asyncio.to_thread(self.engage, items, undo, by=by, timeout=timeout)

    async def arelease(self, by: str) -> None:
        await asyncio.to_thread(self.release, by)
