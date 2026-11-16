"""Unit tests for decorators."""

from __future__ import annotations

import asyncio
import time

import pytest

from agent_killswitch import (
    KillLevel,
    KillScope,
    KillSwitch,
    killswitch_protected,
    with_heartbeat,
)
from agent_killswitch.core.heartbeat import HeartbeatMonitor
from agent_killswitch.decorators import KillSwitchTriggered, circuit_breaker


class TestKillSwitchProtected:
    """Tests for @killswitch_protected decorator."""

    def test_sync_function_passes_when_safe(self) -> None:
        ks = KillSwitch()

        @killswitch_protected(killswitch=ks, agent_id="a1")
        def my_func():
            return 42

        assert my_func() == 42

    def test_sync_function_raises_when_killed(self) -> None:
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="a1")

        @killswitch_protected(killswitch=ks, agent_id="a1")
        def my_func():
            return 42

        with pytest.raises(KillSwitchTriggered):
            my_func()

    @pytest.mark.asyncio
    async def test_async_function_passes_when_safe(self) -> None:
        ks = KillSwitch()

        @killswitch_protected(killswitch=ks, agent_id="a1")
        async def my_func():
            return 42

        assert await my_func() == 42

    @pytest.mark.asyncio
    async def test_async_function_raises_when_killed(self) -> None:
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.AGENT, scope_target="a1")

        @killswitch_protected(killswitch=ks, agent_id="a1")
        async def my_func():
            return 42

        with pytest.raises(KillSwitchTriggered):
            await my_func()

    def test_no_raise_with_callback(self) -> None:
        ks = KillSwitch()
        ks.activate(KillLevel.STOP, KillScope.GLOBAL)
        killed_statuses: list = []

        @killswitch_protected(
            killswitch=ks,
            agent_id="a1",
            on_killed=lambda s: killed_statuses.append(s),
            raise_on_kill=False,
        )
        def my_func():
            return 42

        result = my_func()
        assert result is None
        assert len(killed_statuses) == 1

    def test_none_killswitch_allows_execution(self) -> None:
        @killswitch_protected(killswitch=None, agent_id="a1")
        def my_func():
            return 42

        assert my_func() == 42

    def test_scope_as_string(self) -> None:
        ks = KillSwitch()

        @killswitch_protected(killswitch=ks, scope="agent", agent_id="a1")
        def my_func():
            return 42

        assert my_func() == 42

    def test_killed_exception_has_status(self) -> None:
        ks = KillSwitch()
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="emergency")

        @killswitch_protected(killswitch=ks, agent_id="a1")
        def my_func():
            return 42

        with pytest.raises(KillSwitchTriggered) as exc_info:
            my_func()

        assert exc_info.value.status.is_killed
        assert exc_info.value.status.level == KillLevel.KILL


class TestWithHeartbeat:
    """Tests for @with_heartbeat decorator."""

    def test_sync_heartbeat(self) -> None:
        monitor = HeartbeatMonitor(interval_seconds=0.05)

        @with_heartbeat(monitor=monitor, agent_id="a1", interval=0.05)
        def my_func():
            time.sleep(0.15)
            return "done"

        result = my_func()
        assert result == "done"
        monitor.shutdown()

    @pytest.mark.asyncio
    async def test_async_heartbeat(self) -> None:
        monitor = HeartbeatMonitor(interval_seconds=0.05)

        @with_heartbeat(monitor=monitor, agent_id="a1", interval=0.05)
        async def my_func():
            await asyncio.sleep(0.15)
            return "done"

        result = await my_func()
        assert result == "done"
        monitor.shutdown()

    def test_no_monitor_passthrough(self) -> None:
        @with_heartbeat(monitor=None, agent_id="a1")
        def my_func():
            return 42

        assert my_func() == 42


class TestCircuitBreakerDecorator:
    """Tests for @circuit_breaker decorator."""

    def test_sync_success(self) -> None:
        @circuit_breaker(name="test", failure_threshold=3)
        def my_func():
            return 42

        assert my_func() == 42

    def test_sync_trips_after_threshold(self) -> None:
        @circuit_breaker(name="test", failure_threshold=2, recovery_timeout=10.0)
        def failing_func():
            raise ValueError("fail")

        for _ in range(2):
            with pytest.raises(ValueError):
                failing_func()

        from agent_killswitch import CircuitBreakerOpen

        with pytest.raises(CircuitBreakerOpen):
            failing_func()

    @pytest.mark.asyncio
    async def test_async_success(self) -> None:
        @circuit_breaker(name="test", failure_threshold=3)
        async def my_func():
            return 42

        assert await my_func() == 42

    def test_exposes_breaker(self) -> None:
        @circuit_breaker(name="my-breaker", failure_threshold=5)
        def my_func():
            return 42

        assert hasattr(my_func, "_circuit_breaker")
        assert my_func._circuit_breaker.name == "my-breaker"
