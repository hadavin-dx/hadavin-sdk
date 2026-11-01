"""Circuit breaker and fallback around any ``LLM`` (G-05). Vendor-neutral: it wraps the ``LLM`` protocol and knows
only ``ProviderExhausted`` (the provider kept failing after its retries) and ``SpendLimitReached``.

After ``failures`` such outcomes in a row the circuit opens: calls skip the primary (no wasted attempts, no hammering
a provider that is down) and go to ``fallback`` if one is given, else fail at once with the typed error. After
``reset_after_s`` one probe call is let through; success closes the circuit, failure re-opens it. A plain
``ProviderError`` (bad request, bad key) is the caller's fault, not an outage: it neither trips nor falls back.

CUSTOMER DATA LEAVES FOR THE FALLBACK VENDOR. A fallback call replays the messages and the system prompt to a
different vendor, and the documents too only if ``send_documents_to_fallback=True`` (default False: a call that
carries documents fails closed with the primary's typed error instead, because documents are the client's data and
the contract names the vendors that may see it). Every fallback call is logged (route, why, which backend served,
whether documents went; never content), reported to the ``on_fallback`` hook (wire it to the audit sink) and marked
on the reply (``Reply.fallback_used``, ``Reply.served_by``).

``SpendLimitReached`` on the primary does NOT move traffic to another vendor by default: that would route around a
spend cap into a meter nobody set. Pass ``fallback_metered=True`` only when the fallback's cost is booked against
the same ``Limits`` (the agent loop reserves and settles every reply it receives, whichever backend served it).

The fallback must serve the same route names; it is a different vendor or region on purpose (no single dependency).
Wiring it from client config (``backends.llm``) is a factory change, kept out of this PR (open PR #42 edits the factory).
"""

from __future__ import annotations

import logging
import threading
import time
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

from hadavin_sdk.llm.protocol import LLM, ProviderExhausted, SpendLimitReached
from hadavin_sdk.models import Reply

_LOG = logging.getLogger("hadavin_sdk.llm.resilient")
_TRIPS = (ProviderExhausted, SpendLimitReached)


@dataclass(frozen=True)
class Ticket:
    """What ``allow`` hands out. Only a probe's outcome can change an open circuit: a call that started while it
    was closed and ends after it opened is stale and is ignored."""

    probe: bool
    epoch: int


class CircuitBreaker:
    def __init__(
        self,
        failures: int = 5,
        reset_after_s: float = 30.0,
        clock: Callable[[], float] = time.monotonic,
        probe_timeout_s: float = 60.0,
    ) -> None:
        if failures < 1 or reset_after_s <= 0 or probe_timeout_s <= 0:
            raise ValueError("failures >= 1, reset_after_s > 0, probe_timeout_s > 0")
        self.failures, self.reset_after_s, self._clock = failures, reset_after_s, clock
        self.probe_timeout_s = probe_timeout_s
        self._n, self._opened_at, self._probing, self._probe_at = 0, None, False, 0.0
        self._epoch = (
            0  # bumped when the circuit opens or a probe is abandoned: older tickets are stale
        )
        self._lock = threading.Lock()

    def allow(self) -> Ticket | None:
        """A ticket to call the primary with, or None (circuit open). One probe at a time; a probe that has not
        reported within ``probe_timeout_s`` (a hung call) is abandoned and the next caller probes."""
        with self._lock:
            if self._opened_at is None:
                return Ticket(False, self._epoch)
            t = self._clock()
            if self._probing and t - self._probe_at >= self.probe_timeout_s:
                self._probing, self._epoch = False, self._epoch + 1
            if not self._probing and t - self._opened_at >= self.reset_after_s:
                self._probing, self._probe_at = True, t
                return Ticket(True, self._epoch)
            return None

    def success(self, ticket: Ticket) -> None:
        with self._lock:
            if self._opened_at is None:
                self._n = 0
            elif ticket.probe and ticket.epoch == self._epoch:
                self._n, self._opened_at, self._probing = 0, None, False

    def failure(self, ticket: Ticket) -> None:
        with self._lock:
            if self._opened_at is None:
                self._n += 1
                if self._n >= self.failures:
                    self._opened_at, self._epoch = self._clock(), self._epoch + 1
            elif ticket.probe and ticket.epoch == self._epoch:
                self._opened_at, self._probing = self._clock(), False  # a failed probe re-opens
                self._epoch += 1
            # a stale non-probe failure while open: ignored (no new window, no touch of _probing)

    def release(self, ticket: Ticket) -> None:
        """A probe ended in a non-outage error: let the next call probe again."""
        with self._lock:
            if ticket.probe and ticket.epoch == self._epoch:
                self._probing = False


class ResilientLLM:
    def __init__(
        self,
        primary: LLM,
        fallback: LLM | None = None,
        breaker: CircuitBreaker | None = None,
        *,
        send_documents_to_fallback: bool = False,
        fallback_metered: bool = False,
        on_fallback: Callable[[dict[str, Any]], None] | None = None,
    ) -> None:
        self.primary, self.fallback, self.breaker = primary, fallback, breaker or CircuitBreaker()
        self.send_documents_to_fallback = send_documents_to_fallback
        self.fallback_metered = fallback_metered
        self.on_fallback = on_fallback
        self._spend_tripped = False

    def __getattr__(self, name: str) -> Any:  # call_timeout_s, max_attempts: tick.py reads them
        primary = self.__dict__.get("primary")
        if primary is None or name.startswith("__"):  # copy / pickle probe before __init__ ran
            raise AttributeError(name)
        return getattr(primary, name)

    def chat(self, *args: Any, **kwargs: Any) -> Reply:
        ticket = self.breaker.allow()
        if ticket is None:
            return self._fallback("circuit open", None, args, kwargs)
        try:
            out = self.primary.chat(*args, **kwargs)
        except _TRIPS as exc:
            self.breaker.failure(ticket)
            self._spend_tripped = isinstance(exc, SpendLimitReached)
            return self._fallback(type(exc).__name__, exc, args, kwargs)
        except BaseException:
            self.breaker.release(ticket)
            raise
        self.breaker.success(ticket)
        self._spend_tripped = False
        return out

    def _fallback(
        self, why: str, cause: BaseException | None, args: tuple[Any, ...], kwargs: dict[str, Any]
    ) -> Reply:
        def refuse(reason: str) -> BaseException:
            _LOG.warning("llm fallback refused: %s (primary: %s)", reason, why)
            if cause is not None:
                return cause
            if self._spend_tripped:
                return SpendLimitReached(f"llm: {why}, primary spend limit, fallback not metered")
            return ProviderExhausted(f"llm: {why}, {reason}")

        if self.fallback is None:
            raise refuse("no fallback configured")
        if (cause is None and self._spend_tripped or isinstance(cause, SpendLimitReached)) and (
            not self.fallback_metered
        ):
            raise refuse("spend limit and the fallback is not metered")
        documents = kwargs.get("documents")
        if documents and not self.send_documents_to_fallback:
            raise refuse("call carries documents and send_documents_to_fallback is off")
        served_by = getattr(self.fallback, "label", None) or type(self.fallback).__name__
        event = {
            "event": "llm_fallback",
            "why": why,
            "route": kwargs.get("route"),
            "served_by": served_by,
            "documents_sent": bool(documents),
        }
        _LOG.warning("llm fallback used: %s", event)
        if self.on_fallback is not None:
            self.on_fallback(
                event
            )  # an audit hook that raises stops the call: nothing leaves unrecorded
        out = self.fallback.chat(*args, **kwargs)
        return out.model_copy(update={"fallback_used": True, "served_by": served_by})
