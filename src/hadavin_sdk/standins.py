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
  class that fakes ``==`` or ``hash`` are not). Every allowlist below is judged the same way, by IDENTITY over a
  tuple of classes (``_is_one_of``: ``kind is t``, never ``kind in`` a set or a tuple, which would run the
  ``__hash__`` and ``__eq__`` of a metaclass that the held value controls). A class whose module is not imported (yet) never matches;
* the first time a class is found live, a pin is taken: its metaclass, its ``__mro__`` and the ``vars()`` of every
  class in the ``__mro__`` except ``object`` (name and object, in order, compared by identity). At each later
  question the class must still match the pin: a replaced or added method, a changed base class or a rebinding of
  the module name reads as real. A missing or cleared pin of a class that was seen before reads as real (fail
  closed);
* the instance is scanned too, by an ALLOWLIST (deny by default): every value it holds must be plain data, judged
  by its EXACT type (``type(v) is T``, never ``isinstance``): str, bytes, int, float, bool, None, Decimal, date,
  datetime, timedelta, Path, a lock, and the builtin containers dict, list, tuple, set, frozenset and deque
  (entered; for a dict its keys are judged too), a ``Counter``, a ``defaultdict`` whose factory is one of
  ``list``, ``dict``, ``set``, ``int``, ``float`` or ``Decimal``, and the model types the five stand-ins really hold
  (the literal list ``_DATA_CLASSES``, found in their module dictionaries; each one is judged by exact type and its
  own attributes are entered; the class of a data type is NOT pinned, because those types hold no code the guard
  runs). Anything else reads as real: a function, a method, a class, a subclass of dict or list, a ``defaultdict``
  with another factory, ``UserDict``, ``ChainMap``, ``MappingProxyType``, ``SimpleNamespace``, a client or session
  object, an object with ``__enter__``, a generator, an iterator, a ``memoryview`` or a ``bytearray``. A value whose
  type is itself one of the pinned stand-in classes (a nested stand-in) is judged by the same pin and scanned in
  turn. A member of ``RunState`` is a plain value only when it is the real member (identity against
  ``RunState.__members__``) and its own dictionary holds only the enum's own keys. The scan enters
  ``SCAN_DEPTH_VALUES`` (8) levels of containers (the instance's own attribute dictionary is level 1; an
  approval request with its steps in a store is six levels) and looks at no more than ``SCAN_NODES`` values,
  charged when a container is ENTERED and before it is copied (its size is read with the builtin ``__len__``; a
  container bigger than what is left of the budget is not copied and reads as real, so a huge list referenced a
  thousand times costs the size check, not a thousand copies). Both limits FAIL CLOSED: a container that is still
  unexplored after the last level and holds anything but plain atoms (str, int, ...) reads as real, and so does an
  instance that holds more than the budget;
* a detector list (``AnyOf``) is pinned the same way, its ``detectors`` must be a plain ``tuple``, and every
  member must itself be a stand-in (nesting at most ``SCAN_DEPTH`` (4) deep, cycles refused by an id set);
* any error while asking reads as "not a stand-in".

The pins are taken EAGERLY: ``pin_all`` runs when the approvals receiver is imported (it imports the modules of four
stand-ins and pins them with the detector list and ``Approvals``), so a change made after that import is seen.
``FakeSecretProvider`` is pinned by its own module: the repo's secrets rule (``tests/test_repo_rules.py``, "in any
spelling ... lazy inside a function") does not let anything reachable from approvals import the secret holders, so
the receiver does not import ``hadavin_sdk.actions.secrets``, not even lazily. Instead the last line of that module
calls ``pin_module(__name__)`` here (this module is a leaf: standard imports only, so the secrets module takes in
nothing that reaches a service). The pin is therefore taken when the class is created, whichever of the two modules
is imported first, and a patch or a replaced class made after that is seen. The first-question pin
(``_class_ok`` pins a class it has not seen) is only the fallback for a class whose module did not call
``pin_module``; it is not reached for the five stand-ins today. Pinned by
``test_the_fake_secret_provider_is_pinned_when_its_module_is_loaded_whichever_comes_first``.
The scan runs at every question and its answer is NOT cached: a cache would have to read the whole structure to see
that a function was put inside a held container, which costs what the scan costs. The cost is bounded by
``SCAN_NODES`` (an instance over the budget reads as real: the receiver answers 503 to every request, and
``serve()`` is refused at the start, until the store is smaller).

Fragile on purpose: touching ``cls.__annotations__`` adds an empty entry to the class dictionary on Python 3.12 and
3.13, so the pin touches it at pin time and at every comparison; a class whose dictionary changes in any other way
(for example ``importlib.reload``) reads as real (fail closed).

Not promised: code that runs in the same process and rewrites this module, ``sys.modules`` or the guard itself is
outside what Python can stop. A stand-in fed real secret values or pointed at a real address through its own plain
data is still the class of a stand-in: the check reads classes and the types of what they hold, not what a person
puts in the strings."""

from __future__ import annotations

import contextlib
import sys
import threading
from collections import Counter, defaultdict, deque
from datetime import date, datetime, timedelta
from decimal import Decimal
from pathlib import Path
from types import ModuleType

SCAN_DEPTH = 4  # nesting of detector lists
SCAN_DEPTH_VALUES = 8  # container levels entered in a held instance (its own dict is 1)
SCAN_NODES = (
    100_000  # values looked at in one question (every walk, shared members charged at every visit)
)
STAND_IN_WEIGHT = (
    50  # nodes charged for each stand-in or data row visited (its class shape is compared, a scan)
)
VERDICT_STAND_IN = "stand-in"
VERDICT_REAL = "real"
VERDICT_OVER_BUDGET = (
    "over budget"  # more than SCAN_NODES would be read: not scanned further, read as real
)

# (module, class name): the only classes that count, written here and nowhere else
_ALLOWED: tuple[tuple[str, str], ...] = (
    ("hadavin_sdk.actions.secrets", "FakeSecretProvider"),
    ("hadavin_sdk.approvals.channel", "FakeChannel"),
    ("hadavin_sdk.guard.injection", "RegexDetector"),
    ("hadavin_sdk.llm.fake", "FakeLLM"),
    ("hadavin_sdk.store.memory", "MemoryStore"),
)
_DETECTOR_LIST = ("hadavin_sdk.guard.injection", "AnyOf")
# the approvals object the receiver serves is pinned in the same way (``is_pinned_instance``)
APPROVALS = ("hadavin_sdk.approvals.requests", "Approvals")
_PINNED_KEYS = (*_ALLOWED, _DETECTOR_LIST, APPROVALS)

# The plain-data types the five stand-ins really hold (found by reading their class bodies and by scanning every
# stand-in the test suite makes; each is judged by exact type and its own attributes are entered). Reason per
# group: the models are the rows MemoryStore keeps (runs, plans, gate answers, approval requests and decisions, dead
# letters, the kill switch, tick state, tool-call records), ``Route`` is what FakeLLM reads its prices from, ``Card``
# is what FakeChannel records.
_MODELS = "hadavin_sdk.models"
_DATA_CLASSES: tuple[tuple[str, str], ...] = (
    (_MODELS, "Run"),
    (_MODELS, "Target"),
    (_MODELS, "Plan"),
    (_MODELS, "GateDecision"),
    (_MODELS, "ChainStep"),
    (_MODELS, "ApprovalRequest"),
    (_MODELS, "ApprovalDecision"),
    (_MODELS, "DeadLetter"),
    (_MODELS, "TickState"),
    (_MODELS, "ToolCallRecord"),
    (_MODELS, "KillSwitch"),
    ("hadavin_sdk.config", "Route"),
    ("hadavin_sdk.approvals.cards", "Card"),
)
# the one data class that is a plain dataclass (not pydantic): all its state is its ``__dict__``, which is scanned
_DATACLASS_KEYS: frozenset[tuple[str, str]] = frozenset({("hadavin_sdk.approvals.cards", "Card")})
# plain values that are NOT entered (an enum member holds its own class): the state of a run
_LEAF_CLASSES: tuple[tuple[str, str], ...] = ((_MODELS, "RunState"),)

# Tuples of classes, judged by identity only (``_is_one_of``), never by ``in``
_ATOM_TYPES: tuple[type, ...] = (
    str,
    bytes,
    int,
    float,
    bool,
    type(None),
    Decimal,
    date,
    datetime,
    timedelta,
    type(Path()),
    type(threading.Lock()),  # held by MemoryStore and FakeLLM; it holds no code
)
_PLAIN_CONTAINERS: tuple[type, ...] = (dict, list, tuple, set, frozenset, deque)


def _own_enum_member_keys() -> frozenset[str]:
    """The keys a member of an enum holds in its own dictionary on THIS interpreter, read from a member of a
    throw-away enum made now (a new key in a later Python version cannot make every ``Run`` read as real)."""
    import enum

    class _Probe(enum.Enum):
        A = "a"

    return frozenset(object.__getattribute__(_Probe.A, "__dict__"))


_ENUM_MEMBER_KEYS: frozenset[str] = _own_enum_member_keys()
_DEFAULT_FACTORIES: tuple[object, ...] = (list, dict, set, int, float, Decimal)

# (module, name) -> pin taken at the first question; _SEEN names the keys that were pinned (a key that was seen
# and has no pin any more reads as real)
_PINNED: dict[tuple[str, str], tuple[object, ...]] = {}
_SEEN: frozenset[tuple[str, str]] = frozenset()
_PIN_LOCK = threading.Lock()


def live_class(key: tuple[str, str]) -> type | None:
    """The class the module really holds under that name now, or None (module not imported, not a plain module,
    name missing or not a class). The module's own dictionary is read, never ``getattr``."""
    module = sys.modules.get(key[0])
    if type(module) is not ModuleType:
        return None
    cls = dict.get(vars(module), key[1])
    return cls if isinstance(cls, type) else None


_CLASS_ANNOTATIONS = vars(type)[
    "__annotations__"
]  # ``type``'s own getter: a metaclass cannot answer for it


def _touch_annotations(cls: type) -> None:
    """Python 3.12 and 3.13 add an empty ``__annotations__`` to a class dictionary the first time it is read, and
    3.12 fills some entries lazily: read it now, through ``type``'s own descriptor, so the pin includes it."""
    with contextlib.suppress(Exception):  # a class without one (3.14 reads it differently) is fine
        _CLASS_ANNOTATIONS.__get__(cls)


def _shape(cls: type) -> tuple[object, ...]:
    """(metaclass, mro, then per class of the mro except ``object``: its (name, object) pairs in order)."""
    mro = cls.__mro__
    for c in mro:
        if c is not object:
            _touch_annotations(c)
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


def _class_ok(key: tuple[str, str]) -> bool:
    """The listed class (as found now under ``key``) has not changed since it was pinned (it is pinned now when
    first seen). That ``kind`` IS this class is decided by the caller, by identity, in ``_stand_in_key``."""
    global _SEEN
    cls = live_class(key)
    if cls is None:
        return False
    pin = _PINNED.get(key)
    if pin is None:
        with _PIN_LOCK:
            pin = _PINNED.get(key)
            if pin is None:
                if key in _SEEN:
                    return False  # seen before and the pin is gone: fail closed
                _PINNED[key] = _shape(cls)
                _SEEN = _SEEN | {key}
                return True
    return _same_shape(cls, pin)


def pin_module(module: str) -> None:
    """Pin every listed class of ``module`` now. Called by the last line of a module that holds a listed class and
    that the approvals side must not import (``hadavin_sdk.actions.secrets``). Never raises."""
    for key in _PINNED_KEYS:
        if key[0] == module:
            with contextlib.suppress(Exception):
                if live_class(key) is not None:
                    _class_ok(key)


def pin_all() -> None:
    """Pin the five stand-in classes, the detector list and ``Approvals`` now (called when the approvals receiver
    is imported). A class whose module is not loaded is left for the first
    question (fail closed: the first question pins it)."""
    # plain imports (not importlib) so that the modules exist to be pinned; done here, inside the function, because
    # the approvals package must not import them itself (they are not imported at the top: a circle). The secret
    # provider's module is NOT imported here: the repo rule says nothing reachable from approvals may import the
    # secret holders, so ``FakeSecretProvider`` is pinned now only if its module is already loaded, else at the first question
    from hadavin_sdk.approvals import channel
    from hadavin_sdk.guard import injection
    from hadavin_sdk.llm import fake
    from hadavin_sdk.store import memory

    _ = (channel, injection, fake, memory)  # imported so that their classes exist to be pinned
    for key in _PINNED_KEYS:
        with contextlib.suppress(Exception):  # the lazy path pins it at the first question
            cls = live_class(key)
            if cls is not None:
                _class_ok(key)


def is_pinned_instance(obj: object, key: tuple[str, str] = APPROVALS) -> bool:
    """True when ``obj`` is an instance of exactly the class found under ``key`` and that class is unchanged since
    it was pinned. Never raises."""
    try:
        cls = live_class(key)
        return cls is not None and type(obj) is cls and _class_ok(key)
    except Exception:  # noqa: BLE001 - anything unreadable is not the pinned class
        return False


def _is_one_of(kind: type, types: tuple[type, ...]) -> bool:
    """True when ``kind`` IS one of ``types``: identity only. ``kind`` is the type of a held value, so it can be a
    class with a metaclass that fakes ``__hash__`` and ``__eq__``; ``kind in types`` would run them."""
    return any(kind is t for t in types)


# (builtin type, its own length method, values read per item): a subclass is read with the builtin's method
_SIZED: tuple[tuple[type, object, int], ...] = (
    (dict, dict.__len__, 2),
    (list, list.__len__, 1),
    (tuple, tuple.__len__, 1),
    (set, set.__len__, 1),
    (frozenset, frozenset.__len__, 1),
    (deque, deque.__len__, 1),
)


def _values(container: object, limit: int) -> tuple[object, ...] | None:
    """What a dict (its keys, then its values), list, tuple, set, frozenset or deque (or a subclass) holds, read
    with the builtin's own method, so a subclass's ``__iter__`` is never run; ``()`` for anything else. The size is
    read first, with the builtin ``__len__``: more than ``limit`` values gives ``None`` (read as real) and nothing
    is copied."""
    kind = type(container)
    for base, length, per in _SIZED:
        if issubclass(kind, base):
            if length(container) * per > limit:  # type: ignore[operator]
                return None
            if base is dict:
                return (*dict.keys(container), *dict.values(container))  # type: ignore[arg-type]
            return tuple(base.__iter__(container))  # type: ignore[attr-defined]
    return ()


class _Budget:
    """The one budget of one question: ``left`` nodes for every walk (the values of the instance, the detector
    list, the members of a list of detectors), charged at EVERY visit (a member shared a thousand times is charged a
    thousand times), and the per-question memory of which listed classes were already compared (``ok``: a local of
    this question, never module state, so a patch made between two questions is always seen)."""

    __slots__ = ("left", "ok", "over")

    def __init__(self) -> None:
        self.left = SCAN_NODES
        self.ok: dict[tuple[str, str], bool] = {}
        self.over = False  # set when the budget ran out (the answer is then "real", reported as over budget)

    def charge(self, nodes: int) -> bool:
        self.left -= nodes
        if self.left < 0:
            self.over = True
            return False
        return True

    def class_ok(self, key: tuple[str, str]) -> bool:
        """``_class_ok`` once per class per question (a list of 100,000 references to one class costs one shape
        comparison, not 100,000)."""
        got = self.ok.get(key)
        if got is None:
            got = self.ok[key] = _class_ok(key)
        return got


def _no_instance_state(value: object, kind: type) -> bool:
    """True when an instance of the allowlisted plain type ``kind`` carries no state outside what the scan reads:
    the type has no instance dictionary (a builtin container or atom), or its dictionary is a plain empty ``dict``
    (``Counter`` is pure Python and has one: ``store.stats.client = RealClient()`` would hide there). Every plain
    type goes through this one helper, so a type added to an allowlist cannot skip it. ``kind`` is the exact
    allowlisted type (identity was judged by the caller), so reading its ``__dictoffset__`` runs no foreign code."""
    if kind.__dictoffset__ == 0:
        return True
    own = object.__getattribute__(value, "__dict__")
    return type(own) is dict and not dict.__len__(own)


def _data_state_ok(value: object, key: tuple[str, str]) -> bool:
    """True when a data row (a pydantic model, or the one plain dataclass ``Card``: all its state is its ``__dict__``) keeps nothing in the slots the scan of ``__dict__`` does not read:
    ``__pydantic_extra__`` and ``__pydantic_private__`` are None or empty, ``__pydantic_fields_set__`` is a plain
    ``set`` of ``str``."""
    if key in _DATACLASS_KEYS:
        return True
    for name in ("__pydantic_extra__", "__pydantic_private__"):
        got = object.__getattribute__(value, name)
        if got is not None and not (type(got) is dict and not dict.__len__(got)):
            return False
    fields = object.__getattribute__(value, "__pydantic_fields_set__")
    return type(fields) is set and all(type(f) is str for f in set.__iter__(fields))


def _read(container: object, budget: _Budget) -> tuple[object, ...] | None:
    """``_values`` with what is left of the budget; a container bigger than that sets ``budget.over``."""
    got = _values(container, budget.left)
    if got is None:
        budget.over = True
    return got


def _classes(keys: tuple[tuple[str, str], ...]) -> tuple[tuple[tuple[str, str], type], ...]:
    found = ((key, live_class(key)) for key in keys)
    return tuple((key, c) for key, c in found if c is not None)


def _stand_in_key(kind: type) -> tuple[str, str] | None:
    """The key of the listed class that ``kind`` IS (identity), or None."""
    for key in (*_ALLOWED, _DETECTOR_LIST):
        cls = live_class(key)
        if cls is not None and kind is cls:
            return key
    return None


def _enum_member_ok(value: object, cls: type) -> bool:
    """True when ``value`` is a real member of the enum ``cls`` (identity) and its own dictionary holds only the
    enum's own keys (an attribute hung on a member is not plain data)."""
    members = cls.__members__  # type: ignore[attr-defined]
    if not any(value is m for m in members.values()):
        return False
    own = object.__getattribute__(value, "__dict__")
    if type(own) is not dict:
        return False
    if not all(type(k) is str and k in _ENUM_MEMBER_KEYS for k in dict.keys(own)):
        return False
    return type(dict.get(own, "_value_")) is str and dict.get(own, "__objclass__", cls) is cls


def _entered(
    value: object,
    data: tuple[tuple[tuple[str, str], type], ...],
    leaf: tuple[type, ...],
    budget: _Budget,
) -> tuple[object, ...] | None:
    """What to enter inside ``value``: ``()`` for a plain atom, the values of a plain container, a data object or a
    pinned stand-in; ``None`` when the value is not plain data (it reads as real) or is bigger than what is left of
    the budget. Every class is compared by identity (``_is_one_of``). A stand-in or a data row is charged
    ``STAND_IN_WEIGHT`` nodes (its class is compared against its pin, once per question)."""
    kind = type(value)
    if _is_one_of(kind, _ATOM_TYPES):
        return () if _no_instance_state(value, kind) else None
    if _is_one_of(kind, leaf):
        return () if _enum_member_ok(value, kind) else None
    plain = _is_one_of(kind, _PLAIN_CONTAINERS) or kind is Counter
    if kind is defaultdict:
        factory = value.default_factory  # type: ignore[attr-defined]
        plain = any(factory is f for f in _DEFAULT_FACTORIES)
        if not plain:
            return None
    if plain:
        return _read(value, budget) if _no_instance_state(value, kind) else None
    for key, cls in data:
        if kind is cls:
            if not (
                budget.charge(STAND_IN_WEIGHT)
                and budget.class_ok(key)
                and _data_state_ok(value, key)
            ):
                return None
            return _read(object.__getattribute__(value, "__dict__"), budget)
    key = _stand_in_key(kind)
    if key is not None:
        if not (budget.charge(STAND_IN_WEIGHT) and budget.class_ok(key)):
            return None
        return _read(object.__getattribute__(value, "__dict__"), budget)
    return None


def _holds_real(own: object, budget: _Budget) -> bool:
    """True when the values of ``own`` (an instance dict) are not all plain data (see the module text), or when
    a container left unexplored after ``SCAN_DEPTH_VALUES`` levels holds anything but plain atoms, or when the
    budget runs out. The instance's own dictionary is level 1. A container is charged (its size) each time it is
    entered, before it is copied."""
    data, leaf = _classes(_DATA_CLASSES), tuple(c for _, c in _classes(_LEAF_CLASSES))
    first = _read(own, budget)
    if first is None or not budget.charge(len(first)):
        return True
    level: list[tuple[object, ...]] = [first]
    for _ in range(SCAN_DEPTH_VALUES):
        nxt: list[tuple[object, ...]] = []
        for values in level:
            for value in values:
                inner = _entered(value, data, leaf, budget)
                if inner is None:
                    # None is "not plain" or "bigger than what is left": the second is the over-budget outage
                    return True
                if not budget.charge(len(inner)):
                    return True
                if inner:
                    nxt.append(inner)
        level = nxt
    # fail closed: what is still unexplored after the last level may only be plain atoms (which cannot hide anything)
    return any(not _is_one_of(type(v), _ATOM_TYPES) for values in level for v in values)


def _instance_ok(obj: object, budget: _Budget) -> bool:
    # no instance dictionary is an error here, and an error reads as "not a stand-in"
    return not _holds_real(object.__getattribute__(obj, "__dict__"), budget)


def _check(obj: object, depth: int, seen: frozenset[int], budget: _Budget) -> bool:
    kind = type(obj)
    key = _stand_in_key(kind)
    if key is None:
        return False
    if not budget.charge(STAND_IN_WEIGHT):  # every visit is charged, a shared member at each visit
        return False
    if key != _DETECTOR_LIST:
        return budget.class_ok(key) and _instance_ok(obj, budget)
    if depth >= SCAN_DEPTH or id(obj) in seen:
        return False
    if not (budget.class_ok(_DETECTOR_LIST) and _instance_ok(obj, budget)):
        return False
    members = dict.get(object.__getattribute__(obj, "__dict__"), "detectors")
    if type(members) is not tuple:
        return False
    inner = seen | {id(obj)}
    return all(_check(m, depth + 1, inner, budget) for m in tuple.__iter__(members))


def verdict(obj: object) -> str:
    """``VERDICT_STAND_IN``, ``VERDICT_REAL`` or ``VERDICT_OVER_BUDGET`` (the structure is bigger than
    ``SCAN_NODES``: read as real, and named apart so a person sees the outage is size, not a service). Never raises."""
    budget = _Budget()
    try:
        if _check(obj, 0, frozenset(), budget):
            return VERDICT_STAND_IN
    except Exception:  # noqa: BLE001 - anything unreadable is not a stand-in (fail closed)
        return VERDICT_REAL
    return VERDICT_OVER_BUDGET if budget.over else VERDICT_REAL


def is_stand_in(obj: object) -> bool:
    """True only for an instance of one of the core's own stand-in classes, or of a detector list (``AnyOf``)
    whose members all are (see the module text for everything that is checked). Never raises."""
    return verdict(obj) == VERDICT_STAND_IN


def registered() -> frozenset[type]:
    """The five stand-in classes as they are found now (a class whose module is not imported is left out)."""
    found = (live_class(key) for key in _ALLOWED)
    return frozenset(c for c in found if c is not None)
