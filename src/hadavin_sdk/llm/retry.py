"""Bounded retries for every network llm kind (ported from WARDEN ``llm.py``; design 4.3).

Each SDK's own retries are off, so this loop is the only one. A transient failure is retried with exponential
backoff and full jitter, up to ``max_attempts`` requests in all; still failing, it is ``ProviderExhausted``.
Anything else (401 bad key, 400 malformed request) fails the same way every time, so it is a ``ProviderError``
at once.

Vendor-neutral (lock-in audit 2026-10-31, row 2): this module knows HTTP statuses, the standard library's network
errors and TLS, nothing else. Each kind knows its own SDK's errors and passes ``retryable(exc) -> bool | None``
(None: no opinion, the generic rule decides) and ``facts(exc) -> ProviderFacts`` (checked values only).

The text of a raised error is built from a fixed grammar: the label, one class text, a checked status, a checked
error type and the attempt count. No word of a reply is ever copied into it.
"""

from __future__ import annotations

import random
import ssl
import time
import urllib.error
from collections.abc import Callable

from hadavin_sdk.codes import ProviderErrorType
from hadavin_sdk.guard.diagnostic import class_name_of
from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted
from hadavin_sdk.llm.provider_facts import (
    ProviderFacts,
    clean_status,
    safe_attr,
    safe_facts,
    status_error_type,
)
from hadavin_sdk.neverraise import Site, record

BASE_DELAY_S = 0.5
MAX_DELAY_S = 8.0

Retryable = Callable[[BaseException], "bool | None"]
Facts = Callable[[BaseException], ProviderFacts]

# What the retry decision gave when it raised: never returned by any function, only compared with ``is``.
DECISION_FAILED: object = object()

# A peer closing the TLS connection mid-handshake or mid-read: a dropped connection, worth another attempt.
_TLS_DROPS = (ssl.SSLEOFError, ssl.SSLZeroReturnError)


def status(exc: BaseException) -> int | None:
    """The HTTP status an error carries as an int: ``status_code`` (most SDKs) or ``code`` (urllib)."""
    for value in (getattr(exc, "status_code", None), getattr(exc, "code", None)):
        if isinstance(value, int) and not isinstance(value, bool):
            return value
    return None


def retryable_status(code: int) -> bool:
    return code in (408, 429) or code >= 500


def _chain(exc: BaseException) -> list[BaseException]:
    """The error and what it wraps (urllib's ``reason``, ``__cause__``, ``__context__``), at most 8 deep."""
    seen: list[BaseException] = []
    todo: list[object] = [exc]
    while todo and len(seen) < 8:
        e = todo.pop()
        if isinstance(e, BaseException) and e not in seen:
            seen.append(e)
            todo += [getattr(e, "reason", None), e.__cause__, e.__context__]
    return seen


def transient(exc: BaseException, retryable: Retryable | None = None) -> bool:
    if any(isinstance(e, ssl.SSLError) and not isinstance(e, _TLS_DROPS) for e in _chain(exc)):
        return False  # a certificate or protocol problem fails the same way every time
    if retryable is not None and (said := retryable(exc)) is not None:
        return said
    code = status(exc)
    if code is not None:
        return retryable_status(code)
    return isinstance(exc, OSError)  # URLError, socket timeouts, connection resets


def retry_after(exc: BaseException) -> float:
    """Seconds the server asked for (``Retry-After``, numeric form only), capped at MAX_DELAY_S; else 0."""
    headers = getattr(exc, "headers", None) or getattr(
        getattr(exc, "response", None), "headers", None
    )
    try:
        return min(MAX_DELAY_S, max(0.0, float(headers.get("retry-after"))))
    except (AttributeError, TypeError, ValueError):
        return 0.0


def default_facts(exc: BaseException) -> ProviderFacts:
    """The neutral adapter (standard library only): status from ``status_code`` or ``code``, the type from the status table.

    With no status it walks the chain: any ``TimeoutError`` anywhere gives ``timeout`` (even when a ``URLError`` comes first),
    else another ``OSError`` that is not an ``HTTPError`` gives ``connection``. It never reads ``args``, ``str(exc)``, ``msg``,
    ``hdrs``, ``headers``, ``fp`` or ``read()``; ``reason`` is only tested for its type, by ``_chain``."""
    status_value = clean_status(safe_attr(exc, "status_code"))
    if status_value is None:
        status_value = clean_status(safe_attr(exc, "code"))
    error_type = status_error_type(status_value)
    if status_value is None:
        links = _chain(exc)
        if any(isinstance(e, TimeoutError) for e in links):
            error_type = ProviderErrorType.timeout
        elif any(
            isinstance(e, OSError | ssl.SSLError) and not isinstance(e, urllib.error.HTTPError)
            for e in links
        ):
            error_type = ProviderErrorType.connection
    return ProviderFacts(status_value, error_type, None)


def describe(exc: BaseException, facts: ProviderFacts) -> str:
    """``<ClassText>[ <status>][ <error_type>]``: the class text of ``class_name_of`` and two checked facts. The only
    place in ``llm/`` that turns a class into text."""
    try:
        class_text = class_name_of(exc)
    except Exception:  # noqa: BLE001 - never-raise guard: the class text of a hostile class falls back to a fixed word
        record(Site.retry_class_text)
        class_text = "dynamic_class"
    parts = [class_text]
    if facts.status is not None:
        parts.append(str(facts.status))
    if facts.error_type is not None:
        parts.append(facts.error_type.value)
    return " ".join(parts)


def _close_failed_http(exc: BaseException) -> None:
    """Close the socket of a failed ``HTTPError`` before the next request or the raise. Never raises an ``Exception``."""
    try:
        if isinstance(exc, urllib.error.HTTPError):
            exc.close()
    except Exception:  # noqa: BLE001 - never-raise guard: a close that fails never replaces the real provider error
        record(Site.retry_close_failed_http)


def with_retry[T](
    call: Callable[[], T],
    *,
    label: str,
    max_attempts: int,
    sleep: Callable[[float], None] = time.sleep,
    retryable: Retryable | None = None,
    facts: Facts | None = None,
) -> T:
    for attempt in range(1, max_attempts + 1):
        try:
            return call()
        except ProviderError:
            raise
        except Exception as exc:  # noqa: BLE001 - a conversion, not a guard: every call failure becomes a retry or a ProviderError
            # The ordinary failure path (a 429, a reset connection), so nothing is recorded here: the counters show faults only.
            # ``from None`` keeps the provider text out of __cause__.
            _close_failed_http(exc)
            try:
                decision: object = bool(transient(exc, retryable))
            except Exception:  # noqa: BLE001 - never-raise guard: a crashed retry decision is booked as billed, never raised raw
                record(Site.retry_decision)
                decision = DECISION_FAILED
            if decision is DECISION_FAILED:
                raise _billed(exc, label, attempt, facts) from None
            if not decision:
                f = safe_facts(facts or default_facts, exc)
                raise ProviderError(
                    f"{label}: {describe(exc, f)}",
                    status=f.status,
                    error_type=f.error_type,
                    request_id=f.request_id,
                    retryable=False,
                    retry_count=attempt,
                ) from None
            if attempt == max_attempts:
                f = safe_facts(facts or default_facts, exc)
                raise ProviderExhausted(
                    f"{label}: {describe(exc, f)} after {max_attempts} attempts",
                    status=f.status,
                    error_type=f.error_type,
                    request_id=f.request_id,
                    retryable=True,
                    retry_count=attempt,
                ) from None
            # Full jitter spreads retries from many runs hitting one throttled account (not crypto); never
            # sooner than the server asked.
            jitter = random.uniform(0, min(MAX_DELAY_S, BASE_DELAY_S * 2 ** (attempt - 1)))  # noqa: S311
            try:
                wait = max(jitter, retry_after(exc))
            except Exception:  # noqa: BLE001 - never-raise guard: a crashed wait is booked as billed, never raised raw
                record(Site.retry_wait)
                raise _billed(exc, label, attempt, facts) from None
            sleep(wait)
    raise AssertionError("unreachable")  # max_attempts >= 1 (settings)


def _billed(exc: BaseException, label: str, attempt: int, facts: Facts | None) -> ProviderExhausted:
    """The error for a decision failure: not retried, billing unknown, so the billed class (callers book the worst case)."""
    f = safe_facts(facts or default_facts, exc)
    text = f"{label}: {describe(exc, f)} after {attempt} attempts"
    return ProviderExhausted(
        text,
        status=f.status,
        error_type=f.error_type,
        request_id=f.request_id,
        retryable=None,
        retry_count=attempt,
    )
