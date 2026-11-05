"""asyncio integration for agent-killswitch.

Provides utilities for managing asyncio.Task lifecycle with kill switch
integration. Supports task group cancellation and periodic kill switch
checks during async operations.
"""

from __future__ import annotations

import asyncio
import contextlib
import logging
from collections.abc import Callable, Coroutine
from typing import Any

logger = logging.getLogger(__name__)


class KillSwitchTaskGroup:
    """Managed group of asyncio tasks with kill switch integration.

    Wraps asyncio tasks and periodically checks the kill switch.
    If the kill switch activates, all tasks in the group are cancelled.

    Example::

        from agent_killswitch import KillSwitch
        from agent_killswitch.integrations.asyncio_tasks import KillSwitchTaskGroup

        ks = KillSwitch()


        async def worker(name: str):
            while True:
                await asyncio.sleep(1)
                print(f"{name} working...")


        async def main():
            group = KillSwitchTaskGroup(
                killswitch=ks,
                agent_id="async-agents",
                check_interval=1.0,
            )
            group.add_task(worker("a"))
            group.add_task(worker("b"))

            await group.run()  # Blocks until kill switch or all done

    Args:
        killswitch: The KillSwitch instance.
        agent_id: Agent ID for scope checks.
        crew_id: Optional crew ID.
        check_interval: How often to check kill switch (seconds). Default 1.0.
        on_cancelled: Callback when tasks are cancelled by kill switch.
    """

    def __init__(
        self,
        killswitch: Any,
        agent_id: str | None = None,
        crew_id: str | None = None,
        check_interval: float = 1.0,
        on_cancelled: Callable[[], None] | None = None,
    ) -> None:
        self._ks = killswitch
        self._agent_id = agent_id
        self._crew_id = crew_id
        self._check_interval = check_interval
        self._on_cancelled = on_cancelled
        self._coros: list[Coroutine[Any, Any, Any]] = []
        self._tasks: list[asyncio.Task[Any]] = []
        self._killed = False

    def add_task(self, coro: Coroutine[Any, Any, Any]) -> None:
        """Add a coroutine to the task group.

        Args:
            coro: The coroutine to add. Must not have been awaited yet.
        """
        self._coros.append(coro)

    async def run(self) -> list[Any]:
        """Run all tasks with kill switch monitoring.

        Starts all coroutines as tasks and monitors the kill switch.
        Returns when all tasks complete or kill switch activates.

        Returns:
            List of results from completed tasks. Results may be
            asyncio.CancelledError for tasks cancelled by kill switch.
        """
        asyncio.get_event_loop()

        # Start all tasks
        for coro in self._coros:
            task = asyncio.ensure_future(coro)
            self._tasks.append(task)
        self._coros.clear()

        # Start monitor
        monitor = asyncio.ensure_future(self._monitor_loop())

        # Wait for all tasks to complete (or be cancelled)
        results: list[Any] = []
        try:
            done, _pending = await asyncio.wait(
                self._tasks,
                return_when=asyncio.ALL_COMPLETED,
            )
            for task in done:
                try:
                    results.append(task.result())
                except (asyncio.CancelledError, Exception) as exc:
                    results.append(exc)
        except asyncio.CancelledError:
            results = [asyncio.CancelledError() for _ in self._tasks]
        finally:
            monitor.cancel()
            with contextlib.suppress(asyncio.CancelledError):
                await monitor

        return results

    async def _monitor_loop(self) -> None:
        """Periodically check kill switch and cancel tasks if active."""
        while True:
            await asyncio.sleep(self._check_interval)

            status = self._ks.check(
                scope_target=self._agent_id,
                crew_id=self._crew_id,
            )

            if status.is_killed and not self._killed:
                self._killed = True
                level_str = status.level.value if status.level else "unknown"
                logger.warning(
                    "asyncio_task_group_kill",
                    extra={
                        "agent_id": self._agent_id,
                        "level": level_str,
                        "task_count": len(self._tasks),
                    },
                )

                # Cancel all running tasks
                for task in self._tasks:
                    if not task.done():
                        task.cancel()

                if self._on_cancelled is not None:
                    try:
                        self._on_cancelled()
                    except Exception as exc:
                        logger.error(
                            "on_cancelled callback error",
                            extra={"error": str(exc)},
                        )

                break

    async def cancel_all(self) -> None:
        """Manually cancel all tasks in the group."""
        for task in self._tasks:
            if not task.done():
                task.cancel()

    @property
    def is_killed(self) -> bool:
        """Whether the task group was killed by the kill switch."""
        return self._killed


async def run_with_killswitch(
    coro: Coroutine[Any, Any, Any],
    killswitch: Any,
    agent_id: str | None = None,
    crew_id: str | None = None,
    check_interval: float = 1.0,
) -> Any:
    """Run a single coroutine with kill switch monitoring.

    Convenience function for running a single async operation with
    periodic kill switch checks.

    Args:
        coro: The coroutine to run.
        killswitch: The KillSwitch instance.
        agent_id: Agent ID for scope checks.
        crew_id: Optional crew ID.
        check_interval: Kill switch check interval in seconds.

    Returns:
        The result of the coroutine.

    Raises:
        asyncio.CancelledError: If killed by kill switch.
    """
    group = KillSwitchTaskGroup(
        killswitch=killswitch,
        agent_id=agent_id,
        crew_id=crew_id,
        check_interval=check_interval,
    )
    group.add_task(coro)
    results = await group.run()

    if results and isinstance(results[0], BaseException):
        raise results[0]
    return results[0] if results else None
