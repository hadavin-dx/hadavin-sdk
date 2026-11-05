"""asyncio integration example for agent-killswitch.

Shows how to protect asyncio tasks with kill switch monitoring.
"""

from __future__ import annotations

import asyncio

from agent_killswitch import KillLevel, KillScope, KillSwitch
from agent_killswitch.integrations.asyncio_tasks import KillSwitchTaskGroup


async def worker(name: str, work_time: float) -> str:
    """Simulated async agent worker."""
    print(f"  [{name}] Starting work...")
    for i in range(int(work_time * 10)):
        await asyncio.sleep(0.1)
        print(f"  [{name}] Working... {(i + 1) * 10}%")
    print(f"  [{name}] Done!")
    return f"{name} completed"


async def main() -> None:
    ks = KillSwitch()

    print("Example 1: Normal completion")
    print("-" * 40)

    group = KillSwitchTaskGroup(
        killswitch=ks,
        agent_id="async-demo",
        check_interval=0.2,
    )
    group.add_task(worker("Agent-A", 0.5))
    group.add_task(worker("Agent-B", 0.3))

    results = await group.run()
    for r in results:
        if isinstance(r, str):
            print(f"  Result: {r}")
    print()

    print("Example 2: Kill switch activated during execution")
    print("-" * 40)

    group2 = KillSwitchTaskGroup(
        killswitch=ks,
        agent_id="async-demo",
        check_interval=0.1,
        on_cancelled=lambda: print("  ALL TASKS CANCELLED by kill switch"),
    )
    group2.add_task(worker("Agent-C", 2.0))
    group2.add_task(worker("Agent-D", 2.0))

    # Schedule kill after 0.5 seconds
    async def delayed_kill():
        await asyncio.sleep(0.5)
        print("\n  >>> KILL SWITCH ACTIVATED <<<")
        ks.activate(KillLevel.KILL, KillScope.GLOBAL, reason="Demo emergency")

    # Hold a reference: a task referenced only by the event loop can be garbage
    # collected before it runs, which would mean the kill never fires.
    killer = asyncio.ensure_future(delayed_kill())
    results2 = await group2.run()
    await killer  # let the timer finish so nothing is left pending at exit

    cancelled = sum(1 for r in results2 if isinstance(r, BaseException))
    print(f"\n  Tasks cancelled: {cancelled}")
    print(f"  Group was killed: {group2.is_killed}")


if __name__ == "__main__":
    asyncio.run(main())
