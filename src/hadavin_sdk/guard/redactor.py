"""The redactor kind: masks text before a model sees it, with marks that stay stable for one run.

A ``MaskSession`` is the run's memory of which value got which mark (``<EMAIL_1>``): it only grows, the same value
always gets the same mark and a new value gets the next number. A ``Redactor`` masks text against a session and can
check afterwards that no value the session knows is left in clear. ``RegexRedactor`` is the default kind; it wraps
``guard.redact`` (the pattern table) and adds the input rules (types, sizes, forged marks) around it.

Threat model: this blocks accidents (a value reaching a model, a log or an audit row), not an attacker who runs code
in the same process (``gc``, frame inspection and ``_mapping`` can always read a session).

Input contract (written down here because ``MaskedLLM`` arrives in a later ticket):
  * ``mask`` and ``find`` take ``str``. Bytes go through ``decode_input`` first (UTF-8 strict, leading BOMs dropped
    BEFORE the file-signature check, no NUL, no PDF/PNG/JPEG/GIF/zip signature), which is the one shared decoder.
  * A mark (``<KIND_n>``) in the input must have been issued by THIS session, else ``forged_mark``. The mark text
    is fixed by the spec, so it carries no session identity: a mark issued by ANOTHER session with the same number
    is indistinguishable. Caller invariant for C1b: one session per run, never shared between runs
    (ledger BL-core-c1a-004; tests/test_c1a_redactor.py::test_cross_session_marks_are_a_caller_invariant shows the limit).
  * The output is re-scanned: every mark-shaped token in it was issued by this session, whatever escape sequence
    or hidden character the input used to build one.

Limits (settings of the ``regex`` kind, part of the config hash): ``max_doc_chars``, ``max_token_chars`` (longest
run of non-space characters) and ``max_line_chars`` (longest line), checked by a single linear scan, and
``max_session_values`` (distinct values one session can hold). Over a limit the input is REFUSED (``too_large``),
never passed on unmasked. Inputs that legitimately exceed them (Chinese or Japanese text without spaces, minified
JSON, base64 or data URIs, hex dumps) must be split by the caller. Why: some patterns in ``guard.redact`` take time
that grows with the square of an unbroken run (HIGHENTROPY, EMAIL) or rescan to the end of a line (URLCRED, SECRET);
the pattern fix belongs to the pattern ticket (BL-core-c1a-001), not to this module.

NOT masked by the regex kind (it does not claim more): a spaced or lower-case or hyphenated IBAN; names in free
prose; a value glued to other characters (``bob@example.com_x``); zero-width or soft-hyphen characters inside a
value; percent-encoded (``%40``), HTML-entity (``&#64;``), base64, full-width or line-wrapped forms; images and
PDFs (refused as ``unsupported_input``, not read). ``check`` uses the same rule as ``mask``, so it shares these
blind spots and ignores originals shorter than 4 characters.
"""

from __future__ import annotations

import hashlib
import inspect
import sys
import threading
from collections.abc import Mapping, Sequence
from collections.abc import Set as AbstractSet
from dataclasses import fields, is_dataclass
from typing import Any, NoReturn, Protocol, runtime_checkable

import hadavin_sdk.guard.redact  # noqa: F401  (loads the submodule)

# The submodule, not `guard.redact` the function that guard/__init__ exports under the same name.
_redact = sys.modules["hadavin_sdk.guard.redact"]

# Bump whenever the behaviour of this module or of guard/redact.py changes (a test pins the source fingerprint).
REGEX_VERSION = "2"
DEFAULT_MAX_DOC_CHARS = 200_000
DEFAULT_MAX_TOKEN_CHARS = 8192
DEFAULT_MAX_LINE_CHARS = 20_000
DEFAULT_MAX_SESSION_VALUES = 100_000
MAX_KEY_DEPTH = 100
_MARK = _redact._PLACEHOLDER  # <KIND_n>, the one shape of a mark
# File signatures that are not text: PDF, PNG, JPEG, GIF, zip (and so docx/xlsx).
_SIGNATURES = (b"%PDF-", b"\x89PNG", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"PK\x03\x04")
_SIGNATURE_TEXT = tuple(s.decode("latin-1") for s in _SIGNATURES)
_BOM = "﻿"
_BOM8 = _BOM.encode()

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


def _try(fn, *args) -> tuple[Any, str | None]:
    """(result, None) or (None, code). The exception is dropped here: no cause, no traceback, no raw text escapes."""
    try:
        return fn(*args), None
    except _Refusal as refusal:
        return None, refusal.code
    except Exception:  # noqa: BLE001 - any failure is the code "internal", never its text
        return None, "internal"


def _refuse(code: str) -> NoReturn:
    """The one place a RedactionError is raised: outside any `except`, so it has no context, cause or traceback."""
    err = RedactionError(code)
    err.__cause__ = None
    err.__context__ = None
    err.__suppress_context__ = True
    raise err.with_traceback(None)


class MaskSession:
    """One run's marks. Append-only; the mapping is private and the object cannot be copied or pickled.

    Thread-safe: one lock covers every read-modify-write of the mapping (masking, checking, counting)."""

    __slots__ = ("_check_engine", "_check_len", "_engine", "_lock", "_mapping")

    def __init__(self) -> None:
        self._mapping: dict[str, str] = {}  # mark -> original, never exposed
        self._lock = threading.RLock()
        self._engine = (
            None  # the guard.redact engine for this mapping, rebuilt only after a failure
        )
        self._check_engine = None
        self._check_len = -1

    @property
    def counts(self) -> dict[str, int]:
        """How many distinct values each kind has marked so far."""
        with self._lock:
            marks = list(self._mapping)
        out: dict[str, int] = {}
        for mark in marks:
            kind = _redact._kind(mark)
            out[kind] = out.get(kind, 0) + 1
        return out

    def issued(self, mark: str) -> bool:
        return mark in self._mapping

    def close(self) -> None:
        """End of the run: forget every value, here and in the process-wide pattern cache of guard.redact."""
        with self._lock:
            self._mapping = {}
            self._engine = self._check_engine = None
            self._check_len = -1
        _redact._standalone.cache_clear()

    def _snapshot(self) -> dict[str, str]:
        with self._lock:
            return dict(self._mapping)

    def _absorb(self, mapping: Mapping[str, str]) -> bool:
        """Take a grown mapping. False (nothing changed) if an existing mark would be renumbered or reassigned."""
        with self._lock:
            if any(mapping.get(k) != v for k, v in self._mapping.items()):
                return False
            self._mapping.update(mapping)
            return True

    def __repr__(self) -> str:
        return f"MaskSession(marks={len(self._mapping)})"

    def __reduce__(self) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")

    def __getstate__(self) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")

    def __copy__(self) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")

    def __deepcopy__(self, memo) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")


@runtime_checkable
class Redactor(Protocol):
    name: str
    version: str

    def mask(self, text: str, session: MaskSession) -> str: ...

    def check(self, masked: str, session: MaskSession) -> None: ...

    def find(self, text: str) -> list[str]: ...


def _decode(raw: Any, max_chars: int | None) -> str:
    """Text out of ``raw``, or `_fail` with ``unsupported_input`` / ``too_large``."""
    if isinstance(raw, (bytes, bytearray)):
        data = bytes(raw)
        if max_chars is not None and len(data) > max_chars * 4:
            _fail("too_large")  # before decoding: UTF-8 holds at most 4 bytes per character
        while data.startswith(_BOM8):  # BEFORE the signature check, or BOM + %PDF would pass
            data = data[len(_BOM8) :]
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
    text, code = _try(_decode, raw, max_chars)
    raw = None  # no raw input in this frame when the error propagates
    if code:
        _refuse(code)
    return text


def _forged_marks_code(text: str, issued) -> str | None:
    """`forged_mark` if a mark-shaped token is not issued, or appears only once escape sequences are stripped."""
    stripped = _redact.strip_ansi(text)
    raw_marks = _MARK.findall(text)
    if _MARK.findall(stripped) != raw_marks:
        return "forged_mark"  # `<ESC[0mEMAIL_1>` is a disguised mark
    return "forged_mark" if any(not issued(m) for m in raw_marks) else None


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
    ) -> None:
        self.max_doc_chars = max_doc_chars
        self.max_token_chars = max_token_chars
        self.max_line_chars = max_line_chars
        self.max_session_values = max_session_values

    # ---- public API: every method returns or raises RedactionError(code); nothing else escapes -------------

    def mask(self, text: str, session: MaskSession) -> str:
        out, code = _try(self._mask, text, session)
        text = None  # no raw input in this frame when the error propagates
        if code:
            _refuse(code)
        return out

    def check(self, masked: str, session: MaskSession) -> None:
        """No session original (4+ characters, whole token, case-sensitive, the ones ``_sweep`` masks) in ``masked``."""
        _, code = _try(self._check, masked, session)
        masked = None
        if code:
            _refuse(code)

    def find(self, text: str) -> list[str]:
        """Kinds this text would have masked (empty: nothing). Same input rules as ``mask``; no session."""
        out, code = _try(self._find, text)
        text = None
        if code:
            _refuse(code)
        return out

    def lint(self, text: str) -> list[str]:
        """Kinds of what a trusted text (prompt, contract) must not contain: values that look real, not prose.

        Linted always: PRIVKEY JWT APIKEY GCPTOKEN AZURESAS WEBHOOK URLCRED BEARER BASIC HIGHENTROPY (secrets) and
        EMAIL IBAN CREDITCARD PHONE SSN AADHAAR PAN (personal data). SECRET and TENANT only when the matched value
        has 6+ characters with a digit and a letter (``password: say you cannot`` is prose). Not linted, because
        a keyword or a shape alone says nothing about a real value: NAME ADDRESS ACCOUNTID BANKACCT BANKCODE UUID
        IPV4 IPV6 MAC HOSTNAME ARN GCPRESOURCE AZURERESOURCE."""
        out, code = _try(self._lint, text)
        text = None
        if code:
            _refuse(code)
        return out

    # ---- inside: may `_fail`; `_try` turns everything into a code --------------------------------------------

    def _prepare(self, text: Any) -> str:
        if not isinstance(text, str):
            _fail("unsupported_input")  # bytes go through decode_input first
        text = _decode(text, self.max_doc_chars)
        if any(len(line) > self.max_line_chars for line in text.split("\n")):
            _fail("too_large")
        if any(len(token) > self.max_token_chars for token in text.split()):
            _fail("too_large")
        return text

    def _mask(self, text: Any, session: MaskSession) -> str:
        text = self._prepare(text)
        if code := _forged_marks_code(text, session.issued):
            _fail(code)
        with session._lock:
            engine = session._engine
            if engine is None:
                engine = session._engine = _redact._Redactor(dict(session._mapping))
            try:
                engine.bank_near = _redact._has_bank_word(_redact.strip_ansi(text))
                out = engine.sweep(engine.find(text))
                if len(engine.mapping) > self.max_session_values:
                    _fail("too_large")
                if any(m not in engine.mapping for m in _MARK.findall(out)):
                    _fail("forged_mark")  # the final output carries only marks this session issued
                if not session._absorb(engine.mapping):
                    _fail("internal")
            except BaseException:
                session._engine = None  # the engine may hold values the session never issued
                raise
        return out

    def _check(self, masked: Any, session: MaskSession) -> None:
        if not isinstance(masked, str):
            _fail("unsupported_input")
        with session._lock:
            if session._check_len != len(session._mapping):
                known = {
                    mark: original
                    for mark, original in session._mapping.items()
                    if len(original) >= 4 and _redact._sweep(mark, original) is not None
                }
                session._check_engine = _redact._Redactor(known) if known else None
                session._check_len = len(session._mapping)
            engine = session._check_engine
            # The sweep itself is the finder (trie, longest first) and it skips text inside marks, like masking does.
            if engine is not None and engine.sweep(masked) != masked:
                _fail("self_check_failed")

    def _find(self, text: Any) -> list[str]:
        return _redact.redact(self._prepare(text)).kinds

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
            "PHONE",
            "SSN",
            "AADHAAR",
            "PAN",
        ]
    )
    _LINT_IF_REAL = frozenset({"SECRET", "TENANT"})

    def _lint(self, text: Any) -> list[str]:
        text = self._prepare(text)
        engine = _redact._Redactor(
            None
        )  # find only: no sweep, so a mark written in a prompt is no problem
        engine.bank_near = _redact._has_bank_word(_redact.strip_ansi(text))
        engine.find(text)
        kinds = []
        for mark, original in engine.mapping.items():
            kind = _redact._kind(mark)
            real = (
                len(original) >= 6
                and any(c.isdigit() for c in original)
                and any(c.isalpha() for c in original)
            )
            if kind in self._LINT_ALWAYS or (kind in self._LINT_IF_REAL and real):
                kinds.append(kind)
        return sorted(set(kinds))


def _key_code(key: Any, redactor: Redactor) -> str | None:
    if isinstance(key, (bytes, bytearray)):
        text, code = _try(_decode, key, DEFAULT_MAX_DOC_CHARS)
        if code:
            return code
        key = text
    elif not isinstance(key, str):
        key = str(key)
    if _MARK.search(key) or _MARK.search(_redact.strip_ansi(key)):
        return "forged_mark"
    try:
        return "unsupported_input" if redactor.find(key) else None
    except RedactionError as exc:
        return exc.code


def _keys_code(value: Any, redactor: Redactor) -> str | None:
    stack: list[tuple[Any, int]] = [(value, 0)]
    seen: set[int] = set()
    while stack:
        item, depth = stack.pop()
        if isinstance(item, (str, bytes, bytearray)) or item is None:
            continue
        if id(item) in seen:
            continue  # a cycle, or the same child twice
        seen.add(id(item))
        if depth > MAX_KEY_DEPTH:
            return "too_large"
        children: list[Any] = []
        if isinstance(item, Mapping):
            for key, child in item.items():
                if code := _key_code(key, redactor):
                    return code
                children.append(child)
        elif hasattr(item, "model_dump") and callable(item.model_dump):
            try:
                children.append(item.model_dump())
            except Exception:  # noqa: BLE001 - an unreadable model is refused, not skipped
                return "unsupported_input"
        elif is_dataclass(item) and not isinstance(item, type):
            children.extend(getattr(item, f.name, None) for f in fields(item))
        elif isinstance(item, (Sequence, AbstractSet)):
            children.extend(item)
        stack.extend((c, depth + 1) for c in children)
    return None


def refuse_unsafe_keys(value: Any, redactor: Redactor | None = None) -> None:
    """Dict keys are never masked, so a key that is mark-shaped (``forged_mark``) or that the redactor would mask
    (``unsupported_input``) is refused. Walks mappings of any kind, sequences, sets, dataclasses and pydantic models,
    decodes bytes keys, survives cycles, and refuses nesting deeper than ``MAX_KEY_DEPTH`` (``too_large``)."""
    found, failed = _try(_keys_code, value, redactor or RegexRedactor())
    code = failed or found
    value = None
    if code:
        _refuse(code)


def _normalised_source(module: Any) -> str:
    return inspect.getsource(module).replace("\r\n", "\n")


def regex_fingerprint() -> str:
    """sha256 over the WHOLE source of guard/redact.py and of this module (so every pattern, helper, constant, setting
    default and rule counts). Any edit to either file changes it; a test pins it to ``REGEX_VERSION``, so the edit
    must bump the version and re-pin. That includes core PR #50's changes to redact.py: intended, because a changed
    masking rule means every agent needs a new gate run."""
    me = sys.modules[__name__]
    digest = hashlib.sha256()
    for module in (_redact, me):
        digest.update(_normalised_source(module).encode())
        digest.update(b"\0")
    return digest.hexdigest()


__all__ = [
    "REGEX_VERSION",
    "MaskSession",
    "RedactionError",
    "Redactor",
    "RegexRedactor",
    "decode_input",
    "refuse_unsafe_keys",
]
