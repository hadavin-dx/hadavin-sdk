"""Read-only shared configuration: deep-frozen views, one immutable ``ConfigView``, a holder with one lock.

ACCIDENT-PROOFING, NOT A SANDBOX. ``freeze`` returns a deep copy whose dicts, lists and sets refuse every mutation through
Python's normal interface, so a caller cannot edit a policy or a directory by accident (or by a careless helper). Code that
deliberately calls ``dict.__setitem__(d, ...)`` on a frozen dict still reaches the C slot; a root of trust that must resist a
hostile in-process caller lives in a signed document outside the process. ``copy.deepcopy`` of a frozen value returns a plain,
editable copy BY DESIGN (that is how a change is prepared).

Types: dict -> ``FrozenDict``; list -> ``FrozenList``; tuple stays a tuple (its items are frozen); set -> frozenset; immutable
stdlib scalars (str, int, float, bool, None, bytes, Decimal, datetime, date, time, timedelta, Enum, UUID, PurePath) pass
through. Anything else (a pydantic model, an open file, a bytearray) is a ``TypeError``: it could be edited in place. Input nested
deeper than ``MAX_DEPTH`` (or cyclic) is a ``TypeError`` too, never a ``RecursionError``. A set that holds a tuple of dicts is
refused (a frozen dict is not hashable): configure such data as a list.

``ConfigView`` is ONE immutable policy + directory pair replaced as a whole, so a reader that takes ``holder.view()`` never sees
a new policy with an old directory. ``holder.swap(..., expect=version)`` is compare-and-set (two administrators cannot silently
overwrite each other). ``holder.lock`` serialises config changes and decisions; hold it only for the decision, never across I/O.
"""

from __future__ import annotations

import datetime as _dt
import decimal
import enum
import pathlib
import threading
import uuid
from dataclasses import dataclass
from typing import Any

MAX_DEPTH = 64
_LEAF = (
    str, int, float, bool, type(None), bytes, frozenset, decimal.Decimal, _dt.datetime, _dt.date, _dt.time, _dt.timedelta,
    enum.Enum, uuid.UUID, pathlib.PurePath,
)  # fmt: skip


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


def _freeze(o: Any, depth: int) -> Any:
    if depth > MAX_DEPTH:
        raise TypeError(f"configuration is nested deeper than {MAX_DEPTH} levels (or is cyclic)")
    if isinstance(o, dict):
        d = FrozenDict.__new__(FrozenDict)
        dict.__init__(d, {k: _freeze(v, depth + 1) for k, v in o.items()})
        object.__setattr__(d, "_sealed", True)
        return d
    if isinstance(o, list):
        lst = FrozenList.__new__(FrozenList)
        list.__init__(lst, [_freeze(v, depth + 1) for v in o])
        object.__setattr__(lst, "_sealed", True)
        return lst
    if isinstance(o, tuple):
        return tuple(_freeze(v, depth + 1) for v in o)
    if isinstance(o, (set, frozenset)):
        try:
            return frozenset(_freeze(v, depth + 1) for v in o)
        except TypeError as e:
            raise TypeError(f"a set member cannot be frozen into a hashable value: {e}") from e
    if isinstance(o, _LEAF):
        return o
    raise TypeError(
        f"cannot freeze a {type(o).__name__}: only JSON-shaped values, sets and immutable scalars"
    )


def freeze(o: Any) -> Any:
    """A deep frozen copy; nothing in the result is shared with ``o``."""
    return _freeze(o, 0)


def thaw(o: Any) -> Any:
    """A deep plain (mutable) copy of a frozen or plain structure (tuples stay tuples)."""
    if isinstance(o, dict):
        return {k: thaw(v) for k, v in o.items()}
    if isinstance(o, list):
        return [thaw(v) for v in o]
    if isinstance(o, tuple):
        return tuple(thaw(v) for v in o)
    if isinstance(o, (set, frozenset)):
        return {thaw(v) for v in o}
    return o


@dataclass(frozen=True)
class ConfigView:
    """One immutable policy + directory pair; ``version`` counts swaps."""

    pol: Any
    directory: Any
    version: int = 0


class ConfigConflict(RuntimeError):
    """``swap(expect=...)`` found another version than the caller read."""


class ConfigHolder:
    def __init__(self, pol: dict, directory: dict | None = None) -> None:
        self._view = ConfigView(freeze(pol), None if directory is None else freeze(directory))
        self.lock = threading.RLock()  # public on purpose: callers serialise a decision with a swap; protected by this docstring only

    def view(self) -> ConfigView:
        return self._view  # one attribute read: the pair is consistent

    @property
    def pol(self) -> Any:
        return self._view.pol

    @property
    def directory(self) -> Any:
        return self._view.directory

    def swap(self, pol: dict, directory: dict, *, expect: int | None = None) -> ConfigView:
        """Replace policy and directory together. Freezing happens before the lock is taken. With ``expect`` the swap is refused
        (``ConfigConflict``) unless the current version is that number."""
        new_pol, new_dir = freeze(pol), freeze(directory)
        with self.lock:
            if expect is not None and self._view.version != expect:
                raise ConfigConflict(f"config is at version {self._view.version}, not {expect}")
            self._view = ConfigView(new_pol, new_dir, self._view.version + 1)
            return self._view
