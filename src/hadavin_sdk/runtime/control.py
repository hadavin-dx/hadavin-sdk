"""Read-only shared configuration, one lock, and a kill switch every port can read.

A policy or directory (the root of trust) handed out as a plain dict can be edited in place by any holder of
the reference. ``freeze`` returns a deep copy whose dicts and lists refuse every mutation; ``ConfigHolder`` is
the single source every executor and port reads on each use; ``KillSwitch`` is set first (so no new effect
starts) and then waits for the holder's lock (so an effect already past its gates has recorded itself) before
it sweeps. Vendor-neutral, stdlib only."""

from __future__ import annotations

import threading
from collections.abc import Callable, Iterable
from typing import Any


def _refuse(self: object, *a: object, **k: object) -> None:
    raise TypeError("read-only configuration: change it only through the holder's controlled swap")


class FrozenDict(dict):
    """A dict that refuses every mutation through its Python interface. ``dict.__setitem__(d, ...)`` still
    reaches the C slot: that is a deliberate bypass, outside what a read-only view promises."""

    __setitem__ = __delitem__ = update = pop = popitem = clear = setdefault = __ior__ = _refuse  # type: ignore[assignment]

    def __reduce__(self) -> tuple[Any, ...]:
        return (FrozenDict, (dict(self),))

    def __deepcopy__(self, memo: dict) -> Any:
        return thaw(self)


class FrozenList(list):
    __setitem__ = __delitem__ = append = extend = insert = remove = pop = clear = _refuse  # type: ignore[assignment]
    sort = reverse = __iadd__ = __imul__ = _refuse  # type: ignore[assignment]

    def __reduce__(self) -> tuple[Any, ...]:
        return (FrozenList, (list(self),))

    def __deepcopy__(self, memo: dict) -> Any:
        return thaw(self)


def freeze(o: Any) -> Any:
    """A deep frozen copy; nothing in the result is shared with ``o``."""
    if isinstance(o, dict):
        d = FrozenDict()
        for k, v in o.items():
            dict.__setitem__(d, k, freeze(v))
        return d
    if isinstance(o, (list, tuple)):
        return FrozenList(freeze(v) for v in o)
    return o


def thaw(o: Any) -> Any:
    """A deep plain (mutable) copy of a frozen or plain structure."""
    if isinstance(o, dict):
        return {k: thaw(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [thaw(v) for v in o]
    return o


class ConfigHolder:
    """Policy + directory behind one re-entrant lock. Readers take ``.pol`` / ``.directory`` on every use."""

    def __init__(self, pol: dict, directory: dict | None = None) -> None:
        self._pol: Any = freeze(pol)
        self._directory: Any = None if directory is None else freeze(directory)
        self.bound = False
        self.lock = threading.RLock()
        self._switches: list[KillSwitch] = []

    @property
    def pol(self) -> Any:
        return self._pol

    @property
    def directory(self) -> Any:
        return self._directory

    def swap(self, pol: dict, directory: dict) -> None:
        with self.lock:
            self._pol, self._directory = freeze(pol), freeze(directory)

    def blocked(self) -> bool:
        """True if any kill switch watching this holder is on (ports call this before an outbound effect)."""
        return any(s.engaged for s in self._switches)


class KillSwitch:
    def __init__(self, holder: ConfigHolder) -> None:
        self.holder = holder
        self._on = False
        self._guard = threading.Lock()
        holder._switches.append(self)

    @property
    def engaged(self) -> bool:
        return self._on

    def engage(
        self, items: Callable[[], Iterable[str]], undo: Callable[[str], str]
    ) -> list[tuple[str, str]]:
        """Set the switch, wait for work in flight (the holder's lock), then undo every item; one failing
        undo is reported and never stops the rest."""
        with self._guard:
            self._on = True
        out: list[tuple[str, str]] = []
        with self.holder.lock:
            for item in list(items()):
                try:
                    out.append((item, undo(item)))
                except Exception as e:  # noqa: BLE001 - per-item choke point
                    out.append((item, f"error:{type(e).__name__}"))
        return out

    def release(self) -> None:
        with self._guard:
            self._on = False
