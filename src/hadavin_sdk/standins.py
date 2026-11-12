"""The core's own stand-ins: classes that hold or reach no real service (a fake channel, a recorded model, a
store in memory, a fake secrets provider, the pattern detector).

A leaf module: it imports nothing, so a module that must not reach a secret holder (the approvals receiver, through
``bindguard``) can ask "is this object a stand-in?" without importing the class. Each stand-in class marks itself with
``@stand_in``. What this module promises, and what it does not:

* the registry takes ONLY the classes named in ``_ALLOWED``, a literal written here (module and class name), and only
  from a module of this package; any other class, from a test, a script or a client's code, is refused with a
  ``TypeError``. A new stand-in is therefore a visible edit of two places (the literal and the class);
* the registry is an immutable ``frozenset`` kept in one private variable and rebuilt on each registration, so it
  cannot be added to from outside;
* the question is by EXACT class, by identity (``type(obj) is cls``, never by hash or ``==``): a subclass is not a
  stand-in, and a name or a marker attribute is never read;
* a stand-in stops counting as one when it has been changed: an instance that holds a function, method or class in
  its own attributes, or a class whose attributes differ from the ones it had when it registered (a replaced method,
  an added one), is read as real.

Not promised: a stand-in fed real secret values or pointed at a real address through its own plain data is still
the class of a stand-in. The class check reads classes, not what a person puts in them. Changing the base classes
of a registered class (or the base classes' methods) after registration is also not read."""

from __future__ import annotations

# module.Class names, the only ones the registry takes
_ALLOWED: frozenset[str] = frozenset(
    {
        "hadavin_sdk.actions.secrets.FakeSecretProvider",
        "hadavin_sdk.approvals.channel.FakeChannel",
        "hadavin_sdk.guard.injection.RegexDetector",
        "hadavin_sdk.llm.fake.FakeLLM",
        "hadavin_sdk.store.memory.MemoryStore",
    }
)

# registered class -> a copy of its own attributes at registration (name -> object)
_PINNED: dict[type, dict[str, object]] = {}
_CLASSES: frozenset[type] = frozenset()
_MISSING = object()


def stand_in[T: type](cls: T) -> T:
    """Class decorator: this class reaches no real service. Refused unless it is one of ``_ALLOWED``."""
    global _CLASSES
    name = f"{getattr(cls, '__module__', '')}.{getattr(cls, '__qualname__', '')}"
    if not isinstance(cls, type) or name not in _ALLOWED:
        raise TypeError(
            f"{name!r} is not a stand-in the core lists (standins._ALLOWED); it cannot be registered"
        )
    _PINNED[cls] = dict(vars(cls))
    _CLASSES = _CLASSES | {cls}
    return cls


def _changed(obj: object, cls: type) -> bool:
    """True when the class or the instance no longer matches what registered."""
    now, then = vars(cls), _PINNED[cls]
    if len(now) != len(then) or not all(now.get(n, _MISSING) is v for n, v in then.items()):
        return True
    try:
        own = object.__getattribute__(obj, "__dict__")
    except (
        AttributeError
    ):  # an instance with slots only: nothing of its own that can hold a function
        return False
    return any(callable(value) for value in dict.values(own)) if type(own) is dict else True


def is_registered_stand_in(obj: object) -> bool:
    """True when the exact class of ``obj`` is a registered stand-in (a subclass is not), the class has not been
    changed since it registered, and the instance holds no function, method or class of its own."""
    kind = type(obj)
    for cls in _CLASSES:
        if kind is cls:
            return not _changed(obj, cls)
    return False


def registered() -> frozenset[type]:
    return _CLASSES
