"""Circuit breaker pattern for protecting against cascading failures.

Implements the circuit breaker pattern with three states:
- CLOSED: Normal operation, requests pass through
- OPEN: Too many failures, requests are rejected immediately
- HALF_OPEN: Recovery testing, limited requests pass through

Thread-safe: All state is protected by a reentrant lock.
No external dependencies: Uses only Python stdlib.
"""

from __future__ import annotations

import contextlib
import logging
import threading
import time
from collections.abc import Callable
from typing import Any, TypeVar

from .enums import CircuitState
from .models import CircuitBreakerState

logger = logging.getLogger(__name__)

T = TypeVar("T")


class CircuitBreakerOpen(Exception):
    """Raised when a call is rejected because the circuit breaker is open.

    Attributes:
        breaker_name: Name of the circuit breaker that rejected the call.
        time_until_half_open: Seconds until the breaker will try HALF_OPEN.
    """

    def __init__(self, breaker_name: str, time_until_half_open: float) -> None:
        self.breaker_name = breaker_name
        self.time_until_half_open = time_until_half_open
        super().__init__(
            f"Circuit breaker '{breaker_name}' is OPEN. Try again in {time_until_half_open:.1f}s."
        )


class CircuitBreaker:
    """Circuit breaker for protecting against cascading failures.

    Wraps function calls and tracks failures. When failures exceed
    the threshold, the breaker opens and rejects calls immediately
    (fail-fast) instead of waiting for timeouts.

    Example::

        from agent_killswitch import CircuitBreaker

        breaker = CircuitBreaker(
            name="openai-api",
            failure_threshold=5,
            recovery_timeout=30.0,
        )

        try:
            result = breaker.call(my_api_function, arg1, arg2)
        except CircuitBreakerOpen:
            print("API is down, using fallback")

    Args:
        name: Identifier for this circuit breaker.
        failure_threshold: Consecutive failures to trip the breaker.
        recovery_timeout: Seconds to wait before trying HALF_OPEN.
        half_open_max_calls: Max calls allowed in HALF_OPEN state.
        on_state_change: Callback on state transitions.
            Signature: (name, old_state, new_state) -> None
        on_open: Callback when breaker opens.
            Signature: (name, failure_count) -> None
        excluded_exceptions: Exception types that should NOT count as failures.
    """

    def __init__(
        self,
        name: str = "default",
        failure_threshold: int = 5,
        recovery_timeout: float = 30.0,
        half_open_max_calls: int = 1,
        on_state_change: Callable[[str, CircuitState, CircuitState], None] | None = None,
        on_open: Callable[[str, int], None] | None = None,
        excluded_exceptions: tuple[type[BaseException], ...] | None = None,
    ) -> None:
        self._state = CircuitBreakerState(
            name=name,
            failure_threshold=failure_threshold,
            recovery_timeout=recovery_timeout,
            half_open_max_calls=half_open_max_calls,
            last_state_change=time.monotonic(),
        )
        self._on_state_change = on_state_change
        self._on_open = on_open
        self._excluded = excluded_exceptions or ()
        self._lock = threading.RLock()
        self._half_open_calls = 0

    @property
    def name(self) -> str:
        """Name of this circuit breaker."""
        return self._state.name

    def get_state(self) -> CircuitState:
        """Get the current circuit breaker state.

        Returns:
            Current CircuitState.
        """
        with self._lock:
            self._maybe_transition_to_half_open()
            return self._state.state

    def _maybe_transition_to_half_open(self) -> None:
        """Check if it's time to transition from OPEN to HALF_OPEN."""
        if self._state.state != CircuitState.OPEN:
            return

        elapsed = time.monotonic() - self._state.last_state_change
        if elapsed >= self._state.recovery_timeout:
            self._transition(CircuitState.HALF_OPEN)

    def _transition(self, new_state: CircuitState) -> None:
        """Transition to a new state and fire callbacks."""
        old_state = self._state.state
        if old_state == new_state:
            return

        self._state.state = new_state
        self._state.last_state_change = time.monotonic()

        if new_state == CircuitState.CLOSED:
            self._state.failure_count = 0
            self._state.success_count = 0
            self._half_open_calls = 0
        elif new_state == CircuitState.HALF_OPEN:
            self._state.success_count = 0
            self._half_open_calls = 0

        logger.info(
            "circuit_breaker_state_change",
            extra={
                "name": self._state.name,
                "old_state": old_state.value,
                "new_state": new_state.value,
            },
        )

        if self._on_state_change is not None:
            try:
                self._on_state_change(self._state.name, old_state, new_state)
            except Exception as exc:
                logger.error(
                    "on_state_change callback error",
                    extra={"error": str(exc)},
                )

    def _record_failure(self) -> None:
        """Record a failure and possibly open the circuit."""
        self._state.failure_count += 1
        self._state.last_failure_time = time.monotonic()
        self._state.success_count = 0

        if self._state.state == CircuitState.HALF_OPEN:
            # Any failure in HALF_OPEN immediately reopens
            self._transition(CircuitState.OPEN)
            if self._on_open is not None:
                with contextlib.suppress(Exception):
                    self._on_open(self._state.name, self._state.failure_count)
        elif self._state.failure_count >= self._state.failure_threshold:
            self._transition(CircuitState.OPEN)
            if self._on_open is not None:
                with contextlib.suppress(Exception):
                    self._on_open(self._state.name, self._state.failure_count)

    def _record_success(self) -> None:
        """Record a success and possibly close the circuit."""
        self._state.success_count += 1

        if self._state.state == CircuitState.HALF_OPEN:
            if self._state.success_count >= self._state.half_open_max_calls:
                self._transition(CircuitState.CLOSED)
        elif self._state.state == CircuitState.CLOSED:
            # Reset failure count on success
            self._state.failure_count = 0

    def call(self, func: Callable[..., T], *args: Any, **kwargs: Any) -> T:
        """Execute a function with circuit breaker protection.

        If the circuit is OPEN, raises CircuitBreakerOpen immediately.
        If the circuit is CLOSED or HALF_OPEN, executes the function
        and records the result.

        Args:
            func: The function to execute.
            *args: Positional arguments for the function.
            **kwargs: Keyword arguments for the function.

        Returns:
            The return value of the function.

        Raises:
            CircuitBreakerOpen: If the circuit is OPEN.
            Exception: Any exception raised by the function.
        """
        with self._lock:
            self._maybe_transition_to_half_open()
            state = self._state.state

            if state == CircuitState.OPEN:
                time_remaining = max(
                    0.0,
                    self._state.recovery_timeout
                    - (time.monotonic() - self._state.last_state_change),
                )
                raise CircuitBreakerOpen(self._state.name, time_remaining)

            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self._state.half_open_max_calls:
                    time_remaining = max(
                        0.0,
                        self._state.recovery_timeout
                        - (time.monotonic() - self._state.last_state_change),
                    )
                    raise CircuitBreakerOpen(self._state.name, time_remaining)
                self._half_open_calls += 1

        try:
            result = func(*args, **kwargs)
        except BaseException as exc:
            if isinstance(exc, self._excluded):
                raise
            with self._lock:
                self._record_failure()
            raise
        else:
            with self._lock:
                self._record_success()
            return result

    async def async_call(self, func: Callable[..., Any], *args: Any, **kwargs: Any) -> Any:
        """Execute an async function with circuit breaker protection.

        Same semantics as call() but for async functions.

        Args:
            func: The async function to execute.
            *args: Positional arguments.
            **kwargs: Keyword arguments.

        Returns:
            The return value of the async function.

        Raises:
            CircuitBreakerOpen: If the circuit is OPEN.
        """
        with self._lock:
            self._maybe_transition_to_half_open()
            state = self._state.state

            if state == CircuitState.OPEN:
                time_remaining = max(
                    0.0,
                    self._state.recovery_timeout
                    - (time.monotonic() - self._state.last_state_change),
                )
                raise CircuitBreakerOpen(self._state.name, time_remaining)

            if state == CircuitState.HALF_OPEN:
                if self._half_open_calls >= self._state.half_open_max_calls:
                    time_remaining = max(
                        0.0,
                        self._state.recovery_timeout
                        - (time.monotonic() - self._state.last_state_change),
                    )
                    raise CircuitBreakerOpen(self._state.name, time_remaining)
                self._half_open_calls += 1

        try:
            result = await func(*args, **kwargs)
        except BaseException as exc:
            if isinstance(exc, self._excluded):
                raise
            with self._lock:
                self._record_failure()
            raise
        else:
            with self._lock:
                self._record_success()
            return result

    def reset(self) -> None:
        """Manually reset the circuit breaker to CLOSED state."""
        with self._lock:
            self._transition(CircuitState.CLOSED)

    def trip(self) -> None:
        """Manually trip (open) the circuit breaker."""
        with self._lock:
            self._transition(CircuitState.OPEN)

    @property
    def failure_count(self) -> int:
        """Current consecutive failure count."""
        with self._lock:
            return self._state.failure_count

    @property
    def state_info(self) -> dict[str, Any]:
        """Full state information for debugging."""
        with self._lock:
            self._maybe_transition_to_half_open()
            return {
                "name": self._state.name,
                "state": self._state.state.value,
                "failure_count": self._state.failure_count,
                "success_count": self._state.success_count,
                "failure_threshold": self._state.failure_threshold,
                "recovery_timeout": self._state.recovery_timeout,
            }
