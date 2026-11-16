"""E2E tests for heartbeat monitoring and recovery."""

from __future__ import annotations

import time

import pytest

from agent_killswitch import (
    HeartbeatMonitor,
    HeartbeatStatus,
    KillLevel,
    KillScope,
    KillSwitch,
)


class TestHeartbeatRecovery:
    """E2E tests for heartbeat-based death detection and recovery."""

    @pytest.mark.e2e
    def test_detect_dead_agent_and_kill(self) -> None:
        """Dead agent detected by heartbeat triggers kill switch."""
        ks = KillSwitch()
        killed_agents: list[str] = []

        def on_death(agent_id: str) -> None:
            ks.activate(
                KillLevel.KILL,
                KillScope.AGENT,
                scope_target=agent_id,
                reason=f"Heartbeat timeout for {agent_id}",
                activated_by="heartbeat_monitor",
            )
            killed_agents.append(agent_id)

        monitor = HeartbeatMonitor(
            interval_seconds=0.05,
            miss_threshold=3,
            on_dead=on_death,
        )

        try:
            ks.register_agent("agent-1")
            monitor.start("agent-1")

            # Agent stops sending heartbeats
            time.sleep(0.2)  # 4 intervals missed

            # Check health triggers the callback
            monitor.check_health()

            assert "agent-1" in killed_agents
            assert ks.check(scope_target="agent-1").is_killed
        finally:
            monitor.shutdown()

    @pytest.mark.e2e
    def test_agent_recovery_after_heartbeat_resume(self) -> None:
        """Agent recovers after heartbeat resumes."""
        monitor = HeartbeatMonitor(
            interval_seconds=0.05,
            miss_threshold=3,
        )

        try:
            monitor.start("agent-1")

            # Agent goes quiet
            time.sleep(0.2)
            health = monitor.check_health()
            assert health["agent-1"] == HeartbeatStatus.DEAD

            # Agent resumes heartbeats
            monitor.heartbeat("agent-1")
            health = monitor.check_health()
            assert health["agent-1"] == HeartbeatStatus.ALIVE
        finally:
            monitor.shutdown()

    @pytest.mark.e2e
    def test_mixed_healthy_and_dead(self) -> None:
        """Some agents healthy, others dead."""
        dead_agents: list[str] = []
        monitor = HeartbeatMonitor(
            interval_seconds=0.05,
            miss_threshold=3,
            on_dead=lambda aid: dead_agents.append(aid),
        )

        try:
            monitor.start("healthy-1")
            monitor.start("healthy-2")
            monitor.start("dead-1")

            # Keep healthy agents alive
            for _ in range(4):
                time.sleep(0.05)
                monitor.heartbeat("healthy-1")
                monitor.heartbeat("healthy-2")
                # dead-1 gets no heartbeats

            monitor.check_health()

            assert "dead-1" in dead_agents
            assert "healthy-1" not in dead_agents
            assert "healthy-2" not in dead_agents
        finally:
            monitor.shutdown()
