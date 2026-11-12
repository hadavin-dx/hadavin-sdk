"""The core's own stand-ins: classes that hold or reach no real service (a fake channel, a recorded model, a
store in memory, a fake secrets provider, the pattern detector).

A leaf module (it imports only standard modules), so a module that must not reach a secret holder (the approvals
receiver, through ``bindguard``) can ask "is this object a stand-in?" without importing the class.

Who may be a stand-in is decided HERE, from two literals, never from what a class says about itself:

* ``_ALLOWED`` lists the five stand-ins as literal (module name, class name) pairs, ``_DETECTOR_LIST`` names the
  detector list (``AnyOf``) the same way. There is no registration step and no decorator: a class cannot join by
  writing a ``__module__``, a ``__qualname__`` or a marker, and a new stand-in is a visible edit of this literal;
* the question is answered by LOOKING THE CLASS UP: ``sys.modules[module].__dict__[name]`` (the module's own
  dictionary, not ``getattr``, so a module-level ``__getattr__`` is never run; the module must be a plain module).
  The object is a stand-in only when ``type(obj) is cls`` (identity: a subclass, a class of the same name and a
  class that fakes ``==`` or ``hash`` are not). A class whose module is not imported (yet) never matches;
* the first time a class is found live, a pin is taken: its metaclass, its ``__mro__`` and the ``vars()`` of every
  class in the ``__mro__`` except ``object`` (name and object, in order, compared by identity). At each later
  question the class must still match the pin: a replaced or added method, a changed base class or a rebinding of
  the module name reads as real. A missing or cleared pin of a class that was seen before reads as real (fail
  closed);
* the instance is scanned too, to a depth of ``SCAN_DEPTH`` (4) levels and at most ``SCAN_NODES`` values: a
  function, method or class held in its own attributes or inside a dict, list, tuple, set or deque held there
  reads as real. Containers deeper than the limit are not entered (the limit is stated, not hidden); an instance
  that holds more than the node budget reads as real;
* a detector list (``AnyOf``) is pinned the same way, its ``detectors`` must be a plain ``tuple``, and every
  member must itself be a stand-in (nesting at most ``SCAN_DEPTH`` deep, cycles refused by an id set);
* any error while asking reads as "not a stand-in".

Not promised: the pin is taken at the first question, so a change made before it is not seen; and code that runs in
the same process and rewrites this module, ``sys.modules`` or the guard itself is outside what Python can stop. A
stand-in fed real secret values or pointed at a real address through its own plain data is still the class of a
stand-in: the check reads classes, not what a person puts in them."""

from __future__ import annotations

import sys
from collections import deque
from types import ModuleType

SCAN_DEPTH = 4  # levels of containers entered inside an instance (and of nested detector lists)
SCAN_NODES = 100_000  # values looked at in one instance; more than this reads as real

# (module, class name): the only classes that count, written here and nowhere else
_ALLOWED: tuple[tuple[str, str], ...] = (
    ("hadavin_sdk.actions.secrets", "FakeSecretProvider"),
    ("hadavin_sdk.approvals.channel", "FakeChannel"),
    ("hadavin_sdk.guard.injection", "RegexDetector"),
    ("hadavin_sdk.llm.fake", "FakeLLM"),
    ("hadavin_sdk.store.memory", "MemoryStore"),
)
_DETECTOR_LIST = ("hadavin_sdk.guard.injection", "AnyOf")

# (module, name) -> pin taken at the first question; _SEEN names the keys that were pinned (a key that was seen
# and has no pin any more reads as real)
_PINNED: dict[tuple[str, str], tuple[object, ...]] = {}
_SEEN: frozenset[tuple[str, str]] = frozenset()


def _live_class(key: tuple[str, str]) -> type | None:
    """The class the module really holds under that name now, or None (module not imported, not a plain module,
    name missing or not a class). The module's own dictionary is read, never ``getattr``."""
    module = sys.modules.get(key[0])
    if type(module) is not ModuleType:
        return None
    cls = dict.get(vars(module), key[1])
    return cls if isinstance(cls, type) else None


def _shape(cls: type) -> tuple[object, ...]:
    """(metaclass, mro, then per class of the mro except ``object``: its (name, object) pairs in order)."""
    mro = cls.__mro__
    return (type(cls), mro, *(tuple(vars(c).items()) for c in mro if c is not object))


def _same_shape(cls: type, pin: tuple[object, ...]) -> bool:
    """True when the class still has the pinned metaclass, mro and attributes (compared by identity)."""
    now = _shape(cls)
    if len(now) != len(pin) or now[0] is not pin[0]:
        return False
    if len(now[1]) != len(pin[1]) or not all(a is b for a, b in zip(now[1], pin[1], strict=True)):  # type: ignore[arg-type]
        return False
    for was, is_ in zip(pin[2:], now[2:], strict=True):
        if len(was) != len(is_):  # type: ignore[arg-type]
            return False
        for (kw, vw), (ki, vi) in zip(was, is_, strict=True):  # type: ignore[misc]
            if not (type(ki) is str and kw == ki and vw is vi):
                return False
    return True


def _class_ok(key: tuple[str, str], cls: type) -> bool:
    """The class has not changed since it was pinned (it is pinned now when first seen)."""
    global _SEEN
    pin = _PINNED.get(key)
    if pin is None:
        if key in _SEEN:
            return False  # seen before and the pin is gone: fail closed
        _PINNED[key] = _shape(cls)
        _SEEN = _SEEN | {key}
        return True
    return _same_shape(cls, pin)


def _values(container: object) -> tuple[object, ...]:
    """The values of a dict, list, tuple, set, frozenset or deque (or a subclass), read with the builtin's own
    method, so a subclass's ``__iter__`` is never run; ``()`` for anything else."""
    kind = type(container)
    if issubclass(kind, dict):
        return tuple(dict.values(container))  # type: ignore[arg-type]
    for base in (list, tuple, set, frozenset, deque):
        if issubclass(kind, base):
            return tuple(base.__iter__(container))  # type: ignore[arg-type]
    return ()


def _holds_a_function(own: object) -> bool:
    """True when the values of ``own`` (an instance dict) include a callable (function, method, class, anything
    with ``__call__``) at any of the first ``SCAN_DEPTH`` levels of containers, or more than ``SCAN_NODES`` values."""
    budget = SCAN_NODES
    level: list[object] = [own]
    for _ in range(SCAN_DEPTH):
        nxt: list[object] = []
        for container in level:
            for value in _values(container):
                budget -= 1
                if budget < 0 or callable(value):
                    return True
                if _values(value):
                    nxt.append(value)
        level = nxt
    return False


def _instance_ok(obj: object) -> bool:
    # no instance dictionary is an error here, and an error reads as "not a stand-in"
    return not _holds_a_function(object.__getattribute__(obj, "__dict__"))


def _check(obj: object, depth: int, seen: frozenset[int]) -> bool:
    kind = type(obj)
    for key in _ALLOWED:
        cls = _live_class(key)
        if cls is not None and kind is cls:
            return _class_ok(key, cls) and _instance_ok(obj)
    cls = _live_class(_DETECTOR_LIST)
    if cls is None or kind is not cls or depth >= SCAN_DEPTH or id(obj) in seen:
        return False
    if not (_class_ok(_DETECTOR_LIST, cls) and _instance_ok(obj)):
        return False
    members = dict.get(object.__getattribute__(obj, "__dict__"), "detectors")
    if type(members) is not tuple:
        return False
    return all(_check(m, depth + 1, seen | {id(obj)}) for m in tuple.__iter__(members))


def is_stand_in(obj: object) -> bool:
    """True only for an instance of one of the core's own stand-in classes, or of a detector list (``AnyOf``)
    whose members all are (see the module text for everything that is checked). Never raises."""
    try:
        return _check(obj, 0, frozenset())
    except Exception:  # noqa: BLE001 - anything unreadable is not a stand-in (fail closed)
        return False


def registered() -> frozenset[type]:
    """The five stand-in classes as they are found now (a class whose module is not imported is left out)."""
    found = (_live_class(key) for key in _ALLOWED)
    return frozenset(c for c in found if c is not None)
