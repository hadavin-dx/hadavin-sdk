"""Unit tests for CircuitBreaker."""

from __future__ import annotations

import contextlib
import time

import pytest

from agent_killswitch import CircuitBreaker, CircuitBreakerOpen, CircuitState


class TestCircuitBreakerClosed:
    """Tests for CLOSED state behavior."""

    def test_initial_state_is_closed(self, circuit_breaker: CircuitBreaker) -> None:
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_successful_call(self, circuit_breaker: CircuitBreaker) -> None:
        result = circuit_breaker.call(lambda: 42)
        assert result == 42
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_failure_below_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        for _ in range(2):  # threshold is 3
            with pytest.raises(ValueError):
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_success_resets_failure_count(self, circuit_breaker: CircuitBreaker) -> None:
        # Two failures
        for _ in range(2):
            with contextlib.suppress(ValueError):
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        # One success resets
        circuit_breaker.call(lambda: "ok")
        assert circuit_breaker.failure_count == 0


class TestCircuitBreakerOpen:
    """Tests for OPEN state behavior."""

    def test_opens_after_threshold(self, circuit_breaker: CircuitBreaker) -> None:
        for _ in range(3):  # threshold is 3
            with contextlib.suppress(ValueError):
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert circuit_breaker.get_state() == CircuitState.OPEN

    def test_rejects_calls_when_open(self, circuit_breaker: CircuitBreaker) -> None:
        # Trip the breaker
        for _ in range(3):
            with contextlib.suppress(ValueError):
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        with pytest.raises(CircuitBreakerOpen) as exc_info:
            circuit_breaker.call(lambda: "should not run")

        assert "OPEN" in str(exc_info.value)
        assert exc_info.value.breaker_name == "test"

    def test_open_error_includes_recovery_time(self, circuit_breaker: CircuitBreaker) -> None:
        for _ in range(3):
            with contextlib.suppress(ValueError):
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        with pytest.raises(CircuitBreakerOpen) as exc_info:
            circuit_breaker.call(lambda: "nope")

        assert exc_info.value.time_until_half_open >= 0


class TestCircuitBreakerHalfOpen:
    """Tests for HALF_OPEN state behavior."""

    def test_transitions_to_half_open(self) -> None:
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
        )
        # Trip it
        for _ in range(2):
            with contextlib.suppress(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert breaker.get_state() == CircuitState.OPEN

        # Wait for recovery timeout
        time.sleep(0.15)
        assert breaker.get_state() == CircuitState.HALF_OPEN

    def test_half_open_success_closes(self) -> None:
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
            half_open_max_calls=1,
        )
        for _ in range(2):
            with contextlib.suppress(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        time.sleep(0.15)
        assert breaker.get_state() == CircuitState.HALF_OPEN

        # One success in HALF_OPEN -> CLOSED
        breaker.call(lambda: "recovered")
        assert breaker.get_state() == CircuitState.CLOSED

    def test_half_open_failure_reopens(self) -> None:
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            recovery_timeout=0.1,
        )
        for _ in range(2):
            with contextlib.suppress(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        time.sleep(0.15)
        assert breaker.get_state() == CircuitState.HALF_OPEN

        # Failure in HALF_OPEN -> back to OPEN
        with contextlib.suppress(ValueError):
            breaker.call(lambda: (_ for _ in ()).throw(ValueError("still broken")))
        assert breaker.get_state() == CircuitState.OPEN


class TestCircuitBreakerCallbacks:
    """Tests for state change callbacks."""

    def test_on_state_change_callback(self) -> None:
        changes: list[tuple] = []
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            on_state_change=lambda n, old, new: changes.append((n, old, new)),
        )
        for _ in range(2):
            with contextlib.suppress(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))

        assert len(changes) == 1
        assert changes[0] == ("test", CircuitState.CLOSED, CircuitState.OPEN)

    def test_on_open_callback(self) -> None:
        opens: list[tuple] = []
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            on_open=lambda n, fc: opens.append((n, fc)),
        )
        for _ in range(2):
            with contextlib.suppress(ValueError):
                breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert len(opens) == 1
        assert opens[0][0] == "test"


class TestCircuitBreakerReset:
    """Tests for manual reset/trip."""

    def test_manual_reset(self, circuit_breaker: CircuitBreaker) -> None:
        for _ in range(3):
            with contextlib.suppress(ValueError):
                circuit_breaker.call(lambda: (_ for _ in ()).throw(ValueError("fail")))
        assert circuit_breaker.get_state() == CircuitState.OPEN
        circuit_breaker.reset()
        assert circuit_breaker.get_state() == CircuitState.CLOSED

    def test_manual_trip(self, circuit_breaker: CircuitBreaker) -> None:
        assert circuit_breaker.get_state() == CircuitState.CLOSED
        circuit_breaker.trip()
        assert circuit_breaker.get_state() == CircuitState.OPEN


class TestCircuitBreakerExcluded:
    """Tests for excluded exceptions."""

    def test_excluded_exception_not_counted(self) -> None:
        breaker = CircuitBreaker(
            name="test",
            failure_threshold=2,
            excluded_exceptions=(KeyError,),
        )
        # KeyError should not count as failure
        for _ in range(5):
            with pytest.raises(KeyError):
                breaker.call(lambda: (_ for _ in ()).throw(KeyError("excluded")))
        assert breaker.get_state() == CircuitState.CLOSED
        assert breaker.failure_count == 0


class TestCircuitBreakerAsync:
    """Tests for async call support."""

    @pytest.mark.asyncio
    async def test_async_call_success(self, circuit_breaker: CircuitBreaker) -> None:
        async def async_func():
            return 42

        result = await circuit_breaker.async_call(async_func)
        assert result == 42

    @pytest.mark.asyncio
    async def test_async_call_failure(self, circuit_breaker: CircuitBreaker) -> None:
        async def failing_func():
            raise ValueError("async fail")

        for _ in range(3):
            with pytest.raises(ValueError):
                await circuit_breaker.async_call(failing_func)
        assert circuit_breaker.get_state() == CircuitState.OPEN


class TestCircuitBreakerInfo:
    """Tests for state info."""

    def test_state_info(self, circuit_breaker: CircuitBreaker) -> None:
        info = circuit_breaker.state_info
        assert info["name"] == "test"
        assert info["state"] == "closed"
        assert info["failure_count"] == 0
        assert info["failure_threshold"] == 3
