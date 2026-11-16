"""Integration tests for asyncio task integration."""

from __future__ import annotations

import asyncio

import pytest

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.integrations.asyncio_tasks import (
    KillSwitchTaskGroup,
    run_with_killswitch,
)


@pytest.mark.asyncio
class TestKillSwitchTaskGroup:
    """Tests for asyncio task group with kill switch."""

    async def test_tasks_complete_normally(self) -> None:
        ks = KillSwitch()

        async def worker(name: str) -> str:
            await asyncio.sleep(0.05)
            return f"done-{name}"

        group = KillSwitchTaskGroup(
            killswitch=ks,
            agent_id="test",
            check_interval=0.02,
        )
        group.add_task(worker("a"))
        group.add_task(worker("b"))
        results = await group.run()

        assert len(results) == 2
        result_strs = [r for r in results if isinstance(r, str)]
        assert len(result_strs) == 2

    async def test_tasks_cancelled_on_kill(self) -> None:
        ks = KillSwitch()

        async def long_worker():
            await asyncio.sleep(10.0)
            return "should not complete"

        group = KillSwitchTaskGroup(
            killswitch=ks,
            agent_id="test",
            check_interval=0.05,
        )
        group.add_task(long_worker())
        group.add_task(long_worker())

        # Activate kill switch after a short delay
        async def delayed_kill():
            await asyncio.sleep(0.1)
            ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="test kill")

        _killer = asyncio.ensure_future(delayed_kill())
        results = await group.run()

        assert group.is_killed
        # Results should be CancelledError instances
        assert any(isinstance(r, (asyncio.CancelledError, BaseException)) for r in results)

    async def test_on_cancelled_callback(self) -> None:
        ks = KillSwitch()
        cancelled_called = [False]

        async def long_worker():
            await asyncio.sleep(10.0)

        group = KillSwitchTaskGroup(
            killswitch=ks,
            agent_id="test",
            check_interval=0.05,
            on_cancelled=lambda: cancelled_called.__setitem__(0, True),
        )
        group.add_task(long_worker())

        async def delayed_kill():
            await asyncio.sleep(0.1)
            ks.activate(KillLevel.KILL, KillScope.GLOBAL)

        _killer = asyncio.ensure_future(delayed_kill())
        await group.run()
        assert cancelled_called[0]


@pytest.mark.asyncio
class TestRunWithKillSwitch:
    """Tests for the convenience function."""

    async def test_normal_completion(self) -> None:
        ks = KillSwitch()

        async def my_task():
            await asyncio.sleep(0.05)
            return 42

        result = await run_with_killswitch(
            my_task(),
            killswitch=ks,
            agent_id="test",
            check_interval=0.02,
        )
        assert result == 42

    async def test_killed_during_execution(self) -> None:
        ks = KillSwitch()

        async def long_task():
            await asyncio.sleep(10.0)
            return "should not complete"

        async def delayed_kill():
            await asyncio.sleep(0.1)
            ks.activate(KillLevel.KILL, KillScope.GLOBAL)

        _killer = asyncio.ensure_future(delayed_kill())

        with pytest.raises((asyncio.CancelledError, BaseException)):
            await run_with_killswitch(
                long_task(),
                killswitch=ks,
                agent_id="test",
                check_interval=0.05,
            )
