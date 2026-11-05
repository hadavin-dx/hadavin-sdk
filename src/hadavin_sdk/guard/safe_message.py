"""One safe way to put an exception into a log line or a stored error field.

Exception text can carry the very values the redactor exists to hide (a detector that chokes on a document
repeats pieces of it). `safe_text` and `safe_message` therefore:

* show the text only for exception classes whose whole class chain is Python built-ins or ``hadavin_sdk``
  (an allowlist: a driver, SDK, HTTP or user class, or any subclass of one, or any OSError, shows its class
  name only, because its text can carry hosts, users, DSNs or tokens);
* cap the input, fold look-alike characters (NFKC) and drop invisible format characters, so a value cannot hide
  behind a zero-width character or a full-width form;
* mask everything first and cut second, so a value that straddles the cut is never half shown;
* fail closed: if masking itself raises (including RecursionError), the text is dropped.

Coverage limits (inherited from ``guard.redact``, stated so nobody over-trusts this): a name in free prose is
not recognised; an IBAN written with spaces is not recognised; lowercase hex signatures in presigned URLs are
not recognised. The strict xfail tests in ``tests/test_c18a_safe_message.py`` carry an expiry note: when the
redactor learns one of these, that test starts passing and must be turned into a normal test.
"""

from __future__ import annotations

import unicodedata

from hadavin_sdk.guard.redact import redact

# The text of an exception is shown only if EVERY class in its MRO (but ``object``) lives in one of these.
_TRUSTED_MODULES = frozenset({"builtins", "hadavin_sdk"})
_PRECAP_FACTOR = 8  # redact sees at most limit * 8 characters; the final cut is still after masking
UNAVAILABLE = "(message unavailable)"


def _trusted(exc: BaseException) -> bool:
    if isinstance(exc, OSError):  # sockets, files, DNS: hosts and paths
        return False
    for cls in type(exc).__mro__:
        if cls is object:
            continue
        mod = getattr(cls, "__module__", None)
        if not isinstance(mod, str) or mod.split(".")[0] not in _TRUSTED_MODULES:
            return False
    return True


def safe_text(exc: BaseException, limit: int = 300) -> str:
    """The masked, one-line text of `exc`, at most `limit` characters; empty if withheld, UNAVAILABLE if masking failed."""
    if limit <= 0:
        raise ValueError("limit must be positive")
    if not _trusted(exc):
        return ""
    try:
        text = str(exc)[: limit * _PRECAP_FACTOR]
        text = "".join(
            c for c in unicodedata.normalize("NFKC", text) if unicodedata.category(c) != "Cf"
        )
        masked = redact(text).text
    except Exception:  # noqa: BLE001 - fail closed on anything, RecursionError included
        return UNAVAILABLE
    # Mask the whole capped text before cutting, then cut: a trailing half-mark is fine, a half-value is not.
    return " ".join(masked.split())[:limit]


def safe_message(exc: BaseException, limit: int = 300) -> str:
    """`ClassName: text` (masked, one line); `ClassName` alone if the text is withheld or empty."""
    name = type(exc).__name__
    text = safe_text(exc, limit)
    return f"{name}: {text}" if text else name
