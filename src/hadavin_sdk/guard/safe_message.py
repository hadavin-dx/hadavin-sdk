"""One safe way to put an exception into a log line or a stored error field.

Exception text can carry the very values the redactor exists to hide (a detector that chokes on a document
repeats pieces of it). `safe_message` masks first and cuts second, so a value that straddles the cut is never
half-shown. Driver and network errors carry hosts and users: their type says enough, so the text is withheld.
"""

from __future__ import annotations

from hadavin_sdk.guard.redact import redact

# Modules whose exceptions carry hosts, users or DSNs in their text.
_DRIVERS = ("psycopg", "urllib", "http", "botocore", "boto3", "socket", "ssl")
WITHHELD = "(driver error; details withheld)"


def safe_message(exc: BaseException, limit: int = 300) -> str:
    """`ClassName: text`, masked, on one line, at most `limit` characters of text; class name only if withheld."""
    name = type(exc).__name__
    if type(exc).__module__.split(".")[0] in _DRIVERS or isinstance(exc, OSError):
        return f"{name}: {WITHHELD}"
    try:
        text = str(exc)
    except Exception:  # noqa: BLE001 - a broken __str__ must not break the handler that logs it
        return f"{name}: (message unavailable)"
    # Mask the whole text before cutting, then cut: a trailing half-mark is fine, a half-value is not.
    masked = redact(text).text
    return f"{name}: {' '.join(masked.split())[:limit]}"
