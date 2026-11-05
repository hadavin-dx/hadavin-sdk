"""The redactor kind: masks text before a model sees it, with marks that stay stable for one run.

A ``MaskSession`` is the run's memory of which value got which mark (``<EMAIL_1>``): it only grows, the same value
always gets the same mark and a new value gets the next number. A ``Redactor`` masks text against a session and can
check afterwards that no value the session knows is left in clear. ``RegexRedactor`` is the default kind; it wraps
``guard.redact`` (the pattern table) and adds the input rules (types, sizes, work budget, forged marks) around it.

Threat model: this blocks accidents (a value reaching a model, a log or an audit row), not an attacker who runs code
in the same process (``gc``, frame inspection and the session's attributes can always read a session).

Input contract (written down here because ``MaskedLLM`` arrives in a later ticket):
  * ``mask`` and ``find`` take ``str``. Bytes go through ``decode_input`` first (UTF-8 strict, leading BOMs dropped
    BEFORE the file-signature check, no NUL, no PDF/PNG/JPEG/GIF/zip signature): the one shared decoder.
  * Escape sequences (ANSI/C1) are REMOVED to a FIXPOINT before anything is scanned or masked (nested forms such as
    ``ESC[ESC[0m0m`` included); more than 16 nesting passes is refused. The output never contains an escape.
  * A mark (``<KIND_n>``) in the input must have been issued by THIS session, else ``forged_mark``; a mark that only
    appears after stripping is forged too. The output is re-scanned (as is, and stripped): every mark-shaped token in
    it was issued by this session.
  * C1b obligations (the mark text is fixed by the spec, so it carries no session identity and a mark issued by
    ANOTHER session with the same number cannot be told apart): one ``MaskSession`` per run context, never shared
    between runs; the judge uses the same context; a contract test ``test_two_threads_two_runs_no_crosstalk``; restore
    only on an exact ``<KIND_n>`` match, with no NFKC, entity or percent decoding first (a mark written with full-width
    brackets, zero-width characters or entities is inert text, not a mark); call ``close()`` (or use the session as a
    context manager) at the end of the run.
  * ``RedactionError`` is raised outside any ``except`` block of this module, so it has no cause and its context is
    cleared. If the CALLER calls ``mask`` inside its own ``except`` block, Python sets the caller's exception as
    ``__context__`` (hidden: ``__suppress_context__`` is True); call it outside such a block.

Limits (settings of the ``regex`` kind, all part of the config hash). Checked by linear scans before any pattern runs;
over a limit the input is REFUSED (``too_large``), never passed on unmasked:
  ``max_doc_chars``, ``max_token_chars`` (longest run without whitespace), ``max_line_chars``, ``max_work`` (the sum
  of the squares of the line lengths: the patterns in ``guard.redact`` take time that grows with the square of a line,
  and a long line of one repeated shape is their worst case), ``max_session_values`` (distinct values one run can
  mark; checked before masking starts and again after) and ``max_walk_items`` (keys and containers ``refuse_unsafe_keys``
  looks at). Inputs that legitimately exceed them (Chinese or Japanese text without spaces, minified JSON, base64 or
  data URIs, hex dumps, one 4,000-email line) must be split by the caller.
  Time: the patterns run with the interpreter lock held, so a call blocks every thread of the process. At the default
  limits an ordinary 190,000-character document takes about 1 s and the slowest shape measured (``egm/hadavin-sdk/c1/
  evidence-c1a-5.md``) about 3 s on a laptop; budget a few seconds per call and run masking off the event loop. The pattern fix itself belongs to the
  pattern ticket (BL-core-c1a-001), not to this module. Masks of ONE session run one after another (numbering needs
  it); ``check``, ``counts`` and ``issued`` do not wait for a running mask.
  Cost grows with the number of distinct values in a session (``guard.redact._Redactor._build`` rebuilds its finder
  when the mapping grows), so many documents each adding a new value are quadratic overall; measured in the evidence.

Caches: ``guard.redact`` keeps compiled patterns that contain the values it masked (``_standalone`` lru_cache and the
``re`` compile cache). ``MaskSession.close()`` empties both; ``find``, ``lint`` and ``refuse_unsafe_keys`` (which have no
session) empty them at the end of each call. Both caches are process-wide, so this also costs other callers a rebuild.

NOT masked by the regex kind (it does not claim more): a spaced or lower-case or hyphenated IBAN; names in free
prose; a value glued to other characters (``bob@example.com_x``); zero-width or soft-hyphen characters inside a
value; percent-encoded forms other than ``%40`` in an email (``%2E``), HTML-entity (``&#64;``), base64, full-width
and line-wrapped forms; images and PDFs (refused as ``unsupported_input``, not read). ``check`` uses the same rule as
``mask`` (whole token for identifiers, every copy for secret kinds, like ``_sweep``), so it shares these blind spots
and ignores originals shorter than 4 characters.

Second kind (single-dependency rule): the alternative is a ``service`` kind, a client-run masking service or a
model-based entity recogniser. Trigger: ticket KERNEL-1, or the first client whose documents carry names in free
prose. It must implement ``Redactor`` (name, version, fingerprint, mask, check, find, lint) using only the public
``MaskSession`` API (``issue``, ``original_of``, ``snapshot``, ``absorb``, ``lock``, ``exclusive``, ``cache``) and
bring its own limits as settings. Nothing outside this module imports ``guard.redact``'s internals.
"""

from __future__ import annotations

import functools
import hashlib
import inspect
import re
import sys
import threading
from collections.abc import ItemsView, Iterator, KeysView, Mapping, Sequence, ValuesView
from collections.abc import Set as AbstractSet
from dataclasses import fields, is_dataclass
from datetime import date, datetime, time, timedelta
from decimal import Decimal
from enum import Enum
from pathlib import PurePath
from typing import Any, NoReturn, Protocol, Self, runtime_checkable
from uuid import UUID

import hadavin_sdk.guard.redact  # noqa: F401  (loads the submodule)
from hadavin_sdk.errors import ConfigError

# The submodule, not `guard.redact` the function that guard/__init__ exports under the same name.
_redact = sys.modules["hadavin_sdk.guard.redact"]

# Bump whenever the behaviour of this module or of guard/redact.py changes (a test pins the source fingerprint, and the
# kind refuses to start when guard/redact.py differs from the source hash pinned here).
REGEX_VERSION = "3"
REDACT_SOURCE_SHA256 = "e0fc31eb306a0093bee72b47d314d0d1390d350f05da83fb636ebeb33a27efd5"
DEFAULT_MAX_DOC_CHARS = 200_000
DEFAULT_MAX_TOKEN_CHARS = 1024
DEFAULT_MAX_LINE_CHARS = 10_000
DEFAULT_MAX_WORK = 100_000_000
DEFAULT_MAX_SESSION_VALUES = 5000
DEFAULT_MAX_WALK_ITEMS = 20_000
# Upper bounds (also in the settings model): well below the quadratic cliff of a single line.
BOUNDS = {
    "max_doc_chars": 1_000_000,
    "max_token_chars": 50_000,
    "max_line_chars": 50_000,
    "max_work": 2_000_000_000,
    "max_session_values": 100_000,
    "max_walk_items": 1_000_000,
}
MAX_KEY_DEPTH = 100
MAX_STRIP_PASSES = 16
_MARK = _redact._PLACEHOLDER  # <KIND_n>, the one shape of a mark
# File signatures that are not text: PDF, PNG, JPEG, GIF, zip (and so docx/xlsx).
_SIGNATURES = (b"%PDF-", b"\x89PNG", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"PK\x03\x04")
_SIGNATURE_TEXT = tuple(s.decode("latin-1") for s in _SIGNATURES)
_BOM = "\ufeff"
_BOM8 = _BOM.encode()
_ENGINE = "regex.engine"
_CHECK = "regex.check"

CODES = ("unsupported_input", "too_large", "forged_mark", "self_check_failed", "internal")


class RedactionError(RuntimeError):
    """Masking refused or failed. Carries a code and nothing else: no text, no value, no cause."""

    def __init__(self, code: str) -> None:
        code = code if code in CODES else "internal"
        super().__init__(code)
        self.code = code

    def __str__(self) -> str:
        return self.code


class _Refusal(Exception):
    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code


def _fail(code: str) -> NoReturn:
    """Inside the module: stop with a code. Caught by `_try`; it never reaches a caller."""
    raise _Refusal(code)


def _scrub(exc: BaseException) -> None:
    """Empty the frames an escaping exception passed through, so its traceback holds no input text."""
    tb = exc.__traceback__.tb_next if exc.__traceback__ is not None else None
    while tb is not None:
        try:
            tb.tb_frame.clear()
        except RuntimeError:  # a frame that is still running cannot be cleared
            pass
        tb = tb.tb_next
    exc.__traceback__ = None


def _try(fn, *args) -> tuple[Any, str | None]:
    """(result, None) or (None, code). The exception is dropped here: no cause, no traceback, no raw text escapes."""
    try:
        return fn(*args), None
    except _Refusal as refusal:
        return None, refusal.code
    except Exception:  # noqa: BLE001 - any failure is the code "internal", never its text
        return None, "internal"
    except (
        BaseException
    ) as exc:  # KeyboardInterrupt and friends propagate, but not with the text in the frames
        args = ()
        _scrub(exc)
        raise


def _refuse(code: str) -> NoReturn:
    """The one place a RedactionError is raised: outside any `except` of ours, so no cause and no traceback."""
    err = RedactionError(code)
    err.__cause__ = None
    err.__context__ = None
    err.__suppress_context__ = True
    raise err.with_traceback(None)


def _forget_caches() -> None:
    """guard.redact's pattern caches hold the values it masked; the `re` compile cache holds the finders."""
    _redact._standalone.cache_clear()
    re.purge()


class MaskSession:
    """One run's marks. Append-only; the mapping is private and the object cannot be copied or pickled.

    Public API for redactor kinds (so a second kind needs no private access): ``issue``, ``original_of``, ``snapshot``,
    ``absorb``, ``issued``, ``size``, ``counts`` and three locks: ``lock`` (the mapping, held briefly), ``exclusive``
    (one mask at a time, may be held for the whole masking), ``checking`` (one check engine at a time), plus ``cache``
    (a dict a kind may use for its own engines; emptied by ``close``).
    Thread-safe. ``close()`` forgets everything; a closed session refuses further use."""

    __slots__ = ("_closed", "_mapping", "cache", "checking", "exclusive", "lock")

    def __init__(self) -> None:
        self._mapping: dict[
            str, str
        ] = {}  # mark -> original, never exposed except through snapshot()
        self._closed = False
        self.lock = threading.RLock()
        self.exclusive = threading.RLock()
        self.checking = threading.RLock()
        self.cache: dict[str, Any] = {}

    @property
    def closed(self) -> bool:
        return self._closed

    @property
    def size(self) -> int:
        return len(self._mapping)

    @property
    def counts(self) -> dict[str, int]:
        """How many distinct values each kind has marked so far."""
        with self.lock:
            marks = list(self._mapping)
        out: dict[str, int] = {}
        for mark in marks:
            kind = _redact._kind(mark)
            out[kind] = out.get(kind, 0) + 1
        return out

    def issued(self, mark: str) -> bool:
        return mark in self._mapping

    def original_of(self, mark: str) -> str | None:
        with self.lock:
            return self._mapping.get(mark)

    def issue(self, kind: str, original: str) -> str:
        """The mark for ``original`` (the existing one, or the next ``<KIND_n>``)."""
        with self.lock:
            if self._closed:
                _refuse("internal")
            prefix = f"<{kind}_"
            numbers = [0]
            for mark, value in self._mapping.items():
                if mark.startswith(prefix):
                    if value == original:
                        return mark
                    numbers.append(int(mark[len(prefix) : -1]))
            mark = f"{prefix}{max(numbers) + 1}>"
            self._mapping[mark] = original
            return mark

    def snapshot(self) -> dict[str, str]:
        with self.lock:
            return dict(self._mapping)

    def absorb(self, mapping: Mapping[str, str]) -> bool:
        """Take a grown mapping. False (nothing changed) if an existing mark would be renumbered or reassigned."""
        with self.lock:
            if self._closed or any(mapping.get(k) != v for k, v in self._mapping.items()):
                return False
            self._mapping.update(mapping)
            return True

    def close(self) -> None:
        """End of the run: forget every value, here and in the process-wide pattern caches of guard.redact and re."""
        with self.lock:
            self._mapping = {}
            self.cache.clear()
            self._closed = True
        _forget_caches()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *exc_info) -> None:
        self.close()

    def __repr__(self) -> str:
        return f"MaskSession(marks={len(self._mapping)})"

    def __getstate__(self) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")

    def __copy__(self) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")

    def __deepcopy__(self, memo) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")


@runtime_checkable
class Redactor(Protocol):
    """What the runtime needs from a redactor kind. ``put_back`` (restoring masked values) is NOT a member: frozen
    amendment F10 moves it to ticket C1f, where it will be added together with the approval-card design."""

    name: str
    version: str
    fingerprint: str  # identifies the exact code that masks; part of the config hash

    def mask(self, text: str, session: MaskSession) -> str: ...

    def check(self, masked: str, session: MaskSession) -> None: ...

    def find(self, text: str) -> list[str]: ...

    def lint(self, text: str, *, numeric: bool = False) -> list[str]: ...


def _decode(raw: Any, max_chars: int | None) -> str:
    """Text out of ``raw``, or `_fail` with ``unsupported_input`` / ``too_large``. Linear."""
    if isinstance(raw, (bytes, bytearray)):
        if max_chars is not None and len(raw) > max_chars * 4:
            _fail("too_large")  # before anything else: UTF-8 holds at most 4 bytes per character
        data = bytes(raw)
        start = 0
        while data.startswith(_BOM8, start):  # BEFORE the signature check, or BOM + %PDF would pass
            start += len(_BOM8)
        data = data[start:]
        if data.startswith(_SIGNATURES) or b"\x00" in data:
            _fail("unsupported_input")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            _fail("unsupported_input")
    elif isinstance(raw, str):
        if max_chars is not None and len(raw) > max_chars:
            _fail("too_large")  # before encoding
        text = raw.lstrip(_BOM)
        try:
            text.encode("utf-8")  # a lone surrogate is not valid UTF-8
        except UnicodeEncodeError:
            _fail("unsupported_input")
        if text.startswith(_SIGNATURE_TEXT) or "\x00" in text:
            _fail("unsupported_input")
    else:
        _fail("unsupported_input")
    if max_chars is not None and len(text) > max_chars:
        _fail("too_large")
    return text


def decode_input(raw: str | bytes, max_chars: int | None = None) -> str:
    """The one shared decoder (``MaskedLLM`` uses it before ``mask``): ``RedactionError`` with ``unsupported_input``
    or ``too_large``, else the text with leading BOMs removed."""
    try:
        text, code = _try(_decode, raw, max_chars)
    except BaseException:
        raw = None
        raise
    raw = None  # no raw input in this frame when the error propagates
    if code:
        _refuse(code)
    return text


def _strip(text: str) -> str:
    """Escape sequences REMOVED, to a fixpoint: one pass leaves the inner escape of a nested form (``ESC[ESC[0m0m``).
    Removed, not replaced by a space (``guard.redact.strip_ansi`` inserts one between two word characters): a value
    split by an invisible escape (``AKIA ESC[0m IOSF...``) reads as one value to a person, so it is masked as one.
    More than ``MAX_STRIP_PASSES`` nesting passes is refused."""
    for _ in range(MAX_STRIP_PASSES):
        if "\x1b" not in text and "\x9b" not in text:
            return text
        stripped = _redact._ANSI.sub("", text)
        if stripped == text:
            return text
        text = stripped
    _fail("unsupported_input")


def _scan_marks(text: str, issued) -> str:
    """The stripped text, or `_fail` ``forged_mark`` when a mark-shaped token is not issued or exists only once
    escape sequences are stripped."""
    stripped = _strip(text)
    raw_marks = _MARK.findall(text)
    if _MARK.findall(stripped) != raw_marks:
        _fail("forged_mark")  # `<ESC[0mEMAIL_1>` is a disguised mark
    if any(not issued(m) for m in raw_marks):
        _fail("forged_mark")
    return stripped


def _fingerprint_source() -> str:
    me = sys.modules[__name__]
    return "\0".join(inspect.getsource(m).replace("\r\n", "\n") for m in (_redact, me))


def regex_fingerprint() -> str:
    """sha256 over the WHOLE source of guard/redact.py and of this module (so every pattern, helper, constant, setting
    default and rule counts). Any edit to either file changes it; a test pins it to ``REGEX_VERSION``, so the edit
    must bump the version and re-pin. That includes core PR #50's changes to redact.py: intended, because a changed
    masking rule means every agent needs a new gate run."""
    return hashlib.sha256(_fingerprint_source().encode()).hexdigest()


@functools.cache
def _fingerprint_cached() -> str:
    return regex_fingerprint()


def _redact_source_sha() -> str:
    return hashlib.sha256(inspect.getsource(_redact).replace("\r\n", "\n").encode()).hexdigest()


def _luhn(number: str) -> bool:
    """13 to 19 digits that pass the Luhn check: a payment card number, however the engine typed it."""
    digits = [int(c) for c in number if c.isdigit()]
    if not 13 <= len(digits) <= 19 or len(digits) != len(number.replace(" ", "").replace("-", "")):
        return False
    total = 0
    for i, d in enumerate(reversed(digits)):
        d = d * 2 if i % 2 else d
        total += d - 9 if d > 9 else d
    return total % 10 == 0


def _check_int(name: str, value: Any) -> int:
    if isinstance(value, bool) or not isinstance(value, int) or not 0 < value <= BOUNDS[name]:
        raise ConfigError(f"redactor regex: {name} must be an integer from 1 to {BOUNDS[name]}")
    return value


class RegexRedactor:
    """``guard.redact`` behind the Redactor protocol."""

    name = "regex"
    version = REGEX_VERSION

    def __init__(
        self,
        max_doc_chars: int = DEFAULT_MAX_DOC_CHARS,
        max_token_chars: int = DEFAULT_MAX_TOKEN_CHARS,
        max_line_chars: int = DEFAULT_MAX_LINE_CHARS,
        max_session_values: int = DEFAULT_MAX_SESSION_VALUES,
        max_work: int = DEFAULT_MAX_WORK,
        max_walk_items: int = DEFAULT_MAX_WALK_ITEMS,
    ) -> None:
        if _redact_source_sha() != REDACT_SOURCE_SHA256:
            raise ConfigError(
                f"redactor regex@{REGEX_VERSION}: guard/redact.py changed without a version bump; "
                "bump REGEX_VERSION in guard/redactor.py and pin the new source hash (every agent needs a new gate run)"
            )
        self.max_doc_chars = _check_int("max_doc_chars", max_doc_chars)
        self.max_token_chars = _check_int("max_token_chars", max_token_chars)
        self.max_line_chars = _check_int("max_line_chars", max_line_chars)
        self.max_session_values = _check_int("max_session_values", max_session_values)
        self.max_work = _check_int("max_work", max_work)
        self.max_walk_items = _check_int("max_walk_items", max_walk_items)

    @property
    def fingerprint(self) -> str:
        return _fingerprint_cached()

    # ---- public API: every method returns or raises RedactionError(code); nothing else escapes -------------

    def mask(self, text: str, session: MaskSession) -> str:
        try:
            out, code = _try(self._mask, text, session)
        except BaseException:
            text = None
            raise
        text = None  # no raw input in this frame when the error propagates
        if code:
            _refuse(code)
        return out

    def check(self, masked: str, session: MaskSession) -> None:
        """No session original (4+ characters; whole token for identifiers, every copy for secret kinds, like
        ``_sweep``; case-sensitive) in ``masked``."""
        try:
            _, code = _try(self._check, masked, session)
        except BaseException:
            masked = None
            raise
        masked = None
        if code:
            _refuse(code)

    def find(self, text: str) -> list[str]:
        """Kinds this text would have masked (empty: nothing). Same input rules as ``mask``; no session."""
        try:
            out, code = _try(self._find, text)
        except BaseException:
            text = None
            raise
        text = None
        _forget_caches()
        if code:
            _refuse(code)
        return out

    def lint(self, text: str, *, numeric: bool = False) -> list[str]:
        """Kinds of what a trusted text (prompt, contract) must not contain: values that look real, not prose.

        Linted always: PRIVKEY JWT APIKEY GCPTOKEN AZURESAS WEBHOOK URLCRED BEARER BASIC HIGHENTROPY (secrets) and
        EMAIL IBAN CREDITCARD SSN AADHAAR PAN BANKCODE BANKACCT (personal and financial identifiers; BANKCODE and
        BANKACCT need their bank-word context, which the engine finds in the WHOLE text). Linted only when the value
        looks real: SECRET and TENANT (6+ characters with a digit and a letter, or 12+ letters after a password
        keyword), ADDRESS (a digit and 6+ characters), PHONE (a plus sign or a separator inside the number, or a
        phone word such as tel/phone/mobile/fax in the text: a bare 10-digit run like 2147483647 is a number).
        Not linted, because a keyword or a shape alone says nothing about a real value: NAME ACCOUNTID UUID IPV4 IPV6
        MAC HOSTNAME ARN GCPRESOURCE AZURERESOURCE.
        ``numeric=True`` (the text is a number written in a schema, not prose): only CREDITCARD is linted."""
        try:
            out, code = _try(self._lint, text, numeric)
        except BaseException:
            text = None
            raise
        text = None
        _forget_caches()
        if code:
            _refuse(code)
        return out

    # ---- inside: may `_fail`; `_try` turns everything into a code --------------------------------------------

    def _prepare(self, text: Any) -> str:
        if not isinstance(text, str):
            _fail("unsupported_input")  # bytes go through decode_input first
        text = _decode(text, self.max_doc_chars)
        work = 0
        for line in text.split("\n"):
            size = len(line)
            if size > self.max_line_chars:
                _fail("too_large")
            work += size * size
        if work > self.max_work:
            _fail("too_large")
        if any(len(token) > self.max_token_chars for token in text.split()):
            _fail("too_large")
        return text

    def _open(self, session: MaskSession) -> None:
        if session.closed:
            _fail(
                "internal"
            )  # a closed session would restart its numbering: <EMAIL_1> would mean another person

    def _engine(self, session: MaskSession):
        """The cached guard.redact engine for this session's mapping (rebuilt if another writer changed the mapping)."""
        engine = session.cache.get(_ENGINE)
        if engine is None or len(engine.mapping) != session.size:
            engine = session.cache[_ENGINE] = _redact._Redactor(session.snapshot())
        return engine

    def _mask(self, text: Any, session: MaskSession) -> str:
        self._open(session)
        text = self._prepare(text)
        stripped = _scan_marks(text, session.issued)
        with session.exclusive:
            self._open(session)
            if session.size >= self.max_session_values:
                _fail("too_large")  # BEFORE any pattern runs
            engine = self._engine(session)
            try:
                engine.bank_near = _redact._has_bank_word(stripped)
                out = engine.sweep(engine.find(stripped))
                if len(engine.mapping) > self.max_session_values:
                    _fail("too_large")
                for scanned in (
                    out,
                    _strip(out),
                ):  # the final output carries only marks this session issued
                    if any(m not in engine.mapping for m in _MARK.findall(scanned)):
                        _fail("forged_mark")
                if not session.absorb(engine.mapping):
                    _fail("internal")
            except BaseException:
                session.cache.pop(
                    _ENGINE, None
                )  # the engine may hold values the session never issued
                text = stripped = None
                raise
        return out

    def _check(self, masked: Any, session: MaskSession) -> None:
        if not isinstance(masked, str):
            _fail("unsupported_input")
        self._open(session)
        with session.checking:
            snapshot = session.snapshot()
            cached = session.cache.get(_CHECK)
            if cached is None or cached[0] != len(snapshot):
                known = {
                    mark: original
                    for mark, original in snapshot.items()
                    if len(original) >= 4 and _redact._sweep(mark, original) is not None
                }
                cached = session.cache[_CHECK] = (
                    len(snapshot),
                    _redact._Redactor(known) if known else None,
                )
            engine = cached[1]
            # The sweep itself is the finder (trie, longest first) and it skips text inside marks, like masking does.
            if engine is not None and engine.sweep(masked) != masked:
                _fail("self_check_failed")

    def _find(self, text: Any) -> list[str]:
        return _redact.redact(_strip(self._prepare(text))).kinds

    _LINT_ALWAYS = frozenset(
        [
            "PRIVKEY",
            "JWT",
            "APIKEY",
            "GCPTOKEN",
            "AZURESAS",
            "WEBHOOK",
            "URLCRED",
            "BEARER",
            "BASIC",
            "HIGHENTROPY",
            "EMAIL",
            "IBAN",
            "CREDITCARD",
            "SSN",
            "AADHAAR",
            "PAN",
            "BANKCODE",
            "BANKACCT",
        ]
    )
    _PHONE_WORD = re.compile(r"(?i)\b(?:tel|telephone|phone|mobile|cell|fax|whatsapp|call)\b")

    def _lint(self, text: Any, numeric: bool) -> list[str]:
        stripped = _strip(self._prepare(text))
        engine = _redact._Redactor(
            None
        )  # find only: no sweep, so a mark written in a prompt is no problem
        engine.bank_near = _redact._has_bank_word(stripped)
        engine.find(stripped)
        kinds = []
        for mark, original in engine.mapping.items():
            kind = _redact._kind(mark)
            digit = any(c.isdigit() for c in original)
            alpha = any(c.isalpha() for c in original)
            if numeric:
                hit = kind in {"CREDITCARD", "PHONE"} and _luhn(original)
                kind = "CREDITCARD"  # the engine types an unspaced card number as a phone number
                kind = "CREDITCARD"  # the engine types an unspaced card number as a phone number
            elif kind in self._LINT_ALWAYS:
                hit = True
            elif kind in {"SECRET", "TENANT"}:
                hit = (len(original) >= 6 and digit and alpha) or (
                    len(original) >= 12 and original.isalpha()
                )
            elif kind == "ADDRESS":
                hit = len(original) >= 6 and digit
            elif kind == "PHONE":
                at = stripped.find(original)
                near = stripped[max(0, at - 40) : at].rsplit(chr(10), 1)[-1] if at >= 0 else ""
                hit = bool(re.search(r"[+()\-.\s]", original)) or bool(
                    self._PHONE_WORD.search(near)
                )
            else:
                hit = False
            if hit:
                kinds.append(kind)
        return sorted(set(kinds))


# ---------------------------------------------------------------------------------------------- dict keys

_LEAVES = (
    type(None),
    bool,
    int,
    float,
    complex,
    str,
    bytes,
    bytearray,
    Decimal,
    datetime,
    date,
    time,
    timedelta,
    UUID,
    Enum,
    PurePath,
)


def _key_code(key: Any, redactor: Redactor) -> str | None:
    if isinstance(key, (bytes, bytearray)):
        key, code = _try(_decode, key, None)
        if code:
            return code
    elif not isinstance(key, str):
        key = str(key)
    stripped = _strip(key)
    if _MARK.search(key) or _MARK.search(stripped):
        return "forged_mark"
    try:
        # The same kind table as the registry lint: PII and secrets, not UUID/IP/host keys (decision, BL-core-c1a-026).
        return "unsupported_input" if redactor.lint(stripped) else None
    except RedactionError as exc:
        return exc.code


def _keys_code(value: Any, redactor: Redactor) -> str | None:
    limit = getattr(redactor, "max_walk_items", DEFAULT_MAX_WALK_ITEMS)
    stack: list[tuple[Any, int]] = [(value, 0)]
    seen: dict[
        int, Any
    ] = {}  # id -> the object itself: keeps it alive, so an id can never be reused while we walk
    items = 0
    while stack:
        item, depth = stack.pop()
        if isinstance(item, _LEAVES):
            continue
        items += 1
        if items > limit:
            return "too_large"
        if id(item) in seen:
            continue  # a cycle, or the same child twice
        seen[id(item)] = item
        if depth > MAX_KEY_DEPTH:
            return "too_large"
        children: list[Any] = []
        if isinstance(item, (KeysView, ValuesView, ItemsView, Iterator)):
            return (
                "unsupported_input"  # views and generators: cannot be walked without consuming them
            )
        if isinstance(item, Mapping):
            for key, child in item.items():
                items += 1
                if items > limit:
                    return "too_large"
                if code := _key_code(key, redactor):
                    return code
                children.append(child)
        elif callable(getattr(item, "model_dump", None)):
            try:
                children.append(item.model_dump())  # pydantic v2: the form that is serialised
            except Exception:  # noqa: BLE001 - an unreadable model is refused, not skipped
                return "unsupported_input"
        elif is_dataclass(item) and not isinstance(item, type):
            children.extend(getattr(item, f.name, None) for f in fields(item))
        elif isinstance(item, (Sequence, AbstractSet)):
            children.extend(item)
        else:
            return "unsupported_input"  # an object type we cannot walk (plain class, attrs, msgspec, pydantic v1)
        stack.extend((c, depth + 1) for c in children)
    return None


def refuse_unsafe_keys(value: Any, redactor: Redactor) -> None:
    """Dict keys are never masked, so a key that is mark-shaped (``forged_mark``) or that holds PII or a secret by the
    registry-lint kind table (``unsupported_input``) is refused. UUID, IP, host and MAC keys are allowed (decision: the
    spec forbids only mark-shaped keys; a tool result keyed by id is normal, its VALUES are masked).
    What is walked: the data model that is serialised, i.e. dict-like mappings, lists/tuples/sets, std dataclasses and
    pydantic v2 models (via ``model_dump()``), with scalar leaves (str, bytes, numbers, dates, UUID, Enum, paths) not
    examined. Any other object (generators, iterators, dict views, plain classes, attrs/msgspec, pydantic v1) is refused
    as ``unsupported_input``: convert it to plain data first. Cycles are survived, nesting over ``MAX_KEY_DEPTH`` and
    more than ``redactor.max_walk_items`` keys/containers are ``too_large``. Bytes keys are decoded first."""
    try:
        found, failed = _try(_keys_code, value, redactor)
    except BaseException:
        value = None
        raise
    code = failed or found
    value = None
    _forget_caches()
    if code:
        _refuse(code)


__all__ = [
    "REGEX_VERSION",
    "MaskSession",
    "RedactionError",
    "Redactor",
    "RegexRedactor",
    "decode_input",
    "refuse_unsafe_keys",
]
