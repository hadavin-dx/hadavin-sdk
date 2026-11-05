"""The redactor kind: masks text before a model sees it, with marks that stay stable for one run.

A ``MaskSession`` is the run's memory of which value got which mark (``<EMAIL_1>``): it only grows, the same value
always gets the same mark and a new value gets the next number. A ``Redactor`` masks text against a session and can
check afterwards that no value the session knows is left in clear. ``RegexRedactor`` is the default kind; it wraps
``guard.redact`` (the pattern table) and adds the input rules (types, size, forged marks) around it.

What the regex kind does NOT see (names in free prose, obfuscated or spaced IBANs, images, PDFs) is listed in the
README; this module never claims more than ``guard.redact`` covers. No put-back exists here (ticket C1f).
"""

from __future__ import annotations

import hashlib
import inspect
import re
import sys
from collections.abc import Mapping
from typing import Any, NoReturn, Protocol, runtime_checkable

import hadavin_sdk.guard.redact  # noqa: F401  (loads the submodule)

# The submodule, not `guard.redact` the function that guard/__init__ exports under the same name.
_redact = sys.modules["hadavin_sdk.guard.redact"]

# Bump whenever guard/redact.py PATTERNS or the sweep rules change (a test pins the hashes below).
REGEX_VERSION = "1"
DEFAULT_MAX_DOC_CHARS = 200_000
# Longest run of non-space characters accepted. Some patterns (HIGHENTROPY, EMAIL) rescan a long unbroken run from
# every start, so time grows with its square: 10,000 "=" took 0.8 s, 190,000 about 4 minutes; capped, the worst 190,000-character case measured 4 s. A real value (key,
# token, email, IBAN) is far shorter than this; a longer run is refused (`too_large`), never passed on unmasked.
MAX_TOKEN_CHARS = 2048
_LONG_TOKEN = re.compile(rf"\S{{{MAX_TOKEN_CHARS + 1}}}")
_MARK = _redact._PLACEHOLDER  # <KIND_n>, the one shape of a mark
# File signatures that are not text: PDF, PNG, JPEG, GIF, zip (and so docx/xlsx).
_SIGNATURES = (b"%PDF-", b"\x89PNG", b"\xff\xd8\xff", b"GIF87a", b"GIF89a", b"PK\x03\x04")
_SIGNATURE_TEXT = tuple(s.decode("latin-1") for s in _SIGNATURES)
_BOM = "﻿"

CODES = ("unsupported_input", "too_large", "forged_mark", "self_check_failed", "internal")


class RedactionError(RuntimeError):
    """Masking refused or failed. Carries a code and nothing else: no text, no value, no cause."""

    def __init__(self, code: str) -> None:
        super().__init__(code)
        self.code = code

    def __str__(self) -> str:
        return self.code


def _refuse(code: str) -> NoReturn:
    raise RedactionError(code) from None


class MaskSession:
    """One run's marks. Append-only; the mapping is private and the object cannot be copied or pickled."""

    __slots__ = ("_mapping",)

    def __init__(self) -> None:
        self._mapping: dict[str, str] = {}  # mark -> original, never exposed

    @property
    def counts(self) -> dict[str, int]:
        """How many distinct values each kind has marked so far."""
        out: dict[str, int] = {}
        for mark in self._mapping:
            kind = _redact._kind(mark)
            out[kind] = out.get(kind, 0) + 1
        return out

    def issued(self, mark: str) -> bool:
        return mark in self._mapping

    def _snapshot(self) -> dict[str, str]:
        return dict(self._mapping)

    def _absorb(self, mapping: Mapping[str, str]) -> None:
        """Take a grown mapping. Existing marks must be unchanged: nothing is renumbered or reassigned."""
        if any(mapping.get(k) != v for k, v in self._mapping.items()):
            _refuse("internal")
        self._mapping.update(mapping)

    def __repr__(self) -> str:
        return f"MaskSession(marks={len(self._mapping)})"

    def __reduce__(self) -> NoReturn:
        raise TypeError("MaskSession cannot be copied or pickled")


@runtime_checkable
class Redactor(Protocol):
    name: str
    version: str

    def mask(self, text: str, session: MaskSession) -> str: ...

    def check(self, masked: str, session: MaskSession) -> None: ...

    def find(self, text: str) -> list[str]: ...


def refuse_mark_keys(value: Any) -> None:
    """Dict keys are never masked, so a mark-shaped key can only be forged: ``forged_mark``."""
    stack = [value]
    while stack:
        item = stack.pop()
        if isinstance(item, dict):
            for key, child in item.items():
                if isinstance(key, str) and _MARK.search(key):
                    _refuse("forged_mark")
                stack.append(child)
        elif isinstance(item, (list, tuple)):
            stack.extend(item)


def decode_input(raw: str | bytes) -> str:
    """Text out of ``raw`` or ``unsupported_input``: UTF-8 strict (a BOM is dropped), no NUL, no file signature."""
    if isinstance(raw, (bytes, bytearray)):
        data = bytes(raw)
        if data.startswith(_SIGNATURES) or b"\x00" in data:
            _refuse("unsupported_input")
        try:
            text = data.decode("utf-8")
        except UnicodeDecodeError:
            _refuse("unsupported_input")
    elif isinstance(raw, str):
        text = raw
        try:
            text.encode("utf-8")  # a lone surrogate is not valid UTF-8
        except UnicodeEncodeError:
            _refuse("unsupported_input")
        if text.startswith(_SIGNATURE_TEXT) or "\x00" in text:
            _refuse("unsupported_input")
    else:
        _refuse("unsupported_input")
    return text.removeprefix(_BOM)


class RegexRedactor:
    """``guard.redact`` behind the Redactor protocol."""

    name = "regex"
    version = REGEX_VERSION

    def __init__(self, max_doc_chars: int = DEFAULT_MAX_DOC_CHARS) -> None:
        self.max_doc_chars = max_doc_chars

    def mask(self, text: str | bytes, session: MaskSession) -> str:
        try:
            if isinstance(text, (bytes, bytearray)) and len(text) > self.max_doc_chars * 4:
                _refuse("too_large")  # before decoding: UTF-8 holds at most 4 bytes per character
            text = decode_input(text)
            if len(text) > self.max_doc_chars or _LONG_TOKEN.search(text):
                _refuse("too_large")
            for m in _MARK.finditer(text):
                if not session.issued(m.group(1)):
                    _refuse("forged_mark")
            (out,), mapping = _redact.redact_many([text], session._snapshot())
            session._absorb(mapping)
            return out
        except RedactionError:
            raise
        except Exception:  # noqa: BLE001 - any failure is the code "internal", never its text
            _refuse("internal")

    def check(self, masked: str, session: MaskSession) -> None:
        """No session original (4+ characters, whole token, case-sensitive, the ones ``_sweep`` masks) in ``masked``."""
        try:
            known = {
                mark: original
                for mark, original in session._snapshot().items()
                if len(original) >= 4 and _redact._sweep(mark, original) is not None
            }
            # The sweep itself is the finder (trie, longest first) and it skips text inside marks, like masking does.
            if known and _redact._Redactor(known).sweep(masked) != masked:
                _refuse("self_check_failed")
        except RedactionError:
            raise
        except Exception:  # noqa: BLE001 - any failure is the code "internal", never its text
            _refuse("internal")

    def find(self, text: str) -> list[str]:
        """Kinds this text would have masked (empty: nothing). Does not touch any session."""
        return _redact.redact(text).kinds


def regex_fingerprint() -> tuple[str, str]:
    """sha256 of the pattern table and of the sweep rules. A test pins them to ``REGEX_VERSION``."""
    patterns = repr([(label, p.pattern, p.flags) for label, p in _redact.PATTERNS])
    sweep = inspect.getsource(_redact._sweep).replace("\r\n", "\n")
    sweep += repr((sorted(_redact.SECRET_KINDS), sorted(_redact._COMMON)))
    return (
        hashlib.sha256(patterns.encode()).hexdigest(),
        hashlib.sha256(sweep.encode()).hexdigest(),
    )


__all__ = [
    "CODES",
    "DEFAULT_MAX_DOC_CHARS",
    "MAX_TOKEN_CHARS",
    "REGEX_VERSION",
    "MaskSession",
    "RedactionError",
    "Redactor",
    "RegexRedactor",
    "decode_input",
    "refuse_mark_keys",
    "regex_fingerprint",
]
