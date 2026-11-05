"""Heartbeat monitoring example for agent-killswitch.

Demonstrates how to monitor agent health with periodic heartbeats
and automatically kill unresponsive agents.
"""

from __future__ import annotations

import time

from agent_killswitch import (
    HeartbeatMonitor,
    HeartbeatStatus,
    KillLevel,
    KillScope,
    KillSwitch,
)


def main() -> None:
    # Create kill switch and heartbeat monitor
    ks = KillSwitch()

    def on_agent_dead(agent_id: str) -> None:
        print(f"ALERT: Agent {agent_id} is DEAD! Activating kill switch...")
        ks.activate(
            KillLevel.KILL,
            KillScope.AGENT,
            scope_target=agent_id,
            reason=f"Heartbeat timeout for {agent_id}",
            activated_by="heartbeat_monitor",
        )

    monitor = HeartbeatMonitor(
        interval_seconds=1.0,  # Expect heartbeat every 1 second
        miss_threshold=3,  # 3 missed = dead
        on_dead=on_agent_dead,
    )

    # Register and start monitoring agents
    ks.register_agent("agent-healthy")
    ks.register_agent("agent-flaky")
    monitor.start("agent-healthy")
    monitor.start("agent-flaky")

    print("Monitoring started. Simulating agent behavior...\n")

    # Simulate: healthy agent sends heartbeats, flaky agent stops
    for i in range(8):
        time.sleep(0.5)

        # Healthy agent always sends heartbeats
        monitor.heartbeat("agent-healthy")

        # Flaky agent stops after 3 iterations
        if i < 3:
            monitor.heartbeat("agent-flaky")
        else:
            print(f"  [tick {i}] agent-flaky missed heartbeat")

        # Check health
        health = monitor.check_health()
        for agent_id, status in health.items():
            if status != HeartbeatStatus.ALIVE:
                print(f"  [tick {i}] {agent_id}: {status.value}")

    # Final status
    print("\nFinal status:")
    print(f"  agent-healthy killed: {ks.check(scope_target='agent-healthy').is_killed}")
    print(f"  agent-flaky killed: {ks.check(scope_target='agent-flaky').is_killed}")

    monitor.shutdown()


if __name__ == "__main__":
    main()
