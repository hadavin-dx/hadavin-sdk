"""Turn any exception into a diagnostic: a code from a closed list, a step, a ``file.py:line`` locator and a few closed facts.

The diagnostic never holds text that came from a document, a model, a person or a library. ``diagnose`` reads no ``str``, ``repr``,
``args``, ``__notes__``, ``__cause__``, ``__context__`` or group message of the exception; from pydantic it reads only ``error_count()``
and the ``"type"`` key of ``errors(include_url=False, include_context=False, include_input=False)`` (one helper, ``_error_types``);
from a JSON error only ``pos``; from an operating-system error only ``errno`` and ``winerror``; from a database error only ``sqlstate``.
``render`` is the only function that turns a diagnostic into a line of plain ASCII (Grammar A):

    <kind>: diag_v=1 code=<code> step=<step> at=<locator> fp=<8 hex>[ key=value ...]

No file contents, network, environment, clock or database access at run time. The only state is a counter of guarded failures and a
read of ``sys.modules`` to check that a frame belongs to an imported module. Nothing in this module is wired into
the places that write errors today; that is the job of a later step (P5b3).
"""

from __future__ import annotations

import builtins
import hashlib
import json
import os
import re
import socket
import sys
import threading
from collections import deque
from collections.abc import Mapping
from dataclasses import dataclass
from typing import Final

from pydantic import ValidationError as _ValidationError

from hadavin_sdk import defaults
from hadavin_sdk.codes import (
    FACT_BOUNDS,
    FACT_PRIORITY,
    FOREIGN_PACKAGES_OK,
    OWN_CODES,
    VALIDATION_OTHER,
    VALIDATION_TYPES,
    Code,
    FactKey,
    Phase,
    ProviderErrorType,
    StepToken,
    Where,
)

_OWN_PACKAGE = "hadavin_sdk"
_KIND_RE = re.compile(rf"[A-Za-z0-9_.]{{1,{defaults.DIAG_KIND_CHARS}}}")
_STEP_RE = re.compile(rf"[a-z_]{{1,{defaults.DIAG_STEP_CHARS}}}")
_LOCATOR_RE = re.compile(r"[A-Za-z0-9_./-]{1,120}:[0-9]{1,7}")
_FP_RE = re.compile(r"[0-9a-f]{8}")
_TOKEN_RE = re.compile(rf"[A-Za-z0-9_.-]{{1,{defaults.DIAG_KEY_CHARS}}}")
_SQLSTATE_RE = re.compile(r"[0-9A-Z]{5}")
_VALUE_RE = re.compile(rf"-?[A-Za-z0-9_.-]{{1,{defaults.DIAG_KEY_CHARS}}}")
_TOKEN_KEYS: Final = frozenset(
    {FactKey.key, FactKey.cause_kind, FactKey.field, FactKey.type, FactKey.sqlstate}
)


def _fingerprint(kind: str, code: str, function: str, relpath: str) -> str:
    text = f"{kind}|{code}|{function}|{relpath}"
    return hashlib.sha256(text.encode("utf-8", "replace")).hexdigest()[:8]


FALLBACK_FP: Final = _fingerprint("unknown", Code.foreign_exception.value, "-", "-")
_pkg_file = getattr(sys.modules.get(_OWN_PACKAGE), "__file__", None)
_PKG_DIR: Final = os.path.dirname(_pkg_file) if type(_pkg_file) is str else ""


class SafeToken:
    """A short word that passed an exact check. Made only by ``SafeToken.of`` and ``SafeToken.sqlstate``; holds a member of the
    caller's frozen set (never the caller's own object)."""

    __slots__ = ("value",)
    value: str
    _MINT: Final = object()

    def __init_subclass__(cls, **kw: object) -> None:
        raise TypeError("SafeToken is final")

    def __init__(self, value: str, _mint: object = None) -> None:
        if _mint is not SafeToken._MINT:
            raise TypeError("use SafeToken.of or SafeToken.sqlstate")
        object.__setattr__(self, "value", value)

    def __setattr__(self, name: str, value: object) -> None:
        raise AttributeError("SafeToken is immutable")

    @staticmethod
    def of(value: object, allowed: frozenset[str]) -> SafeToken | None:
        """The member of ``allowed`` that equals ``value`` (exact ``str`` only), if it fits the token pattern.

        What this does NOT guarantee: that ``allowed`` is a closed list. A call such as ``SafeToken.of(x, frozenset({x}))`` makes any
        text that fits the pattern a token. The closed list is a property of the CALL SITE, so every caller must pass a constant set
        written in the code (a ``Final`` frozenset of a module, or an enum's values). P5a's own sites do; the callers that P5b3 wires
        in are covered by its call-site check (an AST test that fails on a set built from the value being checked)."""
        if type(value) is not str or type(allowed) is not frozenset:
            return None
        for member in allowed:
            if type(member) is str and member == value:
                if _TOKEN_RE.fullmatch(member) is None:
                    return None
                return SafeToken(member, SafeToken._MINT)
        return None

    @staticmethod
    def sqlstate(value: object) -> SafeToken | None:
        """A five-character database state (``28P01``). ``re.fullmatch``: ``"28P01\\n"`` is refused."""
        if type(value) is not str or _SQLSTATE_RE.fullmatch(value) is None:
            return None
        return SafeToken(value, SafeToken._MINT)


Fact = int | bool | ProviderErrorType | Phase | SafeToken


@dataclass(frozen=True, slots=True)
class Diagnostic:
    kind: str
    code: Code
    step: str
    locator: str
    facts: tuple[tuple[FactKey, Fact], ...]
    fp: str


# --- identity of classes -------------------------------------------------------------------------------------------------


# How often each guard below fired, by site name. A count only: nothing about the exception (no text, no type) is kept.
_GUARD_FAILURES: dict[str, int] = {}
# one lock: a count read-then-written by two threads at once would lose one. Re-entrant (RLock), so a signal handler that runs on the same
# thread while the lock is held cannot deadlock it.
_GUARD_LOCK = threading.RLock()


def _guard_failed(site: str) -> None:
    """Record that the guard at ``site`` caught an ``Exception``. A fixed site name and a count; never the exception."""
    with _GUARD_LOCK:
        _GUARD_FAILURES[site] = _GUARD_FAILURES.get(site, 0) + 1


def guard_failures() -> dict[str, int]:
    """A copy of the guard counters (site name -> times caught)."""
    with _GUARD_LOCK:
        return dict(_GUARD_FAILURES)


def _is_the_named_class(tp: type, names: tuple[object, object] | None = None) -> bool:
    """True if walking ``sys.modules[tp.__module__].__dict__`` along ``tp.__qualname__`` reaches ``tp`` itself. A caller that has already
    read the two names passes them as ``names``, so the answer and the printed name come from ONE read (a hostile metaclass could
    answer differently the second time)."""
    try:
        mod, qual = names if names is not None else (tp.__module__, tp.__qualname__)
        if type(mod) is not str or type(qual) is not str or "<" in qual:
            return False
        parts = qual.split(".")
        if len(parts) > 4:
            return False
        module = sys.modules.get(mod)
        if module is None:
            return False
        obj: object = None
        scope: Mapping[str, object] = vars(module)
        for i, part in enumerate(parts):
            obj = scope.get(part)
            if obj is None:
                return False
            if i < len(parts) - 1:
                scope = vars(obj)
        return obj is tp
    except Exception:  # noqa: BLE001 - a hostile class attribute may raise any Exception: not the named class
        _guard_failed("named_class")
        return False


def class_name_of(exc_or_type: object) -> str:
    """The only function that turns a class into text. Own classes print the bare qualname, built-ins print bare, an allow-listed
    foreign class prints ``module.qualname``, a foreign class off the list prints ``foreign_class`` and a class that is not the
    object found under its own name prints ``dynamic_class``."""
    try:
        tp = exc_or_type if issubclass(type(exc_or_type), type) else type(exc_or_type)
        mod, qual = (
            tp.__module__,
            tp.__qualname__,
        )  # read once; the check below gets these same two values
        if not _is_the_named_class(tp, (mod, qual)):
            return "dynamic_class"
        if mod == "builtins":
            return qual if _KIND_RE.fullmatch(qual) else "foreign_class"
        if mod == _OWN_PACKAGE or mod.startswith(_OWN_PACKAGE + "."):
            return qual if _KIND_RE.fullmatch(qual) else "dynamic_class"
        text = f"{mod}.{qual}"
        if mod.split(".")[0] in FOREIGN_PACKAGES_OK and _KIND_RE.fullmatch(text):
            return text
        return "foreign_class"
    except Exception:  # noqa: BLE001 - a hostile class attribute may raise any Exception: dynamic_class
        _guard_failed("class_name")
        return "dynamic_class"


def _own_code(tp: type) -> Code | None:
    for cls in tp.__mro__:
        try:
            mod, qual = cls.__module__, cls.__qualname__
            if type(mod) is not str or type(qual) is not str:
                continue
            code = OWN_CODES.get(f"{mod}:{qual}")
            if code is not None and _is_the_named_class(cls, (mod, qual)):
                return code
        except Exception:  # noqa: BLE001 - a hostile class attribute may raise any Exception: not an own class
            _guard_failed("own_code")
            continue
    return None


# --- frames and locator --------------------------------------------------------------------------------------------------


def _counted_module(frame: object) -> str | None:
    """The module name of a frame that is really a file of an imported module; None otherwise. Never raises."""
    try:
        g = frame.f_globals  # type: ignore[attr-defined]
        name = g.get("__name__")
        if type(name) is not str:  # rule a
            return None
        module = sys.modules.get(name)
        if module is None or g is not vars(module):  # rule b
            return None
        filename = frame.f_code.co_filename  # type: ignore[attr-defined]
        if type(filename) is not str or filename != module.__file__:  # rule c, raw strings
            return None
        return name
    except Exception:  # noqa: BLE001 - a hostile frame object may raise any Exception: not counted
        _guard_failed("counted_module")
        return None


def _is_own_module(name: str) -> bool:
    return name == _OWN_PACKAGE or name.startswith(_OWN_PACKAGE + ".")


def _links(exc: object) -> tuple[list[tuple[object, int]], bool]:
    """The innermost ``DIAG_MAX_FRAMES`` traceback links, oldest first, and whether the traceback was longer than ``DIAG_TB_STEPS``."""
    tb = getattr(exc, "__traceback__", None)
    kept: deque[tuple[object, int]] = deque(maxlen=defaults.DIAG_MAX_FRAMES)
    steps = 0
    while tb is not None:
        steps += 1
        if steps > defaults.DIAG_TB_STEPS:
            return [], True
        kept.append((tb.tb_frame, tb.tb_lineno))
        tb = tb.tb_next
    return list(kept), False


def _locate(links: list[tuple[object, int]]) -> tuple[str, str, str]:
    """(locator, function, relpath) of the innermost counted frame of this package that gives a valid locator.

    A frame of this package whose file is outside the package folder, whose line is missing (``None`` on Python 3.11+) or whose
    locator fails the grammar is skipped and the next outer frame of this package is tried; ('-', '-', '-') when none is left."""
    prefix = _PKG_DIR + os.sep
    for frame, lineno in reversed(links):
        name = _counted_module(frame)
        if name is None or not _is_own_module(name):
            continue
        try:
            filename = frame.f_code.co_filename  # type: ignore[attr-defined]
            if not _PKG_DIR or not filename.startswith(prefix) or type(lineno) is not int:
                continue
            rel = filename[len(prefix) :].replace(os.sep, "/")
            locator = f"{rel}:{lineno}"
            if _LOCATOR_RE.fullmatch(locator) is None:
                continue
            function = frame.f_code.co_name  # type: ignore[attr-defined]
            return locator, function if type(function) is str else "-", rel
        except Exception:  # noqa: BLE001 - a hostile frame object may raise any Exception: no locator from this frame
            _guard_failed("locator")
            continue
    return "-", "-", "-"


def _raised_in_own_code(
    exc: object, tp: type, links: list[tuple[object, int]], too_long: bool
) -> bool:
    if too_long or not links:
        return False
    name = _counted_module(links[-1][0])
    if name is None or not _is_own_module(name):
        return False
    tname = tp.__name__
    return type(tname) is str and getattr(builtins, tname, None) is tp


# --- the closed reads of a pydantic error --------------------------------------------------------------------------------


def _error_types(exc: BaseException) -> tuple[int, tuple[str, ...]]:
    """``error_count()`` and the first ``DIAG_MAX_ERRORS`` ``"type"`` values. The only place that touches a pydantic error.

    Cost: pydantic builds an entry for every error before the slice, so the time is linear in the error count (a library limit;
    the traceback and document size bound it, and the call runs only on the error path)."""
    count = exc.error_count()  # type: ignore[attr-defined]
    found = exc.errors(include_url=False, include_context=False, include_input=False)  # type: ignore[attr-defined]
    types: list[str] = []
    for entry in found[: defaults.DIAG_MAX_ERRORS]:
        value = entry["type"]
        types.append(value if type(value) is str else "")
    return count, tuple(types)


def _closed_type(value: str) -> str:
    return value if value in VALIDATION_TYPES else VALIDATION_OTHER


def validation_text(exc: BaseException) -> str:
    """Closed type names only: ``V := TYPE ("; " TYPE){0,4} ("; +" N " more")?``. Never a value from the document, never a
    library sentence, never a ``loc``. An exception that is not a pydantic ``ValidationError`` gives ``other``."""
    try:
        if not issubclass(type(exc), _ValidationError):
            return VALIDATION_OTHER
        count, types = _error_types(exc)
        names = [_closed_type(t) for t in types] or [VALIDATION_OTHER]
        _, hi = FACT_BOUNDS[FactKey.count]
        text = "; ".join(names)
        if type(count) is int and count > defaults.DIAG_MAX_ERRORS:
            # a count above the bound is printed as the bound (the number of types stays a fact within FACT_BOUNDS)
            text += f"; +{min(count, hi) - defaults.DIAG_MAX_ERRORS} more"
        return text
    except Exception:  # noqa: BLE001 - a hostile pydantic error object may raise any Exception: other
        _guard_failed("validation_text")
        return VALIDATION_OTHER


# --- the code and the facts ----------------------------------------------------------------------------------------------


def _bounded(key: FactKey, value: object) -> int | None:
    lo, hi = FACT_BOUNDS[key]
    return value if type(value) is int and lo <= value <= hi else None  # type: ignore[return-value]


def _check_fact(key: object, value: object) -> Fact | None:
    """The fact value if it has the right exact type for its key and passes its bound; None otherwise (dropped)."""
    if type(key) is not FactKey:
        return None
    if key in FACT_BOUNDS:
        return _bounded(key, value)
    if key is FactKey.retryable:
        return value if type(value) is bool else None
    if key is FactKey.provider_error_type:
        return value if type(value) is ProviderErrorType else None
    if key is FactKey.phase:
        return value if type(value) is Phase else None
    if key in _TOKEN_KEYS:
        return value if type(value) is SafeToken else None
    return None  # request_id: no accepted value in this package


def _phase_of(sqlstate: SafeToken | None) -> Phase:
    if sqlstate is None:
        return Phase.unknown
    return {"28": Phase.auth, "08": Phase.connect}.get(sqlstate.value[:2], Phase.query)


def _classify(
    exc: object,
    tp: type,
    *,
    read_facts: bool,
    nested: bool = False,
    walked: tuple[list[tuple[object, int]], bool] | None = None,
) -> tuple[Code, dict[FactKey, object]]:
    if not issubclass(tp, Exception):
        return Code.foreign_exception, {}
    own = _own_code(tp)
    if own is not None:
        return own, {}
    facts: dict[FactKey, object] = {}
    if issubclass(tp, TimeoutError):
        return Code.timeout, facts
    if issubclass(tp, socket.gaierror):
        if read_facts:
            facts[FactKey.gai] = exc.errno  # type: ignore[attr-defined]
        return Code.os_error, facts
    if issubclass(tp, OSError):
        if read_facts:
            facts[FactKey.errno] = exc.errno  # type: ignore[attr-defined]
            facts[FactKey.winerror] = getattr(exc, "winerror", None)
        return Code.os_error, facts
    if issubclass(tp, _ValidationError):
        if read_facts:
            count, types = _error_types(exc)  # type: ignore[arg-type]
            facts[FactKey.count] = count
            first = _closed_type(types[0]) if types else VALIDATION_OTHER
            facts[FactKey.type] = SafeToken.of(first, VALIDATION_TYPES | {VALIDATION_OTHER})
        return Code.validation_failed, facts
    if issubclass(tp, json.JSONDecodeError):
        if read_facts:
            facts[FactKey.position] = exc.pos  # type: ignore[attr-defined]
        return Code.validation_failed, facts
    psycopg = sys.modules.get("psycopg")
    base = getattr(psycopg, "Error", None)
    if type(base) is type and issubclass(tp, base):
        if read_facts:
            sqlstate = SafeToken.sqlstate(getattr(exc, "sqlstate", None))
            facts[FactKey.sqlstate] = sqlstate
            facts[FactKey.phase] = _phase_of(sqlstate)
        return Code.db_error, facts
    if issubclass(tp, BaseExceptionGroup):
        if nested:
            return Code.foreign_exception, {}
        try:
            first_member = exc.exceptions[0]  # type: ignore[attr-defined]
            member_code, _ = _classify(
                first_member, type(first_member), read_facts=False, nested=True
            )
            return member_code, {}
        except Exception:  # noqa: BLE001 - a hostile group object may raise any Exception: foreign_exception
            _guard_failed("group_member")
            return Code.foreign_exception, {}
    links, too_long = walked if walked is not None else _links(exc)
    if _raised_in_own_code(exc, tp, links, too_long):
        return Code.internal_bug, {}
    return Code.foreign_exception, {}


def _step_text(step: object) -> str:
    if type(step) is Where or type(step) is StepToken:
        return step.value  # type: ignore[union-attr]
    return Where.other.value


def _merge_facts(
    caller: object, derived: Mapping[FactKey, object]
) -> tuple[tuple[FactKey, Fact], ...]:
    merged: dict[FactKey, Fact] = {}
    if caller is not None:
        for key, value in list(caller.items()):  # type: ignore[attr-defined]
            checked = _check_fact(key, value)
            if checked is not None:
                merged[key] = checked
    for key, value in derived.items():
        checked = _check_fact(key, value)
        if checked is not None:
            merged[key] = checked
    ordered = [(k, merged[k]) for k in FACT_PRIORITY if k in merged]
    return tuple(ordered[: defaults.DIAG_MAX_FACTS])


def _diagnose(exc: object, step: str, facts: object) -> Diagnostic:
    tp = type(exc)
    kind = class_name_of(tp)
    # the traceback is walked once per diagnosis; the classifier and the locator share the result
    walked = _links(exc)
    code, derived = _classify(exc, tp, read_facts=True, walked=walked)
    locator, function, relpath = _locate(walked[0])
    return Diagnostic(
        kind=kind,
        code=code,
        step=step,
        locator=locator,
        facts=_merge_facts(facts, derived),
        fp=_fingerprint(kind, code.value, function, relpath),
    )


def diagnose(
    exc: BaseException, *, step: StepToken | Where, facts: Mapping[FactKey, Fact] | None = None
) -> Diagnostic:
    """The diagnostic of ``exc``. Catches ``Exception`` only: a ``KeyboardInterrupt`` or ``CancelledError`` raised inside (by a hostile
    attribute) propagates, so a stop request is never swallowed. A value in ``facts`` of the wrong type or out of bounds is dropped."""
    step_text = _step_text(step)
    try:
        return _diagnose(exc, step_text, facts)
    except Exception:  # noqa: BLE001 - a hostile exception object may raise any Exception: the fixed fallback
        _guard_failed("diagnose")
        return Diagnostic(
            kind="unknown",
            code=Code.foreign_exception,
            step=step_text,
            locator="-",
            facts=(),
            fp=FALLBACK_FP,
        )


# --- rendering -----------------------------------------------------------------------------------------------------------


def _fact_text(key: object, value: object) -> str | None:
    if type(key) is not FactKey:
        return None
    if type(value) is bool:
        text = "true" if value else "false"
    elif type(value) is int:
        text = str(value)
    elif type(value) in (ProviderErrorType, Phase, SafeToken):
        text = value.value
    else:
        return None
    return f"{key.value}={text}" if type(text) is str and _VALUE_RE.fullmatch(text) else None


def render(d: Diagnostic) -> str:
    """Grammar A, plain ASCII, at most ``DIAG_LINE_CHARS`` characters; trailing facts are dropped first."""
    try:
        kind = d.kind if type(d.kind) is str and _KIND_RE.fullmatch(d.kind) else "foreign_class"
        code = d.code.value if type(d.code) is Code else Code.foreign_exception.value
        step = d.step if type(d.step) is str and _STEP_RE.fullmatch(d.step) else Where.other.value
        at = (
            d.locator
            if type(d.locator) is str and (d.locator == "-" or _LOCATOR_RE.fullmatch(d.locator))
            else "-"
        )
        fp = d.fp if type(d.fp) is str and _FP_RE.fullmatch(d.fp) else FALLBACK_FP
        line = f"{kind}: diag_v={defaults.DIAG_VERSION} code={code} step={step} at={at} fp={fp}"
        for key, value in d.facts:
            part = _fact_text(key, value)
            if part is None:
                continue
            if len(line) + 1 + len(part) > defaults.DIAG_LINE_CHARS:
                break
            line += " " + part
        return line.encode("ascii", "backslashreplace").decode("ascii")
    except Exception:  # noqa: BLE001 - a hostile diagnostic object may raise any Exception: the fixed line
        _guard_failed("render")
        return (
            f"unknown: diag_v={defaults.DIAG_VERSION} code={Code.foreign_exception.value} "
            f"step={Where.other.value} at=- fp={FALLBACK_FP}"
        )
