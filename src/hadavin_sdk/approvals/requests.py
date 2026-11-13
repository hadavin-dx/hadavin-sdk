"""Approval requests and decisions. A timeout escalates and never approves; no model output decides."""

from __future__ import annotations

import hashlib
import logging
import secrets
import weakref
from collections import deque
from collections.abc import Callable, Mapping
from datetime import UTC, datetime, timedelta
from types import FunctionType, MappingProxyType, MethodType
from typing import Any

from hadavin_sdk import standins
from hadavin_sdk.approvals.channel import Channel, clean
from hadavin_sdk.audit.protocol import AuditSink
from hadavin_sdk.bindguard import config_services, held_services_found
from hadavin_sdk.config import Config
from hadavin_sdk.guard.injection import Detector, injection_check
from hadavin_sdk.guard.runmap import RedactionError
from hadavin_sdk.models import (
    ApprovalDecision,
    ApprovalRequest,
    AuditEvent,
    GateDecision,
    Plan,
    canonical_json,
    now,
)
from hadavin_sdk.registry import Registry
from hadavin_sdk.store.protocol import StaleState, Store

OnDecided = Callable[[str, str, ApprovalDecision | None], object]
_LOG = logging.getLogger("hadavin_sdk.approvals")
RESEND_AFTER = timedelta(seconds=60)  # more than 2x a channel call's timeout


def make_on_decided(holder: dict[str, Any]) -> OnDecided:
    """The one ``on_decided`` function the core builds (``build()`` uses it): it hands a recorded decision to the
    runtime kept in ``holder["rt"]``. The bind guard recognises it by its code, its closure (one cell, a plain dict)
    AND what the dict holds (see ``_holder_ok``): the factory is public, so a function made by it is believed only
    while its holder is empty or holds the core's own runtime; any other callable, or a holder with anything else
    in it, can reach anything, so it is counted as held."""

    def on_decided(run_id: str, status: str, decision: ApprovalDecision | None) -> object:
        return holder["rt"].on_decided(run_id, status, decision)

    return on_decided


_ON_DECIDED_CODE = make_on_decided({}).__code__


_RUNTIME_SERVICES = (
    "store",
    "llm",
    "detector",
)  # the attributes of a core ``Runtime`` that reach a service: each must be one of the core's own stand-ins

# The other members ``Runtime.__init__`` writes. ``registry``, ``audit``, ``limits``, ``hooks`` and ``_evidence`` are each
# believed only while they are the very object ``build()`` put there (identity, recorded at the end of ``build()`` by
# ``_seal_runtime``); ``agents`` is the very set, and its text is compared too; ``_kinds`` is compared by value (a
# ``frozenset`` of text), not by identity. One line each: a member that is not listed is not compared, so every row of
# ``tests/bind_mutants.py`` that drops one line is killed by a test that replaces that member. Together with
# ``_RUNTIME_SERVICES`` these are ALL the keys of a built ``Runtime`` (a test compares the two lists with the key set
# of a built runtime, so a member added to ``Runtime.__init__`` fails that test until it is listed here).
_RUNTIME_SEALED = (
    "registry",
    "audit",
    "limits",
    "agents",
    "hooks",
    "_evidence",
    "_kinds",
)

# What a seal holds is DERIVED DATA only, never a strong reference to an object that can reach the runtime (the hooks
# reach it through ``request_approval`` -> ``Approvals`` -> ``on_decided`` -> the holder -> the runtime). Each object
# is written down as a "mark" (``_mark``): a weak reference when Python allows one; text, bytes and numbers by value
# (text and bytes as a keyed digest, so no second copy of a secret such as ``restored_key`` is kept); the exact class
# for a container; and (id, class) for an object that cannot be weakly referenced.
_MARK_ATOM, _MARK_WEAK, _MARK_KIND, _MARK_ID, _MARK_STRONG, _MARK_SLOT, _MARK_DIGEST = (
    0,
    1,
    2,
    3,
    4,
    5,
    6,
)
_DIGEST_KEY = secrets.token_bytes(
    16
)  # per process: a digest of a recorded text is not comparable across processes
_ATOM_KINDS: tuple[type, ...] = (str, int, float, bool, bytes, type(None))
_STATE_KINDS: tuple[type, ...] = (
    set,
    frozenset,
    deque,
)  # change in place while the server works: the class counts, the content is not read
_WALK_DEPTH = 4  # levels entered below a hook field (functions, cells, bound methods, dicts, lists)
_WALK_NODES = (
    5_000  # objects written down per runtime; more is refused at build and read as changed later
)

# runtime -> (instance keys, {member: mark} (the agents' own set is held as it is: text only, it reaches nothing), the
# agents as a frozenset copy, the stored kinds, the marks of the hooks' own (name, value) walk, the hooks class, the
# marks of the walk of ``limits``, ``audit``, ``registry`` and ``_evidence`` (``_member_fields``)). Weak, and its value
# holds only marks (a weak reference, a plain text or number, a class): a runtime that is gone is collected (tested
# with ``gc``). Written by ``_seal_runtime`` (``build()``) only.
_RUNTIME_SEALS: weakref.WeakKeyDictionary[object, tuple] = weakref.WeakKeyDictionary()
_MEMBERS_WALKED = ("limits", "audit", "registry", "_evidence")


class _Over(Exception):
    """More than ``_WALK_NODES`` objects would be written down or compared."""


class _Changed(Exception):
    """An object met by the walk is not the one that was written down (or there are more or fewer of them)."""


def _digest(value: str | bytes) -> bytes:
    """A keyed digest of exact text or bytes (the builtin methods only: no foreign ``encode`` runs)."""
    raw = str.encode(value, "utf-8", "surrogatepass") if type(value) is str else value
    return hashlib.blake2b(raw, key=_DIGEST_KEY, digest_size=16).digest()


def _mark(obj: object) -> tuple:
    """One object written down so it can be recognised later without holding it: see ``_MARK_*``."""
    kind = type(obj)
    if kind is str or kind is bytes:
        return (_MARK_DIGEST, (kind, _digest(obj)))
    if any(kind is k for k in _ATOM_KINDS):
        return (_MARK_ATOM, obj)
    if any(kind is k for k in _STATE_KINDS) or kind is dict or kind is list or kind is tuple:
        return (_MARK_KIND, kind)  # its content is walked; the container itself may be rebuilt
    try:
        return (_MARK_WEAK, weakref.ref(obj))
    except (
        TypeError
    ):  # no ``__weakref__`` slot (``Approvals``): the object is kept alive by the app, id and class
        return (_MARK_ID, (id(obj), kind))


def _is_slot_value(obj: object) -> bool:
    """A value that moves in use: text, a number, ``None`` or a set or deque (the class of the container, not its content)."""
    kind = type(obj)
    return any(kind is k for k in _ATOM_KINDS + _STATE_KINDS)


def _mark_matches(mark: tuple, obj: object) -> bool:
    """True when ``obj`` is the very object (or, for a container, the very class) ``mark`` was made from. Text and
    numbers are compared by exact class and value (builtin comparison only: no foreign ``__eq__`` runs). A slot mark
    (``_MARK_SLOT``) holds for any text, number, ``None``, set or deque and for nothing else."""
    tag, held = mark
    kind = type(obj)
    if tag == _MARK_ATOM:
        return kind is type(held) and (obj is held or obj == held)
    if tag == _MARK_KIND:
        return kind is held
    if tag == _MARK_DIGEST:
        return kind is held[0] and _digest(obj) == held[1]
    if tag == _MARK_WEAK:
        target = (
            held()
        )  # a reference that is dead answers None: it must not match a ``None`` found there now
        return target is not None and target is obj
    if tag == _MARK_STRONG:
        return held is obj
    if tag == _MARK_SLOT:
        return _is_slot_value(obj)
    return held == (id(obj), kind)


class _Walk:
    """The order in which the objects of a runtime are met. Two uses: ``marks is None`` writes every object down
    (``build()``); otherwise each object is COMPARED with its mark at the moment it is met, BEFORE anything is read
    from it, so an object that is not the recorded one is never entered (a replacement whose class has its own
    ``__dict__`` property or ``__getattr__`` runs no code). More than ``_WALK_NODES`` objects raise ``_Over`` inside
    the loops, so one request never iterates a huge container in full."""

    __slots__ = ("marks", "out", "pos")

    def __init__(self, marks: tuple[tuple, ...] | None = None) -> None:
        self.marks = marks
        self.out: list[tuple] = []
        self.pos = 0

    def add(self, obj: object) -> None:
        if self.pos >= _WALK_NODES:
            raise _Over
        if self.marks is None:
            self.out.append(_mark(obj))
        else:
            if self.pos >= len(self.marks) or not _mark_matches(self.marks[self.pos], obj):
                raise _Changed
        self.pos += 1

    def slot(self, obj: object) -> None:
        """Write down (or check) that a field holds a value that moves in use: any text, number, ``None``, set or deque."""
        if self.pos >= _WALK_NODES:
            raise _Over
        if self.marks is None:
            self.out.append((_MARK_SLOT, None))
        elif self.pos >= len(self.marks) or not (
            self.marks[self.pos][0] == _MARK_SLOT and _is_slot_value(obj)
        ):
            raise _Changed
        self.pos += 1

    def done(self) -> None:
        if self.marks is not None and self.pos != len(self.marks):
            raise _Changed


def _walk(obj: object, w: _Walk, depth: int, entered: bool) -> None:
    """Write down or compare (in a fixed order) every object whose identity must not change after ``build()``: ``obj``
    itself and what it carries that is code or points to code. A function: its code, its defaults, its keyword
    defaults, its own dictionary (``__wrapped__`` lives there) and the contents of its closure cells (a cell's content
    can be rewritten: ``cell.cell_contents = x``); a bound method: its function and its object; a dict, list or
    tuple: its keys and items. ``entered``: the instance dictionary of this object is walked too (a hook field itself
    and the object of a bound method: the ``ToolBox`` and the ``Executor``), where a value that changes in use (text,
    numbers, sets, deques) is a slot mark. Objects met deeper (a channel in a closure cell) are written down by
    identity only: their own state moves in use and is judged where they are held. Exact classes only, read with the
    builtin methods, so no foreign code runs. An object is compared before it is entered."""
    w.add(obj)
    if depth >= _WALK_DEPTH:
        return
    kind = type(obj)
    if kind is FunctionType:
        w.add(obj.__code__)
        _walk(obj.__defaults__, w, depth + 1, False)
        _walk(obj.__kwdefaults__, w, depth + 1, False)
        _walk(obj.__dict__, w, depth + 1, False)
        for cell in obj.__closure__ or ():
            try:
                content = cell.cell_contents
            except ValueError:  # an empty cell
                content = _EMPTY_CELL
            _walk(content, w, depth + 1, False)
    elif kind is MethodType:
        _walk(obj.__func__, w, depth + 1, False)
        _walk(obj.__self__, w, depth + 1, True)
    elif kind is dict:
        for key, value in dict.items(obj):
            w.add(key)
            _walk(value, w, depth + 1, False)
    elif kind is list or kind is tuple:
        for item in list.__iter__(obj) if kind is list else tuple.__iter__(obj):
            _walk(item, w, depth + 1, False)
    elif entered:
        _member_fields(obj, w, depth + 1, deep=True)


_EMPTY_CELL = object()  # what ``_walk`` writes for a closure cell that holds nothing


def _instance_dict(obj: object) -> dict | None:
    try:
        own = object.__getattribute__(obj, "__dict__")
    except AttributeError:
        return None
    return own if type(own) is dict else None


def _member_fields(obj: object, w: _Walk, depth: int, deep: bool) -> None:
    """The instance dictionary of ``obj`` (which ``w.add`` has just compared, so it is the recorded object): its class,
    each key, and each value (``deep``: walked like a hook field; else by identity only, the container kept by class).
    A value that moves in use is a slot mark. The class is compared first: ``__class__`` can be assigned, and a
    class with its own ``__dict__`` property must not run."""
    w.add(type(obj))
    own = _instance_dict(obj)
    if own is None:
        w.add(own)
        return
    w.add(_FIELDS_MARK)
    for key, value in dict.items(own):
        w.add(key)
        if _is_slot_value(value):
            w.slot(value)
        elif deep:
            _walk(value, w, depth, False)
        else:
            w.add(value)


_FIELDS_MARK = object()  # separates the class of an entered object from its fields


def _walk_fields(fields: dict, w: _Walk) -> None:
    """``_walk`` of the instance dictionary of a ``Hooks``: each field is entered (``entered=True``)."""
    w.add(fields)
    for name, value in dict.items(fields):
        w.add(name)
        _walk(value, w, 1, True)


def _marks_of(fields: dict) -> tuple[tuple, ...]:
    w = _Walk()
    _walk_fields(fields, w)
    return tuple(w.out)


def _members_walk(own: dict, w: _Walk) -> None:
    """``limits``, ``audit``, ``registry`` and ``_evidence`` of a runtime: each is compared (identity) and only then are
    its own fields read (``_member_fields``, identity of each value). A ``Limits`` reaches ``store``, ``audit`` and
    ``registry`` from ``handle``, ``tick`` and ``on_decided``; an audit sink reaches its own store; ``Registry`` and
    the evidence settings are read for every run."""
    for name in _MEMBERS_WALKED:
        member = dict.get(own, name)
        w.add(member)
        _member_fields(member, w, 1, deep=False)


def _marks_match(marks: tuple[tuple, ...], fields: dict) -> bool:
    w = _Walk(marks)
    try:
        _walk_fields(fields, w)
        w.done()
    except (_Over, _Changed):
        return False
    return True


def _seal_runtime(runtime: object) -> None:
    """Record what ``build()`` made a ``Runtime`` hold: the names its ``__init__`` wrote (its instance dictionary keys),
    a mark of every member in ``_RUNTIME_SEALED`` and, for its ``hooks``, a mark of every field AND of what each field
    carries (``_walk``: the keys and the item identities of ``tools``, the members of the toolbox, the code and the
    closure cells of ``post_card`` and ``request_approval``), the fields of ``limits``, ``audit``, ``registry`` and
    ``_evidence`` (``_members_walk``) and its agents. A runtime that is not sealed (made by hand) is never believed
    (``_runtime_ok``). Private: only ``app.build`` calls it, once the runtime is complete; it refuses (``TypeError``) an
    object that is not exactly the core's ``Runtime``, and (``ValueError``) a runtime with more than ``_WALK_NODES``
    objects to check, so the size outage shows at build, not at the first request."""
    if type(runtime) is not standins.live_class(standins.RUNTIME):
        raise TypeError("only a core Runtime can be sealed")
    own = object.__getattribute__(runtime, "__dict__")
    hooks = dict.get(own, "hooks")
    agents = dict.get(own, "agents")
    try:
        hook_marks = _marks_of(object.__getattribute__(hooks, "__dict__"))
        member_walk = _Walk()
        _members_walk(own, member_walk)
    except _Over:
        raise ValueError(
            f"too many hook objects to check (over {_WALK_NODES}): the seal is over budget, so the runtime is "
            "refused at build, not at the first request"
        ) from None
    _RUNTIME_SEALS[runtime] = (
        frozenset(dict.keys(own)),
        {
            name: (_MARK_STRONG, dict.get(own, name))
            if name == "agents"
            else _mark(dict.get(own, name))
            for name in _RUNTIME_SEALED
            if name != "_kinds"
        },
        frozenset(set.__iter__(agents)),
        dict.get(own, "_kinds"),
        hook_marks,
        type(hooks),
        tuple(member_walk.out),
    )


def _members_unchanged(own: dict, sealed: tuple) -> bool:
    w = _Walk(sealed[6])
    try:
        _members_walk(own, w)
        w.done()
    except (_Over, _Changed):
        return False
    return True


def _hooks_unchanged(hooks: object, sealed: tuple) -> bool:
    """The hooks are the very object ``build()`` made: exact class (pinned), the same field names holding the same
    objects, and what the fields carry unchanged since the seal (``_walk``): a ``hold_run_ids``, ``execute`` or
    ``post_card`` put in later, a tool added to or replaced in ``hooks.tools``, a member of the toolbox replaced, the
    code of a hook function or the content of one of its closure cells rewritten, is not the wiring ``build()``
    made. What stays outside this model (code in the same process that rewrites a module, ``sys.modules``, the guard
    itself or uses ``object.__setattr__`` on a sealed object) is listed in the CHANGELOG."""
    if type(hooks) is not sealed[5] or not standins.is_pinned_instance(hooks, standins.HOOKS):
        return False
    fields = _instance_dict(hooks)
    return fields is not None and _marks_match(sealed[4], fields)


def _kinds_unchanged(kinds: object, was: object) -> bool:
    """``Runtime._kinds`` is a ``frozenset`` of text made from the config: believed while it is an exact ``frozenset`` of
    exact ``str`` that equals the one ``build()`` sealed (builtin comparison only: an object with its own
    ``__contains__`` is refused)."""
    return (
        type(kinds) is frozenset
        and type(was) is frozenset
        and all(type(k) is str for k in frozenset.__iter__(kinds))
        and frozenset.__eq__(kinds, was) is True
    )


def _runtime_ok(runtime: object, scan: standins.Scan | None = None) -> bool:
    """True only for a runtime ``build()`` made and sealed: an instance of exactly the core's ``Runtime`` class,
    unchanged since it was pinned (``standins.is_pinned_instance``, pinned when its module is loaded), whose instance
    dictionary holds exactly the names ``__init__`` wrote (an ``rt.on_decided = f`` or ``rt.extra = f`` (any extra name) on the instance
    would shadow the pinned class method: such a key, or a missing one, is refused), whose ``registry``, ``audit``,
    ``limits``, ``agents``, ``hooks`` and ``_evidence`` are the objects ``build()`` put there (and ``_kinds`` the same
    set of names), whose hooks carry what ``build()`` gave them (``_hooks_unchanged``), and whose ``store``, ``llm`` and
    ``detector`` are each one of the core's own stand-ins (a runtime made by hand with a real store or model is real).
    ``scan`` is the request's one scan (see ``standins.Scan``). An ``Approvals`` made by hand does not get this belief
    at all (see ``_holder_ok``)."""
    try:
        if not standins.is_pinned_instance(runtime, standins.RUNTIME):
            return False
        own = object.__getattribute__(runtime, "__dict__")
        sealed = _RUNTIME_SEALS.get(runtime)
        if type(own) is not dict or sealed is None:
            return False
        keys = tuple(dict.keys(own))
        methods = vars(type(runtime))
        if (
            not all(type(k) is str and k not in methods for k in keys)
            or frozenset(keys) != sealed[0]
        ):
            return False
        members = sealed[1]
        if not all(_mark_matches(members[name], dict.get(own, name)) for name in members):
            return False
        agents = dict.get(own, "agents")
        if type(agents) is not set or not all(type(a) is str for a in set.__iter__(agents)):
            return False
        if frozenset(set.__iter__(agents)) != sealed[2]:
            return False
        if not _kinds_unchanged(dict.get(own, "_kinds"), sealed[3]):
            return False
        if not _members_unchanged(own, sealed):
            return False
        if not _hooks_unchanged(dict.get(own, "hooks"), sealed):
            return False
        return all(standins.is_stand_in(dict.get(own, name), scan) for name in _RUNTIME_SERVICES)
    # anything unreadable is not the core's runtime (a hostile object may raise anything)
    except standins.READ_ERRORS:
        return False


def _holder_ok(holder: object, built: bool, scan: standins.Scan | None = None) -> bool:
    """True only for a plain ``dict`` that is empty, or (only when the ``Approvals`` was made by ``build()``) whose one
    entry under ``rt`` is a runtime the core made (``_runtime_ok``). The one key is read with the builtin dict
    methods and compared as an exact ``str`` by identity of its type, never with ``==`` (a key that is a ``str``
    subclass with its own ``__eq__`` is foreign code); a one-entry dict under another key has no ``rt`` and is counted."""
    if type(holder) is not dict:
        return False
    size = dict.__len__(holder)
    if size == 0:
        return True
    if size != 1 or not built:
        return False
    key = next(dict.__iter__(holder))
    # ``key`` is an exact ``str`` there: its ``!=`` is the builtin one
    if type(key) is not str or key != "rt":
        return False
    return _runtime_ok(dict.__getitem__(holder, key), scan)


_NONE = object()  # the marker ``_one_cell`` answers when the function is not made from the code


def _one_cell(func: object, code: object) -> object:
    """The one closure cell's content of a function made from ``code`` (identity of the code), else the marker
    ``_NONE``. Never raises (an empty cell is a ``ValueError``)."""
    try:
        if type(func) is not FunctionType or func.__code__ is not code:
            return _NONE
        cells = func.__closure__
        if cells is None or len(cells) != 1:
            return _NONE
        return cells[0].cell_contents
    # the one error this read can raise from an exact function: an empty cell is a ValueError
    except ValueError:
        return _NONE


def _seal_over_budget(func: object, built: bool) -> bool:
    """True when ``func`` is the core's ``on_decided`` of a built, sealed runtime whose walk now meets more than
    ``_WALK_NODES`` objects: the size outage, named apart from "an ``on_decided`` that is not the core's". Asked only
    after the runtime was refused, so its cost is not paid by a served request. Never raises."""
    try:
        holder = _one_cell(func, _ON_DECIDED_CODE)
        if not built or type(holder) is not dict or dict.__len__(holder) != 1:
            return False
        key = next(dict.__iter__(holder))
        if (
            type(key) is not str or key != "rt"
        ):  # an exact text only: a key of a subclass runs its own ``__eq__``
            return False
        runtime = dict.__getitem__(holder, key)
        sealed = _RUNTIME_SEALS.get(runtime)
        if sealed is None or not standins.is_pinned_instance(runtime, standins.RUNTIME):
            return False
        own = object.__getattribute__(runtime, "__dict__")
        hooks = dict.get(own, "hooks")
        for marks, walk in (
            (sealed[4], lambda w: _walk_fields(object.__getattribute__(hooks, "__dict__"), w)),
            (sealed[6], lambda w: _members_walk(own, w)),
        ):
            try:
                walk(_Walk(marks))
            except _Over:
                return True
            except _Changed:
                continue
    # an unreadable runtime is not "over budget"; it stays counted as held
    except standins.READ_ERRORS:
        return False
    return False


def _is_core_on_decided(func: object, built: bool, scan: standins.Scan | None = None) -> bool:
    """True only for a function made by ``make_on_decided`` (identity of its code) whose holder is judged by
    ``_holder_ok`` (``built``: the ``Approvals`` was made by ``build()``)."""
    cell = _one_cell(func, _ON_DECIDED_CODE)
    return cell is not _NONE and _holder_ok(cell, built, scan)


def fixed_clock(moment: datetime) -> Callable[[], datetime]:
    """A clock that always answers ``moment`` (tests move time with it). The bind guard recognises it by its code
    and its closure (one cell, an exact ``datetime``), so a test can use a fake clock and still be served."""

    def clock() -> datetime:
        return moment

    return clock


# a moment only to make the factory's code object
_FIXED_CLOCK_CODE = fixed_clock(datetime.min.replace(tzinfo=UTC)).__code__
_NOW_CODE = (
    now.__code__
)  # ``models.now`` is the same function object after ``now.__code__ = ...``: its code is pinned
# the two names ``models.now`` reads from its module (``datetime.now(UTC)``): pinned by identity too, so a replaced
# ``models.datetime`` or ``models.UTC`` (foreign code run before the signature is checked) is seen. Read from the
# function's own globals dictionary with the builtin ``dict.get``.
_NOW_DATETIME = dict.get(now.__globals__, "datetime")
_NOW_UTC = dict.get(now.__globals__, "UTC")


def _is_core_clock(func: object) -> bool:
    """True only for ``models.now`` (its code unchanged since this module was imported) or a clock made by
    ``fixed_clock`` whose moment is a ``datetime`` ``standins.plain_datetime`` accepts (exact type, ``tzinfo`` None or
    ``datetime.UTC``: an aware moment calls ``tzinfo.utcoffset`` in ``receive``, so a ``tzinfo`` that is a class with
    its own code is not believed). Any other callable is run before the signature is checked and can hold anything,
    so it is counted."""
    if func is now:
        names = now.__globals__
        return (
            now.__code__ is _NOW_CODE
            and dict.get(names, "datetime") is _NOW_DATETIME
            and dict.get(names, "UTC") is _NOW_UTC
        )
    moment = _one_cell(func, _FIXED_CLOCK_CODE)
    return moment is not _NONE and standins.plain_datetime(moment)


# Only ``app.build`` holds this: an ``Approvals`` made with it counts as built by ``build()`` (its audit sink and
# registry are not named as held). Python cannot hide a module name from code in the same process; the point is that
# the claim is no longer a plain argument value (``overrides={}``) that any caller can write.
_BUILD_TOKEN = object()


WARNING = "WARNING: the inputs read like instructions to an AI. Check them before approving. "


def summary(plan: Plan, detector: Detector | None = None) -> str:
    """Template-built, never by the model; inputs redacted and link-free. Inputs that read like instructions
    (the model copied them from a document) get a warning so a person does not approve them on autopilot."""
    inputs = canonical_json(plan.inputs)
    flagged = detector is not None and injection_check(detector, inputs, "approval_summary").flagged
    try:
        return clean(
            f"{WARNING if flagged else ''}{plan.agent_id} asks to run {plan.action_id} "
            f"v{plan.action_version} ({plan.risk_class}) on {plan.target.system}. Inputs: {inputs}. "
            f"Expected: {plan.expected_outcome}. Plan {plan.hash()[:12]}."
        )
    except (
        RedactionError
    ):  # inputs too large to redact (or nested too deep): the approver still sees what and where
        return clean(
            f"{WARNING if flagged else ''}{plan.agent_id} asks to run {plan.action_id} "
            f"v{plan.action_version} ({plan.risk_class}) on {plan.target.system}. "
            f"Inputs: (too large to show here). Plan {plan.hash()[:12]}."
        )


class Approvals:
    """Decisions must come from a channel's verified parse (``receive``), never from caller-supplied fields:
    ``decide`` is the internal step after verification and the one tests drive with a trusted fake.

    Everything the object holds (``store``, ``audit``, ``registry``, ``channel``, ``on_decided``, ``detector``,
    ``config``, ``overrides``, and the frozen facts) is set once, when the object is made; only ``clock`` can be set
    again (tests move time). ``__setattr__`` refuses every other assignment (a plain ``a._channel = x``, a private
    slot name that is already set, ``a.__class__ = Other``, any new name) with an ``AttributeError``. The attributes
    are slots, so ``vars(a)`` raises ``TypeError`` and the object cannot be weakly referenced (``weakref.ref(a)``
    raises ``TypeError``: there is no ``__weakref__`` slot). ``del a._channel`` is refused too (``__delattr__``
    always raises). ``object.__setattr__(a, "_channel", x)`` and ``object.__delattr__(a, "_channel")`` are the ways left; they
    are caught by the receiver, which asks again at every request on a bind other computers can reach with no reason
    given: the exact class of ``a``, that the ``Approvals`` class is unchanged since it was pinned, and what it holds
    now (``real_now``; a missing slot is answered 503). A copy of an ``Approvals`` (``copy.copy``, ``copy.deepcopy``,
    pickle) is refused with a ``TypeError``: a copy would duplicate the frozen facts and the set-once objects."""

    __slots__ = (
        "_audit_sink",
        "_channel",
        "_clock",
        "_config",
        "_config_facts",
        "_detector",
        "_hand_built",
        "_on_decided",
        "_overrides",
        "_registry",
        "_store",
    )

    def __init__(
        self,
        store: Store,
        audit: AuditSink,
        registry: Registry,
        channel: Channel,
        on_decided: OnDecided,
        clock: Callable[[], datetime] = now,
        detector: Detector | None = None,
        config: Config | None = None,
        overrides: Mapping[str, object] | None = None,
        *,
        _built_by: object = None,
    ) -> None:
        self._store, self._audit_sink, self._registry, self._channel = (
            store,
            audit,
            registry,
            channel,
        )
        self._on_decided, self._clock, self._detector = on_decided, clock, detector
        # The deployment config these approvals were built from, and the objects ``build()`` was handed in place of
        # configured ones (name -> object). Both are set once and read-only (no setter): ``receiver.serve`` checks
        # the config is the one it was given and counts what the approvals really hold, so neither can be swapped
        # for a stand-in after construction (None: built by hand, never served). What the config reaches is read
        # NOW and kept (``_config_facts``): the containers of a ``Config`` can be changed after it is built.
        self._config = config
        self._overrides = MappingProxyType(dict(overrides or {}))
        self._config_facts = config_services(config) if config is not None else ()
        # only ``build()`` holds the token: an object made with ``overrides={}`` from outside is hand-built
        self._hand_built = _built_by is not _BUILD_TOKEN

    @property
    def store(self) -> Store:
        return self._store

    @property
    def channel(self) -> Channel:
        return self._channel

    @property
    def detector(self) -> Detector | None:
        return self._detector

    @property
    def audit(self) -> AuditSink:
        return self._audit_sink

    @property
    def registry(self) -> Registry:
        return self._registry

    @property
    def on_decided(self) -> OnDecided:
        return self._on_decided

    @property
    def clock(self) -> Callable[[], datetime]:
        return self._clock

    @clock.setter
    def clock(
        self, value: Callable[[], datetime]
    ) -> None:  # tests move time; the bind guard judges the clock it holds at every question
        object.__setattr__(self, "_clock", value)

    def __setattr__(self, name: str, value: object) -> None:
        """Set once: a private slot can be written only while it is still empty (the constructor), and ``clock`` is
        the one name that can be set again. ``__class__`` and every other name are refused."""
        if name == "clock":
            object.__setattr__(self, name, value)  # the property setter
            return
        if name in Approvals.__slots__:
            try:
                object.__getattribute__(self, name)
            except AttributeError:  # empty: this is the constructor writing it for the first time
                object.__setattr__(self, name, value)
                return
        raise AttributeError(
            f"an Approvals is set once: {name!r} cannot be set (only 'clock' can be set again)"
        )

    def __delattr__(self, name: str) -> None:
        """Nothing is ever deleted: ``del a._channel`` followed by a new assignment would undo the set-once rule."""
        raise AttributeError(f"an Approvals is set once: {name!r} cannot be deleted")

    @property
    def config(self) -> Config | None:
        return self._config

    @property
    def config_facts(self) -> tuple[str, ...]:
        """What the config reached that is real, read when the approvals were made (never read again)."""
        return self._config_facts

    @property
    def overrides(self) -> Mapping[str, object]:
        """The objects ``build()`` was handed in place of configured ones (read-only)."""
        return self._overrides

    def held_services(self, scan: standins.Scan | None = None) -> dict[str, object]:
        """What these approvals really hold that can reach a service, read when asked: the build overrides, and the
        channel, the detector and the store as they are now. The bind guard (``bindguard.held_services_found``)
        counts each one that is not one of the core's own stand-ins. Approvals made by hand (not by ``build()``)
        also name their audit sink and registry: nothing says those are stand-ins. ``on_decided`` is named unless it
        is the function ``make_on_decided`` builds with an empty holder or (approvals made by ``build()`` only) the core
        runtime in it (``_runtime_ok``), and ``clock`` is named unless it is ``models.now`` or a ``fixed_clock`` of a
        plain ``datetime`` (``standins.plain_datetime``). ``scan``: the one scan of a request (``real_now`` makes it), shared
        with ``bindguard.held_services_found`` so the store the runtime holds and the store named here are read once."""
        # read through the same accessors the runtime uses (``self.channel`` and so on), never through the private
        # slots: a replaced accessor and the slot behind it cannot give two answers
        held: dict[str, object] = dict(self.overrides)
        live = {"channel": self.channel, "detector": self.detector, "store": self.store}
        for name, obj in live.items():
            # a given object and a different one now in its place are both counted (neither hides the other)
            if name in held and held[name] is not obj:
                held[f"{name}_given_to_build"] = held[name]
            held[name] = obj
        if self._hand_built:
            held["audit"], held["registry"] = self.audit, self.registry
        if not _is_core_on_decided(
            self.on_decided, not self._hand_built, scan
        ):  # a callable run after a valid signature can hold anything
            over = _seal_over_budget(self.on_decided, not self._hand_built)
            held["seal_over_budget" if over else "on_decided"] = self.on_decided
        if not _is_core_clock(self.clock):  # ``receive`` runs it before the signature is checked
            held["clock"] = self.clock
        return held

    def real_now(self) -> tuple[str, ...]:
        """What these approvals reach that is real, now: the facts of the config frozen at construction, and the held
        objects as they are at this moment. The receiver asks this at every request on a bind other computers can
        reach with no reason given (called as ``Approvals.real_now(a)``, so a subclass cannot answer for itself)."""
        scan = (
            standins.Scan()
        )  # ONE budget for the whole request, and an object looked at twice is read once
        return self.config_facts + held_services_found(Approvals.held_services(self, scan), scan)

    def __deepcopy__(self, memo: object) -> object:
        raise TypeError("an Approvals cannot be copied: it holds set-once objects and frozen facts")

    def __reduce_ex__(self, protocol: object) -> object:
        raise TypeError(
            "an Approvals cannot be copied or pickled: it holds set-once objects and frozen facts"
        )

    def receive(
        self, headers: Mapping[str, str], body: bytes, *, record_only: bool = False
    ) -> tuple[bool, str]:
        """Entry point for a channel callback: the channel verifies the request and names the approver.
        The HTTP receiver passes ``record_only=True``: it records and answers fast; ``tick`` runs the plan."""
        # ORDER: ``self.clock()`` and ``.timestamp()`` run BEFORE the signature is checked, so on a bind other computers
        # can reach nothing may be called here that the guard did not judge: the receiver's per-request check
        # (``real_now``) refuses a clock that is not ``models.now`` or a ``fixed_clock`` of a plain ``datetime``
        d = self.channel.parse_decision(headers, body, self.clock().timestamp())
        if d is None:
            return False, "bad_signature"
        return self.decide(d, record_only=record_only)

    def _audit(self, req: ApprovalRequest, operation: str, principal: str, **kw) -> None:
        self.audit.write_outcome(
            AuditEvent(
                run_id=req.run_id,
                domain="approval",
                operation=operation,
                principal=principal,
                source=self.channel.name,
                object_ref=req.approval_id,
                inputs_hash=req.plan_hash,
                **kw,
            )
        )

    def request(self, plan: Plan, decision: GateDecision, requested_by: str) -> ApprovalRequest:
        chain = self.registry.chains[self.registry.contracts[plan.action_id].chain_id]
        req = ApprovalRequest(
            run_id=plan.run_id,
            plan_hash=decision.plan_hash,
            risk_class=plan.risk_class,
            chain_id=chain.id,
            steps=chain.steps,
            step_expires_at=self.clock() + timedelta(seconds=chain.steps[0].timeout_s),
            requested_by=requested_by,
            summary=summary(plan, self.detector),
        )
        self.store.save_approval_request(req)
        req = self._send(req, chain.steps[0].approver_ids)
        self._audit(req, "request", requested_by, result="PENDING")
        return req

    def _send(self, req: ApprovalRequest, approver_ids: list[str]) -> ApprovalRequest:
        """Send, then record `sent_at` and the channel's message id. A failed send leaves `sent_at` empty,
        the request stays PENDING and ``resend_unsent`` (a tick step) tries again."""
        try:
            ref = self.channel.send(req, approver_ids)
        except Exception as exc:  # noqa: BLE001 - any channel failure: keep the request, resend later
            _LOG.warning(
                "approval %s: channel send failed (%s); tick will resend",
                req.approval_id,
                type(exc).__name__,
            )
            return req
        sent = req.model_copy(update={"sent_at": self.clock(), "channel_ref": ref})
        try:
            self.store.update_approval_request(sent, req.status, req.current_step)
        except StaleState:  # decided or escalated meanwhile: the newer row wins
            return self.store.get_approval_request(req.approval_id)
        return sent

    def resend_unsent(self, at: datetime | None = None) -> list[str]:
        """PENDING requests whose send failed (`sent_at` empty) for at least RESEND_AFTER since their step
        began (a send still in flight is left alone): send them again. Returns approval ids."""
        at = at or self.clock()
        sent = []
        for req in self.store.list_approvals({"PENDING"}):
            step = req.steps[req.current_step]
            began = req.step_expires_at - timedelta(seconds=step.timeout_s)
            due = req.sent_at is None and at - began >= RESEND_AFTER
            if due and self._send(req, step.approver_ids).sent_at:
                sent.append(req.approval_id)
        # ponytail: a send that reached Slack but timed out on the reply is sent again (a duplicate message;
        # both carry the same valid buttons). An idempotency key needs the channel to support one.
        return sent

    def decide(self, d: ApprovalDecision, *, record_only: bool = False) -> tuple[bool, str]:
        """Check and record one decision. ``record_only``: leave running the plan to ``tick`` reconcile."""
        req = self.store.get_approval_request(d.approval_id)
        reason = None
        if req.status != "PENDING":
            reason = "not_pending"
        elif d.step != req.current_step:
            reason = "old_step"
        elif self.clock() >= req.step_expires_at:
            reason = "step_expired"  # the sweep escalates it; a late decision never runs the plan
        elif d.approver_id not in req.steps[req.current_step].approver_ids:
            reason = "not_an_approver_for_this_step"
        elif d.approver_id == req.requested_by:
            reason = "requester_cannot_approve"
        elif d.plan_hash != req.plan_hash:
            reason = "plan_hash_mismatch"
        if reason:
            self._audit(req, "decide", d.approver_id, decision=d.decision, error_code=reason)
            return False, reason
        status = "APPROVED" if d.decision == "approve" else "REJECTED"
        new = req.model_copy(update={"status": status})
        try:
            # One atomic write: the decision (one per approval step) and the status compare-and-set. Of two
            # racing clicks, or a click racing the sweep, exactly one is kept, and nothing of the loser.
            self.store.record_decision(d, new, "PENDING", req.current_step)
        except StaleState:
            return False, "stale"
        self._audit(req, "decide", d.approver_id, decision=d.decision, result=status)
        if (
            record_only
        ):  # the receiver must answer fast: tick reconcile updates the message and runs it
            return True, status.lower()
        self.update_message(new)
        self.on_decided(req.run_id, status, d)
        return True, status.lower()

    def update_message(self, req: ApprovalRequest) -> None:
        """Show the outcome in the channel; a failure is logged (the decision is already recorded)."""
        try:
            self.channel.update(req)
        except Exception as exc:  # noqa: BLE001 - a stale message is cosmetic
            _LOG.warning(
                "approval %s: channel update failed (%s)", req.approval_id, type(exc).__name__
            )

    def sweep(self, at: datetime | None = None) -> list[str]:
        """Escalate each due request one step; after the last step it expires. Returns approval ids touched."""
        at = at or self.clock()
        touched = []
        for req in self.store.list_due_approvals(at):
            nxt = req.current_step + 1
            if nxt < len(req.steps):
                new = req.model_copy(
                    update={
                        "current_step": nxt,
                        "step_expires_at": at + timedelta(seconds=req.steps[nxt].timeout_s),
                        "sent_at": None,  # the next step's approvers have not been asked yet
                    }
                )
                status = "PENDING"
            else:
                new = req.model_copy(update={"status": "EXPIRED"})
                status = "EXPIRED"
            try:
                self.store.update_approval_request(new, "PENDING", req.current_step)
            except StaleState:
                continue
            self._audit(req, "sweep", "system", result=status, decision=f"step{new.current_step}")
            if status == "PENDING":
                self._send(new, req.steps[nxt].approver_ids)
            else:
                self.update_message(new)
                try:
                    self.channel.notify(
                        req.requested_by,
                        f"Approval {req.approval_id} expired with no decision. Nothing was run.",
                    )
                    self.on_decided(req.run_id, "EXPIRED", None)
                except Exception as exc:  # noqa: BLE001 - tick reconcile ends the run if this failed
                    _LOG.warning(
                        "approval %s: expiry follow-up failed (%s)",
                        req.approval_id,
                        type(exc).__name__,
                    )
            touched.append(req.approval_id)
        return touched
