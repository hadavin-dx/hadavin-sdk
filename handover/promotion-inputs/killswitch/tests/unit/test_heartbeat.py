"""Unit tests for HeartbeatMonitor."""

from __future__ import annotations

import time

from agent_killswitch import HeartbeatMonitor, HeartbeatStatus


class TestHeartbeatStart:
    """Tests for starting heartbeat monitoring."""

    def test_start_registers_agent(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        assert heartbeat_monitor.monitored_count == 1

    def test_start_sets_alive_status(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        record = heartbeat_monitor.get_record("agent-1")
        assert record is not None
        assert record.status == HeartbeatStatus.ALIVE

    def test_start_multiple_agents(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("a1")
        heartbeat_monitor.start("a2")
        heartbeat_monitor.start("a3")
        assert heartbeat_monitor.monitored_count == 3


class TestHeartbeatSend:
    """Tests for sending heartbeats."""

    def test_heartbeat_updates_time(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        time.sleep(0.05)
        heartbeat_monitor.heartbeat("agent-1")
        record = heartbeat_monitor.get_record("agent-1")
        assert record is not None
        assert record.status == HeartbeatStatus.ALIVE

    def test_heartbeat_returns_false_for_unknown(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        assert heartbeat_monitor.heartbeat("unknown") is False

    def test_heartbeat_resets_miss_count(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        # Wait enough to miss some heartbeats
        time.sleep(0.25)  # 2.5 intervals at 0.1s
        heartbeat_monitor.check_health()
        # Now send a heartbeat
        heartbeat_monitor.heartbeat("agent-1")
        record = heartbeat_monitor.get_record("agent-1")
        assert record is not None
        assert record.miss_count == 0
        assert record.status == HeartbeatStatus.ALIVE


class TestHeartbeatHealth:
    """Tests for health checking."""

    def test_alive_within_interval(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        health = heartbeat_monitor.check_health()
        assert health["agent-1"] == HeartbeatStatus.ALIVE

    def test_suspect_after_miss(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        time.sleep(0.15)  # 1.5 intervals
        health = heartbeat_monitor.check_health()
        assert health["agent-1"] == HeartbeatStatus.SUSPECT

    def test_dead_after_threshold(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        time.sleep(0.35)  # 3.5 intervals, threshold is 3
        health = heartbeat_monitor.check_health()
        assert health["agent-1"] == HeartbeatStatus.DEAD

    def test_get_dead_agents(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("a1")
        heartbeat_monitor.start("a2")
        time.sleep(0.35)
        heartbeat_monitor.heartbeat("a1")  # Keep a1 alive
        dead = heartbeat_monitor.get_dead_agents()
        assert "a2" in dead
        assert "a1" not in dead


class TestHeartbeatCallbacks:
    """Tests for heartbeat callbacks."""

    def test_on_dead_callback(self) -> None:
        dead_agents: list[str] = []
        monitor = HeartbeatMonitor(
            interval_seconds=0.05,
            miss_threshold=2,
            on_dead=lambda aid: dead_agents.append(aid),
        )
        try:
            monitor.start("agent-1")
            time.sleep(0.15)
            monitor.check_health()
            assert "agent-1" in dead_agents
        finally:
            monitor.shutdown()

    def test_on_dead_called_once(self) -> None:
        dead_calls: list[str] = []
        monitor = HeartbeatMonitor(
            interval_seconds=0.05,
            miss_threshold=2,
            on_dead=lambda aid: dead_calls.append(aid),
        )
        try:
            monitor.start("agent-1")
            time.sleep(0.15)
            monitor.check_health()
            monitor.check_health()
            monitor.check_health()
            # Should only be called once per death event
            assert dead_calls.count("agent-1") == 1
        finally:
            monitor.shutdown()

    def test_on_suspect_callback(self) -> None:
        suspect_calls: list[tuple[str, int]] = []
        monitor = HeartbeatMonitor(
            interval_seconds=0.05,
            miss_threshold=5,
            on_suspect=lambda aid, mc: suspect_calls.append((aid, mc)),
        )
        try:
            monitor.start("agent-1")
            time.sleep(0.08)
            monitor.check_health()
            assert len(suspect_calls) >= 1
            assert suspect_calls[0][0] == "agent-1"
        finally:
            monitor.shutdown()


class TestHeartbeatStop:
    """Tests for stopping monitoring."""

    def test_stop_removes_agent(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.start("agent-1")
        heartbeat_monitor.stop("agent-1")
        assert heartbeat_monitor.monitored_count == 0
        assert heartbeat_monitor.get_record("agent-1") is None

    def test_stop_nonexistent_is_safe(self, heartbeat_monitor: HeartbeatMonitor) -> None:
        heartbeat_monitor.stop("nonexistent")  # Should not raise


class TestHeartbeatCustomInterval:
    """Tests for custom heartbeat intervals."""

    def test_custom_interval_per_agent(self) -> None:
        monitor = HeartbeatMonitor(interval_seconds=1.0, miss_threshold=3)
        try:
            monitor.start("fast", interval_seconds=0.05)
            monitor.start("slow", interval_seconds=10.0)

            time.sleep(0.2)
            health = monitor.check_health()
            # Fast agent should be dead, slow agent still alive
            assert health["fast"] == HeartbeatStatus.DEAD
            assert health["slow"] == HeartbeatStatus.ALIVE
        finally:
            monitor.shutdown()
