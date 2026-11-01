"""Bounded retries for every network llm kind (ported from WARDEN ``llm.py``; design 4.3).

Each SDK's own retries are off, so this loop is the only one. A transient failure is retried with exponential
backoff and full jitter, up to ``max_attempts`` requests in all; still failing, it is ``ProviderExhausted``.
Anything else (401 bad key, 400 malformed request) fails the same way every time, so it is a ``ProviderError``
at once.

A provider's spend or quota cap (Claude API: the monthly cap is HTTP 429, error type ``rate_limit_error``,
``error.details.error_code == "enforced_spend_limit_reached"``, and no ``retry-after`` header; see
platform.claude.com/docs/en/api/rate-limits, read 2026-11-01) fails until it resets: the kind's
``spend_limit(exc)`` recognises it and it is raised as ``SpendLimitReached`` after ONE attempt. Other 429s are
throttles and are retried. A numeric ``retry-after`` is honoured as the wait, up to ``RETRY_AFTER_CEILING_S``;
a server asking for longer than that is not retried (``ProviderExhausted``): sleeping less than asked would only be
throttled again. The ceiling is a ceiling, not a floor: the wait is the larger of the jitter and the server's ask.

``deadline_s`` is a real wall-clock bound on one call, attempts and sleeps together: every attempt runs under the
time that is left, and an attempt still running when it runs out is abandoned (``DeadlineExceeded``). An abandoned
request can still finish and be billed at the vendor, so the caller must treat its cost as unknown (the agent loop
keeps the reserved worst case booked). ``deadline_s=None`` turns the bound off; the config default is not None.

Vendor-neutral (lock-in audit 2026-10-31, row 2): this module knows HTTP statuses, the standard library's network
errors and TLS, nothing else. Each kind knows its own SDK's errors and passes ``retryable(exc) -> bool | None``
(None: no opinion, the generic rule decides) and ``detail(exc) -> str`` (an error code safe to log).
"""

from __future__ import annotations

import random
import ssl
import threading
import time
from collections.abc import Callable

from hadavin_sdk.llm.protocol import (
    DeadlineExceeded,
    ProviderError,
    ProviderExhausted,
    SpendLimitReached,
)

BASE_DELAY_S = 0.5
MAX_DELAY_S = 8.0  # ceiling of the jittered backoff
RETRY_AFTER_CEILING_S = 60.0  # longest server-requested wait we honour

Retryable = Callable[[BaseException], "bool | None"]

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
    """Seconds the server asked for (``Retry-After``, numeric form only), not capped; else 0. Not finite or
    negative counts as no ask."""
    headers = getattr(exc, "headers", None) or getattr(
        getattr(exc, "response", None), "headers", None
    )
    try:
        asked = float(headers.get("retry-after"))
    except (AttributeError, TypeError, ValueError):
        return 0.0
    return asked if 0.0 < asked < float("inf") else 0.0


def _bounded[T](call: Callable[[], T], seconds: float, label: str) -> T:
    """Run ``call`` for at most ``seconds`` of wall clock. On timeout the worker thread is abandoned (it ends at
    the kind's socket timeout) and its result is discarded."""
    box: dict[str, object] = {}

    def run() -> None:
        try:
            box["value"] = call()
        except BaseException as exc:  # noqa: BLE001 - re-raised in the caller's thread
            box["error"] = exc

    worker = threading.Thread(target=run, daemon=True, name=f"{label}-attempt")
    worker.start()
    worker.join(max(0.0, seconds))
    if worker.is_alive():
        raise DeadlineExceeded(f"{label}: attempt still running at the deadline")
    if "error" in box:
        raise box["error"]  # type: ignore[misc]
    return box["value"]  # type: ignore[return-value]


def describe(exc: BaseException, detail: Callable[[BaseException], str] | None = None) -> str:
    """Class, status and the kind's error code only: an SDK message can quote the request."""
    parts = [type(exc).__name__, str(status(exc) or ""), detail(exc) if detail else ""]
    return " ".join(p for p in parts if p)


def with_retry[T](
    call: Callable[[], T],
    *,
    label: str,
    max_attempts: int,
    sleep: Callable[[float], None] = time.sleep,
    retryable: Retryable | None = None,
    detail: Callable[[BaseException], str] | None = None,
    spend_limit: Callable[[BaseException], bool] | None = None,
    deadline_s: float | None = None,
    clock: Callable[[], float] = time.monotonic,
) -> T:
    started = clock()
    for attempt in range(1, max_attempts + 1):
        try:
            if deadline_s is None:
                return call()
            left = deadline_s - (clock() - started)
            if left <= 0:
                raise DeadlineExceeded(f"{label}: deadline {deadline_s}s reached")
            return _bounded(call, left, label)
        except ProviderError:
            raise
        except Exception as exc:  # every failure is classified below, never swallowed
            if spend_limit is not None and spend_limit(exc):
                raise SpendLimitReached(f"{label}: {describe(exc, detail)} spend limit") from exc
            if not transient(exc, retryable):
                raise ProviderError(f"{label}: {describe(exc, detail)}") from exc
            if attempt == max_attempts:
                raise ProviderExhausted(
                    f"{label}: {describe(exc, detail)} after {max_attempts} attempts"
                ) from exc
            # Full jitter spreads retries from many runs hitting one throttled account (not crypto); never
            # sooner than the server asked.
            jitter = random.uniform(0, min(MAX_DELAY_S, BASE_DELAY_S * 2 ** (attempt - 1)))  # noqa: S311
            asked = retry_after(exc)
            if asked > RETRY_AFTER_CEILING_S:
                raise ProviderExhausted(
                    f"{label}: {describe(exc, detail)} server asked {asked:g}s, over the "
                    f"{RETRY_AFTER_CEILING_S:g}s ceiling"
                ) from exc
            delay = max(jitter, asked)
            if deadline_s is not None and clock() - started + delay > deadline_s:
                raise ProviderExhausted(
                    f"{label}: {describe(exc, detail)} deadline {deadline_s}s reached"
                ) from exc
            sleep(delay)
    raise AssertionError("unreachable")  # max_attempts >= 1 (settings)
