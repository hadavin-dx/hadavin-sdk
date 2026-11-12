"""The core's own stand-ins: classes that hold or reach no real service (a fake channel, a recorded model, a
store in memory, a fake secrets provider, the pattern detector).

A leaf module: it imports nothing, so a module that must not reach a secret holder (the approvals receiver, through
``bindguard``) can ask "is this object a stand-in?" without importing the class. Each stand-in class marks itself with
``@stand_in``. The test is by EXACT class: a subclass is not a stand-in, and a name or a marker attribute is never
read. ``tests/test_bindguard.py`` pins the complete list, so a new entry is a visible change."""

from __future__ import annotations

_CLASSES: set[type] = set()


def stand_in[T: type](cls: T) -> T:
    """Class decorator: this class reaches no real service."""
    _CLASSES.add(cls)
    return cls


def is_registered_stand_in(obj: object) -> bool:
    """True when the exact class of ``obj`` is a registered stand-in (a subclass is not)."""
    return type(obj) in _CLASSES


def registered() -> frozenset[type]:
    return frozenset(_CLASSES)
