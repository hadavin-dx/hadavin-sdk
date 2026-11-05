"""One safe way to put an exception into a log line or a stored error field.

Exception text can carry the very values the redactor exists to hide (a detector that chokes on a document
repeats pieces of it). `safe_text` and `safe_message` therefore:

* show the text only for exception classes whose whole class chain (MRO) lives in Python built-ins or
  ``hadavin_sdk``; a driver, SDK, HTTP or user class, any subclass of one, and any OSError shows its class
  name only, because its text can carry hosts, users, DSNs or tokens. A caller that knows a class is safe to
  show (extract.py: pydantic validation errors, which it needs for the retry prompt) names its top-level
  modules in ``also_trust``;
* strip invisible characters, collapse whitespace, cap the input, then fold look-alike characters (NFKC),
  so a value cannot hide behind a zero-width character, a full-width form or a wall of padding;
* mask first and cut second, so a value that straddles the cut is never half shown; when the text was cut
  before masking, the trailing partial word is dropped and ``[truncated]`` is added;
* fail closed: if masking itself raises (including RecursionError), the text is replaced by a fixed note.

What this does NOT promise (stated so nobody over-trusts it):
* Built-in exceptions can carry arbitrary document text: ``KeyError(key)``, ``ValueError(f"cannot parse {doc}")``,
  ``AssertionError(data)``, ``SyntaxError``. Only patterns the redactor recognises are masked. I kept built-ins
  shown (masked) because an operator needs the message of a failing step; the alternative, showing only
  ``hadavin_sdk`` classes, would make every tick failure a bare class name. Revisit if a client's threat model
  needs it: remove ``builtins`` from ``_TRUSTED_MODULES``.
* The allowlist trusts the *declared* ``__module__`` of each class; a class that lies about its module is
  trusted.
* Coverage limits inherited from ``guard.redact``: a name in free prose, a spaced IBAN and lowercase-hex
  presigned-URL signatures are not recognised; cross-script look-alikes are not folded by NFKC (an email with
  a Cyrillic letter is still masked today because the email pattern is Unicode-wide; other value kinds may not be). Strict xfail tests mark each; when the redactor learns one, that test XPASSes, the
  run fails, and the test must become a normal test (review again 2027-01-31; nothing enforces the date).
"""

from __future__ import annotations

import unicodedata

from hadavin_sdk.guard.redact import redact

# The text of an exception is shown only if EVERY class in its MRO (but ``object``) lives in one of these.
_TRUSTED_MODULES = frozenset({"builtins", "hadavin_sdk"})
_RAW_FACTOR = (
    64  # str(exc) is read up to limit * 64 characters (so padding cannot push a value out of view)
)
_PRECAP_FACTOR = 8  # redact sees at most limit * 8 characters, measured after folding and stripping
UNAVAILABLE = "(message unavailable)"
WITHHELD = "(withheld)"
TRUNCATED = " [truncated]"
# Invisible characters that can split a value without changing how it looks: format (Cf), private use (Co),
# control (Cc) except the whitespace kinds, plus known blank fillers and variation selectors.
_KEEP_CONTROL = "\t\n\r\x0b\x0c"
_FILLERS = frozenset("\u034f\u115f\u1160\u3164\uffa0\u2800")


def _invisible(c: str) -> bool:
    cat = unicodedata.category(c)
    if cat == "Cc":
        return c not in _KEEP_CONTROL
    return (
        cat in {"Cf", "Co"}
        or c in _FILLERS
        or "\ufe00" <= c <= "\ufe0f"
        or "\U000e0100" <= c <= "\U000e01ef"
    )


def _clean(s: str) -> str:
    return " ".join("".join(c for c in s if not _invisible(c)).split())


def _trusted(exc: BaseException, also_trust: frozenset[str]) -> bool:
    if isinstance(exc, OSError):  # sockets, files, DNS: hosts and paths
        return False
    allowed = _TRUSTED_MODULES | also_trust
    for cls in type(exc).__mro__:
        if cls is object:
            continue
        mod = getattr(cls, "__module__", None)
        if not isinstance(mod, str) or mod.split(".")[0] not in allowed:
            return False
    return True


def _cut_partial_word(s: str) -> str:
    cut = s.rfind(" ")
    return s[:cut] if cut >= 0 else ""


def safe_text(
    exc: BaseException, limit: int = 300, also_trust: frozenset[str] = frozenset()
) -> str:
    """The masked, one-line text of `exc`, at most `limit` characters.

    WITHHELD if the class may not show its text, UNAVAILABLE if masking failed, "" if there was no text."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if not _trusted(exc, also_trust):
        return WITHHELD
    try:
        full = str(exc)
        cap = limit * _PRECAP_FACTOR
        # Read at most 64*limit characters; NFKC can grow that ~18x, so it is capped again below.
        text = _clean(full[: limit * _RAW_FACTOR])
        truncated = len(full) > limit * _RAW_FACTOR
        text = _clean(unicodedata.normalize("NFKC", text))  # NFKC can expand a character ~18x
        if len(text) > cap:  # post-fold cap
            text, truncated = text[:cap], True  # post-fold cut
        if truncated:  # a value may be cut in half at the edge: drop the last word before masking
            text = _cut_partial_word(text)
        masked = redact(text).text
    except Exception:  # noqa: BLE001 - fail closed on anything, RecursionError included
        return UNAVAILABLE
    if truncated:
        masked += TRUNCATED
    return masked[:limit]  # the input had no whitespace runs or newlines and the marks add none


def with_class(exc: BaseException, text: str) -> str:
    """`ClassName: text`; the class name alone if the text is empty or withheld."""
    name = type(exc).__name__
    return f"{name}: {text}" if text and text != WITHHELD else name


def safe_message(
    exc: BaseException, limit: int = 300, also_trust: frozenset[str] = frozenset()
) -> str:
    """`ClassName: text` (masked, one line); `ClassName` alone if the text is withheld or empty."""
    return with_class(exc, safe_text(exc, limit, also_trust))
