"""Circuit breaker and fallback around any ``LLM`` (G-05). Vendor-neutral: it wraps the ``LLM`` protocol and knows
only ``ProviderExhausted`` (the provider kept failing after its retries) and ``SpendLimitReached``.

After ``failures`` such outcomes in a row the circuit opens: calls skip the primary (no wasted attempts, no hammering
a provider that is down) and go to ``fallback`` if one is given, else fail at once with ``ProviderExhausted``. After
``reset_after_s`` one probe call is let through; success closes the circuit, failure re-opens it. A plain
``ProviderError`` (bad request, bad key) is the caller's fault, not an outage: it neither trips nor falls back.

The fallback must serve the same route names; it is a different vendor or region on purpose (no single dependency).
Wiring it from client config (``backends.llm``) is a factory change, kept out of this PR (open PR #42 edits the factory).
"""

from __future__ import annotations

import threading
import time
from collections.abc import Callable
from typing import Any

from hadavin_sdk.llm.protocol import LLM, ProviderExhausted, SpendLimitReached
from hadavin_sdk.models import Reply

_TRIPS = (ProviderExhausted, SpendLimitReached)


class CircuitBreaker:
    def __init__(
        self,
        failures: int = 5,
        reset_after_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
    ) -> None:
        if failures < 1 or reset_after_s <= 0:
            raise ValueError("failures >= 1 and reset_after_s > 0")
        self.failures, self.reset_after_s, self._clock = failures, reset_after_s, clock
        self._n, self._opened_at, self._probing = 0, None, False
        self._lock = threading.Lock()

    def allow(self) -> bool:
        with self._lock:
            if self._opened_at is None:
                return True
            if not self._probing and self._clock() - self._opened_at >= self.reset_after_s:
                self._probing = True  # exactly one probe at a time
                return True
            return False

    def success(self) -> None:
        with self._lock:
            self._n, self._opened_at, self._probing = 0, None, False

    def failure(self) -> None:
        with self._lock:
            self._n += 1
            if self._probing or self._n >= self.failures:
                self._opened_at, self._probing = self._clock(), False

    def release(self) -> None:
        """A probe ended in a non-outage error: let the next call probe again."""
        with self._lock:
            self._probing = False


class ResilientLLM:
    def __init__(
        self, primary: LLM, fallback: LLM | None = None, breaker: CircuitBreaker | None = None
    ) -> None:
        self.primary, self.fallback, self.breaker = primary, fallback, breaker or CircuitBreaker()

    def __getattr__(self, name: str) -> Any:  # call_timeout_s, max_attempts: tick.py reads them
        return getattr(self.primary, name)

    def chat(self, *args: Any, **kwargs: Any) -> Reply:
        if not self.breaker.allow():
            return self._fallback("circuit open", *args, **kwargs)
        try:
            out = self.primary.chat(*args, **kwargs)
        except _TRIPS as exc:
            self.breaker.failure()
            return self._fallback(type(exc).__name__, *args, **kwargs, _cause=exc)
        except BaseException:
            self.breaker.release()
            raise
        self.breaker.success()
        return out

    def _fallback(
        self, why: str, *args: Any, _cause: BaseException | None = None, **kwargs: Any
    ) -> Reply:
        if self.fallback is None:
            if _cause is not None:
                raise _cause
            raise ProviderExhausted(f"llm: {why}, no fallback configured")
        return self.fallback.chat(*args, **kwargs)
