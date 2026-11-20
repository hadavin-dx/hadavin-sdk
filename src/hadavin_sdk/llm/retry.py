"""Bounded retries for every network llm kind (ported from WARDEN ``llm.py``; design 4.3).

Each SDK's own retries are off, so this loop is the only one. A transient failure is retried with exponential
backoff and full jitter, up to ``max_attempts`` requests in all; still failing, it is ``ProviderExhausted``.
Anything else (401 bad key, 400 malformed request) fails the same way every time, so it is a ``ProviderError``
at once.

Vendor-neutral (lock-in audit 2026-10-31, row 2): this module knows HTTP statuses, the standard library's network
errors and TLS, nothing else. Each kind knows its own SDK's errors and passes ``retryable(exc) -> bool | None``
(None: no opinion, the generic rule decides) and ``detail(exc) -> str`` (an error code safe to log).

The mark "refused before any response" (``ProviderError.refused_before_response``, read by the model gate, which
then settles the spend reservation at 0 instead of the worst case) is set to True here and nowhere else (a kind
may only clear it: openai_compat does, for its second request). It is True in two cases, and only when no
attempt of the call got any other answer, timed out, was cut off or failed to parse:
  1. the final error is not retried, every earlier attempt was never sent (the connection was refused or the
     host name did not resolve: ``never_sent``), and the final error is itself never sent or carries an HTTP
     status the kind counts as refused (``refused_statuses``: ``REFUSED_STATUSES`` = 400, 401, 403, 404, 413,
     422 by default; the openai_compat kind narrows it to 401, 403, 404);
  2. the retries ran out (``ProviderExhausted``) and EVERY attempt ended in HTTP 429 (throttled) or was never
     sent, in any mix. NOT YET CONSUMED: the model gate ignores the mark on ``ProviderExhausted`` by type
     (requests/to-core-c-1-exhausted-mark.md), so rule 2 sets the mark but settles nothing until the gate honours
     it; it is not evidence that the case is covered. Rule 2 is also not narrowed for routers: a 429 from a router
     (openai_compat) may follow upstream work, so a gate honouring it must treat that kind as unmarked.
Everything else leaves the mark False: 408, 409 and 5xx on any attempt, a 429 followed by an error that is not
retried (a 400 after a 429 stays unmarked), and a 429 that a kind chose not to retry. A parse failure of an
answer is wrapped here into a new ``ProviderError`` like any other failure and gets the normal rule (unmarked
unless never sent or status-refused); no adapter raises ``ProviderError`` from its own call.
A cause chain longer than the walk limit counts as NOT never sent.
Stated limit (UNVERIFIED for every network kind): the list follows the HTTP meaning of
the codes (the request was rejected before any model work). Whether a given provider bills a 400, 401, 403 or
429 was not verified against its billing rules. A provider that bills one of them is under-counted by that call.
For a kind whose base_url can be any router or proxy (openai_compat) a 400, 413 or 422 may come from the
router after the upstream model consumed tokens, so only 401, 403 and 404 count there. The Claude kind
narrows the same way unless it is built for the direct Claude API (``direct_api``): on Vertex or Foundry a
gateway can answer after the model started.
"""

from __future__ import annotations

import random
import socket
import ssl
import time
from collections.abc import Callable

from hadavin_sdk.llm.protocol import ProviderError, ProviderExhausted

BASE_DELAY_S = 0.5
MAX_DELAY_S = 8.0

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


# Statuses that reject a request before any model work (see the module docstring for the stated limit).
REFUSED_STATUSES = frozenset({400, 401, 403, 404, 413, 422})
# Throttled: retried, and no model work was done for it (same stated limit).
THROTTLED_STATUS = 429


_CHAIN_LIMIT = 8


def _chain(exc: BaseException) -> tuple[list[BaseException], bool]:
    """The error and what it wraps (urllib's ``reason``, ``__cause__``, ``__context__``), at most 8 deep;
    the flag is True when the walk stopped at the limit with errors left unvisited."""
    seen: list[BaseException] = []
    todo: list[object] = [exc]
    while todo:
        e = todo.pop()
        if isinstance(e, BaseException) and e not in seen:
            if len(seen) >= _CHAIN_LIMIT:
                return seen, True
            seen.append(e)
            todo += [getattr(e, "reason", None), e.__cause__, e.__context__]
    return seen, False


def never_sent(exc: BaseException) -> bool:
    """True when the request certainly never left: the connection was refused or the name did not resolve,
    and nothing in the chain is a timeout or carries an HTTP status."""
    chain, truncated = _chain(exc)
    if truncated:
        return False  # part of the chain was not looked at: the safe answer
    if any(isinstance(e, TimeoutError) or status(e) is not None for e in chain):
        return False
    return any(isinstance(e, (ConnectionRefusedError, socket.gaierror)) for e in chain)


def transient(exc: BaseException, retryable: Retryable | None = None) -> bool:
    if any(isinstance(e, ssl.SSLError) and not isinstance(e, _TLS_DROPS) for e in _chain(exc)[0]):
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
    http_status: Callable[[BaseException], int | None] | None = None,
    refused_statuses: frozenset[int] = REFUSED_STATUSES,
) -> T:
    """``http_status(exc)`` is the kind's way to the HTTP status of its SDK's errors when the generic
    ``status`` finds none; it only feeds the mark, never the retry decision. ``refused_statuses`` is the
    kind's list of statuses that mean refused before any response (default ``REFUSED_STATUSES``)."""
    unsent = True  # every attempt so far failed before any request was sent
    unbilled = True  # every attempt so far was never sent or was answered 429 (throttled)
    for attempt in range(1, max_attempts + 1):
        try:
            return call()
        except ProviderError:
            raise
        except Exception as exc:  # every failure is classified below, never swallowed
            this_unsent = never_sent(exc)
            code = status(exc)
            if code is None and http_status is not None:
                code = http_status(exc)
            if not transient(exc, retryable):
                error = ProviderError(f"{label}: {describe(exc, detail)}")
                error.refused_before_response = unsent and (this_unsent or code in refused_statuses)
                raise error from exc
            unsent = unsent and this_unsent
            unbilled = unbilled and (this_unsent or code == THROTTLED_STATUS)
            if attempt == max_attempts:
                exhausted = ProviderExhausted(
                    f"{label}: {describe(exc, detail)} after {max_attempts} attempts"
                )
                exhausted.refused_before_response = unbilled
                raise exhausted from exc
            # Full jitter spreads retries from many runs hitting one throttled account (not crypto); never
            # sooner than the server asked.
            jitter = random.uniform(0, min(MAX_DELAY_S, BASE_DELAY_S * 2 ** (attempt - 1)))  # noqa: S311
            sleep(max(jitter, retry_after(exc)))
    raise AssertionError("unreachable")  # max_attempts >= 1 (settings)
