"""Decorators for easy kill switch integration.

Provides decorator-based APIs for common patterns:
- @killswitch_protected: Check kill switch before/after function execution
- @with_heartbeat: Send heartbeats during long-running operations
- @circuit_breaker: Wrap functions with circuit breaker protection

All decorators support both sync and async functions.
"""

from __future__ import annotations

import functools
import inspect
import logging
import threading
from collections.abc import Callable
from typing import Any, TypeVar, Union

from .core.circuit_breaker import CircuitBreaker
from .core.enums import KillScope
from .core.killswitch import KillSwitch
from .core.models import KillStatus

logger = logging.getLogger(__name__)

F = TypeVar("F", bound=Callable[..., Any])


class KillSwitchTriggered(Exception):
    """Raised when a kill switch check finds an active kill.

    Attributes:
        status: The KillStatus that triggered the exception.
    """

    def __init__(self, status: KillStatus) -> None:
        self.status = status
        level_str = status.level.value if status.level else "unknown"
        super().__init__(
            f"Kill switch triggered: level={level_str}, "
            f"scope={status.scope}, target={status.scope_target}, "
            f"reason={status.reason}"
        )


def killswitch_protected(
    killswitch: KillSwitch | None = None,
    scope: Union[str, KillScope] = KillScope.AGENT,
    agent_id: str | None = None,
    crew_id: str | None = None,
    on_killed: Callable[[KillStatus], None] | None = None,
    raise_on_kill: bool = True,
) -> Callable[[F], F]:
    """Decorator that checks the kill switch before and after execution.

    If the kill switch is active, either raises KillSwitchTriggered
    or calls the on_killed callback (depending on raise_on_kill).

    Example::

        ks = KillSwitch()


        @killswitch_protected(killswitch=ks, agent_id="my-agent")
        async def my_agent_task():
            # ... agent work ...
            pass

    Args:
        killswitch: The KillSwitch instance to check. If None, the
            function runs without protection (useful for testing).
        scope: The scope to check. Default AGENT.
        agent_id: The agent ID for scope checks.
        crew_id: The crew ID for crew scope checks.
        on_killed: Callback when kill is detected.
        raise_on_kill: If True, raise KillSwitchTriggered. Default True.

    Returns:
        Decorator function.
    """
    if isinstance(scope, str):
        scope = KillScope(scope)

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if killswitch is not None:
                    status = killswitch.check(
                        scope_target=agent_id,
                        crew_id=crew_id,
                    )
                    if status.is_killed:
                        if on_killed is not None:
                            on_killed(status)
                        if raise_on_kill:
                            raise KillSwitchTriggered(status)
                        return None

                result = await func(*args, **kwargs)

                if killswitch is not None:
                    status = killswitch.check(
                        scope_target=agent_id,
                        crew_id=crew_id,
                    )
                    if status.is_killed:
                        if on_killed is not None:
                            on_killed(status)
                        if raise_on_kill:
                            raise KillSwitchTriggered(status)

                return result

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                if killswitch is not None:
                    status = killswitch.check(
                        scope_target=agent_id,
                        crew_id=crew_id,
                    )
                    if status.is_killed:
                        if on_killed is not None:
                            on_killed(status)
                        if raise_on_kill:
                            raise KillSwitchTriggered(status)
                        return None

                result = func(*args, **kwargs)

                if killswitch is not None:
                    status = killswitch.check(
                        scope_target=agent_id,
                        crew_id=crew_id,
                    )
                    if status.is_killed:
                        if on_killed is not None:
                            on_killed(status)
                        if raise_on_kill:
                            raise KillSwitchTriggered(status)

                return result

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def with_heartbeat(
    monitor: Any = None,
    agent_id: str | None = None,
    interval: float = 5.0,
) -> Callable[[F], F]:
    """Decorator that sends heartbeats during function execution.

    Starts a background thread that sends periodic heartbeats to the
    HeartbeatMonitor while the decorated function is running.

    Example::

        from agent_killswitch import HeartbeatMonitor

        monitor = HeartbeatMonitor()


        @with_heartbeat(monitor=monitor, agent_id="my-agent", interval=5.0)
        async def long_running_agent():
            # heartbeats are sent automatically
            await do_work()

    Args:
        monitor: HeartbeatMonitor instance. If None, no heartbeats sent.
        agent_id: The agent ID for heartbeats.
        interval: Heartbeat interval in seconds. Default 5.0.

    Returns:
        Decorator function.
    """

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                if monitor is None or agent_id is None:
                    return await func(*args, **kwargs)

                monitor.start(agent_id, interval_seconds=interval)
                stop_event = threading.Event()

                def heartbeat_loop() -> None:
                    while not stop_event.is_set():
                        monitor.heartbeat(agent_id)
                        stop_event.wait(interval)

                thread = threading.Thread(
                    target=heartbeat_loop,
                    daemon=True,
                    name=f"heartbeat-{agent_id}",
                )
                thread.start()

                try:
                    return await func(*args, **kwargs)
                finally:
                    stop_event.set()
                    thread.join(timeout=interval + 1.0)
                    monitor.stop(agent_id)

            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                if monitor is None or agent_id is None:
                    return func(*args, **kwargs)

                monitor.start(agent_id, interval_seconds=interval)
                stop_event = threading.Event()

                def heartbeat_loop() -> None:
                    while not stop_event.is_set():
                        monitor.heartbeat(agent_id)
                        stop_event.wait(interval)

                thread = threading.Thread(
                    target=heartbeat_loop,
                    daemon=True,
                    name=f"heartbeat-{agent_id}",
                )
                thread.start()

                try:
                    return func(*args, **kwargs)
                finally:
                    stop_event.set()
                    thread.join(timeout=interval + 1.0)
                    monitor.stop(agent_id)

            return sync_wrapper  # type: ignore[return-value]

    return decorator


def circuit_breaker(
    name: str = "default",
    failure_threshold: int = 5,
    recovery_timeout: float = 30.0,
    excluded_exceptions: tuple[type[BaseException], ...] | None = None,
) -> Callable[[F], F]:
    """Decorator that wraps a function with circuit breaker protection.

    Creates a CircuitBreaker instance per decorated function and
    routes all calls through it.

    Example::

        @circuit_breaker(name="openai", failure_threshold=3, recovery_timeout=60)
        async def call_openai(prompt: str) -> str:
            return await openai.chat(prompt)

    Args:
        name: Circuit breaker name.
        failure_threshold: Failures before opening.
        recovery_timeout: Seconds before trying half-open.
        excluded_exceptions: Exceptions that don't count as failures.

    Returns:
        Decorator function.
    """
    breaker = CircuitBreaker(
        name=name,
        failure_threshold=failure_threshold,
        recovery_timeout=recovery_timeout,
        excluded_exceptions=excluded_exceptions,
    )

    def decorator(func: F) -> F:
        if inspect.iscoroutinefunction(func):

            @functools.wraps(func)
            async def async_wrapper(*args: Any, **kwargs: Any) -> Any:
                return await breaker.async_call(func, *args, **kwargs)

            # Expose the breaker for inspection
            async_wrapper._circuit_breaker = breaker  # type: ignore[attr-defined]
            return async_wrapper  # type: ignore[return-value]
        else:

            @functools.wraps(func)
            def sync_wrapper(*args: Any, **kwargs: Any) -> Any:
                return breaker.call(func, *args, **kwargs)

            sync_wrapper._circuit_breaker = breaker  # type: ignore[attr-defined]
            return sync_wrapper  # type: ignore[return-value]

    return decorator
